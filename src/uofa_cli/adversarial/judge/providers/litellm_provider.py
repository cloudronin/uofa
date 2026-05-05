"""Unified judge provider via litellm (Phase 3 v1.6 litellm-first refactor).

Replaces the per-vendor `OpenAICompatProvider` and `GeminiProvider` classes
with a single `LiteLLMProvider`. Vendor-specific quirks live in
`capabilities.py`; this class orchestrates the call.

Construction:
    LiteLLMProvider(
        provider_token='openai',  # or 'gemini', 'hf-llama', 'anthropic', 'mistral'
        model='gpt-4o-mini',  # optional override; default from capabilities
        judge_role='production',  # or 'calibration_anchor', 'arbiter'
        client=None,  # mock injection for tests; if None, calls litellm.acompletion
    )
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Awaitable, Callable

from uofa_cli.adversarial.judge.prompts import (
    ARBITRATION_PROMPT_VERSION,
    PROMPT_TEMPLATE_VERSION,
    build_arbitration_prompt_for_case,
    build_arbitration_prompt_static_prefix,
    build_prompt_for_case,
    build_prompt_static_prefix,
)
from uofa_cli.adversarial.judge.providers.base import (
    AbstractJudgeProvider,
    CalibrationResult,
    Judgment,
)
from uofa_cli.adversarial.judge.providers.capabilities import (
    ProviderCapabilities,
    get_capabilities,
    litellm_model_string,
    strip_schema_for_provider,
)
from uofa_cli.adversarial.judge.retry import TransientError, with_retry

logger = logging.getLogger(__name__)


def _load_schema(schema_name: str = "judge_output_schema.json") -> dict:
    """Load specs/<schema_name> from the repo root."""
    repo_root = Path(__file__).resolve().parents[5]
    schema_path = repo_root / "specs" / schema_name
    if not schema_path.exists():
        raise FileNotFoundError(f"judge schema not found at {schema_path}")
    return json.loads(schema_path.read_text())


# Type alias for the litellm.acompletion callable; tests inject a mock.
CompletionFn = Callable[..., Awaitable[Any]]


class LiteLLMProvider(AbstractJudgeProvider):
    """Single judge provider that routes through `litellm.acompletion`.

    Vendor-specific behavior (strict-schema support, schema-keyword
    blocklist, batch availability, caching, thinking-mode params) lives in
    `capabilities.py` keyed by `provider_token`. This class glues the
    capability table to the prompt-assembly + retry + parse pipeline.
    """

    def __init__(
        self,
        provider_token: str,
        *,
        model: str | None = None,
        judge_role: str = "production",
        completion_fn: CompletionFn | None = None,
        thinking_enabled: bool = True,
        schema_name: str = "judge_output_schema.json",
    ) -> None:
        self._provider_token = provider_token
        self._caps: ProviderCapabilities = get_capabilities(provider_token)
        self._model = model or self._caps.default_model
        self._litellm_model = litellm_model_string(provider_token, model)
        self._judge_role = judge_role
        self._thinking_enabled = thinking_enabled
        self._schema_name = schema_name
        # `completion_fn` is the seam for tests. None → real litellm.acompletion.
        self._completion_fn = completion_fn

    # ── identity / capability properties ──

    @property
    def family(self) -> str:
        return self._caps.family

    @property
    def model(self) -> str:
        return self._model

    @property
    def judge_role(self) -> str:
        return self._judge_role

    @property
    def supports_strict_schema(self) -> bool:
        return self._caps.supports_strict_schema

    @property
    def provider_token(self) -> str:
        return self._provider_token

    @property
    def capabilities(self) -> ProviderCapabilities:
        return self._caps

    # ── core call paths ──

    async def judge(self, case: dict) -> Judgment:
        return await self._judge_with_retry(case)

    @with_retry()
    async def _judge_with_retry(self, case: dict) -> Judgment:
        # Arbiter role uses the Judge E arbitration prompt + per-case
        # rendering that includes the three production-judge verdicts.
        # Production / calibration_anchor roles use the standard prompt.
        if self._judge_role == "arbiter":
            prefix = build_arbitration_prompt_static_prefix()
            production_verdicts = case.get("_production_verdicts") or case.get(
                "production_verdicts", []
            )
            per_case = build_arbitration_prompt_for_case(case, production_verdicts)
            schema_name = "judge_e_output_schema.json"
        else:
            prefix = build_prompt_static_prefix()
            per_case = build_prompt_for_case(case)
            schema_name = self._schema_name
        return await self._call(prefix, per_case, case, schema_name=schema_name)

    async def _call(
        self,
        prefix: str,
        per_case: str,
        case: dict,
        *,
        schema_name: str | None = None,
    ) -> Judgment:
        """Single litellm.acompletion call → Judgment."""
        if schema_name is None:
            schema_name = self._schema_name
        messages = [
            {"role": "system", "content": prefix},
            {"role": "user", "content": per_case},
        ]

        kwargs: dict[str, Any] = {
            "model": self._litellm_model,
            "messages": messages,
            "temperature": 0.0,
        }
        # Add thinking-mode params if the capability table specifies them
        # and the caller requested thinking. Each (k, v) pair in
        # thinking_kwargs becomes a top-level kwarg to litellm.acompletion.
        if self._thinking_enabled:
            for k, v in self._caps.thinking_kwargs:
                kwargs[k] = v

        # OpenAI honors `seed`; other vendors generally accept-and-ignore via
        # litellm. Setting it broadly is safe; litellm filters per-vendor.
        kwargs["seed"] = 42

        # response_format: strict json-schema for vendors that support it,
        # json_object for others (with tolerant-parser fallback).
        schema = _load_schema(schema_name)
        if self._caps.supports_strict_schema:
            sent_schema = strip_schema_for_provider(schema, self._provider_token)
            kwargs["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": "judge_verdict_output",
                    "strict": True,
                    "schema": sent_schema,
                },
            }
        else:
            kwargs["response_format"] = {"type": "json_object"}

        try:
            response = await self._invoke_completion(**kwargs)
        except Exception as e:
            if _is_transient(e):
                raise TransientError(str(e)) from e
            raise

        text = self._extract_text(response)
        if not text:
            raise RuntimeError(f"empty response from {self._litellm_model}")
        parsed = self._parse_response(text, schema)
        return self._build_judgment(case, parsed, raw=parsed)

    async def _invoke_completion(self, **kwargs):
        """Dispatch to either an injected completion_fn or litellm.acompletion."""
        if self._completion_fn is not None:
            result = self._completion_fn(**kwargs)
            # Test mocks may return a coroutine or a plain value.
            if hasattr(result, "__await__"):
                return await result
            return result
        # Real path: lazy-import litellm so test environments without it work.
        import litellm

        return await litellm.acompletion(**kwargs)

    @staticmethod
    def _extract_text(response: Any) -> str | None:
        """Pull the assistant text from a litellm.ModelResponse-like object."""
        # Real ModelResponse: response.choices[0].message.content
        try:
            return response.choices[0].message.content
        except AttributeError:
            pass
        # Dict-shaped responses (test mocks).
        try:
            return response["choices"][0]["message"]["content"]
        except (KeyError, TypeError, IndexError):
            return None

    def _parse_response(self, text: str, schema: dict) -> dict:
        """Parse + schema-validate the response.

        Strict-mode providers may have had keywords stripped before the
        call; we always validate against the FULL schema here so dropped
        constraints still gate the verdict.
        """
        # For strict-schema providers, response is JSON; parse directly.
        if self._caps.supports_strict_schema:
            parsed = json.loads(text)
        else:
            # HF Llama / Mistral non-strict path: tolerant parser handles
            # brace-drop, code-fence-strip, prefix truncation. Reuses the
            # extract eval pattern from llm_extractor.
            from uofa_cli.llm_extractor import _parse_response as tolerant_parse

            try:
                parsed = tolerant_parse(text)
            except ValueError as e:
                raise RuntimeError(f"could not parse {self._provider_token} response: {e}") from e

        # Always validate against the full schema (post-call).
        try:
            import jsonschema

            jsonschema.validate(parsed, schema)
        except ImportError:
            logger.warning("jsonschema not installed; skipping post-parse validation")
        except Exception as e:
            raise RuntimeError(
                f"{self._provider_token} response failed full-schema validation: {e}"
            ) from e

        return parsed

    def _build_judgment(self, case: dict, parsed: dict, *, raw: dict) -> Judgment:
        """Assemble a Judgment from the parsed response.

        Override `judge_model` with our authoritative model id since some
        providers fabricate this field (cosmetic but the user flagged this
        in v1.5 smoke).
        """
        return Judgment(
            case_id=parsed["case_id"],
            verdict=parsed["verdict"],
            confidence=parsed["confidence"],
            reasoning_steps=parsed["reasoning_steps"],
            reasoning=parsed["reasoning"],
            section_6_7_candidate=parsed.get("section_6_7_candidate"),
            alternative_rule_analysis=parsed.get("alternative_rule_analysis"),
            prompt_template_version=parsed.get(
                "prompt_template_version", PROMPT_TEMPLATE_VERSION
            ),
            judge_model=self._model,  # authoritative; ignore any model fabrication
            judge_thinking_enabled=parsed.get(
                "judge_thinking_enabled", self._thinking_enabled
            ),
            judge_model_params=parsed.get(
                "judge_model_params", {"temperature": 0.0, "seed": 42}
            ),
            generator_provenance=parsed.get(
                "generator_provenance",
                {"generator_model": "unknown", "temperature": None, "seed": None},
            ),
            raw_response=raw,
        )

    # ── calibration ──

    async def calibrate(self, calibration_set: list[dict]) -> CalibrationResult:
        if not calibration_set:
            return CalibrationResult(
                judge_model=self._model,
                overall_accuracy=0.0,
                per_class_accuracy={},
                confusion_matrix={},
                case_count=0,
                correct_count=0,
            )

        per_class_total: dict[str, int] = {}
        per_class_correct: dict[str, int] = {}
        confusion: dict[str, dict[str, int]] = {}
        correct = 0

        for entry in calibration_set:
            ground_truth = entry["ground_truth_verdict"]
            judgment = await self.judge(entry)
            per_class_total[ground_truth] = per_class_total.get(ground_truth, 0) + 1
            if judgment.verdict == ground_truth:
                correct += 1
                per_class_correct[ground_truth] = per_class_correct.get(ground_truth, 0) + 1
            confusion.setdefault(ground_truth, {})
            confusion[ground_truth][judgment.verdict] = (
                confusion[ground_truth].get(judgment.verdict, 0) + 1
            )

        per_class_accuracy = {
            cls: per_class_correct.get(cls, 0) / per_class_total[cls]
            for cls in per_class_total
        }

        return CalibrationResult(
            judge_model=self._model,
            overall_accuracy=correct / len(calibration_set),
            per_class_accuracy=per_class_accuracy,
            confusion_matrix=confusion,
            case_count=len(calibration_set),
            correct_count=correct,
        )


def _is_transient(exc: BaseException) -> bool:
    """Heuristic classification of vendor errors as retry-worthy."""
    name = type(exc).__name__.lower()
    if any(s in name for s in ("rate", "timeout", "connection", "deadline")):
        return True
    code = getattr(exc, "status_code", None)
    if isinstance(code, int) and 500 <= code < 600:
        return True
    return False

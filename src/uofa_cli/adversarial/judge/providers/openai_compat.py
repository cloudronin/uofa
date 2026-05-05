"""OpenAI-compatible provider (spec v1.5 §5.2).

Serves two targets via env-var-driven init:

    target='openai'    → OpenAI proper (gpt-5.4) with strict JSON schema
    target='hf-llama'  → HuggingFace Inference Endpoints OpenAI-compat
                         API (Llama 3.3 70B) with JSON-mode + tolerant
                         parser fallback (spec §7.7)

The class uses the `openai` Python SDK for both, varying only `api_key`
and `base_url` at construction time.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

from uofa_cli.adversarial.judge.prompts import (
    PROMPT_TEMPLATE_VERSION,
    build_prompt_for_case,
    build_prompt_static_prefix,
)
from uofa_cli.adversarial.judge.providers.base import (
    AbstractJudgeProvider,
    CalibrationResult,
    Judgment,
)
from uofa_cli.adversarial.judge.retry import TransientError, with_retry

logger = logging.getLogger(__name__)

_DEFAULT_OPENAI_MODEL = "gpt-5.4"
_DEFAULT_HF_LLAMA_MODEL = "meta-llama/Llama-3.3-70B-Instruct"
_DEFAULT_ANTHROPIC_MODEL = "claude-sonnet-4-5"


def _load_schema() -> dict:
    """Load specs/judge_output_schema.json from the repo root.

    Located lazily (not at import time) so tests with no schema present
    still import cleanly, and the path is resolved from this module's
    location rather than CWD.
    """
    repo_root = Path(__file__).resolve().parents[5]
    schema_path = repo_root / "specs" / "judge_output_schema.json"
    if not schema_path.exists():
        raise FileNotFoundError(
            f"judge output schema not found at {schema_path}; "
            f"the schema is required for strict-mode and validation"
        )
    return json.loads(schema_path.read_text())


class OpenAICompatProvider(AbstractJudgeProvider):
    """Judge provider over an OpenAI-compatible HTTP API.

    Two valid targets: 'openai' (real OpenAI API) and 'hf-llama' (HF
    Inference Endpoints, which exposes OpenAI-compat). Construction:

        # Judge A — GPT
        gpt = OpenAICompatProvider(target='openai')

        # Judge C — Llama via HF Endpoints
        llama = OpenAICompatProvider(target='hf-llama')

    Real network calls are guarded behind the `client` injection in tests:
    pass `client=Mock()` at construction to short-circuit.
    """

    def __init__(
        self,
        target: str,
        *,
        model: str | None = None,
        thinking_enabled: bool = True,
        client: Any = None,  # Mock-able for tests; real OpenAI() if None
    ) -> None:
        if target not in ("openai", "hf-llama", "anthropic"):
            raise ValueError(
                f"unknown target {target!r}; expected 'openai', 'hf-llama', or 'anthropic'"
            )
        self.target = target
        self._thinking_enabled = thinking_enabled

        if target == "openai":
            self._family = "GPT"
            self._model = model or _DEFAULT_OPENAI_MODEL
            self._supports_strict_schema = True
        elif target == "hf-llama":
            self._family = "Llama"
            self._model = model or _DEFAULT_HF_LLAMA_MODEL
            # HF TGI only supports JSON-mode hint (no strict schema).
            self._supports_strict_schema = False
        else:  # anthropic
            # Anthropic's OpenAI-compatible endpoint
            # (https://docs.anthropic.com/en/api/openai-sdk) accepts
            # `response_format={'type': 'json_schema', ...}` — same shape
            # as OpenAI strict-mode. (It does NOT accept json_object.)
            #
            # Note: Anthropic is the Phase 2 generator family, so this
            # target is intended for smoke tests against same-family
            # judges (requires --allow-same-family-judge), not Stage 2
            # production runs.
            self._family = "Claude"
            self._model = model or _DEFAULT_ANTHROPIC_MODEL
            self._supports_strict_schema = True

        self._client = client if client is not None else self._build_default_client()

    def _build_default_client(self):
        # Imported lazily so tests that pass a mock client don't need the
        # `openai` package installed.
        from openai import OpenAI

        if self.target == "openai":
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                raise EnvironmentError("OPENAI_API_KEY not set")
            return OpenAI(api_key=api_key)

        if self.target == "hf-llama":
            api_key = os.environ.get("OPENAI_API_KEY_HF")
            base_url = os.environ.get("OPENAI_BASE_URL_HF")
            if not api_key or not base_url:
                raise EnvironmentError(
                    "OPENAI_API_KEY_HF and OPENAI_BASE_URL_HF must both be set "
                    "for the hf-llama target"
                )
            return OpenAI(api_key=api_key, base_url=base_url)

        # anthropic — Anthropic's OpenAI-compat endpoint. The OpenAI SDK
        # appends paths to base_url verbatim, and Anthropic's OpenAI-compat
        # routes live under /v1/, so we normalize the base_url to end with
        # /v1/ regardless of how the user provided ANTHROPIC_BASE_URL.
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise EnvironmentError("ANTHROPIC_API_KEY not set")
        base_url = os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com")
        base_url = base_url.rstrip("/")
        if not base_url.endswith("/v1"):
            base_url = base_url + "/v1"
        return OpenAI(api_key=api_key, base_url=base_url + "/")

    # ── AbstractJudgeProvider properties ──

    @property
    def family(self) -> str:
        return self._family

    @property
    def model(self) -> str:
        return self._model

    @property
    def supports_strict_schema(self) -> bool:
        return self._supports_strict_schema

    # ── judging ──

    async def judge(self, case: dict) -> Judgment:
        return await self._judge_with_retry(case)

    @with_retry()
    async def _judge_with_retry(self, case: dict) -> Judgment:
        """Single-case judgment with retry on transient errors.

        Retry classes per spec §9.2: HTTP 5xx, timeout, 429. The
        @with_retry decorator wraps this method; the inner body raises
        TransientError for retryable failures and the original exception
        otherwise.
        """
        prompt_prefix = build_prompt_static_prefix()
        prompt_case = build_prompt_for_case(case)

        try:
            if self._supports_strict_schema:
                response_text = self._call_strict(prompt_prefix, prompt_case)
            else:
                response_text = self._call_json_mode(prompt_prefix, prompt_case)
        except Exception as e:
            # Convert vendor errors to TransientError where appropriate.
            # The `openai` SDK raises subclasses we can pattern-match;
            # we keep this generic so MockClient errors propagate
            # unchanged.
            if _is_transient(e):
                raise TransientError(str(e)) from e
            raise

        parsed = self._parse_response(response_text)
        return self._build_judgment(case, parsed, raw=parsed)

    def _call_strict(self, prefix: str, case_text: str) -> str:
        """Real OpenAI strict-schema call. Returns the response content."""
        schema = _load_schema()
        if self.target == "anthropic":
            # Anthropic strict-mode is more restrictive than OpenAI's:
            # rejects minimum/maximum/minLength/exclusive*. Strip those
            # before sending; semantic constraints are revalidated post-
            # parse via jsonschema.validate() against the full schema.
            schema = _strip_unsupported_for_anthropic(schema)
        kwargs: dict[str, Any] = {
            "model": self._model,
            "temperature": 0.0,
            "messages": [
                {"role": "system", "content": prefix},
                {"role": "user", "content": case_text},
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "judge_verdict_output",
                    "strict": True,
                    "schema": schema,
                },
            },
        }
        # OpenAI supports `seed`; Anthropic's compat endpoint accepts it
        # but ignores. Keep it everywhere for OpenAI determinism.
        if self.target == "openai":
            kwargs["seed"] = 42
        completion = self._client.chat.completions.create(**kwargs)
        content = completion.choices[0].message.content
        if not content:
            raise RuntimeError("empty response from strict-mode call")
        # When schema was stripped for Anthropic, post-parse validation
        # against the FULL schema enforces the dropped constraints.
        if self.target == "anthropic":
            import json as _json
            import jsonschema
            parsed = _json.loads(content)
            try:
                jsonschema.validate(parsed, _load_schema())
            except jsonschema.ValidationError as e:
                raise RuntimeError(
                    f"Anthropic response failed full-schema validation: {e.message}"
                ) from e
        return content

    def _call_json_mode(self, prefix: str, case_text: str) -> str:
        """HF Endpoints / non-strict JSON-mode call.

        TGI accepts `response_format={'type': 'json_object'}` which hints
        the model to emit JSON but does NOT enforce a schema. Post-call,
        we use the tolerant parser from llm_extractor (spec §7.7).
        """
        completion = self._client.chat.completions.create(
            model=self._model,
            temperature=0.0,
            seed=42,
            messages=[
                {"role": "system", "content": prefix},
                {"role": "user", "content": case_text},
            ],
            response_format={"type": "json_object"},
        )
        content = completion.choices[0].message.content
        if not content:
            raise RuntimeError("empty response from HF Endpoints call")
        return content

    def _parse_response(self, text: str) -> dict:
        """Parse + schema-validate. Strict path is already validated server-side."""
        if self._supports_strict_schema:
            return json.loads(text)

        # HF path: tolerant parser handles brace-drop / fence-strip /
        # prefix-truncation. Reuses the extract eval pattern (spec §7.7).
        from uofa_cli.llm_extractor import _parse_response as tolerant_parse

        try:
            parsed = tolerant_parse(text)
        except ValueError as e:
            raise RuntimeError(f"could not parse HF Llama response: {e}") from e

        # Post-parse schema validation. Lazy-import jsonschema so tests
        # that don't exercise this path don't require the dep.
        import jsonschema

        schema = _load_schema()
        try:
            jsonschema.validate(parsed, schema)
        except jsonschema.ValidationError as e:
            raise RuntimeError(
                f"HF Llama response did not validate against schema: {e.message}"
            ) from e
        return parsed

    def _build_judgment(self, case: dict, parsed: dict, *, raw: dict) -> Judgment:
        """Assemble a Judgment from the parsed response.

        `parsed` already conforms to the schema (either via strict-mode or
        post-parse validation). We trust the field shapes here.
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
            judge_model=parsed.get("judge_model", self._model),
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

    async def calibrate(self, calibration_set: list[dict]) -> CalibrationResult:
        """Run the calibration set; compute per-class accuracy + confusion matrix.

        Skeleton implementation: judges every case, scores against each
        case's `ground_truth_verdict` field. Real Stage 1 calibration
        runs (spec §8) extend this with §7.5 prompt-tuning iteration; for
        Tier A we just need the call shape correct.
        """
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


_ANTHROPIC_UNSUPPORTED_KEYWORDS: tuple[str, ...] = (
    "minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum",
    "minLength", "maxLength", "minItems", "maxItems", "pattern",
)


def _strip_unsupported_for_anthropic(schema: dict) -> dict:
    """Recursively drop keywords Anthropic strict-mode rejects.

    Anthropic's OpenAI-compat endpoint accepts strict JSON schema but
    rejects several JSON Schema 2020-12 keywords (`minimum`, `maximum`,
    `pattern`, etc.) that OpenAI strict-mode allows. We strip those for
    the API call and revalidate the response against the FULL schema
    post-parse so dropped constraints still gate the verdict.
    """
    if isinstance(schema, dict):
        return {
            k: _strip_unsupported_for_anthropic(v)
            for k, v in schema.items()
            if k not in _ANTHROPIC_UNSUPPORTED_KEYWORDS
        }
    if isinstance(schema, list):
        return [_strip_unsupported_for_anthropic(item) for item in schema]
    return schema


def _is_transient(exc: BaseException) -> bool:
    """Best-effort classification of vendor errors as retry-worthy."""
    name = type(exc).__name__.lower()
    if "rate" in name or "timeout" in name or "connection" in name:
        return True
    # OpenAI APIStatusError carries a status_code attribute on real errors.
    code = getattr(exc, "status_code", None)
    if isinstance(code, int) and 500 <= code < 600:
        return True
    return False

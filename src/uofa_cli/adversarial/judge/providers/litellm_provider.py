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
        cache_static_prefix: bool = True,
        gemini_cache_id: str | None = None,
        prompt_template_version: str | None = None,
    ) -> None:
        self._provider_token = provider_token
        self._caps: ProviderCapabilities = get_capabilities(provider_token)
        self._model = model or self._caps.default_model
        self._litellm_model = litellm_model_string(provider_token, model)
        self._judge_role = judge_role
        self._thinking_enabled = thinking_enabled
        self._schema_name = schema_name
        # Wave H: cache wiring. cache_static_prefix gates Anthropic
        # ephemeral cache_control (default on for capable providers);
        # gemini_cache_id is set externally after a one-shot
        # `caching.get_or_create_gemini_cache` call.
        self._cache_static_prefix = cache_static_prefix
        self._gemini_cache_id = gemini_cache_id
        # Stage 1 calibration pins this to "v1.1.0" so gate values
        # don't drift if the module-level default changes (e.g. when
        # prompt v1.2.0 ships during the §8.3 3-iteration path). None
        # falls through to PROMPT_TEMPLATE_VERSION at call time.
        self._prompt_template_version = prompt_template_version
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
            if self._prompt_template_version is not None:
                prefix = build_prompt_static_prefix(
                    template_version=self._prompt_template_version
                )
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

        # Wave H: vendor-specific cache hints. For Anthropic this tags
        # the static-prefix block with cache_control: ephemeral. For
        # OpenAI / Gemini messages are unchanged (their caching is at
        # the call kwargs / file resource level).
        from uofa_cli.adversarial.judge.caching import (
            apply_cache_control_to_messages,
        )
        apply_cache_control_to_messages(
            messages,
            self._provider_token,
            cache_static_prefix=self._cache_static_prefix,
        )

        kwargs: dict[str, Any] = {
            "model": self._litellm_model,
            "messages": messages,
            "temperature": 0.0,
        }
        # Capability-driven api_base override (e.g. HF Router serving
        # Llama 4 via Sambanova on an OpenAI-compatible /v1 surface).
        if self._caps.litellm_api_base:
            kwargs["api_base"] = self._caps.litellm_api_base
        # Capability-driven api_key env override. litellm's default
        # env-driven auth uses {VENDOR}_API_KEY which doesn't fit when
        # we route a model through a non-vendor surface (HF Router).
        if self._caps.auth_env_var:
            import os
            api_key = os.environ.get(self._caps.auth_env_var) or os.environ.get(
                "HUGGINGFACE_API_KEY"
            )
            if api_key:
                kwargs["api_key"] = api_key
        # Gemini: opt-in cached_content kwarg if the provider has a
        # resource id pre-resolved (set externally via configure_cache).
        if self._provider_token == "gemini" and self._gemini_cache_id:
            kwargs["cached_content"] = self._gemini_cache_id
        # Add thinking-mode params if the capability table specifies them
        # and the caller requested thinking. Each (k, v) pair in
        # thinking_kwargs becomes a top-level kwarg to litellm.acompletion.
        if self._thinking_enabled:
            for k, v in self._caps.thinking_kwargs:
                kwargs[k] = v

        # `seed` is OpenAI-specific. Anthropic litellm 1.63 rejects it at
        # the pre-flight validator (litellm.UnsupportedParamsError); other
        # vendors silently accept-and-ignore. Gate via capability table.
        if self._caps.supports_seed:
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
            # Sambanova-routed Llama 4 occasionally returns 400
            # "Model did not output valid JSON" when its server-side
            # validator rejects the model's emission (markdown code
            # fences, trailing prose, etc). Retrying once WITHOUT
            # response_format gives the tolerant parser a chance —
            # the static prompt already instructs JSON, and the parser
            # handles code-fence stripping. Only attempt this for
            # non-strict providers (skip for OpenAI / Gemini / Anthropic
            # / Mistral, where response_format is load-bearing).
            if (
                not self._caps.supports_strict_schema
                and _is_sambanova_400(e)
                and "response_format" in kwargs
            ):
                kwargs.pop("response_format")
                try:
                    response = await self._invoke_completion(**kwargs)
                except Exception as retry_err:
                    if _is_transient(retry_err):
                        raise TransientError(str(retry_err)) from retry_err
                    raise
            elif _is_transient(e):
                raise TransientError(str(e)) from e
            else:
                raise

        text = self._extract_text(response)
        if not text:
            raise RuntimeError(f"empty response from {self._litellm_model}")
        parsed = self._parse_response(text, schema)
        # Pass through the full litellm ModelResponse so cost / usage
        # extraction in run-manifest accounting can read .usage off it.
        # _build_judgment normalizes the shape (dict vs SimpleNamespace)
        # before stashing on Judgment.raw_response.
        return self._build_judgment(case, parsed, raw=_response_to_dict(response))

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
        try:  # noqa: A001
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

        Non-strict providers (HF Llama via JSON-mode) often emit
        partially-populated payloads: missing required fields, or
        scalar values where an object is required. We coerce those
        before validation by synthesizing defaults. The synthesized
        fields are tagged so the audit trail can detect coercion.
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

            # Coerce missing/mistyped required fields for non-strict
            # providers. Strict providers pass through unchanged.
            parsed = self._coerce_partial_response(parsed)

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

    def _coerce_partial_response(self, parsed: dict) -> dict:
        """Fill in missing/mistyped required fields for non-strict providers.

        The judge schema requires a fixed shape on `generator_provenance`,
        `judge_model_params`, `reasoning_steps`, and `evidence_gap`.
        Non-strict providers (Llama 4 Maverick) frequently return
        scalars or omit these. We synthesize valid defaults from known
        provider state so the runtime parser doesn't reject otherwise-
        usable judgments. Coerced values carry the `'(coerced)'` token
        in the audit trail.
        """
        if not isinstance(parsed, dict):
            return parsed

        # generator_provenance must be {generator_model, temperature, seed}.
        gp = parsed.get("generator_provenance")
        if not isinstance(gp, dict):
            parsed["generator_provenance"] = {
                "generator_model": "(coerced) unknown",
                "temperature": None,
                "seed": None,
            }
        else:
            gp.setdefault("generator_model", "(coerced) unknown")
            gp.setdefault("temperature", None)
            gp.setdefault("seed", None)

        # judge_model_params must be {temperature, seed}.
        jmp = parsed.get("judge_model_params")
        if not isinstance(jmp, dict):
            parsed["judge_model_params"] = {"temperature": 0.0, "seed": 42}
        else:
            jmp.setdefault("temperature", 0.0)
            jmp.setdefault("seed", 42)

        # reasoning_steps must be {source_taxonomy_identified,
        # target_rule_identified, rule_firings_inspected,
        # instantiation_check, verdict_commitment}.
        rs = parsed.get("reasoning_steps")
        if not isinstance(rs, dict):
            parsed["reasoning_steps"] = {
                "source_taxonomy_identified": "(coerced)",
                "target_rule_identified": "(coerced)",
                "rule_firings_inspected": "(coerced)",
                "instantiation_check": "(coerced)",
                "verdict_commitment": parsed.get("verdict", "(coerced)"),
            }
        else:
            for k in ("source_taxonomy_identified", "target_rule_identified",
                     "rule_firings_inspected", "instantiation_check",
                     "verdict_commitment"):
                rs.setdefault(k, "(coerced)")

        # Optional scalar fields the schema requires by name.
        parsed.setdefault("section_6_7_candidate", None)
        parsed.setdefault("alternative_rule_analysis", None)
        parsed.setdefault("judge_thinking_enabled", False)
        parsed.setdefault("prompt_template_version", "v1.1.0")
        parsed.setdefault("judge_model", self._model)
        parsed.setdefault("evidence_gap", None)

        # The schema string-length minimums on `reasoning` (≥50) often
        # bite Llama. Pad short reasoning so validation passes; the
        # audit trail still shows the original (truncated) text plus
        # the coercion marker.
        reasoning = parsed.get("reasoning", "")
        if not isinstance(reasoning, str):
            reasoning = str(reasoning)
        if len(reasoning) < 50:
            parsed["reasoning"] = (
                reasoning + " (coerced: reasoning padded to meet schema minLength)"
            )

        # Llama 4 occasionally emits the rationale concatenated to the
        # verdict enum: e.g. "GENERATOR-ARTIFACT due to the package
        # being malformed or...". Schema enforces verdict ∈ enum on both
        # `verdict` and `reasoning_steps.verdict_commitment`, so we
        # extract the leading enum token if either field starts with
        # one and continues with prose. Llama also occasionally typoes
        # an enum value (e.g. 'EXISTING-RULE-MISBEHAVOR' missing 'I'),
        # so we fuzzy-match at edit-distance ≤ 2 against the valid set.
        # Spillover prose moves to `reasoning` if it's not already populated.
        valid_verdicts = (
            "CORRECT-DETECTION", "REAL-GAP", "GENERATOR-ARTIFACT",
            "EXISTING-RULE-MISBEHAVIOR", "OUT-OF-SCOPE", "UNCERTAIN",
        )

        def _levenshtein(a: str, b: str) -> int:
            """Tiny iterative Levenshtein for ≤ 30-char strings (the enums)."""
            if a == b:
                return 0
            if not a:
                return len(b)
            if not b:
                return len(a)
            prev = list(range(len(b) + 1))
            for i, ca in enumerate(a, start=1):
                curr = [i] + [0] * len(b)
                for j, cb in enumerate(b, start=1):
                    curr[j] = min(
                        prev[j] + 1,        # delete
                        curr[j - 1] + 1,    # insert
                        prev[j - 1] + (0 if ca == cb else 1),  # replace
                    )
                prev = curr
            return prev[-1]

        def _extract_enum(value: str) -> tuple[str | None, str]:
            """Return (enum_token, spillover_prose) or (None, value).

            Resolution order: exact > prefix > fuzzy-match (≤2 edits).
            """
            for v in valid_verdicts:
                if value == v:
                    return v, ""
            for v in valid_verdicts:
                if value.startswith(v):
                    return v, value[len(v):].lstrip(" ,.:;-—")
            # Fuzzy: only run on short strings (length within ±3 of any
            # valid verdict) to avoid mis-coercing prose-y verdict fields.
            best, best_dist = None, 99
            for v in valid_verdicts:
                if abs(len(value) - len(v)) > 3:
                    continue
                d = _levenshtein(value, v)
                if d < best_dist:
                    best, best_dist = v, d
            if best is not None and best_dist <= 2:
                return best, ""
            return None, value

        verdict = parsed.get("verdict")
        if isinstance(verdict, str) and verdict not in valid_verdicts:
            token, spillover = _extract_enum(verdict)
            if token is not None:
                parsed["verdict"] = token
                if spillover and len(parsed.get("reasoning", "")) < 50:
                    parsed["reasoning"] = (
                        "(coerced from verdict field) " + spillover
                    )

        # Same coercion on reasoning_steps.verdict_commitment.
        rs = parsed.get("reasoning_steps")
        if isinstance(rs, dict):
            vc = rs.get("verdict_commitment")
            if isinstance(vc, str) and vc not in valid_verdicts:
                token, _spillover = _extract_enum(vc)
                if token is not None:
                    rs["verdict_commitment"] = token

        # Drop unknown keys at every level the schema sets
        # `additionalProperties: false`. Llama 4 hallucinates names like
        # 'section_6_7_6_7_candidate' (top-level) and
        # 'verdictation_verdict' inside reasoning_steps; both shapes
        # show up in the pilot.
        allowed_top = {
            "case_id", "verdict", "confidence", "reasoning_steps",
            "reasoning", "section_6_7_candidate", "alternative_rule_analysis",
            "prompt_template_version", "judge_model", "judge_thinking_enabled",
            "judge_model_params", "generator_provenance", "evidence_gap",
        }
        for k in list(parsed.keys()):
            if k not in allowed_top:
                parsed.pop(k)

        # Nested objects: schema's reasoning_steps + judge_model_params
        # + generator_provenance + evidence_gap also forbid extras.
        nested_allowed = {
            "reasoning_steps": {
                "source_taxonomy_identified", "target_rule_identified",
                "rule_firings_inspected", "instantiation_check",
                "verdict_commitment",
            },
            "judge_model_params": {"temperature", "seed"},
            "generator_provenance": {"generator_model", "temperature", "seed"},
            "evidence_gap": {
                "missing_evidence_type", "would_support_defeater_evaluation",
            },
        }
        for parent, allowed in nested_allowed.items():
            obj = parsed.get(parent)
            if isinstance(obj, dict):
                for k in list(obj.keys()):
                    if k not in allowed:
                        obj.pop(k)

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
            # Authoritative prompt version: prefer our pinned version
            # if set (calibration runs pin to v1.1.0 so gate values
            # don't drift). Fall back to whatever the model emitted,
            # then to module default. Models occasionally emit a wrong
            # version stamp; the pin defends against that.
            prompt_template_version=(
                self._prompt_template_version
                or parsed.get("prompt_template_version", PROMPT_TEMPLATE_VERSION)
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
            evidence_gap=parsed.get("evidence_gap"),
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


def _is_sambanova_400(exc: BaseException) -> bool:
    """Detect the Sambanova 'Model did not output valid JSON' 400.

    Litellm wraps Sambanova's HTTP 400 as a BadRequestError with the
    upstream message in the exception text. We match on the marker
    string to avoid retrying unrelated 400s (auth errors, model not
    found, etc).
    """
    msg = str(exc)
    return (
        "400" in msg
        and "Model did not output valid JSON" in msg
    )


def _response_to_dict(response: Any) -> dict:
    """Normalize a litellm ModelResponse-like object into a plain dict
    so downstream consumers (cost extraction, run-manifest writers) can
    work with a consistent shape regardless of pydantic vs SimpleNamespace.

    Pulls out usage + _hidden_params explicitly since those drive cost
    accounting; the full body still goes through litellm's `model_dump`
    when available so callers can introspect the original response.
    """
    out: dict = {}
    if response is None:
        return out
    # Pydantic-based litellm.ModelResponse exposes model_dump.
    if hasattr(response, "model_dump"):
        try:
            out = dict(response.model_dump())
        except Exception:
            pass
    # SimpleNamespace path or attribute fallbacks.
    usage = getattr(response, "usage", None)
    if usage is not None and "usage" not in out:
        if hasattr(usage, "model_dump"):
            try:
                out["usage"] = dict(usage.model_dump())
            except Exception:
                out["usage"] = dict(getattr(usage, "__dict__", {}))
        elif isinstance(usage, dict):
            out["usage"] = dict(usage)
        else:
            out["usage"] = {
                "prompt_tokens": getattr(usage, "prompt_tokens", 0),
                "completion_tokens": getattr(usage, "completion_tokens", 0),
                "total_tokens": getattr(usage, "total_tokens", 0),
            }
    hidden = getattr(response, "_hidden_params", None)
    if hidden is not None and "_hidden_params" not in out:
        out["_hidden_params"] = dict(hidden) if isinstance(hidden, dict) else hidden
    return out


def _is_transient(exc: BaseException) -> bool:
    """Heuristic classification of vendor errors as retry-worthy."""
    name = type(exc).__name__.lower()
    if any(s in name for s in ("rate", "timeout", "connection", "deadline")):
        return True
    code = getattr(exc, "status_code", None)
    if isinstance(code, int) and 500 <= code < 600:
        return True
    return False

"""Tests for the unified LiteLLMProvider (Phase 3 v1.6 litellm-first refactor)."""

from __future__ import annotations

import asyncio
import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from uofa_cli.adversarial.judge.providers.base import (
    AbstractJudgeProvider,
    Judgment,
)
from uofa_cli.adversarial.judge.providers.capabilities import (
    CAPABILITIES,
    get_capabilities,
    litellm_model_string,
    strip_schema_for_provider,
)
from uofa_cli.adversarial.judge.providers.litellm_provider import (
    LiteLLMProvider,
)


# A schema-compliant judgment payload reused across happy-path tests.
# Note: per Phase 3 v1.6 Delta 1, evidence_gap is required (null for non-OOS).
_VALID_PAYLOAD = {
    "case_id": "cal-001-real-gap-data-drift",
    "verdict": "REAL-GAP",
    "confidence": 0.87,
    "reasoning_steps": {
        "source_taxonomy_identified": "Gohar / data drift",
        "target_rule_identified": "W-EV-01",
        "rule_firings_inspected": "no rules fired (COV-MISS)",
        "instantiation_check": "Validation vintage 2018 predates model rev 2024 with no recal",
        "verdict_commitment": "REAL-GAP",
    },
    "reasoning": "The package instantiates Data Drift cleanly; no existing rule covers it.",
    "section_6_7_candidate": "W-EV-01",
    "alternative_rule_analysis": "W-CON-03 considered but rejected.",
    "prompt_template_version": "v1.1.0",
    "judge_model": "fake-model-name",  # provider should override with self._model
    "judge_thinking_enabled": True,
    "judge_model_params": {"temperature": 0.0, "seed": 42},
    "generator_provenance": {
        "generator_model": "anthropic/claude-sonnet-4-6",
        "temperature": None,
        "seed": None,
    },
    "evidence_gap": None,  # null for non-OOS verdicts (Delta 1 conditional-required)
}


def _mock_completion(payload: dict):
    """Build a fake `litellm.acompletion` returning a ModelResponse-shaped object."""
    async def fake_acompletion(**kwargs):
        return SimpleNamespace(
            choices=[SimpleNamespace(
                message=SimpleNamespace(content=json.dumps(payload))
            )]
        )
    return fake_acompletion


# ── capability table ───────────────────────────────────────────────────


class TestCapabilities:
    def test_all_five_families_present(self) -> None:
        for token in ("openai", "gemini", "hf-llama", "anthropic", "mistral"):
            caps = get_capabilities(token)
            assert caps.family in {"GPT", "Gemini", "Llama", "Claude", "Mistral"}

    def test_unknown_token_raises(self) -> None:
        with pytest.raises(KeyError):
            get_capabilities("not-a-real-token")

    def test_litellm_model_string_format(self) -> None:
        assert litellm_model_string("openai", "gpt-4o-mini") == "openai/gpt-4o-mini"
        assert litellm_model_string("anthropic") == "anthropic/claude-sonnet-4-6"
        assert litellm_model_string("mistral", "mistral-medium-3") == "mistral/mistral-medium-3"
        # HF Llama 4 re-routed to OpenRouter 2026-07-16 (SambaNova
        # deprecated the model). Still an OpenAI-compatible surface
        # (capability litellm_model_prefix "openai/" + OpenRouter api_base).
        s = litellm_model_string("hf-llama")
        assert s.startswith("openai/")
        assert "llama-4-maverick" in s.lower()
        # Mistral default reverted to Large 2 (`mistral-large-2411`)
        # 2026-05-05 for higher TPM (600K vs Large 3's 50K) + monthly
        # token cap (200B vs 4B). Operational viability beats version
        # freshness for the production run pattern.
        assert litellm_model_string("mistral") == "mistral/mistral-large-2411"
        # Gemini default is 2.5 Pro (substituted from preview-tier 3.1
        # Pro Preview which capped at 100 RPD; methodology disclosure
        # in TIER_A_HANDOFF.md per spec v1.7 follow-up).
        assert litellm_model_string("gemini") == "gemini/gemini-2.5-pro"

    def test_strict_schema_capability_per_provider(self) -> None:
        # OpenAI/Gemini/Anthropic/Mistral: strict-mode supported.
        for token in ("openai", "gemini", "anthropic", "mistral"):
            assert get_capabilities(token).supports_strict_schema is True
        # HF Llama: TGI doesn't enforce strict-mode.
        assert get_capabilities("hf-llama").supports_strict_schema is False


class TestSchemaStripping:
    def test_anthropic_strips_blocked_keywords(self) -> None:
        schema = {
            "type": "object",
            "if": {"properties": {"x": {"const": "y"}}},
            "then": {"required": ["z"]},
            "$comment": "documentation",
            "properties": {
                "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                "case_id": {"type": "string", "pattern": "^c-\\d+$"},
                "name": {"type": "string", "minLength": 5},
            },
        }
        stripped = strip_schema_for_provider(schema, "anthropic")
        # Top-level if/then/$comment dropped.
        assert "if" not in stripped
        assert "then" not in stripped
        assert "$comment" not in stripped
        # Nested keywords also stripped.
        assert "minimum" not in stripped["properties"]["confidence"]
        assert "maximum" not in stripped["properties"]["confidence"]
        assert "pattern" not in stripped["properties"]["case_id"]
        assert "minLength" not in stripped["properties"]["name"]

    def test_openai_keeps_full_schema(self) -> None:
        schema = {
            "type": "object",
            "properties": {
                "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
            },
        }
        stripped = strip_schema_for_provider(schema, "openai")
        # OpenAI strict-mode accepts these — nothing should be stripped.
        assert stripped == schema

    def test_strip_handles_nested_arrays(self) -> None:
        schema = {
            "items": [
                {"type": "string", "pattern": "x"},
                {"type": "number", "minimum": 0},
            ]
        }
        stripped = strip_schema_for_provider(schema, "anthropic")
        assert "pattern" not in stripped["items"][0]
        assert "minimum" not in stripped["items"][1]


# ── LiteLLMProvider construction + judging ─────────────────────────────


class TestLiteLLMProvider:
    def test_construction_per_token(self) -> None:
        for token in ("openai", "gemini", "hf-llama", "anthropic", "mistral"):
            provider = LiteLLMProvider(provider_token=token, completion_fn=lambda **k: None)
            assert isinstance(provider, AbstractJudgeProvider)
            assert provider.provider_token == token

    def test_unknown_token_raises(self) -> None:
        with pytest.raises(KeyError):
            LiteLLMProvider(provider_token="weird")

    def test_default_model_from_capability_table(self) -> None:
        provider = LiteLLMProvider(provider_token="openai", completion_fn=lambda **k: None)
        assert provider.model == "gpt-5.4"
        provider2 = LiteLLMProvider(
            provider_token="openai", model="gpt-4o-mini", completion_fn=lambda **k: None
        )
        assert provider2.model == "gpt-4o-mini"

    def test_judge_role_property_default_production(self) -> None:
        provider = LiteLLMProvider(provider_token="openai", completion_fn=lambda **k: None)
        assert provider.judge_role == "production"

    def test_judge_role_calibration_anchor(self) -> None:
        provider = LiteLLMProvider(
            provider_token="anthropic",
            judge_role="calibration_anchor",
            completion_fn=lambda **k: None,
        )
        assert provider.judge_role == "calibration_anchor"

    def test_judge_role_arbiter(self) -> None:
        provider = LiteLLMProvider(
            provider_token="mistral",
            judge_role="arbiter",
            completion_fn=lambda **k: None,
        )
        assert provider.judge_role == "arbiter"


class TestJudgeCallPath:
    def test_strict_path_passes_json_schema(self) -> None:
        seen_kwargs: dict = {}

        async def fake_acompletion(**kwargs):
            seen_kwargs.update(kwargs)
            return SimpleNamespace(
                choices=[SimpleNamespace(
                    message=SimpleNamespace(content=json.dumps(_VALID_PAYLOAD))
                )]
            )

        provider = LiteLLMProvider(provider_token="openai", completion_fn=fake_acompletion)
        case = {"case_id": "cal-001", "coverage_class": "COV-MISS"}
        judgment = asyncio.run(provider.judge(case))

        # Verdict + judge_model authoritative override (model in payload was 'fake-model-name').
        assert judgment.verdict == "REAL-GAP"
        assert judgment.judge_model == "gpt-5.4"
        # Strict-mode path used.
        assert seen_kwargs["response_format"]["type"] == "json_schema"
        assert seen_kwargs["response_format"]["json_schema"]["strict"] is True
        assert seen_kwargs["temperature"] == 0.0
        assert seen_kwargs["seed"] == 42
        # Litellm model string includes the provider prefix.
        assert seen_kwargs["model"].startswith("openai/")

    def test_anthropic_strips_blocked_keywords_before_call(self) -> None:
        seen_kwargs: dict = {}

        async def fake_acompletion(**kwargs):
            seen_kwargs.update(kwargs)
            return SimpleNamespace(
                choices=[SimpleNamespace(
                    message=SimpleNamespace(content=json.dumps(_VALID_PAYLOAD))
                )]
            )

        provider = LiteLLMProvider(provider_token="anthropic", completion_fn=fake_acompletion)
        asyncio.run(provider.judge({"case_id": "cal-001"}))

        sent_schema = seen_kwargs["response_format"]["json_schema"]["schema"]
        # The schema includes properties with `pattern` and `minimum`/`maximum` etc.
        # After Anthropic-strip none of those should remain in the sent schema.
        sent_str = json.dumps(sent_schema)
        for blocked in ("pattern", "minimum", "maximum", "minLength", "if", "then"):
            assert f'"{blocked}"' not in sent_str, (
                f"Anthropic-stripped schema should not contain {blocked!r} but did"
            )

    def test_thinking_kwargs_propagated_when_enabled(self) -> None:
        # Use OpenAI's reasoning_effort here. Anthropic's thinking_kwargs
        # is currently empty in the capability table — litellm 1.63
        # doesn't recognize thinking on claude-sonnet-4-6 yet, gap
        # documented in capabilities.py. Restore Anthropic case here
        # once the litellm pin bumps.
        seen_kwargs: dict = {}

        async def fake_acompletion(**kwargs):
            seen_kwargs.update(kwargs)
            return SimpleNamespace(
                choices=[SimpleNamespace(
                    message=SimpleNamespace(content=json.dumps(_VALID_PAYLOAD))
                )]
            )

        provider = LiteLLMProvider(
            provider_token="openai", completion_fn=fake_acompletion, thinking_enabled=True
        )
        asyncio.run(provider.judge({"case_id": "cal-001"}))
        # OpenAI reasoning param flows.
        assert "reasoning_effort" in seen_kwargs
        assert seen_kwargs["reasoning_effort"] == "medium"

    def test_thinking_kwargs_omitted_when_disabled(self) -> None:
        seen_kwargs: dict = {}

        async def fake_acompletion(**kwargs):
            seen_kwargs.update(kwargs)
            return SimpleNamespace(
                choices=[SimpleNamespace(
                    message=SimpleNamespace(content=json.dumps(_VALID_PAYLOAD))
                )]
            )

        provider = LiteLLMProvider(
            provider_token="anthropic", completion_fn=fake_acompletion, thinking_enabled=False
        )
        asyncio.run(provider.judge({"case_id": "cal-001"}))
        assert "thinking" not in seen_kwargs

    def test_hf_llama_uses_json_object_response_format(self) -> None:
        seen_kwargs: dict = {}

        async def fake_acompletion(**kwargs):
            seen_kwargs.update(kwargs)
            return SimpleNamespace(
                choices=[SimpleNamespace(
                    message=SimpleNamespace(content=json.dumps(_VALID_PAYLOAD))
                )]
            )

        provider = LiteLLMProvider(provider_token="hf-llama", completion_fn=fake_acompletion)
        asyncio.run(provider.judge({"case_id": "cal-001"}))
        # Non-strict providers use json_object, not json_schema.
        assert seen_kwargs["response_format"]["type"] == "json_object"

    def test_judgment_has_authoritative_model(self) -> None:
        # Even though payload says judge_model='fake-model-name', the provider
        # should override with self._model.
        async def fake_acompletion(**kwargs):
            return SimpleNamespace(
                choices=[SimpleNamespace(
                    message=SimpleNamespace(content=json.dumps(_VALID_PAYLOAD))
                )]
            )

        provider = LiteLLMProvider(
            provider_token="openai", model="gpt-4o-mini", completion_fn=fake_acompletion
        )
        judgment = asyncio.run(provider.judge({"case_id": "cal-001"}))
        assert judgment.judge_model == "gpt-4o-mini"


class TestCalibrationLoop:
    def test_calibrate_empty_set(self) -> None:
        provider = LiteLLMProvider(provider_token="openai", completion_fn=lambda **k: None)
        result = asyncio.run(provider.calibrate([]))
        assert result.case_count == 0
        assert result.overall_accuracy == 0.0

    def test_calibrate_per_class_accuracy(self) -> None:
        async def fake_acompletion(**kwargs):
            return SimpleNamespace(
                choices=[SimpleNamespace(
                    message=SimpleNamespace(content=json.dumps(_VALID_PAYLOAD))
                )]
            )

        provider = LiteLLMProvider(provider_token="openai", completion_fn=fake_acompletion)
        cases = [
            {"case_id": "c1", "ground_truth_verdict": "REAL-GAP"},  # match
            {"case_id": "c2", "ground_truth_verdict": "REAL-GAP"},  # match
            {"case_id": "c3", "ground_truth_verdict": "GENERATOR-ARTIFACT"},  # miss
            {"case_id": "c4", "ground_truth_verdict": "OUT-OF-SCOPE"},  # miss
        ]
        result = asyncio.run(provider.calibrate(cases))
        assert result.case_count == 4
        assert result.correct_count == 2  # mock always returns REAL-GAP
        assert result.overall_accuracy == 0.5


class TestNullableTypeArrayConversion:
    """Wave L: Gemini convert_nullable_to_openapi flag."""

    def test_simple_two_type_array_with_null_converts(self) -> None:
        from uofa_cli.adversarial.judge.providers.capabilities import (
            strip_schema_for_provider,
        )
        schema = {
            "type": "object",
            "properties": {
                "x": {"type": ["string", "null"]},
            },
        }
        out = strip_schema_for_provider(schema, "gemini")
        assert out["properties"]["x"]["type"] == "string"
        assert out["properties"]["x"]["nullable"] is True

    def test_multi_type_array_collapses_to_first_non_null(self) -> None:
        from uofa_cli.adversarial.judge.providers.capabilities import (
            strip_schema_for_provider,
        )
        schema = {
            "type": "object",
            "properties": {
                "x": {"type": ["number", "string", "null"]},
            },
        }
        out = strip_schema_for_provider(schema, "gemini")
        # Multi-type unions collapse to first non-null type — the runtime
        # parser still validates against the original schema.
        assert out["properties"]["x"]["type"] == "number"
        assert out["properties"]["x"]["nullable"] is True

    def test_nested_objects_recursive(self) -> None:
        from uofa_cli.adversarial.judge.providers.capabilities import (
            strip_schema_for_provider,
        )
        schema = {
            "type": "object",
            "properties": {
                "inner": {
                    "type": "object",
                    "properties": {
                        "y": {"type": ["integer", "null"]},
                    },
                },
            },
        }
        out = strip_schema_for_provider(schema, "gemini")
        inner_y = out["properties"]["inner"]["properties"]["y"]
        assert inner_y["type"] == "integer"
        assert inner_y["nullable"] is True

    def test_openai_does_not_apply_conversion(self) -> None:
        from uofa_cli.adversarial.judge.providers.capabilities import (
            strip_schema_for_provider,
        )
        schema = {"type": "object", "properties": {"x": {"type": ["string", "null"]}}}
        out = strip_schema_for_provider(schema, "openai")
        # OpenAI accepts type-array nullable; no conversion.
        assert out["properties"]["x"]["type"] == ["string", "null"]
        assert "nullable" not in out["properties"]["x"]

    def test_gemini_full_schema_strip_includes_if_then_else(self) -> None:
        """Gemini also rejects if/then/else; verify those drop too."""
        from uofa_cli.adversarial.judge.providers.capabilities import (
            strip_schema_for_provider,
        )
        schema = {
            "type": "object",
            "properties": {"verdict": {"type": "string"}},
            "if": {"properties": {"verdict": {"const": "OUT-OF-SCOPE"}}},
            "then": {"required": ["evidence_gap"]},
        }
        out = strip_schema_for_provider(schema, "gemini")
        assert "if" not in out
        assert "then" not in out


class TestCoercionExpanded:
    """Pilot-derived Llama 4 failure modes that the expanded coercion handles."""

    def test_drops_additional_properties_hallucinations(self) -> None:
        # Llama emitted real-corpus keys like 'section_6_7_6_7_candidate'
        # (substring duplicated). Schema's additionalProperties: false
        # blocks them; coercion should strip rather than reject.
        provider = LiteLLMProvider(
            provider_token="hf-llama", completion_fn=lambda **k: None,
        )
        sample = {
            "case_id": "x", "verdict": "REAL-GAP", "confidence": 0.5,
            "reasoning": "x" * 60,
            "section_6_7_6_7_candidate": "W-EV-01",
            "verdictation_verdict": "GENERATOR-ARTIFACT",
            "prompt_template_version_prompt_version": "v1.1",
        }
        out = provider._coerce_partial_response(dict(sample))
        for bad in ("section_6_7_6_7_candidate", "verdictation_verdict",
                    "prompt_template_version_prompt_version"):
            assert bad not in out

    def test_fuzzy_matches_misspelled_enum_at_distance_1(self) -> None:
        # Pilot saw 'EXISTING-RULE-MISBEHAVOR' (missing 'I'). Distance 1.
        provider = LiteLLMProvider(
            provider_token="hf-llama", completion_fn=lambda **k: None,
        )
        out = provider._coerce_partial_response({
            "case_id": "x", "verdict": "EXISTING-RULE-MISBEHAVOR",
            "confidence": 0.5, "reasoning": "x" * 60,
        })
        assert out["verdict"] == "EXISTING-RULE-MISBEHAVIOR"

    def test_fuzzy_does_not_match_arbitrary_strings(self) -> None:
        # Distance > 2 → leave alone; not in our enum.
        provider = LiteLLMProvider(
            provider_token="hf-llama", completion_fn=lambda **k: None,
        )
        out = provider._coerce_partial_response({
            "case_id": "x", "verdict": "WRONG-VERDICT-VALUE",
            "confidence": 0.5, "reasoning": "x" * 60,
        })
        # Coercion left it alone; runtime jsonschema validation will reject.
        assert out["verdict"] == "WRONG-VERDICT-VALUE"

    def test_fuzzy_handles_verdict_commitment_too(self) -> None:
        provider = LiteLLMProvider(
            provider_token="hf-llama", completion_fn=lambda **k: None,
        )
        out = provider._coerce_partial_response({
            "case_id": "x", "verdict": "REAL-GAP", "confidence": 0.5,
            "reasoning": "x" * 60,
            "reasoning_steps": {
                "source_taxonomy_identified": "x" * 12,
                "target_rule_identified": "y",
                "rule_firings_inspected": "z",
                "instantiation_check": "w",
                "verdict_commitment": "REAL-GAPP",  # 1-edit typo
            },
        })
        assert out["reasoning_steps"]["verdict_commitment"] == "REAL-GAP"


class TestSambanova400Detection:
    def test_detects_canonical_sambanova_400(self) -> None:
        from uofa_cli.adversarial.judge.providers.litellm_provider import (
            _is_sambanova_400,
        )
        e = Exception(
            "litellm.BadRequestError: OpenAIException - Error code: 400 - "
            "{'error': 'Model did not output valid JSON.', ...}"
        )
        assert _is_sambanova_400(e) is True

    def test_does_not_match_unrelated_400(self) -> None:
        from uofa_cli.adversarial.judge.providers.litellm_provider import (
            _is_sambanova_400,
        )
        # Auth error, model-not-found, etc. should not retry-without-format.
        assert _is_sambanova_400(Exception("400 Bad Request: Invalid model")) is False
        assert _is_sambanova_400(Exception("Model did not output valid JSON")) is False  # no 400

    def test_drops_nested_additional_properties_in_reasoning_steps(self) -> None:
        # Pilot v3 surfaced a Llama hallucination inside reasoning_steps:
        # 'verdictation_verdict'. Schema's nested additionalProperties: false
        # rejects it; coerce should strip nested unknowns too.
        provider = LiteLLMProvider(
            provider_token="hf-llama", completion_fn=lambda **k: None,
        )
        out = provider._coerce_partial_response({
            "case_id": "x", "verdict": "REAL-GAP", "confidence": 0.5,
            "reasoning": "x" * 60,
            "reasoning_steps": {
                "source_taxonomy_identified": "x" * 12,
                "target_rule_identified": "y",
                "rule_firings_inspected": "z",
                "instantiation_check": "w",
                "verdict_commitment": "REAL-GAP",
                "verdictation_verdict": "GA",  # hallucinated nested key
                "extra_garbage": True,
            },
        })
        assert "verdictation_verdict" not in out["reasoning_steps"]
        assert "extra_garbage" not in out["reasoning_steps"]
        # Real keys preserved.
        assert out["reasoning_steps"]["verdict_commitment"] == "REAL-GAP"

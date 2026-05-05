"""Tests for OpenAICompatProvider + GeminiProvider with mocked clients."""

from __future__ import annotations

import asyncio
import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from uofa_cli.adversarial.judge.providers.base import (
    AbstractJudgeProvider,
    CalibrationResult,
    Judgment,
)
from uofa_cli.adversarial.judge.providers.gemini import GeminiProvider
from uofa_cli.adversarial.judge.providers.openai_compat import (
    OpenAICompatProvider,
)


# A schema-compliant judgment payload reused across happy-path tests.
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
    "prompt_template_version": "v0.0.0-stub",
    "judge_model": "gpt-4o",
    "judge_thinking_enabled": True,
    "judge_model_params": {"temperature": 0.0, "seed": 42},
    "generator_provenance": {
        "generator_model": "anthropic/claude-sonnet-4-6",
        "temperature": None,
        "seed": None,
    },
}


def _mock_openai_client(payload: dict) -> MagicMock:
    """Mock the openai.OpenAI client to return `payload` from the chat call."""
    client = MagicMock()
    completion = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps(payload)))]
    )
    client.chat.completions.create.return_value = completion
    return client


def _mock_gemini_client(payload: dict) -> MagicMock:
    """Mock the google-generativeai GenerativeModel."""
    client = MagicMock()
    response = SimpleNamespace(text=json.dumps(payload))
    client.generate_content.return_value = response
    return client


# ── OpenAICompatProvider — openai target ───────────────────────────────


class TestOpenAITarget:
    def test_construction_with_mock_client(self) -> None:
        provider = OpenAICompatProvider(target="openai", client=MagicMock())
        assert provider.target == "openai"
        assert provider.family == "GPT"
        assert provider.supports_strict_schema is True
        assert provider.model == "gpt-5.4"  # default

    def test_unknown_target_raises(self) -> None:
        with pytest.raises(ValueError, match="unknown target"):
            OpenAICompatProvider(target="weird", client=MagicMock())

    def test_judge_returns_judgment(self) -> None:
        client = _mock_openai_client(_VALID_PAYLOAD)
        provider = OpenAICompatProvider(target="openai", client=client)
        case = {"case_id": "cal-001", "coverage_class": "COV-MISS"}
        judgment = asyncio.run(provider.judge(case))
        assert isinstance(judgment, Judgment)
        assert judgment.verdict == "REAL-GAP"
        assert judgment.confidence == 0.87
        assert judgment.case_id == "cal-001-real-gap-data-drift"

    def test_strict_call_uses_response_format_json_schema(self) -> None:
        client = _mock_openai_client(_VALID_PAYLOAD)
        provider = OpenAICompatProvider(target="openai", client=client)
        asyncio.run(provider.judge({"case_id": "cal-001"}))
        kwargs = client.chat.completions.create.call_args.kwargs
        assert kwargs["response_format"]["type"] == "json_schema"
        assert kwargs["response_format"]["json_schema"]["strict"] is True
        assert kwargs["temperature"] == 0.0
        assert kwargs["seed"] == 42

    def test_calibrate_returns_per_class_accuracy(self) -> None:
        # Mock returns the same payload every call. Construct a calibration
        # set where ground truth varies — accuracy should reflect mismatches.
        client = _mock_openai_client(_VALID_PAYLOAD)
        provider = OpenAICompatProvider(target="openai", client=client)
        cases = [
            {"case_id": "c1", "ground_truth_verdict": "REAL-GAP"},
            {"case_id": "c2", "ground_truth_verdict": "REAL-GAP"},
            {"case_id": "c3", "ground_truth_verdict": "GENERATOR-ARTIFACT"},
            {"case_id": "c4", "ground_truth_verdict": "OUT-OF-SCOPE"},
        ]
        result = asyncio.run(provider.calibrate(cases))
        assert isinstance(result, CalibrationResult)
        # Mock always returns REAL-GAP → 2/4 correct.
        assert result.case_count == 4
        assert result.correct_count == 2
        assert result.overall_accuracy == 0.5
        assert result.per_class_accuracy["REAL-GAP"] == 1.0
        assert result.per_class_accuracy["GENERATOR-ARTIFACT"] == 0.0

    def test_empty_calibration_set(self) -> None:
        provider = OpenAICompatProvider(target="openai", client=MagicMock())
        result = asyncio.run(provider.calibrate([]))
        assert result.case_count == 0
        assert result.overall_accuracy == 0.0


# ── OpenAICompatProvider — hf-llama target ─────────────────────────────


class TestHFLlamaTarget:
    def test_construction_with_mock_client(self) -> None:
        provider = OpenAICompatProvider(target="hf-llama", client=MagicMock())
        assert provider.target == "hf-llama"
        assert provider.family == "Llama"
        assert provider.supports_strict_schema is False
        assert "Llama-3.3" in provider.model  # default

    def test_judge_uses_json_object_response_format(self) -> None:
        client = _mock_openai_client(_VALID_PAYLOAD)
        provider = OpenAICompatProvider(target="hf-llama", client=client)
        asyncio.run(provider.judge({"case_id": "cal-001"}))
        kwargs = client.chat.completions.create.call_args.kwargs
        # HF path uses json_object (no strict schema), per spec §7.7.
        assert kwargs["response_format"]["type"] == "json_object"

    def test_judge_returns_valid_judgment_through_tolerant_parser(self) -> None:
        # Mock returns the schema-valid payload as JSON; tolerant parser
        # accepts it (degrades gracefully on malformed input, but here
        # input is well-formed).
        client = _mock_openai_client(_VALID_PAYLOAD)
        provider = OpenAICompatProvider(target="hf-llama", client=client)
        judgment = asyncio.run(provider.judge({"case_id": "cal-001"}))
        assert judgment.verdict == "REAL-GAP"


# ── GeminiProvider ──────────────────────────────────────────────────────


class TestGeminiProvider:
    def test_construction_with_mock_client(self) -> None:
        provider = GeminiProvider(client=MagicMock())
        assert provider.family == "Gemini"
        assert provider.supports_strict_schema is True
        assert provider.model == "gemini-3.1-pro"

    def test_judge_returns_judgment(self) -> None:
        client = _mock_gemini_client(_VALID_PAYLOAD)
        provider = GeminiProvider(client=client)
        judgment = asyncio.run(provider.judge({"case_id": "cal-001"}))
        assert isinstance(judgment, Judgment)
        assert judgment.verdict == "REAL-GAP"

    def test_uses_response_mime_type_and_schema(self) -> None:
        client = _mock_gemini_client(_VALID_PAYLOAD)
        provider = GeminiProvider(client=client)
        asyncio.run(provider.judge({"case_id": "cal-001"}))
        kwargs = client.generate_content.call_args.kwargs
        config = kwargs["generation_config"]
        assert config["response_mime_type"] == "application/json"
        assert "response_schema" in config
        assert config["temperature"] == 0.0


# ── ABC conformance ─────────────────────────────────────────────────────


class TestProvidersAreAbstractJudgeProviders:
    def test_openai_compat_is_judge_provider(self) -> None:
        provider = OpenAICompatProvider(target="openai", client=MagicMock())
        assert isinstance(provider, AbstractJudgeProvider)

    def test_gemini_is_judge_provider(self) -> None:
        provider = GeminiProvider(client=MagicMock())
        assert isinstance(provider, AbstractJudgeProvider)

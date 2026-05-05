"""Tests for the batch dispatch layer (Wave G: litellm-backed, mocked at the litellm boundary)."""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from uofa_cli.adversarial.judge.batch import (
    BatchHandle,
    BatchNotSupported,
    BatchResult,
    BatchStatus,
    _coerce_status,
    _dict_to_judgment,
    _parse_batch_jsonl_responses,
    _submit_anthropic_batch,
    _reassemble_anthropic,
    poll_batch,
    reassemble_batch,
    submit_batch,
)
from uofa_cli.adversarial.judge.providers.litellm_provider import LiteLLMProvider


def _provider(token: str) -> LiteLLMProvider:
    """Build a LiteLLMProvider with a no-op completion_fn (batch tests never call it)."""
    return LiteLLMProvider(
        provider_token=token,
        completion_fn=lambda **k: None,
    )


# Canonical batch-line response payload (passes our judge schema).
_VALID_RESPONSE_PAYLOAD = {
    "case_id": "c1",
    "verdict": "REAL-GAP",
    "confidence": 0.85,
    "reasoning_steps": {
        "source_taxonomy_identified": "x",
        "target_rule_identified": "x",
        "rule_firings_inspected": "x",
        "instantiation_check": "x",
        "verdict_commitment": "REAL-GAP",
    },
    "reasoning": "x" * 50,
    "section_6_7_candidate": None,
    "alternative_rule_analysis": None,
    "prompt_template_version": "v1.1.0",
    "judge_thinking_enabled": False,
    "judge_model_params": {"temperature": 0.0, "seed": 42},
    "generator_provenance": {
        "generator_model": "openai/gpt-4o", "temperature": None, "seed": None,
    },
}


# ── status coercion ─────────────────────────────────────────────────────


class TestCoerceStatus:
    @pytest.mark.parametrize(
        ("vendor_str", "expected"),
        [
            ("validating", BatchStatus.IN_PROGRESS),
            ("in_progress", BatchStatus.IN_PROGRESS),
            ("running", BatchStatus.IN_PROGRESS),
            ("active", BatchStatus.IN_PROGRESS),
            ("completed", BatchStatus.COMPLETED),
            ("succeeded", BatchStatus.COMPLETED),
            ("done", BatchStatus.COMPLETED),
            ("failed", BatchStatus.FAILED),
            ("expired", BatchStatus.FAILED),
            ("cancelled", BatchStatus.CANCELLED),
            ("canceled", BatchStatus.CANCELLED),
            ("queued", BatchStatus.PENDING),  # unknown → pending
            ("PENDING", BatchStatus.PENDING),  # case-insensitive
        ],
    )
    def test_coerce(self, vendor_str: str, expected: BatchStatus) -> None:
        assert _coerce_status(vendor_str) == expected


# ── HF Llama refuses batch (per spec §6.7) ──────────────────────────────


class TestHFLlamaNotBatchable:
    def test_submit_batch_raises_for_hf_llama(self) -> None:
        provider = _provider("hf-llama")
        with pytest.raises(BatchNotSupported, match="HF Endpoints"):
            submit_batch(provider, [{"case_id": "c1"}])


# ── Mistral has no batch API (per spec §6.7) ────────────────────────────


class TestMistralNotBatchable:
    def test_submit_batch_raises_for_mistral(self) -> None:
        provider = _provider("mistral")
        with pytest.raises(BatchNotSupported, match="Mistral"):
            submit_batch(provider, [{"case_id": "c1"}])


# ── OpenAI batch happy path (Wave G) ────────────────────────────────────


class TestOpenAIBatchHappyPath:
    def test_submit_creates_file_and_batch(self) -> None:
        provider = _provider("openai")
        case = {
            "case_id": "c1",
            "package": {"id": "pkg-c1"},
            "rules_fired": [],
        }
        upload_obj = SimpleNamespace(id="file-abc")
        batch_obj = SimpleNamespace(id="batch-xyz")
        with patch("litellm.create_file", return_value=upload_obj) as create_file, \
             patch("litellm.create_batch", return_value=batch_obj) as create_batch:
            handle = submit_batch(provider, [case])
        assert handle.vendor == "openai"
        assert handle.batch_id == "batch-xyz"
        assert handle.case_count == 1
        assert handle.case_id_order == ("c1",)
        assert handle.input_file_id == "file-abc"
        create_file.assert_called_once()
        create_batch.assert_called_once()

    def test_poll_normalizes_status(self) -> None:
        provider = _provider("openai")
        handle = BatchHandle(
            vendor="openai", batch_id="b1", case_count=1, case_id_order=("c1",)
        )
        with patch(
            "litellm.retrieve_batch",
            return_value=SimpleNamespace(status="in_progress"),
        ):
            assert poll_batch(provider, handle) == BatchStatus.IN_PROGRESS

    def test_reassemble_parses_jsonl_output(self) -> None:
        provider = _provider("openai")
        handle = BatchHandle(
            vendor="openai", batch_id="b1", case_count=1, case_id_order=("c1",)
        )
        out_line = {
            "custom_id": "c1",
            "response": {
                "body": {
                    "choices": [
                        {"message": {"content": json.dumps(_VALID_RESPONSE_PAYLOAD)}}
                    ]
                }
            },
        }
        with patch(
            "litellm.retrieve_batch",
            return_value=SimpleNamespace(
                status="completed", output_file_id="file-out"
            ),
        ), patch(
            "litellm.file_content",
            return_value=SimpleNamespace(text=json.dumps(out_line) + "\n"),
        ):
            result = reassemble_batch(provider, handle)
        assert result.status == BatchStatus.COMPLETED
        assert len(result.judgments) == 1
        assert result.judgments[0].case_id == "c1"
        assert result.judgments[0].verdict == "REAL-GAP"
        assert result.failed_case_ids == []

    def test_reassemble_collects_failed_case_ids_on_malformed_output(self) -> None:
        provider = _provider("openai")
        handle = BatchHandle(
            vendor="openai", batch_id="b1", case_count=2,
            case_id_order=("c1", "c2"),
        )
        bad_line = {"custom_id": "c1", "response": {"body": {"choices": []}}}
        good_line = {
            "custom_id": "c2",
            "response": {
                "body": {
                    "choices": [
                        {"message": {"content": json.dumps({
                            **_VALID_RESPONSE_PAYLOAD, "case_id": "c2"
                        })}}
                    ]
                }
            },
        }
        with patch(
            "litellm.retrieve_batch",
            return_value=SimpleNamespace(
                status="completed", output_file_id="file-out"
            ),
        ), patch(
            "litellm.file_content",
            return_value=SimpleNamespace(
                text="\n".join([json.dumps(bad_line), json.dumps(good_line)])
            ),
        ):
            result = reassemble_batch(provider, handle)
        assert "c1" in result.failed_case_ids
        assert len(result.judgments) == 1
        assert result.judgments[0].case_id == "c2"


# ── Anthropic batch happy path (Wave G) ─────────────────────────────────


class TestAnthropicNotBatchableByDefault:
    """Per capabilities.py: Anthropic batch is gated OFF until litellm
    matures (gemini same story). The `submit_batch` dispatch refuses;
    callers fall back to synchronous + --parallel."""

    def test_submit_anthropic_falls_back(self) -> None:
        provider = _provider("anthropic")
        with pytest.raises(BatchNotSupported, match="not configured for batch"):
            submit_batch(provider, [{"case_id": "c1"}])

    def test_submit_gemini_falls_back(self) -> None:
        provider = _provider("gemini")
        with pytest.raises(BatchNotSupported, match="not configured for batch"):
            submit_batch(provider, [{"case_id": "c1"}])


class TestAnthropicBatchInternalWiring:
    """Direct calls into the vendor helpers prove the litellm wiring is
    correct so that flipping `supports_batch_api=True` later is just a
    capability-table change, no code change."""

    def test_submit_uses_inline_requests(self) -> None:
        provider = _provider("anthropic")
        cases = [{"case_id": "c1", "package": {}, "rules_fired": []}]
        batch_obj = SimpleNamespace(id="msgbatch-xyz")
        with patch("litellm.create_batch", return_value=batch_obj) as create_batch:
            handle = _submit_anthropic_batch(provider, cases)
        assert handle.vendor == "anthropic"
        assert handle.batch_id == "msgbatch-xyz"
        # Anthropic doesn't use file IDs; field is None.
        assert handle.input_file_id is None
        kwargs = create_batch.call_args.kwargs
        assert kwargs.get("custom_llm_provider") == "anthropic"
        assert "requests" in kwargs

    def test_reassemble_parses_inline_results(self) -> None:
        provider = _provider("anthropic")
        handle = BatchHandle(
            vendor="anthropic", batch_id="msgbatch-xyz", case_count=1,
            case_id_order=("c1",),
        )
        result_entry = {
            "custom_id": "c1",
            "result": {
                "type": "succeeded",
                "message": {
                    "content": [
                        {"type": "text", "text": json.dumps(_VALID_RESPONSE_PAYLOAD)}
                    ]
                },
            },
        }
        with patch(
            "litellm.list_batch_results",
            return_value=[result_entry],
            create=True,
        ):
            result = _reassemble_anthropic(provider, handle)
        assert result.status == BatchStatus.COMPLETED
        assert len(result.judgments) == 1


# ── parse helpers ───────────────────────────────────────────────────────


class TestParseBatchJsonlResponses:
    def test_skips_empty_lines(self) -> None:
        provider = _provider("openai")
        text = "\n\n" + json.dumps({
            "custom_id": "c1",
            "response": {"body": {"choices": [{"message": {
                "content": json.dumps(_VALID_RESPONSE_PAYLOAD)
            }}]}}
        }) + "\n"
        judgments, failed = _parse_batch_jsonl_responses(
            provider, text, custom_id_field="custom_id",
        )
        assert len(judgments) == 1
        assert failed == []


class TestDictToJudgment:
    def test_propagates_evidence_gap(self) -> None:
        provider = _provider("openai")
        payload = {
            **_VALID_RESPONSE_PAYLOAD,
            "verdict": "OUT-OF-SCOPE",
            "evidence_gap": {
                "missing_evidence_type": "structured tolerance evidence",
                "would_support_defeater_evaluation":
                    "would justify the ±15% tolerance",
            },
        }
        j = _dict_to_judgment(provider, payload)
        assert j.evidence_gap is not None
        assert j.evidence_gap["missing_evidence_type"].startswith("structured")


# ── unknown vendor ──────────────────────────────────────────────────────


class TestUnknownVendor:
    def test_poll_unknown_vendor_raises(self) -> None:
        handle = BatchHandle(vendor="unknown", batch_id="x", case_count=0)
        provider = _provider("openai")
        with pytest.raises(ValueError, match="unknown batch vendor"):
            poll_batch(provider, handle)

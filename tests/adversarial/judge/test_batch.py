"""Tests for the batch dispatch layer (Phase 1 skeleton; Wave G fills in real litellm calls)."""

from __future__ import annotations

import pytest

from uofa_cli.adversarial.judge.batch import (
    BatchHandle,
    BatchNotSupported,
    BatchStatus,
    _coerce_status,
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
    def test_submit_batch_for_mistral_handled(self) -> None:
        # Mistral's family is 'Mistral' which doesn't match the batch
        # vendors ('GPT', 'Gemini'); current dispatch falls through to the
        # ValueError. Wave G will add Mistral-aware routing or document
        # it as out-of-batch.
        provider = _provider("mistral")
        with pytest.raises((ValueError, BatchNotSupported, NotImplementedError)):
            submit_batch(provider, [{"case_id": "c1"}])


# ── Phase 1 dispatch layer: routing works, real calls deferred to Wave G ────


class TestOpenAIBatchDispatchSkeleton:
    def test_submit_raises_not_implemented_phase1(self) -> None:
        provider = _provider("openai")
        with pytest.raises(NotImplementedError, match="Wave G"):
            submit_batch(provider, [{"case_id": "c1"}, {"case_id": "c2"}])

    def test_poll_raises_not_implemented_phase1(self) -> None:
        provider = _provider("openai")
        handle = BatchHandle(vendor="openai", batch_id="batch_abc123", case_count=2)
        with pytest.raises(NotImplementedError, match="Wave G"):
            poll_batch(provider, handle)

    def test_reassemble_raises_not_implemented_phase1(self) -> None:
        provider = _provider("openai")
        handle = BatchHandle(vendor="openai", batch_id="batch_abc123", case_count=2)
        with pytest.raises(NotImplementedError, match="Wave G"):
            reassemble_batch(provider, handle)


class TestGeminiBatchDispatchSkeleton:
    def test_submit_raises_not_implemented_phase1(self) -> None:
        provider = _provider("gemini")
        with pytest.raises(NotImplementedError, match="Wave G"):
            submit_batch(provider, [{"case_id": "c1"}])

    def test_poll_raises_not_implemented_phase1(self) -> None:
        provider = _provider("gemini")
        handle = BatchHandle(vendor="gemini", batch_id="batches/xyz", case_count=1)
        with pytest.raises(NotImplementedError, match="Wave G"):
            poll_batch(provider, handle)


# ── unknown vendor ──────────────────────────────────────────────────────


class TestUnknownVendor:
    def test_poll_unknown_vendor_raises(self) -> None:
        handle = BatchHandle(vendor="unknown", batch_id="x", case_count=0)
        provider = _provider("openai")
        with pytest.raises(ValueError, match="unknown batch vendor"):
            poll_batch(provider, handle)

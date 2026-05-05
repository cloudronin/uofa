"""Tests for the batch dispatch layer (skeleton implementation)."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

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
from uofa_cli.adversarial.judge.providers.gemini import GeminiProvider
from uofa_cli.adversarial.judge.providers.openai_compat import (
    OpenAICompatProvider,
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


# ── HF Llama refuses batch ──────────────────────────────────────────────


class TestHFLlamaNotBatchable:
    def test_submit_batch_raises_for_hf_llama(self) -> None:
        provider = OpenAICompatProvider(target="hf-llama", client=MagicMock())
        with pytest.raises(BatchNotSupported, match="HF Endpoints"):
            submit_batch(provider, [{"case_id": "c1"}])


# ── OpenAI batch dispatch ───────────────────────────────────────────────


class TestOpenAIBatchDispatch:
    def _provider_with_batch_client(self):
        client = MagicMock()
        # Set up .batches.create to return an object with .id
        client.batches.create.return_value = SimpleNamespace(id="batch_abc123")
        client.batches.retrieve.return_value = SimpleNamespace(status="validating")
        return OpenAICompatProvider(target="openai", client=client)

    def test_submit_returns_handle(self) -> None:
        provider = self._provider_with_batch_client()
        handle = submit_batch(provider, [{"case_id": "c1"}, {"case_id": "c2"}])
        assert handle.vendor == "openai"
        assert handle.batch_id == "batch_abc123"
        assert handle.case_count == 2

    def test_poll_returns_status(self) -> None:
        provider = self._provider_with_batch_client()
        handle = BatchHandle(vendor="openai", batch_id="batch_abc123", case_count=2)
        assert poll_batch(provider, handle) == BatchStatus.IN_PROGRESS

    def test_reassemble_is_stage2_skeleton(self) -> None:
        provider = self._provider_with_batch_client()
        handle = BatchHandle(vendor="openai", batch_id="batch_abc123", case_count=2)
        with pytest.raises(NotImplementedError, match="Stage 2"):
            reassemble_batch(provider, handle)


# ── Gemini batch dispatch ───────────────────────────────────────────────


class TestGeminiBatchDispatch:
    def _provider_with_batch_client(self):
        client = MagicMock()
        client.batches.create.return_value = SimpleNamespace(name="batches/xyz")
        client.batches.get.return_value = SimpleNamespace(state="ACTIVE")
        return GeminiProvider(client=client)

    def test_submit_returns_handle(self) -> None:
        provider = self._provider_with_batch_client()
        handle = submit_batch(provider, [{"case_id": "c1"}])
        assert handle.vendor == "gemini"
        assert handle.batch_id == "batches/xyz"
        assert handle.case_count == 1

    def test_poll_returns_status(self) -> None:
        provider = self._provider_with_batch_client()
        handle = BatchHandle(vendor="gemini", batch_id="batches/xyz", case_count=1)
        assert poll_batch(provider, handle) == BatchStatus.IN_PROGRESS


# ── unknown vendor ──────────────────────────────────────────────────────


class TestUnknownVendor:
    def test_poll_unknown_vendor_raises(self) -> None:
        # Construct a handle with an unknown vendor; poll should raise.
        handle = BatchHandle(vendor="unknown", batch_id="x", case_count=0)
        provider = OpenAICompatProvider(target="openai", client=MagicMock())
        with pytest.raises(ValueError, match="unknown batch vendor"):
            poll_batch(provider, handle)

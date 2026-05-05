"""Batch API submission + polling + reassembly (spec v1.5 §9.1, §9.4).

OpenAI and Gemini both support batch APIs at 50% discount with a 24-hour
SLA. The Phase 3 full-corpus run (~4,221 packages × 3 judges) uses these
to keep cost bounded.

HF Endpoints (Llama judge) does NOT have a batch concept — it's a
dedicated endpoint billed by the hour, so we use the synchronous
provider path with `--parallel N` for concurrency. `submit_batch` raises
NotImplementedError when called against an HF-Llama provider.

This module is the dispatch layer; the actual vendor API surface is wrapped
in private helpers per vendor. Tests stub the helpers via the provider's
mock client.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

from uofa_cli.adversarial.judge.providers.base import (
    AbstractJudgeProvider,
    Judgment,
)

logger = logging.getLogger(__name__)


class BatchStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class BatchHandle:
    """Opaque handle returned by `submit_batch` for later polling.

    `vendor` distinguishes OpenAI vs Gemini batch IDs (the formats
    differ); `batch_id` is the vendor-specific identifier.
    """

    vendor: str
    batch_id: str
    case_count: int


@dataclass(frozen=True)
class BatchResult:
    """Result of polling a completed batch."""

    handle: BatchHandle
    status: BatchStatus
    judgments: list[Judgment]
    failed_case_ids: list[str]


class BatchNotSupported(Exception):
    """Raised when the provider doesn't support batch submission (HF Llama)."""


def submit_batch(
    provider: AbstractJudgeProvider,
    cases: list[dict],
) -> BatchHandle:
    """Submit `cases` as a batch job; return a handle for polling.

    Raises BatchNotSupported for HF-Llama providers.
    """
    if provider.family == "Llama":
        raise BatchNotSupported(
            "HF Endpoints does not support batch API; "
            "use the synchronous --parallel path for the Llama judge"
        )
    if provider.family == "GPT":
        return _submit_openai_batch(provider, cases)
    if provider.family == "Gemini":
        return _submit_gemini_batch(provider, cases)
    raise ValueError(f"unknown provider family: {provider.family}")


def poll_batch(provider: AbstractJudgeProvider, handle: BatchHandle) -> BatchStatus:
    """Check the status of an in-flight batch."""
    if handle.vendor == "openai":
        return _poll_openai_batch(provider, handle)
    if handle.vendor == "gemini":
        return _poll_gemini_batch(provider, handle)
    raise ValueError(f"unknown batch vendor: {handle.vendor}")


def reassemble_batch(
    provider: AbstractJudgeProvider,
    handle: BatchHandle,
) -> BatchResult:
    """Pull batch results and reassemble into Judgment objects."""
    if handle.vendor == "openai":
        return _reassemble_openai(provider, handle)
    if handle.vendor == "gemini":
        return _reassemble_gemini(provider, handle)
    raise ValueError(f"unknown batch vendor: {handle.vendor}")


# ── vendor-specific helpers ─────────────────────────────────────────────
# Tier A: skeleton implementations that delegate to the provider's client.
# The exact API shape (file uploads, JSONL request format, etc.) is
# verified in Stage 1 calibration runs. These functions raise
# NotImplementedError if the underlying client doesn't expose the right
# attributes — tests inject mocks that DO expose them.


def _submit_openai_batch(
    provider: AbstractJudgeProvider, cases: list[dict]
) -> BatchHandle:
    client = _client_of(provider)
    if not hasattr(client, "batches") or not hasattr(client.batches, "create"):
        raise NotImplementedError(
            "OpenAI client does not expose .batches.create; "
            "Tier A skeleton — full implementation lands at Stage 2"
        )
    # Real implementation uploads a JSONL file with one request per case
    # (see https://platform.openai.com/docs/guides/batch). Tests inject a
    # mock that returns a stub batch object with .id.
    response = client.batches.create(
        input_file_id="<placeholder — real impl uploads cases as JSONL>",
        endpoint="/v1/chat/completions",
        completion_window="24h",
    )
    batch_id = getattr(response, "id", None) or response["id"]
    return BatchHandle(vendor="openai", batch_id=batch_id, case_count=len(cases))


def _poll_openai_batch(
    provider: AbstractJudgeProvider, handle: BatchHandle
) -> BatchStatus:
    client = _client_of(provider)
    if not hasattr(client, "batches"):
        raise NotImplementedError("OpenAI client does not expose .batches")
    batch = client.batches.retrieve(handle.batch_id)
    status_str = getattr(batch, "status", None) or batch.get("status", "pending")
    return _coerce_status(status_str)


def _reassemble_openai(
    provider: AbstractJudgeProvider, handle: BatchHandle
) -> BatchResult:
    """Stage 2 will fetch the output file and parse one Judgment per line."""
    raise NotImplementedError(
        "OpenAI batch reassembly is a Stage 2 deliverable; Tier A ships the dispatch layer"
    )


def _submit_gemini_batch(
    provider: AbstractJudgeProvider, cases: list[dict]
) -> BatchHandle:
    client = _client_of(provider)
    # Gemini batch is exposed via the `genai.batches` namespace in v0.8+.
    if not hasattr(client, "batches"):
        raise NotImplementedError(
            "Gemini client does not expose .batches; "
            "Tier A skeleton — full implementation lands at Stage 2"
        )
    response = client.batches.create(
        model=provider.model,
        cases="<placeholder — real impl serializes cases per Gemini batch schema>",
    )
    batch_id = getattr(response, "name", None) or response["name"]
    return BatchHandle(vendor="gemini", batch_id=batch_id, case_count=len(cases))


def _poll_gemini_batch(
    provider: AbstractJudgeProvider, handle: BatchHandle
) -> BatchStatus:
    client = _client_of(provider)
    if not hasattr(client, "batches"):
        raise NotImplementedError("Gemini client does not expose .batches")
    batch = client.batches.get(handle.batch_id)
    state_str = getattr(batch, "state", None) or batch.get("state", "pending")
    return _coerce_status(state_str)


def _reassemble_gemini(
    provider: AbstractJudgeProvider, handle: BatchHandle
) -> BatchResult:
    raise NotImplementedError(
        "Gemini batch reassembly is a Stage 2 deliverable"
    )


def _client_of(provider: AbstractJudgeProvider) -> Any:
    """Pull the underlying client out of the provider for batch calls."""
    client = getattr(provider, "_client", None)
    if client is None:
        raise RuntimeError(
            f"provider {type(provider).__name__} does not expose ._client; "
            f"batch operations require client access"
        )
    return client


def _coerce_status(s: str) -> BatchStatus:
    """Normalize vendor-specific status strings to BatchStatus enum."""
    s = s.lower().strip()
    if s in ("validating", "in_progress", "running", "active"):
        return BatchStatus.IN_PROGRESS
    if s in ("completed", "succeeded", "done"):
        return BatchStatus.COMPLETED
    if s in ("failed", "expired", "errored"):
        return BatchStatus.FAILED
    if s in ("cancelled", "canceled"):
        return BatchStatus.CANCELLED
    return BatchStatus.PENDING

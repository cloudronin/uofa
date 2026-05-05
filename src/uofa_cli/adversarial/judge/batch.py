"""Batch API submission + polling + reassembly (spec v1.6 §9.1, §9.4).

OpenAI, Gemini, and Anthropic all support batch APIs at ~50% discount with
a 24-hour SLA. The Phase 3 full-corpus run (~4,221 packages × 3 judges)
uses these to keep cost bounded.

HF Endpoints (Llama judge) does NOT have a batch concept — it's a
dedicated endpoint billed by the hour, so we use the synchronous
provider path with `--parallel N` for concurrency. Mistral has no batch
API per spec v1.6 §6.7.

This module routes to litellm's unified batch surface where available
(`litellm.create_batch` / `litellm.retrieve_batch` / `litellm.list_files`).
Where litellm hasn't caught up to a vendor (notably Anthropic message-
batches as of 2026-04), we fall back to synchronous parallel execution
and surface the limitation in the run manifest.

Wave G scope: dispatch layer + OpenAI happy path. Gemini and Anthropic
batch paths are stubbed against litellm calls but verified against mocks
only — real batch verification is a Wave L Phase 5 item, gated on a
small ($0.50–1.00) end-to-end smoke against each vendor.
"""

from __future__ import annotations

import asyncio
import json
import logging
import tempfile
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from uofa_cli.adversarial.judge.providers.base import (
    AbstractJudgeProvider,
    Judgment,
)
from uofa_cli.adversarial.judge.providers.capabilities import (
    get_capabilities,
    litellm_model_string,
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

    `vendor` distinguishes OpenAI vs Gemini vs Anthropic batch IDs (the
    formats differ); `batch_id` is the vendor-specific identifier.
    `case_id_order` preserves the submission ordering for reassembly so
    we can map response line N → case_id at fetch time without round-
    tripping through litellm metadata.
    """

    vendor: str
    batch_id: str
    case_count: int
    case_id_order: tuple[str, ...] = ()
    input_file_id: str | None = None


@dataclass(frozen=True)
class BatchResult:
    """Result of polling a completed batch."""

    handle: BatchHandle
    status: BatchStatus
    judgments: list[Judgment]
    failed_case_ids: list[str]


class BatchNotSupported(Exception):
    """Raised when the provider doesn't support batch submission."""


# ── dispatch ────────────────────────────────────────────────────────────


def submit_batch(
    provider: AbstractJudgeProvider,
    cases: list[dict],
) -> BatchHandle:
    """Submit `cases` as a batch job; return a handle for polling.

    Raises BatchNotSupported for providers without batch capability.
    Provider family resolution defers to the FAMILY_MAP via
    `provider.family`; capability lookup defers to the table.
    """
    family = provider.family
    if family == "Llama":
        raise BatchNotSupported(
            "HF Endpoints does not support batch API; "
            "use the synchronous --parallel path for the Llama judge"
        )
    if family == "Mistral":
        raise BatchNotSupported(
            "Mistral has no batch API per spec v1.6 §6.7; use synchronous"
        )
    # Capability lookup: providers without supports_batch_api flagged ON
    # are routed to the sync path even if family is GPT/Gemini/Claude.
    token = _provider_token(provider)
    caps = get_capabilities(token) if token else None
    if caps is not None and not caps.supports_batch_api:
        raise BatchNotSupported(
            f"provider token '{token}' is not configured for batch API"
        )

    if family == "GPT":
        return _submit_openai_batch(provider, cases)
    if family == "Gemini":
        return _submit_gemini_batch(provider, cases)
    if family == "Claude":
        return _submit_anthropic_batch(provider, cases)
    raise ValueError(f"unknown provider family: {family}")


def poll_batch(provider: AbstractJudgeProvider, handle: BatchHandle) -> BatchStatus:
    """Check the status of an in-flight batch."""
    if handle.vendor == "openai":
        return _poll_openai_batch(provider, handle)
    if handle.vendor == "gemini":
        return _poll_gemini_batch(provider, handle)
    if handle.vendor == "anthropic":
        return _poll_anthropic_batch(provider, handle)
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
    if handle.vendor == "anthropic":
        return _reassemble_anthropic(provider, handle)
    raise ValueError(f"unknown batch vendor: {handle.vendor}")


# ── OpenAI batch via litellm ────────────────────────────────────────────


def _submit_openai_batch(
    provider: AbstractJudgeProvider, cases: list[dict]
) -> BatchHandle:
    """Submit OpenAI batch via litellm.create_batch.

    Build a JSONL input file with one request per case (custom_id =
    case_id), upload via litellm.create_file, then create the batch.
    """
    import litellm  # type: ignore

    case_id_order = tuple(c["case_id"] for c in cases)

    # Build batch JSONL.
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".jsonl", delete=False, dir=tempfile.gettempdir()
    ) as f:
        batch_input_path = Path(f.name)
        for case in cases:
            line = {
                "custom_id": case["case_id"],
                "method": "POST",
                "url": "/v1/chat/completions",
                "body": _request_body_for_case(provider, case),
            }
            f.write(json.dumps(line) + "\n")

    try:
        upload = litellm.create_file(
            file=open(batch_input_path, "rb"),
            purpose="batch",
            custom_llm_provider="openai",
        )
        input_file_id = getattr(upload, "id", None) or upload["id"]

        batch = litellm.create_batch(
            completion_window="24h",
            endpoint="/v1/chat/completions",
            input_file_id=input_file_id,
            custom_llm_provider="openai",
        )
        batch_id = getattr(batch, "id", None) or batch["id"]
    finally:
        try:
            batch_input_path.unlink()
        except OSError:
            pass

    return BatchHandle(
        vendor="openai",
        batch_id=batch_id,
        case_count=len(cases),
        case_id_order=case_id_order,
        input_file_id=input_file_id,
    )


def _poll_openai_batch(
    provider: AbstractJudgeProvider, handle: BatchHandle
) -> BatchStatus:
    """Poll OpenAI batch status via litellm.retrieve_batch."""
    import litellm  # type: ignore
    res = litellm.retrieve_batch(
        batch_id=handle.batch_id, custom_llm_provider="openai"
    )
    raw_status = getattr(res, "status", None) or res["status"]
    return _coerce_status(str(raw_status))


def _reassemble_openai(
    provider: AbstractJudgeProvider, handle: BatchHandle
) -> BatchResult:
    """Fetch + parse OpenAI batch output via litellm.file_content."""
    import litellm  # type: ignore
    res = litellm.retrieve_batch(
        batch_id=handle.batch_id, custom_llm_provider="openai"
    )
    output_file_id = (
        getattr(res, "output_file_id", None) or res.get("output_file_id")
    )
    if not output_file_id:
        return BatchResult(
            handle=handle, status=BatchStatus.FAILED,
            judgments=[], failed_case_ids=list(handle.case_id_order),
        )

    file_resp = litellm.file_content(
        file_id=output_file_id, custom_llm_provider="openai"
    )
    raw_text = (
        file_resp.text if hasattr(file_resp, "text")
        else (
            file_resp.content.decode("utf-8")
            if hasattr(file_resp, "content") else str(file_resp)
        )
    )

    judgments, failed = _parse_batch_jsonl_responses(
        provider, raw_text, custom_id_field="custom_id",
    )
    return BatchResult(
        handle=handle, status=BatchStatus.COMPLETED,
        judgments=judgments, failed_case_ids=failed,
    )


# ── Gemini batch via litellm ────────────────────────────────────────────


def _submit_gemini_batch(
    provider: AbstractJudgeProvider, cases: list[dict]
) -> BatchHandle:
    """Gemini batch via litellm.create_batch (custom_llm_provider='gemini').

    Gemini's batch surface is closer to GenerativeAI BatchPredictionJob;
    litellm normalizes to the OpenAI-style create_batch interface.
    """
    import litellm  # type: ignore

    case_id_order = tuple(c["case_id"] for c in cases)
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".jsonl", delete=False, dir=tempfile.gettempdir()
    ) as f:
        batch_input_path = Path(f.name)
        for case in cases:
            line = {
                "custom_id": case["case_id"],
                "request": _request_body_for_case(provider, case),
            }
            f.write(json.dumps(line) + "\n")

    try:
        upload = litellm.create_file(
            file=open(batch_input_path, "rb"),
            purpose="batch",
            custom_llm_provider="gemini",
        )
        input_file_id = getattr(upload, "id", None) or upload["id"]
        batch = litellm.create_batch(
            completion_window="24h",
            endpoint="/v1/chat/completions",
            input_file_id=input_file_id,
            custom_llm_provider="gemini",
        )
        batch_id = getattr(batch, "id", None) or batch["id"]
    finally:
        try:
            batch_input_path.unlink()
        except OSError:
            pass

    return BatchHandle(
        vendor="gemini",
        batch_id=batch_id,
        case_count=len(cases),
        case_id_order=case_id_order,
        input_file_id=input_file_id,
    )


def _poll_gemini_batch(
    provider: AbstractJudgeProvider, handle: BatchHandle
) -> BatchStatus:
    import litellm  # type: ignore
    res = litellm.retrieve_batch(
        batch_id=handle.batch_id, custom_llm_provider="gemini"
    )
    raw_status = getattr(res, "status", None) or res["status"]
    return _coerce_status(str(raw_status))


def _reassemble_gemini(
    provider: AbstractJudgeProvider, handle: BatchHandle
) -> BatchResult:
    import litellm  # type: ignore
    res = litellm.retrieve_batch(
        batch_id=handle.batch_id, custom_llm_provider="gemini"
    )
    output_file_id = (
        getattr(res, "output_file_id", None) or res.get("output_file_id")
    )
    if not output_file_id:
        return BatchResult(
            handle=handle, status=BatchStatus.FAILED,
            judgments=[], failed_case_ids=list(handle.case_id_order),
        )
    file_resp = litellm.file_content(
        file_id=output_file_id, custom_llm_provider="gemini"
    )
    raw_text = (
        file_resp.text if hasattr(file_resp, "text")
        else (
            file_resp.content.decode("utf-8")
            if hasattr(file_resp, "content") else str(file_resp)
        )
    )
    judgments, failed = _parse_batch_jsonl_responses(
        provider, raw_text, custom_id_field="custom_id",
    )
    return BatchResult(
        handle=handle, status=BatchStatus.COMPLETED,
        judgments=judgments, failed_case_ids=failed,
    )


# ── Anthropic message-batches via litellm ───────────────────────────────


def _submit_anthropic_batch(
    provider: AbstractJudgeProvider, cases: list[dict]
) -> BatchHandle:
    """Anthropic message-batches via litellm.

    Anthropic's batch API takes a list of MessageCreateParamsNonStreaming
    requests inline (no file upload). Litellm exposes this through
    `create_batch` with `custom_llm_provider='anthropic'` and the requests
    embedded in `requests` rather than `input_file_id`.
    """
    import litellm  # type: ignore

    case_id_order = tuple(c["case_id"] for c in cases)
    requests = [
        {
            "custom_id": case["case_id"],
            "params": _request_body_for_case(provider, case),
        }
        for case in cases
    ]

    batch = litellm.create_batch(
        custom_llm_provider="anthropic",
        requests=requests,
    )
    batch_id = getattr(batch, "id", None) or batch["id"]
    return BatchHandle(
        vendor="anthropic",
        batch_id=batch_id,
        case_count=len(cases),
        case_id_order=case_id_order,
    )


def _poll_anthropic_batch(
    provider: AbstractJudgeProvider, handle: BatchHandle
) -> BatchStatus:
    import litellm  # type: ignore
    res = litellm.retrieve_batch(
        batch_id=handle.batch_id, custom_llm_provider="anthropic"
    )
    raw_status = (
        getattr(res, "processing_status", None)
        or res.get("processing_status")
        or getattr(res, "status", None)
        or res.get("status")
    )
    return _coerce_status(str(raw_status))


def _reassemble_anthropic(
    provider: AbstractJudgeProvider, handle: BatchHandle
) -> BatchResult:
    import litellm  # type: ignore
    # Anthropic returns results inline via list_batches_results.
    results = litellm.list_batch_results(
        batch_id=handle.batch_id, custom_llm_provider="anthropic"
    )
    judgments: list[Judgment] = []
    failed: list[str] = []

    for entry in results:
        custom_id = (
            getattr(entry, "custom_id", None) or entry.get("custom_id")
        )
        result = (
            getattr(entry, "result", None) or entry.get("result")
        )
        if not isinstance(result, dict) or result.get("type") != "succeeded":
            if custom_id:
                failed.append(custom_id)
            continue
        message = result.get("message") or {}
        try:
            text = _anthropic_message_text(message)
            parsed = json.loads(text)
            judgments.append(_dict_to_judgment(provider, parsed))
        except Exception:
            if custom_id:
                failed.append(custom_id)

    return BatchResult(
        handle=handle, status=BatchStatus.COMPLETED,
        judgments=judgments, failed_case_ids=failed,
    )


# ── helpers ────────────────────────────────────────────────────────────


def _request_body_for_case(
    provider: AbstractJudgeProvider, case: dict
) -> dict:
    """Build the per-case request body shared by all batch shapes.

    Reuses the LiteLLMProvider's prompt construction so the batch path
    sees the exact same prefix + per-case content as the synchronous
    path. Falls back to a minimal user-only body for providers that
    don't expose `_build_messages`.
    """
    builder = getattr(provider, "_build_messages", None)
    if callable(builder):
        messages = builder(case)
    else:
        from uofa_cli.adversarial.judge.prompts import (
            build_prompt_for_case,
            build_prompt_static_prefix,
        )
        messages = [
            {"role": "system", "content": build_prompt_static_prefix()},
            {"role": "user", "content": build_prompt_for_case(case)},
        ]

    body: dict = {
        "model": _provider_model_id(provider),
        "messages": messages,
        "temperature": 0.0,
    }
    # Strict-schema response_format is not always batch-compatible. Defer
    # to the provider's capability table at call construction time.
    schema_dict = getattr(provider, "_response_format", None)
    if schema_dict:
        body["response_format"] = schema_dict
    return body


def _provider_model_id(provider: AbstractJudgeProvider) -> str:
    """Resolve the litellm-style model id for a provider instance."""
    token = _provider_token(provider)
    if token is not None:
        return litellm_model_string(token, getattr(provider, "_model_id", None))
    return getattr(provider, "_model", None) or provider.model


def _provider_token(provider: AbstractJudgeProvider) -> str | None:
    """Return the provider token (e.g. 'openai', 'anthropic') if present."""
    return getattr(provider, "_provider_token", None)


def _parse_batch_jsonl_responses(
    provider: AbstractJudgeProvider,
    raw_text: str,
    *,
    custom_id_field: str,
) -> tuple[list[Judgment], list[str]]:
    """Parse OpenAI/Gemini batch output JSONL into Judgments + failed ids."""
    judgments: list[Judgment] = []
    failed: list[str] = []
    for line in raw_text.splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        custom_id = record.get(custom_id_field)
        response = record.get("response") or {}
        body = response.get("body") if isinstance(response, dict) else None
        if not body:
            if custom_id:
                failed.append(custom_id)
            continue
        try:
            choices = body.get("choices") or []
            if not choices:
                raise ValueError("no choices")
            content = choices[0]["message"]["content"]
            parsed = json.loads(content)
            judgments.append(_dict_to_judgment(provider, parsed))
        except Exception:
            if custom_id:
                failed.append(custom_id)
    return judgments, failed


def _anthropic_message_text(message: dict) -> str:
    """Pull the text content out of an Anthropic message structure."""
    content = message.get("content") or []
    if isinstance(content, list):
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                return block.get("text", "")
    if isinstance(content, str):
        return content
    return json.dumps(message)


def _dict_to_judgment(provider: AbstractJudgeProvider, parsed: dict) -> Judgment:
    """Build a Judgment from a parsed JSON payload (batch path)."""
    from uofa_cli.adversarial.judge.prompts import PROMPT_TEMPLATE_VERSION
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
        judge_model=_provider_model_id(provider),
        judge_thinking_enabled=parsed.get("judge_thinking_enabled", False),
        judge_model_params=parsed.get(
            "judge_model_params", {"temperature": 0.0, "seed": 42}
        ),
        generator_provenance=parsed.get(
            "generator_provenance",
            {"generator_model": "unknown", "temperature": None, "seed": None},
        ),
        evidence_gap=parsed.get("evidence_gap"),
        raw_response=parsed,
    )


def _coerce_status(s: str) -> BatchStatus:
    """Normalize vendor-specific status strings to BatchStatus enum."""
    s = s.lower().strip()
    if s in ("validating", "in_progress", "running", "active"):
        return BatchStatus.IN_PROGRESS
    if s in ("completed", "succeeded", "ended", "done"):
        return BatchStatus.COMPLETED
    if s in ("failed", "expired", "errored"):
        return BatchStatus.FAILED
    if s in ("cancelled", "canceled"):
        return BatchStatus.CANCELLED
    return BatchStatus.PENDING


# ── synchronous fallback runner ─────────────────────────────────────────


async def run_batch_or_sync_fallback(
    provider: AbstractJudgeProvider,
    cases: list[dict],
    *,
    poll_interval_seconds: float = 30.0,
    max_wait_seconds: float | None = None,
) -> list[Judgment]:
    """Submit a batch and wait for completion; on BatchNotSupported run sync.

    `max_wait_seconds=None` means wait indefinitely (suitable for the
    24-hour OpenAI SLA). Most callers should use the explicit submit /
    poll / reassemble functions; this helper is for the smoke-test path.
    """
    try:
        handle = submit_batch(provider, cases)
    except BatchNotSupported:
        # Synchronous path: judge each case in order.
        out: list[Judgment] = []
        for case in cases:
            out.append(await provider.judge(case))
        return out

    waited = 0.0
    while True:
        status = poll_batch(provider, handle)
        if status in (BatchStatus.COMPLETED, BatchStatus.FAILED, BatchStatus.CANCELLED):
            break
        if max_wait_seconds is not None and waited >= max_wait_seconds:
            raise TimeoutError(
                f"batch {handle.batch_id} not done after {max_wait_seconds}s"
            )
        await asyncio.sleep(poll_interval_seconds)
        waited += poll_interval_seconds

    result = reassemble_batch(provider, handle)
    return result.judgments

"""LLMBackend Protocol and supporting dataclasses (spec v0.4 §4.8).

Concrete backends live in sibling modules (`mock_backend.py`, `litellm_backend.py`).
The Protocol intentionally mirrors the spec's surface so callers (`extract`,
`interpretation`) can be implemented against the abstraction before any real
backend exists.

Design notes:
- `Protocol` is `runtime_checkable` so tests can assert conformance via
  `isinstance(backend, LLMBackend)`. Capability methods are concrete bools, not
  exceptions, so callers can guard their code paths cleanly (`if not
  backend.supports_streaming(): fall back`).
- `generate_structured` returns `dict` rather than a typed object; the schema
  is provided per-call because different commands extract different shapes.
- Streaming returns an iterator of partial-text chunks; the caller is
  responsible for accumulating.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class GenerationOptions:
    """Per-call generation parameters.

    All fields optional; backends apply their own defaults when None. `seed`
    and `temperature` are advisory — backends that don't support them silently
    ignore (capability methods on `LLMBackend` advertise support so callers can
    decide).
    """

    temperature: float | None = None
    max_tokens: int | None = None
    seed: int | None = None
    timeout_seconds: float | None = None
    # Backend-specific knobs (e.g. Ollama's "think" flag for Qwen3 reasoning
    # mode). Kept open-ended so we don't need a Protocol change every time a
    # backend exposes a new switch.
    extra: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class HealthStatus:
    """Result of `LLMBackend.health_check()`.

    `ok=True` means the backend is reachable and the configured model is
    available. `ok=False` carries a user-facing `diagnostic` (one of the
    failure-mode rows in spec §3.7) plus a `suggestion` for remediation.
    """

    ok: bool
    diagnostic: str = ""
    suggestion: str = ""

    @classmethod
    def healthy(cls) -> "HealthStatus":
        return cls(ok=True)


@runtime_checkable
class LLMBackend(Protocol):
    """Pluggable interface for LLM inference (spec v0.4 §4.8).

    Implemented by `MockBackend` (always-available, deterministic) and
    `LiteLLMBackend` (single concrete class for Ollama/Anthropic/OpenAI/
    OpenAI-compatible — all routing handled internally by `litellm`).
    """

    # ── Identity ──────────────────────────────────────────────

    def name(self) -> str:
        """Stable backend identifier (e.g. "ollama", "anthropic", "mock").

        Used in cache keys (spec §4.7) and verbose-mode output (§4.8). Must
        not echo any credential material.
        """
        ...

    def model(self) -> str:
        """Model identifier as seen by the backend (e.g. "qwen3.5:4b",
        "claude-sonnet-5-2026"). Used in cache keys and verbose output."""
        ...

    # ── Capability advertisement ──────────────────────────────

    def supports_seed(self) -> bool:
        """True if `GenerationOptions.seed` is honored deterministically."""
        ...

    def supports_temperature(self) -> bool: ...

    def supports_streaming(self) -> bool: ...

    def supports_structured_output(self) -> bool:
        """True if `generate_structured` enforces the schema (e.g. via JSON
        mode, tool use, or response_format). False means the backend will
        raise `NotImplementedError` on `generate_structured`."""
        ...

    def max_context_tokens(self) -> int:
        """Advertised max input+output token window for the configured model."""
        ...

    # ── Generation ────────────────────────────────────────────

    def generate(self, prompt: str, options: GenerationOptions) -> str:
        """Single text-in / text-out call. The most basic interface."""
        ...

    def generate_streaming(
        self, prompt: str, options: GenerationOptions
    ) -> Iterator[str]:
        """Yield partial text chunks as the backend produces them.

        Backends that don't support streaming raise `NotImplementedError`.
        Callers should check `supports_streaming()` first.
        """
        ...

    def generate_structured(
        self, prompt: str, schema: dict, options: GenerationOptions
    ) -> dict:
        """Constrained generation against a JSON schema.

        Backends that support it (Ollama JSON mode, OpenAI response_format,
        Anthropic tool use) enforce the schema server-side and return parsed
        dict. Backends that don't raise `NotImplementedError`; the caller
        should check `supports_structured_output()` and fall back to
        `generate()` + manual parse if needed.
        """
        ...

    # ── Health + cost ────────────────────────────────────────

    def health_check(self) -> HealthStatus:
        """Probe whether the backend can serve requests right now.

        Called before LLM operations so graceful degradation (spec §3.7) can
        engage cleanly instead of failing partway through. Implementations
        should be cheap (no actual generation call); a tiny "ping" request or
        a model-list query is appropriate.
        """
        ...

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """USD cost estimate for the given token counts.

        Returns 0.0 for local backends (Ollama, mock). Remote backends look
        up advertised pricing (per-call, no network — the pricing table ships
        with the CLI). Estimates are advisory; spec §4.8 makes that explicit.
        """
        ...

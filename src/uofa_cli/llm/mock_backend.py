"""In-process MockBackend for tests and offline development.

Always available (no network, no Ollama, no API keys). Tests can pre-program
responses by prompt-substring or by a default fallback. The backend
implements the full Protocol surface — `generate`, `generate_streaming`, and
`generate_structured` — so callers can be exercised against it without
branching on `supports_*` checks.

This is *not* a drop-in replacement for the existing `_mock_extract` in
`llm_extractor.py`; that helper produces a pack-aware extraction-shaped JSON
and is wired into `extract` via the `model == "mock"` magic string. The
extract migration phase will switch that path over by configuring this
MockBackend with the same canned dict.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from dataclasses import dataclass, field

from uofa_cli.llm.backend import GenerationOptions, HealthStatus


@dataclass
class MockBackend:
    """Deterministic backend for tests.

    Args:
        default_response: Returned by `generate()` when no canned response
            matches the prompt. Defaults to a short fixed string.
        responses: Map of prompt-substring → full response. The first key
            that appears as a substring of the prompt wins (insertion order).
        structured_responses: Same idea for `generate_structured` — values
            should be `dict`, returned as-is.
        model_name: What `model()` reports.
        backend_name: What `name()` reports.
        max_context: What `max_context_tokens()` reports.
        healthy: When False, `health_check()` returns an unhealthy status
            with the configured `unhealthy_diagnostic`.
    """

    default_response: str = "MOCK RESPONSE"
    responses: dict[str, str] = field(default_factory=dict)
    structured_responses: dict[str, dict] = field(default_factory=dict)
    model_name: str = "mock"
    backend_name: str = "mock"
    max_context: int = 32_768
    healthy: bool = True
    unhealthy_diagnostic: str = "MockBackend configured as unhealthy"

    # Call log for test assertions — populated by every generate* call.
    calls: list[tuple[str, str, GenerationOptions]] = field(default_factory=list)

    # ── Identity ──────────────────────────────────────────────

    def name(self) -> str:
        return self.backend_name

    def model(self) -> str:
        return self.model_name

    # ── Capability advertisement ──────────────────────────────

    def supports_seed(self) -> bool:
        return True

    def supports_temperature(self) -> bool:
        return True

    def supports_streaming(self) -> bool:
        return True

    def supports_structured_output(self) -> bool:
        return True

    def max_context_tokens(self) -> int:
        return self.max_context

    # ── Generation ────────────────────────────────────────────

    def generate(self, prompt: str, options: GenerationOptions) -> str:
        self.calls.append(("generate", prompt, options))
        return self._lookup_text(prompt)

    def generate_streaming(
        self, prompt: str, options: GenerationOptions
    ) -> Iterator[str]:
        self.calls.append(("generate_streaming", prompt, options))
        text = self._lookup_text(prompt)
        # Yield word-by-word so streaming consumers can be exercised end-to-end.
        for token in text.split(" "):
            yield token + " "

    def generate_structured(
        self, prompt: str, schema: dict, options: GenerationOptions
    ) -> dict:
        self.calls.append(("generate_structured", prompt, options))
        for needle, value in self.structured_responses.items():
            if needle in prompt:
                return value
        # Fall back: try to coerce default_response into JSON; otherwise a
        # minimal empty dict so callers can decide how to handle.
        try:
            return json.loads(self.default_response)
        except (json.JSONDecodeError, TypeError):
            return {}

    # ── Health + cost ────────────────────────────────────────

    def health_check(self) -> HealthStatus:
        if self.healthy:
            return HealthStatus.healthy()
        return HealthStatus(
            ok=False,
            diagnostic=self.unhealthy_diagnostic,
            suggestion="Reconfigure the test fixture or use a different backend.",
        )

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        return 0.0

    # ── Internals ────────────────────────────────────────────

    def _lookup_text(self, prompt: str) -> str:
        for needle, value in self.responses.items():
            if needle in prompt:
                return value
        return self.default_response

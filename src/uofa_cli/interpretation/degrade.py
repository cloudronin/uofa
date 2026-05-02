"""Graceful-degradation notice formatter (spec v0.4 §3.7).

When `--explain` is requested but no LLM is available, the underlying analysis
still runs and produces structured output, with a clearly-formatted notice
appended explaining why interpretation was skipped and how to enable it. This
module turns an `LLMError` into that notice in both text and JSON forms.

The same notice serves `extract`, with one wording change in the opening line:
extract requires an LLM to function (so the notice describes a hard failure
rather than a skipped opt-in step). Spec §3.7 explicitly unifies the body and
splits only the opening + the exit-code semantics.

Exit-code semantics (caller-owned, not enforced here):
- explain mode: exit 0 (analysis succeeded, interpretation was opt-in)
- extract mode: exit 1 (extract requires LLM and could not function)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from uofa_cli.llm.config import BUNDLED_MODEL
from uofa_cli.llm.errors import (
    AuthenticationError,
    BackendNotInstalled,
    ConfigError,
    ContextWindowExceeded,
    LLMError,
    LLMUnavailable,
    ModelNotFound,
    RateLimited,
    TimeoutError as LLMTimeoutError,
)


Mode = Literal["explain", "extract"]


# Reason codes used in the JSON `reason` field — stable contract for the
# Tauri app (spec §3.7) and any other consumer that branches on failure type.
_REASON_BY_TYPE: dict[type[LLMError], str] = {
    LLMUnavailable: "no_llm_available",
    BackendNotInstalled: "backend_not_installed",
    AuthenticationError: "authentication_failed",
    RateLimited: "rate_limited",
    LLMTimeoutError: "timeout",
    ContextWindowExceeded: "context_window_exceeded",
    ModelNotFound: "model_not_found",
    ConfigError: "config_error",
}


# Opening lines per spec §3.7. The bodies are identical; only this line
# differs because the user-facing situations differ.
_OPENING_TEXT: dict[Mode, str] = {
    "explain": "--explain was requested but no LLM is available.\nShowing structured output only.",
    "extract": "extract requires an LLM to function, but no LLM is available.",
}


@dataclass(frozen=True)
class Suggestion:
    """One actionable remediation in the notice (spec §3.7 enumerates three)."""

    option: str  # "install_ollama" | "configure_remote" | "use_copilot"
    description: str
    instructions: str | None = None  # multi-line shell or TOML snippet
    url: str | None = None           # for use_copilot


@dataclass(frozen=True)
class DegradationNotice:
    """Resolved notice ready to render to text or JSON.

    Fields:
        reason: Stable code from `_REASON_BY_TYPE` (or "unknown_error").
        diagnostic: User-facing one-liner describing what failed; never echoes
            credential material (errors.py guarantees this on construction).
        suggestion: Optional remediation hint specific to this error
            (e.g. "Run `ollama pull qwen3.5:4b`."). Distinct from the three
            standard suggestions in `suggestions` — this one is error-specific.
        mode: "explain" or "extract" — controls only the opening line.
        suggestions: The three standard remediation options (always the same).
    """

    reason: str
    diagnostic: str
    suggestion: str
    mode: Mode
    suggestions: list[Suggestion] = field(default_factory=list)

    # ── Text rendering ───────────────────────────────────────

    def to_text(self) -> str:
        """Render the bracketed text block from spec §3.7.

        Designed to be appended to the command's normal stdout (for
        `--explain`) or emitted as the failure message (for `extract`).
        Wrapped in `[...]` so it visually separates from the analysis output.
        """
        lines = ["[Note: " + _OPENING_TEXT[self.mode], ""]
        lines.append("To enable, you have several options:")
        lines.append("")
        for i, sugg in enumerate(self.suggestions, start=1):
            lines.append(f"{i}. {sugg.description}")
            if sugg.instructions:
                for instr_line in sugg.instructions.splitlines():
                    lines.append(f"       {instr_line}")
            if sugg.url:
                lines.append(f"       {sugg.url}")
            lines.append("")
        lines.append(f"Diagnostic: {self.diagnostic}")
        if self.suggestion:
            lines.append(f"Suggestion: {self.suggestion}")
        # Close the bracket on the last content line.
        block = "\n".join(lines).rstrip()
        return block + "]"

    # ── JSON rendering ───────────────────────────────────────

    def to_explain_envelope(
        self,
        *,
        command: str,
        structured_output: dict | list,
    ) -> dict:
        """Spec §3.7 JSON shape for `--explain` graceful degradation.

        The wrapper has a top-level `interpretation_skipped` block carrying
        reason + diagnostic + suggestions. `interpretation` itself is null so
        consumers can branch on `interpretation is None`.
        """
        return {
            "command": command,
            "structured_output": structured_output,
            "interpretation": None,
            "interpretation_skipped": self._inner_dict(),
        }

    def to_extract_envelope(self) -> dict:
        """Spec §3.7 JSON shape for `extract` failure (LLM required)."""
        return {
            "command": "extract",
            "status": "failed",
            "error": self._inner_dict(),
        }

    def _inner_dict(self) -> dict:
        out: dict = {
            "reason": self.reason,
            "diagnostic": self.diagnostic,
        }
        if self.suggestion:
            out["suggestion"] = self.suggestion
        out["suggestions"] = [_suggestion_to_dict(s) for s in self.suggestions]
        return out


def _suggestion_to_dict(s: Suggestion) -> dict:
    out: dict = {"option": s.option, "description": s.description}
    if s.instructions is not None:
        out["instructions"] = s.instructions
    if s.url is not None:
        out["url"] = s.url
    return out


# ── Standard suggestions (spec §3.7 enumerates exactly these three) ──


def _standard_suggestions() -> list[Suggestion]:
    """The three standard remediation options shown in every notice.

    BUNDLED_MODEL is sourced from llm.config so the install instructions
    automatically track the actual bundled model name (the spec text uses
    "qwen2.5:4b" but the constant is the source of truth).
    """
    return [
        Suggestion(
            option="install_ollama",
            description="Install Ollama and pull the bundled model (local, free, private):",
            instructions=(
                "curl -fsSL https://ollama.com/install.sh | sh\n"
                f"ollama pull {BUNDLED_MODEL}"
            ),
        ),
        Suggestion(
            option="configure_remote",
            description="Configure a remote LLM in your project's uofa.toml or in ~/.uofa/config.toml:",
            instructions=(
                "[llm]\n"
                'backend = "anthropic"\n'
                'api_key_env = "ANTHROPIC_API_KEY"\n'
                'model = "claude-sonnet-5-2026"\n'
                "See `uofa explain --help` for full configuration options."
            ),
        ),
        Suggestion(
            option="use_copilot",
            description=(
                "Use the proprietary UofA Copilot for higher-quality interpretation "
                "plus remediation suggestions, submission narrative generation, and "
                "conversational Q&A:"
            ),
            url="https://uofa.net/copilot",
        ),
    ]


# ── Public factory ─────────────────────────────────────────


def make_degradation_notice(
    error: LLMError,
    *,
    mode: Mode = "explain",
) -> DegradationNotice:
    """Construct a DegradationNotice from an LLMError.

    The reason code is dispatched on the exception's most-specific type. Any
    LLMError subclass not in the dispatch table maps to "unknown_error" — we
    deliberately don't fall through to a generic `Exception` handler because
    only LLM-related failures should reach degradation; other exceptions are
    real bugs and should propagate.

    Args:
        error: The LLMError raised by the backend or config layer.
        mode: "explain" (opt-in skip, exit 0) or "extract" (hard failure,
            exit 1). Controls only the notice's opening line + the JSON
            envelope shape produced by the to_*_envelope methods.

    Returns:
        A DegradationNotice. Caller decides whether to render to text
        (`.to_text()`) or JSON (`.to_explain_envelope()` /
        `.to_extract_envelope()`).
    """
    reason = _REASON_BY_TYPE.get(type(error), "unknown_error")
    return DegradationNotice(
        reason=reason,
        diagnostic=error.diagnostic,
        suggestion=error.suggestion or "",
        mode=mode,
        suggestions=_standard_suggestions(),
    )

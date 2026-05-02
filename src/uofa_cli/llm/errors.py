"""Exception hierarchy for the LLM backend layer.

Maps onto the failure-mode table in spec v0.4 §3.7 so the graceful-degradation
notice formatter (`interpretation/degrade.py`, future phase) can render the
right diagnostic + suggested remediation for each case.

All concrete errors carry a `diagnostic` string suitable for the user-facing
notice plus an optional `suggestion` for actionable next steps.
"""

from __future__ import annotations


class LLMError(RuntimeError):
    """Base class for all errors from `uofa_cli.llm`."""

    def __init__(self, diagnostic: str, suggestion: str | None = None):
        super().__init__(diagnostic)
        self.diagnostic = diagnostic
        self.suggestion = suggestion


class LLMUnavailable(LLMError):
    """Backend health check failed — service is not reachable.

    Covers Ollama-not-running, network-unreachable, and similar transient
    availability failures. Spec §3.7 graceful degradation engages on this.
    """


class BackendNotInstalled(LLMError):
    """Required Python dependency for the chosen backend is missing.

    With the litellm-wrap design this typically means `litellm` itself is
    not installed (i.e. `pip install uofa[extract]` was skipped).
    """


class AuthenticationError(LLMError):
    """Backend rejected the credentials.

    Maps to spec §3.7 row "API key invalid". The `diagnostic` deliberately
    avoids echoing the credential value (spec §6.4 Rule 2).
    """


class RateLimited(LLMError):
    """Backend returned 429 / quota exceeded.

    `retry_after_seconds` is set when the backend reports a Retry-After
    header so callers can decide whether to wait or fall back.
    """

    def __init__(
        self,
        diagnostic: str,
        suggestion: str | None = None,
        retry_after_seconds: float | None = None,
    ):
        super().__init__(diagnostic, suggestion)
        self.retry_after_seconds = retry_after_seconds


class ModelNotFound(LLMError):
    """Configured model is not available on the chosen backend."""


class ContextWindowExceeded(LLMError):
    """Prompt is larger than the backend's max context window.

    Extract-specific failure (spec §3.7 last row) — surfaces when the user
    tries to extract from a document the local model cannot fit.
    """

    def __init__(
        self,
        diagnostic: str,
        suggestion: str | None = None,
        prompt_tokens: int | None = None,
        max_context_tokens: int | None = None,
    ):
        super().__init__(diagnostic, suggestion)
        self.prompt_tokens = prompt_tokens
        self.max_context_tokens = max_context_tokens


class TimeoutError(LLMError):  # noqa: A001 — shadows builtin intentionally; scoped to llm package
    """Backend did not respond within the configured timeout."""


class ConfigError(LLMError):
    """LLM configuration is malformed.

    Raised by `config.resolve_llm_config()` for invalid backend names,
    literal API keys in TOML files (spec §6.4 Rule 1), missing required
    fields, etc.
    """

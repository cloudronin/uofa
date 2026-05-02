"""Tests for the graceful-degradation notice formatter (spec v0.4 §3.7)."""

from __future__ import annotations

import pytest

from uofa_cli.interpretation import (
    DegradationNotice,
    Suggestion,
    make_degradation_notice,
)
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


# ── Reason dispatch (one row per spec §3.7 failure-mode table) ──


@pytest.mark.parametrize("error_cls,expected_reason", [
    (LLMUnavailable,        "no_llm_available"),
    (BackendNotInstalled,   "backend_not_installed"),
    (AuthenticationError,   "authentication_failed"),
    (RateLimited,           "rate_limited"),
    (LLMTimeoutError,       "timeout"),
    (ContextWindowExceeded, "context_window_exceeded"),
    (ModelNotFound,         "model_not_found"),
    (ConfigError,           "config_error"),
])
def test_reason_dispatch(error_cls, expected_reason):
    notice = make_degradation_notice(error_cls("diag"))
    assert notice.reason == expected_reason


def test_unknown_error_subclass_falls_back_to_unknown_error():
    """Custom LLMError subclasses not in the dispatch table get 'unknown_error'."""
    class _NewKindOfError(LLMError):
        pass
    notice = make_degradation_notice(_NewKindOfError("diag"))
    assert notice.reason == "unknown_error"


# ── Diagnostic + suggestion plumbing ────────────────────────


def test_diagnostic_passes_through():
    err = LLMUnavailable("Ollama not responding on http://127.0.0.1:11434")
    notice = make_degradation_notice(err)
    assert notice.diagnostic == "Ollama not responding on http://127.0.0.1:11434"


def test_error_specific_suggestion_passes_through():
    err = ModelNotFound("model gone", suggestion="Try llama3.3:70b instead.")
    notice = make_degradation_notice(err)
    assert notice.suggestion == "Try llama3.3:70b instead."


def test_missing_error_suggestion_becomes_empty_string():
    notice = make_degradation_notice(LLMUnavailable("diag"))
    assert notice.suggestion == ""


# ── Standard suggestions (spec §3.7 enumerates exactly 3) ──


def test_three_standard_suggestions_always_present():
    notice = make_degradation_notice(LLMUnavailable("diag"))
    options = [s.option for s in notice.suggestions]
    assert options == ["install_ollama", "configure_remote", "use_copilot"]


def test_install_ollama_uses_bundled_model_constant():
    """If BUNDLED_MODEL changes, the install instructions should track it."""
    notice = make_degradation_notice(LLMUnavailable("diag"))
    install = next(s for s in notice.suggestions if s.option == "install_ollama")
    assert BUNDLED_MODEL in install.instructions


def test_configure_remote_includes_api_key_env_pattern():
    """Spec §6.4: notice must direct users to api_key_env, never literal keys."""
    notice = make_degradation_notice(LLMUnavailable("diag"))
    config = next(s for s in notice.suggestions if s.option == "configure_remote")
    assert "api_key_env" in config.instructions
    # Defense: must not show a literal example like api_key = "sk-..."
    assert 'api_key = "sk-' not in config.instructions
    assert "api_key =" not in config.instructions  # no equals form at all


def test_copilot_suggestion_carries_url():
    notice = make_degradation_notice(LLMUnavailable("diag"))
    copilot = next(s for s in notice.suggestions if s.option == "use_copilot")
    assert copilot.url == "https://uofa.net/copilot"
    assert copilot.instructions is None  # url-only, not an instructions block


# ── Mode wording (explain vs extract) ───────────────────────


def test_explain_mode_opening_line():
    notice = make_degradation_notice(LLMUnavailable("diag"), mode="explain")
    text = notice.to_text()
    assert "--explain was requested but no LLM is available" in text
    assert "Showing structured output only" in text


def test_extract_mode_opening_line():
    notice = make_degradation_notice(LLMUnavailable("diag"), mode="extract")
    text = notice.to_text()
    assert "extract requires an LLM to function" in text
    # The explain-specific phrasing must NOT appear in extract mode.
    assert "Showing structured output only" not in text


def test_body_is_identical_across_modes():
    """Spec §3.7: only the opening line changes between explain and extract."""
    err = LLMUnavailable("same diagnostic")
    explain_text = make_degradation_notice(err, mode="explain").to_text()
    extract_text = make_degradation_notice(err, mode="extract").to_text()
    # Strip the opening line by searching from "To enable" onward.
    explain_body = explain_text[explain_text.find("To enable"):]
    extract_body = extract_text[extract_text.find("To enable"):]
    assert explain_body == extract_body


# ── Text rendering ──────────────────────────────────────────


def test_text_is_bracket_wrapped():
    text = make_degradation_notice(LLMUnavailable("diag")).to_text()
    assert text.startswith("[Note:")
    assert text.endswith("]")


def test_text_lists_all_three_suggestions_numbered():
    text = make_degradation_notice(LLMUnavailable("diag")).to_text()
    # Numbered list per spec example.
    assert "\n1. " in text
    assert "\n2. " in text
    assert "\n3. " in text


def test_text_includes_diagnostic_line():
    text = make_degradation_notice(
        LLMUnavailable("Ollama not responding on http://127.0.0.1:11434")
    ).to_text()
    assert "Diagnostic: Ollama not responding on http://127.0.0.1:11434" in text


def test_text_includes_specific_suggestion_when_present():
    text = make_degradation_notice(
        ModelNotFound("missing", suggestion="Try foo instead.")
    ).to_text()
    assert "Suggestion: Try foo instead." in text


def test_text_omits_suggestion_line_when_blank():
    text = make_degradation_notice(LLMUnavailable("diag")).to_text()
    assert "Suggestion:" not in text


# ── JSON envelope (explain mode) ────────────────────────────


def test_explain_envelope_shape():
    notice = make_degradation_notice(
        LLMUnavailable("Ollama not running on http://localhost:11434"),
        mode="explain",
    )
    envelope = notice.to_explain_envelope(
        command="rules",
        structured_output={"firings": [{"id": "f1"}]},
    )
    assert envelope["command"] == "rules"
    assert envelope["structured_output"] == {"firings": [{"id": "f1"}]}
    assert envelope["interpretation"] is None
    skipped = envelope["interpretation_skipped"]
    assert skipped["reason"] == "no_llm_available"
    assert skipped["diagnostic"] == "Ollama not running on http://localhost:11434"
    assert isinstance(skipped["suggestions"], list)
    assert len(skipped["suggestions"]) == 3


def test_explain_envelope_suggestions_structure():
    """Each suggestion dict carries `option` + `description`; URLs / instructions
    only when the suggestion has them. Tauri parses on these keys."""
    notice = make_degradation_notice(LLMUnavailable("diag"))
    envelope = notice.to_explain_envelope(command="rules", structured_output={})
    suggestions = envelope["interpretation_skipped"]["suggestions"]
    by_option = {s["option"]: s for s in suggestions}

    assert "instructions" in by_option["install_ollama"]
    assert "url" not in by_option["install_ollama"]

    assert "instructions" in by_option["configure_remote"]
    assert "url" not in by_option["configure_remote"]

    assert "url" in by_option["use_copilot"]
    assert "instructions" not in by_option["use_copilot"]


def test_explain_envelope_passes_through_list_structured_output():
    """Some commands (e.g. rules) emit a list, not a dict — spec §4.5
    allows either at the structured_output position."""
    notice = make_degradation_notice(LLMUnavailable("diag"))
    envelope = notice.to_explain_envelope(
        command="rules",
        structured_output=[{"id": "f1"}, {"id": "f2"}],
    )
    assert envelope["structured_output"] == [{"id": "f1"}, {"id": "f2"}]


# ── JSON envelope (extract mode) ────────────────────────────


def test_extract_envelope_shape():
    notice = make_degradation_notice(
        LLMUnavailable("Ollama not running"),
        mode="extract",
    )
    envelope = notice.to_extract_envelope()
    assert envelope == {
        "command": "extract",
        "status": "failed",
        "error": {
            "reason": "no_llm_available",
            "diagnostic": "Ollama not running",
            "suggestions": envelope["error"]["suggestions"],  # checked separately
        },
    }
    assert len(envelope["error"]["suggestions"]) == 3


def test_extract_envelope_with_specific_suggestion():
    notice = make_degradation_notice(
        ContextWindowExceeded(
            "Document my-validation-report.pdf is 180K tokens, exceeds bundled Qwen 32K context window",
            suggestion="Configure a remote backend with a larger context window.",
        ),
        mode="extract",
    )
    envelope = notice.to_extract_envelope()
    assert envelope["error"]["reason"] == "context_window_exceeded"
    assert envelope["error"]["suggestion"] == (
        "Configure a remote backend with a larger context window."
    )


# ── Spec §6.4 invariant: notice never echoes credential material ────


def test_notice_never_echoes_credential_in_diagnostic():
    """LLMError construction in errors.py is the guarantor — this test
    documents the invariant from the consumer side and will fail loudly if
    a future change introduces a leak path."""
    # Simulate a backend that did NOT echo the key (correct behavior).
    err = AuthenticationError("anthropic authentication failed")
    notice = make_degradation_notice(err)
    text = notice.to_text()
    json_envelope = notice.to_explain_envelope(command="rules", structured_output={})
    for s in (text, str(json_envelope)):
        assert "sk-" not in s
        assert "Bearer " not in s
        assert "anthropic-key" not in s


# ── Failure-mode table coverage check (spec §3.7) ──────────


@pytest.mark.parametrize("error_cls,diagnostic_match", [
    # Each row of spec §3.7's failure-mode table maps to one of these errors.
    # The diagnostic strings here are representative — what matters is that
    # the constructed notice carries the diagnostic and a coherent reason.
    (LLMUnavailable,        "Ollama service not responding on http://localhost:11434"),
    (BackendNotInstalled,   "litellm is not installed"),
    (ConfigError,           "Environment variable ANTHROPIC_API_KEY not set"),
    (AuthenticationError,   "anthropic authentication failed"),
    (RateLimited,           "openai returned rate limit error: 429"),
    (ModelNotFound,         "Model claude-foo-bar not found on anthropic"),
    (LLMUnavailable,        "Cannot reach anthropic: dns lookup failed"),
    (LLMTimeoutError,       "Request to anthropic timed out"),
    (ContextWindowExceeded, "Prompt exceeds qwen3.5:4b context window: 180000 > 32768"),
])
def test_each_spec_failure_mode_round_trips(error_cls, diagnostic_match):
    err = error_cls(diagnostic_match)
    notice = make_degradation_notice(err)
    # Reason is non-empty and stable.
    assert notice.reason
    # Diagnostic survives intact.
    assert notice.diagnostic == diagnostic_match
    # Both render targets work without crashing.
    notice.to_text()
    notice.to_explain_envelope(command="rules", structured_output={})
    notice.to_extract_envelope()

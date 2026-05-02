"""Tests for the uofa_cli.llm Protocol + MockBackend (spec v0.4 §4.8)."""

from __future__ import annotations

import pytest

from uofa_cli.llm import (
    AuthenticationError,
    BackendNotInstalled,
    ConfigError,
    ContextWindowExceeded,
    GenerationOptions,
    HealthStatus,
    LLMBackend,
    LLMError,
    LLMUnavailable,
    MockBackend,
    ModelNotFound,
    RateLimited,
)


# ── Protocol conformance ────────────────────────────────────


def test_mock_backend_satisfies_protocol():
    """MockBackend should be a structurally-valid LLMBackend."""
    backend = MockBackend()
    assert isinstance(backend, LLMBackend)


def test_protocol_methods_are_all_callable():
    """Smoke-test every Protocol method on MockBackend."""
    backend = MockBackend()
    assert isinstance(backend.name(), str)
    assert isinstance(backend.model(), str)
    assert isinstance(backend.supports_seed(), bool)
    assert isinstance(backend.supports_temperature(), bool)
    assert isinstance(backend.supports_streaming(), bool)
    assert isinstance(backend.supports_structured_output(), bool)
    assert isinstance(backend.max_context_tokens(), int)
    assert isinstance(backend.estimate_cost(0, 0), float)


# ── MockBackend behavior ────────────────────────────────────


def test_mock_default_response():
    backend = MockBackend(default_response="hello world")
    assert backend.generate("any prompt", GenerationOptions()) == "hello world"


def test_mock_canned_response_substring_match():
    backend = MockBackend(
        default_response="default",
        responses={"firing": "firing-explanation", "violation": "violation-explanation"},
    )
    assert backend.generate("explain this firing please", GenerationOptions()) == "firing-explanation"
    assert backend.generate("about a SHACL violation", GenerationOptions()) == "violation-explanation"
    assert backend.generate("unrelated prompt", GenerationOptions()) == "default"


def test_mock_canned_response_first_match_wins():
    backend = MockBackend(
        responses={
            "firing": "first",
            "fir": "second",  # also matches "firing"
        },
    )
    assert backend.generate("firing", GenerationOptions()) == "first"


def test_mock_streaming_yields_tokens():
    backend = MockBackend(default_response="one two three")
    chunks = list(backend.generate_streaming("anything", GenerationOptions()))
    assert "".join(chunks).strip() == "one two three"
    assert len(chunks) == 3


def test_mock_structured_canned():
    backend = MockBackend(
        structured_responses={"extract": {"foo": "bar"}},
    )
    out = backend.generate_structured("please extract", {}, GenerationOptions())
    assert out == {"foo": "bar"}


def test_mock_structured_falls_back_to_json_default():
    backend = MockBackend(default_response='{"foo": 1}')
    out = backend.generate_structured("anything", {}, GenerationOptions())
    assert out == {"foo": 1}


def test_mock_structured_returns_empty_when_default_not_json():
    backend = MockBackend(default_response="not json")
    out = backend.generate_structured("anything", {}, GenerationOptions())
    assert out == {}


def test_mock_call_log():
    """Tests should be able to assert on what was called and with what options."""
    backend = MockBackend()
    opts = GenerationOptions(temperature=0.7, seed=42)
    backend.generate("p1", opts)
    list(backend.generate_streaming("p2", opts))
    backend.generate_structured("p3", {}, opts)

    methods = [c[0] for c in backend.calls]
    assert methods == ["generate", "generate_streaming", "generate_structured"]
    assert all(c[2] is opts for c in backend.calls)


def test_mock_health_check_healthy_by_default():
    assert MockBackend().health_check().ok is True


def test_mock_health_check_can_be_unhealthy():
    backend = MockBackend(healthy=False, unhealthy_diagnostic="nope")
    status = backend.health_check()
    assert status.ok is False
    assert status.diagnostic == "nope"
    assert status.suggestion  # populated


# ── GenerationOptions / HealthStatus ────────────────────────


def test_generation_options_defaults_are_none():
    opts = GenerationOptions()
    assert opts.temperature is None
    assert opts.max_tokens is None
    assert opts.seed is None
    assert opts.timeout_seconds is None
    assert opts.extra == {}


def test_generation_options_is_immutable():
    """Frozen dataclass — attempts to mutate should raise."""
    opts = GenerationOptions()
    with pytest.raises(Exception):  # FrozenInstanceError on Py3.10+
        opts.temperature = 0.5  # type: ignore[misc]


def test_health_status_healthy_helper():
    h = HealthStatus.healthy()
    assert h.ok is True
    assert h.diagnostic == ""
    assert h.suggestion == ""


# ── Error hierarchy ─────────────────────────────────────────


def test_all_errors_inherit_from_llm_error():
    """The graceful-degradation formatter dispatches on LLMError as the
    common base — every concrete error must inherit from it."""
    for cls in (
        LLMUnavailable,
        BackendNotInstalled,
        AuthenticationError,
        RateLimited,
        ModelNotFound,
        ContextWindowExceeded,
        ConfigError,
    ):
        assert issubclass(cls, LLMError)


def test_llm_error_carries_diagnostic_and_suggestion():
    err = LLMError("something broke", suggestion="try X")
    assert err.diagnostic == "something broke"
    assert err.suggestion == "try X"
    assert str(err) == "something broke"


def test_rate_limited_carries_retry_after():
    err = RateLimited("429", retry_after_seconds=12.0)
    assert err.retry_after_seconds == 12.0


def test_context_window_exceeded_carries_token_counts():
    err = ContextWindowExceeded(
        "too big", prompt_tokens=180_000, max_context_tokens=32_768
    )
    assert err.prompt_tokens == 180_000
    assert err.max_context_tokens == 32_768

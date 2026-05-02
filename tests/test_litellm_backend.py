"""Tests for LiteLLMBackend.

Tests stub `litellm` via monkeypatch so no real network calls are made. Real
end-to-end smoke tests against Ollama / Anthropic / OpenAI live in
`tests/integration/` (not yet present; gated on credentials in CI).
"""

from __future__ import annotations

import json
import sys
import types
from typing import Iterator

import pytest

from uofa_cli.llm import (
    AuthenticationError,
    BackendNotInstalled,
    ContextWindowExceeded,
    GenerationOptions,
    LLMBackend,
    LLMError,
    LLMTimeoutError,
    LiteLLMBackend,
    LLMUnavailable,
    ModelNotFound,
    RateLimited,
)


# ── Fake litellm fixture ────────────────────────────────────


class _FakeMessage:
    def __init__(self, content: str):
        self.content = content


class _FakeChoice:
    def __init__(self, content: str):
        self.message = _FakeMessage(content)


class _FakeChoiceDelta:
    def __init__(self, content: str | None):
        self.delta = types.SimpleNamespace(content=content)


class _FakeResponse:
    def __init__(self, content: str):
        self.choices = [_FakeChoice(content)]


class _FakeStream:
    def __init__(self, parts: list[str]):
        self._parts = parts

    def __iter__(self) -> Iterator[object]:
        for p in self._parts:
            yield types.SimpleNamespace(choices=[_FakeChoiceDelta(p)])


@pytest.fixture
def fake_litellm(monkeypatch):
    """Install a fake `litellm` module with a stub `completion()`.

    The fake captures kwargs in `last_kwargs` and returns whatever is set on
    `next_response` (or raises `next_exception`).
    """
    fake = types.ModuleType("litellm")
    fake.last_kwargs = None
    fake.next_response = _FakeResponse("default text")
    fake.next_exception = None

    def completion(**kwargs):
        fake.last_kwargs = kwargs
        if fake.next_exception is not None:
            raise fake.next_exception
        return fake.next_response

    fake.completion = completion
    fake.cost_per_token = lambda **kw: (0.001, 0.002)
    fake.get_model_info = lambda model: {"max_input_tokens": 200_000}

    # Mirror the exception hierarchy litellm exposes — the wrapper imports
    # them by name from litellm.exceptions.
    exc_mod = types.ModuleType("litellm.exceptions")

    class _LE(Exception):
        pass

    class APIError(_LE): pass
    class APIConnectionError(_LE): pass
    class AuthenticationError(_LE): pass
    class BadRequestError(_LE): pass
    class ContextWindowExceededError(_LE): pass
    class NotFoundError(_LE): pass
    class RateLimitError(_LE):
        def __init__(self, msg, retry_after=None):
            super().__init__(msg)
            self.retry_after = retry_after
    class ServiceUnavailableError(_LE): pass
    class Timeout(_LE): pass

    exc_mod.APIError = APIError
    exc_mod.APIConnectionError = APIConnectionError
    exc_mod.AuthenticationError = AuthenticationError
    exc_mod.BadRequestError = BadRequestError
    exc_mod.ContextWindowExceededError = ContextWindowExceededError
    exc_mod.NotFoundError = NotFoundError
    exc_mod.RateLimitError = RateLimitError
    exc_mod.ServiceUnavailableError = ServiceUnavailableError
    exc_mod.Timeout = Timeout
    fake.exceptions = exc_mod

    monkeypatch.setitem(sys.modules, "litellm", fake)
    monkeypatch.setitem(sys.modules, "litellm.exceptions", exc_mod)
    return fake


# ── Identity + capability ───────────────────────────────────


def test_litellm_backend_satisfies_protocol():
    b = LiteLLMBackend(backend_name="anthropic", model_name="claude-sonnet-5-2026")
    assert isinstance(b, LLMBackend)


def test_unknown_backend_rejected():
    with pytest.raises(ValueError, match="Unknown backend"):
        LiteLLMBackend(backend_name="bogus-provider", model_name="x")


def test_ollama_default_base_url():
    b = LiteLLMBackend(backend_name="ollama", model_name="qwen3.5:4b")
    assert b.base_url == "http://127.0.0.1:11434"


def test_capability_flags_per_backend():
    ollama = LiteLLMBackend(backend_name="ollama", model_name="qwen3.5:4b")
    anthropic = LiteLLMBackend(backend_name="anthropic", model_name="claude")
    assert ollama.supports_seed() is True
    assert anthropic.supports_seed() is False  # spec §4.8 table
    assert ollama.supports_streaming() is True
    assert anthropic.supports_streaming() is True
    # Ollama structured output is disabled in v0.6.0 (litellm + qwen3.5
    # bug; see note in litellm_backend._DEFAULT_CAPS). Anthropic has it
    # via tool use.
    assert ollama.supports_structured_output() is False
    assert anthropic.supports_structured_output() is True


def test_capability_overrides():
    b = LiteLLMBackend(
        backend_name="openai-compatible",
        model_name="custom",
        capability_overrides={"supports_structured_output": True, "max_context_tokens": 1_000_000},
    )
    assert b.supports_structured_output() is True
    assert b.max_context_tokens() == 1_000_000


def test_max_context_prefers_litellm_runtime_info(fake_litellm):
    b = LiteLLMBackend(backend_name="anthropic", model_name="claude")
    assert b.max_context_tokens() == 200_000  # from fake get_model_info


# ── Routing: backend → litellm model string ─────────────────


def test_routing_anthropic(fake_litellm):
    b = LiteLLMBackend(
        backend_name="anthropic",
        model_name="claude-sonnet-5-2026",
        api_key="test-key",
    )
    b.generate("hello", GenerationOptions())
    assert fake_litellm.last_kwargs["model"] == "anthropic/claude-sonnet-5-2026"
    assert fake_litellm.last_kwargs["api_key"] == "test-key"


def test_routing_openai_compatible_uses_openai_prefix_and_api_base(fake_litellm):
    b = LiteLLMBackend(
        backend_name="openai-compatible",
        model_name="meta-llama/Llama-3.3-70B-Instruct",
        api_key="key",
        base_url="https://api.together.xyz/v1",
    )
    b.generate("hi", GenerationOptions())
    assert fake_litellm.last_kwargs["model"] == "openai/meta-llama/Llama-3.3-70B-Instruct"
    assert fake_litellm.last_kwargs["api_base"] == "https://api.together.xyz/v1"


def test_routing_ollama_uses_direct_http(monkeypatch):
    """In v0.6.0 Ollama bypasses litellm and goes through direct /api/chat.

    Background: litellm's `ollama_chat/` provider returns empty content
    intermittently for thinking-capable models (qwen3.5+), even with
    `think:False`. The legacy extract code (pre-v0.6.0) used direct HTTP
    and was reliable; we restore that path for Ollama specifically while
    other backends keep using litellm.
    """
    import requests

    captured: dict = {}

    class _FakeResp:
        status_code = 200
        text = ""

        def raise_for_status(self): pass

        def json(self):
            return {"message": {"content": "DIRECT-HTTP RESPONSE"}}

    def _fake_post(url, json=None, timeout=None):  # noqa: A002
        captured["url"] = url
        captured["payload"] = json
        captured["timeout"] = timeout
        return _FakeResp()

    monkeypatch.setattr(requests, "post", _fake_post)

    b = LiteLLMBackend(backend_name="ollama", model_name="qwen3.5:4b")
    out = b.generate("hi", GenerationOptions())
    assert out == "DIRECT-HTTP RESPONSE"
    assert captured["url"] == "http://127.0.0.1:11434/api/chat"
    assert captured["payload"]["model"] == "qwen3.5:4b"
    assert captured["payload"]["messages"] == [{"role": "user", "content": "hi"}]
    assert captured["payload"]["stream"] is False


# ── GenerationOptions plumbing ──────────────────────────────


def test_temperature_passed_when_supported(fake_litellm):
    b = LiteLLMBackend(backend_name="anthropic", model_name="claude")
    b.generate("hi", GenerationOptions(temperature=0.3))
    assert fake_litellm.last_kwargs["temperature"] == 0.3


def test_seed_dropped_when_unsupported(fake_litellm):
    b = LiteLLMBackend(backend_name="anthropic", model_name="claude")  # supports_seed=False
    b.generate("hi", GenerationOptions(seed=42))
    assert "seed" not in fake_litellm.last_kwargs


def test_seed_passed_when_supported(fake_litellm):
    # OpenAI advertises supports_seed=True; Ollama does too but goes
    # through the direct-HTTP path (covered separately).
    b = LiteLLMBackend(backend_name="openai", model_name="gpt-4o", api_key="k")
    b.generate("hi", GenerationOptions(seed=42))
    assert fake_litellm.last_kwargs["seed"] == 42


def test_extra_kwargs_merged_for_litellm_backends(fake_litellm):
    """For non-Ollama backends, GenerationOptions.extra forwards as
    top-level litellm kwargs (matches pre-v0.6.0 behavior). Ollama has
    its own forwarding path tested in test_ollama_direct_*."""
    b = LiteLLMBackend(backend_name="anthropic", model_name="claude")
    b.generate("hi", GenerationOptions(extra={"my_custom_kwarg": "value"}))
    assert fake_litellm.last_kwargs["my_custom_kwarg"] == "value"


def test_ollama_direct_forwards_think_extra(monkeypatch):
    """Ollama's direct-HTTP path puts `think` at the payload top level
    (matches the daemon's API), not inside `options`."""
    import requests

    captured: dict = {}

    class _FakeResp:
        status_code = 200
        def raise_for_status(self): pass
        def json(self): return {"message": {"content": "ok"}}

    def _fake_post(url, json=None, timeout=None):  # noqa: A002
        captured.update(json)
        return _FakeResp()

    monkeypatch.setattr(requests, "post", _fake_post)
    b = LiteLLMBackend(backend_name="ollama", model_name="qwen3.5:4b")
    b.generate("hi", GenerationOptions(extra={"think": False}))
    assert captured["think"] is False


def test_ollama_direct_forwards_temperature_and_max_tokens(monkeypatch):
    """temperature / max_tokens land in payload['options'] per Ollama API."""
    import requests

    captured: dict = {}

    class _FakeResp:
        status_code = 200
        def raise_for_status(self): pass
        def json(self): return {"message": {"content": "ok"}}

    def _fake_post(url, json=None, timeout=None):  # noqa: A002
        captured.update(json)
        return _FakeResp()

    monkeypatch.setattr(requests, "post", _fake_post)
    b = LiteLLMBackend(backend_name="ollama", model_name="qwen3.5:4b")
    b.generate("hi", GenerationOptions(temperature=0.3, max_tokens=512, seed=7))
    assert captured["options"]["temperature"] == 0.3
    assert captured["options"]["num_predict"] == 512
    assert captured["options"]["seed"] == 7


def test_default_timeout_used_when_none(fake_litellm):
    b = LiteLLMBackend(backend_name="anthropic", model_name="claude", default_timeout_seconds=99.0)
    b.generate("hi", GenerationOptions())
    assert fake_litellm.last_kwargs["timeout"] == 99.0


def test_per_call_timeout_overrides_default(fake_litellm):
    b = LiteLLMBackend(backend_name="anthropic", model_name="claude")
    b.generate("hi", GenerationOptions(timeout_seconds=12.0))
    assert fake_litellm.last_kwargs["timeout"] == 12.0


# ── Generation forms ────────────────────────────────────────


def test_generate_returns_text(fake_litellm):
    fake_litellm.next_response = _FakeResponse("the actual response")
    b = LiteLLMBackend(backend_name="anthropic", model_name="claude")
    assert b.generate("hi", GenerationOptions()) == "the actual response"


def test_generate_streaming_yields_chunks(fake_litellm):
    fake_litellm.next_response = _FakeStream(["one ", "two ", "three"])
    b = LiteLLMBackend(backend_name="anthropic", model_name="claude")
    chunks = list(b.generate_streaming("hi", GenerationOptions()))
    assert "".join(chunks) == "one two three"


def test_generate_streaming_raises_when_unsupported(fake_litellm):
    b = LiteLLMBackend(
        backend_name="anthropic", model_name="claude",
        capability_overrides={"supports_streaming": False},
    )
    with pytest.raises(NotImplementedError):
        list(b.generate_streaming("hi", GenerationOptions()))


def test_generate_structured_returns_parsed_dict(fake_litellm):
    fake_litellm.next_response = _FakeResponse('{"foo": "bar"}')
    b = LiteLLMBackend(backend_name="anthropic", model_name="claude")
    out = b.generate_structured("hi", {}, GenerationOptions())
    assert out == {"foo": "bar"}
    assert fake_litellm.last_kwargs["response_format"] == {"type": "json_object"}


def test_generate_structured_wraps_invalid_json(fake_litellm):
    fake_litellm.next_response = _FakeResponse("not valid json")
    b = LiteLLMBackend(backend_name="anthropic", model_name="claude")
    with pytest.raises(LLMError, match="non-JSON"):
        b.generate_structured("hi", {}, GenerationOptions())


def test_generate_structured_raises_when_unsupported(fake_litellm):
    b = LiteLLMBackend(
        backend_name="openai-compatible", model_name="x",
    )  # default has supports_structured_output=False
    with pytest.raises(NotImplementedError):
        b.generate_structured("hi", {}, GenerationOptions())


# ── Error normalization ─────────────────────────────────────


def test_authentication_error_normalized(fake_litellm):
    fake_litellm.next_exception = fake_litellm.exceptions.AuthenticationError("401")
    b = LiteLLMBackend(backend_name="anthropic", model_name="claude")
    with pytest.raises(AuthenticationError) as exc:
        b.generate("hi", GenerationOptions())
    # Diagnostic must NOT echo any credential material
    assert "test-key" not in str(exc.value)
    assert "anthropic" in str(exc.value)


def test_rate_limit_carries_retry_after(fake_litellm):
    fake_litellm.next_exception = fake_litellm.exceptions.RateLimitError("429", retry_after=15)
    b = LiteLLMBackend(backend_name="openai", model_name="gpt-4o")
    with pytest.raises(RateLimited) as exc:
        b.generate("hi", GenerationOptions())
    assert exc.value.retry_after_seconds == 15.0


def test_timeout_normalized(fake_litellm):
    fake_litellm.next_exception = fake_litellm.exceptions.Timeout("slow")
    b = LiteLLMBackend(backend_name="anthropic", model_name="claude")
    with pytest.raises(LLMTimeoutError):
        b.generate("hi", GenerationOptions())


def test_context_window_exceeded_normalized(fake_litellm):
    # Use anthropic so the call goes through the litellm-routed path and
    # the fake's `next_exception` actually fires. (Ollama bypasses litellm
    # in v0.6.0; its context-window failures surface differently.)
    fake_litellm.next_exception = fake_litellm.exceptions.ContextWindowExceededError("too big")
    b = LiteLLMBackend(backend_name="anthropic", model_name="claude")
    with pytest.raises(ContextWindowExceeded):
        b.generate("x" * 10_000, GenerationOptions())


def test_not_found_normalized(fake_litellm):
    fake_litellm.next_exception = fake_litellm.exceptions.NotFoundError("no such model")
    b = LiteLLMBackend(backend_name="anthropic", model_name="claude-foo-bar")
    with pytest.raises(ModelNotFound):
        b.generate("hi", GenerationOptions())


def test_connection_error_normalized(fake_litellm):
    fake_litellm.next_exception = fake_litellm.exceptions.APIConnectionError("dns fail")
    b = LiteLLMBackend(backend_name="anthropic", model_name="claude")
    with pytest.raises(LLMUnavailable):
        b.generate("hi", GenerationOptions())


def test_unknown_exception_falls_through_to_llm_error(fake_litellm):
    class WeirdError(Exception):
        pass
    fake_litellm.next_exception = WeirdError("???")
    b = LiteLLMBackend(backend_name="anthropic", model_name="claude")
    with pytest.raises(LLMError) as exc:
        b.generate("hi", GenerationOptions())
    # Must not be one of the more specific subclasses
    assert type(exc.value) is LLMError


# ── Backend-not-installed path ──────────────────────────────


def test_backend_not_installed_when_litellm_missing(monkeypatch):
    """Simulate `litellm` being absent — the wrapper must surface
    BackendNotInstalled, not crash with a raw ImportError."""
    # Force the lazy-import to fail
    monkeypatch.setitem(sys.modules, "litellm", None)
    b = LiteLLMBackend(backend_name="anthropic", model_name="claude")
    with pytest.raises(BackendNotInstalled, match="litellm"):
        b.generate("hi", GenerationOptions())


# ── Cost ────────────────────────────────────────────────────


def test_cost_for_remote_uses_litellm_pricing(fake_litellm):
    b = LiteLLMBackend(backend_name="anthropic", model_name="claude")
    cost = b.estimate_cost(1000, 500)
    assert cost == pytest.approx(0.003)  # 0.001 + 0.002 from fake


def test_cost_for_ollama_is_zero():
    b = LiteLLMBackend(backend_name="ollama", model_name="qwen3.5:4b")
    assert b.estimate_cost(1_000_000, 500_000) == 0.0


def test_cost_returns_zero_when_pricing_table_misses(fake_litellm):
    def boom(**kw): raise KeyError("no entry")
    fake_litellm.cost_per_token = boom
    b = LiteLLMBackend(backend_name="anthropic", model_name="claude")
    assert b.estimate_cost(100, 50) == 0.0


# ── Health check ────────────────────────────────────────────


def test_remote_health_check_returns_healthy_without_call():
    """Remote backends shouldn't burn money on health checks."""
    b = LiteLLMBackend(backend_name="anthropic", model_name="claude")
    assert b.health_check().ok is True


def test_ollama_health_check_unreachable(monkeypatch):
    """Simulate Ollama daemon not running."""
    import requests
    def boom(*a, **kw): raise requests.ConnectionError("nope")
    monkeypatch.setattr(requests, "get", boom)
    b = LiteLLMBackend(backend_name="ollama", model_name="qwen3.5:4b")
    status = b.health_check()
    assert status.ok is False
    assert "not responding" in status.diagnostic
    assert "ollama serve" in status.suggestion.lower() or "uofa setup" in status.suggestion.lower()


def test_ollama_health_check_model_not_pulled(monkeypatch):
    """Daemon up but configured model missing."""
    import requests
    class _Resp:
        status_code = 200
        def json(self): return {"models": [{"name": "llama3:8b"}]}
    monkeypatch.setattr(requests, "get", lambda *a, **kw: _Resp())
    b = LiteLLMBackend(backend_name="ollama", model_name="qwen3.5:4b")
    status = b.health_check()
    assert status.ok is False
    assert "qwen3.5:4b" in status.diagnostic
    assert "ollama pull" in status.suggestion


def test_ollama_health_check_happy_path(monkeypatch):
    import requests
    class _Resp:
        status_code = 200
        def json(self): return {"models": [{"name": "qwen3.5:4b"}]}
    monkeypatch.setattr(requests, "get", lambda *a, **kw: _Resp())
    b = LiteLLMBackend(backend_name="ollama", model_name="qwen3.5:4b")
    assert b.health_check().ok is True

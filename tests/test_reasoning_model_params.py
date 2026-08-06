"""OpenAI's reasoning-era models reject two parameters every other model takes.

Both are hard 400s, so every call fails and nothing is billed. That is why a
3-bundle dry run caught them for $0.00 before a 50-bundle generation run:

    Unsupported parameter: 'max_tokens' is not supported with this model.
    Use 'max_completion_tokens' instead.

    Unsupported value: 'temperature' does not support 0.7 with this model.
    Only the default (1) value is supported.

Anthropic and the older OpenAI models still take both, so neither can be
switched globally -- they are chosen per model.
"""

from __future__ import annotations

import pytest

from uofa_cli.llm.backend import GenerationOptions
from uofa_cli.llm.litellm_backend import LiteLLMBackend, _gpt5_or_later


def _backend(backend_name: str, model: str, **kw) -> LiteLLMBackend:
    return LiteLLMBackend(backend_name=backend_name, model_name=model,
                          api_key="test-key", **kw)


@pytest.mark.parametrize("name,expected", [
    ("gpt-5", True), ("gpt-5-mini", True), ("gpt-5.4", True), ("gpt-6", True),
    ("gpt-4o", False), ("gpt-4.1", False), ("gpt-4o-mini", False),
    ("claude-sonnet-4-6", False), ("o1-preview", False), ("", False),
])
def test_gpt5_or_later_compares_the_major_version_numerically(name, expected):
    """A prefix test would catch gpt-4.1 or miss gpt-6.

    gpt-4.1 and gpt-4o take the old parameters; gpt-5 and anything after it do
    not. Comparing the major version as an integer covers a future gpt-6
    without another edit.
    """
    assert _gpt5_or_later(name) is expected


@pytest.mark.parametrize("backend_name,model,param", [
    ("openai", "gpt-5", "max_completion_tokens"),
    ("openai", "gpt-5-mini", "max_completion_tokens"),
    ("openai", "o1-preview", "max_completion_tokens"),
    ("openai", "o3-mini", "max_completion_tokens"),
    ("openai", "gpt-4o", "max_tokens"),
    ("openai", "gpt-4.1", "max_tokens"),
    ("anthropic", "claude-sonnet-4-6", "max_tokens"),
])
def test_output_budget_parameter_is_chosen_per_model(backend_name, model, param):
    assert _backend(backend_name, model).max_tokens_param() == param


@pytest.mark.parametrize("backend_name,model,allowed", [
    ("openai", "gpt-5", False),
    ("openai", "o1-preview", False),
    ("openai", "gpt-4o", True),
    ("anthropic", "claude-sonnet-4-6", True),
])
def test_temperature_is_withheld_from_models_that_only_accept_the_default(
        backend_name, model, allowed):
    assert _backend(backend_name, model).supports_temperature() is allowed


def test_an_explicit_capability_override_still_wins():
    """The model check is a default, not a lock.

    A caller who knows the API has changed can force it without editing this
    file.
    """
    b = _backend("openai", "gpt-5",
                 capability_overrides={"supports_temperature": True})
    assert b.supports_temperature() is True


def test_the_request_carries_the_right_keys_for_a_reasoning_model():
    """The end-to-end assertion: what actually goes on the wire.

    Sending `max_tokens` or a non-default `temperature` to gpt-5 is a 400, so
    the kwargs must carry neither.
    """
    opts = GenerationOptions(temperature=0.7, max_tokens=4096)

    gpt5 = _backend("openai", "gpt-5")._completion_kwargs("hello", opts)
    assert "max_tokens" not in gpt5
    assert gpt5["max_completion_tokens"] == 4096
    assert "temperature" not in gpt5, (
        "gpt-5 accepts temperature only at its default; sending 0.7 is a 400")

    gpt4o = _backend("openai", "gpt-4o")._completion_kwargs("hello", opts)
    assert gpt4o["max_tokens"] == 4096
    assert "max_completion_tokens" not in gpt4o
    assert gpt4o["temperature"] == 0.7

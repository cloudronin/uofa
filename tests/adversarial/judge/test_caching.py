"""Tests for cache-key construction."""

from __future__ import annotations

import pytest

from uofa_cli.adversarial.judge.caching import (
    build_cache_key,
    is_cacheable_prefix_size,
)


class TestBuildCacheKey:
    def test_key_starts_with_uofa_provider_model(self) -> None:
        k = build_cache_key("openai", "static prefix", "gpt-5.4")
        assert k.startswith("uofa:openai:gpt-5.4:")

    def test_same_inputs_produce_same_key(self) -> None:
        k1 = build_cache_key("openai", "static prefix", "gpt-5.4")
        k2 = build_cache_key("openai", "static prefix", "gpt-5.4")
        assert k1 == k2

    def test_prefix_change_invalidates_key(self) -> None:
        k1 = build_cache_key("openai", "v1.0.0 prefix", "gpt-5.4")
        k2 = build_cache_key("openai", "v1.0.1 prefix", "gpt-5.4")
        assert k1 != k2

    def test_model_change_invalidates_key(self) -> None:
        k1 = build_cache_key("openai", "prefix", "gpt-5.4")
        k2 = build_cache_key("openai", "prefix", "gpt-5.5")
        assert k1 != k2

    def test_provider_change_invalidates_key(self) -> None:
        k1 = build_cache_key("openai", "prefix", "model")
        k2 = build_cache_key("gemini", "prefix", "model")
        assert k1 != k2

    def test_hash_is_16_hex_chars(self) -> None:
        k = build_cache_key("openai", "prefix", "gpt-5.4")
        suffix = k.split(":")[-1]
        assert len(suffix) == 16
        assert all(c in "0123456789abcdef" for c in suffix)

    def test_empty_provider_raises(self) -> None:
        with pytest.raises(ValueError):
            build_cache_key("", "prefix", "model")

    def test_empty_model_raises(self) -> None:
        with pytest.raises(ValueError):
            build_cache_key("openai", "prefix", "")


class TestIsCacheablePrefixSize:
    def test_short_prefix_not_cacheable_with_default_threshold(self) -> None:
        assert is_cacheable_prefix_size("short text") is False

    def test_long_prefix_is_cacheable(self) -> None:
        # 1024 tokens ≈ 4096 chars by the heuristic.
        long = "x" * 5000
        assert is_cacheable_prefix_size(long) is True

    def test_custom_threshold_overrides_default(self) -> None:
        # 100-token threshold, 50-char text ≈ 12 tokens.
        assert is_cacheable_prefix_size("x" * 50, min_tokens=100) is False
        # 100-token threshold, 500-char text ≈ 125 tokens.
        assert is_cacheable_prefix_size("x" * 500, min_tokens=100) is True


# ── Wave H: vendor cache wire-up ────────────────────────────────────────


class TestApplyCacheControlToMessages:
    def test_anthropic_promotes_string_content_to_tagged_block(self) -> None:
        from uofa_cli.adversarial.judge.caching import apply_cache_control_to_messages

        messages = [
            {"role": "system", "content": "static prefix"},
            {"role": "user", "content": "case content"},
        ]
        out = apply_cache_control_to_messages(messages, "anthropic")
        assert out is messages  # in-place
        assert isinstance(messages[0]["content"], list)
        first_block = messages[0]["content"][0]
        assert first_block["type"] == "text"
        assert first_block["cache_control"] == {"type": "ephemeral"}

    def test_anthropic_already_structured_content_tags_first_block(self) -> None:
        from uofa_cli.adversarial.judge.caching import apply_cache_control_to_messages

        messages = [
            {
                "role": "system",
                "content": [{"type": "text", "text": "prefix"}],
            }
        ]
        apply_cache_control_to_messages(messages, "anthropic")
        assert messages[0]["content"][0]["cache_control"] == {"type": "ephemeral"}

    def test_openai_messages_unchanged(self) -> None:
        from uofa_cli.adversarial.judge.caching import apply_cache_control_to_messages

        messages = [
            {"role": "system", "content": "prefix"},
            {"role": "user", "content": "case"},
        ]
        before = [dict(m) for m in messages]
        apply_cache_control_to_messages(messages, "openai")
        assert messages == before  # unchanged for OpenAI implicit caching

    def test_gemini_messages_unchanged(self) -> None:
        from uofa_cli.adversarial.judge.caching import apply_cache_control_to_messages

        messages = [{"role": "system", "content": "prefix"}]
        before = [dict(m) for m in messages]
        apply_cache_control_to_messages(messages, "gemini")
        assert messages == before  # Gemini caches via cached_content, not messages

    def test_disable_cache_static_prefix_skips_mutation(self) -> None:
        from uofa_cli.adversarial.judge.caching import apply_cache_control_to_messages

        messages = [{"role": "system", "content": "prefix"}]
        before = [dict(m) for m in messages]
        apply_cache_control_to_messages(
            messages, "anthropic", cache_static_prefix=False,
        )
        assert messages == before

    def test_unknown_provider_token_no_op(self) -> None:
        from uofa_cli.adversarial.judge.caching import apply_cache_control_to_messages

        messages = [{"role": "system", "content": "prefix"}]
        before = [dict(m) for m in messages]
        apply_cache_control_to_messages(messages, "non-existent-provider")
        assert messages == before


class TestGeminiCacheKwargs:
    def test_returns_empty_dict_when_no_resource_id(self) -> None:
        from uofa_cli.adversarial.judge.caching import build_gemini_cache_kwargs

        assert build_gemini_cache_kwargs(None) == {}

    def test_returns_cached_content_kwarg(self) -> None:
        from uofa_cli.adversarial.judge.caching import build_gemini_cache_kwargs

        assert build_gemini_cache_kwargs("caches/abc") == {
            "cached_content": "caches/abc"
        }


class TestGetOrCreateGeminiCache:
    def test_returns_resource_name_on_success(self) -> None:
        from unittest.mock import patch
        from uofa_cli.adversarial.judge.caching import get_or_create_gemini_cache
        from types import SimpleNamespace

        with patch(
            "litellm.create_cached_content",
            return_value=SimpleNamespace(name="caches/abc"),
            create=True,
        ):
            res = get_or_create_gemini_cache(
                model="gemini-3.1-pro", static_prefix="x" * 5000,
                display_name="uofa-static",
            )
        assert res == "caches/abc"

    def test_returns_none_on_litellm_failure(self) -> None:
        from unittest.mock import patch
        from uofa_cli.adversarial.judge.caching import get_or_create_gemini_cache

        with patch(
            "litellm.create_cached_content",
            side_effect=RuntimeError("quota exceeded"),
            create=True,
        ):
            res = get_or_create_gemini_cache(
                model="gemini-3.1-pro", static_prefix="x" * 5000,
                display_name="uofa-static",
            )
        assert res is None

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

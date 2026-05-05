"""Tests for --judges parsing and --parallel validation."""

from __future__ import annotations

import pytest

from uofa_cli.adversarial.judge.cli_args import (
    JudgesConfig,
    PROVIDER_TO_POSITION,
    parse_judges,
    validate_parallel_flag,
)


# ── parse_judges happy path ────────────────────────────────────────────


class TestParseJudgesHappyPath:
    def test_canonical_order(self) -> None:
        cfg = parse_judges("openai,gemini,hf-llama")
        assert cfg.tokens == ("openai", "gemini", "hf-llama")
        assert cfg.positions == ("A", "B", "C")
        assert cfg.is_mock is False

    def test_user_order_is_normalized_to_canonical(self) -> None:
        # User passes them in C, A, B order; cfg.tokens still comes back A, B, C.
        cfg = parse_judges("hf-llama,openai,gemini")
        assert cfg.tokens == ("openai", "gemini", "hf-llama")
        assert cfg.positions == ("A", "B", "C")

    def test_mock_ensemble(self) -> None:
        cfg = parse_judges("mock_a,mock_b,mock_c")
        assert cfg.is_mock is True
        assert cfg.positions == ("A", "B", "C")

    def test_mock_in_arbitrary_order(self) -> None:
        cfg = parse_judges("mock_c,mock_a,mock_b")
        assert cfg.tokens == ("mock_a", "mock_b", "mock_c")

    def test_whitespace_tolerant(self) -> None:
        cfg = parse_judges(" openai , gemini , hf-llama ")
        assert cfg.tokens == ("openai", "gemini", "hf-llama")


# ── parse_judges failure modes ─────────────────────────────────────────


class TestParseJudgesFailureModes:
    def test_empty_raises(self) -> None:
        with pytest.raises(ValueError, match="required"):
            parse_judges("")

    def test_unknown_token_raises(self) -> None:
        with pytest.raises(ValueError, match="unknown judge tokens"):
            parse_judges("openai,gemini,fake-judge")

    def test_missing_position_raises(self) -> None:
        # Only A and B; missing C.
        with pytest.raises(ValueError, match="cover all three positions"):
            parse_judges("openai,gemini")

    def test_duplicate_position_raises(self) -> None:
        # Both openai (A) and mock_a (A) → duplicate position.
        with pytest.raises(ValueError, match="duplicate positions|cannot mix"):
            parse_judges("openai,mock_a,gemini")

    def test_mix_real_and_mock_allowed_for_smoke(self) -> None:
        # Smoke runs intentionally mix one real provider with mocks (e.g.
        # `anthropic,mock_b,mock_c`) to validate the real provider path
        # end-to-end without spending budget on all three. is_mock=False
        # because not all tokens are mocks.
        cfg = parse_judges("anthropic,mock_b,mock_c")
        assert cfg.is_mock is False
        assert cfg.tokens == ("anthropic", "mock_b", "mock_c")


# ── PROVIDER_TO_POSITION map ───────────────────────────────────────────


class TestProviderToPosition:
    def test_real_providers_map_to_canonical_positions(self) -> None:
        assert PROVIDER_TO_POSITION["openai"] == "A"
        assert PROVIDER_TO_POSITION["gemini"] == "B"
        assert PROVIDER_TO_POSITION["hf-llama"] == "C"

    def test_mock_providers_align_with_real_positions(self) -> None:
        assert PROVIDER_TO_POSITION["mock_a"] == "A"
        assert PROVIDER_TO_POSITION["mock_b"] == "B"
        assert PROVIDER_TO_POSITION["mock_c"] == "C"


# ── validate_parallel_flag ─────────────────────────────────────────────


class TestValidateParallelFlag:
    def test_default_parallel_is_noop(self) -> None:
        cfg = parse_judges("openai,gemini,hf-llama")
        # parallel=1 or None → no validation needed.
        validate_parallel_flag(cfg, None)
        validate_parallel_flag(cfg, 1)

    def test_parallel_with_hf_llama_passes(self) -> None:
        cfg = parse_judges("openai,gemini,hf-llama")
        validate_parallel_flag(cfg, 8)  # no exception

    def test_parallel_without_hf_llama_raises(self) -> None:
        cfg = parse_judges("mock_a,mock_b,mock_c")
        with pytest.raises(ValueError, match="hf-llama"):
            validate_parallel_flag(cfg, 8)

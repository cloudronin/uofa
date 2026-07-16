"""Tests for the cost-gate module: token estimation + budget tracking."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from uofa_cli.adversarial.judge.cost_gate import (
    BudgetTracker,
    CostEstimate,
    count_tokens,
    estimate_bundle_cost,
    estimate_call_cost,
    render_estimate_table,
)


# ── BudgetTracker ───────────────────────────────────────────────────────


class TestBudgetTracker:
    def test_unlimited_when_no_max(self) -> None:
        tracker = BudgetTracker(max_cost_usd=None)
        assert tracker.authorize("openai", 999.0)
        tracker.record("openai", 100.0)
        assert tracker.authorize("openai", 999.0)  # still ok

    def test_authorize_under_budget(self) -> None:
        tracker = BudgetTracker(max_cost_usd=10.0)
        assert tracker.authorize("openai", 3.0)
        tracker.record("openai", 3.0)
        assert tracker.authorize("openai", 6.0)
        assert tracker.running_total_usd == 3.0

    def test_authorize_blocks_when_over_budget(self) -> None:
        tracker = BudgetTracker(max_cost_usd=10.0)
        tracker.record("openai", 9.0)
        assert tracker.authorize("openai", 2.0) is False
        assert tracker.over_budget is True

    def test_per_judge_totals_track_separately(self) -> None:
        tracker = BudgetTracker(max_cost_usd=10.0)
        tracker.record("openai", 2.0)
        tracker.record("anthropic", 3.0)
        tracker.record("openai", 1.0)
        assert tracker.per_judge_total_usd == {"openai": 3.0, "anthropic": 3.0}

    def test_write_manifest(self, tmp_path: Path) -> None:
        tracker = BudgetTracker(max_cost_usd=10.0)
        tracker.record("openai", 2.5)
        tracker.write_manifest(tmp_path / "cost.json")
        import json
        data = json.loads((tmp_path / "cost.json").read_text())
        assert data["running_total_usd"] == 2.5
        assert data["max_cost_usd"] == 10.0
        assert data["call_count"] == 1


# ── token + cost helpers ────────────────────────────────────────────────


class TestTokenCounting:
    def test_count_tokens_uses_litellm_when_available(self) -> None:
        with patch("litellm.token_counter", return_value=42) as mock_count:
            n = count_tokens("openai", None, "hello world")
            assert n == 42
            mock_count.assert_called_once()

    def test_count_tokens_falls_back_on_exception(self) -> None:
        with patch("litellm.token_counter", side_effect=Exception("no model")):
            n = count_tokens("openai", None, "x" * 40)
            # Heuristic: 40/4 = 10 tokens.
            assert n == 10

    def test_gemini_padding_applied(self) -> None:
        with patch("litellm.token_counter", return_value=100):
            n = count_tokens("gemini", None, "x")
            # 100 * 1.10 = 110 (Gemini under-count pad).
            assert n == 110


class TestEstimateCallCost:
    def test_uses_litellm_cost_per_token(self) -> None:
        with patch("litellm.cost_per_token", return_value=(0.001, 0.002)):
            usd = estimate_call_cost(
                "openai", None,
                input_tokens=100, output_tokens=50,
            )
            assert usd == pytest.approx(0.003)

    def test_falls_back_to_zero_when_no_cost_data(self) -> None:
        # Use a known-good provider token so the model-string lookup
        # succeeds; the patched litellm.cost_per_token forces the
        # exception path that drops the call cost to 0.
        with patch("litellm.cost_per_token", side_effect=Exception("no model")):
            usd = estimate_call_cost(
                "openai", "openai/some-unsupported-model",
                input_tokens=100, output_tokens=50,
            )
            assert usd == 0.0

    def test_capability_override_takes_precedence_for_hf_llama(self) -> None:
        # hf-llama has explicit input/output rates in the capability
        # table because litellm doesn't carry the OpenRouter-routed
        # Llama 4 Maverick id in its price table. The override path
        # should NOT call litellm.cost_per_token at all.
        with patch("litellm.cost_per_token") as mock_cpt:
            usd = estimate_call_cost(
                "hf-llama", None,
                input_tokens=1_000_000, output_tokens=1_000_000,
            )
            # OpenRouter rate: $0.20/M input + $0.80/M output = $1.00 total.
            assert usd == pytest.approx(1.00)
            mock_cpt.assert_not_called()

    def test_capability_override_scales_per_token(self) -> None:
        usd = estimate_call_cost(
            "hf-llama", None,
            input_tokens=10_000, output_tokens=5_000,
        )
        # 10000/1M * 0.20 + 5000/1M * 0.80 = 0.002 + 0.004 = 0.006
        assert usd == pytest.approx(0.006)


class TestEstimateBundleCost:
    def test_zero_cases_returns_zero(self) -> None:
        e = estimate_bundle_cost(
            provider_token="openai", model=None,
            static_prefix="prefix", per_case_blocks=[],
        )
        assert e.case_count == 0
        assert e.estimated_usd == 0.0

    def test_aggregates_across_cases(self) -> None:
        # Mock token counter and cost so we can predict the sum.
        with patch("litellm.token_counter", return_value=10), \
             patch("litellm.cost_per_token", return_value=(0.01, 0.02)):
            e = estimate_bundle_cost(
                provider_token="openai", model=None,
                static_prefix="prefix",
                per_case_blocks=["case1", "case2", "case3"],
                expected_output_tokens_per_case=100,
            )
        assert e.case_count == 3
        # 3 cases * (0.01 + 0.02) = 0.09
        assert e.estimated_usd == pytest.approx(0.09)


class TestRenderEstimateTable:
    def test_empty_estimates(self) -> None:
        assert render_estimate_table([]) == "(no estimates)"

    def test_aligned_table(self) -> None:
        rendered = render_estimate_table([
            CostEstimate(
                provider_token="openai", model="openai/gpt-5.4",
                case_count=10, total_input_tokens=1000,
                total_output_tokens=500, estimated_usd=0.0123,
            ),
            CostEstimate(
                provider_token="anthropic", model="anthropic/claude-sonnet-4-6",
                case_count=10, total_input_tokens=1000,
                total_output_tokens=500, estimated_usd=0.0234,
            ),
        ])
        assert "openai" in rendered
        assert "anthropic" in rendered
        # Column header + alignment check.
        assert "token" in rendered
        # Total line.
        assert "total: $" in rendered

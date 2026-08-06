"""Cost rates, and the reason an unpriced model has to be a hard failure.

`--max-cost` is the only upper bound on what a generation run can spend. It is
enforced by accumulating `estimate_cost(...)` and halting at the ceiling, and
`estimate_cost` returns 0.0 for any model it has no rate for.

So an unpriced model does not weaken the guard, it removes it: the accumulator
stays at zero, the ceiling is never reached, and the run looks free the whole way
down. Nothing in the output distinguishes "this run cost nothing" from "this run
cannot be measured", which is why the check is a refusal rather than a warning.
"""

from __future__ import annotations

import pytest

from uofa_cli.adversarial.model_costs import (
    _RATES,
    assert_priced,
    estimate_cost,
    is_priced,
)


def test_an_unknown_model_estimates_zero():
    """The behaviour that makes the guard necessary. Pinned, not fixed.

    Returning 0.0 is right for the advisory manifest field; it is only dangerous
    where it backs a spend ceiling, which is what `assert_priced` covers.
    """
    assert estimate_cost("gpt-9-does-not-exist", 100_000_000) == 0.0
    assert is_priced("gpt-9-does-not-exist") is False


def test_assert_priced_refuses_and_says_why():
    with pytest.raises(SystemExit) as exc:
        assert_priced("gpt-9-does-not-exist")
    msg = str(exc.value)
    assert "--max-cost cannot guard" in msg
    assert "$0.00" in msg, "the message must name the actual failure mode"
    assert "_RATES" in msg, "and say where to fix it"


def test_locally_run_models_are_free_not_unpriced():
    """ollama costs nothing per token, so 0.0 there is a fact, not a gap.

    Collapsing the two would either block local runs or reopen the hole.
    """
    assert is_priced("ollama/qwen3.5:4b") is True
    assert estimate_cost("ollama/qwen3.5:4b", 10_000_000) == 0.0
    assert_priced("ollama/qwen3.5:4b")


def test_provider_prefix_does_not_change_the_rate():
    """LiteLLM routes "openai/gpt-5"; the corpus generator passes bare "gpt-5"."""
    assert estimate_cost("openai/gpt-5", 1_000_000) == estimate_cost("gpt-5", 1_000_000)
    assert is_priced("openai/gpt-5")


def test_the_openai_models_a_paid_run_would_use_are_priced():
    """P3b needs an OpenAI backend, and the plan requires rates before the run."""
    for m in ("gpt-5", "gpt-5-mini", "gpt-4.1", "gpt-4o", "gpt-4o-mini"):
        assert is_priced(m), m
        assert estimate_cost(m, 1_000_000) > 0.0, m


def test_output_tokens_cost_more_than_input():
    """Guards a transposed (input, output) tuple, which would under-estimate.

    Every rate in the table is cheaper in than out, so a swapped pair is both
    silent and always in the dangerous direction.
    """
    for model, (in_rate, out_rate) in _RATES.items():
        assert out_rate > in_rate, f"{model}: rates look transposed"


def test_estimate_scales_with_the_output_ratio():
    lo = estimate_cost("gpt-5", 1_000_000, output_ratio=0.1)
    hi = estimate_cost("gpt-5", 1_000_000, output_ratio=0.9)
    assert hi > lo


def test_zero_and_negative_token_counts_are_free():
    assert estimate_cost("gpt-5", 0) == 0.0
    assert estimate_cost("gpt-5", -5) == 0.0

"""Advisory per-model token cost estimates (USD per 1M tokens).

Not billing-grade accurate. Used for the manifest's total_cost_estimate and,
importantly, for the `--max-cost` spend guard in `adversarial/runner.py`.

Anthropic rates as of April 2026 public pricing; OpenAI rates as of August 2026.

## Why `is_priced` exists

`estimate_cost` returns 0.0 for a model it does not know. That is the right
behaviour for an advisory manifest field and a silent catastrophe for a spend
guard: `runner.py` accumulates `estimate_cost(...)` and halts once the total
reaches `--max-cost`, so an unpriced model accumulates $0 forever and the guard
never fires. Nothing looks wrong -- the run simply appears to be free.

Callers that gate spending must ask `is_priced(model)` first and refuse to start
rather than trust a 0.0. `assert_priced` does that in one call.
"""

from __future__ import annotations

# (input, output) dollars per 1M tokens
_RATES: dict[str, tuple[float, float]] = {
    # Anthropic
    "claude-opus-4-7": (15.0, 75.0),
    "claude-opus-4-6": (15.0, 75.0),
    "claude-sonnet-4-6": (3.0, 15.0),
    "claude-haiku-4-5-20251001": (1.0, 5.0),
    # OpenAI
    "gpt-5.6-sol": (5.0, 30.0),
    "gpt-5.6-terra": (2.0, 12.0),
    "gpt-5.6-luna": (0.20, 1.20),
    "gpt-5.5": (5.0, 30.0),
    "gpt-5.5-pro": (30.0, 180.0),
    "gpt-5.4": (2.50, 15.0),
    "gpt-5.4-mini": (0.75, 4.50),
    "gpt-5.4-nano": (0.20, 1.25),
    "gpt-5.2": (1.75, 14.0),
    "gpt-5.1": (1.25, 10.0),
    "gpt-5": (1.25, 10.0),
    "gpt-5-mini": (0.25, 2.0),
    "gpt-5-nano": (0.05, 0.40),
    "gpt-4.1": (2.0, 8.0),
    "gpt-4.1-mini": (0.40, 1.60),
    "gpt-4.1-nano": (0.10, 0.40),
    "gpt-4o": (2.50, 10.0),
    "gpt-4o-mini": (0.15, 0.60),
}

# Providers whose models run on local hardware and genuinely cost nothing per
# token, so a 0.0 estimate there is a fact rather than a missing rate.
_FREE_PREFIXES = ("ollama/", "local/", "huggingface/")


def _strip_provider(model: str) -> str:
    """LiteLLM-style "openai/gpt-5" and bare "gpt-5" bill at the same rate."""
    return model.split("/", 1)[1] if "/" in model else model


def is_priced(model: str) -> bool:
    """Can this model's spend be estimated at all?

    False means `estimate_cost` returns 0.0 because the rate is unknown, not
    because the model is free. Anything gating spend must branch on this rather
    than on the estimate.
    """
    if any(model.startswith(p) for p in _FREE_PREFIXES):
        return True
    return _strip_provider(model) in _RATES


def assert_priced(model: str) -> None:
    """Refuse to start a paid run whose spend cannot be measured.

    A `--max-cost` ceiling over an unpriced model is not a weak guard, it is no
    guard: the accumulator stays at zero and the ceiling is never reached.
    Failing here costs one dictionary entry; failing to fail costs a bill nobody
    set an upper bound on.
    """
    if is_priced(model):
        return
    raise SystemExit(
        f"No cost rate is known for model {model!r}, so --max-cost cannot guard "
        f"this run: estimate_cost() would report $0.00 however many tokens are "
        f"spent, and the ceiling would never be reached.\n"
        f"Add its (input, output) USD-per-1M-token rate to _RATES in "
        f"{__file__} before running.\n"
        f"Known: {', '.join(sorted(_RATES))}"
    )


def estimate_cost(model: str, total_tokens: int, output_ratio: float = 0.4) -> float:
    """Estimate the USD cost for *total_tokens* at *model* rates.

    If the model is unknown, returns 0.0 (advisory only, never blocks). Callers
    gating spend must call `assert_priced` first -- see the module docstring.
    *output_ratio* is the fraction of total tokens that were output tokens.
    """
    if total_tokens <= 0:
        return 0.0
    rates = _RATES.get(_strip_provider(model))
    if not rates:
        return 0.0
    in_rate, out_rate = rates
    output_tokens = total_tokens * output_ratio
    input_tokens = total_tokens - output_tokens
    return (input_tokens * in_rate + output_tokens * out_rate) / 1_000_000

"""Advisory per-model token cost estimates (USD per 1M tokens).

Not billing-grade accurate. Used for the manifest's total_cost_estimate.
Numbers as of April 2026 public Anthropic pricing.
"""

from __future__ import annotations

# (input, output) dollars per 1M tokens
_RATES: dict[str, tuple[float, float]] = {
    "claude-opus-4-7": (15.0, 75.0),
    "claude-opus-4-6": (15.0, 75.0),
    "claude-sonnet-4-6": (3.0, 15.0),
    "claude-haiku-4-5-20251001": (1.0, 5.0),
}


def estimate_cost(model: str, total_tokens: int, output_ratio: float = 0.4) -> float:
    """Estimate the USD cost for *total_tokens* at *model* rates.

    If the model is unknown, returns 0.0 (advisory only, never blocks).
    *output_ratio* is the fraction of total tokens that were output tokens.
    """
    if total_tokens <= 0:
        return 0.0
    rates = _RATES.get(model)
    if not rates:
        return 0.0
    in_rate, out_rate = rates
    output_tokens = total_tokens * output_ratio
    input_tokens = total_tokens - output_tokens
    return (input_tokens * in_rate + output_tokens * out_rate) / 1_000_000

"""Token estimation + cost-budget enforcement for the judge run path.

Two responsibilities (spec v1.6 §11.5 + plan Wave F):
  1. `--dry-run`: estimate per-judge token + USD cost for the bundle and
     report a table without spending. The estimate uses litellm's
     `token_counter` (tiktoken/transformers locally) and
     `cost_per_token` (model price table).
  2. `--max-cost USD`: track accumulated cost during a real run; halt
     when the next call would push over the budget. Halt path is
     graceful — current judgments are flushed, an interrupt manifest
     captures the partial-run state, and the runner exits with rc=4.

Litellm's token_counter has known under-counts for some Gemini models
(spec R-V1.5-3 mitigation note); we apply a 1.10× safety pad for any
provider whose capability table flags it. Real costs are tracked off
the actual response usage where the API returns it.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

from uofa_cli.adversarial.judge.providers.capabilities import (
    get_capabilities,
    litellm_model_string,
)


# Padding factor for providers whose token counter under-counts.
# Applied at the estimate-only path so dry-run doesn't undershoot.
TOKEN_COUNT_PAD: dict[str, float] = {
    # Gemini: see spec R-V1.5-3.
    "gemini": 1.10,
}


@dataclass(frozen=True)
class CostEstimate:
    """One judge's estimated cost on a bundle."""

    provider_token: str
    model: str
    case_count: int
    total_input_tokens: int
    total_output_tokens: int
    estimated_usd: float


@dataclass
class BudgetTracker:
    """Accumulates spend during a real run; raises BudgetExceeded when a
    call would push over the limit.

    `max_cost_usd` is the absolute ceiling. `running_total_usd` accumulates
    real costs from response usage metadata. `pending_estimate_usd` is the
    cost the next call would add; the tracker compares the sum against
    max_cost before authorizing the call.
    """

    max_cost_usd: float | None = None
    running_total_usd: float = 0.0
    per_judge_total_usd: dict[str, float] = field(default_factory=dict)
    call_count: int = 0
    over_budget: bool = False

    def authorize(self, judge_token: str, estimate_usd: float) -> bool:
        """Return True if a call costing ~estimate_usd is within budget."""
        if self.max_cost_usd is None:
            return True
        if self.running_total_usd + estimate_usd > self.max_cost_usd:
            self.over_budget = True
            return False
        return True

    def record(self, judge_token: str, actual_usd: float) -> None:
        """Record actual cost from a completed call."""
        self.running_total_usd += actual_usd
        self.per_judge_total_usd[judge_token] = (
            self.per_judge_total_usd.get(judge_token, 0.0) + actual_usd
        )
        self.call_count += 1

    def write_manifest(self, path: Path) -> None:
        """Dump a cost manifest (used at end-of-run or budget-exceeded)."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({
            "max_cost_usd": self.max_cost_usd,
            "running_total_usd": self.running_total_usd,
            "per_judge_total_usd": self.per_judge_total_usd,
            "call_count": self.call_count,
            "over_budget": self.over_budget,
        }, indent=2))


class BudgetExceeded(Exception):
    """Raised when a call would push the run over `--max-cost`."""


# ── token + cost estimation ────────────────────────────────────────────


def count_tokens(provider_token: str, model: str | None, text: str) -> int:
    """Count tokens for a (provider, model, text) tuple via litellm.

    Falls back to a 4-char-per-token heuristic if litellm raises (some
    providers/models aren't supported by the local tokenizer; the spec
    accepts the heuristic as a dry-run-only approximation).
    """
    model_str = litellm_model_string(provider_token, model)
    try:
        import litellm  # type: ignore
        n = int(litellm.token_counter(model=model_str, text=text))
    except Exception:
        n = max(1, len(text) // 4)
    pad = TOKEN_COUNT_PAD.get(provider_token, 1.0)
    return int(n * pad)


def estimate_call_cost(
    provider_token: str,
    model: str | None,
    *,
    input_tokens: int,
    output_tokens: int,
) -> float:
    """Estimate USD cost for one call.

    Resolution order:
      1. Capability-table override (`input_cost_per_1m_usd` /
         `output_cost_per_1m_usd`) when present. Used for models
         litellm hasn't shipped a price entry for — currently the
         HF-Router-routed Llama 4 Maverick.
      2. `litellm.cost_per_token` for the resolved litellm model id.
      3. 0.0 fallback if neither path produces a number (the cost
         gate will run unrestricted; surface this in the run manifest
         if an audit is needed).
    """
    from uofa_cli.adversarial.judge.providers.capabilities import (
        get_capabilities,
    )

    # Path 1: capability override.
    try:
        caps = get_capabilities(provider_token)
    except KeyError:
        caps = None
    if (
        caps is not None
        and caps.input_cost_per_1m_usd is not None
        and caps.output_cost_per_1m_usd is not None
    ):
        return (
            (input_tokens / 1_000_000) * caps.input_cost_per_1m_usd
            + (output_tokens / 1_000_000) * caps.output_cost_per_1m_usd
        )

    # Path 2: litellm price table.
    model_str = litellm_model_string(provider_token, model)
    try:
        import litellm  # type: ignore
        in_cost, out_cost = litellm.cost_per_token(
            model=model_str,
            prompt_tokens=input_tokens,
            completion_tokens=output_tokens,
        )
        return float(in_cost + out_cost)
    except Exception:
        return 0.0


def estimate_bundle_cost(
    *,
    provider_token: str,
    model: str | None,
    static_prefix: str,
    per_case_blocks: Sequence[str],
    expected_output_tokens_per_case: int = 500,
) -> CostEstimate:
    """Sum cost across all per-case calls for one judge.

    Static prefix tokens are counted once per call (no caching credit at
    the dry-run path; the actual run gets the cache discount via Wave H).
    `expected_output_tokens_per_case` is a conservative ceiling (spec
    response objects are ~300–500 tokens; default 500).
    """
    if not per_case_blocks:
        return CostEstimate(
            provider_token=provider_token,
            model=model or litellm_model_string(provider_token, None),
            case_count=0,
            total_input_tokens=0,
            total_output_tokens=0,
            estimated_usd=0.0,
        )

    prefix_tokens = count_tokens(provider_token, model, static_prefix)
    total_input = 0
    total_output = 0
    total_usd = 0.0
    for block in per_case_blocks:
        case_tokens = count_tokens(provider_token, model, block)
        in_tok = prefix_tokens + case_tokens
        out_tok = expected_output_tokens_per_case
        total_input += in_tok
        total_output += out_tok
        total_usd += estimate_call_cost(
            provider_token, model,
            input_tokens=in_tok, output_tokens=out_tok,
        )
    return CostEstimate(
        provider_token=provider_token,
        model=model or litellm_model_string(provider_token, None),
        case_count=len(per_case_blocks),
        total_input_tokens=total_input,
        total_output_tokens=total_output,
        estimated_usd=total_usd,
    )


def render_estimate_table(estimates: Sequence[CostEstimate]) -> str:
    """Format a fixed-width table of per-judge cost estimates."""
    if not estimates:
        return "(no estimates)"
    rows = [
        ("token", "model", "cases", "in_tok", "out_tok", "USD"),
    ]
    for e in estimates:
        rows.append((
            e.provider_token,
            e.model,
            str(e.case_count),
            str(e.total_input_tokens),
            str(e.total_output_tokens),
            f"${e.estimated_usd:.4f}",
        ))
    widths = [max(len(r[i]) for r in rows) for i in range(len(rows[0]))]

    def fmt(row):
        return "  " + "  ".join(c.ljust(w) for c, w in zip(row, widths))

    out = [fmt(rows[0]), "  " + "  ".join("-" * w for w in widths)]
    for row in rows[1:]:
        out.append(fmt(row))
    total = sum(e.estimated_usd for e in estimates)
    out.append("")
    out.append(f"  total: ${total:.4f}")
    return "\n".join(out)

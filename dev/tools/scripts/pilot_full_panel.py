#!/usr/bin/env python3
"""Pilot run: stratified sample of N Phase 2 packages through the full
5-judge panel, measuring rate limits + token distribution + disagreement
rate to refine production-run projections.

What it captures (per vendor):
  - latency distribution (p50/p95/max)
  - input/output token counts (mean + range)
  - call cost (real, not estimated) sourced from response usage
  - retry / rate-limit incidents (HTTP 429, 503, etc.)
  - schema-coercion incidents (Llama only; non-strict path)

What it captures (overall):
  - disagreement rate over A/B/C trio (CONVERGENT vs DISAGREEMENT)
  - Judge E firing rate + ARBITRATED/ESCALATED partition at 0.6 floor
  - distribution of arbitration_basis when Judge E fires
  - wall-clock at the chosen --concurrency level

Exit 0 always; the script's value is the printed report. Output also
writes a JSON metrics file so the projection table can be regenerated
without re-running.

Usage (with all five keys):
  ANTHROPIC_API_KEY=$(cat /tmp/anthropic.txt) \
  OPENAI_API_KEY=$(cat /tmp/openai.txt) \
  GEMINI_API_KEY=$(cat /tmp/gemini.txt) \
  HF_TOKEN=$(cat /tmp/huggingface.txt) \
  MISTRAL_API_KEY=$(cat /tmp/mistral.txt) \
      python dev/tools/scripts/pilot_full_panel.py --n 100 --concurrency 5

The default bundle is dev/build/adversarial/phase2/2026-04-26/judge_ready_bundle.tgz.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import statistics
import sys
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[3] / "src"))

from uofa_cli.adversarial.judge.bundle import open_bundle  # noqa: E402
from uofa_cli.adversarial.judge.providers.litellm_provider import LiteLLMProvider  # noqa: E402
from uofa_cli.adversarial.judge.triage import TriageBucket, triage_case  # noqa: E402


# Stratified outcome-class targets (proportional to corpus distribution).
DEFAULT_BUNDLE = Path(
    "dev/build/adversarial/phase2/2026-04-26/judge_ready_bundle.tgz"
)


@dataclass
class CallMetric:
    """One judge call against one case."""
    case_id: str
    judge_role: str
    provider_token: str
    verdict: str | None
    confidence: float | None
    latency_s: float
    input_tokens: int
    output_tokens: int
    cost_usd: float
    error: str | None = None
    coerced_fields: list[str] = field(default_factory=list)


@dataclass
class CaseResult:
    """A whole case's panel run."""
    case_id: str
    triage_bucket: str | None  # CONVERGENT | DISAGREEMENT | None
    triage_subtype: str | None
    majority_verdict: str | None
    arbitration_verdict: str | None
    arbitration_confidence: float | None
    arbitration_partition: str | None  # ARBITRATED | ESCALATED | None
    calls: list[CallMetric] = field(default_factory=list)


def _stratified_sample(entries: list[Any], n: int) -> list[Any]:
    """Pick n entries proportional to phase2_outcome_class_raw distribution."""
    by_class: dict[str, list[Any]] = defaultdict(list)
    for e in entries:
        cls = e.outcome.get("phase2_outcome_class_raw") or e.outcome.get(
            "coverage_class"
        ) or "unknown"
        by_class[cls].append(e)

    total = len(entries)
    sample: list[Any] = []
    for cls, items in sorted(by_class.items()):
        share = round(n * len(items) / total)
        sample.extend(items[:share])
    # Trim or pad to exactly n.
    if len(sample) > n:
        sample = sample[:n]
    elif len(sample) < n:
        # Pad from the largest bucket.
        biggest = max(by_class.values(), key=len)
        used = set(id(s) for s in sample)
        for e in biggest:
            if id(e) not in used:
                sample.append(e)
                used.add(id(e))
                if len(sample) >= n:
                    break
    return sample


def _entry_to_case(entry) -> dict:
    return {
        "case_id": entry.case_id,
        "phase2_case_id": entry.case_id,
        "source_taxonomy": entry.outcome.get("source_taxonomy"),
        "rules_fired": entry.outcome.get("rules_fired", []),
        "expected_rule": entry.outcome.get("expected_rule"),
        "section_6_7_mapping": entry.outcome.get("section_6_7_mapping"),
        "phase2_outcome_class_raw": entry.outcome.get(
            "phase2_outcome_class_raw"
        ) or entry.outcome.get("coverage_class"),
        "package": entry.package,
    }


async def _run_one_judge_metric(
    provider_token: str,
    judge_role: str,
    case: dict,
    semaphore: asyncio.Semaphore,
) -> CallMetric:
    """Time + cost a single call. Bound by `semaphore` for concurrency."""
    case_id = case["case_id"]
    async with semaphore:
        provider = LiteLLMProvider(
            provider_token=provider_token,
            judge_role=judge_role,
            thinking_enabled=False,
        )
        t0 = time.perf_counter()
        try:
            judgment = await provider.judge(case)
            latency = time.perf_counter() - t0
            raw = judgment.raw_response or {}
            usage = raw.get("usage") or {} if isinstance(raw, dict) else {}
            in_tok = int(usage.get("prompt_tokens", 0) or 0)
            out_tok = int(usage.get("completion_tokens", 0) or 0)
            from uofa_cli.adversarial.judge.cost_gate import estimate_call_cost
            cost = estimate_call_cost(
                provider_token, judgment.judge_model,
                input_tokens=in_tok, output_tokens=out_tok,
            )
            coerced = _detect_coerced(judgment)
            return CallMetric(
                case_id=case_id, judge_role=judge_role,
                provider_token=provider_token,
                verdict=judgment.verdict, confidence=judgment.confidence,
                latency_s=latency, input_tokens=in_tok, output_tokens=out_tok,
                cost_usd=cost, coerced_fields=coerced,
            )
        except Exception as e:
            latency = time.perf_counter() - t0
            return CallMetric(
                case_id=case_id, judge_role=judge_role,
                provider_token=provider_token, verdict=None, confidence=None,
                latency_s=latency, input_tokens=0, output_tokens=0,
                cost_usd=0.0, error=repr(e)[:300],
            )


def _detect_coerced(judgment) -> list[str]:
    """Identify which fields were filled by _coerce_partial_response."""
    coerced: list[str] = []
    rs = judgment.reasoning_steps or {}
    for k, v in rs.items():
        if isinstance(v, str) and "(coerced)" in v:
            coerced.append(f"reasoning_steps.{k}")
    if "(coerced)" in (judgment.judge_model or ""):
        coerced.append("judge_model")
    if isinstance(judgment.reasoning, str) and "(coerced:" in judgment.reasoning:
        coerced.append("reasoning")
    return coerced


async def _run_case(
    case: dict,
    semaphores: dict[str, asyncio.Semaphore],
) -> CaseResult:
    """Run all production judges + Judge D on one case in parallel; triage; arbitrate if needed."""
    a, b, c, d = await asyncio.gather(
        _run_one_judge_metric("openai", "production", case, semaphores["openai"]),
        _run_one_judge_metric("gemini", "production", case, semaphores["gemini"]),
        _run_one_judge_metric("hf-llama", "production", case, semaphores["hf-llama"]),
        _run_one_judge_metric("anthropic", "calibration_anchor", case, semaphores["anthropic"]),
    )
    result = CaseResult(
        case_id=case["case_id"],
        triage_bucket=None, triage_subtype=None, majority_verdict=None,
        arbitration_verdict=None, arbitration_confidence=None,
        arbitration_partition=None,
        calls=[a, b, c, d],
    )

    # Triage A/B/C only (D is anchor, separate signal).
    if any(call.error for call in (a, b, c)):
        return result

    from types import SimpleNamespace
    def _stub(call: CallMetric) -> SimpleNamespace:
        return SimpleNamespace(
            case_id=call.case_id, verdict=call.verdict,
            confidence=call.confidence,
        )
    triage = triage_case(_stub(a), _stub(b), _stub(c), confidence_floor=0.6)
    result.triage_bucket = triage.bucket.value
    result.triage_subtype = triage.disagreement_type
    result.majority_verdict = triage.majority_verdict

    # Arbitrate on disagreement.
    if triage.bucket != TriageBucket.CONVERGENT:
        arbitration_case = dict(case)
        arbitration_case["production_verdicts"] = [
            {"position": p, "verdict": call.verdict or "ERROR",
             "confidence": call.confidence or 0.0,
             "reasoning": "(see judgments_*.jsonl)"}
            for p, call in zip(("A", "B", "C"), (a, b, c))
        ]
        e = await _run_one_judge_metric(
            "mistral", "arbiter", arbitration_case, semaphores["mistral"]
        )
        result.calls.append(e)
        result.arbitration_verdict = e.verdict
        result.arbitration_confidence = e.confidence
        if e.confidence is not None:
            result.arbitration_partition = (
                "ARBITRATED" if e.confidence >= 0.6 else "ESCALATED"
            )
    return result


def _percentiles(values: list[float], pcts: list[float]) -> dict[str, float]:
    if not values:
        return {f"p{int(p)}": 0.0 for p in pcts}
    s = sorted(values)
    out = {}
    for p in pcts:
        idx = int(round((p / 100) * (len(s) - 1)))
        out[f"p{int(p)}"] = s[idx]
    return out


def _summarize(results: list[CaseResult], wall_clock_s: float, args) -> dict:
    """Build the final metrics report."""
    by_judge: dict[str, list[CallMetric]] = defaultdict(list)
    for r in results:
        for c in r.calls:
            by_judge[c.provider_token].append(c)

    judge_summaries = {}
    grand_cost = 0.0
    for token, calls in by_judge.items():
        ok = [c for c in calls if c.error is None]
        errs = [c for c in calls if c.error is not None]
        rate_limit = [c for c in errs if "429" in (c.error or "") or "rate" in (c.error or "").lower()]
        coerced = sum(1 for c in ok if c.coerced_fields)
        cost = sum(c.cost_usd for c in calls)
        grand_cost += cost
        judge_summaries[token] = {
            "calls": len(calls),
            "ok": len(ok),
            "errors": len(errs),
            "rate_limit_incidents": len(rate_limit),
            "schema_coercion_incidents": coerced,
            "total_cost_usd": cost,
            "mean_input_tokens": (
                statistics.mean([c.input_tokens for c in ok]) if ok else 0
            ),
            "mean_output_tokens": (
                statistics.mean([c.output_tokens for c in ok]) if ok else 0
            ),
            "max_input_tokens": max((c.input_tokens for c in ok), default=0),
            "latency_seconds": _percentiles(
                [c.latency_s for c in ok], [50, 95, 99]
            ),
            "max_latency_s": max((c.latency_s for c in ok), default=0.0),
        }

    triage_counter = Counter(
        r.triage_bucket or "ERROR" for r in results
    )
    arbitration_counter = Counter(
        r.arbitration_partition or "N/A" for r in results
        if r.triage_bucket and r.triage_bucket != "CONVERGENT"
    )
    disagreement_rate = (
        triage_counter.get("DISAGREEMENT", 0) / len(results) if results else 0
    )

    return {
        "n_cases": len(results),
        "concurrency_per_judge": args.concurrency,
        "wall_clock_s": wall_clock_s,
        "grand_cost_usd": grand_cost,
        "by_judge": judge_summaries,
        "triage": dict(triage_counter),
        "disagreement_rate": disagreement_rate,
        "arbitration_partition": dict(arbitration_counter),
    }


def _print_report(summary: dict) -> None:
    print("\n" + "=" * 72)
    print(f"Pilot run: {summary['n_cases']} cases, "
          f"concurrency={summary['concurrency_per_judge']} per judge")
    print(f"Wall-clock:    {summary['wall_clock_s']:.1f}s")
    print(f"Grand cost:    ${summary['grand_cost_usd']:.4f}")
    print()
    print(f"{'judge':12} {'ok':>4}/{'tot':>4}  "
          f"{'cost':>10}  {'in/out tok':>14}  "
          f"{'p50':>7} {'p95':>7} {'errs':>5} {'coerce':>6}")
    for token, s in summary["by_judge"].items():
        in_out = f"{s['mean_input_tokens']:.0f}/{s['mean_output_tokens']:.0f}"
        cost_str = f"${s['total_cost_usd']:.4f}"
        print(
            f"{token:12} {s['ok']:>4}/{s['calls']:>4}  "
            f"{cost_str:>10}  {in_out:>14}  "
            f"{s['latency_seconds']['p50']:>5.1f}s "
            f"{s['latency_seconds']['p95']:>5.1f}s "
            f"{s['errors']:>5} {s['schema_coercion_incidents']:>6}"
        )
    print()
    print(f"Triage: {summary['triage']}")
    print(f"Disagreement rate: {summary['disagreement_rate']:.1%}")
    print(f"Arbitration partition: {summary['arbitration_partition']}")
    print("=" * 72)


def _project_full_corpus(summary: dict, n_corpus: int) -> dict:
    """Scale pilot metrics to the full corpus."""
    scale = n_corpus / summary["n_cases"] if summary["n_cases"] else 0
    per_judge_corpus = {}
    grand = 0.0
    for token, s in summary["by_judge"].items():
        c = s["total_cost_usd"] * scale
        per_judge_corpus[token] = c
        grand += c
    return {
        "n_corpus": n_corpus,
        "scale_factor": scale,
        "projected_total_cost_usd": grand,
        "projected_per_judge_cost_usd": per_judge_corpus,
        "wall_clock_at_pilot_concurrency_s": summary["wall_clock_s"] * scale,
    }


async def _amain(args) -> int:
    bundle_path = Path(args.bundle)
    if not bundle_path.exists():
        print(f"ERROR: bundle not found: {bundle_path}", file=sys.stderr)
        return 2

    with open_bundle(bundle_path) as bundle:
        all_entries = list(bundle.iter_entries())
    print(f"Bundle: {len(all_entries)} packages")
    sample_entries = _stratified_sample(all_entries, args.n)
    print(f"Stratified sample: {len(sample_entries)} cases")
    cases = [_entry_to_case(e) for e in sample_entries]

    # One semaphore per provider so each judge respects its own concurrency
    # cap; vendors don't share rate limits.
    semaphores = {
        token: asyncio.Semaphore(args.concurrency)
        for token in ("openai", "gemini", "hf-llama", "anthropic", "mistral")
    }

    t0 = time.perf_counter()
    case_results: list[CaseResult] = await asyncio.gather(
        *(_run_case(c, semaphores) for c in cases)
    )
    wall_clock = time.perf_counter() - t0

    summary = _summarize(case_results, wall_clock, args)
    _print_report(summary)

    # Project to full corpus.
    projection = _project_full_corpus(summary, n_corpus=4_556)
    print()
    print("Full-corpus projection (4,556 packages):")
    print(f"  total cost:      ${projection['projected_total_cost_usd']:.2f}")
    print(f"  per-judge cost:")
    for token, c in projection["projected_per_judge_cost_usd"].items():
        print(f"    {token:12} ${c:.2f}")
    print(f"  wall-clock @ this concurrency: "
          f"{projection['wall_clock_at_pilot_concurrency_s']/3600:.2f}h")

    # Write metrics + per-case detail to JSON.
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "pilot_summary.json").write_text(
        json.dumps({"summary": summary, "projection": projection}, indent=2)
    )
    (out_dir / "pilot_per_case.jsonl").write_text(
        "\n".join(json.dumps(asdict(r)) for r in case_results) + "\n"
    )
    print(f"\nWrote {out_dir/'pilot_summary.json'} and per-case detail.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n", type=int, default=100, help="pilot sample size (default: 100)")
    parser.add_argument(
        "--concurrency", type=int, default=5,
        help="max concurrent calls per provider (default: 5)",
    )
    parser.add_argument("--bundle", type=Path, default=DEFAULT_BUNDLE)
    parser.add_argument(
        "--out", type=Path, default=Path("dev/build/adversarial/pilot/2026-05-05"),
    )
    args = parser.parse_args()

    required = ["ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY",
                "HF_TOKEN", "MISTRAL_API_KEY"]
    missing = [v for v in required if v not in os.environ]
    if missing:
        print(f"ERROR: missing env vars: {missing}", file=sys.stderr)
        return 2
    return asyncio.run(_amain(args))


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Export the View 3 precision/recall metrics as Markdown.

Phase 2 v1.8 §11 View 3. Reads ``coverage/outcomes.csv`` produced by
``uofa adversarial analyze`` and writes a Ch3-abstract-ready Markdown
table, computed identically to the HTML reporter's
``_view3_precision_recall``.

Usage:
    python scripts/export_view3_markdown.py \\
        --outcomes dev/build/.../coverage/outcomes.csv \\
        --output   dev/build/.../view3_precision_recall.md
"""

from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter
from pathlib import Path


def compute_view3_metrics(rows: list[dict]) -> dict:
    """Return a dict with View 3 metrics (matches reporter._view3_precision_recall).

    Keys:
      catalog_recall                — confirm_existing HIT/HIT+ rate
      catalog_precision_1_minus_fpr — 1 − (NC COV-CLEAN-WRONG / NC total)
      gap_probe_miss_rate           — gap_probe COV-MISS rate
      counts                        — per-outcome-class counts
      n_confirm / n_nc / n_gp       — per-battery sample sizes
    """
    by_class = Counter(r.get("outcome_class", "") for r in rows)
    # Exclude GEN-INVALID from per-battery denominators (mirrors
    # reporter._view3_precision_recall): those rows represent generation
    # failures, not coverage data points.
    confirm_total = sum(
        1 for r in rows
        if r.get("coverage_intent") == "confirm_existing"
        and r.get("outcome_class") != "GEN-INVALID"
    )
    confirm_hits = sum(
        1 for r in rows
        if r.get("coverage_intent") == "confirm_existing"
        and r.get("outcome_class") in ("COV-HIT", "COV-HIT-PLUS")
    )
    nc_total = sum(
        1 for r in rows
        if r.get("coverage_intent") == "negative_control"
        and r.get("outcome_class") != "GEN-INVALID"
    )
    nc_wrong = sum(
        1 for r in rows
        if r.get("coverage_intent") == "negative_control"
        and r.get("outcome_class") == "COV-CLEAN-WRONG"
    )
    gp_total = sum(
        1 for r in rows
        if r.get("coverage_intent") == "gap_probe"
        and r.get("outcome_class") != "GEN-INVALID"
    )
    gp_miss = sum(
        1 for r in rows
        if r.get("coverage_intent") == "gap_probe"
        and r.get("outcome_class") == "COV-MISS"
    )
    return {
        "catalog_recall": confirm_hits / confirm_total if confirm_total else 0.0,
        "catalog_precision_1_minus_fpr": (
            1 - (nc_wrong / nc_total) if nc_total else 1.0
        ),
        "gap_probe_miss_rate": gp_miss / gp_total if gp_total else 0.0,
        "n_confirm": confirm_total,
        "n_nc": nc_total,
        "n_gp": gp_total,
        "counts": dict(by_class),
    }


def render_markdown(metrics: dict) -> str:
    out: list[str] = []
    out.append("# View 3 — Catalog precision / recall summary")
    out.append("")
    out.append("Computed from a Phase 2 batch's `outcomes.csv` (per Phase 2 §11.")
    out.append("View 3 in the HTML report renders the same numbers).")
    out.append("")
    out.append("| Metric | Value | Source battery |")
    out.append("|---|---|---|")
    out.append(
        f"| Catalog recall (HIT + HIT+) "
        f"| {metrics['catalog_recall']:.1%} "
        f"| confirm_existing (n={metrics['n_confirm']}) |"
    )
    out.append(
        f"| Catalog precision (1 − FPR) "
        f"| {metrics['catalog_precision_1_minus_fpr']:.1%} "
        f"| negative_controls (n={metrics['n_nc']}) |"
    )
    out.append(
        f"| Gap-probe MISS rate "
        f"| {metrics['gap_probe_miss_rate']:.1%} "
        f"| gap_probe (n={metrics['n_gp']}) |"
    )
    out.append("")
    out.append("## Outcome class counts")
    out.append("")
    out.append("| Outcome class | Count |")
    out.append("|---|---|")
    for cls in sorted(metrics["counts"]):
        out.append(f"| `{cls}` | {metrics['counts'][cls]} |")
    out.append("")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--outcomes", type=Path, required=True, help="path to outcomes.csv")
    p.add_argument("--output", type=Path, required=True, help="output .md path")
    args = p.parse_args(argv)

    if not args.outcomes.exists():
        print(f"Error: outcomes.csv not found: {args.outcomes}", file=sys.stderr)
        return 2

    with open(args.outcomes) as f:
        rows = list(csv.DictReader(f))
    metrics = compute_view3_metrics(rows)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_markdown(metrics))
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

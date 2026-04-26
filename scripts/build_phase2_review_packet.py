#!/usr/bin/env python3
"""Build the Phase 2 → Phase 3 master review packet.

Phase 2 v1.8 §16 Q6 deliverable. Distinct from the per-spec packets
written by ``uofa adversarial prep-review`` (those land in
``<batch>/review_packets/``). This produces a single Markdown handoff
document for Phase 3 reviewers, summarizing the batch:

  - Front matter: batch ID, dates, package count, total cost, fan-out
    overrides applied.
  - View 3 metrics table inline (re-uses export_view3_markdown logic).
  - COV-MISS inventory grouped by source_taxonomy with §6.7 candidate
    flags surfaced.
  - Pointer to the per-spec ``review_packets/INDEX.md``.
  - Pointer to the Figure 3.x PDF (if generated).
  - Prioritized Upwork reviewer question list (template — Phase 3
    triage refines).

Usage:
    python scripts/build_phase2_review_packet.py \\
        --batch-dir out/adversarial/phase2/2026-05-16/ \\
        --output    out/adversarial/phase2/phase2_review_packet.md \\
        [--figure-pdf out/adversarial/phase2/figure_3_x.pdf] \\
        [--review-index-rel review_packets/INDEX.md]
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

# Reuse the View 3 metric computation
sys.path.insert(0, str(Path(__file__).parent))
from export_view3_markdown import compute_view3_metrics  # noqa: E402


def _read_outcomes(coverage_dir: Path) -> list[dict]:
    p = coverage_dir / "outcomes.csv"
    if not p.exists():
        return []
    with open(p) as f:
        return list(csv.DictReader(f))


def _read_manifest(batch_dir: Path) -> dict:
    p = batch_dir / "batch_manifest.json"
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text())
    except (OSError, json.JSONDecodeError):
        return {}


def _front_matter(manifest: dict) -> str:
    out = ["## Batch metadata", ""]
    out.append("| Field | Value |")
    out.append("|---|---|")
    for k_in, k_out in [
        ("batchId", "Batch ID"),
        ("timestamp", "Timestamp (UTC)"),
        ("toolVersion", "Tool version"),
        ("generatorVersion", "Generator version"),
        ("specsLoaded", "Specs loaded"),
        ("specsSucceeded", "Specs succeeded"),
        ("specsGenInvalid", "Specs GEN-INVALID"),
        ("totalPackages", "Total packages"),
        ("estimatedCostUsd", "Est. cost (USD)"),
        ("subtletyOverride", "Subtlety override"),
        ("baseCouOverride", "Base COU override"),
        ("modelsOverride", "Models override"),
        ("strictCircularity", "Strict circularity"),
        ("halted", "Halted before completion"),
    ]:
        v = manifest.get(k_in)
        out.append(f"| {k_out} | `{v!r}` |")
    out.append("")
    return "\n".join(out)


def _view3_section(metrics: dict) -> str:
    lines = [
        "## View 3 — catalog precision / recall",
        "",
        "| Metric | Value | Source battery |",
        "|---|---|---|",
        f"| Catalog recall (HIT + HIT+) | {metrics['catalog_recall']:.1%} "
        f"| confirm_existing (n={metrics['n_confirm']}) |",
        f"| Catalog precision (1 − FPR) | "
        f"{metrics['catalog_precision_1_minus_fpr']:.1%} "
        f"| negative_controls (n={metrics['n_nc']}) |",
        f"| Gap-probe MISS rate | {metrics['gap_probe_miss_rate']:.1%} "
        f"| gap_probe (n={metrics['n_gp']}) |",
        "",
    ]
    return "\n".join(lines)


def _miss_inventory(rows: list[dict]) -> str:
    """Group COV-MISS / COV-WRONG rows by source_taxonomy for reviewer triage."""
    misses_by_taxon: dict[str, list[dict]] = defaultdict(list)
    candidate_count = 0
    for r in rows:
        if r.get("outcome_class") not in ("COV-MISS", "COV-WRONG"):
            continue
        taxon = r.get("source_taxonomy") or "(no source_taxonomy declared)"
        misses_by_taxon[taxon].append(r)
        if str(r.get("section_6_7_candidate") or "").lower() in ("true", "1", "yes"):
            candidate_count += 1

    if not misses_by_taxon:
        return "## COV-MISS / COV-WRONG inventory\n\n_No misses observed._\n"

    out = [
        "## COV-MISS / COV-WRONG inventory",
        "",
        f"Total miss/wrong rows: **{sum(len(v) for v in misses_by_taxon.values())}**",
        f" • §6.7 candidate flags: **{candidate_count}**",
        "",
        "| Source taxonomy | Count | §6.7 candidate cells |",
        "|---|---|---|",
    ]
    for taxon in sorted(misses_by_taxon):
        cells = misses_by_taxon[taxon]
        cand = sum(
            1 for c in cells
            if str(c.get("section_6_7_candidate") or "").lower() in ("true", "1", "yes")
        )
        marker = "★" if cand else ""
        out.append(f"| `{taxon}` | {len(cells)} | {cand} {marker} |")
    out.append("")
    return "\n".join(out)


def _reviewer_questions() -> str:
    return (
        "## Reviewer questions (prioritized)\n\n"
        "1. **Are the §6.7 candidates genuine catalog gaps?** Spot-check 5\n"
        "   `★`-flagged rows from the inventory above against `review_packets/`.\n"
        "2. **Do COV-CLEAN-WRONG rows on `negative_controls` indicate over-firing\n"
        "   rules?** If >5%, scope a Phase 3 catalog audit (§13.3).\n"
        "3. **Does the paraphrasing battery (`p1`/`p2`) show the same hit rate\n"
        "   as `p0`?** A drop >10% suggests prompt-text fragility worth\n"
        "   addressing before Phase 3 reviewer recruitment.\n"
        "4. **For each `★` candidate, is a new Jena rule warranted?** Default\n"
        "   answer is no — most §6.7 candidates resolve via taxonomy refinement\n"
        "   in §13.3, not catalog growth.\n"
    )


def _figure_link(figure_pdf: Path | None, batch_dir: Path) -> str:
    if not figure_pdf:
        return ""
    try:
        rel = figure_pdf.resolve().relative_to(batch_dir.resolve().parent)
    except ValueError:
        rel = figure_pdf
    return f"## Figure 3.x\n\nSee [`{rel}`]({rel}).\n\n"


def _review_index_link(batch_dir: Path, rel: str | None) -> str:
    rel = rel or "review_packets/INDEX.md"
    target = batch_dir / rel
    if not target.exists():
        return (
            f"## Per-spec reviewer packets\n\n"
            f"_Not generated yet._ Run\n\n"
            f"```bash\n"
            f"uofa adversarial prep-review --outcomes {batch_dir}/coverage/outcomes.csv "
            f"--output {batch_dir}/review_packets/\n"
            f"```\n\n"
        )
    return f"## Per-spec reviewer packets\n\nSee [`{rel}`]({rel}).\n\n"


def build_packet(
    batch_dir: Path,
    *,
    figure_pdf: Path | None = None,
    review_index_rel: str | None = None,
) -> str:
    """Compose the full Markdown packet."""
    coverage_dir = batch_dir / "coverage"
    rows = _read_outcomes(coverage_dir)
    metrics = compute_view3_metrics(rows)
    manifest = _read_manifest(batch_dir)

    parts = [
        f"# Phase 2 → Phase 3 review packet — `{batch_dir.name}`",
        "",
        "_Master handoff document for Phase 3 reviewers. Distinct from the "
        "per-spec packets in `review_packets/INDEX.md`._",
        "",
        _front_matter(manifest),
        _figure_link(figure_pdf, batch_dir),
        _view3_section(metrics),
        _miss_inventory(rows),
        _review_index_link(batch_dir, review_index_rel),
        _reviewer_questions(),
    ]
    return "\n".join(p for p in parts if p)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--batch-dir", type=Path, required=True, help="batch root directory")
    p.add_argument("--output", type=Path, required=True, help="output .md path")
    p.add_argument(
        "--figure-pdf", type=Path, default=None,
        help="path to figure_3_x.pdf for inline link (optional)",
    )
    p.add_argument(
        "--review-index-rel", default=None,
        help="relative path from batch-dir to per-spec INDEX.md (default: "
             "review_packets/INDEX.md)",
    )
    args = p.parse_args(argv)

    if not args.batch_dir.exists():
        print(f"Error: batch dir not found: {args.batch_dir}", file=sys.stderr)
        return 2
    body = build_packet(
        args.batch_dir,
        figure_pdf=args.figure_pdf,
        review_index_rel=args.review_index_rel,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(body)
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

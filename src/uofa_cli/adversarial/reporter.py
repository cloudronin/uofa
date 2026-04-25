"""HTML coverage reporter — Phase 2 §11.

Renders three views (catalog self-coverage, literature coverage,
precision/recall summary) into a single ``index.html`` per spec §11.2.
The classifier delegates to :func:`write_html_report` after writing
the CSVs.

Cell coloring (View 2):

- ``solid green``  covered by an existing rule (HIT / HIT-PLUS)
- ``dashed green`` covered by a §6.7 candidate (placeholder, dashed border)
- ``red``          COV-MISS (open gap)
- ``yellow``       COV-WRONG (alternative rule fires)
- ``grey``         deliberately out of scope
"""

from __future__ import annotations

from collections import Counter, defaultdict
from html import escape
from pathlib import Path

# Avoid an import-time cycle: the OutcomeRow dataclass lives in classifier.py.
# We accept any object with the documented attribute set.

_CSS = """
* { box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
       margin: 0; padding: 1.25rem; background: #fafafa; color: #222; }
h1 { margin-top: 0; font-size: 1.4rem; }
h2 { margin-top: 2rem; font-size: 1.15rem; border-bottom: 1px solid #ccc; padding-bottom: 0.25rem; }
nav a { margin-right: 1rem; font-size: 0.9rem; }
table { border-collapse: collapse; margin-top: 0.75rem; font-size: 0.85rem; }
th, td { border: 1px solid #ccc; padding: 0.4rem 0.6rem; text-align: left; }
th { background: #eee; }
td.cell-hit       { background: #4caf50; color: white; }
td.cell-hit-plus  { background: #6fbf73; color: white; }
td.cell-miss      { background: #d32f2f; color: white; }
td.cell-wrong     { background: #fbc02d; color: #333; }
td.cell-clean-ok  { background: #b3e5fc; color: #14365c; }
td.cell-clean-bad { background: #ff8a65; color: white; }
td.cell-gen-invalid { background: #9e9e9e; color: white; }
td.cell-empty     { background: #f5f5f5; color: #999; }
td.candidate      { border: 2px dashed #4caf50; background: #e8f5e9; color: #2e7d32; }
.legend span { display: inline-block; padding: 0.15rem 0.6rem; margin-right: 0.5rem;
               border-radius: 3px; font-size: 0.8rem; }
.metric-table td:nth-child(2) { font-weight: 600; }
"""


def _outcome_class_to_css(outcome_class: str) -> str:
    return {
        "COV-HIT":           "cell-hit",
        "COV-HIT-PLUS":      "cell-hit-plus",
        "COV-MISS":          "cell-miss",
        "COV-WRONG":         "cell-wrong",
        "COV-CLEAN-CORRECT": "cell-clean-ok",
        "COV-CLEAN-WRONG":   "cell-clean-bad",
        "GEN-INVALID":       "cell-gen-invalid",
    }.get(outcome_class, "cell-empty")


def _view1_catalog_self_coverage(rows) -> str:
    """Heatmap: UofA pattern × subtlety."""
    pivot: dict[tuple[str, str], dict[str, int]] = defaultdict(lambda: {"hit": 0, "total": 0})
    patterns = set()
    for r in rows:
        if r.coverage_intent != "confirm_existing" or not r.target_weakener:
            continue
        patterns.add(r.target_weakener)
        key = (r.target_weakener, r.subtlety)
        pivot[key]["total"] += 1
        if r.outcome_class in ("COV-HIT", "COV-HIT-PLUS"):
            pivot[key]["hit"] += 1

    if not patterns:
        return "<p><em>No confirm_existing rows; View 1 unavailable.</em></p>"

    subtlety_levels = ["low", "medium", "high"]
    out = ['<table>', '<thead><tr><th>Pattern</th>']
    for s in subtlety_levels:
        out.append(f"<th>{escape(s)}</th>")
    out.append("</tr></thead><tbody>")
    for pat in sorted(patterns):
        out.append(f"<tr><td>{escape(pat)}</td>")
        for s in subtlety_levels:
            counts = pivot.get((pat, s), {"hit": 0, "total": 0})
            total = counts["total"]
            if total == 0:
                out.append('<td class="cell-empty">—</td>')
                continue
            rate = counts["hit"] / total
            css = "cell-hit" if rate >= 0.8 else ("cell-hit-plus" if rate >= 0.5 else "cell-wrong")
            out.append(
                f'<td class="{css}">{rate:.0%} ({counts["hit"]}/{total})</td>'
            )
        out.append("</tr>")
    out.append("</tbody></table>")
    return "\n".join(out)


def _view2_literature_coverage(rows) -> str:
    """Matrix: source_taxonomy → outcome distribution."""
    by_taxonomy: dict[str, Counter] = defaultdict(Counter)
    for r in rows:
        if r.coverage_intent != "gap_probe" or not r.source_taxonomy:
            continue
        by_taxonomy[r.source_taxonomy][r.outcome_class] += 1

    if not by_taxonomy:
        return "<p><em>No gap_probe rows; View 2 unavailable.</em></p>"

    out = [
        '<table>',
        '<thead><tr><th>Source taxonomy</th>',
        '<th>HIT</th><th>HIT+</th><th>MISS</th><th>WRONG</th><th>INVALID</th><th>Verdict</th>',
        '</tr></thead><tbody>',
    ]
    for tx in sorted(by_taxonomy):
        cnt = by_taxonomy[tx]
        miss = cnt["COV-MISS"]
        wrong = cnt["COV-WRONG"]
        hit = cnt["COV-HIT"]
        hit_plus = cnt["COV-HIT-PLUS"]
        invalid = cnt["GEN-INVALID"]
        # cell-coloring per spec §11.2
        if hit + hit_plus > 0:
            verdict_css = "cell-hit"
            verdict = "covered"
        elif miss > 0 and wrong == 0:
            verdict_css = "cell-miss"
            verdict = "open gap"
        elif wrong > 0:
            verdict_css = "cell-wrong"
            verdict = "alt rule fires"
        else:
            verdict_css = "cell-gen-invalid"
            verdict = "no verdict"
        out.append(
            f"<tr><td>{escape(tx)}</td>"
            f"<td>{hit}</td><td>{hit_plus}</td>"
            f"<td>{miss}</td><td>{wrong}</td>"
            f"<td>{invalid}</td>"
            f'<td class="{verdict_css}">{verdict}</td></tr>'
        )
    out.append("</tbody></table>")
    return "\n".join(out)


def _view3_precision_recall(rows) -> str:
    by_class = Counter(r.outcome_class for r in rows)
    confirm_total = sum(1 for r in rows if r.coverage_intent == "confirm_existing")
    confirm_hits = sum(
        1 for r in rows
        if r.coverage_intent == "confirm_existing"
        and r.outcome_class in ("COV-HIT", "COV-HIT-PLUS")
    )
    nc_total = sum(1 for r in rows if r.coverage_intent == "negative_control")
    nc_wrong = sum(
        1 for r in rows
        if r.coverage_intent == "negative_control"
        and r.outcome_class == "COV-CLEAN-WRONG"
    )
    gp_total = sum(1 for r in rows if r.coverage_intent == "gap_probe")
    gp_miss = sum(
        1 for r in rows
        if r.coverage_intent == "gap_probe"
        and r.outcome_class == "COV-MISS"
    )

    recall = confirm_hits / confirm_total if confirm_total else 0.0
    precision = (1 - (nc_wrong / nc_total)) if nc_total else 1.0
    miss_rate = gp_miss / gp_total if gp_total else 0.0

    rows_html = [
        '<table class="metric-table">',
        '<thead><tr><th>Metric</th><th>Value</th><th>Source battery</th></tr></thead>',
        '<tbody>',
        f"<tr><td>Catalog recall (HIT + HIT+)</td><td>{recall:.1%}</td>"
        f"<td>confirm_existing (n={confirm_total})</td></tr>",
        f"<tr><td>Catalog precision (1 − FPR)</td><td>{precision:.1%}</td>"
        f"<td>negative_controls (n={nc_total})</td></tr>",
        f"<tr><td>Gap-probe MISS rate</td><td>{miss_rate:.1%}</td>"
        f"<td>gap_probe (n={gp_total})</td></tr>",
        '</tbody></table>',
        '<h3>Outcome class counts</h3>',
        '<table class="metric-table"><thead><tr><th>Class</th><th>Count</th></tr></thead><tbody>',
    ]
    for cls in sorted(by_class):
        rows_html.append(f"<tr><td>{escape(cls)}</td><td>{by_class[cls]}</td></tr>")
    rows_html.append("</tbody></table>")
    return "\n".join(rows_html)


def write_html_report(rows, out_path: Path) -> None:
    """Render the three-view report as ``out_path``.

    Accepts a list of objects with the OutcomeRow attribute set
    (spec_id, variant_num, target_weakener, source_taxonomy,
    coverage_intent, subtlety, outcome_class, ...).
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    body = [
        "<!DOCTYPE html><html><head><meta charset='utf-8'>",
        "<title>UofA Adversarial Coverage Report</title>",
        f"<style>{_CSS}</style>",
        "</head><body>",
        "<h1>UofA Adversarial Coverage Report</h1>",
        "<nav>",
        "<a href='#view1'>View 1 — Catalog self-coverage</a>",
        "<a href='#view2'>View 2 — Literature coverage</a>",
        "<a href='#view3'>View 3 — Precision/recall</a>",
        "</nav>",
        "<p class='legend'>",
        "<span class='cell-hit'>HIT</span>",
        "<span class='cell-hit-plus'>HIT+</span>",
        "<span class='cell-miss'>MISS</span>",
        "<span class='cell-wrong'>WRONG</span>",
        "<span class='cell-clean-ok'>CLEAN-CORRECT</span>",
        "<span class='cell-clean-bad'>CLEAN-WRONG</span>",
        "<span class='cell-gen-invalid'>GEN-INVALID</span>",
        "</p>",
        f"<h2 id='view1'>View 1 — Catalog self-coverage (UofA pattern × subtlety)</h2>",
        _view1_catalog_self_coverage(rows),
        f"<h2 id='view2'>View 2 — Literature coverage (gap_probe outcomes by taxonomy)</h2>",
        _view2_literature_coverage(rows),
        f"<h2 id='view3'>View 3 — Precision / recall summary</h2>",
        _view3_precision_recall(rows),
        f"<p style='font-size:0.8rem;color:#999;'>n = {len(rows)} package rows.</p>",
        "</body></html>",
    ]
    out_path.write_text("\n".join(body))

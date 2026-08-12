#!/usr/bin/env python
"""Turn the enrichment search's candidates into a self-contained label sheet.

    python studies/taxonomy-validation/enrichment/make_sheet.py

Reads `candidates.jsonl` (from search.py), writes `enriched_set.csv`.

**Column-identical to `gold/gold_set.csv`, deliberately.** The A16.3 instructions
are unchanged by the protocol (s5.2), so the sheet they are used against should
be unchanged too -- same columns, same order, same meaning. Only three columns
are added, and all three are protocol requirements rather than new labeling work:

    stratum          `enriched` or `micro-ground`; s2 forbids mixing these into
                     one rate and s7 requires their yields reported separately
    search_ground    s5.3 -- which declared ground surfaced this card
    matched_pattern  s5.3 -- which keyword matched, so the selection path is
                     inspectable rather than trusted

All seven properties get label columns, not just the four being enriched. P1 is
already validated and P3/P4 are not searched for, but s3 says they are "included
if the search surfaces them incidentally" -- and the labeler is reading the card
either way, so recording what is there costs nothing and discards nothing.

Self-contained, because the gold session established that opening files to fill
rows is not a workflow. Card text travels in the sheet; `row_hash` ties every
label to the exact text labeled.

Labels are written BLANK. Nothing here consults the extractor -- the blindness
requirement in the instructions is the whole basis of the measurement.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO / "src"))

from uofa_cli.furnishers import card_eval  # noqa: E402

PROPERTIES = ["P1_score", "P2_uncertainty", "P3_sampling", "P4_determinism",
              "P5_null_baseline", "P6_claimed_cou", "P7_confound_control"]
ENRICHED_FOR = ["P2_uncertainty", "P5_null_baseline", "P6_claimed_cou",
                "P7_confound_control"]
CELL_LIMIT = 30000       # Excel caps a cell at 32,767


def _fit(text: str) -> str:
    if len(text) <= CELL_LIMIT:
        return text
    return text[:CELL_LIMIT] + (
        f"\n\n[TRUNCATED at {CELL_LIMIT:,} of {len(text):,} chars for the "
        f"spreadsheet cell limit. If a label depends on what was cut, mark "
        f"unclear and note it.]")


def build(cand_path: Path, out_dir: Path) -> dict:
    cands = [json.loads(line) for line in
             cand_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    # Interleave strata so the labeler does not meet all enriched cards first;
    # order effects stay checkable via session_id only if order is not stratum.
    cands.sort(key=lambda c: (c["row_hash"]))

    rows = []
    for i, c in enumerate(cands):
        scoped = c["eval_sections"]
        secs = card_eval.eval_sections(c.get("card") or "")
        row = {
            "row_no": i + 1,
            "card_id": c["model_id"],
            "row_hash": c["row_hash"],
            "stratum": c["stratum"],
            "search_ground": c.get("search_ground", ""),
            # Which pattern matched, per property, so a reader can see WHY this
            # card was surfaced without re-running the search.
            "matched_pattern": "; ".join(
                f"{p}={v}" for p, v in (c.get("props") or {}).items()),
            "word_count": len((c.get("card") or "").split()),
            "eval_headings": " | ".join(s.heading for s in secs),
            # THE labeling surface. Section scoping is binding (instructions s1),
            # so this is the only content that may support a `present` label.
            "eval_sections": _fit(scoped) if scoped else "(no evaluation section detected)",
        }
        for prop in PROPERTIES:
            row[prop] = ""
            row[f"{prop}_note"] = ""
        row["seen_before"] = ""
        row["link_only"] = ""
        row["session_id"] = ""
        row["labeled_at"] = ""
        # Verification only: confirms the detector did not MISS a section. Never
        # a source for `present` -- if a property appears only here, it is absent.
        row["card_full_for_verification"] = _fit(c.get("card") or "")
        rows.append(row)

    sheet = out_dir / "enriched_set.csv"
    with sheet.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    by_stratum: dict[str, int] = {}
    for r in rows:
        by_stratum[r["stratum"]] = by_stratum.get(r["stratum"], 0) + 1
    return {"n_rows": len(rows), "by_stratum": by_stratum, "sheet": str(sheet)}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--candidates", type=Path,
                    default=Path(__file__).parent / "candidates.jsonl")
    ap.add_argument("--out", type=Path, default=Path(__file__).parent)
    args = ap.parse_args()
    if not args.candidates.exists():
        raise SystemExit(f"run search.py first: {args.candidates} not found")

    res = build(args.candidates, args.out)
    print(f"sheet: {res['sheet']}")
    print(f"  rows: {res['n_rows']}  ({res['by_stratum']})")
    print(f"  enriched for: {', '.join(ENRICHED_FOR)}")
    print("  labels blank; all 7 properties present so P3/P4 accrue incidentally")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

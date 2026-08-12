#!/usr/bin/env python
"""Split every case by table-borne vs prose-borne evidence. No new runs.

    python studies/taxonomy-validation/enrichment/split_by_structure.py

Recomputes miss rates from the EXISTING per-case results in `specificity/*.json`,
partitioned by where the property's evidence sits. Costs nothing: the extractor
already ran, and every case records its outcome.

## The hypothesis this tests

P2's largest positive family is `stefan-it`: five per-run columns plus a
`mean ± std` cell, entirely inside a markdown table. If misses concentrate in
table-borne evidence ACROSS properties, the mechanism is neither relational
reading nor instruction overload -- it is structural reading of markdown tables,
and the fix is table-aware preprocessing rather than prompt design or
per-property calls.

If instead the table/prose split is flat within each property while the
relational pair (P6, P7) stays high and the lexical pair (P2, P5) does not, the
relational hypothesis survives this test and the per-property variant is the
right next measurement.

## Classification

A case is **table-borne** when the line carrying its matched lure is a markdown
table row -- two or more unescaped pipes. That is a deliberately mechanical test
on the line the evidence actually sits on, not a judgment about the card.

The lure is the right anchor because for a `present` case it IS the
characteristic language the labeler read. Cases with no recoverable lure are
counted separately rather than assigned to either side.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
CASES = _REPO / "tests/fixtures/specificity/cases.json"
PROPS = ["P2_uncertainty", "P5_null_baseline", "P6_claimed_cou",
         "P7_confound_control"]
RELATIONAL = {"P6_claimed_cou", "P7_confound_control"}


def _line_of(text: str, pos: int) -> str:
    start = text.rfind("\n", 0, pos) + 1
    end = text.find("\n", pos)
    return text[start: end if end != -1 else len(text)]


def classify(case: dict) -> str:
    """table | prose | unknown — from the line the lure sits on."""
    lure = case.get("matched_text") or ""
    if not lure:
        return "unknown"
    m = re.search(re.escape(lure), case["excerpt"])
    if not m:
        return "unknown"
    line = _line_of(case["excerpt"], m.start())
    return "table" if len(re.findall(r"(?<!\\)\|", line)) >= 2 else "prose"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--results", type=Path,
                    default=Path(__file__).parent / "specificity")
    args = ap.parse_args()

    cases = {(c["card_id"], c["property"]): c
             for c in json.loads(CASES.read_text(encoding="utf-8"))["cases"]}
    kind = {k: classify(c) for k, c in cases.items()}

    print("  case counts by structure (positives only -- the miss denominator)")
    print(f"  {'property':22s} {'table':>7s} {'prose':>7s} {'unknown':>8s}")
    for prop in PROPS:
        pos = [k for k, c in cases.items()
               if c["property"] == prop and c["expected"] == "present"]
        row = {t: sum(kind[k] == t for k in pos) for t in ("table", "prose", "unknown")}
        print(f"  {prop:22s} {row['table']:>7d} {row['prose']:>7d} {row['unknown']:>8d}")

    for path in sorted(args.results.glob("*.json")):
        if path.name.endswith(".json") and path.name.replace(
                ".corrected.json", ".json") in {
                q.name.replace(".corrected.json", ".json")
                for q in args.results.glob("*.corrected.json")} \
                and not path.name.endswith(".corrected.json"):
            continue                      # prefer the corrected v1
        d = json.loads(path.read_text(encoding="utf-8"))
        label = d["extractor"]["model"] + (" (v2)" if ".v2." in path.name else "")
        print(f"\n  === {label} ===")
        print(f"  {'property':22s} {'table miss':>18s} {'prose miss':>18s}")
        for prop in PROPS:
            rows = [r for r in d["results"]
                    if r["property"] == prop and r["expected"] == "present"
                    and r["outcome"] != "error"]
            out = {}
            for t in ("table", "prose"):
                sub = [r for r in rows if kind.get((r["card_id"], prop)) == t]
                miss = sum(r["outcome"] == "false-fire" for r in sub)
                out[t] = (f"{miss}/{len(sub)} ({miss/len(sub):.0%})"
                          if sub else "--")
            tag = " [rel]" if prop in RELATIONAL else ""
            print(f"  {prop:22s} {out['table']:>18s} {out['prose']:>18s}{tag}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

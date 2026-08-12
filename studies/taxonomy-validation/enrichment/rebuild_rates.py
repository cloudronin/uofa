#!/usr/bin/env python
"""Recompute specificity rates against corrected labels. No API calls.

    python studies/taxonomy-validation/enrichment/rebuild_rates.py

Each result file already stores, per case, whether extraction populated the
property (`populated`). The label is the OTHER half of the comparison. So when a
label changes, the outcome re-derives arithmetically:

    populated=False, expected=present  -> false-fire
    populated=False, expected=absent   -> correct
    populated=True,  expected=absent   -> false-clear
    populated=True,  expected=present  -> correct

Re-running the extractor would be wrong here, not merely wasteful: it would
change the extractor's outputs and the labels in one step, and the v1-to-v2
comparison could not attribute the difference to either. The corrected v1 rates
must come from the SAME extraction outputs the original rates came from.

Errors stay errors. A case that failed to extract has no `populated` value and
cannot be re-classified by a label change.

Writes `<slug>.corrected.json` beside each result, preserving the original.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

csv.field_size_limit(10 ** 9)

_REPO = Path(__file__).resolve().parents[3]
LABELS = _REPO / "studies/taxonomy-validation/enrichment/enriched_labels.csv"
PROPS = ["P2_uncertainty", "P5_null_baseline", "P6_claimed_cou",
         "P7_confound_control"]


def labels() -> dict[tuple[str, str], str]:
    """(card_id, property) -> label.

    Keyed on card_id, NOT row_hash: 27 rows share one eval-text hash (the
    empty-template stubs), so row_hash cannot identify a row.
    """
    out = {}
    for r in csv.DictReader(LABELS.open(encoding="utf-8")):
        for p in PROPS:
            out[(r["card_id"], p)] = (r.get(p) or "").strip().lower()
    return out


def rebuild(path: Path, lab: dict) -> dict:
    d = json.loads(path.read_text(encoding="utf-8"))
    changed = 0
    for row in d["results"]:
        if row["outcome"] == "error":
            continue                       # no `populated`; nothing to re-derive
        new = lab.get((row["card_id"], row["property"]))
        if new not in ("present", "absent") or new == row["expected"]:
            continue
        row["expected"] = new
        row["outcome"] = ("correct" if row["populated"] == (new == "present")
                          else ("false-clear" if row["populated"] else "false-fire"))
        changed += 1

    rates = {}
    for prop in PROPS:
        rows = [r for r in d["results"]
                if r["property"] == prop and r["outcome"] != "error"]
        absent = [r for r in rows if r["expected"] == "absent"]
        present = [r for r in rows if r["expected"] == "present"]
        fc = sum(r["outcome"] == "false-clear" for r in absent)
        ff = sum(r["outcome"] == "false-fire" for r in present)
        rates[prop] = {
            "n_absent": len(absent), "false_clears": fc,
            "false_clear_rate": round(fc / len(absent), 3) if absent else None,
            "n_present": len(present), "false_fires": ff,
            "false_fire_rate": round(ff / len(present), 3) if present else None,
        }
    d["rates"] = rates
    d["label_basis"] = {
        "source": "enriched_labels.csv after v3 adoption + 4 adjudicated flips",
        "sha256": hashlib.sha256(LABELS.read_bytes()).hexdigest()[:16],
        "cases_reclassified": changed,
        "note": ("recomputed from the ORIGINAL extraction outputs; the extractor "
                 "was not re-run, so any v1-to-v2 difference is attributable to "
                 "the prompt alone"),
    }
    out = path.with_suffix(".corrected.json")
    out.write_text(json.dumps(d, indent=2) + "\n")
    return {"path": out, "changed": changed, "rates": rates,
            "model": d["extractor"]["model"]}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--results", type=Path,
                    default=Path(__file__).parent / "specificity")
    args = ap.parse_args()

    lab = labels()
    for path in sorted(args.results.glob("*.json")):
        if path.name.endswith(".corrected.json"):
            continue
        r = rebuild(path, lab)
        print(f"\n  {r['model']}  ({r['changed']} cases re-classified)")
        print(f"  {'property':22s} {'false-clear':>16s} {'false-fire':>16s}")
        for p, v in r["rates"].items():
            fc = ("--" if v["false_clear_rate"] is None
                  else f"{v['false_clears']}/{v['n_absent']} ({v['false_clear_rate']:.0%})")
            ff = ("--" if v["false_fire_rate"] is None
                  else f"{v['false_fires']}/{v['n_present']} ({v['false_fire_rate']:.0%})")
            print(f"    {p:22s} {fc:>16s} {ff:>16s}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

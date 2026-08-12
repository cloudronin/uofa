#!/usr/bin/env python
"""Apply the CLASS-RULINGS to the draft sheet and emit committable labels.

    python studies/taxonomy-validation/enrichment/apply_rulings.py --labels <csv>

Writes `enriched_labels.csv`: labels and provenance, **no card bodies**, the same
shape `gold/gold_labels.csv` is committed in. The sheet the labeler works from
embeds card text to be self-contained and stays uncommitted; the labels are the
author's own work and travel with the study.

Rulings and their justification are in `CLASS-RULINGS.md`. Each is decided
against the standard the gold set already set, because sensitivity is measured
there and specificity here -- two standards would measure two different
properties. Every changed cell records which ruling moved it, so a reviewer can
overturn one class without re-reading the sheet.

The draft marker is preserved. These rulings make the draft self-consistent; they
do not make it gold.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

csv.field_size_limit(10 ** 9)

# class_rule -> (property, verdict). See CLASS-RULINGS.md for the anchor each
# was decided against; the one-line reason here is the summary, not the argument.
RULINGS = {
    "CLASS-SEALION":        ("P3_sampling", "absent",
                             "sample SIZE, not a population relationship; every "
                             "gold P3 positive is a population claim"),
    "CLASS-STEFANIT":       ("P4_determinism", "present",
                             "five linked runs aggregated as mean+/-std "
                             "discloses more than the gold anchor's best-of-5"),
    "CLASS-LMEVAL-P4":      ("P4_determinism", "absent",
                             "n-shot is a prompting condition; states nothing "
                             "about repeats, seeds or temperature (MARGINAL)"),
    "CLASS-NVIDIA-P6":      ("P6_claimed_cou", "absent",
                             "structured template metadata, same category the "
                             "pre-filter excluded 1,884 times as furniture"),
    "CLASS-TEMPLATE-EMPTY": (None, "absent",
                             "auto-generated stub, eval heading with no content"),
}

PROPS = ["P1_score", "P2_uncertainty", "P3_sampling", "P4_determinism",
         "P5_null_baseline", "P6_claimed_cou", "P7_confound_control"]
# Card text is the labeler's surface, not part of the record.
DROP = {"eval_sections", "card_full_for_verification"}


def apply(labels: Path, out: Path) -> dict:
    rows = list(csv.DictReader(labels.open(encoding="utf-8")))
    changed = {k: 0 for k in RULINGS}
    unchanged = {k: 0 for k in RULINGS}

    for r in rows:
        rule = (r.get("class_rule") or "").strip()
        if rule not in RULINGS:
            continue
        prop, verdict, reason = RULINGS[rule]
        targets = PROPS if prop is None else [prop]
        moved = False
        for p in targets:
            if (r.get(p) or "").strip().lower() == verdict:
                continue
            # TEMPLATE-EMPTY sweeps every property to absent; a `present` there
            # would be a real finding, so record rather than overwrite silently.
            r[f"{p}_note"] = (f"[{rule}] {reason}"
                              + (f" | was: {r[p]}" if r.get(p) else "")
                              + (f" | {r[f'{p}_note']}" if r.get(f"{p}_note") else ""))
            r[p] = verdict
            moved = True
        changed[rule] += bool(moved)
        unchanged[rule] += (not moved)
        r["class_ruling_applied"] = rule

    fields = [c for c in rows[0] if c not in DROP]
    if "class_ruling_applied" not in fields:
        fields.append("class_ruling_applied")
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            r.setdefault("class_ruling_applied", "")
            w.writerow(r)
    return {"rows": len(rows), "changed": changed, "unchanged": unchanged,
            "fields": fields}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--labels", required=True, type=Path)
    ap.add_argument("--out", type=Path,
                    default=Path(__file__).parent / "enriched_labels.csv")
    args = ap.parse_args()
    res = apply(args.labels, args.out)
    print(f"rows {res['rows']} -> {args.out.name} ({len(res['fields'])} cols, "
          f"no card bodies)")
    for rule in RULINGS:
        print(f"  {rule:22s} moved {res['changed'][rule]:>3d}  "
              f"already-correct {res['unchanged'][rule]:>3d}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

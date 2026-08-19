"""Regenerate TIER1_SUPPORT.md — the dig behind the R2 restatement paragraph.

W10 of the Ch4 Numbers and Repairs spec. Digs, does not write: it assembles the
12 REAL-GAP spot-check rows with the author's own rationales, the policy text,
the grounding slice and the claim locations, so the author's paragraph has its
supporting material in one place.

    python studies/phase3_stage4/build_tier1_support.py > studies/phase3_stage4/TIER1_SUPPORT.md

Sections 2-5 are static text (quotations and pointers verified by hand against
the artifacts named in them); section 1 is generated from the committed
worksheet and sample key, so the rows and rationales cannot drift from what was
actually ruled.
"""
from __future__ import annotations

import csv
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
T = ROOT / "dev/build/adversarial/phase3/triage"
STATIC = pathlib.Path(__file__).resolve().parent / "TIER1_SUPPORT.static.md"


def main() -> int:
    work = {r["case_id"]: r for r in csv.DictReader(
        (T / "adjudication_worksheet.csv").open(encoding="utf-8"))}
    key = {r["case_id"]: r for r in csv.DictReader(
        (T / "adjudication_sample_key.csv").open(encoding="utf-8"))}
    rg = sorted(k for k, r in key.items()
                if r["queue_type"] == "CONVERGENT_SAMPLE" and r["stratum"] == "REAL-GAP")
    assert len(rg) == 12, f"expected 12 REAL-GAP spot-check rows, found {len(rg)}"

    rows = "\n".join(
        f"| {i} | `{cid}` | {key[cid]['ensemble_majority_verdict']} | "
        f"**{work[cid]['author_verdict'].strip()}** |"
        for i, cid in enumerate(rg, 1))

    rationales = "\n".join(
        f"**`{cid}`**\n> {(work[cid].get('author_rationale') or '').strip()}\n"
        for cid in rg if (work[cid].get("author_rationale") or "").strip())

    print(STATIC.read_text(encoding="utf-8")
          .replace("{{ROWS}}", rows)
          .replace("{{RATIONALES}}", rationales), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

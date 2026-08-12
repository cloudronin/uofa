#!/usr/bin/env python
"""Turn labeled enrichment rows into committed extractor test cases.

    python studies/taxonomy-validation/enrichment/make_cases.py --labels <csv>

Writes `tests/fixtures/specificity/cases.json`.

The labeling produced two kinds of case, and they test opposite failures:

  expected=absent   The pre-filter's false positives. Characteristic language is
                    present, the property is not. If extraction reads "Within ±1
                    Level" as uncertainty it populates the field and SILENCES a
                    warranted weakener -- a false clear. These are far more
                    adversarial than the gold set's ordinary absences, because
                    the language is there to be misread.
  expected=present  Cards that genuinely state the property. If a rule fires
                    here it accuses a published card of an omission it did not
                    commit -- a false fire, the reputation-damaging direction
                    the enrichment stratum exists to measure.

**`hard_assert` marks the cases a test may fail on.** Labels are a
machine-drafted (A16.3 amended 2026-08-11), so most expectations are provisional
and travel as data only. A case earns `hard_assert` when its reason is
mechanically determined rather than a labeling judgment -- "Within ±1 Level" is
a tolerance band, "Out of Scope" is a classifier label name, `±` inside a
SentencePiece vocabulary dump is not a dispersion statement. Those are facts
about the text, and they stay true whoever confirms the sheet.

Excerpts are minimal spans around the match, not whole cards. The corpus is
CC-BY-4.0 with a paper (A17.3), so quoting with attribution is permitted, and
`card_id` attributes every case. Minimal anyway: a test needs the span that
fools the reader, not the document around it.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO / "src"))

csv.field_size_limit(10 ** 9)

PROPS = ["P2_uncertainty", "P5_null_baseline", "P6_claimed_cou",
         "P7_confound_control"]
EXCERPT_PAD = 420

# A reason is mechanical when it names what the text IS, independent of how a
# labeler feels about the card. Each phrase below was written by the labeler; the
# match is on the phenomenon, not on wording style.
_MECHANICAL = (
    r"vocab dump|vocabulary dump|config dump|tokenizer",       # not prose
    r"repo name|script names? only",                           # not card content
    r"label name|classifier label",                            # a class, not a claim
    r"metric name|tolerance[- ]band|tolerance band",           # a metric, not a spread
    r"rubric|scoring rubric",                                  # a rubric anchor
    r"licen[cs]e statement|licen[cs]e term",                   # a licence, not a COU
)


def _mechanical(reason: str) -> bool:
    return any(re.search(p, reason, re.I) for p in _MECHANICAL)


def _excerpt(text: str, patterns: str) -> tuple[str, str]:
    """Smallest span containing the match that fooled the pre-filter.

    The sheet joins a property's matched patterns with `|`, and the patterns
    THEMSELVES contain `|` -- `\\bstd(?:ev|\\.|\\b)` is one pattern, not three.
    Splitting on the separator shreds those into invalid regexes, which silently
    yielded an excerpt containing no lure at all. So try the joined string whole
    first: it is already a valid alternation, and it is what actually matched.
    """
    pat = (patterns or "").strip()
    for candidate in ([pat] if pat else []) + [p.strip() for p in pat.split("|")]:
        if not candidate:
            continue
        try:
            m = re.search(candidate, text, re.I)
        except re.error:
            continue
        if m:
            lo, hi = max(0, m.start() - EXCERPT_PAD), m.end() + EXCERPT_PAD
            return text[lo:hi].strip(), m.group(0)
    return text[:EXCERPT_PAD * 2].strip(), ""


def build(labels: Path, out: Path, candidates: Path | None = None) -> dict:
    rows = list(csv.DictReader(labels.open(encoding="utf-8")))
    # The SHEET truncates eval_sections at 30,000 chars for the spreadsheet cell
    # limit, and several espnet config dumps carry their lure past the cut -- an
    # excerpt with no lure in it tests nothing. Prefer the untruncated text.
    full: dict[str, str] = {}
    if candidates and candidates.exists():
        for line in candidates.read_text(encoding="utf-8").splitlines():
            if line.strip():
                c = json.loads(line)
                full[c["row_hash"]] = c["eval_sections"]
    cases, skipped = [], 0
    for r in rows:
        matched = r.get("matched_pattern", "")
        for prop in PROPS:
            label = (r.get(prop) or "").strip().lower()
            if label not in ("present", "absent"):
                continue                      # `unclear` is not an expectation
            reason = (r.get(f"{prop}_note") or "").strip()
            pat = ""
            for chunk in matched.split(";"):
                if chunk.strip().startswith(prop.split("_")[0]):
                    pat = chunk.split("=", 1)[-1].strip()
            if label == "absent" and not pat:
                skipped += 1
                continue                      # absence with no lure is not a case
            source = full.get(r["row_hash"], r["eval_sections"])
            excerpt, hit = _excerpt(source, pat)
            if label == "absent" and not hit:
                skipped += 1
                continue          # no lure recoverable -> nothing to test
            cases.append({
                "card_id": r["card_id"],
                "row_hash": r["row_hash"],
                "stratum": r["stratum"],
                "property": prop,
                "expected": label,
                "reason": reason,
                "matched_pattern": pat,
                "matched_text": hit,
                "hard_assert": bool(label == "absent" and _mechanical(reason)),
                "label_status": "machine-drafted",
                "excerpt": excerpt,
            })
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "source": "studies/taxonomy-validation/enrichment",
        "corpus": "modelbiome/ai_ecosystem_withmodelcards @ 4cb5d873 (CC-BY-4.0)",
        "attribution": "Card excerpts are quoted with attribution via card_id.",
        "label_status": ("machine-drafted, permanently. There is no "
                         "confirmed-gold path; A16.4 finding validity is the "
                         "settle authority (A16.3/A16.7 amended 2026-08-11). "
                         "Only hard_assert cases may fail a test."),
        "n_cases": len(cases),
        "n_hard_assert": sum(c["hard_assert"] for c in cases),
        "n_skipped_no_lure": skipped,
        "cases": cases,
    }
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    return payload


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--labels", required=True, type=Path)
    ap.add_argument("--candidates", type=Path,
                    default=Path(__file__).parent / "modelbiome/candidates.jsonl")
    ap.add_argument("--out", type=Path,
                    default=_REPO / "tests/fixtures/specificity/cases.json")
    args = ap.parse_args()
    p = build(args.labels, args.out, args.candidates)
    print(f"cases: {p['n_cases']}  (hard_assert {p['n_hard_assert']})")
    by = {}
    for c in p["cases"]:
        by.setdefault((c["property"], c["expected"]), 0)
        by[(c["property"], c["expected"])] += 1
    for (prop, exp), n in sorted(by.items()):
        print(f"  {prop:22s} {exp:8s} {n:>3d}")
    print(f"  -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

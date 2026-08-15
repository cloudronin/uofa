#!/usr/bin/env python3
"""What can be recovered from a rationale, in the most favourable case there is.

`tests/fixtures/extract_corpus_vv40/bundle_bologna_bcthip/ground_truth.json`
carries 23 `published_rationale` strings, each with a `pack_factor` mapping. The
labels are the *paper authors'*, not an annotator's, and no Python in the repo
read them until this. They are the cheapest real falsifier available.

## The question they answer

Probing found that the extractor writes each rationale in its filed factor's own
vocabulary regardless of what evidence it quotes, and that a second opinion
reading such a rationale names the *filed* factor 0.70 of the time and the
correct factor for a genuine misfile 4 times in 68. Any post-hoc re-attribution
that reads the rationale as written confirms the misfiling 94% of the time.

This asks the same question of prose nobody wrote to be scored: given only the
author's own rationale, can the author's factor be recovered?

## Why the answer is an upper bound and not a headline

These rationales are the friendliest possible input to a lexical method:

- short clauses, written by domain experts, no filler
- written in V&V 40 vocabulary, beside a V&V 40 gradation, for a V&V 40 factor
- so the factor's own name is often *in* its rationale ("SQA procedures from the
  vendors are referenced" for Software quality assurance)

That last one is the trap, and it is why this script reports the **name-only
null** beside every figure: a matcher that looks for nothing but the factor's
own name and acronym. Whatever the null recovers is not evidence about
attribution -- it is evidence that the author wrote the factor's name down.

One document, 23 factors, one standard. A ceiling, on the easy case.

Usage:

    PYTHONPATH=src python dev/tools/scripts/published_rationale_ceiling.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(_ROOT / "dev" / "tools" / "scripts"))
sys.path.insert(0, str(_ROOT / "src"))

from keyless_extract_probe import (  # noqa: E402
    PROMPTS,
    assert_anchors_come_from_the_prompt,
    parse_anchors,
)

GT = (_ROOT / "tests" / "fixtures" / "extract_corpus_vv40"
      / "bundle_bologna_bcthip" / "ground_truth.json")

_STOP = {"the", "and", "for", "are", "was", "were", "with", "from", "that",
         "this", "used", "use", "has", "have", "been", "its", "not", "all"}


def _toks(s: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9]{3,}", s.lower()) if t not in _STOP}


def _acronym(name: str) -> str:
    return "".join(w[0] for w in name.split() if w[0].isupper() or len(w) > 3).lower()


def name_only_null(rationale: str, factors: list[str]) -> str | None:
    """The null: match on the factor's own name and acronym, nothing else.

    Scores whatever the authors happened to restate. Any method that does not
    clearly beat this has demonstrated that the name was in the text.
    """
    low = rationale.lower()
    best, best_n = None, 0
    for f in factors:
        ft = _toks(f)
        hits = len(ft & _toks(low))
        if _acronym(f) and re.search(rf"\b{re.escape(_acronym(f))}\b", low):
            hits += len(ft)
        if hits > best_n:
            best, best_n = f, hits
    return best


def anchor_match(rationale: str, anchors: dict[str, list[str]]) -> str | None:
    """The pack prompts' own `Look for:` phrases, scored against the rationale."""
    rt = _toks(rationale)
    best, best_s = None, 0.0
    for factor, phrases in anchors.items():
        s = 0.0
        for p in phrases:
            pt = _toks(p)
            if pt:
                s = max(s, len(pt & rt) / len(pt))
        if s > best_s:
            best, best_s = factor, s
    return best


def main() -> int:
    gt = json.loads(GT.read_text())
    rows = [(f["pack_factor"], f["published_rationale"])
            for f in gt["expected_factors"]
            if f.get("pack_factor") and f.get("published_rationale")]

    anchors = parse_anchors(PROMPTS["vv40"])
    assert_anchors_come_from_the_prompt(anchors, PROMPTS["vv40"])
    factors = sorted(anchors)

    print(f"{len(rows)} author-written rationales, {GT.relative_to(_ROOT)}")
    print(f"pack factors: {len(factors)}   median rationale length: "
          f"{sorted(len(r.split()) for _, r in rows)[len(rows)//2]} words\n")

    results = {}
    for label, fn in (("name-only null", lambda r: name_only_null(r, factors)),
                      ("prompt anchors", lambda r: anchor_match(r, anchors))):
        hits = [(gold, fn(rat), rat) for gold, rat in rows]
        n = sum(1 for g, p, _ in hits if g == p)
        results[label] = (n, hits)
        print(f"  {label:<16s} {n:>2d}/{len(rows)}  ({n/len(rows):.3f})")

    null_n = results["name-only null"][0]
    anc_n = results["prompt anchors"][0]
    print(f"\n  anchors over null: {(anc_n - null_n)/len(rows):+.3f}")
    if anc_n <= null_n:
        print("  -> the anchors recover nothing the factor's own name did not.")

    print("\n  where the anchors and the author disagree:")
    for gold, pred, rat in results["prompt anchors"][1]:
        if gold != pred:
            print(f"    author: {gold}")
            print(f"    anchor: {pred}")
            print(f"      \"{rat[:96]}\"")

    print("\n  Upper bound on one document, one standard, 23 factors. Author "
          "\n  rationales are short expert clauses in the pack's own vocabulary, "
          "\n  which flatters lexical matching. Not a headline.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

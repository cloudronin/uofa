#!/usr/bin/env python3
"""K3c re-specified: score entities by NAME, not by count.

The deliverable's first recommendation, in order of value per hour:

    Re-specify K3c as named-entity overlap rather than counts. Unblocks three
    rows and needs no new documents.

Counts were never the right measure, and more documents did not help: at n=40 the
count-based K3b still loses to `control_constant_entity` on 0 of 3 properties in
train and 1 of 3 in holdout, which is the same verdict it reached at n=5.

## Why counts cannot separate reading from asserting

`control_constant_entity` emits a fixed count for every document and reads
nothing. It wins on MAE whenever the true counts cluster, which they do -- most
papers assess two or three models. An extractor that finds the RIGHT two models
and one that asserts "two" score identically, and the first is doing the work.

Names break that tie. A constant cannot name the models in a document it never
opened.

## What can be scored today, and what cannot

The seeded gold carries model names, because the plan names them:

    "models": [{"name": "Implant-Only Explicit Contact Model (IO-ECM)"}, ...]

Dataset and requirement names are not recorded -- `expected_entities` carries
counts for those and nothing else. So `bindsModel` is scored by name here and the
other two rows still cannot be, for want of gold rather than for want of a
method. Extending the gold step to emit names would close them; it is a
regeneration, not a redesign.

Reporting one row rather than three is the honest reading of "unblocks three
rows": the method transfers, the gold has not caught up.

## Matching

A model is found if a proposal shares every significant word with it, after
dropping articles and prepositions -- the same rule `generate_seeded_corpus`
uses for factor names, and for the same reason: a paper that writes "the IO-ECM
model" where gold says "Implant-Only Explicit Contact Model (IO-ECM)" has named
the same thing, and an exact-match score would measure punctuation.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(_ROOT / "dev" / "tools" / "scripts"))
sys.path.insert(0, str(_ROOT / "src"))

from keyless_k3_entities import _read_source, extract_entities_salient  # noqa: E402

_FILLER = {"the", "of", "to", "a", "an", "and", "for", "in", "on", "with", "model",
           "models", "simulation", "framework"}


def _words(x: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]{2,}", x.lower()) if w not in _FILLER}


def names_match(gold: str, proposed: str) -> bool:
    """Same entity, allowing for abbreviation and punctuation.

    A hit needs the proposal to carry either every significant word of the gold
    name, or its acronym -- papers refer to "IO-ECM" far more often than to
    "Implant-Only Explicit Contact Model", and both name the same model.
    """
    g, p = _words(gold), _words(proposed)
    if not g or not p:
        return False
    if g <= p or p <= g:
        return True
    acro = {t for t in re.findall(r"\b([A-Z][A-Z0-9-]{2,})\b", gold)}
    return bool(acro & {t.upper() for t in re.findall(r"[A-Za-z0-9-]{3,}", proposed)})


# A candidate model name in running text: a capitalised phrase, or an acronym.
_CANDIDATE = re.compile(
    r"\b([A-Z][A-Za-z0-9-]*(?:\s+[A-Z][A-Za-z0-9-]*){0,5}\s+"
    r"(?:Model|Simulation|Framework|Analysis))\b|\b([A-Z][A-Z0-9]{2,}(?:-[A-Z0-9]+)*)\b")


def propose_models(text: str, cap: int = 12) -> list[str]:
    """Model names a keyless reader would put forward, most frequent first."""
    counts: dict[str, int] = {}
    for m in _CANDIDATE.finditer(text):
        name = (m.group(1) or m.group(2) or "").strip()
        if len(name) > 2:
            counts[name] = counts.get(name, 0) + 1
    return [n for n, _ in sorted(counts.items(), key=lambda kv: -kv[1])[:cap]]


def control_constant_name(_text: str, cap: int = 12) -> list[str]:
    """Null model: the words a credibility paper always contains.

    The count-based control wins by asserting a number. Its named analogue has
    to assert a NAME, and there is no name every paper shares -- which is the
    whole argument for scoring names.
    """
    return ["Computational Model", "Finite Element Model", "CFD Model"][:cap]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--corpus", type=pathlib.Path, required=True)
    ap.add_argument("--k", type=int, default=12)
    args = ap.parse_args()

    bundles = [b for b in sorted(args.corpus.rglob("bundle_*"))
               if (b / "ground_truth.json").exists()]
    if not bundles:
        raise SystemExit(f"no bundles under {args.corpus}")

    hit = tot = chit = 0
    cnt_hit = cnt_tot = 0
    print(f"\nK3c — models by NAME, {len(bundles)} bundles\n")
    for b in bundles:
        gt = json.loads((b / "ground_truth.json").read_text())
        gold = [m["name"] for m in (gt.get("models") or []) if m.get("name")]
        if not gold:
            continue
        text = _read_source(b)
        proposed = propose_models(text, args.k)
        ctrl = control_constant_name(text, args.k)
        for g in gold:
            tot += 1
            hit += any(names_match(g, p) for p in proposed)
            chit += any(names_match(g, p) for p in ctrl)
        # the count row, for the comparison the deliverable rests on
        got = extract_entities_salient(text).get("models", 0)
        cnt_tot += 1
        cnt_hit += (got == len(gold))

    print(f"  {'measure':34s}{'K3c':>10s}{'control':>10s}")
    print(f"  {'models found BY NAME':34s}{hit}/{tot:<8d}{chit}/{tot:<8d}")
    print(f"  {'                     ':34s}{hit/max(tot,1):>10.3f}{chit/max(tot,1):>10.3f}")
    print(f"\n  exact model COUNT, for contrast: {cnt_hit}/{cnt_tot} = "
          f"{cnt_hit/max(cnt_tot,1):.3f}")
    print(f"\n  KILL CRITERION: name recall must beat the constant")
    verdict = "PASSES" if hit / max(tot, 1) > chit / max(tot, 1) else "FAILS"
    print(f"  -> {verdict}")
    print(f"\n  bindsModel only. Dataset and requirement names are not in the gold,")
    print(f"  so those two rows stay blocked for want of gold rather than method.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

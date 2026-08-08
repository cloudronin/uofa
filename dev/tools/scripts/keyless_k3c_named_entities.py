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

## All three rows

`bindsModel` could be scored immediately, because the plan already named the
models. `bindsDataset` and `bindsRequirement` could not: `expected_entities`
carried counts and nothing else, so those rows were blocked on gold rather than
on method.

Gold now emits `expected_entity_names` for all three kinds, with counts derived
from the names so the two cannot disagree. Each kind gets its own route, because
they are named differently in prose:

* a **model** is a proper noun, usually with an acronym
* a **dataset** is a body of measurements, named after its source or rig
* a **requirement** is an acceptance target, named by the quantity it bounds

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


# A MAJORITY of the longer name's words, not half. At exactly half,
# "knee simulator" matched "AMTI sixstation knee simulator" -- and the words it
# drops are the distinguishing ones, so it names a category rather than that rig.
# Genuine abbreviations are handled by the acronym path, which is why this can be
# strict without penalising "IO-ECM".
_OVERLAP = 0.60


def names_match(gold: str, proposed: str) -> bool:
    """Same entity, allowing for abbreviation and punctuation.

    Overlap is measured against the LONGER of the two, not as a subset test. A
    symmetric subset rule is fine for proper names and catastrophic for the long
    clauses gold records as requirement names: against

        "energy balance artifacts <=1% and maximum penetration <=0.02 mm
         support 8-10 on solver control"

    the bare word "balance" satisfied `p <= g` and counted as naming that
    requirement. Every short fragment did. bindsRequirement measured 0.387 that
    way, and the number was fragments.

    The acronym path survives, because it is the one case where a short proposal
    genuinely names a long entity: papers write "IO-ECM" far more often than
    "Implant-Only Explicit Contact Model", and both name the same model.
    """
    g, p = _words(gold), _words(proposed)
    if not g or not p:
        return False
    acro = {t for t in re.findall(r"\b([A-Z][A-Z0-9-]{2,})\b", gold)}
    if acro & {t.upper() for t in re.findall(r"[A-Za-z0-9-]{3,}", proposed)}:
        return True
    return len(g & p) / max(len(g), len(p)) >= _OVERLAP


# One pattern per kind, because the three are named differently in prose.
_PATTERNS = {
    "models": re.compile(
        r"\b([A-Z][A-Za-z0-9-]*(?:\s+[A-Z][A-Za-z0-9-]*){0,5}\s+"
        r"(?:Model|Simulation|Framework|Analysis))\b|"
        r"\b([A-Z][A-Z0-9]{2,}(?:-[A-Z0-9]+)*)\b"),
    "datasets": re.compile(
        r"\b([A-Z][A-Za-z0-9-]*(?:\s+[A-Za-z0-9-]+){0,4}\s+"
        r"(?:dataset|data\s?set|corpus|campaign|series|cohort|specimens?|"
        r"measurements?|tests?|trials?|bench(?:top)?|rig|study))\b|"
        r"\b(ISO\s?\d{3,5}[\w-]*|ASTM\s?[A-Z]?\d+[\w-]*)\b", re.I),
    "requirements": re.compile(
        r"\b((?:within|below|above|less than|greater than|no more than|at least)\s+"
        r"[\d.]+\s*(?:%|mm|MPa|N|kPa|s|Hz|micro\w*|percent)?[\w\s-]{0,24})\b|"
        r"\b([A-Za-z][\w\s-]{2,28}\s+(?:criterion|criteria|requirement|"
        r"acceptance\s+limit|tolerance|threshold|target))\b", re.I),
}


def propose(kind: str, text: str, cap: int = 12) -> list[str]:
    """Names a keyless reader would put forward for this kind, most frequent first."""
    counts: dict[str, int] = {}
    for m in _PATTERNS[kind].finditer(text):
        name = next((g for g in m.groups() if g), "").strip()
        if len(name) > 2:
            counts[name] = counts.get(name, 0) + 1
    return [n for n, _ in sorted(counts.items(), key=lambda kv: -kv[1])[:cap]]


def propose_models(text: str, cap: int = 12) -> list[str]:
    return propose("models", text, cap)


def control_constant_name(_text: str, cap: int = 12) -> list[str]:
    """Constant null: the phrases every credibility paper contains.

    Scores 0.000 on datasets and requirements, because no dataset name is common
    to all papers. That makes "beats the constant" a meaningless bar for those
    two rows -- any non-zero recall clears it -- so it is reported alongside a
    control that actually competes.
    """
    return ["Computational Model", "Finite Element Model", "CFD Model"][:cap]


# A capitalised phrase: what a reader would propose knowing nothing about the
# three kinds. It reads the document, so it is not free, and it is the control
# worth beating -- if a kind-specific pattern cannot outscore "the most frequent
# proper nouns", the pattern is not contributing.
_NOUN_PHRASE = re.compile(
    r"\b([A-Z][A-Za-z0-9-]*(?:\s+[a-z0-9-]+){0,3}(?:\s+[A-Z][A-Za-z0-9-]*)?)\b")


def control_frequent_phrases(text: str, cap: int = 12) -> list[str]:
    """Null model: the document's most frequent capitalised phrases."""
    counts: dict[str, int] = {}
    for m in _NOUN_PHRASE.finditer(text):
        n = m.group(1).strip()
        if len(n) > 4:
            counts[n] = counts.get(n, 0) + 1
    return [n for n, _ in sorted(counts.items(), key=lambda kv: -kv[1])[:cap]]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--corpus", type=pathlib.Path, required=True)
    ap.add_argument("--k", type=int, default=12)
    args = ap.parse_args()

    bundles = [b for b in sorted(args.corpus.rglob("bundle_*"))
               if (b / "ground_truth.json").exists()]
    if not bundles:
        raise SystemExit(f"no bundles under {args.corpus}")

    KINDS = ("models", "datasets", "requirements")
    hit = {k: 0 for k in KINDS}
    tot = {k: 0 for k in KINDS}
    chit = {k: 0 for k in KINDS}
    fhit = {k: 0 for k in KINDS}
    print(f"\nK3c — entities by NAME, {len(bundles)} bundles\n")
    for b in bundles:
        gt = json.loads((b / "ground_truth.json").read_text())
        names = gt.get("expected_entity_names") or {}
        text = _read_source(b)
        for kind in KINDS:
            gold = names.get(kind) or []
            if kind == "models" and not gold:
                gold = [m["name"] for m in (gt.get("models") or []) if m.get("name")]
            if not gold:
                continue
            proposed = propose(kind, text, args.k)
            ctrl = control_constant_name(text, args.k)
            freq = control_frequent_phrases(text, args.k)
            for g in gold:
                tot[kind] += 1
                hit[kind] += any(names_match(g, p) for p in proposed)
                chit[kind] += any(names_match(g, p) for p in ctrl)
                fhit[kind] += any(names_match(g, p) for p in freq)

    print(f"  {'property':16s}{'gold':>7s}{'K3c':>10s}{'constant':>10s}"
          f"{'freq-NP':>10s}{'verdict':>10s}")
    passed = 0
    for kind, prop in (("models", "bindsModel"), ("datasets", "bindsDataset"),
                       ("requirements", "bindsRequirement")):
        n = tot[kind]
        if not n:
            print(f"  {prop:16s}{'—':>7s}{'no gold names recorded':>30s}")
            continue
        r, c, f = hit[kind] / n, chit[kind] / n, fhit[kind] / n
        # Must beat the STRONGER of the two controls. The constant scores 0 on
        # two of three kinds, so it alone cannot decide anything.
        ok = r > max(c, f)
        passed += ok
        print(f"  {prop:16s}{n:>7d}{r:>10.3f}{c:>10.3f}{f:>10.3f}"
              f"{'PASSES' if ok else 'FAILS':>10s}")

    print(f"\n  KILL CRITERION: name recall must beat the STRONGER control, per property")
    print(f"  -> {passed}/3 properties pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

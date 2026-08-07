"""The real corpus speaks a different standard than the synthetic one.

Two separate facts, both found while trying to run K6 -- the trained sentence
classifier whose 0.615 attribution is the headline keyless figure -- against a
real document for the first time.

## 1. The label spaces are disjoint

The real bundles are assessed under NASA-STD-7009A (`rollup_7009a`, 8 factors;
`decomposed_7009a`, 6). Every synthetic bundle was generated against the pack's
NASA-STD-7009B list of 19, and carries no `cas_variant` at all. Three factor
names are common to both.

That is not a transfer *failure*. A classifier cannot be scored on labels it was
never trained to emit, so the question "does K6 transfer to real documents" is
not answerable with this pair of corpora, and no number should be reported for
it until one of them changes.

## 2. The same factor was transcribed two ways

`decomposed_7009a` carried "Data Pedigree" in 8 bundles and "Data pedigree" in
3 -- split exactly by source paper, NTRS 20230017197 in Title Case and
20240016501 in sentence case. Two transcription sessions, two conventions. Any
exact-match scorer reads them as different factors, silently halving the support
for each. Normalised to the pack's sentence case; these tests pin it.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

_REAL = _ROOT / "tests" / "fixtures" / "extract_corpus_real"
_SYN = _ROOT / "tests" / "fixtures" / "extract_corpus_v2"

pytestmark = pytest.mark.skipif(not _REAL.is_dir(), reason="real corpus absent")


def _factors(root: Path) -> Counter:
    c: Counter = Counter()
    for b in sorted(root.glob("bundle_*")):
        gt = b / "ground_truth.json"
        if gt.exists():
            for f in json.loads(gt.read_text()).get("expected_factors", []):
                c[f["factor_type"]] += 1
    return c


def test_no_factor_appears_in_two_casings():
    names = list(_factors(_REAL))
    by_lower: dict[str, list[str]] = {}
    for n in names:
        by_lower.setdefault(n.strip().lower(), []).append(n)
    dupes = {k: v for k, v in by_lower.items() if len(v) > 1}
    assert not dupes, (
        f"the same factor is spelled more than one way, so an exact-match "
        f"scorer counts it as several: {dupes}"
    )


def test_real_factor_names_use_the_packs_sentence_case():
    """"Data pedigree", not "Data Pedigree" -- so the 3 shared names really match."""
    offenders = []
    for n in _factors(_REAL):
        words = n.split()
        # Skip acronym-led tokens (M&S) and the first word, which is capitalised.
        for w in words[1:]:
            if w[:1].isupper() and w.upper() != w and "&" not in w and "/" not in w:
                offenders.append(n)
                break
    assert not offenders, f"Title Case factor names in the real corpus: {offenders}"


def test_the_two_corpora_do_not_share_a_vocabulary():
    """Pins the gap that blocks K6, so it is a known constraint and not a surprise.

    If this ever fails it is good news -- it means the corpora were brought onto
    one standard -- but it must be a deliberate change, because every keyless
    figure in the plan is measured in the synthetic vocabulary.
    """
    real = set(_factors(_REAL))
    syn = set(_factors(_SYN / "dev")) | set(_factors(_SYN / "test"))
    shared = real & syn
    assert len(shared) < len(real), (
        "the real and synthetic corpora now share a vocabulary -- K6 can be "
        "evaluated on real documents, and the plan's transfer question is live"
    )
    # Documents the exact size of the gap; update deliberately, never to be green.
    # Four of twelve. It was three before the casing was normalised -- "Use
    # History" became "Use history" and started matching the pack, which is a
    # small demonstration that the two problems were entangled.
    assert sorted(shared) == ["Data pedigree", "Results robustness",
                              "Results uncertainty", "Use history"], sorted(shared)


def test_every_real_bundle_declares_its_cas_variant():
    """The variant is what says which standard's factor list applies."""
    missing = []
    for b in sorted(_REAL.glob("bundle_*")):
        gt = b / "ground_truth.json"
        if gt.exists() and not json.loads(gt.read_text()).get("cas_variant"):
            missing.append(b.name)
    assert not missing, f"real bundles with no cas_variant: {missing}"

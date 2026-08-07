"""The real corpus speaks 7009A; the synthetic corpus speaks the 7009B pack.

Found while setting up to run K6 -- the trained sentence classifier whose 0.615
attribution is the headline keyless figure -- against a real document.

    corpus                cas_variant           standard          factors
    real,  2 bundles      rollup_7009a          NASA-STD-7009A          8
    real, 11 bundles      decomposed_7009a      NASA-STD-7009A          6
    synthetic, all 87     (none)                the 7009B pack         19

Four of the twelve published names appear verbatim in the pack. That does NOT
mean the corpora are unbridgeable: `cas_mapping.py` maps each published factor
to the pack factors that constitute it, and rolls a pack prediction UP to the
published vocabulary with a `min` rule. The direction matters and is the whole
design -- a published score is never pushed DOWN onto several pack factors,
because that would invent per-factor ground truth the document does not contain.

So the constraint on K6 is narrower than "the label spaces are disjoint": a
per-sentence prediction in pack vocabulary has to be rolled up before it can be
compared to anything a real paper printed. These tests pin the properties that
make that rollup meaningful.

## Capitalisation is deliberately NOT normalised

The two decomposed-vocabulary papers disagree -- one prints "Data Pedigree", the
other "Data pedigree" -- and each bundle keeps what its own table printed,
because that is what transcription means. `canonical()` resolves case at lookup
instead. An earlier version of this file asserted the opposite and rewrote the
ground truth to match, which forced one paper's house style onto the other's
transcription; that is reverted, and this file now tests the invariant that
actually holds.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent
_REAL = _ROOT / "tests" / "fixtures" / "extract_corpus_real"
_SYN = _ROOT / "tests" / "fixtures" / "extract_corpus_v2"
sys.path.insert(0, str(_REAL))
sys.path.insert(0, str(_ROOT / "src"))

pytestmark = pytest.mark.skipif(not _REAL.is_dir(), reason="real corpus absent")

from cas_mapping import VARIANTS, canonical, roll_up  # noqa: E402


def _bundles():
    for b in sorted(_REAL.glob("bundle_*")):
        gt = b / "ground_truth.json"
        if gt.exists():
            yield b.name, json.loads(gt.read_text())


def _factors(root: Path) -> Counter:
    c: Counter = Counter()
    for b in sorted(root.glob("bundle_*")):
        gt = b / "ground_truth.json"
        if gt.exists():
            for f in json.loads(gt.read_text()).get("expected_factors", []):
                c[f["factor_type"]] += 1
    return c


def test_every_printed_name_resolves_through_canonical():
    """The invariant that replaces "one casing everywhere".

    Bundles keep their paper's capitalisation, so the guarantee worth having is
    not that the strings match each other but that each one resolves to a key of
    its own variant. A name that does not resolve is a transcription typo, and
    it would otherwise surface much later as a silently unscored factor.
    """
    bad = []
    for name, gt in _bundles():
        for f in gt["expected_factors"]:
            try:
                canonical(f["factor_type"], gt["cas_variant"])
            except KeyError:
                bad.append((name, f["factor_type"], gt["cas_variant"]))
    assert not bad, f"printed factor names that resolve to no variant key: {bad}"


def test_every_real_bundle_declares_its_cas_variant():
    """The variant is what says which published vocabulary applies."""
    missing = [n for n, gt in _bundles() if not gt.get("cas_variant")]
    assert not missing, f"real bundles with no cas_variant: {missing}"


def test_the_pack_vocabulary_is_not_the_published_one():
    """Pins the gap K6 has to cross, so it stays a known constraint.

    If this ever fails it is good news -- the corpora were brought onto one
    vocabulary -- but it must be a deliberate change, because every keyless
    figure in the plan is measured in pack vocabulary.
    """
    real = set(_factors(_REAL))
    syn = set(_factors(_SYN / "dev")) | set(_factors(_SYN / "test"))
    shared = real & syn
    assert shared < real, (
        "the real corpus now uses only pack factor names -- transcription is no "
        "longer at published granularity, which is the value of Tier 1"
    )


def test_rollup_covers_every_published_factor_the_corpus_uses():
    """A published factor with no rollup entry cannot be scored at all.

    `People Qualifications` is the known exception and is declared unmapped
    rather than silently absent -- the pack has nothing to say about who ran the
    model, and counting that as a miss would penalise the extractor for a gap in
    the schema.
    """
    for name, gt in _bundles():
        variant = gt["cas_variant"]
        for f in gt["expected_factors"]:
            key = canonical(f["factor_type"], variant)
            assert key in VARIANTS[variant], f"{name}: {key} missing from {variant}"


def test_rollup_direction_is_pack_to_published_only():
    """The design rule, pinned: predictions roll UP, scores never push DOWN.

    Pushing a published score down onto its constituents would manufacture
    per-factor ground truth the paper never printed, which is exactly what Tier 1
    exists to avoid.
    """
    out = roll_up({"Numerical code verification": 3, "Discretization error": 1,
                   "Numerical solver error": 2}, "decomposed_7009a")
    # min, because credibility is limited by its weakest constituent.
    assert out["Code/solution verification"] == 1
    # Nothing extracted is None, not 0: "did not extract" and "extracted, scored
    # zero" are different failures.
    assert roll_up({}, "decomposed_7009a")["Code/solution verification"] is None

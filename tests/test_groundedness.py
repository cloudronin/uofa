"""The groundedness metric, and the two ways it could be gamed.

Every other metric this harness reports is reachable by a function that reads no
input. This one is not, which is the reason it exists. That also makes it worth
attacking deliberately: a metric introduced to fix untrustworthy numbers has to
survive the obvious cheat, or it becomes the next untrustworthy number.

The two cheats, both tested below:

* write nothing -- caught by `coverage`
* write contentless prose for every factor -- caught by `claim_density`, and
  invisible to coverage and groundedness alone
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "dev" / "tools" / "scripts"))

from groundedness import (  # noqa: E402
    checkable_claims,
    grounds,
    normalise_numbers,
    score_factor_rationales,
)

SOURCE = """
    Grid convergence was assessed on three meshes. GCI_fine for head rise is
    0.72% and for shaft power 0.43%. Residuals were driven below 1 × 10⁻⁵
    (scaled). The rig recorded 28.61 kPa against 28.1 kPa predicted, a 1.8%
    deviation. Sample size was 1,250 points.
"""


# ── number handling ──────────────────────────────────────────

def test_scientific_notation_survives_reformatting():
    """The source writes 1 × 10⁻⁵; the extractor writes 1e-5.

    Verified on bundle_nasa_cfd_001. Naive string matching calls that correct,
    well-grounded rationale a fabrication, which is the single most likely way
    this metric would produce a false accusation.
    """
    assert 1e-5 in normalise_numbers("driven below 1 × 10⁻⁵ (scaled)")
    assert 1e-5 in normalise_numbers("residuals below 1e-5")
    assert 1e-5 in normalise_numbers("residuals below 1 x 10^-5")
    assert 1e-5 in normalise_numbers("residuals below 1.0E-05")


def test_thousands_separators_do_not_split_a_number():
    assert 1250.0 in normalise_numbers("Sample size was 1,250 points.")
    # A comma that is not a separator must still split.
    assert {3.0, 4.0} <= normalise_numbers("meshes 3, 4")


# ── the tokeniser, pinned against the triage ─────────────────
#
# Every case below is a row the triage found the metric accusing of fabrication
# when the rationale was correct. The first pass reported 42 ungrounded rows, of
# which 28 were artefacts -- 67% against a 20% stopping rule -- so none of these
# is hypothetical. They are regression pins: if one breaks, the published
# groundedness figure is overstating hallucination again.

@pytest.mark.parametrize("text,expected,provenance", [
    ("Ns 800-1200, steady state", {800.0, 1200.0},
     "21 rows: a range hyphen read as a minus sign"),
    ("Re up to 65k (COU climb ~72k)", {65000.0, 72000.0},
     "4 rows: rationale writes 65k, source writes 65,000"),
    ("mean bias of +12K, RSS ±33K", {12.0, 33.0},
     "12 rows: K is KELVIN. An earlier fix accepted [kK] and turned 33K into "
     "33000, inventing more fabrication reports than it fixed"),
    ("28.1 kPa predicted", {28.1},
     "kPa is a unit prefix, not a magnitude suffix"),
    ("residuals below 10^-5", {1e-5},
     "6 rows: a bare exponent with no mantissa parsed as 10 and -5"),
    ("reached 10⁻⁶ to 10⁻⁸", {1e-6, 1e-8},
     "bare exponent, superscript form"),
    ("Lateral | −870 | −11.2% |", {-870.0, -11.2},
     "4 rows: the source typesets U+2212 MINUS, the extractor writes ASCII"),
    ("Forty-two thin-film RTD sensors", {42.0},
     "3 rows: sources spell counts out, extractors digitise them"),
    ("at nine speed lines", {9.0}, "same, single word"),
    ("certs CC-2024-017/018 filed", set(),
     "1 row: an identifier fragment became the claim 18"),
    ("ISO 17025 traceability", set(),
     "a standard's number is a citation, not a measurement"),
    ("a -5% deviation", {-5.0}, "a real negative must stay negative"),
    # The identifier rule must not swallow ordinary prose. It was once
    # case-insensitive and allowed any word between the keyword and the number,
    # so these three lost a real claim each -- dropping claims silently, which is
    # the same defect as inventing them and harder to notice.
    ("table shows 88% agreement", {88.0}, "'Table 4' is a citation, 'table shows 88' is not"),
    ("reference 7 locations", {7.0}, "'Ref. 7' is a citation, 'reference 7 locations' is not"),
    ("no formal bands, 12% error", {12.0}, "'No. 12' is a citation, 'no ... 12%' is not"),
])
def test_tokeniser_regressions_from_the_triage(text, expected, provenance):
    assert normalise_numbers(text) == expected, provenance


def test_rounding_is_allowed_only_where_precision_implies_it():
    """28.6 against a source reading 28.61 is rounding, not fabrication.

    The tolerance is derived from the claim's own precision rather than a fixed
    epsilon, so it admits rounding and nothing else.
    """
    assert grounds(28.6, {28.61})
    assert not grounds(28.4, {28.61})
    # An integer claim must match exactly: rounding 65 to zero places would
    # ground it against anything in [64.5, 65.5), which is a licence.
    assert not grounds(65.0, {65.4})


def test_sign_is_not_checked_and_that_is_a_documented_weakening():
    """Sources state a magnitude and put the direction in words.

    "a correction of up to 1.2 percentage points" extracted as "-1.2%" is not a
    fabrication. The cost is real and belongs in a test rather than a note.
    """
    assert grounds(-1.2, {1.2}), "the magnitude did come from the document"
    assert not grounds(1.2, {-1.2}), "one-directional: only negative claims relax"


def test_trivial_integers_are_not_checkable_claims():
    """"three meshes" grounds against any document containing a 3.

    Counting it would inflate both density and groundedness without evidence
    that the extractor read this particular document.
    """
    assert checkable_claims("assessed on 3 meshes") == set()
    assert checkable_claims("GCI_fine is 0.72%") == {0.72}


# ── the metric ───────────────────────────────────────────────

def _factors(*rationales):
    return [{"factor_type": f"F{i}", "rationale": r} for i, r in enumerate(rationales)]


def test_grounded_rationale_scores_high():
    res = score_factor_rationales(
        _factors("GCI_fine for head rise is 0.72%, shaft power 0.43%."), SOURCE)
    assert res.coverage == 1.0
    assert res.claim_density == 1.0
    assert res.groundedness == 1.0


def test_fabricated_number_is_caught():
    res = score_factor_rationales(
        _factors("GCI_fine for head rise is 9.99%."), SOURCE)
    assert res.groundedness == 0.0
    assert res.ungrounded and 9.99 in res.ungrounded[0]["missing"]


def test_writing_nothing_scores_zero_coverage():
    """The first cheat: emit no rationale.

    A keyless dictionary backend does exactly this, so the metric must report it
    as absent rather than as unmeasurable.
    """
    res = score_factor_rationales(
        [{"factor_type": "F1", "rationale": None},
         {"factor_type": "F2", "rationale": "   "}], SOURCE)
    assert res.coverage == 0.0
    assert res.claim_density == 0.0
    # Not 1.0: making no claim is not the same as making only true ones.
    assert res.groundedness == 0.0


def test_contentless_prose_is_caught_by_claim_density():
    """The second cheat, and the reason claim_density exists.

    "evidence was reviewed and found adequate" for every factor scores coverage
    1.0 and contributes zero rows to the groundedness denominator, because there
    is nothing in it to check. Against a two-number metric that is the optimal
    strategy: perfect coverage, and groundedness cannot be computed so it cannot
    be lost.
    """
    filler = "Evidence was reviewed and found adequate for this factor."
    res = score_factor_rationales(_factors(filler, filler, filler), SOURCE)

    assert res.coverage == 1.0, "the cheat does achieve full coverage"
    assert res.claim_density == 0.0, "and claim_density is what exposes it"
    assert res.claims_total == 0


def test_repetition_passes_all_three_numbers_and_only_distinctness_catches_it():
    """The loophole that "read the three together" does not close.

    Measured on a real bundle: a control quoting one sentence of the source for
    every factor scores coverage 1.000, claim density 1.000 AND groundedness
    1.000. Every figure it cites is real and every rationale carries one, so
    nothing in the first three numbers separates "found thirteen pieces of
    evidence" from "found one and pasted it thirteen times".

    Density counts rationales that carry a claim. It never asks whether they
    carry the *same* claim. That is why distinctness is a fourth column rather
    than an implication of the other three.
    """
    quoted = "GCI_fine for head rise is 0.72% and shaft power 0.43%."
    res = score_factor_rationales(_factors(*([quoted] * 13)), SOURCE)

    assert res.coverage == 1.0
    assert res.claim_density == 1.0
    assert res.groundedness == 1.0
    assert res.distinctness == 0.0, (
        "the repetition cheat must fail on distinctness and nothing else")


def test_distinctness_catches_partial_overlap_not_just_exact_repeats():
    """A method quoting overlapping windows of one paragraph has still restated it.

    Containment rather than symmetric Jaccard, so a long quote and a sentence
    taken from inside it count as the same span -- Jaccard would call them
    different because their lengths differ.
    """
    long_quote = ("Grid convergence was assessed on three meshes and GCI_fine "
                  "for head rise is 0.72% and for shaft power 0.43%.")
    inside_it = "GCI_fine for head rise is 0.72%"
    res = score_factor_rationales(_factors(long_quote, inside_it), SOURCE)
    assert res.distinctness == 0.0

    genuinely_different = "The rig recorded 28.61 kPa against 28.1 kPa predicted."
    res2 = score_factor_rationales(_factors(long_quote, genuinely_different), SOURCE)
    assert res2.distinctness == 1.0


def test_the_llm_scores_high_on_distinctness():
    """The contrast that makes the control's 0.000 meaningful.

    Measured over the shipped corpus: 0.995. If this collapses, the extractor
    has started repeating itself and the other three numbers will not say so.
    """
    res = score_factor_rationales(
        _factors("GCI_fine is 0.72%.", "Residuals below 1e-5.",
                 "Sample size was 1,250 points."), SOURCE)
    assert res.distinctness == 1.0


def test_the_cheat_is_distinguishable_from_real_work():
    """Side by side, the three numbers must separate them."""
    filler = score_factor_rationales(
        _factors("Evidence reviewed and found adequate.") * 1, SOURCE)
    real = score_factor_rationales(
        _factors("GCI_fine 0.72%, deviation 1.8% against 28.61 kPa."), SOURCE)

    assert filler.coverage == real.coverage == 1.0        # indistinguishable here
    assert filler.claim_density < real.claim_density      # and separated here
    assert filler.groundedness < real.groundedness


# ── contamination ────────────────────────────────────────────

def test_refuses_a_grounding_reference_that_is_not_the_source():
    """evidence_keywords are verbatim source spans.

    Grounding against them would score any echo of the source at 1.000 by
    construction, and score_factors does not read them, so nothing downstream
    would notice.
    """
    gt = {"expected_factors": [
        {"evidence_keywords": ["grid convergence index", "Richardson extrapolation",
                               "mesh refinement study", "asymptotic range"]}]}
    with pytest.raises(SystemExit, match="CONTAMINATION"):
        score_factor_rationales(_factors("GCI 0.72%"), "grid convergence index", gt)

    # The real source documents are far larger and pass.
    score_factor_rationales(_factors("GCI 0.72%"), SOURCE * 20, gt)


# ── the live corpus ──────────────────────────────────────────

def test_llm_baseline_on_the_shipped_corpus():
    """Pins what the current extractor scores, so a regression is visible.

    These are the numbers a candidate backend has to be compared against, and
    unlike detection F1 there is no constant function that reaches them.
    """
    from extracted_corpus import extracted_corpus_by_bundle
    from groundedness import GroundednessResult, read_source_text

    # See test_per_factor_fields: the xlsx are gitignored, so this read nothing
    # in CI and failed on totals of zero.
    by_bundle = extracted_corpus_by_bundle()
    assert by_bundle, ("extracted_rows.json is missing; regenerate with "
                       "dev/tools/scripts/dump_corpus_rows.py")
    agg = GroundednessResult()
    for rel, facs in sorted(by_bundle.items()):
        bd = _ROOT / "tests" / "fixtures" / "extract_corpus" / rel
        res = score_factor_rationales(facs, read_source_text(bd))
        for k in ("factors_total", "factors_with_rationale", "rationales_with_claims",
                  "claims_total", "claims_grounded"):
            setattr(agg, k, getattr(agg, k) + getattr(res, k))
        agg.ungrounded += res.ungrounded

    assert agg.factors_total == 800
    assert agg.coverage == pytest.approx(0.974, abs=0.005)
    assert agg.claim_density == pytest.approx(0.565, abs=0.01)
    assert agg.groundedness == pytest.approx(0.994, abs=0.003)
    assert (agg.claims_grounded, agg.claims_total) == (859, 864)

    # The triage set, hand-classified in full: three derived quantities and one
    # out-of-bundle constant (101.325 kPa, standard atmosphere). Zero
    # fabrications in 842 checkable claims, and zero metric artefacts -- which is
    # what cleared the stopping rule.
    #
    # If this count rises, the artefact rate is unknown again and the figure in
    # docs/keyless-extract-findings.md is no longer substantiated. Re-triage
    # before republishing it.
    assert len(agg.ungrounded) == 4
    assert sorted(u["factor_type"] for u in agg.ungrounded) == [
        "Equivalency of input parameters",
        "Numerical solver error",
        "Output comparison",
        "Results robustness",
    ]

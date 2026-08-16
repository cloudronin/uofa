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
    assert_attribution_available,
    attribution_confusion,
    checkable_claims,
    grounds,
    normalise_numbers,
    null_battery,
    null_document_order,
    null_shotgun,
    permutation_null,
    score_attribution,
    score_attribution_by_sentence,
    score_attribution_full,
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

    The pins track the current pipeline deliberately. A check left standing red
    as a reminder stops being a check: it alerts nobody when something *else*
    drifts through it, and it is the vacuous-pass rule inverted -- an assertion
    that cannot meaningfully fail because it has already failed. Where the
    pipeline changes, these move, and the superseded figures are recorded in
    the comment below and in studies/hosted-model-specificity/, which commits
    the full row sets on both sides.
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
    assert agg.coverage == pytest.approx(1.000, abs=0.005)
    # Widened deliberately -- see the run-to-run note below. Two runs of the
    # IDENTICAL pinned config gave 0.199 and 0.115, so a +/-0.01 pin on this
    # quantity was pinning a sample, not a property.
    assert agg.claim_density == pytest.approx(0.157, abs=0.06)
    assert agg.groundedness >= 0.98
    assert 100 <= agg.claims_total <= 220

    # These pins moved on 2026-08-14 when the baseline was regenerated after the
    # C3 hosted-model migration. Recorded here rather than only in the diff,
    # because the direction is the point:
    #
    #                        qwen3.5:4b      Llama-3.3-70B
    #   coverage                  0.974      1.000     up
    #   groundedness              0.994      0.990     flat
    #   claim_density             0.565      0.199     DOWN 65%
    #   claims_total                864        200     DOWN 77%
    #
    # RUN-TO-RUN, 2026-08-15. Two regenerations of the corpus at the IDENTICAL
    # pinned config -- same prompt sha, same model, same temperature -- gave:
    #
    #   claim_density   0.199   and   0.115      (42% relative swing)
    #   claims_total      200   and     125
    #   groundedness    0.990   and   1.000
    #   ungrounded          1   and       0
    #
    # So claim_density is not stable to three decimals on this corpus, and the
    # old +/-0.01 pin was pinning one sample of an unstable quantity. That is
    # W-EV-DET-03 one level down from where studies/model-selection just found
    # it -- the baseline had no repeat policy either.
    #
    # The bands here are wide enough to hold both observed runs. Note that
    # acceptance_criteria_distinct in test_per_factor_fields was ALREADY a band
    # (300-420) and survived this regeneration at 314 without edit, which is
    # evidence that bands are the right shape for these quantities and points
    # are not.
    #
    # Two of the three moved the reassuring way while the number of checkable
    # claims in the corpus fell by three quarters. That is why the triple is
    # asserted as a triple and why groundedness is never quoted alone: on its
    # own it reports this migration as a clean improvement.
    #
    # studies/hosted-model-specificity/ holds both row sets and the declared
    # questions. Do not "fix" a future failure here by relaxing claim_density --
    # a drop is the finding, not the noise.
    # The triage set, hand-classified in full. Under qwen it was four items --
    # three derived quantities and one out-of-bundle constant (101.325 kPa,
    # standard atmosphere), zero fabrications in 864 checkable claims. It is now
    # one, over 200 checkable claims.
    #
    # Read that against claim_density, not on its own: a shrinking triage set is
    # what a shrinking denominator produces whether or not anything improved.
    # Four in 864 is 0.46%; one in 200 is 0.50%. The artefact *rate* did not
    # move. Only the amount of output exposed to the check did.
    #
    # If this count rises, the artefact rate is unknown again and the figure in
    # docs/keyless-extract-findings.md is no longer substantiated. Re-triage
    # before republishing it.
    assert len(agg.ungrounded) <= 4


# ── attribution: which factor was the evidence filed under ───

def _gt(**factors):
    """ground_truth with one factor per kwarg: name -> its evidence keywords."""
    return {"expected_factors": [
        {"factor_type": name.replace("_", " "), "evidence_keywords": kws}
        for name, kws in factors.items()]}


def test_a_rationale_citing_another_factors_evidence_is_misfiled():
    """The failure the pair table exists to name.

    `score_attribution` counts this as one miss and stops. The evidence is in
    the document; it is under the wrong heading. That is a routing defect, and
    it is fixed differently from a rationale that cites nothing.
    """
    gt = _gt(Test_conditions=["calibrated thermocouples"],
             Test_samples=["iso 9906:2012 grade 1b"])
    rows = attribution_confusion(
        [{"factor_type": "Test conditions",
          "rationale": "Testing followed ISO 9906:2012 Grade 1B throughout."}], gt)

    assert len(rows) == 1
    assert rows[0]["kind"] == "misfiled"
    assert rows[0]["matches"] == ["Test samples"]


def test_a_rationale_matching_nothing_is_unmatched_not_misfiled():
    """The other failure, which must never be added to the first.

    Either the rationale cites evidence the annotation does not cover, or it
    cites nothing checkable. Neither is a routing problem, and a combined
    count would send someone to fix routing.
    """
    gt = _gt(Test_conditions=["calibrated thermocouples"],
             Test_samples=["iso 9906:2012 grade 1b"])
    rows = attribution_confusion(
        [{"factor_type": "Test conditions",
          "rationale": "The team considered this factor adequately addressed."}], gt)

    assert len(rows) == 1
    assert rows[0]["kind"] == "unmatched"
    assert rows[0]["matches"] == []


def test_a_correct_attribution_produces_no_confusion_row():
    gt = _gt(Test_conditions=["calibrated thermocouples"])
    assert attribution_confusion(
        [{"factor_type": "Test conditions",
          "rationale": "Measured with calibrated thermocouples at three stations."}],
        gt) == []


def test_confusion_rows_equal_the_miss_count_exactly():
    """The invariant that keeps the table honest.

    The table and the score read the same keywords under the same rule, via one
    shared `_matches`. If they ever diverge -- a table computed by a slightly
    different rule than the score it explains -- the pairs would describe
    failures the headline does not have. One row per miss, always.
    """
    gt = _gt(Test_conditions=["calibrated thermocouples"],
             Test_samples=["iso 9906:2012 grade 1b"],
             Model_inputs=["material properties from coupon testing"])
    factors = [
        {"factor_type": "Test conditions",
         "rationale": "Measured with calibrated thermocouples."},          # right
        {"factor_type": "Test samples",
         "rationale": "Material properties from coupon testing were used."},  # misfiled
        {"factor_type": "Model inputs",
         "rationale": "Considered adequate by the review board."},         # unmatched
    ]
    right, scored = score_attribution(factors, gt)
    rows = attribution_confusion(factors, gt)

    assert (right, scored) == (1, 3)
    assert len(rows) == scored - right
    assert sorted(r["kind"] for r in rows) == ["misfiled", "unmatched"]


def test_a_row_is_skipped_the_same_way_the_score_skips_it():
    """Skips must agree too, or the denominators drift apart.

    A factor with no reference keywords, or no rationale, is not scored -- so it
    cannot appear as a failure either.
    """
    gt = _gt(Test_conditions=["calibrated thermocouples"], Unreferenced=[])
    factors = [{"factor_type": "Unreferenced", "rationale": "Something was done."},
               {"factor_type": "Test conditions", "rationale": None}]

    assert score_attribution(factors, gt) == (0, 0)
    assert attribution_confusion(factors, gt) == []


# ── attribution: the nulls, and what the rule is worth ───────

# A source big enough that a k=20 blob is a genuine subset rather than the
# whole document, and a candidate that is deliberately imperfect. Both matter:
# on a short source every shotgun contains every reference and the sweep is
# tautological, and against a perfect candidate a null can only tie.
_SRC_SENTS = [
    "Grid convergence was assessed on three successively refined meshes.",
    "GCI_fine for head rise is 0.72% and for shaft power 0.43%.",
    "Richardson extrapolation gave an observed order of 1.94.",
    "Residuals were driven below 1e-5 scaled for all equations.",
    "The solver used a coupled pressure-velocity scheme.",
    "Iteration counts averaged 340 per timestep.",
    "The rig recorded 28.61 kPa against 28.1 kPa predicted.",
    "Agreement across nine speed lines was within 1.8%.",
    "Sample size was 1,250 measurement points.",
    "Specimens were production-representative castings.",
    "Testing followed ISO 9906:2012 Grade 1B throughout.",
    "Ambient conditions were held at 20C plus or minus 0.5C.",
    "Instruments carried ISO 17025 calibration certificates.",
    "Material properties came from coupon testing at 20C.",
    "Geometry was taken from the as-built CMM scan.",
    "Boundary conditions were measured at the inlet plane.",
    "An independent reviewer checked the boundary conditions.",
    "Mesh quality metrics were logged for every run.",
    "The turbulence model was k-omega SST throughout.",
    "Known limitations include the neglect of cavitation.",
    "Wall roughness was set from the surface finish specification.",
    "The validation envelope covers 60 to 110 percent of design flow.",
    "Cruise conditions sit outside the validated range.",
    "Uncertainty on the measured head was 0.15 metres.",
    "A sensitivity study varied inlet temperature by 5 kelvin.",
    "Configuration management used Git with tagged releases.",
    "Two review cycles preceded this assessment.",
    "The model has six months of prior operational use.",
    "No cavitation testing was performed for this study.",
    "Post-processing scripts were checked against hand calculations.",
]

_BATTERY_SOURCE = "\n".join(_SRC_SENTS)

_BATTERY_GT = _gt(
    Discretization_error=["gci_fine for head rise is 0.72%"],
    Numerical_solver_error=["residuals were driven below 1e-5"],
    Output_comparison=["28.61 kpa against 28.1 kpa predicted"],
    Test_samples=["sample size was 1,250 measurement points"],
    Test_conditions=["iso 9906:2012 grade 1b"],
    Model_inputs=["material properties came from coupon testing"],
    Use_error=["an independent reviewer checked the boundary conditions"],
    Model_form=["turbulence model was k-omega sst"],
    Equivalency_of_input_parameters=["boundary conditions were measured at the inlet plane"],
    Relevance_of_the_validation_activities_to_the_COU=[
        "validation envelope covers 60 to 110 percent of design flow"],
)

# Six of ten match their reference; four are plausible prose that cites nothing
# the annotation covers. That puts the candidate near the corpus figure (0.607)
# rather than at a ceiling a null cannot exceed.
_BATTERY_FACTORS = [
    {"factor_type": "Discretization error",
     "rationale": "GCI_fine for head rise is 0.72%, from three meshes."},
    {"factor_type": "Numerical solver error",
     "rationale": "Residuals were driven below 1e-5 scaled."},
    {"factor_type": "Output comparison",
     "rationale": "The rig recorded 28.61 kPa against 28.1 kPa predicted."},
    {"factor_type": "Test samples",
     "rationale": "Sample size was 1,250 measurement points."},
    {"factor_type": "Test conditions",
     "rationale": "Testing followed ISO 9906:2012 Grade 1B."},
    {"factor_type": "Model inputs",
     "rationale": "Material properties came from coupon testing."},
    {"factor_type": "Use error",
     "rationale": "The setup was reviewed and found adequate."},
    {"factor_type": "Model form",
     "rationale": "The physics representation is considered appropriate."},
    {"factor_type": "Equivalency of input parameters",
     "rationale": "Inputs were judged equivalent to the test conditions."},
    {"factor_type": "Relevance of the validation activities to the COU",
     "rationale": "Validation is considered relevant to the intended use."},
]


def test_the_record_returns_exactly_what_the_pair_returned():
    """`score_attribution_full` may add numbers; it may not change one.

    The record exists so nothing has to be recomputed by a second code path.
    The moment its `(right, scored)` diverges from `score_attribution`, every
    figure in the repo splits into two lineages.
    """
    right, scored = score_attribution(_BATTERY_FACTORS, _BATTERY_GT)
    res = score_attribution_full(_BATTERY_FACTORS, _BATTERY_GT)
    assert (res.right, res.scored) == (right, scored)


def test_abstention_is_counted_wrong_not_counted_nowhere():
    """`rate` and `rate_over_gold` must diverge when the extractor declines.

    A factor with a reference and no rationale leaves `rate`'s denominator
    entirely, so declining to answer raises the headline. `rate_over_gold`
    is the number that does not reward silence.
    """
    silent = _BATTERY_FACTORS[:3] + [
        {"factor_type": "Test samples", "rationale": None},
        {"factor_type": "Test conditions", "rationale": "   "},
    ]
    res = score_attribution_full(silent, _BATTERY_GT)

    assert res.scored == 3 and res.right == 3
    assert res.rate == 1.0, "three of three scored rationales matched"
    assert res.gold_scorable == 10
    assert res.abstained == 7
    assert res.rate_over_gold == pytest.approx(3 / 10)
    assert res.rate > res.rate_over_gold, (
        "abstention must cost something somewhere, or declining to answer is "
        "the optimal play")


def test_verbatim_and_loose_are_reported_as_two_numbers():
    """A paraphrase counts, and that decision has to stay visible.

    98% of sonnet's rationales are written rather than quoted, so a
    verbatim-only rule scored it 0.422 against K6's 0.645 -- reading that as
    "a TF-IDF classifier attributes better than sonnet" would have been wrong.
    But merging the two hides which one a figure came from.
    """
    paraphrased = [{"factor_type": "Test conditions",
                    "rationale": "Conditions followed the ISO 9906:2012 standard "
                                 "at Grade 1B tolerance."}]
    res = score_attribution_full(paraphrased, _BATTERY_GT)
    assert res.right == 1, "the loose rule accepts a reworded reference"
    assert res.right_verbatim == 0, "and the verbatim count records that it was reworded"
    assert res.rate == 1.0 and res.rate_verbatim == 0.0


def test_an_unmeasured_attribution_refuses_instead_of_returning_zero():
    """AGENTS.md 13: an unmeasured thing may not render as a passed thing.

    `(0, 0)` renders as an omitted row, which is indistinguishable from a run
    where attribution was fine. The guard is the difference between "we did not
    measure this" and silence.
    """
    empty = score_attribution_full(_BATTERY_FACTORS, _gt(Some_factor=[]))
    assert empty.scored == 0
    with pytest.raises(SystemExit, match="ATTRIBUTION NOT MEASURED"):
        assert_attribution_available(empty)

    assert_attribution_available(score_attribution_full(_BATTERY_FACTORS, _BATTERY_GT))


def test_the_document_order_null_scores_near_zero():
    """The constant router: walk the document, one sentence per factor.

    Measured at 0.058 in the keyless pipeline against a real router's 0.62.
    This is the one place attribution has behaved like a discriminating metric,
    and it is why the metric is being repaired rather than discarded.
    """
    names = [f["factor_type"] for f in _BATTERY_FACTORS]
    right, scored = score_attribution(
        null_document_order(names, _SRC_SENTS), _BATTERY_GT)
    assert scored > 0
    assert right / scored <= 0.30


def test_the_permutation_null_is_low_and_stable():
    """Chance level computed on the run's own rationales.

    Inherits their length and vocabulary, which a synthetic null would not --
    and length is the confound. Measured on the shipped corpus at 0.094.
    """
    null = permutation_null(_BATTERY_FACTORS, _BATTERY_GT, iterations=200)
    assert null["iterations"] == 200
    assert null["mean"] < 0.30, f"chance level should be low, got {null['mean']}"


def test_the_battery_reports_every_null_and_the_sweep():
    names = [f["factor_type"] for f in _BATTERY_FACTORS]
    battery = null_battery(_BATTERY_FACTORS, _BATTERY_GT, _SRC_SENTS)
    assert set(battery) >= {"document_order", "first_sentence", "permutation",
                            "shotgun_k1", "shotgun_k5", "shotgun_k12", "shotgun_k20"}
    assert battery["shotgun_k20"] >= battery["shotgun_k1"], (
        "the sweep must be monotone-ish in k, or it is not measuring length")
    assert names  # the battery is built from the candidate's own factor list


def test_a_longer_rationale_cannot_buy_attribution():
    """Length must not be worth attribution points.

    This shipped as xfail(strict=True) in Phase 1 and flipped here. The old
    keyword-overlap rule failed it outright: on the shipped corpus, 740 scored
    rationales, a 20-sentence shotgun blob -- k random source sentences, the
    identical blob under every factor, carrying no attribution judgment by
    construction -- scored 0.7527 against the extractor's 0.6068.

    Sentence-index attribution takes the same shotgun to 0.0702. The sweep is
    nearly flat in k (0.0289 / 0.0495 / 0.0646 / 0.0702 at k = 1, 5, 12, 20),
    which is what length-invariance looks like.

    The old rule is kept scored beside it in
    `test_the_old_rule_still_fails_this`, because a repair is only legible next
    to the defect.
    """
    names = [f["factor_type"] for f in _BATTERY_FACTORS]
    cand = score_attribution_by_sentence(
        _BATTERY_FACTORS, _BATTERY_GT, _BATTERY_SOURCE, _SRC_SENTS)
    cand_rate = cand.rate

    for k in (5, 12, 20):
        rows = null_shotgun(names, _SRC_SENTS, k)
        res = score_attribution_by_sentence(
            rows, _BATTERY_GT, _BATTERY_SOURCE, _SRC_SENTS)
        assert res.rate < cand_rate, (
            f"a {k}-sentence blob carrying no attribution judgment scored "
            f"{res.rate:.3f} against the extractor's {cand_rate:.3f}")


def test_the_old_rule_still_fails_this():
    """The defect, kept measurable so the repair stays legible.

    If this ever starts passing, either the old rule was changed -- it must not
    be, it is the historical figure -- or the fixture stopped exercising the
    defect, which is how the first version of this test went wrong.
    """
    names = [f["factor_type"] for f in _BATTERY_FACTORS]
    right, scored = score_attribution(_BATTERY_FACTORS, _BATTERY_GT)
    cand_rate = right / scored

    rows = null_shotgun(names, _SRC_SENTS, 20)
    r, s = score_attribution(rows, _BATTERY_GT)
    assert r / s > cand_rate, (
        "the old keyword-overlap rule is supposed to be buyable by length; if "
        "it no longer is, this fixture is not exercising the defect")

"""The two per-factor columns the scorer used to parse and throw away.

`required_level` and `acceptance_criteria` are filled on 98.5% of corpus rows
and neither was scored. The gap between required and achieved is the first thing
a V&V 40 reviewer looks at -- it says whether the evidence reaches the rigour the
model's risk demands -- and it was invisible to every number this harness
reported.

The tests that matter here are the ones about *what kind* of number is being
reported: a distribution is not an accuracy, and reporting one as the other is
the confusion this whole exercise exists to stop.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "dev" / "tools" / "scripts"))

from score_extraction import score_per_factor_fields  # noqa: E402


def _rows(*triples):
    """(factor, required, achieved) -> extracted-factor dicts."""
    return [{"factor_type": ft, "required_level": req, "achieved_level": ach,
             "acceptance_criteria": f"criterion for {ft}"}
            for ft, req, ach in triples]


# ── the shortfall ────────────────────────────────────────────

def test_shortfall_is_achieved_minus_required():
    s = score_per_factor_fields(_rows(("A", 3, 2), ("B", 2, 2), ("C", 2, 4)), [])
    assert s["shortfall_distribution"] == {-1: 1, 0: 1, 2: 1}
    assert s["rows_below_required"] == 1


def test_fractional_levels_survive():
    """Real reports publish 2.3 and 1.6; the synthetic corpus is integer-only.

    A scorer that assumed integers passed on synthetic data and would silently
    misreport every real bundle.
    """
    s = score_per_factor_fields(_rows(("A", 3.0, 2.3), ("B", 3.0, 1.6)), [])
    assert s["rows_below_required"] == 2
    assert set(s["shortfall_distribution"]) == {-0.7, -1.4}


def test_equal_shortfalls_land_in_one_bucket():
    """2.3 - 3.0 is -0.7000000000000002 in binary floating point.

    Unrounded it buckets separately from the -0.7 that 1.3 - 2.0 produces, and
    the histogram fragments into singleton bins that look like a spread.
    """
    s = score_per_factor_fields(_rows(("A", 3.0, 2.3), ("B", 2.0, 1.3)), [])
    assert s["shortfall_distribution"] == {-0.7: 2}


def test_a_row_missing_either_level_is_not_counted_as_meeting_it():
    """Absent is not zero and not equal. It contributes to neither side."""
    s = score_per_factor_fields(
        [{"factor_type": "A", "required_level": 3, "achieved_level": None},
         {"factor_type": "B", "required_level": None, "achieved_level": 2}], [])
    assert s["rows_with_shortfall"] == 0
    assert s["rows_below_required"] == 0
    assert s["required_level_present"] == 1


# ── distribution is not accuracy ─────────────────────────────

def test_without_ground_truth_only_a_distribution_is_reported():
    """The synthetic corpus has no expected_required_level.

    Reporting a distribution as though it were accuracy is exactly the failure
    that made the detection F1 meaningless, so the flag has to be explicit
    rather than inferred from an empty count.
    """
    gt = [{"factor_type": "A", "expected_level": 2}]     # no threshold key
    s = score_per_factor_fields(_rows(("A", 3, 2)), gt)
    assert s["required_level_scored"] is False
    assert s["required_level_comparable"] == 0
    assert s["required_level_distribution"] == {3: 1}


def test_with_transcribed_thresholds_accuracy_is_computed():
    gt = [{"factor_type": "A", "expected_required_level": 3},
          {"factor_type": "B", "expected_required_level": 2}]
    s = score_per_factor_fields(_rows(("A", 3, 2), ("B", 4, 2)), gt)
    assert s["required_level_scored"] is True
    assert (s["required_level_exact"], s["required_level_comparable"]) == (1, 2)


def test_accuracy_ignores_factors_the_ground_truth_does_not_threshold():
    """Partial profiles are real: some tables print only some factors.

    A factor with no published threshold must not count as a miss, or the
    extractor is charged for a row the document never asserted.
    """
    gt = [{"factor_type": "A", "expected_required_level": 3},
          {"factor_type": "B"}]
    s = score_per_factor_fields(_rows(("A", 3, 2), ("B", 4, 2)), gt)
    assert s["required_level_comparable"] == 1
    assert s["required_level_exact"] == 1


# ── acceptance criteria, and the cheat coverage cannot see ───

def test_acceptance_criteria_reports_distinctness_not_just_coverage():
    """The filler strategy again, in a different column.

    Emitting one sentence for every factor scores 100% coverage. Only the
    distinct count separates it from real per-factor content -- the same hole
    claim_density closes for rationale.
    """
    filler = [{"factor_type": f"F{i}", "required_level": 2, "achieved_level": 2,
               "acceptance_criteria": "Evidence was reviewed and found adequate."}
              for i in range(8)]
    s = score_per_factor_fields(filler, [])
    assert s["acceptance_criteria_present"] == 8, "the cheat does get full coverage"
    assert s["acceptance_criteria_distinct"] == 1, "and distinctness is what exposes it"


def test_blank_and_whitespace_criteria_do_not_count_as_present():
    s = score_per_factor_fields(
        [{"factor_type": "A", "acceptance_criteria": "   "},
         {"factor_type": "B", "acceptance_criteria": None},
         {"factor_type": "C", "acceptance_criteria": "GCI below 1.5%"}], [])
    assert s["acceptance_criteria_present"] == 1


# ── the corpus figures these claims rest on ──────────────────

def test_the_synthetic_corpus_shortfall_rate():
    """Pins 19.5%, the number the real bundles are compared against.

    If this moves, the claim in the Tier 1 corpus tests that real models fall
    short far more often is comparing against a stale baseline.

    The pins track the current pipeline. Superseded figures are recorded below
    rather than left standing as a failing assertion -- a check that is already
    red cannot report the next thing that drifts through it.
    """
    from extracted_corpus import extracted_corpus_rows

    # From the committed JSON, not from extracted.xlsx. Those are gitignored, so
    # in CI every loop body was skipped, the totals came out zero, and this
    # failed on an assertion that said nothing about the cause.
    rows = extracted_corpus_rows()
    assert rows, ("extracted_rows.json is missing; regenerate with "
                  "dev/tools/scripts/dump_corpus_rows.py")

    s = score_per_factor_fields(rows, [])
    assert s["rows"] == 800
    assert s["required_level_present"] == 800
    # Banded for the same reason as test_groundedness's triple: two
    # regenerations at the identical pinned config gave 156 and 134 rows below
    # required (0.195 and 0.168). A point pin here was pinning a sample.
    assert 120 <= s["rows_below_required"] <= 170
    assert s["rows_below_required"] / s["rows_with_shortfall"] == pytest.approx(0.181, abs=0.025)

    # This one is a finding, not a pin. It was `> 700` against the qwen3.5:4b
    # baseline, where 738 of 788 filled criteria were distinct across the corpus
    # (0.937). After the C3 migration to Llama-3.3-70B it is 343 of 774 (0.443):
    # the model writes a generic criterion per factor and reuses it in every
    # document. Within a bundle distinctness is still 1.000 -- which is why the
    # per-factor report, which only counts within a bundle, cannot see this and
    # prints "13 distinct" truthfully.
    #
    # The band is set around the measured value, tight enough that a further
    # collapse toward pure boilerplate fires, and open enough that recovering
    # specificity does not. Cause and recovery threshold are declared in
    # studies/hosted-model-specificity/FINDINGS.md (Q1: >= 0.70 on the shared
    # thirteen means the prompt's "or implied" licence is the cause).
    #
    # If this fails LOW, criteria became more boilerplate: read the finding, do
    # not widen the band. If it fails HIGH, something recovered specificity and
    # the finding needs updating with what did it.
    assert 300 < s["acceptance_criteria_distinct"] < 420, (
        f'acceptance_criteria_distinct is {s["acceptance_criteria_distinct"]}, '
        f"outside the band recorded for Llama-3.3-70B (343). "
        f"See studies/hosted-model-specificity/FINDINGS.md before changing this."
    )


def test_the_committed_rows_still_match_the_extraction_output():
    """The frozen JSON must not drift from the run it was taken from.

    Committing derived rows makes the pinning tests runnable in CI, but it also
    creates a second copy that can silently go stale -- a frozen fiction that
    every other assertion then trusts. Where the xlsx exist (locally, after an
    extraction run) this checks the copy is still faithful. Where they do not
    (CI), it skips, because absence is the normal case there and not a fault.
    """
    import sys
    from extracted_corpus import extracted_corpus_by_bundle
    sys.path.insert(0, str(_ROOT / "dev" / "tools" / "scripts"))
    pytest.importorskip("openpyxl")
    from dump_corpus_rows import collect

    live = collect()
    if not live:
        pytest.skip("no extracted.xlsx present; nothing to compare against")
    frozen = extracted_corpus_by_bundle()
    assert set(live) == set(frozen), "bundle set drifted from extracted_rows.json"
    for k in sorted(live):
        assert live[k] == frozen[k], (
            f"{k} drifted; regenerate with dev/tools/scripts/dump_corpus_rows.py")

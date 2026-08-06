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
    """Pins 27.9%, the number the real bundles are compared against.

    If this moves, the claim in the Tier 1 corpus tests that real models fall
    short far more often is comparing against a stale baseline.
    """
    openpyxl = pytest.importorskip("openpyxl")
    from uofa_cli.excel_constants import NASA_ALL_FACTOR_NAMES, VV40_FACTOR_NAMES

    known = set(VV40_FACTOR_NAMES) | set(NASA_ALL_FACTOR_NAMES)
    rows = []
    for bd in sorted((_ROOT / "tests" / "fixtures" / "extract_corpus").glob("*/bundle_*")):
        x = bd / "extracted.xlsx"
        if not x.exists():
            continue
        ws = openpyxl.load_workbook(x, data_only=True)["Credibility Factors"]
        for r in range(1, ws.max_row + 1):
            if ws.cell(r, 1).value in known:
                rows.append({"factor_type": ws.cell(r, 1).value,
                             "required_level": ws.cell(r, 3).value,
                             "achieved_level": ws.cell(r, 4).value,
                             "acceptance_criteria": ws.cell(r, 5).value})

    s = score_per_factor_fields(rows, [])
    assert s["rows"] == 800
    assert s["required_level_present"] == 788
    assert s["rows_below_required"] == 223
    assert s["rows_below_required"] / s["rows_with_shortfall"] == pytest.approx(0.279, abs=0.005)
    # Not boilerplate: if this collapses, the column stopped being extracted and
    # started being echoed from the template.
    assert s["acceptance_criteria_distinct"] > 700

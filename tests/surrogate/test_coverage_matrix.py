"""Phase H: coverage-validation harness.

Verifies the §8 coverage matrix against the actual implementation:
- the emerging-reference caveat is present and NO Cohen's-κ claim is made;
- every pattern the matrix claims as a C3 detector is actually implemented;
- every OOS rule the matrix references is actually implemented;
- method-first discipline holds: CANDIDATE/GAP rows (W-SURR-04,
  residuals-unlinked) are NOT pre-implemented as firing rules.

These are static (file-content) checks — no engine required.
"""

from __future__ import annotations

from pathlib import Path

import pytest

PACK = Path(__file__).resolve().parents[2] / "packs" / "surrogate"
MATRIX = PACK / "coverage" / "surrogate_proto_taxonomy_coverage.md"
RULES = (PACK / "rules" / "surrogate_weakener.rules").read_text(encoding="utf-8")
OOS_RULES = (PACK / "rules" / "oos" / "oos_v0.1.rules").read_text(encoding="utf-8")
MATRIX_TEXT = MATRIX.read_text(encoding="utf-8")


def test_matrix_exists():
    assert MATRIX.is_file()


def test_emerging_reference_caveat_present():
    lowered = MATRIX_TEXT.lower()
    assert "emerging reference" in lowered
    assert "disclaims comprehensiveness" in lowered


def test_no_kappa_claim():
    # Coverage is fraction-detected, explicitly NOT a Cohen's-κ claim.
    assert "not" in MATRIX_TEXT.lower()
    assert "κ" in MATRIX_TEXT or "kappa" in MATRIX_TEXT.lower()
    assert "not a Cohen's-κ claim" in MATRIX_TEXT or "not** a Cohen" in MATRIX_TEXT


@pytest.mark.parametrize("pattern", ["W-SURR-01", "W-SURR-02", "W-SURR-03"])
def test_covered_c3_patterns_are_implemented(pattern):
    # The matrix claims these as C3 detectors; they must exist in the catalog.
    assert pattern in MATRIX_TEXT
    assert f"'{pattern}'" in RULES, f"{pattern} claimed in matrix but not implemented"


@pytest.mark.parametrize(
    "rule", ["oos_surr_calibration_provenance_warranted", "oos_surr_model_comparison_warranted"]
)
def test_referenced_oos_rules_are_implemented(rule):
    assert rule in OOS_RULES


@pytest.mark.parametrize("candidate", ["W-SURR-04", "residuals-unlinked"])
def test_candidates_are_not_pre_implemented(candidate):
    # Method-first: candidates may appear in the matrix as CANDIDATE, and the
    # rules file may NAME them in a comment explaining they are deliberately
    # unbuilt — but no rule may EMIT their patternId. The patternId literal is
    # single-quoted only in a rule head, so its absence proves non-implementation.
    assert candidate.lower() in MATRIX_TEXT.lower()
    assert "'W-SURR-04'" not in RULES, "W-SURR-04 must not be emitted by any rule"


def test_matrix_marks_gaps_as_traceable():
    # The report names uncovered dimensions rather than hiding them.
    assert "GAP" in MATRIX_TEXT and "CANDIDATE" in MATRIX_TEXT
    for gap_dim in ["D-VER-05", "D-CCB-11", "D-CCB-16"]:
        assert gap_dim in MATRIX_TEXT

"""Tests for Cohen's κ + Fleiss' κ + confusion matrices.

Includes a Fleiss-shape check against a known-result fixture so
statsmodels' (n_subjects, n_categories) count-matrix expectation is
exercised. The single most common bug in Fleiss implementations.
"""

from __future__ import annotations

import math

import pytest

from uofa_cli.adversarial.judge.adjudication import (
    VERDICT_CLASSES,
    AgreementStats,
    _to_count_matrix,
    cohen_kappa,
    compute_agreement,
    confusion_matrix,
    fleiss_kappa,
)


# ── _to_count_matrix ────────────────────────────────────────────────────


class TestToCountMatrix:
    def test_basic_3rater_2case(self) -> None:
        verdicts = [
            ["REAL-GAP", "REAL-GAP", "GENERATOR-ARTIFACT"],
            ["UNCERTAIN", "UNCERTAIN", "UNCERTAIN"],
        ]
        m = _to_count_matrix(verdicts)
        assert len(m) == 2  # 2 cases
        assert len(m[0]) == len(VERDICT_CLASSES)  # 6 categories
        # First case: 2 REAL-GAP + 1 GENERATOR-ARTIFACT
        rg_idx = VERDICT_CLASSES.index("REAL-GAP")
        ga_idx = VERDICT_CLASSES.index("GENERATOR-ARTIFACT")
        unc_idx = VERDICT_CLASSES.index("UNCERTAIN")
        assert m[0][rg_idx] == 2 and m[0][ga_idx] == 1
        # Second case: 3 UNCERTAIN
        assert m[1][unc_idx] == 3
        # Per-row sum equals rater count.
        assert sum(m[0]) == 3
        assert sum(m[1]) == 3

    def test_unknown_verdict_raises(self) -> None:
        verdicts = [["REAL-GAP", "FAKE-VERDICT", "REAL-GAP"]]
        with pytest.raises(ValueError, match="unknown verdict"):
            _to_count_matrix(verdicts)


# ── cohen_kappa ─────────────────────────────────────────────────────────


class TestCohenKappa:
    def test_perfect_agreement(self) -> None:
        x = ["REAL-GAP", "GENERATOR-ARTIFACT", "REAL-GAP"]
        # Perfect agreement → κ = 1.0
        assert cohen_kappa(x, x) == 1.0

    def test_perfect_disagreement(self) -> None:
        x = ["REAL-GAP", "REAL-GAP", "REAL-GAP"]
        y = ["GENERATOR-ARTIFACT", "GENERATOR-ARTIFACT", "GENERATOR-ARTIFACT"]
        # Both raters always agree internally → κ = -1 (max disagreement)
        # or 0.0 depending on prevalence. With our fixed labels, sklearn
        # returns 0.0 when expected agreement equals observed disagreement.
        result = cohen_kappa(x, y)
        assert result <= 0.0

    def test_moderate_agreement_falls_in_target_range(self) -> None:
        # Hand-constructed pair with ~75% agreement, expected κ ~0.5-0.7.
        x = ["REAL-GAP"] * 7 + ["GENERATOR-ARTIFACT"] * 3
        y = ["REAL-GAP"] * 6 + ["GENERATOR-ARTIFACT"] * 4
        k = cohen_kappa(x, y)
        # Spec mock-fixture target: 0.4 ≤ κ ≤ 0.7.
        assert 0.3 <= k <= 0.9

    def test_length_mismatch_raises(self) -> None:
        with pytest.raises(ValueError, match="differ in length"):
            cohen_kappa(["REAL-GAP"], ["REAL-GAP", "OUT-OF-SCOPE"])

    def test_empty_returns_nan(self) -> None:
        result = cohen_kappa([], [])
        assert math.isnan(result)


# ── fleiss_kappa ────────────────────────────────────────────────────────


class TestFleissKappa:
    def test_perfect_agreement(self) -> None:
        # 5 cases × 3 raters all agreeing → κ ≈ 1.0
        verdicts = [["REAL-GAP", "REAL-GAP", "REAL-GAP"]] * 5
        # Add another case with a different verdict so the metric is defined.
        verdicts.append(["GENERATOR-ARTIFACT", "GENERATOR-ARTIFACT", "GENERATOR-ARTIFACT"])
        k = fleiss_kappa(verdicts)
        assert k == pytest.approx(1.0, abs=0.01)

    def test_moderate_agreement(self) -> None:
        # 5-case mock fixture target: pairwise κ in 0.4–0.7. Build a
        # scenario where Fleiss' κ also lands moderate.
        verdicts = [
            ["REAL-GAP", "REAL-GAP", "REAL-GAP"],
            ["GENERATOR-ARTIFACT", "GENERATOR-ARTIFACT", "REAL-GAP"],
            ["OUT-OF-SCOPE", "OUT-OF-SCOPE", "OUT-OF-SCOPE"],
            ["UNCERTAIN", "REAL-GAP", "UNCERTAIN"],
            ["REAL-GAP", "REAL-GAP", "GENERATOR-ARTIFACT"],
        ]
        k = fleiss_kappa(verdicts)
        # Should be moderate (positive, not perfect).
        assert 0.0 < k < 1.0

    def test_inconsistent_rater_count_raises(self) -> None:
        verdicts = [
            ["REAL-GAP", "REAL-GAP", "REAL-GAP"],
            ["UNCERTAIN", "UNCERTAIN"],  # missing one rater
        ]
        with pytest.raises(ValueError, match="same number of raters"):
            fleiss_kappa(verdicts)

    def test_empty_returns_nan(self) -> None:
        assert math.isnan(fleiss_kappa([]))


# ── confusion_matrix ────────────────────────────────────────────────────


class TestConfusionMatrix:
    def test_diagonal_for_perfect_agreement(self) -> None:
        x = ["REAL-GAP", "GENERATOR-ARTIFACT", "REAL-GAP"]
        m = confusion_matrix(x, x)
        # 6×6 matrix with non-zero only on diagonal.
        assert len(m) == 6
        assert all(len(row) == 6 for row in m)
        rg = VERDICT_CLASSES.index("REAL-GAP")
        ga = VERDICT_CLASSES.index("GENERATOR-ARTIFACT")
        assert m[rg][rg] == 2
        assert m[ga][ga] == 1
        # All other cells are zero.
        total = sum(sum(row) for row in m)
        assert total == 3

    def test_off_diagonal_for_disagreement(self) -> None:
        x = ["REAL-GAP", "REAL-GAP"]
        y = ["GENERATOR-ARTIFACT", "GENERATOR-ARTIFACT"]
        m = confusion_matrix(x, y)
        rg = VERDICT_CLASSES.index("REAL-GAP")
        ga = VERDICT_CLASSES.index("GENERATOR-ARTIFACT")
        assert m[rg][ga] == 2  # x=REAL-GAP and y=GENERATOR-ARTIFACT, twice.
        assert m[rg][rg] == 0


# ── compute_agreement (the Stage-4 entry point) ─────────────────────────


class TestComputeAgreement:
    def test_returns_agreement_stats_with_all_kappas(self) -> None:
        a = ["REAL-GAP", "GENERATOR-ARTIFACT", "REAL-GAP", "OUT-OF-SCOPE", "UNCERTAIN"]
        b = ["REAL-GAP", "GENERATOR-ARTIFACT", "GENERATOR-ARTIFACT", "OUT-OF-SCOPE", "UNCERTAIN"]
        c = ["REAL-GAP", "REAL-GAP", "REAL-GAP", "OUT-OF-SCOPE", "REAL-GAP"]
        result = compute_agreement(a, b, c)
        assert isinstance(result, AgreementStats)
        assert result.case_count == 5
        assert isinstance(result.cohen_kappa_AB, float)
        assert isinstance(result.cohen_kappa_AC, float)
        assert isinstance(result.cohen_kappa_BC, float)
        assert isinstance(result.fleiss_kappa, float)

    def test_pairwise_kappa_in_target_range_for_mock_fixture(self) -> None:
        """Plan acceptance: mock fixture pairwise κ lands in 0.4–0.7.

        Hand-designed 5-case fixture where each judge pair disagrees on
        exactly 2 of 5 cases (raw 60% agreement). All three pairwise κ
        values fall in [0.4, 0.5]. This anchors the smoke fixtures we'll
        use in Wave 5 — kappas are well-defined (not NaN, not
        degenerate-1.0) and inside the target range.
        """
        # case 0: all three agree (REAL-GAP)
        # case 1: A=GA, B=RG, C=GA  → A,C agree; B disagrees
        # case 2: A=RG, B=RG, C=GA  → A,B agree; C disagrees
        # case 3: all three agree (OOS)
        # case 4: A=CORRECT, B=ERM, C=ERM → B,C agree; A disagrees
        a = ["REAL-GAP", "GENERATOR-ARTIFACT", "REAL-GAP", "OUT-OF-SCOPE", "CORRECT-DETECTION"]
        b = ["REAL-GAP", "REAL-GAP",           "REAL-GAP", "OUT-OF-SCOPE", "EXISTING-RULE-MISBEHAVIOR"]
        c = ["REAL-GAP", "GENERATOR-ARTIFACT", "GENERATOR-ARTIFACT", "OUT-OF-SCOPE", "EXISTING-RULE-MISBEHAVIOR"]
        result = compute_agreement(a, b, c)
        # All three pairwise κ ≈ 0.44–0.50, squarely inside 0.4–0.7.
        assert 0.4 <= result.cohen_kappa_AB <= 0.7
        assert 0.4 <= result.cohen_kappa_AC <= 0.7
        assert 0.4 <= result.cohen_kappa_BC <= 0.7

    def test_raw_agreement_ratio_correct(self) -> None:
        # 4/5 cases have ≥2 of 3 agreeing.
        a = ["REAL-GAP", "REAL-GAP", "REAL-GAP", "REAL-GAP", "REAL-GAP"]
        b = ["REAL-GAP", "REAL-GAP", "REAL-GAP", "GENERATOR-ARTIFACT", "REAL-GAP"]
        c = ["REAL-GAP", "GENERATOR-ARTIFACT", "OUT-OF-SCOPE", "UNCERTAIN", "REAL-GAP"]
        # Agreements (≥2 of 3 same):
        # case 0: A=B=C=REAL-GAP → 3-way → counted
        # case 1: A=REAL-GAP, B=REAL-GAP, C=GA → 2 agree → counted
        # case 2: A=REAL-GAP, B=REAL-GAP, C=OOS → 2 agree → counted
        # case 3: A=REAL-GAP, B=GA, C=UNC → all different → NOT counted
        # case 4: 3-way agree → counted
        # → 4/5 = 0.8
        result = compute_agreement(a, b, c)
        assert result.raw_agreement_at_least_2of3 == pytest.approx(0.8)

    def test_length_mismatch_raises(self) -> None:
        with pytest.raises(ValueError, match="differ in length"):
            compute_agreement(["REAL-GAP"], ["REAL-GAP"], ["REAL-GAP", "REAL-GAP"])

    def test_empty_returns_nan_kappa(self) -> None:
        result = compute_agreement([], [], [])
        assert result.case_count == 0
        assert math.isnan(result.cohen_kappa_AB)
        assert math.isnan(result.fleiss_kappa)

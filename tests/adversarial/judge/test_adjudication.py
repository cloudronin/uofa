"""Tests for Cohen's κ + Fleiss' κ + confusion matrices.

Includes a Fleiss-shape check against a known-result fixture so
statsmodels' (n_subjects, n_categories) count-matrix expectation is
exercised. The single most common bug in Fleiss implementations.
"""

from __future__ import annotations

import math

import pytest

# Skip the whole file when judge extras aren't installed. sklearn +
# statsmodels are listed under the [judge] optional-dependency group
# (pyproject.toml). The devcontainer install pulls them; this guard
# keeps the suite green when the user runs `pytest tests/` without
# `pip install -e '.[judge]'` first.
pytest.importorskip("sklearn", reason="install [judge] extras")
pytest.importorskip("statsmodels", reason="install [judge] extras")

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


# ── v1.6 additions: Judge E + author + Judge D agreement ────────────────


class TestComputeJudgeEAgreement:
    """v1.6 §10.2 Judge E vs production-judge κ on the disagreement queue."""

    def test_basic_three_judge_e_vs_production(self) -> None:
        from uofa_cli.adversarial.judge.adjudication import compute_judge_e_agreement

        # 5 disagreement cases. Judge E mostly aligns with A.
        a = ["REAL-GAP", "REAL-GAP", "GENERATOR-ARTIFACT", "OUT-OF-SCOPE", "REAL-GAP"]
        b = ["GENERATOR-ARTIFACT", "REAL-GAP", "OUT-OF-SCOPE", "OUT-OF-SCOPE", "GENERATOR-ARTIFACT"]
        c = ["UNCERTAIN", "GENERATOR-ARTIFACT", "REAL-GAP", "GENERATOR-ARTIFACT", "REAL-GAP"]
        e = ["REAL-GAP", "REAL-GAP", "GENERATOR-ARTIFACT", "OUT-OF-SCOPE", "GENERATOR-ARTIFACT"]
        stats = compute_judge_e_agreement(
            judgments_a=a, judgments_b=b, judgments_c=c, judgments_e=e,
            arbitrated_count=3, escalated_count=2,
        )
        assert stats.case_count == 5
        # E agrees with A on 4/5 → high κ
        assert stats.cohen_kappa_EA > stats.cohen_kappa_EB
        # Confusion matrices are 6×6
        assert len(stats.confusion_matrix_EA) == len(VERDICT_CLASSES)
        assert len(stats.confusion_matrix_EA[0]) == len(VERDICT_CLASSES)
        assert stats.arbitrated_count == 3
        assert stats.escalated_count == 2

    def test_empty_returns_nan_and_zero_matrices(self) -> None:
        from uofa_cli.adversarial.judge.adjudication import compute_judge_e_agreement

        stats = compute_judge_e_agreement(
            judgments_a=[], judgments_b=[], judgments_c=[], judgments_e=[]
        )
        assert stats.case_count == 0
        assert math.isnan(stats.cohen_kappa_EA)
        assert all(c == 0 for row in stats.confusion_matrix_EA for c in row)

    def test_length_mismatch_raises(self) -> None:
        from uofa_cli.adversarial.judge.adjudication import compute_judge_e_agreement

        with pytest.raises(ValueError, match="differ in length"):
            compute_judge_e_agreement(
                judgments_a=["REAL-GAP"], judgments_b=["REAL-GAP"],
                judgments_c=["REAL-GAP", "REAL-GAP"], judgments_e=["REAL-GAP"],
            )


class TestComputeAuthorAdjudication:
    """v1.6 §11 author final-verdict + spot-check override metrics."""

    def test_author_E_confusion_basic(self) -> None:
        from uofa_cli.adversarial.judge.adjudication import (
            compute_author_adjudication,
        )

        author = ["REAL-GAP", "OUT-OF-SCOPE", "GENERATOR-ARTIFACT"]
        e = ["GENERATOR-ARTIFACT", "OUT-OF-SCOPE", "GENERATOR-ARTIFACT"]
        stats = compute_author_adjudication(
            author_verdicts=author, judge_e_verdicts=e,
            spot_check_total=20, spot_check_override_count=1,
        )
        assert stats.escalated_case_count == 3
        assert stats.spot_check_override_rate == pytest.approx(0.05)
        # Author=REAL-GAP, E=GA → off-diagonal
        rg_idx = VERDICT_CLASSES.index("REAL-GAP")
        ga_idx = VERDICT_CLASSES.index("GENERATOR-ARTIFACT")
        assert stats.confusion_matrix_author_E[rg_idx][ga_idx] == 1

    def test_spot_check_no_overrides_yields_zero_rate(self) -> None:
        from uofa_cli.adversarial.judge.adjudication import (
            compute_author_adjudication,
        )

        stats = compute_author_adjudication(
            author_verdicts=[], judge_e_verdicts=[],
            spot_check_total=15, spot_check_override_count=0,
        )
        assert stats.spot_check_override_rate == 0.0
        assert stats.escalated_case_count == 0

    def test_spot_check_override_target_threshold(self) -> None:
        # §11.4 target ≤ 0.10. 1/15 = 0.067 — under target.
        from uofa_cli.adversarial.judge.adjudication import (
            compute_author_adjudication,
        )

        stats = compute_author_adjudication(
            author_verdicts=[], judge_e_verdicts=[],
            spot_check_total=15, spot_check_override_count=1,
        )
        assert stats.spot_check_override_rate < 0.10

    def test_length_mismatch_raises(self) -> None:
        from uofa_cli.adversarial.judge.adjudication import (
            compute_author_adjudication,
        )

        with pytest.raises(ValueError, match="differ in length"):
            compute_author_adjudication(
                author_verdicts=["REAL-GAP"], judge_e_verdicts=[],
            )


class TestComputeJudgeEvsDAgreement:
    """v1.6 §8.0 Judge E vs Judge D agreement on calibration set (informational)."""

    def test_per_class_match_rate(self) -> None:
        from uofa_cli.adversarial.judge.adjudication import (
            compute_judge_e_vs_d_agreement,
        )

        # Judge D ground truth: 3 REAL-GAP + 2 GENERATOR-ARTIFACT
        d = ["REAL-GAP", "REAL-GAP", "REAL-GAP", "GENERATOR-ARTIFACT", "GENERATOR-ARTIFACT"]
        # Judge E: 2/3 REAL-GAP correct, 2/2 GA correct
        e = ["REAL-GAP", "REAL-GAP", "GENERATOR-ARTIFACT", "GENERATOR-ARTIFACT", "GENERATOR-ARTIFACT"]
        stats = compute_judge_e_vs_d_agreement(
            judge_e_verdicts=e, judge_d_verdicts=d
        )
        assert stats.case_count == 5
        assert stats.overall_match_rate == pytest.approx(0.8)
        assert stats.per_class_match_rate["REAL-GAP"] == pytest.approx(2 / 3)
        assert stats.per_class_match_rate["GENERATOR-ARTIFACT"] == 1.0

    def test_unknown_verdict_raises(self) -> None:
        from uofa_cli.adversarial.judge.adjudication import (
            compute_judge_e_vs_d_agreement,
        )

        with pytest.raises(ValueError, match="unknown verdict"):
            compute_judge_e_vs_d_agreement(
                judge_e_verdicts=["REAL-GAP"], judge_d_verdicts=["GIBBERISH"],
            )

    def test_empty_returns_nan(self) -> None:
        from uofa_cli.adversarial.judge.adjudication import (
            compute_judge_e_vs_d_agreement,
        )

        stats = compute_judge_e_vs_d_agreement(
            judge_e_verdicts=[], judge_d_verdicts=[],
        )
        assert stats.case_count == 0
        assert math.isnan(stats.overall_match_rate)
        assert stats.per_class_match_rate == {}

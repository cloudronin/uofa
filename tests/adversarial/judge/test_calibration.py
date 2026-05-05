"""Tests for Stage 1 calibration runner (spec v1.6 §8.1–8.4, §15.1 #5/6/7)."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from uofa_cli.adversarial.judge.calibration import (
    DEFAULT_PROMPT_VERSION,
    GATE_PAIRWISE_KAPPA,
    GATE_PER_CLASS_ACCURACY,
    GATE_PER_JUDGE_ACCURACY,
    CalibrationRunResults,
    JudgeCalibrationResult,
    _evaluate_hard_gates,
    _gate_pairwise_kappa,
    _judge_e_vs_d_agreement,
    _validate_prompt_version,
    render_results_json,
    render_summary_md,
)
from uofa_cli.adversarial.judge.providers.base import Judgment


def _make_judgment(case_id: str, verdict: str, *, prompt_version: str = "v1.1.0") -> Judgment:
    return Judgment(
        case_id=case_id, verdict=verdict, confidence=0.85,
        reasoning_steps={
            "source_taxonomy_identified": "x" * 11,
            "target_rule_identified": "x", "rule_firings_inspected": "x",
            "instantiation_check": "x", "verdict_commitment": verdict,
        },
        reasoning="x" * 60,
        section_6_7_candidate=None, alternative_rule_analysis=None,
        prompt_template_version=prompt_version,
        judge_model="mock", judge_thinking_enabled=False,
        judge_model_params={"temperature": 0.0, "seed": 42},
        generator_provenance={"generator_model": "mock", "temperature": None, "seed": None},
        evidence_gap=None,
    )


def _make_judge_result(
    position: str, *, verdicts_by_case: list[tuple[str, str]],
    ground_truth: list[tuple[str, str]],
) -> JudgeCalibrationResult:
    """Helper: build a JudgeCalibrationResult from (case_id, verdict) lists."""
    judgments = [_make_judgment(cid, v) for cid, v in verdicts_by_case]
    gt_map = dict(ground_truth)
    correct = sum(1 for j in judgments if gt_map.get(j.case_id) == j.verdict)
    per_class_correct: dict[str, int] = {}
    per_class_total: dict[str, int] = {}
    from uofa_cli.adversarial.judge.adjudication import VERDICT_CLASSES
    for cls in VERDICT_CLASSES:
        per_class_correct[cls] = 0
        per_class_total[cls] = 0
    for cid, gt in ground_truth:
        per_class_total[gt] = per_class_total.get(gt, 0) + 1
    for j in judgments:
        gt = gt_map.get(j.case_id)
        if gt and j.verdict == gt:
            per_class_correct[gt] = per_class_correct.get(gt, 0) + 1
    per_class_accuracy = {
        cls: (per_class_correct[cls] / per_class_total[cls]) if per_class_total[cls] else 0.0
        for cls in VERDICT_CLASSES
    }
    return JudgeCalibrationResult(
        position=position, provider_token=f"mock_{position.lower()}",
        judge_model=f"mock-{position}",
        case_count=len(judgments), correct_count=correct,
        overall_accuracy=correct / len(judgments) if judgments else 0.0,
        per_class_correct=per_class_correct,
        per_class_total=per_class_total,
        per_class_accuracy=per_class_accuracy,
        judgments=judgments,
        verdicts_by_index=[j.verdict for j in judgments],
    )


# ── pairwise κ ──────────────────────────────────────────────────────────


class TestPairwiseKappa:
    def test_perfect_agreement_returns_kappa_one(self) -> None:
        # All three judges produce ground-truth-matching verdicts on
        # 30 cases stratified across 6 classes (5 per class). Multi-
        # class is required for well-defined κ — single-class fixtures
        # divide by zero in sklearn's cohen_kappa.
        from uofa_cli.adversarial.judge.adjudication import VERDICT_CLASSES
        ids = [f"cal-{i:03}" for i in range(30)]
        verdicts = []
        for i, cls in enumerate(VERDICT_CLASSES):
            for j in range(5):
                verdicts.append((ids[i * 5 + j], cls))
        gt = list(verdicts)
        results = {
            pos: _make_judge_result(pos, verdicts_by_case=verdicts, ground_truth=gt)
            for pos in ("A", "B", "C")
        }
        kappa, fleiss = _gate_pairwise_kappa(results)
        assert kappa["AB"] == 1.0 and kappa["AC"] == 1.0 and kappa["BC"] == 1.0
        assert fleiss == 1.0

    def test_some_disagreement_yields_intermediate_kappa(self) -> None:
        # Two judges agree on the multi-class ground truth; one disagrees
        # on half by flipping the second half to GENERATOR-ARTIFACT.
        from uofa_cli.adversarial.judge.adjudication import VERDICT_CLASSES
        ids = [f"cal-{i:03}" for i in range(30)]
        gt = []
        for i, cls in enumerate(VERDICT_CLASSES):
            for j in range(5):
                gt.append((ids[i * 5 + j], cls))
        a_verdicts = list(gt)
        b_verdicts = list(gt)
        c_verdicts = [
            (c, v if i < 15 else "GENERATOR-ARTIFACT")
            for i, (c, v) in enumerate(gt)
        ]
        results = {
            "A": _make_judge_result("A", verdicts_by_case=a_verdicts, ground_truth=gt),
            "B": _make_judge_result("B", verdicts_by_case=b_verdicts, ground_truth=gt),
            "C": _make_judge_result("C", verdicts_by_case=c_verdicts, ground_truth=gt),
        }
        kappa, _ = _gate_pairwise_kappa(results)
        assert kappa["AB"] == 1.0
        assert kappa["AC"] < 1.0  # has disagreement
        assert kappa["BC"] < 1.0


# ── hard-gate evaluation ────────────────────────────────────────────────


class TestEvaluateHardGates:
    def test_all_pass_when_thresholds_met(self) -> None:
        ids = [f"cal-{i:03}" for i in range(30)]
        # 5 cases per class for 6 classes.
        from uofa_cli.adversarial.judge.adjudication import VERDICT_CLASSES
        gt = []
        for i, cls in enumerate(VERDICT_CLASSES):
            for j in range(5):
                gt.append((ids[i * 5 + j], cls))
        # All 3 judges produce ground-truth verdicts → 100% accuracy.
        results = {
            pos: _make_judge_result(pos, verdicts_by_case=gt, ground_truth=gt)
            for pos in ("A", "B", "C")
        }
        kappa, _ = _gate_pairwise_kappa(results)
        per_judge, pair_pass, per_class, all_pass = _evaluate_hard_gates(results, kappa)
        assert all(per_judge.values())
        assert all(pair_pass.values())
        assert all_pass

    def test_one_judge_below_accuracy_fails(self) -> None:
        # Same 30-case ground truth.
        ids = [f"cal-{i:03}" for i in range(30)]
        from uofa_cli.adversarial.judge.adjudication import VERDICT_CLASSES
        gt = []
        for i, cls in enumerate(VERDICT_CLASSES):
            for j in range(5):
                gt.append((ids[i * 5 + j], cls))
        # B gets only 50% right.
        gt_map = dict(gt)
        a_verdicts = list(gt)
        b_verdicts = [
            (c, gt_map[c] if i < 15 else "UNCERTAIN")
            for i, (c, _) in enumerate(gt)
        ]
        c_verdicts = list(gt)
        results = {
            "A": _make_judge_result("A", verdicts_by_case=a_verdicts, ground_truth=gt),
            "B": _make_judge_result("B", verdicts_by_case=b_verdicts, ground_truth=gt),
            "C": _make_judge_result("C", verdicts_by_case=c_verdicts, ground_truth=gt),
        }
        kappa, _ = _gate_pairwise_kappa(results)
        per_judge, _pair, _pc, all_pass = _evaluate_hard_gates(results, kappa)
        assert per_judge["B"] is False
        assert per_judge["A"] is True
        assert all_pass is False


# ── prompt-version drift detection ──────────────────────────────────────


class TestValidatePromptVersion:
    def test_clean_when_all_match(self) -> None:
        results = {
            "A": _make_judge_result(
                "A",
                verdicts_by_case=[("cal-001", "REAL-GAP")],
                ground_truth=[("cal-001", "REAL-GAP")],
            ),
        }
        assert _validate_prompt_version(results, expected="v1.1.0") == []

    def test_flags_drift(self) -> None:
        # Pollute one judgment with a wrong version stamp.
        results = {
            "A": _make_judge_result(
                "A",
                verdicts_by_case=[("cal-001", "REAL-GAP")],
                ground_truth=[("cal-001", "REAL-GAP")],
            ),
        }
        results["A"].judgments[0] = _make_judgment(
            "cal-001", "REAL-GAP", prompt_version="v0.9.0",
        )
        bad = _validate_prompt_version(results, expected="v1.1.0")
        assert len(bad) == 1 and "v0.9.0" in bad[0] and "cal-001" in bad[0]


# ── markdown report ─────────────────────────────────────────────────────


class TestRenderSummaryMd:
    def test_contains_hard_gate_table_and_disclosure(self) -> None:
        ids = [f"cal-{i:03}" for i in range(30)]
        from uofa_cli.adversarial.judge.adjudication import VERDICT_CLASSES
        gt = []
        for i, cls in enumerate(VERDICT_CLASSES):
            for j in range(5):
                gt.append((ids[i * 5 + j], cls))
        results = {
            pos: _make_judge_result(pos, verdicts_by_case=gt, ground_truth=gt)
            for pos in ("A", "B", "C")
        }
        kappa, fleiss = _gate_pairwise_kappa(results)
        per_judge, pair_pass, per_class, all_pass = _evaluate_hard_gates(results, kappa)
        run = CalibrationRunResults(
            run_timestamp_utc="2026-05-05T12:00:00Z",
            prompt_template_version="v1.1.0",
            calibration_set_path="specs/calibration/calibration_set_v1.jsonl",
            case_count=30,
            judge_results=results,
            pairwise_kappa=kappa,
            fleiss_kappa=fleiss,
            judge_e_vs_d_match_rate=None,
            gate_per_judge_accuracy=per_judge,
            gate_pairwise_kappa=pair_pass,
            gate_per_class_accuracy=per_class,
            all_gates_pass=all_pass,
        )
        md = render_summary_md(run)
        # Hard-gate verdicts visible.
        assert "ALL HARD GATES PASS" in md
        # Methodology disclosure present (Gemini substitution).
        assert "gemini-2.5-pro" in md
        assert "gemini-3.1-pro" in md
        # Prompt version visible.
        assert "v1.1.0" in md
        # All 6 classes appear.
        for cls in VERDICT_CLASSES:
            assert cls in md
        # Pairwise + Fleiss table present.
        assert "Cohen" in md or "Pairwise" in md


# ── results JSON shape ──────────────────────────────────────────────────


class TestRenderResultsJson:
    def test_contains_provenance_fields(self) -> None:
        ids = [f"cal-{i:03}" for i in range(30)]
        from uofa_cli.adversarial.judge.adjudication import VERDICT_CLASSES
        gt = []
        for i, cls in enumerate(VERDICT_CLASSES):
            for j in range(5):
                gt.append((ids[i * 5 + j], cls))
        results = {
            pos: _make_judge_result(pos, verdicts_by_case=gt, ground_truth=gt)
            for pos in ("A", "B", "C")
        }
        kappa, fleiss = _gate_pairwise_kappa(results)
        per_judge, pair_pass, per_class, all_pass = _evaluate_hard_gates(results, kappa)
        run = CalibrationRunResults(
            run_timestamp_utc="2026-05-05T12:00:00Z",
            prompt_template_version="v1.1.0",
            calibration_set_path="specs/calibration/calibration_set_v1.jsonl",
            case_count=30,
            judge_results=results,
            pairwise_kappa=kappa,
            fleiss_kappa=fleiss,
            judge_e_vs_d_match_rate=None,
            gate_per_judge_accuracy=per_judge,
            gate_pairwise_kappa=pair_pass,
            gate_per_class_accuracy=per_class,
            all_gates_pass=all_pass,
        )
        d = render_results_json(run)
        assert d["prompt_template_version"] == "v1.1.0"
        assert d["run_timestamp_utc"] == "2026-05-05T12:00:00Z"
        assert d["case_count"] == 30
        assert "per_judge" in d and set(d["per_judge"].keys()) == {"A", "B", "C"}
        assert "hard_gates" in d
        assert d["hard_gates"]["all_pass"] is True


# ── parse_calibrate_judges ──────────────────────────────────────────────


class TestParseCalibrateJudges:
    def test_accepts_production_trio(self) -> None:
        from uofa_cli.adversarial.judge.cli_args import parse_calibrate_judges
        cfg = parse_calibrate_judges("openai,gemini,hf-llama")
        assert cfg.positions == ("A", "B", "C")
        assert cfg.tokens == ("openai", "gemini", "hf-llama")

    def test_accepts_trio_plus_judge_e(self) -> None:
        from uofa_cli.adversarial.judge.cli_args import parse_calibrate_judges
        cfg = parse_calibrate_judges("openai,gemini,hf-llama,mistral")
        assert cfg.positions == ("A", "B", "C", "E")

    def test_rejects_judge_d(self) -> None:
        from uofa_cli.adversarial.judge.cli_args import parse_calibrate_judges
        with pytest.raises(ValueError, match="anchor"):
            parse_calibrate_judges("openai,gemini,hf-llama,anthropic")

    def test_rejects_missing_production_position(self) -> None:
        from uofa_cli.adversarial.judge.cli_args import parse_calibrate_judges
        with pytest.raises(ValueError, match="A/B/C"):
            parse_calibrate_judges("openai,gemini,mistral")  # missing C

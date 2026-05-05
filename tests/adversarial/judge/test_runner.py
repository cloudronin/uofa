"""Tests for the runner.py CLI dispatch layer."""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

import pytest

from uofa_cli.adversarial.judge.runner import (
    _MockProvider,
    _build_providers,
    _judgment_to_dict,
    _load_judgments,
    _reset_mock_ledger,
    _write_confusion,
    run_adjudicate,
    run_bundle,
    run_judge,
    run_triage,
)
from uofa_cli.adversarial.judge.cli_args import parse_judges
from uofa_cli.adversarial.judge.providers.base import Judgment


def _args(**kwargs) -> argparse.Namespace:
    """Build an argparse.Namespace from kwargs for run_* entry points."""
    ns = argparse.Namespace()
    for k, v in kwargs.items():
        setattr(ns, k, v)
    return ns


# ── _MockProvider ──────────────────────────────────────────────────────


class TestMockProvider:
    def test_unknown_token_raises(self) -> None:
        with pytest.raises(ValueError, match="unknown mock token"):
            _MockProvider("mock_z")

    def test_judge_returns_canned_verdict(self) -> None:
        _reset_mock_ledger()
        provider = _MockProvider("mock_a")
        case = {"case_id": "c0"}
        judgment = asyncio.run(provider.judge(case))
        # First mock_a verdict is REAL-GAP per _MOCK_VERDICTS_A.
        assert judgment.verdict == "REAL-GAP"
        assert judgment.case_id == "c0"

    def test_three_providers_agree_on_first_case(self) -> None:
        # First case in the mock arrays: A, B, C all REAL-GAP.
        _reset_mock_ledger()
        a = _MockProvider("mock_a")
        b = _MockProvider("mock_b")
        c = _MockProvider("mock_c")
        case = {"case_id": "c0"}
        ja = asyncio.run(a.judge(case))
        jb = asyncio.run(b.judge(case))
        jc = asyncio.run(c.judge(case))
        assert ja.verdict == jb.verdict == jc.verdict == "REAL-GAP"

    def test_calibrate_empty_set(self) -> None:
        provider = _MockProvider("mock_a")
        result = asyncio.run(provider.calibrate([]))
        assert result.case_count == 0
        assert result.overall_accuracy == 0.0


# ── _build_providers ────────────────────────────────────────────────────


class TestBuildProviders:
    def test_all_mock(self) -> None:
        cfg = parse_judges("mock_a,mock_b,mock_c")
        providers = _build_providers(cfg)
        assert len(providers) == 3
        assert all(isinstance(p, _MockProvider) for p in providers)

    def test_unknown_token_raises(self) -> None:
        # Construct a JudgesConfig directly with an unsupported token —
        # parse_judges normally rejects it, but we want runtime safety.
        cfg = parse_judges("mock_a,mock_b,mock_c")
        # Replace one token with an invalid one.
        from uofa_cli.adversarial.judge.cli_args import JudgesConfig
        bad = JudgesConfig(tokens=("nope", "mock_b", "mock_c"), positions=("A","B","C"), is_mock=True)
        with pytest.raises(ValueError, match="unknown judge token"):
            _build_providers(bad)


# ── run_judge ──────────────────────────────────────────────────────────


class TestRunJudge:
    def _bundle_path(self, tmp_path: Path) -> Path:
        from tests.adversarial.judge.fixtures.mock_bundle import write_mock_bundle
        return write_mock_bundle(tmp_path / "b.tgz")

    def test_smoke_calibration_only(self, tmp_path: Path) -> None:
        bundle = self._bundle_path(tmp_path)
        out = tmp_path / "judge_out"
        args = _args(
            in_bundle=bundle, out=out,
            judges="mock_a,mock_b,mock_c",
            parallel=1,
            calibration_only=True,
            allow_same_family_judge=False,
        )
        rc = run_judge(args)
        assert rc == 0
        assert (out / "judgments_A.jsonl").exists()
        assert (out / "judgments_B.jsonl").exists()
        assert (out / "judgments_C.jsonl").exists()
        assert (out / "calibration_results_summary.json").exists()
        # Per-judge calibration files written.
        assert (out / "calibration_results_mock_a.json").exists()

    def test_summary_kappas_in_target_range(self, tmp_path: Path) -> None:
        bundle = self._bundle_path(tmp_path)
        out = tmp_path / "judge_out"
        args = _args(
            in_bundle=bundle, out=out, judges="mock_a,mock_b,mock_c",
            parallel=1, calibration_only=True, allow_same_family_judge=False,
        )
        run_judge(args)
        summary = json.loads((out / "calibration_results_summary.json").read_text())
        # All three pairwise κ should be in 0.4–0.7 (mock fixtures designed for this).
        for k in ("pairwise_kappa_AB", "pairwise_kappa_AC", "pairwise_kappa_BC"):
            assert summary[k] is not None
            assert 0.3 <= summary[k] <= 0.75

    def test_invalid_judges_returns_2(self, tmp_path: Path) -> None:
        bundle = self._bundle_path(tmp_path)
        args = _args(
            in_bundle=bundle, out=tmp_path / "out", judges="not-a-judge",
            parallel=1, calibration_only=True, allow_same_family_judge=False,
        )
        assert run_judge(args) == 2

    def test_missing_bundle_returns_2(self, tmp_path: Path) -> None:
        args = _args(
            in_bundle=tmp_path / "doesnt-exist.tgz", out=tmp_path / "out",
            judges="mock_a,mock_b,mock_c",
            parallel=1, calibration_only=True, allow_same_family_judge=False,
        )
        assert run_judge(args) == 2

    def test_parallel_with_no_hf_llama_returns_2(self, tmp_path: Path) -> None:
        bundle = self._bundle_path(tmp_path)
        args = _args(
            in_bundle=bundle, out=tmp_path / "out", judges="mock_a,mock_b,mock_c",
            parallel=8, calibration_only=True, allow_same_family_judge=False,
        )
        assert run_judge(args) == 2


# ── run_triage ─────────────────────────────────────────────────────────


def _write_judgments_jsonl(path: Path, judgments: list[Judgment]) -> None:
    with path.open("w") as f:
        for j in judgments:
            f.write(json.dumps(_judgment_to_dict(j)) + "\n")


def _make_judgment(case_id: str, verdict: str, confidence: float = 0.85) -> Judgment:
    return Judgment(
        case_id=case_id,
        verdict=verdict,
        confidence=confidence,
        reasoning_steps={
            "source_taxonomy_identified": "x" * 10,
            "target_rule_identified": "x" * 5,
            "rule_firings_inspected": "x" * 10,
            "instantiation_check": "x" * 20,
            "verdict_commitment": verdict,
        },
        reasoning="x" * 50,
        section_6_7_candidate=None,
        alternative_rule_analysis=None,
        prompt_template_version="v0.0.0-stub",
        judge_model="mock",
        judge_thinking_enabled=False,
        judge_model_params={"temperature": 0.0, "seed": 42},
        generator_provenance={"generator_model": "mock", "temperature": None, "seed": None},
    )


class TestRunTriage:
    def test_writes_queue_and_summary(self, tmp_path: Path) -> None:
        a = [_make_judgment("c1", "REAL-GAP"), _make_judgment("c2", "REAL-GAP")]
        b = [_make_judgment("c1", "REAL-GAP"), _make_judgment("c2", "GENERATOR-ARTIFACT")]
        c = [_make_judgment("c1", "REAL-GAP"), _make_judgment("c2", "OUT-OF-SCOPE")]

        for name, jl in (("a", a), ("b", b), ("c", c)):
            _write_judgments_jsonl(tmp_path / f"j_{name}.jsonl", jl)

        args = _args(
            judgments_a=tmp_path / "j_a.jsonl",
            judgments_b=tmp_path / "j_b.jsonl",
            judgments_c=tmp_path / "j_c.jsonl",
            out=tmp_path / "triage_out",
            confidence_floor=0.6,
        )
        rc = run_triage(args)
        assert rc == 0
        summary = json.loads((tmp_path / "triage_out" / "triage_summary.json").read_text())
        assert summary["case_count"] == 2
        assert summary["bucket_counts"]["CONVERGENT"] == 1
        assert summary["bucket_counts"]["DIVERGENT"] == 1


# ── run_adjudicate ─────────────────────────────────────────────────────


class TestRunAdjudicate:
    def test_writes_agreement_stats_and_confusion_matrices(self, tmp_path: Path) -> None:
        a = [_make_judgment(f"c{i}", "REAL-GAP" if i < 3 else "GENERATOR-ARTIFACT") for i in range(5)]
        b = [_make_judgment(f"c{i}", "REAL-GAP" if i < 4 else "GENERATOR-ARTIFACT") for i in range(5)]
        c = [_make_judgment(f"c{i}", "REAL-GAP" if i < 2 else "GENERATOR-ARTIFACT") for i in range(5)]

        for name, jl in (("a", a), ("b", b), ("c", c)):
            _write_judgments_jsonl(tmp_path / f"j_{name}.jsonl", jl)

        args = _args(
            judgments_a=tmp_path / "j_a.jsonl",
            judgments_b=tmp_path / "j_b.jsonl",
            judgments_c=tmp_path / "j_c.jsonl",
            out=tmp_path / "adj_out",
            adjudications=None,
        )
        rc = run_adjudicate(args)
        assert rc == 0
        out = tmp_path / "adj_out"
        stats = json.loads((out / "agreement_stats.json").read_text())
        assert stats["case_count"] == 5
        assert {"cohen_kappa_AB", "cohen_kappa_AC", "cohen_kappa_BC", "fleiss_kappa"} <= set(stats)
        # Confusion matrices written for each pair.
        assert (out / "confusion_matrix_AB.csv").exists()
        assert (out / "confusion_matrix_AC.csv").exists()
        assert (out / "confusion_matrix_BC.csv").exists()

    def test_no_aligned_trios_returns_1(self, tmp_path: Path) -> None:
        # Three lists with no overlapping case_ids.
        a = [_make_judgment("c1", "REAL-GAP")]
        b = [_make_judgment("c2", "REAL-GAP")]
        c = [_make_judgment("c3", "REAL-GAP")]
        for name, jl in (("a", a), ("b", b), ("c", c)):
            _write_judgments_jsonl(tmp_path / f"j_{name}.jsonl", jl)
        args = _args(
            judgments_a=tmp_path / "j_a.jsonl",
            judgments_b=tmp_path / "j_b.jsonl",
            judgments_c=tmp_path / "j_c.jsonl",
            out=tmp_path / "adj_out",
            adjudications=None,
        )
        assert run_adjudicate(args) == 1


# ── run_bundle ─────────────────────────────────────────────────────────


class TestRunBundle:
    def test_missing_batch_dir_returns_2(self, tmp_path: Path) -> None:
        args = _args(
            batch_dir=tmp_path / "nope",
            outcomes_csv=None,
            out=tmp_path / "out.tgz",
        )
        assert run_bundle(args) == 2

    def test_missing_outcomes_csv_returns_2(self, tmp_path: Path) -> None:
        # batch_dir exists but no outcomes.csv.
        (tmp_path / "batch").mkdir()
        args = _args(
            batch_dir=tmp_path / "batch",
            outcomes_csv=None,
            out=tmp_path / "out.tgz",
        )
        assert run_bundle(args) == 2


# ── _write_confusion ────────────────────────────────────────────────────


class TestWriteConfusion:
    def test_writes_6x6_csv_with_headers(self, tmp_path: Path) -> None:
        path = tmp_path / "cm.csv"
        _write_confusion(path, ["REAL-GAP", "REAL-GAP"], ["REAL-GAP", "GENERATOR-ARTIFACT"])
        lines = path.read_text().strip().splitlines()
        # 1 header + 6 rows = 7 lines
        assert len(lines) == 7
        # First col of each data row is the label.
        labels = [l.split(",")[0] for l in lines[1:]]
        assert labels == [
            "CORRECT-DETECTION", "REAL-GAP", "GENERATOR-ARTIFACT",
            "EXISTING-RULE-MISBEHAVIOR", "OUT-OF-SCOPE", "UNCERTAIN",
        ]


# ── _load_judgments ────────────────────────────────────────────────────


class TestLoadJudgments:
    def test_round_trip(self, tmp_path: Path) -> None:
        original = [_make_judgment("c1", "REAL-GAP")]
        path = tmp_path / "j.jsonl"
        _write_judgments_jsonl(path, original)
        loaded = _load_judgments(path)
        assert len(loaded) == 1
        assert loaded[0].case_id == "c1"
        assert loaded[0].verdict == "REAL-GAP"

    def test_missing_file_raises(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            _load_judgments(tmp_path / "nope.jsonl")

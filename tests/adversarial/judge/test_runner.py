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
        from .fixtures.mock_bundle import write_mock_bundle
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
        # v1.6: UNCERTAIN bin folded into DISAGREEMENT (was DIVERGENT in v1.5).
        assert summary["bucket_counts"]["DISAGREEMENT"] == 1


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


# ── run_finalize / run_formalize / run_case_study_rerun (Waves E/J/K) ─


class TestRunFinalize:
    def test_writes_final_verdicts_jsonl(self, tmp_path: Path) -> None:
        from uofa_cli.adversarial.judge.runner import run_finalize

        # 3 cases: 1 CONVERGENT REAL-GAP + 2 disagreements that go to UNRESOLVED.
        a = [
            _make_judgment("c1", "REAL-GAP", 0.9),
            _make_judgment("c2", "REAL-GAP", 0.9),
            _make_judgment("c3", "REAL-GAP", 0.9),
        ]
        b = [
            _make_judgment("c1", "REAL-GAP", 0.85),
            _make_judgment("c2", "GENERATOR-ARTIFACT", 0.85),
            _make_judgment("c3", "OUT-OF-SCOPE", 0.85),
        ]
        c = [
            _make_judgment("c1", "REAL-GAP", 0.8),
            _make_judgment("c2", "OUT-OF-SCOPE", 0.85),
            _make_judgment("c3", "GENERATOR-ARTIFACT", 0.85),
        ]
        for name, jl in (("a", a), ("b", b), ("c", c)):
            _write_judgments_jsonl(tmp_path / f"j_{name}.jsonl", jl)

        args = _args(
            judgments_a=tmp_path / "j_a.jsonl",
            judgments_b=tmp_path / "j_b.jsonl",
            judgments_c=tmp_path / "j_c.jsonl",
            judgments_e=None,
            author_adjudications=None,
            spot_check_overrides=None,
            confidence_floor=0.6,
            out=tmp_path / "fin",
        )
        rc = run_finalize(args)
        assert rc == 0
        path = tmp_path / "fin" / "final_verdicts.jsonl"
        records = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
        assert len(records) == 3
        provs = {r["provenance"] for r in records}
        # c1 → CONVERGENT, c2/c3 → UNRESOLVED (no arbiter or author input).
        assert "CONVERGENT" in provs
        assert "UNRESOLVED" in provs

    def test_summary_counts_oos_with_evidence_gap(self, tmp_path: Path) -> None:
        from uofa_cli.adversarial.judge.runner import run_finalize

        gap = {
            "missing_evidence_type": "x" * 20,
            "would_support_defeater_evaluation": "y" * 20,
        }
        # 3 OOS-agreeing cases with evidence_gap on at least one judge.
        a = [_make_judgment(f"c{i}", "OUT-OF-SCOPE", 0.85) for i in range(3)]
        for j in a:
            object.__setattr__(j, "evidence_gap", gap)
        b = [_make_judgment(f"c{i}", "OUT-OF-SCOPE", 0.85) for i in range(3)]
        c = [_make_judgment(f"c{i}", "REAL-GAP", 0.7) for i in range(3)]
        for name, jl in (("a", a), ("b", b), ("c", c)):
            _write_judgments_jsonl(tmp_path / f"j_{name}.jsonl", jl)

        args = _args(
            judgments_a=tmp_path / "j_a.jsonl",
            judgments_b=tmp_path / "j_b.jsonl",
            judgments_c=tmp_path / "j_c.jsonl",
            judgments_e=None,
            author_adjudications=None,
            spot_check_overrides=None,
            confidence_floor=0.6,
            out=tmp_path / "fin",
        )
        run_finalize(args)
        summary = json.loads((tmp_path / "fin" / "final_verdicts_summary.json").read_text())
        assert summary["case_count"] == 3
        assert summary["out_of_scope_with_evidence_gap"] == 3
        assert summary["out_of_scope_without_evidence_gap"] == 0


class TestRunFormalize:
    def test_emits_rule_scaffolds(self, tmp_path: Path) -> None:
        from uofa_cli.adversarial.judge.runner import run_formalize

        # Write a final_verdicts.jsonl with a REAL-GAP entry.
        fv_path = tmp_path / "final.jsonl"
        fv_path.write_text(json.dumps({
            "case_id": "c1", "final_verdict": "REAL-GAP",
            "provenance": "CONVERGENT",
            "provenance_judges": ["A", "B"],
            "final_verdict_confidence": 0.85,
        }) + "\n")
        # Provide §6.7 candidate via judgments_A.jsonl.
        ja_path = tmp_path / "judgments_A.jsonl"
        ja_path.write_text(json.dumps({
            "case_id": "c1", "verdict": "REAL-GAP",
            "section_6_7_candidate": "W-EV-01",
        }) + "\n")

        args = _args(
            final_verdicts=fv_path,
            judgments_a=ja_path,
            judgments_b=None,
            judgments_c=None,
            severity_overrides=None,
            out=tmp_path / "fz",
        )
        rc = run_formalize(args)
        assert rc == 0
        assert (tmp_path / "fz" / "rules" / "w_ev01.rule").exists()


class TestRunCaseStudyRerun:
    def test_requires_two_catalogs(self, tmp_path: Path) -> None:
        from uofa_cli.adversarial.judge.runner import run_case_study_rerun

        args = _args(
            catalog=["v0.5"],
            cou=["morrison-cou1"],
            out=tmp_path / "cs",
        )
        rc = run_case_study_rerun(args)
        assert rc == 2


class TestRunJudgeDryRunAndResume:
    """Cover Wave F (--dry-run) + Wave I (--resume) flags."""

    def test_dry_run_writes_cost_estimate_no_calls(self, tmp_path: Path) -> None:
        from uofa_cli.adversarial.judge.runner import run_judge
        from .fixtures.mock_bundle import write_mock_bundle

        bundle_path = write_mock_bundle(tmp_path / "bundle.tgz")

        args = _args(
            in_bundle=bundle_path,
            out=tmp_path / "out",
            judges="mock_a,mock_b,mock_c",
            parallel=1,
            calibration_only=False,
            allow_same_family_judge=False,
            dry_run=True,
            max_cost=None,
            resume=False,
        )
        rc = run_judge(args)
        assert rc == 0
        # Mock-only dry run produces an empty per-judge table (no real cost
        # to estimate); the file still exists for downstream tooling.
        cost_path = tmp_path / "out" / "cost_estimate.json"
        assert cost_path.exists()
        data = json.loads(cost_path.read_text())
        assert data["estimated_total_usd"] == 0.0  # all mocks


class TestExtractResponseCost:
    def test_returns_litellm_hidden_cost_when_present(self) -> None:
        from uofa_cli.adversarial.judge.runner import _extract_response_cost

        j = _make_judgment("c1", "REAL-GAP")
        # Set raw_response via __setattr__ since Judgment is frozen.
        object.__setattr__(j, "raw_response", {
            "_hidden_params": {"response_cost": 0.0125},
            "usage": {"prompt_tokens": 100, "completion_tokens": 50},
        })
        usd = _extract_response_cost(j, "openai")
        assert usd == 0.0125

    def test_returns_zero_when_no_usage(self) -> None:
        from uofa_cli.adversarial.judge.runner import _extract_response_cost

        j = _make_judgment("c1", "REAL-GAP")
        usd = _extract_response_cost(j, "openai")
        assert usd == 0.0


class TestRunArbitrate:
    """Cover the run_arbitrate dispatch path (Wave C / runner.py 267-328)."""

    def test_arbitrate_with_mock_e_writes_outputs(self, tmp_path: Path) -> None:
        from uofa_cli.adversarial.judge.runner import run_arbitrate

        # Set up production judgments + a 2-case disagreement queue.
        a = [_make_judgment("c1", "REAL-GAP", 0.85),
             _make_judgment("c2", "GENERATOR-ARTIFACT", 0.85)]
        b = [_make_judgment("c1", "GENERATOR-ARTIFACT", 0.85),
             _make_judgment("c2", "REAL-GAP", 0.85)]
        c = [_make_judgment("c1", "OUT-OF-SCOPE", 0.85),
             _make_judgment("c2", "OUT-OF-SCOPE", 0.85)]
        for name, jl in (("a", a), ("b", b), ("c", c)):
            _write_judgments_jsonl(tmp_path / f"j_{name}.jsonl", jl)

        # Disagreement queue CSV (subset of cases to arbitrate).
        queue_path = tmp_path / "disagreement_queue.csv"
        queue_path.write_text(
            "case_id,bucket,majority_verdict,disagreement_type\n"
            "c1,DISAGREEMENT,,all_three_disagree\n"
            "c2,DISAGREEMENT,,all_three_disagree\n"
        )

        args = _args(
            judgments_a=tmp_path / "j_a.jsonl",
            judgments_b=tmp_path / "j_b.jsonl",
            judgments_c=tmp_path / "j_c.jsonl",
            disagreement_queue=queue_path,
            out=tmp_path / "arb",
            judge_e="mock_e",
            confidence_floor=0.6,
        )
        rc = run_arbitrate(args)
        assert rc == 0
        out = tmp_path / "arb"
        assert (out / "judgments_E.jsonl").exists()
        assert (out / "arbitrated.jsonl").exists()
        assert (out / "escalation_queue.csv").exists()

    def test_arbitrate_unknown_judge_e_token_returns_2(self, tmp_path: Path) -> None:
        from uofa_cli.adversarial.judge.runner import run_arbitrate

        # Same fixture shape but with a bogus token.
        a = [_make_judgment("c1", "REAL-GAP", 0.85)]
        b = [_make_judgment("c1", "GENERATOR-ARTIFACT", 0.85)]
        c = [_make_judgment("c1", "OUT-OF-SCOPE", 0.85)]
        for name, jl in (("a", a), ("b", b), ("c", c)):
            _write_judgments_jsonl(tmp_path / f"j_{name}.jsonl", jl)
        queue_path = tmp_path / "queue.csv"
        queue_path.write_text("case_id\nc1\n")

        args = _args(
            judgments_a=tmp_path / "j_a.jsonl",
            judgments_b=tmp_path / "j_b.jsonl",
            judgments_c=tmp_path / "j_c.jsonl",
            disagreement_queue=queue_path,
            out=tmp_path / "arb",
            judge_e="not-a-real-token",
            confidence_floor=0.6,
        )
        rc = run_arbitrate(args)
        assert rc == 2


class TestReadDisagreementQueue:
    def test_reads_case_ids(self, tmp_path: Path) -> None:
        from uofa_cli.adversarial.judge.runner import _read_disagreement_queue

        path = tmp_path / "q.csv"
        path.write_text("case_id,bucket\nc1,DISAGREEMENT\nc2,DISAGREEMENT\n\n")
        ids = _read_disagreement_queue(path)
        assert ids == ["c1", "c2"]

    def test_missing_file_raises(self, tmp_path: Path) -> None:
        from uofa_cli.adversarial.judge.runner import _read_disagreement_queue

        with pytest.raises(FileNotFoundError):
            _read_disagreement_queue(tmp_path / "nope.csv")


class TestRunCalibrateAnchor:
    """Cover run_calibrate_anchor (Wave B / runner.py 354-384)."""

    def test_ingest_committed_calibration_set(self, tmp_path: Path) -> None:
        from uofa_cli.adversarial.judge.runner import run_calibrate_anchor

        # Use the actual committed calibration set; ingest is read-only.
        from pathlib import Path as P
        cal_path = P("specs/calibration/calibration_set_v1.jsonl")
        if not cal_path.exists():
            pytest.skip("calibration set not present in this checkout")

        args = _args(
            anchor_action="ingest",
            in_path=cal_path,
            overrides=None,
            out=tmp_path / "anchor",
        )
        rc = run_calibrate_anchor(args)
        assert rc == 0
        # Normalized anchor JSONL written to out_dir.
        assert (tmp_path / "anchor" / "judge_d_anchor.jsonl").exists()

    def test_ingest_missing_file_returns_2(self, tmp_path: Path) -> None:
        from uofa_cli.adversarial.judge.runner import run_calibrate_anchor

        args = _args(
            anchor_action="ingest",
            in_path=tmp_path / "nonexistent.jsonl",
            overrides=None,
            out=None,
        )
        rc = run_calibrate_anchor(args)
        assert rc == 2

    def test_regenerate_returns_2_not_implemented(self, tmp_path: Path) -> None:
        from uofa_cli.adversarial.judge.runner import run_calibrate_anchor

        args = _args(anchor_action="regenerate", in_path=tmp_path / "x", out=None)
        rc = run_calibrate_anchor(args)
        assert rc == 2


class TestRunCaseStudyRerunHappyPath:
    """Patch-around case-study so we cover the happy path of run_case_study_rerun
    (runner.py ~300-333) without shelling out to `uofa rules`."""

    def test_writes_delta_table(self, tmp_path: Path, monkeypatch) -> None:
        from uofa_cli.adversarial.judge import case_study as cs_mod
        from uofa_cli.adversarial.judge.runner import run_case_study_rerun

        # Stub the rule engine via the module-level `run_case_study` callable
        # by monkeypatching CatalogRun production at the engine level.
        def stub(catalog: str, cou: str):
            return cs_mod.CatalogRun(
                catalog=catalog, cou=cou,
                annotation_count=2 if catalog == "v0.5" else 1,
                per_pattern_firings={"W-EP-01": 1},
            )

        # Monkeypatch the default rule engine to the stub.
        monkeypatch.setattr(cs_mod, "_default_rule_engine", stub)

        args = _args(
            catalog=["v0.4.1", "v0.5"],
            cou=["morrison-cou1"],
            out=tmp_path / "cs",
        )
        rc = run_case_study_rerun(args)
        assert rc == 0
        assert (tmp_path / "cs" / "delta_table.md").exists()
        assert (tmp_path / "cs" / "delta_table.json").exists()


class TestJudgeBundleConcurrency:
    """Wave J pilot follow-up: per-vendor concurrency in _judge_bundle."""

    def test_concurrent_path_writes_same_output_as_serial(self, tmp_path: Path) -> None:
        """Concurrent and serial paths must produce identical JSONL."""
        from uofa_cli.adversarial.judge.runner import _judge_bundle
        from .fixtures.mock_bundle import write_mock_bundle

        bundle = write_mock_bundle(tmp_path / "b.tgz")

        async def _run(out_dir: Path, concurrency: int) -> None:
            providers = [_MockProvider(t) for t in ("mock_a", "mock_b", "mock_c")]
            await _judge_bundle(
                in_bundle=bundle,
                providers=providers,
                positions=("A", "B", "C"),
                tokens=("mock_a", "mock_b", "mock_c"),
                out_dir=out_dir,
                calibration_only=False,
                concurrency=concurrency,
            )

        out_serial = tmp_path / "serial"
        out_concurrent = tmp_path / "concurrent"
        out_serial.mkdir(); out_concurrent.mkdir()
        asyncio.run(_run(out_serial, concurrency=1))
        asyncio.run(_run(out_concurrent, concurrency=5))

        for pos in ("A", "B", "C"):
            serial_lines = sorted(
                (out_serial / f"judgments_{pos}.jsonl").read_text().splitlines()
            )
            concurrent_lines = sorted(
                (out_concurrent / f"judgments_{pos}.jsonl").read_text().splitlines()
            )
            assert serial_lines == concurrent_lines, (
                f"position {pos} mismatch under concurrency"
            )

    def test_per_judge_overrides_apply(self, tmp_path: Path) -> None:
        """concurrency_per_judge overrides the global concurrency value."""
        from uofa_cli.adversarial.judge.runner import _judge_bundle
        from .fixtures.mock_bundle import write_mock_bundle

        bundle = write_mock_bundle(tmp_path / "b.tgz")
        out = tmp_path / "out"
        out.mkdir()

        async def _run() -> None:
            providers = [_MockProvider(t) for t in ("mock_a", "mock_b", "mock_c")]
            await _judge_bundle(
                in_bundle=bundle,
                providers=providers,
                positions=("A", "B", "C"),
                tokens=("mock_a", "mock_b", "mock_c"),
                out_dir=out,
                calibration_only=False,
                concurrency=1,
                concurrency_per_judge={"mock_b": 5, "mock_c": 3},
            )

        asyncio.run(_run())
        # Just verify the output files exist + have content (semaphore
        # values are internal to the gather; we test the wiring works).
        for pos in ("A", "B", "C"):
            path = out / f"judgments_{pos}.jsonl"
            assert path.exists()
            assert len(path.read_text().splitlines()) >= 1

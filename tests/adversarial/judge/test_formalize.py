"""Tests for Wave J: REAL-GAP → Jena rule scaffold (forward-chaining only)."""

from __future__ import annotations

import json
from pathlib import Path

from uofa_cli.adversarial.judge.final_verdict import (
    EvidenceGap,
    FinalVerdict,
    write_final_verdicts,
)
from uofa_cli.adversarial.judge.formalize import (
    DEFAULT_SEVERITY,
    SECTION_6_7_SEVERITY,
    formalize_real_gaps,
    run_formalize_from_files,
    write_formalization_outputs,
)


def _real_gap_fv(case_id: str, candidate: str | None = "W-EV-01") -> FinalVerdict:
    fv = FinalVerdict(
        case_id=case_id,
        final_verdict="REAL-GAP",
        provenance="CONVERGENT",
        provenance_judges=("A", "B"),
        final_verdict_confidence=0.85,
    )
    if candidate is not None:
        # FinalVerdict is frozen but we can set new attrs through the
        # pickle-style __setattr__; this matches what
        # run_formalize_from_files does at runtime.
        object.__setattr__(fv, "section_6_7_candidate", candidate)
    return fv


def _correct_detection_fv(case_id: str) -> FinalVerdict:
    return FinalVerdict(
        case_id=case_id,
        final_verdict="CORRECT-DETECTION",
        provenance="CONVERGENT",
        provenance_judges=("A", "B", "C"),
        final_verdict_confidence=0.9,
    )


# ── candidate generation ────────────────────────────────────────────────


class TestFormalizeRealGaps:
    def test_real_gap_with_candidate_produces_scaffold(self) -> None:
        result = formalize_real_gaps(
            final_verdicts=[_real_gap_fv("c1", "W-EV-01")]
        )
        assert len(result.candidates) == 1
        c = result.candidates[0]
        assert c.case_id == "c1"
        assert c.section_6_7_candidate == "W-EV-01"
        assert c.severity == "High"  # from §6.7 table
        assert c.rule_id == "w_ev01"
        # Forward-chaining shape:
        assert "[w_ev01:" in c.rule_skeleton
        assert "uofa:hasWeakener ?ann" in c.rule_skeleton
        assert "uofa:patternId 'W-EV-01'" in c.rule_skeleton
        # Test scaffold present:
        assert "test_w_ev01_fires_on_pattern_instance" in c.test_skeleton
        assert "test_w_ev01_does_not_fire_on_negative_control" in c.test_skeleton

    def test_non_real_gap_skipped(self) -> None:
        result = formalize_real_gaps(
            final_verdicts=[_correct_detection_fv("c1")]
        )
        assert result.candidates == []
        assert result.skipped_case_count == 1
        assert result.skipped_reasons["not_real_gap"] == 1

    def test_real_gap_without_candidate_skipped(self) -> None:
        result = formalize_real_gaps(
            final_verdicts=[_real_gap_fv("c1", candidate=None)]
        )
        assert result.candidates == []
        assert result.skipped_case_count == 1
        assert result.skipped_reasons["no_section_6_7_candidate"] == 1

    def test_severity_override_applied(self) -> None:
        result = formalize_real_gaps(
            final_verdicts=[_real_gap_fv("c1", "W-EV-01")],
            severity_overrides={"W-EV-01": "Critical"},
        )
        assert result.candidates[0].severity == "Critical"

    def test_unknown_candidate_uses_default_severity(self) -> None:
        result = formalize_real_gaps(
            final_verdicts=[_real_gap_fv("c1", "W-XX-99")]
        )
        assert result.candidates[0].severity == DEFAULT_SEVERITY

    def test_section_6_7_severity_table_covers_5_of_6_candidates(self) -> None:
        # Per spec §6.7 Tier 1 candidates: W-EV-01, W-EV-02, W-REQ-01,
        # W-CX-01, W-AR-06, W-AR-07.
        for candidate in ("W-EV-01", "W-EV-02", "W-REQ-01", "W-CX-01", "W-AR-06"):
            assert candidate in SECTION_6_7_SEVERITY


# ── persistence ─────────────────────────────────────────────────────────


class TestPersistence:
    def test_writes_rule_test_and_summary(self, tmp_path: Path) -> None:
        result = formalize_real_gaps(
            final_verdicts=[
                _real_gap_fv("c1", "W-EV-01"),
                _real_gap_fv("c2", "W-AR-06"),
            ]
        )
        write_formalization_outputs(result, tmp_path)
        # Per-rule files (catalog convention: w_ev01, no underscore
        # between the letter group and the digits):
        assert (tmp_path / "rules" / "w_ev01.rule").exists()
        assert (tmp_path / "rules" / "w_ar06.rule").exists()
        # Per-test files:
        assert (tmp_path / "tests" / "test_w_ev01.py").exists()
        assert (tmp_path / "tests" / "test_w_ar06.py").exists()
        # Summary index:
        summary = json.loads((tmp_path / "formalization_summary.json").read_text())
        assert summary["candidate_count"] == 2
        assert summary["skipped_case_count"] == 0
        assert {c["section_6_7_candidate"] for c in summary["candidates"]} == {
            "W-EV-01", "W-AR-06"
        }


# ── end-to-end CLI helper ────────────────────────────────────────────────


class TestRunFormalizeFromFiles:
    def test_attaches_section_6_7_from_judgments(self, tmp_path: Path) -> None:
        # Write final_verdicts.jsonl with one REAL-GAP case (no candidate).
        fv_path = tmp_path / "final.jsonl"
        write_final_verdicts(
            [
                FinalVerdict(
                    case_id="c1", final_verdict="REAL-GAP",
                    provenance="CONVERGENT", provenance_judges=("A", "B"),
                    final_verdict_confidence=0.85,
                ),
            ],
            fv_path,
        )

        # Write a judgments_A.jsonl that supplies the candidate.
        ja_path = tmp_path / "judgments_A.jsonl"
        ja_path.write_text(json.dumps({
            "case_id": "c1", "verdict": "REAL-GAP",
            "section_6_7_candidate": "W-REQ-01",
        }) + "\n")

        out_dir = tmp_path / "out"
        result = run_formalize_from_files(
            final_verdicts_path=fv_path,
            judgments_paths={"A": ja_path},
            out_dir=out_dir,
        )
        assert len(result.candidates) == 1
        assert result.candidates[0].section_6_7_candidate == "W-REQ-01"
        assert (out_dir / "rules" / "w_req01.rule").exists()


# ── §6.7 scope guard (Delta 6: forward-chaining only) ───────────────────


class TestDelta6Scope:
    def test_oos_verdicts_never_produce_jena_rules(self) -> None:
        # Delta 6: OOS verdicts ship as evidence_gap, NOT Jena rules.
        # Even with a productive evidence_gap and a §6.7 candidate, the
        # formalize path skips them.
        oos_fv = FinalVerdict(
            case_id="oos1",
            final_verdict="OUT-OF-SCOPE",
            provenance="ARBITRATED",
            provenance_judges=("E",),
            final_verdict_confidence=0.7,
            evidence_gap=EvidenceGap(
                missing_evidence_type="EMA jurisdiction evidence",
                would_support_defeater_evaluation="x",
                evidence_gap_source="judge_e",
            ),
        )
        # Even if we (incorrectly) attached a candidate, formalize must skip.
        object.__setattr__(oos_fv, "section_6_7_candidate", "W-EV-01")
        result = formalize_real_gaps(final_verdicts=[oos_fv])
        assert result.candidates == []
        assert result.skipped_reasons["not_real_gap"] == 1

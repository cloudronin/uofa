"""Tests for Wave E final-verdict assembly + productive-OOS Delta 5.

Covers:
  - Source priority: AUTHOR_OVERRIDE > AUTHOR_FINAL > ARBITRATED > CONVERGENT
  - CONVERGENT OOS aggregation: highest-confidence judge primary;
    canonical A→B→C tie-break; alternatives preserved.
  - ARBITRATED OOS sourced from Judge E.
  - AUTHOR_FINAL / AUTHOR_OVERRIDE OOS sourced from author record.
  - Schema validation: every OOS final_verdict has evidence_gap with
    `evidence_gap_source` ∈ {judge_a..c, judge_e, author}.
  - JSONL round-trip.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from uofa_cli.adversarial.judge.final_verdict import (
    EvidenceGap,
    FinalVerdict,
    assemble_final_verdicts,
    load_arbitration_records,
    load_author_records,
    load_final_verdicts,
    load_spot_check_overrides,
    write_final_verdicts,
)
from uofa_cli.adversarial.judge.providers.base import Judgment
from uofa_cli.adversarial.judge.triage import triage_corpus


def _judgment(
    case_id: str, verdict: str, confidence: float = 0.85, *,
    evidence_gap: dict | None = None,
) -> Judgment:
    return Judgment(
        case_id=case_id,
        verdict=verdict,
        confidence=confidence,
        reasoning_steps={"verdict_commitment": verdict},
        reasoning="x" * 50,
        section_6_7_candidate=None,
        alternative_rule_analysis=None,
        prompt_template_version="v1.1.0",
        judge_model="mock",
        judge_thinking_enabled=False,
        judge_model_params={"temperature": 0.0, "seed": 42},
        generator_provenance={"generator_model": "mock", "temperature": None, "seed": None},
        evidence_gap=evidence_gap,
    )


# ── source priority ────────────────────────────────────────────────────


class TestSourcePriority:
    def test_convergent_baseline(self) -> None:
        # All three agree, no override / arbitration / author input.
        a = _judgment("c1", "REAL-GAP", 0.9)
        b = _judgment("c1", "REAL-GAP", 0.85)
        c = _judgment("c1", "REAL-GAP", 0.8)
        triage = triage_corpus([(a, b, c)])
        final = assemble_final_verdicts(triage_entries=triage.entries)
        assert len(final) == 1
        assert final[0].provenance == "CONVERGENT"
        assert final[0].final_verdict == "REAL-GAP"
        assert final[0].provenance_judges == ("A", "B", "C")
        assert final[0].evidence_gap is None

    def test_arbitrated_takes_precedence_on_disagreement(self) -> None:
        a = _judgment("c1", "REAL-GAP", 0.85)
        b = _judgment("c1", "GENERATOR-ARTIFACT", 0.85)
        c = _judgment("c1", "OUT-OF-SCOPE", 0.85)
        triage = triage_corpus([(a, b, c)])
        # Judge E confidence ≥ floor → ARBITRATED.
        arbitration = {
            "c1": {
                "case_id": "c1", "verdict": "REAL-GAP", "confidence": 0.85
            }
        }
        final = assemble_final_verdicts(
            triage_entries=triage.entries,
            arbitration_records=arbitration,
        )
        assert final[0].provenance == "ARBITRATED"
        assert final[0].final_verdict == "REAL-GAP"
        assert final[0].provenance_judges == ("E",)

    def test_author_final_over_arbitration_below_floor(self) -> None:
        a = _judgment("c1", "REAL-GAP", 0.85)
        b = _judgment("c1", "GENERATOR-ARTIFACT", 0.85)
        c = _judgment("c1", "OUT-OF-SCOPE", 0.85)
        triage = triage_corpus([(a, b, c)])
        # Judge E < floor → not ARBITRATED.
        arbitration = {
            "c1": {"case_id": "c1", "verdict": "REAL-GAP", "confidence": 0.4}
        }
        author = {
            "c1": {"case_id": "c1", "final_verdict": "GENERATOR-ARTIFACT",
                   "rationale": "manual review concluded GA"}
        }
        final = assemble_final_verdicts(
            triage_entries=triage.entries,
            arbitration_records=arbitration,
            author_records=author,
        )
        assert final[0].provenance == "AUTHOR_FINAL"
        assert final[0].final_verdict == "GENERATOR-ARTIFACT"

    def test_author_override_beats_convergent(self) -> None:
        a = _judgment("c1", "REAL-GAP", 0.9)
        b = _judgment("c1", "REAL-GAP", 0.85)
        c = _judgment("c1", "REAL-GAP", 0.8)
        triage = triage_corpus([(a, b, c)])
        spot_check = {
            "c1": {"case_id": "c1", "original_verdict": "REAL-GAP",
                   "override_verdict": "GENERATOR-ARTIFACT",
                   "override_rationale": "actually a generator artifact"}
        }
        final = assemble_final_verdicts(
            triage_entries=triage.entries,
            spot_check_overrides=spot_check,
        )
        assert final[0].provenance == "AUTHOR_OVERRIDE"
        assert final[0].final_verdict == "GENERATOR-ARTIFACT"

    def test_unresolved_for_disagreement_with_no_arbiter_or_author(self) -> None:
        a = _judgment("c1", "REAL-GAP", 0.85)
        b = _judgment("c1", "GENERATOR-ARTIFACT", 0.85)
        c = _judgment("c1", "OUT-OF-SCOPE", 0.85)
        triage = triage_corpus([(a, b, c)])
        final = assemble_final_verdicts(triage_entries=triage.entries)
        assert final[0].provenance == "UNRESOLVED"
        assert final[0].final_verdict == "UNRESOLVED"


# ── productive-OOS evidence_gap (Delta 5) ──────────────────────────────


class TestEvidenceGapCarryThrough:
    def test_convergent_oos_picks_highest_confidence(self) -> None:
        # Two judges agree on OOS with different confidence + different
        # gaps. Primary should come from higher-confidence judge.
        gap_a = {
            "missing_evidence_type": "EMA-jurisdiction credibility evidence",
            "would_support_defeater_evaluation":
                "would let UofA evaluate cross-framework reconciliation",
        }
        gap_b = {
            "missing_evidence_type": "tolerance rationale calibration studies",
            "would_support_defeater_evaluation":
                "would justify the ±15% tolerance specification",
        }
        a = _judgment("c1", "OUT-OF-SCOPE", 0.92, evidence_gap=gap_a)
        b = _judgment("c1", "OUT-OF-SCOPE", 0.85, evidence_gap=gap_b)
        c = _judgment("c1", "REAL-GAP", 0.7)  # disagrees
        triage = triage_corpus([(a, b, c)])
        # 2-of-3 agree on OOS at high confidence → CONVERGENT.
        assert triage.entries[0].majority_verdict == "OUT-OF-SCOPE"
        final = assemble_final_verdicts(triage_entries=triage.entries)
        assert final[0].final_verdict == "OUT-OF-SCOPE"
        assert final[0].evidence_gap is not None
        assert final[0].evidence_gap.evidence_gap_source == "judge_a"
        assert "EMA-jurisdiction" in final[0].evidence_gap.missing_evidence_type
        # Alternative gap from B preserved.
        assert len(final[0].alternative_evidence_gaps) == 1
        assert final[0].alternative_evidence_gaps[0].evidence_gap_source == "judge_b"

    def test_convergent_oos_canonical_tiebreak_when_equal_confidence(self) -> None:
        # Same confidence on B and C → A first wins by canonical priority,
        # but A disagrees here. Then B beats C on canonical order.
        gap_b = {"missing_evidence_type": "tolerance studies",
                 "would_support_defeater_evaluation": "would justify ±15%"}
        gap_c = {"missing_evidence_type": "predicate device precedent",
                 "would_support_defeater_evaluation": "would justify class"}
        a = _judgment("c1", "REAL-GAP", 0.7)
        b = _judgment("c1", "OUT-OF-SCOPE", 0.85, evidence_gap=gap_b)
        c = _judgment("c1", "OUT-OF-SCOPE", 0.85, evidence_gap=gap_c)
        triage = triage_corpus([(a, b, c)])
        final = assemble_final_verdicts(triage_entries=triage.entries)
        assert final[0].evidence_gap.evidence_gap_source == "judge_b"
        assert final[0].alternative_evidence_gaps[0].evidence_gap_source == "judge_c"

    def test_arbitrated_oos_sourced_from_judge_e(self) -> None:
        a = _judgment("c1", "REAL-GAP", 0.85)
        b = _judgment("c1", "GENERATOR-ARTIFACT", 0.85)
        c = _judgment("c1", "OUT-OF-SCOPE", 0.85)
        triage = triage_corpus([(a, b, c)])
        gap = {
            "missing_evidence_type": "clinical interpretation framework",
            "would_support_defeater_evaluation":
                "would let UofA evaluate clinical acceptance reasoning",
        }
        arbitration = {
            "c1": {
                "case_id": "c1", "verdict": "OUT-OF-SCOPE", "confidence": 0.8,
                "evidence_gap": gap,
            }
        }
        final = assemble_final_verdicts(
            triage_entries=triage.entries,
            arbitration_records=arbitration,
        )
        assert final[0].provenance == "ARBITRATED"
        assert final[0].evidence_gap is not None
        assert final[0].evidence_gap.evidence_gap_source == "judge_e"

    def test_author_final_oos_sourced_from_author(self) -> None:
        a = _judgment("c1", "REAL-GAP", 0.85)
        b = _judgment("c1", "GENERATOR-ARTIFACT", 0.85)
        c = _judgment("c1", "OUT-OF-SCOPE", 0.85)
        triage = triage_corpus([(a, b, c)])
        arbitration = {
            "c1": {"case_id": "c1", "verdict": "OUT-OF-SCOPE", "confidence": 0.4}
        }
        author = {
            "c1": {
                "case_id": "c1",
                "final_verdict": "OUT-OF-SCOPE",
                "evidence_gap": {
                    "missing_evidence_type": "behavioral compliance audit logs",
                    "would_support_defeater_evaluation":
                        "would let UofA verify governance policy execution",
                },
            }
        }
        final = assemble_final_verdicts(
            triage_entries=triage.entries,
            arbitration_records=arbitration,
            author_records=author,
        )
        assert final[0].provenance == "AUTHOR_FINAL"
        assert final[0].evidence_gap.evidence_gap_source == "author"

    def test_non_oos_verdict_never_carries_evidence_gap(self) -> None:
        a = _judgment("c1", "REAL-GAP", 0.9)
        b = _judgment("c1", "REAL-GAP", 0.85)
        c = _judgment("c1", "REAL-GAP", 0.8)
        triage = triage_corpus([(a, b, c)])
        final = assemble_final_verdicts(triage_entries=triage.entries)
        assert final[0].evidence_gap is None
        assert final[0].alternative_evidence_gaps == ()


# ── persistence round-trip ─────────────────────────────────────────────


class TestRoundTrip:
    def test_jsonl_round_trip_preserves_evidence_gap(self, tmp_path: Path) -> None:
        gap = EvidenceGap(
            missing_evidence_type="x-ref evidence",
            would_support_defeater_evaluation="would let UofA evaluate y",
            evidence_gap_source="judge_a",
        )
        alt = EvidenceGap(
            missing_evidence_type="y-ref evidence",
            would_support_defeater_evaluation="would also help",
            evidence_gap_source="judge_b",
        )
        fv = FinalVerdict(
            case_id="c1",
            final_verdict="OUT-OF-SCOPE",
            provenance="CONVERGENT",
            provenance_judges=("A", "B"),
            final_verdict_confidence=0.85,
            evidence_gap=gap,
            alternative_evidence_gaps=(alt,),
        )
        path = tmp_path / "final.jsonl"
        write_final_verdicts([fv], path)
        loaded = load_final_verdicts(path)
        assert len(loaded) == 1
        assert loaded[0] == fv

    def test_load_spot_check_overrides_parses_jsonl(self, tmp_path: Path) -> None:
        path = tmp_path / "overrides.jsonl"
        path.write_text(
            json.dumps({
                "case_id": "c1", "original_verdict": "REAL-GAP",
                "override_verdict": "GENERATOR-ARTIFACT",
                "override_rationale": "actually GA",
                "original_provenance": "CONVERGENT"
            }) + "\n"
        )
        records = load_spot_check_overrides(path)
        assert "c1" in records
        assert records["c1"]["override_verdict"] == "GENERATOR-ARTIFACT"

    def test_load_author_records_parses_jsonl(self, tmp_path: Path) -> None:
        path = tmp_path / "author.jsonl"
        path.write_text(
            json.dumps({"case_id": "c1", "final_verdict": "REAL-GAP"}) + "\n"
        )
        records = load_author_records(path)
        assert records["c1"]["final_verdict"] == "REAL-GAP"

    def test_load_arbitration_records_parses_jsonl(self, tmp_path: Path) -> None:
        path = tmp_path / "arb.jsonl"
        path.write_text(
            json.dumps({"case_id": "c1", "verdict": "OUT-OF-SCOPE",
                        "confidence": 0.7}) + "\n"
        )
        records = load_arbitration_records(path)
        assert records["c1"]["verdict"] == "OUT-OF-SCOPE"

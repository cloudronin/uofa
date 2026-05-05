"""Tests for the Judge E arbitration pipeline (Phase 3 v1.6 §6.7, §10.2)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from uofa_cli.adversarial.judge.arbitration import (
    ArbitrationEntry,
    Stage3bPartition,
    load_arbitration_jsonl,
    partition_arbitration_results,
    write_arbitration_jsonl,
    write_escalation_queue_csv,
)
from .fixtures.mock_arbitration import (
    build_mock_arbitration_results,
)


# ── Stage 3b partition logic ───────────────────────────────────────────


class TestPartitionArbitrationResults:
    def test_default_floor_partitions_7_arbitrated_3_escalated(self) -> None:
        results = build_mock_arbitration_results()
        partition = partition_arbitration_results(results)
        assert isinstance(partition, Stage3bPartition)
        assert len(partition.arbitrated) == 7
        assert len(partition.escalated) == 3
        assert partition.confidence_floor == 0.6

    def test_higher_floor_moves_more_to_escalated(self) -> None:
        results = build_mock_arbitration_results()
        partition = partition_arbitration_results(results, confidence_floor=0.8)
        # Cases with confidence ≥ 0.8: 0.82 + 0.91 + 0.85 = 3
        assert len(partition.arbitrated) == 3
        assert len(partition.escalated) == 7

    def test_lower_floor_moves_more_to_arbitrated(self) -> None:
        results = build_mock_arbitration_results()
        partition = partition_arbitration_results(results, confidence_floor=0.4)
        # All confidences ≥ 0.4 → all 10 ARBITRATED
        assert len(partition.arbitrated) == 10
        assert len(partition.escalated) == 0

    def test_empty_input_returns_empty_partition(self) -> None:
        partition = partition_arbitration_results([])
        assert len(partition.arbitrated) == 0
        assert len(partition.escalated) == 0


# ── arbitration JSONL round-trip ──────────────────────────────────────


class TestArbitrationJSONL:
    def test_write_and_load_round_trip(self, tmp_path: Path) -> None:
        results = build_mock_arbitration_results()
        out = tmp_path / "judgments_E.jsonl"
        write_arbitration_jsonl(results, out)

        loaded = load_arbitration_jsonl(out)
        assert len(loaded) == 10
        # Confirm a known field round-trips.
        assert loaded[0].case_id == results[0].case_id
        assert loaded[0].verdict == results[0].verdict
        assert loaded[0].arbitration_basis == results[0].arbitration_basis

    def test_oos_evidence_gap_preserved(self, tmp_path: Path) -> None:
        results = build_mock_arbitration_results()
        out = tmp_path / "judgments_E.jsonl"
        write_arbitration_jsonl(results, out)
        loaded = load_arbitration_jsonl(out)

        # The fixture has one OOS case with evidence_gap populated.
        oos = [r for r in loaded if r.verdict == "OUT-OF-SCOPE"]
        assert len(oos) == 1
        assert oos[0].evidence_gap is not None
        assert "clinical" in oos[0].evidence_gap["missing_evidence_type"]


class TestEscalationQueueCSV:
    def test_writes_csv_with_headers(self, tmp_path: Path) -> None:
        results = build_mock_arbitration_results()
        partition = partition_arbitration_results(results)
        out = tmp_path / "escalation_queue.csv"
        write_escalation_queue_csv(partition.escalated, out)
        lines = out.read_text().strip().splitlines()
        # 1 header + 3 escalated rows.
        assert len(lines) == 4
        assert "case_id" in lines[0]
        assert "judge_e_confidence" in lines[0]


# ── arbitrate_disagreement_queue (mock provider) ───────────────────────


class TestArbitrateDisagreementQueueWithMock:
    """Smoke test using mock_e provider; verifies the full async path runs."""

    def test_smoke_with_mock_judge_e(self) -> None:
        import asyncio
        from uofa_cli.adversarial.judge.arbitration import arbitrate_disagreement_queue
        from uofa_cli.adversarial.judge.runner import _MockProvider, _reset_mock_ledger
        from uofa_cli.adversarial.judge.providers.base import Judgment

        # Build production judgments for 5 disagreement cases.
        case_ids = [f"c{i}" for i in range(5)]
        production = {
            pos: {
                cid: Judgment(
                    case_id=cid,
                    verdict="REAL-GAP",
                    confidence=0.5,  # below convergent floor; simulates disagreement
                    reasoning_steps={
                        "source_taxonomy_identified": "test/x", "target_rule_identified": "Wxx",
                        "rule_firings_inspected": "none", "instantiation_check": "x" * 25,
                        "verdict_commitment": "REAL-GAP",
                    },
                    reasoning="x" * 60,
                    section_6_7_candidate=None,
                    alternative_rule_analysis=None,
                    prompt_template_version="v1.1.0",
                    judge_model=f"mock-{pos}",
                    judge_thinking_enabled=False,
                    judge_model_params={"temperature": 0.0, "seed": 42},
                    generator_provenance={"generator_model": "mock", "temperature": None, "seed": None},
                ) for cid in case_ids
            }
            for pos in ("A", "B", "C")
        }

        _reset_mock_ledger()
        judge_e = _MockProvider("mock_e")
        partition = asyncio.run(arbitrate_disagreement_queue(
            disagreement_case_ids=case_ids,
            production_judgments=production,
            judge_e=judge_e,
        ))
        # mock_e returns confidence=0.85 for every case, so all should ARBITRATE.
        assert len(partition.arbitrated) == 5
        assert len(partition.escalated) == 0

"""Tests for the Judge D calibration-anchor pipeline (Phase 3 v1.6 §8.0)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from uofa_cli.adversarial.judge.anchor import (
    IngestResult,
    ingest_anchor,
    record_override,
)


def _record(idx: int, verdict: str, *, canonical: bool = False, section_6_7: str | None = None) -> dict:
    return {
        "case_id": f"cal-{idx:03d}-test",
        "phase2_case_id": f"adv-2026-p2-{idx:03d}-test-v01",
        "package_path": None,
        "source_taxonomy": "test/example",
        "phase2_outcome_class": "COV-HIT-PLUS",
        "phase2_outcome_class_normalized": "COV-HIT",
        "expected_target_rule": "W-AR-01",
        "rules_fired": [],
        "section_6_7_mapping": section_6_7,
        "scaffold_note": "test",
        "ground_truth_verdict": verdict,
        "ground_truth_reasoning": "x" * 50,
        "ground_truth_section_6_7_candidate": None,
        "annotator": "Judge D",
        "annotation_date": "2026-05-04",
        "review_confidence": "high",
        "is_canonical_few_shot": canonical,
        "notes": "",
    }


def _full_set(tmp_path: Path) -> Path:
    classes = [
        "CORRECT-DETECTION", "REAL-GAP", "GENERATOR-ARTIFACT",
        "EXISTING-RULE-MISBEHAVIOR", "OUT-OF-SCOPE", "UNCERTAIN",
    ]
    rg_mappings = ["W-EV-01", "W-EV-02", "W-REQ-01", "W-CX-01", "W-AR-06"]
    records = []
    idx = 1
    for cls in classes:
        for i in range(5):
            extra = {"section_6_7": rg_mappings[i]} if cls == "REAL-GAP" else {}
            records.append(_record(idx, cls, canonical=(i == 0), **extra))
            idx += 1
    path = tmp_path / "cal.jsonl"
    path.write_text("\n".join(json.dumps(r) for r in records))
    return path


# ── ingest happy path ──────────────────────────────────────────────────


class TestIngestHappyPath:
    def test_ingest_returns_summary(self, tmp_path: Path) -> None:
        cal = _full_set(tmp_path)
        result = ingest_anchor(cal)
        assert isinstance(result, IngestResult)
        assert result.record_count == 30
        assert result.canonical_few_shot_count == 6
        assert sorted(result.section_6_7_coverage) == [
            "W-AR-06", "W-CX-01", "W-EV-01", "W-EV-02", "W-REQ-01"
        ]

    def test_ingest_writes_normalized_anchor_when_out_dir_set(self, tmp_path: Path) -> None:
        cal = _full_set(tmp_path)
        out_dir = tmp_path / "anchor_out"
        ingest_anchor(cal, out_dir=out_dir)
        anchor_file = out_dir / "judge_d_anchor.jsonl"
        assert anchor_file.exists()
        records = [json.loads(l) for l in anchor_file.read_text().splitlines() if l.strip()]
        assert len(records) == 30


class TestIngestFailureModes:
    def test_missing_calibration_set_raises(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            ingest_anchor(tmp_path / "missing.jsonl")

    def test_wrong_record_count_raises(self, tmp_path: Path) -> None:
        path = tmp_path / "cal.jsonl"
        path.write_text(json.dumps(_record(1, "REAL-GAP", canonical=True, section_6_7="W-EV-01")) + "\n")
        with pytest.raises(ValueError, match="expected 30"):
            ingest_anchor(path)

    def test_missing_canonical_per_class_raises(self, tmp_path: Path) -> None:
        # 30 records but no canonical for REAL-GAP class.
        classes = [
            "CORRECT-DETECTION", "REAL-GAP", "GENERATOR-ARTIFACT",
            "EXISTING-RULE-MISBEHAVIOR", "OUT-OF-SCOPE", "UNCERTAIN",
        ]
        rg_mappings = ["W-EV-01", "W-EV-02", "W-REQ-01", "W-CX-01", "W-AR-06"]
        records = []
        idx = 1
        for cls in classes:
            for i in range(5):
                canonical = (i == 0) and (cls != "REAL-GAP")
                extra = {"section_6_7": rg_mappings[i]} if cls == "REAL-GAP" else {}
                records.append(_record(idx, cls, canonical=canonical, **extra))
                idx += 1
        path = tmp_path / "cal.jsonl"
        path.write_text("\n".join(json.dumps(r) for r in records))
        with pytest.raises(ValueError, match="canonical few-shot"):
            ingest_anchor(path)


# ── author overrides ───────────────────────────────────────────────────


class TestAuthorOverrides:
    def test_record_override_appends(self, tmp_path: Path) -> None:
        overrides = tmp_path / "judge_d_author_overrides.jsonl"
        record_override(
            overrides,
            case_id="cal-001-test",
            original_verdict="CORRECT-DETECTION",
            override_verdict="UNCERTAIN",
            override_rationale="Author disputes Judge D's CORRECT-DETECTION on review",
        )
        records = [json.loads(l) for l in overrides.read_text().splitlines() if l.strip()]
        assert len(records) == 1
        assert records[0]["override_verdict"] == "UNCERTAIN"
        assert "overridden_at" in records[0]

    def test_invalid_override_verdict_rejected(self, tmp_path: Path) -> None:
        overrides = tmp_path / "judge_d_author_overrides.jsonl"
        with pytest.raises(ValueError, match="not in spec set"):
            record_override(
                overrides,
                case_id="cal-001",
                original_verdict="REAL-GAP",
                override_verdict="FAKE-VERDICT",
                override_rationale="x" * 50,
            )

    def test_short_rationale_rejected(self, tmp_path: Path) -> None:
        overrides = tmp_path / "judge_d_author_overrides.jsonl"
        with pytest.raises(ValueError, match="≥5 words"):
            record_override(
                overrides,
                case_id="cal-001",
                original_verdict="REAL-GAP",
                override_verdict="UNCERTAIN",
                override_rationale="too short",
            )

    def test_apply_overrides_through_ingest(self, tmp_path: Path) -> None:
        cal = _full_set(tmp_path)
        overrides = tmp_path / "overrides.jsonl"
        record_override(
            overrides,
            case_id="cal-001-test",  # CORRECT-DETECTION class case
            original_verdict="CORRECT-DETECTION",
            override_verdict="UNCERTAIN",
            override_rationale="Author override during sanity-check review",
        )
        # Validation runs BEFORE overrides apply (validates the as-committed
        # Judge D anchor); overrides then mutate the records in-memory and
        # propagate to the normalized output. Verify the override took effect
        # by reading the normalized output.
        out_dir = tmp_path / "anchor"
        result = ingest_anchor(cal, overrides_path=overrides, out_dir=out_dir)
        assert result.override_count == 1
        anchor = [
            json.loads(l) for l in (out_dir / "judge_d_anchor.jsonl").read_text().splitlines()
            if l.strip()
        ]
        cal_001 = next(r for r in anchor if r["case_id"] == "cal-001-test")
        assert cal_001["ground_truth_verdict"] == "UNCERTAIN"
        assert "AUTHOR OVERRIDE" in cal_001["notes"]


# ── real calibration set integration ───────────────────────────────────


class TestRealCalibrationSet:
    def test_ingest_real_calibration_set(self, tmp_path: Path) -> None:
        # Ingest the actually-committed calibration set; should pass.
        repo_root = Path(__file__).resolve().parents[3]
        cal = repo_root / "specs" / "calibration" / "calibration_set_v1.jsonl"
        if not cal.exists():
            pytest.skip("real calibration set not committed yet")
        out_dir = tmp_path / "anchor"
        result = ingest_anchor(cal, out_dir=out_dir)
        assert result.record_count == 30
        assert result.canonical_few_shot_count == 6
        # 5 of 6 §6.7 candidates covered (W-AR-07 missing per the user note).
        assert len(result.section_6_7_coverage) >= 4

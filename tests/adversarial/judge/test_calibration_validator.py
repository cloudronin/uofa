"""Tests for dev/tools/scripts/validate_calibration_set.py (v2 with §6.7 coverage check)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# Add dev/tools/scripts to sys.path so we can import the validator module.
_SCRIPTS = Path(__file__).resolve().parents[3] / "dev" / "tools" / "scripts"
sys.path.insert(0, str(_SCRIPTS))

import validate_calibration_set as cv  # type: ignore[import]


def _make_record(
    verdict: str,
    idx: int,
    *,
    canonical: bool = False,
    section_6_7: str | None = None,
    **overrides,
) -> dict:
    """Build a fully-filled valid calibration record."""
    # case_id uses underscored verdict token to match the validator's W1 token
    # set (e.g. 'real_gap', 'correct_detection'). The actual calibration set
    # ships with this convention; tests mirror it.
    rec = {
        "case_id": f"cal-{idx:03d}-{verdict.lower().replace('-', '_')}-test",
        "phase2_case_id": f"adv-2026-p2-{idx:03d}-test-v01",
        "package_path": None,
        "source_taxonomy": "test/example/sub-type",
        "phase2_outcome_class": "COV-HIT-PLUS",
        "phase2_outcome_class_normalized": "COV-HIT",
        "expected_target_rule": "W-AR-01",
        "rules_fired": ["W-AR-01"],
        "section_6_7_mapping": section_6_7,
        "scaffold_note": "test",
        "ground_truth_verdict": verdict,
        "ground_truth_reasoning": (
            "This is a deliberately long reasoning string that contains "
            "more than enough words to satisfy the thirty-word minimum "
            "requirement imposed by the validator on the "
            "ground_truth_reasoning field for testing purposes here in "
            "the unit tests."
        ),
        "ground_truth_section_6_7_candidate": None,
        "annotator": "Test",
        "annotation_date": "2026-05-04",
        "review_confidence": "high",
        "is_canonical_few_shot": canonical,
        "notes": "",
    }
    rec.update(overrides)
    return rec


def _write_jsonl(path: Path, records: list[dict]) -> Path:
    path.write_text("\n".join(json.dumps(r) for r in records))
    return path


def _full_set(tmp_path: Path) -> Path:
    """Build a complete 30-case valid calibration set with §6.7 coverage ≥4."""
    classes = [
        "CORRECT-DETECTION", "REAL-GAP", "GENERATOR-ARTIFACT",
        "EXISTING-RULE-MISBEHAVIOR", "OUT-OF-SCOPE", "UNCERTAIN",
    ]
    # REAL-GAP cases must have section_6_7_mapping populated and collectively
    # cover ≥4 of the 6 §6.7 candidates.
    real_gap_mappings = ["W-EV-01", "W-EV-02", "W-REQ-01", "W-CX-01", "W-AR-06"]
    records = []
    idx = 1
    for cls in classes:
        for i in range(5):
            extra = {}
            if cls == "REAL-GAP":
                extra["section_6_7"] = real_gap_mappings[i]
            # Mark exactly one record per class as canonical (i==0).
            records.append(_make_record(cls, idx, canonical=(i == 0), **extra))
            idx += 1
    return _write_jsonl(tmp_path / "cal.jsonl", records)


# ── happy path ─────────────────────────────────────────────────────────


class TestValidPath:
    def test_complete_set_passes(self, tmp_path: Path) -> None:
        path = _full_set(tmp_path)
        issues, warnings = cv.validate(
            path, repo_root=tmp_path, allow_verdict_in_case_id=True
        )
        assert issues == [], f"unexpected issues: {issues}"


# ── failure modes ──────────────────────────────────────────────────────


class TestFailureModes:
    def test_missing_file(self, tmp_path: Path) -> None:
        issues, warnings = cv.validate(tmp_path / "missing.jsonl", repo_root=tmp_path)
        assert any("not found" in i for i in issues)

    def test_wrong_total_count(self, tmp_path: Path) -> None:
        # 25 records instead of 30.
        records = [_make_record("REAL-GAP", i, canonical=(i == 1), section_6_7="W-EV-01") for i in range(1, 26)]
        path = _write_jsonl(tmp_path / "cal.jsonl", records)
        issues, _ = cv.validate(path, repo_root=tmp_path, allow_verdict_in_case_id=True)
        assert any("expected 30 records" in i for i in issues)

    def test_per_class_count_mismatch(self, tmp_path: Path) -> None:
        # 30 records but all REAL-GAP — other classes have 0.
        records = [
            _make_record("REAL-GAP", i, canonical=(i == 1), section_6_7="W-EV-01")
            for i in range(1, 31)
        ]
        path = _write_jsonl(tmp_path / "cal.jsonl", records)
        issues, _ = cv.validate(path, repo_root=tmp_path, allow_verdict_in_case_id=True)
        for cls in (
            "CORRECT-DETECTION", "GENERATOR-ARTIFACT",
            "EXISTING-RULE-MISBEHAVIOR", "OUT-OF-SCOPE", "UNCERTAIN",
        ):
            assert any(cls in i and "expected 5 records, got 0" in i for i in issues)

    def test_todo_marker_remaining(self, tmp_path: Path) -> None:
        records = [_make_record("REAL-GAP", 1, canonical=True, section_6_7="W-EV-01")]
        records[0]["ground_truth_verdict"] = "TODO_AUTHOR_VERDICT"
        path = _write_jsonl(tmp_path / "cal.jsonl", records)
        issues, _ = cv.validate(path, repo_root=tmp_path, allow_verdict_in_case_id=True)
        assert any("TODO_AUTHOR" in i for i in issues)

    def test_unknown_verdict_class(self, tmp_path: Path) -> None:
        rec = _make_record("REAL-GAP", 1, canonical=True, section_6_7="W-EV-01")
        rec["ground_truth_verdict"] = "FAKE-VERDICT"
        path = _write_jsonl(tmp_path / "cal.jsonl", [rec])
        issues, _ = cv.validate(path, repo_root=tmp_path, allow_verdict_in_case_id=True)
        assert any("not in spec set" in i for i in issues)

    def test_short_reasoning(self, tmp_path: Path) -> None:
        rec = _make_record("REAL-GAP", 1, canonical=True, section_6_7="W-EV-01")
        rec["ground_truth_reasoning"] = "too short"
        path = _write_jsonl(tmp_path / "cal.jsonl", [rec])
        issues, _ = cv.validate(path, repo_root=tmp_path, allow_verdict_in_case_id=True)
        assert any("ground_truth_reasoning has" in i and "≥30" in i for i in issues)

    def test_invalid_review_confidence(self, tmp_path: Path) -> None:
        rec = _make_record("REAL-GAP", 1, canonical=True, section_6_7="W-EV-01")
        rec["review_confidence"] = "kinda-sure"
        path = _write_jsonl(tmp_path / "cal.jsonl", [rec])
        issues, _ = cv.validate(path, repo_root=tmp_path, allow_verdict_in_case_id=True)
        assert any("review_confidence" in i and "high|medium|low" in i for i in issues)

    def test_invalid_annotation_date(self, tmp_path: Path) -> None:
        rec = _make_record("REAL-GAP", 1, canonical=True, section_6_7="W-EV-01")
        rec["annotation_date"] = "yesterday"
        path = _write_jsonl(tmp_path / "cal.jsonl", [rec])
        issues, _ = cv.validate(path, repo_root=tmp_path, allow_verdict_in_case_id=True)
        assert any("annotation_date" in i and "ISO" in i for i in issues)

    def test_missing_canonical_for_class(self, tmp_path: Path) -> None:
        # Full set, but one class has zero canonical few-shots (validator v2:
        # exactly 1 per class required).
        classes = [
            "CORRECT-DETECTION", "REAL-GAP", "GENERATOR-ARTIFACT",
            "EXISTING-RULE-MISBEHAVIOR", "OUT-OF-SCOPE", "UNCERTAIN",
        ]
        real_gap_mappings = ["W-EV-01", "W-EV-02", "W-REQ-01", "W-CX-01", "W-AR-06"]
        records = []
        idx = 1
        for cls in classes:
            for i in range(5):
                # Mark canonical for non-REAL-GAP classes only.
                canonical = (i == 0) and (cls != "REAL-GAP")
                extra = {}
                if cls == "REAL-GAP":
                    extra["section_6_7"] = real_gap_mappings[i]
                records.append(_make_record(cls, idx, canonical=canonical, **extra))
                idx += 1
        path = _write_jsonl(tmp_path / "cal.jsonl", records)
        issues, _ = cv.validate(path, repo_root=tmp_path, allow_verdict_in_case_id=True)
        assert any("REAL-GAP" in i and "is_canonical_few_shot" in i for i in issues)

    def test_invalid_json_line(self, tmp_path: Path) -> None:
        path = tmp_path / "cal.jsonl"
        path.write_text("not valid json\n")
        issues, _ = cv.validate(path, repo_root=tmp_path)
        assert any("invalid JSON" in i for i in issues)

    def test_empty_file(self, tmp_path: Path) -> None:
        path = tmp_path / "cal.jsonl"
        path.write_text("")
        issues, _ = cv.validate(path, repo_root=tmp_path)
        assert any("no records" in i for i in issues)

    def test_missing_package_path(self, tmp_path: Path) -> None:
        rec = _make_record("REAL-GAP", 1, canonical=True, section_6_7="W-EV-01")
        rec["package_path"] = "specs/calibration/packages/missing.jsonld"
        path = _write_jsonl(tmp_path / "cal.jsonl", [rec])
        issues, _ = cv.validate(path, repo_root=tmp_path, allow_verdict_in_case_id=True)
        assert any("package_path does not exist" in i for i in issues)

    def test_existing_package_path_passes(self, tmp_path: Path) -> None:
        # Create a real jsonld file at the referenced path.
        pkg_dir = tmp_path / "specs" / "calibration" / "packages"
        pkg_dir.mkdir(parents=True)
        pkg_path = pkg_dir / "p.jsonld"
        pkg_path.write_text(json.dumps({"@type": "EvidencePackage"}))

        rec = _make_record("REAL-GAP", 1, canonical=True, section_6_7="W-EV-01")
        rec["package_path"] = "specs/calibration/packages/p.jsonld"
        path = _write_jsonl(tmp_path / "cal.jsonl", [rec])
        issues, _ = cv.validate(path, repo_root=tmp_path, allow_verdict_in_case_id=True)
        assert not any("package_path does not exist" in i for i in issues)


# ── new v2 checks: REAL-GAP §6.7 mapping + coverage ────────────────────


class TestRealGapSection67Coverage:
    def test_real_gap_without_section_6_7_fails(self, tmp_path: Path) -> None:
        # REAL-GAP record without section_6_7_mapping fails Check 11.
        rec = _make_record("REAL-GAP", 1, canonical=True, section_6_7=None)
        path = _write_jsonl(tmp_path / "cal.jsonl", [rec])
        issues, _ = cv.validate(path, repo_root=tmp_path, allow_verdict_in_case_id=True)
        assert any("REAL-GAP" in i and "section_6_7_mapping" in i for i in issues)

    def test_section_6_7_coverage_below_threshold_fails(self, tmp_path: Path) -> None:
        # 5 REAL-GAP records all mapping to the SAME §6.7 candidate.
        # Coverage = 1 candidate; threshold is ≥4.
        classes = [
            "CORRECT-DETECTION", "REAL-GAP", "GENERATOR-ARTIFACT",
            "EXISTING-RULE-MISBEHAVIOR", "OUT-OF-SCOPE", "UNCERTAIN",
        ]
        records = []
        idx = 1
        for cls in classes:
            for i in range(5):
                extra = {"section_6_7": "W-EV-01"} if cls == "REAL-GAP" else {}
                records.append(_make_record(cls, idx, canonical=(i == 0), **extra))
                idx += 1
        path = _write_jsonl(tmp_path / "cal.jsonl", records)
        issues, _ = cv.validate(path, repo_root=tmp_path, allow_verdict_in_case_id=True)
        assert any("§6.7 coverage" in i for i in issues)


class TestSoftWarnings:
    def test_verdict_token_in_case_id_warns(self, tmp_path: Path) -> None:
        # case_id includes the verdict-class token; default mode warns (W1).
        rec = _make_record("REAL-GAP", 1, canonical=True, section_6_7="W-EV-01")
        path = _write_jsonl(tmp_path / "cal.jsonl", [rec])
        issues, warnings = cv.validate(path, repo_root=tmp_path)  # no allow flag
        # case_id contains 'real_gap' token (lowercased).
        assert any("verdict token" in w for w in warnings)

    def test_allow_verdict_in_case_id_silences_warning(self, tmp_path: Path) -> None:
        rec = _make_record("REAL-GAP", 1, canonical=True, section_6_7="W-EV-01")
        path = _write_jsonl(tmp_path / "cal.jsonl", [rec])
        _, warnings = cv.validate(path, repo_root=tmp_path, allow_verdict_in_case_id=True)
        assert not any("verdict token" in w for w in warnings)

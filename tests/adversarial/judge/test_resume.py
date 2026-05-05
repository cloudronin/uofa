"""Tests for the resume / idempotency module."""

from __future__ import annotations

import json
from pathlib import Path

from uofa_cli.adversarial.judge.resume import (
    compute_remaining_cases,
    load_done_case_ids,
    open_append_handles,
    write_resume_manifest,
)


class TestLoadDoneCaseIds:
    def test_returns_empty_for_missing_file(self, tmp_path: Path) -> None:
        assert load_done_case_ids(tmp_path / "nope.jsonl") == set()

    def test_reads_case_ids(self, tmp_path: Path) -> None:
        path = tmp_path / "j_a.jsonl"
        path.write_text("\n".join([
            json.dumps({"case_id": "c1", "verdict": "REAL-GAP"}),
            json.dumps({"case_id": "c2", "verdict": "GENERATOR-ARTIFACT"}),
        ]) + "\n")
        assert load_done_case_ids(path) == {"c1", "c2"}

    def test_skips_malformed_trailing_line(self, tmp_path: Path) -> None:
        # Simulates a SIGTERM mid-write: complete line followed by garbage.
        path = tmp_path / "j_a.jsonl"
        path.write_text(
            json.dumps({"case_id": "c1", "verdict": "REAL-GAP"}) + "\n"
            + "{partial-write-cut-mid"
        )
        assert load_done_case_ids(path) == {"c1"}

    def test_skips_blank_lines(self, tmp_path: Path) -> None:
        path = tmp_path / "j_a.jsonl"
        path.write_text(
            "\n\n"
            + json.dumps({"case_id": "c1", "verdict": "REAL-GAP"}) + "\n\n"
        )
        assert load_done_case_ids(path) == {"c1"}


class TestComputeRemainingCases:
    def test_no_done_returns_all(self) -> None:
        assert compute_remaining_cases(
            ["c1", "c2", "c3"], {}
        ) == ["c1", "c2", "c3"]

    def test_intersect_across_judges(self) -> None:
        # c1 done in all three judges → skip; c2 missing from B → re-judge.
        remaining = compute_remaining_cases(
            ["c1", "c2", "c3"],
            {"A": {"c1", "c2"}, "B": {"c1"}, "C": {"c1", "c2", "c3"}},
        )
        assert remaining == ["c2", "c3"]

    def test_all_done(self) -> None:
        remaining = compute_remaining_cases(
            ["c1", "c2"],
            {"A": {"c1", "c2"}, "B": {"c1", "c2"}, "C": {"c1", "c2"}},
        )
        assert remaining == []


class TestOpenAppendHandles:
    def test_creates_files_and_appends(self, tmp_path: Path) -> None:
        # Pre-existing file should be appended to, not truncated.
        existing = tmp_path / "judgments_A.jsonl"
        existing.write_text("EXISTING\n")
        handles = open_append_handles(tmp_path, ("A", "B", "C"))
        try:
            handles["A"].write("NEW\n")
            handles["B"].write("FIRST\n")
        finally:
            for h in handles.values():
                h.close()
        assert (tmp_path / "judgments_A.jsonl").read_text() == "EXISTING\nNEW\n"
        assert (tmp_path / "judgments_B.jsonl").read_text() == "FIRST\n"


class TestWriteResumeManifest:
    def test_writes_summary_json(self, tmp_path: Path) -> None:
        write_resume_manifest(
            out_dir=tmp_path,
            bundle_path=Path("/tmp/bundle.tgz"),
            total_case_count=100,
            skipped_case_count=40,
            judged_case_count=60,
        )
        data = json.loads((tmp_path / "resume_manifest.json").read_text())
        assert data["total_case_count"] == 100
        assert data["skipped_case_count_resumed_from_existing"] == 40
        assert data["judged_case_count_this_run"] == 60

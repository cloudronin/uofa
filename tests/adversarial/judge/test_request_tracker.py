"""Tests for RequestTracker — per-judge daily-cap with day-rollover."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from uofa_cli.adversarial.judge.request_tracker import (
    RequestTracker,
    parse_per_judge_cap,
)


class TestAuthorizeAndRecord:
    def test_uncapped_token_always_authorized(self) -> None:
        t = RequestTracker(per_judge_cap={"gemini": 5})
        # 'openai' has no cap → never blocks.
        for _ in range(100):
            assert t.authorize("openai") is True
            t.record("openai")
        assert t.per_judge_count["openai"] == 100
        assert t.over_cap is False

    def test_authorize_blocks_when_cap_hit(self) -> None:
        t = RequestTracker(per_judge_cap={"gemini": 3})
        for _ in range(3):
            assert t.authorize("gemini") is True
            t.record("gemini")
        # 4th call rejected.
        assert t.authorize("gemini") is False
        assert t.over_cap is True
        assert "gemini" in t.halt_reason and "3/3" in t.halt_reason

    def test_record_increments_after_failure_too(self) -> None:
        # Failures still burn quota (vendor counts the request).
        t = RequestTracker(per_judge_cap={"gemini": 2})
        t.record("gemini")  # success
        t.record("gemini")  # failure also recorded
        assert t.authorize("gemini") is False


class TestManifestRoundTrip:
    def test_write_then_read_same_day(self, tmp_path: Path) -> None:
        t = RequestTracker(per_judge_cap={"gemini": 950, "openai": 2000})
        t.record("gemini"); t.record("gemini"); t.record("openai")
        path = tmp_path / "request_manifest.json"
        t.write_manifest(path)

        data = json.loads(path.read_text())
        assert data["per_judge_count"] == {"gemini": 2, "openai": 1}
        assert data["per_judge_cap"] == {"gemini": 950, "openai": 2000}
        assert data["halted"] is False

    def test_resume_same_day_accumulates(self, tmp_path: Path) -> None:
        path = tmp_path / "request_manifest.json"
        t1 = RequestTracker(per_judge_cap={"gemini": 950})
        for _ in range(900):
            t1.record("gemini")
        t1.write_manifest(path)

        # Resume same UTC day → counts carry over.
        t2 = RequestTracker.from_manifest(path, per_judge_cap={"gemini": 950})
        assert t2.per_judge_count["gemini"] == 900
        # 50 more authorized, then halt.
        for _ in range(50):
            assert t2.authorize("gemini") is True
            t2.record("gemini")
        assert t2.authorize("gemini") is False

    def test_resume_different_day_resets_counts(self, tmp_path: Path) -> None:
        path = tmp_path / "request_manifest.json"
        # Write a manifest stamped yesterday.
        path.write_text(json.dumps({
            "date": "2026-05-04",  # arbitrary earlier date
            "per_judge_cap": {"gemini": 950},
            "per_judge_count": {"gemini": 950},
            "halted": True,
            "halt_reason": "yesterday's halt",
        }))

        # `_utc_today()` returns the current UTC date — patch it to a
        # later date so we test the day-rollover branch deterministically.
        with patch(
            "uofa_cli.adversarial.judge.request_tracker._utc_today",
            return_value="2026-05-05",
        ):
            t = RequestTracker.from_manifest(
                path, per_judge_cap={"gemini": 950}
            )
        assert t.per_judge_count == {}  # reset
        assert t.halted is False
        assert t.authorize("gemini") is True

    def test_missing_manifest_returns_fresh_tracker(self, tmp_path: Path) -> None:
        t = RequestTracker.from_manifest(
            tmp_path / "nope.json", per_judge_cap={"gemini": 5}
        )
        assert t.per_judge_count == {}
        assert t.authorize("gemini") is True

    def test_corrupted_manifest_returns_fresh_tracker(self, tmp_path: Path) -> None:
        path = tmp_path / "manifest.json"
        path.write_text("{not-valid-json")
        t = RequestTracker.from_manifest(path, per_judge_cap={"gemini": 5})
        assert t.per_judge_count == {}


class TestParsePerJudgeCap:
    def test_basic(self) -> None:
        assert parse_per_judge_cap("gemini=950,openai=2000") == {
            "gemini": 950, "openai": 2000,
        }

    def test_empty_input(self) -> None:
        assert parse_per_judge_cap(None) == {}
        assert parse_per_judge_cap("") == {}

    def test_whitespace_tolerated(self) -> None:
        assert parse_per_judge_cap(" gemini = 950 , openai=2000 ") == {
            "gemini": 950, "openai": 2000,
        }

    def test_bad_value_raises(self) -> None:
        with pytest.raises(ValueError, match="bad value"):
            parse_per_judge_cap("gemini=notanumber")

    def test_skips_malformed_pairs(self) -> None:
        # Pairs without '=' are silently skipped (forgiving parser).
        assert parse_per_judge_cap("gemini=950,garbage,openai=2000") == {
            "gemini": 950, "openai": 2000,
        }

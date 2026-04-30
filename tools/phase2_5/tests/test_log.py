"""Unit tests for tools.phase2_5.log."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.phase2_5.refinement_loop.log import (
    IterationRecord,
    RefinementLog,
    extract_rule_body,
    predicate_sha,
    write_predicate_diff,
)


def test_predicate_sha_stable():
    assert predicate_sha("foo") == predicate_sha("foo")
    assert predicate_sha("foo") != predicate_sha("bar")
    assert predicate_sha("foo").startswith("sha256:")


def test_iteration_record_roundtrip():
    rec = IterationRecord(
        rule_id="W-EP-01", iteration=1, timestamp="2026-04-27T00:00:00Z",
        proposed_by="claude_code", review_decision="accepted-auto",
        predicate_before_sha="sha256:abc", predicate_after_sha="sha256:def",
        predicate_diff_path="/tmp/diff.diff", rationale="test",
        train_metrics={"recall": 0.9}, dev_metrics={"recall": 0.85},
        decision="accepted-auto", git_sha="abc1234",
    )
    line = rec.to_jsonl()
    parsed = json.loads(line)
    assert parsed["rule_id"] == "W-EP-01"
    assert parsed["iteration"] == 1
    assert parsed["holdout_metrics"] is None


def test_refinement_log_append_and_read(tmp_path: Path):
    log_path = tmp_path / "refinement_log.jsonl"
    log = RefinementLog(log_path)
    rec = IterationRecord(
        rule_id="W-EP-01", iteration=1, timestamp="2026-04-27T00:00:00Z",
        proposed_by="claude_code", review_decision="accepted-auto",
        predicate_before_sha="sha256:abc", predicate_after_sha="sha256:def",
        predicate_diff_path="/tmp/x.diff", rationale="test",
        train_metrics={}, dev_metrics={},
        decision="accepted-auto", git_sha="abc1234",
    )
    log.append(rec)
    log.append(rec)
    assert len(log.read_all()) == 2
    assert log.latest_iteration("W-EP-01") == 1
    assert log.latest_iteration("W-XX-99") == 0


def test_refinement_log_records_for_rule(tmp_path: Path):
    log_path = tmp_path / "refinement_log.jsonl"
    log = RefinementLog(log_path)
    for rid in ("W-EP-01", "W-ON-02", "W-EP-01"):
        log.append(IterationRecord(
            rule_id=rid, iteration=1, timestamp="2026-04-27T00:00:00Z",
            proposed_by="claude_code", review_decision="accepted-auto",
            predicate_before_sha="x", predicate_after_sha="y",
            predicate_diff_path="z", rationale="r",
            train_metrics={}, dev_metrics={},
            decision="accepted-auto", git_sha="abc",
        ))
    assert len(log.records_for_rule("W-EP-01")) == 2
    assert len(log.records_for_rule("W-ON-02")) == 1


def test_write_predicate_diff(tmp_path: Path):
    p = write_predicate_diff("--- a\n+++ b\n", tmp_path, "W-EP-01", 3)
    assert p.exists()
    assert p.name == "w_ep_01_iter03.diff"
    assert "+++ b" in p.read_text()


def test_extract_rule_body(tmp_path: Path):
    rules = tmp_path / "test.rules"
    rules.write_text(
        """\
@prefix uofa: <http://example.com/uofa#>.

[w_ep01: (?x rdf:type uofa:Foo) -> (?x uofa:fired "true") ]

[w_on02: (?x rdf:type uofa:Bar) (?y rdf:type uofa:Baz)
        -> (?x uofa:other "true") ]
"""
    )
    body1 = extract_rule_body(rules, "w_ep01")
    assert body1.startswith("[w_ep01:")
    assert body1.endswith("]")
    assert "uofa:Foo" in body1

    body2 = extract_rule_body(rules, "w_on02")
    assert body2.startswith("[w_on02:")
    assert "uofa:Baz" in body2

    with pytest.raises(ValueError):
        extract_rule_body(rules, "does_not_exist")

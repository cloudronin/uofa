"""S4 lead-capture tests — privacy of the record + the no-silent-loss policy."""

from __future__ import annotations

import json

from space import leadcapture
from space.leadcapture import build_record, capture_lead

_SUMMARY = {"completeness": {"n_assessed": 11, "n_expected": 13}, "weakeners": [{"patternId": "W-AL-02"}]}


def test_record_contains_no_evidence_content():
    rec = build_record("user@org.com", "vv40", _SUMMARY, now="2026-06-23T00:00:00Z")
    assert set(rec) == {"email", "timestamp", "pack", "x_of_n", "weakener_count"}
    assert rec["x_of_n"] == "11/13"
    assert rec["weakener_count"] == 1
    # No free text / factor content leaks into the lead.
    assert "rationale" not in rec and "acceptance_criteria" not in rec


def test_invalid_email_rejected_without_storing():
    calls = []
    out = capture_lead("nope", push=lambda r: calls.append(r), fallback=lambda r: calls.append(r))
    assert not out.accepted
    assert out.sink == "invalid"
    assert calls == []  # nothing stored for an invalid email


def test_success_path_uses_dataset():
    pushed = []
    out = capture_lead("user@org.com", pack="vv40", summary=_SUMMARY, push=pushed.append)
    assert out.accepted and out.sink == "dataset"
    assert pushed and pushed[0]["email"] == "user@org.com"


def test_retries_then_falls_back_without_blocking():
    attempts = {"n": 0}

    def flaky_push(_rec):
        attempts["n"] += 1
        raise RuntimeError("network down")

    fell_back = []
    out = capture_lead(
        "user@org.com", summary=_SUMMARY,
        push=flaky_push, fallback=lambda r: (fell_back.append(r), "fallback")[1],
        retries=2, sleep=lambda _s: None,
    )
    assert attempts["n"] == 3            # initial + 2 retries
    assert len(fell_back) == 1           # lead not lost
    assert out.accepted is True          # unlock NOT blocked by sink failure
    assert out.sink == "fallback"


def test_fallback_writes_jsonl(tmp_path, monkeypatch):
    monkeypatch.setenv("LEAD_FALLBACK_PATH", str(tmp_path / "leads.jsonl"))

    def boom(_rec):
        raise RuntimeError("down")

    out = capture_lead("user@org.com", summary=_SUMMARY, push=boom,
                       retries=0, sleep=lambda _s: None)
    assert out.accepted and out.sink == "fallback"
    lines = (tmp_path / "leads.jsonl").read_text().strip().splitlines()
    assert json.loads(lines[0])["email"] == "user@org.com"


def test_unconfigured_dataset_raises_then_falls_back(tmp_path, monkeypatch):
    """The real _push_to_dataset raises when HF env is unset -> fallback engages."""
    monkeypatch.delenv("HF_DATASET_REPO", raising=False)
    monkeypatch.delenv("HF_TOKEN", raising=False)
    monkeypatch.setenv("LEAD_FALLBACK_PATH", str(tmp_path / "leads.jsonl"))
    out = capture_lead("user@org.com", summary=_SUMMARY, retries=0, sleep=lambda _s: None)
    assert out.accepted and out.sink in ("fallback", "fallback-log")

"""Tests for the standalone `uofa explain --from-file/--from-stdin` command
(spec v0.4 §3.3).

Covers:
- Input-type auto-detection from JSON shape (envelope + raw structured forms)
- Per-input-type routing (each maps to the right interpret_*_output)
- File vs stdin sources
- --input-type override
- Graceful error paths (bad JSON, undetectable shape, missing file)
"""

from __future__ import annotations

import argparse
import io
import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from uofa_cli.commands import explain as explain_cmd
from uofa_cli.commands.explain import _detect_input_type
from uofa_cli.llm import MockBackend


def _build_args(**fields) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    explain_cmd.add_arguments(parser)
    defaults = {a.dest: a.default for a in parser._actions if a.dest != "help"}
    # Fill in --pack global flag default that the parent parser supplies
    defaults.setdefault("pack", None)
    return argparse.Namespace(**{**defaults, **fields})


def _canned_explanation() -> str:
    """v0.4.0 three-field schema (no confidence)."""
    return json.dumps({
        "patternId": "MOCK", "severity": "High",
        "affected_evidence_summary": "Mock affected evidence.",
        "gap_description": "Standalone-mock explanation.",
        "relevance_to_cou": "Mock relevance.",
    })


@pytest.fixture
def mock_backend(monkeypatch):
    backend = MockBackend(default_response=_canned_explanation())
    monkeypatch.setattr("uofa_cli.llm.get_backend", lambda *a, **kw: backend)
    return backend


# ── Auto-detection ────────────────────────────────────────


class TestAutoDetection:
    def test_envelope_with_command_field_wins(self):
        """Top-level `command` field is the most specific signal."""
        for cmd in ("rules", "check", "diff", "shacl"):
            assert _detect_input_type({"command": cmd, "structured_output": {}}) == cmd

    def test_diff_shape_detected(self):
        assert _detect_input_type({"only_a": ["W-AR-02"], "only_b": []}) == "diff"
        assert _detect_input_type({"divergence_count": 3}) == "diff"

    def test_check_shape_detected(self):
        assert _detect_input_type({"shacl": {}, "rules": {}}) == "check"

    def test_shacl_shape_detected(self):
        assert _detect_input_type({"violations": [], "conforms": True}) == "shacl"

    def test_rules_shape_detected(self):
        assert _detect_input_type({"firings": []}) == "rules"

    def test_envelope_unwraps_for_shape_detection(self):
        """When the data is a full envelope, we sniff the structured_output."""
        env = {"structured_output": {"firings": [{"patternId": "X"}]}}
        assert _detect_input_type(env) == "rules"

    def test_undetectable_returns_none(self):
        assert _detect_input_type({"random": "stuff"}) is None
        assert _detect_input_type({}) is None

    def test_non_dict_returns_none(self):
        assert _detect_input_type([{"firings": []}]) is None
        assert _detect_input_type("not a dict") is None

    def test_diff_has_priority_over_other_shape_keys(self):
        """If a payload happens to have both `firings` and `only_a`, diff wins
        (they don't normally co-occur, but be deterministic)."""
        assert _detect_input_type({"only_a": ["X"], "firings": []}) == "diff"


# ── Per-input-type routing ────────────────────────────────


class TestRouting:
    def test_rules_routes_to_interpret_rules(self, mock_backend, tmp_path):
        f = tmp_path / "rules.json"
        f.write_text(json.dumps({
            "command": "rules",
            "structured_output": {
                "firings": [{"patternId": "W-EP-04", "severity": "High", "hits": 6}],
            },
        }))
        rc = explain_cmd.run(_build_args(from_file=f))
        assert rc == 0
        # MockBackend was called for the one firing
        assert any(c[0] in ("generate", "generate_structured") for c in mock_backend.calls)

    def test_shacl_routes_to_interpret_shacl(self, mock_backend, tmp_path):
        f = tmp_path / "shacl.json"
        f.write_text(json.dumps({
            "command": "shacl",
            "structured_output": {
                "violations": [{"path": "uofa:hasContextOfUse", "severity": "High"}],
                "conforms": False,
            },
        }))
        rc = explain_cmd.run(_build_args(from_file=f))
        assert rc == 0

    def test_diff_routes_to_interpret_diff(self, mock_backend, tmp_path):
        f = tmp_path / "diff.json"
        f.write_text(json.dumps({
            "command": "diff",
            "structured_output": {
                "only_a": ["W-AR-02"],
                "only_b": [],
                "weakeners_a": [{"patternId": "W-AR-02", "severity": "High"}],
                "weakeners_b": [],
                "cou_identity_a": {"cou_name": "A"},
                "cou_identity_b": {"cou_name": "B"},
            },
        }))
        rc = explain_cmd.run(_build_args(from_file=f))
        assert rc == 0

    def test_check_routes_to_interpret_check(self, mock_backend, tmp_path):
        f = tmp_path / "check.json"
        f.write_text(json.dumps({
            "command": "check",
            "structured_output": {
                "shacl": {"violations": [], "conforms": True},
                "rules": {"firings": [{"patternId": "W-EP-04", "severity": "High", "hits": 1}]},
            },
        }))
        rc = explain_cmd.run(_build_args(from_file=f))
        assert rc == 0


# ── --input-type override ─────────────────────────────────


class TestInputTypeOverride:
    def test_explicit_override_used(self, mock_backend, tmp_path):
        """Even when shape detection would say one type, --input-type wins."""
        f = tmp_path / "ambiguous.json"
        f.write_text(json.dumps({"firings": []}))  # would auto-detect as rules
        rc = explain_cmd.run(_build_args(from_file=f, input_type="shacl"))
        assert rc == 0


# ── Source: stdin ─────────────────────────────────────────


class TestFromStdin:
    def test_reads_envelope_from_stdin(self, mock_backend, monkeypatch):
        envelope = json.dumps({
            "command": "rules",
            "structured_output": {"firings": [{"patternId": "W-X", "severity": "Low", "hits": 1}]},
        })
        monkeypatch.setattr(sys, "stdin", io.StringIO(envelope))
        rc = explain_cmd.run(_build_args(from_stdin=True, from_file=None))
        assert rc == 0


# ── Error paths ───────────────────────────────────────────


class TestErrors:
    def test_missing_file_returns_1(self, capsys, tmp_path):
        rc = explain_cmd.run(_build_args(from_file=tmp_path / "nope.json"))
        assert rc == 1
        captured = capsys.readouterr()
        assert "Could not read input" in captured.out + captured.err

    def test_invalid_json_returns_1(self, capsys, tmp_path):
        f = tmp_path / "bad.json"
        f.write_text("not { valid json")
        rc = explain_cmd.run(_build_args(from_file=f))
        assert rc == 1
        captured = capsys.readouterr()
        assert "not valid JSON" in captured.out + captured.err

    def test_undetectable_input_type_returns_1(self, capsys, tmp_path):
        f = tmp_path / "weird.json"
        f.write_text(json.dumps({"random_key": "no shape signals"}))
        rc = explain_cmd.run(_build_args(from_file=f))
        assert rc == 1
        captured = capsys.readouterr()
        assert "Could not detect input type" in captured.out + captured.err


# ── --format json round-trip ──────────────────────────────


class TestJsonFormat:
    def test_envelope_round_trips(self, mock_backend, capsys, tmp_path):
        """Pipe `uofa rules --explain --explain-format json` output back into
        `uofa explain --from-file --format json` and the result is a
        well-formed envelope. Restrict to `--functions explain` so the
        test isn't sensitive to the v0.6.0 function set (group, etc.
        also run by default and aren't the focus here)."""
        f = tmp_path / "rules.json"
        f.write_text(json.dumps({
            "command": "rules",
            "structured_output": {
                "firings": [{"patternId": "W-EP-04", "severity": "High", "hits": 1}],
            },
        }))
        rc = explain_cmd.run(_build_args(from_file=f, format="json", functions="explain"))
        assert rc == 0
        out = capsys.readouterr().out
        envelope = json.loads(out.strip())
        assert envelope["command"] == "rules"
        assert "interpretation" in envelope
        assert envelope["interpretation"]["functions_run"] == ["explain"]

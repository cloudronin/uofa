"""Integration tests for the `--explain` flag on rules / check / diff / shacl.

Tests the wiring between argparse → command.run() → interpretation pipeline.
Uses MockBackend (in-process, no network) so the suite stays hermetic and
fast. End-to-end verification against real Ollama is in the dev/tools/
sample-generation script (out of CI scope).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from uofa_cli.commands import check, diff, rules, shacl
from uofa_cli.llm import MockBackend


REPO_ROOT = Path(__file__).parent.parent
MORRISON_COU1 = REPO_ROOT / "packs" / "vv40" / "examples" / "morrison" / "cou1" / "uofa-morrison-cou1.jsonld"
MORRISON_COU2 = REPO_ROOT / "packs" / "vv40" / "examples" / "morrison" / "cou2" / "uofa-morrison-cou2.jsonld"
CONTEXT_FILE = str(REPO_ROOT / "spec" / "context" / "v0.5.jsonld")


def _write_shacl_failing_jsonld(path: Path) -> Path:
    """Build a minimal but well-formed JSON-LD file that fails SHACL.

    Same shape as `tests/test_integration.py::test_shacl_invalid_file_fails`
    — has the right @context / id / type but is missing required UofA
    properties (hasContextOfUse, hasDecisionRecord, etc.) so SHACL emits
    violations. We need a JSON-LD parser-valid file (otherwise we hit a
    parse error, not a SHACL violation) that still fails the shapes.
    """
    path.write_text(json.dumps({
        "@context": CONTEXT_FILE,
        "id": "https://example.org/bad",
        "type": "UnitOfAssurance",
        "conformsToProfile": "https://uofa.net/vocab#ProfileMinimal",
    }))
    return path

pytestmark = pytest.mark.skipif(
    not MORRISON_COU1.exists(),
    reason="Morrison fixture not available",
)


def _build_args(add_arguments_fn, **overrides) -> argparse.Namespace:
    """Build an args Namespace from a command's add_arguments() function.

    Walks the argparse parser to pick up every option's default — so tests
    don't break when a new flag is added to add_arguments() upstream.
    """
    parser = argparse.ArgumentParser()
    add_arguments_fn(parser)
    defaults = {a.dest: a.default for a in parser._actions if a.dest != "help"}
    return argparse.Namespace(**{**defaults, **overrides})


def _canned_explanation_response() -> str:
    """v0.4.0 three-field schema (no confidence)."""
    return json.dumps({
        "patternId": "MOCK",
        "severity": "High",
        "affected_evidence_summary": "Mock affected evidence summary.",
        "gap_description": "Mock explanation produced by the test backend.",
        "relevance_to_cou": "Mock relevance.",
    })


@pytest.fixture
def mock_backend(monkeypatch):
    """Replace `get_backend()` everywhere — even when InterpretationOptions
    auto-resolves a backend, it lands on this mock."""
    backend = MockBackend(default_response=_canned_explanation_response())
    monkeypatch.setattr("uofa_cli.llm.get_backend", lambda *a, **kw: backend)
    return backend


# ── shacl --explain ────────────────────────────────────────


class TestShaclExplain:
    def test_skipped_when_package_conforms(self, mock_backend, capsys):
        """No violations → no interpretation work (would be empty anyway)."""
        args = _build_args(shacl.add_arguments, file=MORRISON_COU1, explain=True)
        rc = shacl.run(args)
        assert rc == 0
        captured = capsys.readouterr()
        # No interpretation block was printed because conforms=True
        assert "══ Interpretation ══" not in captured.out

    def test_explain_runs_when_violations_present(self, mock_backend, capsys, tmp_path):
        """A SHACL-failing package triggers the explain pipeline. Even
        though P-K (shacl-specific explain function) isn't registered
        yet, the interpretation block is printed so consumers can see
        the pipeline ran."""
        bad = _write_shacl_failing_jsonld(tmp_path / "bad.jsonld")
        args = _build_args(shacl.add_arguments, file=bad, explain=True)
        rc = shacl.run(args)
        assert rc == 1  # SHACL failed
        captured = capsys.readouterr()
        assert "══ Interpretation ══" in captured.out


# ── diff --explain ─────────────────────────────────────────


class TestDiffExplain:
    def test_skipped_when_no_divergence(self, mock_backend, capsys):
        """No divergent patterns → no interpretation work."""
        args = _build_args(
            diff.add_arguments,
            file_a=MORRISON_COU1, file_b=MORRISON_COU1,  # identical
            skip_rules=True,
            explain=True,
        )
        rc = diff.run(args)
        assert rc == 0
        captured = capsys.readouterr()
        assert "══ Interpretation ══" not in captured.out


# ── rules --explain ────────────────────────────────────────


class TestRulesExplain:
    """rules tests need the Java engine. Skipped if not available."""

    def _has_java(self) -> bool:
        try:
            from uofa_cli.commands.rules import _ensure_java
            _ensure_java()
            return True
        except Exception:  # noqa: BLE001
            return False

    def test_explain_block_printed(self, mock_backend, capsys):
        if not self._has_java():
            pytest.skip("Java not available")
        args = _build_args(
            rules.add_arguments,
            file=MORRISON_COU1, explain=True, explain_max_items=1,
        )
        rc = rules.run(args)
        captured = capsys.readouterr()
        # Returncode is 0 even though firings exist (rules engine emits
        # firings as a normal report, not an error)
        assert rc == 0
        # Interpretation block printed
        assert "══ Interpretation ══" in captured.out
        # MockBackend's canned response (Round 1: in gap_description field) shows up
        assert "Mock explanation produced by the test backend." in captured.out


# ── --explain-format json ──────────────────────────────────


class TestExplainFormat:
    def test_json_format_emits_envelope(self, mock_backend, capsys, tmp_path):
        """--explain-format json should emit the spec §4.5 envelope as JSON."""
        bad = _write_shacl_failing_jsonld(tmp_path / "bad.jsonld")
        args = _build_args(
            shacl.add_arguments, file=bad, explain=True, explain_format="json",
        )
        shacl.run(args)
        captured = capsys.readouterr()
        # The friendly text comes first, then the JSON envelope — find the
        # last `{` that starts a complete top-level object.
        out = captured.out
        json_start = out.rfind('{\n  "command":')
        if json_start == -1:
            pytest.fail(f"No JSON envelope found in output:\n{out[-500:]}")
        envelope = json.loads(out[json_start:].strip())
        assert envelope["command"] == "shacl"
        assert "interpretation" in envelope


# ── --explain-functions filter ─────────────────────────────


class TestExplainFunctionsFilter:
    def test_invalid_function_name_raises(self, mock_backend, tmp_path):
        bad = _write_shacl_failing_jsonld(tmp_path / "bad.jsonld")
        args = _build_args(
            shacl.add_arguments, file=bad, explain=True,
            explain_functions="not-a-real-function",
        )
        # The dispatcher rejects the unknown name. Currently this raises
        # ValueError up to the run() shell — Phase 14 caching/UX polish
        # should catch + degrade. For now we just assert it doesn't
        # silently swallow the error.
        with pytest.raises(ValueError, match="Unknown interpretation functions"):
            shacl.run(args)


# ── help text contains the new flags ──────────────────────


class TestHelpText:
    @pytest.mark.parametrize("module", [rules, check, diff, shacl])
    def test_help_includes_explain_flags(self, module):
        parser = argparse.ArgumentParser()
        module.add_arguments(parser)
        help_text = parser.format_help()
        for flag in ("--explain", "--explain-functions", "--explain-format",
                     "--explain-backend", "--explain-model", "--explain-max-items"):
            assert flag in help_text, f"{module.__name__} missing {flag} in --help"

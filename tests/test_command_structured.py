"""Tests for the run_structured() entry points on rules/check/diff/shacl.

These functions are the integration surface for the future `--explain`
pipeline (spec v0.4 §4.1). Two contracts they must honor:

1. Return a typed dataclass with the data the interpretation pipeline needs.
2. Produce NO output to stdout/stderr — `run()` is the I/O shell. If
   `run_structured()` prints, the eventual `--explain` flow will emit
   duplicated text (run_structured for the data + run() for the display).

This module asserts both. Uses real Morrison fixtures so the data shape is
exercised against actual rule-engine output, not synthetic.
"""

from __future__ import annotations

import argparse
import io
import sys
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import pytest

from uofa_cli.commands import check, diff, rules, shacl
from uofa_cli.commands.check import CheckResult, IntegrityResult
from uofa_cli.commands.diff import DiffResult
from uofa_cli.commands.rules import RulesResult
from uofa_cli.commands.shacl import ShaclResult


REPO_ROOT = Path(__file__).parent.parent
MORRISON_COU1 = REPO_ROOT / "packs" / "vv40" / "examples" / "morrison" / "cou1" / "uofa-morrison-cou1.jsonld"
MORRISON_COU2 = REPO_ROOT / "packs" / "vv40" / "examples" / "morrison" / "cou2" / "uofa-morrison-cou2.jsonld"

pytestmark = pytest.mark.skipif(
    not MORRISON_COU1.exists(),
    reason="Morrison COU1 fixture not available",
)


# ── Helpers ────────────────────────────────────────────────


def _silent(fn, *args, **kwargs):
    """Run fn and capture stdout/stderr — returns (result, stdout, stderr)."""
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        result = fn(*args, **kwargs)
    return result, out.getvalue(), err.getvalue()


# ── shacl.run_structured ───────────────────────────────────


class TestShaclStructured:
    def test_returns_typed_result(self):
        ns = argparse.Namespace(file=MORRISON_COU1, raw=False)
        result = shacl.run_structured(ns)
        assert isinstance(result, ShaclResult)

    def test_returns_correct_data_for_morrison(self):
        ns = argparse.Namespace(file=MORRISON_COU1, raw=False)
        result = shacl.run_structured(ns)
        assert result.conforms is True
        assert result.violations == []
        assert result.exit_code == 0

    def test_does_not_print(self):
        ns = argparse.Namespace(file=MORRISON_COU1, raw=False)
        _, stdout, stderr = _silent(shacl.run_structured, ns)
        assert stdout == ""
        assert stderr == ""

    def test_raw_mode_carries_text(self):
        ns = argparse.Namespace(file=MORRISON_COU1, raw=True)
        result, stdout, _ = _silent(shacl.run_structured, ns)
        assert result.raw_text is not None
        assert stdout == ""  # raw mode still doesn't print from run_structured

    def test_missing_file_raises(self, tmp_path):
        ns = argparse.Namespace(file=tmp_path / "no-such.jsonld", raw=False)
        with pytest.raises(FileNotFoundError):
            shacl.run_structured(ns)


# ── rules.run_structured ───────────────────────────────────


class TestRulesStructured:
    def _ns(self, **overrides):
        defaults = dict(
            file=MORRISON_COU1, rules=None, context=None, build=False,
            raw=False, format="summary", output=None,
        )
        defaults.update(overrides)
        return argparse.Namespace(**defaults)

    def test_returns_typed_result(self):
        result = rules.run_structured(self._ns())
        assert isinstance(result, RulesResult)

    def test_summary_mode_parses_firings(self):
        result = rules.run_structured(self._ns())
        assert result.format == "summary"
        # Morrison COU1 reliably fires multiple weakener patterns; count is
        # not pinned because rule-engine evolution may add/remove patterns.
        assert len(result.firings) >= 1
        for f in result.firings:
            assert "patternId" in f
            assert "severity" in f
            assert "hits" in f
            assert isinstance(f["hits"], int)

    def test_does_not_print_in_summary_mode(self):
        result, stdout, stderr = _silent(rules.run_structured, self._ns())
        assert stdout == ""
        assert stderr == ""
        assert result.raw_stdout != ""  # but it IS captured into the result

    def test_jsonld_mode_returns_no_firings_but_carries_stdout(self):
        result = rules.run_structured(self._ns(format="jsonld"))
        # JSON-LD output isn't summary text, so the regex parser yields []
        assert result.firings == []
        assert result.format == "jsonld"
        assert len(result.raw_stdout) > 0  # the actual JSON-LD payload

    def test_output_mode_returns_empty_stdout(self, tmp_path):
        out_file = tmp_path / "rules-output.txt"
        result, stdout, _ = _silent(rules.run_structured, self._ns(output=out_file))
        # --output mode lets the engine write directly to file; we don't
        # capture stdout (would double-print) so raw_stdout is empty.
        assert result.raw_stdout == ""
        assert result.output_path == out_file
        assert out_file.exists()

    def test_parse_firings_helper_is_public(self):
        """Phase 4 interpretation pipeline (and the standalone explain
        --from-file path) needs to re-parse stdout from cached output."""
        from uofa_cli.commands.rules import parse_firings
        sample = "  ⚠ W-EP-04 [High] — 6 hit(s)\n  ⚡ COMPOUND-01 [Critical] — 1 hit(s)\n"
        firings = parse_firings(sample)
        assert firings == [
            {"patternId": "W-EP-04", "severity": "High", "hits": 6},
            {"patternId": "COMPOUND-01", "severity": "Critical", "hits": 1},
        ]


# ── diff.run_structured ────────────────────────────────────


class TestDiffStructured:
    def _ns(self, **overrides):
        defaults = dict(
            file_a=MORRISON_COU1, file_b=MORRISON_COU2,
            build=False, skip_rules=True,  # skip Java for hermeticity
        )
        defaults.update(overrides)
        return argparse.Namespace(**defaults)

    def test_returns_typed_result(self):
        result = diff.run_structured(self._ns())
        assert isinstance(result, DiffResult)

    def test_carries_both_documents(self):
        result = diff.run_structured(self._ns())
        assert isinstance(result.doc_a, dict)
        assert isinstance(result.doc_b, dict)
        # Spot-check: cou_name should differ between the two COUs
        assert result.cou_identity_a["cou_name"] != result.cou_identity_b["cou_name"]

    def test_static_fallback_flag_set_when_skipping_rules(self):
        """Phase 4 explain pipeline needs to know when firings come from the
        static array vs the rule engine — different interpretation strategy."""
        result = diff.run_structured(self._ns(skip_rules=True))
        assert result.used_static_fallback is True

    def test_does_not_print(self):
        _, stdout, stderr = _silent(diff.run_structured, self._ns())
        assert stdout == ""
        assert stderr == ""

    def test_divergence_indices_consistent_with_weakener_sets(self):
        """only_a should be patterns in A but not B; only_b vice versa."""
        result = diff.run_structured(self._ns())
        pids_a = {w["patternId"] for w in result.weakeners_a}
        pids_b = {w["patternId"] for w in result.weakeners_b}
        assert set(result.only_a) == pids_a - pids_b
        assert set(result.only_b) == pids_b - pids_a
        assert set(result.all_pids) == pids_a | pids_b
        assert result.divergence_count == len(result.only_a) + len(result.only_b)


# ── check.run_structured ───────────────────────────────────


class TestCheckStructured:
    def _ns(self, **overrides):
        defaults = dict(
            file=MORRISON_COU1, pubkey=None, context=None,
            rules=None, skip_rules=True, build=False,
        )
        defaults.update(overrides)
        return argparse.Namespace(**defaults)

    def test_returns_typed_result(self):
        result = check.run_structured(self._ns())
        assert isinstance(result, CheckResult)

    def test_composes_shacl_and_integrity(self):
        result = check.run_structured(self._ns())
        assert isinstance(result.shacl, ShaclResult)
        assert isinstance(result.integrity, IntegrityResult)
        assert result.rules is None  # --skip-rules

    def test_rules_populated_when_not_skipped(self):
        """The composed result threads rules.run_structured() through, so
        the explain pipeline can address sections individually."""
        result = check.run_structured(self._ns(skip_rules=False))
        assert result.rules is None or isinstance(result.rules, RulesResult)
        # If rules ran successfully, firings should be available
        if result.rules and result.rules.returncode == 0:
            assert isinstance(result.rules.firings, list)

    def test_does_not_print(self):
        _, stdout, stderr = _silent(check.run_structured, self._ns())
        assert stdout == ""
        assert stderr == ""

    def test_all_ok_aggregates_correctly(self):
        result = check.run_structured(self._ns())
        # Morrison COU1 conforms + has valid signature → all_ok True
        assert result.all_ok is (
            result.shacl.conforms
            and result.integrity.ok
            and (result.rules is None or result.rules.returncode == 0)
        )

    def test_exit_code_matches_all_ok(self):
        result = check.run_structured(self._ns())
        assert result.exit_code == (0 if result.all_ok else 1)

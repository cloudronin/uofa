"""OOS Backward-Chaining Substrate Validation Test — Python harness.

Drives the Java entry point (`net.uofa.OOSSubstrateTest`) per
PRD UofA_OOS_Substrate_Validation_Test_v0_1.md §3.3 and writes the structured
test report to a per-test pytest ``tmp_path``. The committed snapshot at
``tests/substrate/oos_backward_substrate_test_report.json`` is a separate,
decision-relevant artifact (see ``docs/decisions/2026-05-05-oos-substrate.md``)
and is NOT touched by these tests.

Per PRD §5, individual property failures are *expected* outcomes (Outcome 2 or
3), not test errors — the harness asserts the test ran to completion and the
report is well-formed; it does NOT assert overall_pass=true. The disposition
session reads the report to decide path one vs. path two.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest


def _run_substrate_test(
    java_exe: str,
    jar: Path,
    paths: dict,
    report_path: Path,
    mode: str = "full",
) -> dict:
    """Invoke the substrate-test entry point and return the parsed JSON report.

    Post-T4: the unified engine JAR dispatches by first-arg subcommand
    (see net.uofa.Engine). The ``substrate-test`` subcommand routes to
    OOSSubstrateTest.

    ``report_path`` is where the JAR writes its structured report; tests pass
    in a pytest ``tmp_path``-derived location so runs don't mutate the
    committed snapshot in tests/substrate/.
    """
    cmd = [
        java_exe,
        "-jar",
        str(jar),
        "substrate-test",
        "--mode",
        mode,
        "--cal-021-path",
        str(paths["cal_021_path"]),
        "--c3-rules-path",
        str(paths["c3_rules_path"]),
        "--oos-rule-path",
        str(paths["oos_rule_path"]),
        "--vocab-path",
        str(paths["vocab_path"]),
        "--context-path",
        str(paths["context_path"]),
        "--report-path",
        str(report_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    assert result.returncode == 0, (
        f"Substrate test JAR exited non-zero ({result.returncode}).\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
    assert report_path.exists(), "Report file was not written"
    return json.loads(report_path.read_text())


def test_substrate_full_run_emits_well_formed_report(java_executable, substrate_jar, substrate_paths, substrate_report_path):
    """End-to-end: run full mode, verify report has all expected sections."""
    report = _run_substrate_test(java_executable, substrate_jar, substrate_paths, substrate_report_path)

    # Top-level metadata
    assert report["test_id"] == "substrate_validation_v0.1"
    assert report["jena_version"] == "5.3.0"
    assert report["mode"] == "full"
    assert "elapsed_seconds" in report
    assert "outcome_classification" in report
    assert "disposition_input" in report

    # All four properties + A.1 sub-property + LHS-decomp diagnostic present
    for key in ("property_a1_standalone_parse", "property_a", "property_b",
                 "property_c", "property_d"):
        assert key in report, f"missing property block: {key}"
        if key != "property_c":
            assert "passed" in report[key], f"{key} missing 'passed' field"

    assert "native" in report["property_c"]
    assert "lhs_decomposition_diagnostic" in report["property_c"]


def test_substrate_property_a1_passes(java_executable, substrate_jar, substrate_paths, substrate_report_path):
    """Property A.1: OOS rule file must parse standalone."""
    report = _run_substrate_test(java_executable, substrate_jar, substrate_paths, substrate_report_path)
    a1 = report["property_a1_standalone_parse"]
    assert a1["passed"] is True, f"OOS rule file did not parse: {a1}"
    assert a1["rules_parsed"] >= 1


def test_substrate_property_a_hybrid_loads(java_executable, substrate_jar, substrate_paths, substrate_report_path):
    """Property A: hybrid mode reasoner instantiates and prepares cleanly."""
    report = _run_substrate_test(java_executable, substrate_jar, substrate_paths, substrate_report_path)
    pa = report["property_a"]
    assert pa["passed"] is True, f"Property A failed: {pa}"


def test_substrate_property_b_backward_chain_executes(java_executable, substrate_jar, substrate_paths, substrate_report_path):
    """Property B: backward chain executes (proof_outcome present, regardless of success/failure)."""
    report = _run_substrate_test(java_executable, substrate_jar, substrate_paths, substrate_report_path)
    pb = report["property_b"]
    assert pb["passed"] is True, f"Property B did not execute: {pb}"
    assert pb["proof_outcome"] in ("success", "failure")


def test_substrate_property_d_no_forward_regression(java_executable, substrate_jar, substrate_paths, substrate_report_path):
    """Property D: weakener firings unchanged when OOS rule loaded alongside C3."""
    report = _run_substrate_test(java_executable, substrate_jar, substrate_paths, substrate_report_path)
    pd = report["property_d"]
    assert pd["passed"] is True, (
        f"Property D regression — forward firings differ.\n"
        f"only_in_baseline: {pd.get('only_in_baseline')}\n"
        f"only_in_with_oos: {pd.get('only_in_with_oos')}"
    )


def test_substrate_lhs_decomp_identifies_missing_subgoal(java_executable, substrate_jar, substrate_paths, substrate_report_path):
    """LHS-decomposition diagnostic: structurally missing sub-goal is identified.

    On cal-021, the missing sub-goal must be the `hasSupportingEvidence` clause
    because cal-021 has the ModelFormAdequacyClaim typing we add but no
    StructuredComparisonStudy evidence linkage.
    """
    report = _run_substrate_test(java_executable, substrate_jar, substrate_paths, substrate_report_path)
    diag = report["property_c"]["lhs_decomposition_diagnostic"]
    assert diag["passed"] is True, f"LHS-decomp diagnostic failed: {diag}"
    assert "hasSupportingEvidence" in diag["missing_subgoal"], (
        f"Expected missing_subgoal to mention hasSupportingEvidence, "
        f"got: {diag['missing_subgoal']}"
    )


def test_substrate_outcome_classification_is_known(java_executable, substrate_jar, substrate_paths, substrate_report_path):
    """Outcome must classify as 1, 2, or 3 per PRD §5."""
    report = _run_substrate_test(java_executable, substrate_jar, substrate_paths, substrate_report_path)
    assert report["outcome_classification"] in ("1", "2", "3"), (
        f"Unknown outcome: {report['outcome_classification']}"
    )


def test_substrate_determinism(java_executable, substrate_jar, substrate_paths, substrate_report_path):
    """Run the test 3 times — firing lists must be byte-identical (PRD §7 verification)."""
    reports = [
        _run_substrate_test(java_executable, substrate_jar, substrate_paths, substrate_report_path)
        for _ in range(3)
    ]
    baselines = [json.dumps(r["property_d"]["weakener_firings_baseline"], sort_keys=True)
                 for r in reports]
    with_oos = [json.dumps(r["property_d"]["weakener_firings_with_oos_rule"], sort_keys=True)
                for r in reports]
    assert len(set(baselines)) == 1, f"Baseline firings non-deterministic across runs: {baselines}"
    assert len(set(with_oos)) == 1, f"With-OOS firings non-deterministic across runs: {with_oos}"

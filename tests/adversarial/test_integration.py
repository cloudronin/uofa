"""End-to-end integration tests via subprocess.

Mirrors the pattern in tests/test_extract_integration.py — invokes the
installed ``uofa`` CLI as a child process.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
MOCK_FIXTURE = REPO_ROOT / "tests" / "adversarial" / "fixtures" / "mock_response.jsonld"


def run_uofa(*args, env: dict | None = None, cwd: Path | None = None) -> subprocess.CompletedProcess:
    """Invoke the installed `uofa` CLI as a subprocess."""
    full_env = os.environ.copy()
    if env:
        full_env.update(env)
    return subprocess.run(
        [sys.executable, "-m", "uofa_cli.cli", *args],
        capture_output=True,
        text=True,
        env=full_env,
        cwd=cwd or REPO_ROOT,
    )


def test_adversarial_help_lists_generate():
    result = run_uofa("adversarial", "--help")
    assert result.returncode == 0
    assert "generate" in result.stdout


def test_dry_run_exits_zero_and_prints_prompt(tmp_path):
    result = run_uofa(
        "adversarial",
        "generate",
        "--spec",
        "tests/adversarial/fixtures/spec_w_ar_05_valid.yaml",
        "--out",
        str(tmp_path / "dryrun"),
        "--dry-run",
    )
    assert result.returncode == 0, result.stderr
    assert "DRY RUN" in result.stdout
    assert "W-AR-05" in result.stdout


def test_bad_spec_exits_3(tmp_path):
    result = run_uofa(
        "adversarial",
        "generate",
        "--spec",
        "tests/adversarial/fixtures/spec_w_ar_05_bad_weakener.yaml",
        "--out",
        str(tmp_path),
    )
    assert result.returncode == 3
    assert "spec" in (result.stderr.lower() + result.stdout.lower())


def test_end_to_end_generate_with_mock_llm(tmp_path):
    """HARD GATE (spec §13, Hour 4).

    Invokes the full CLI pipeline with ``--model mock``, which reads a
    known-good JSON-LD fixture and runs it through SHACL. All 3 variants
    must pass and the manifest must be written.
    """
    out_dir = tmp_path / "adv_e2e"
    result = run_uofa(
        "adversarial",
        "generate",
        "--spec",
        "tests/adversarial/fixtures/spec_w_ar_05_valid.yaml",
        "--out",
        str(out_dir),
        "--model",
        "mock",
        "--allow-circular-model",
        env={"UOFA_ADVERSARIAL_MOCK_FIXTURE": str(MOCK_FIXTURE)},
    )
    assert result.returncode == 0, (
        f"exit {result.returncode}\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )

    manifest_path = out_dir / "manifest.json"
    assert manifest_path.exists()
    manifest = json.loads(manifest_path.read_text())
    assert manifest["specId"] == "adv-test-w-ar-05"
    assert manifest["generated"] == 3
    assert manifest["shaclFailed"] == 0

    # All 3 variant files exist, pass SHACL already (verified inside generate),
    # and carry the synthetic markers.
    jsonld_files = sorted(out_dir.glob("*.jsonld"))
    assert len(jsonld_files) == 3
    for p in jsonld_files:
        pkg = json.loads(p.read_text())
        assert pkg["synthetic"] is True
        assert "uofa:SyntheticAdversarialSample" in pkg["type"]
        assert "adversarialProvenance" in pkg
        assert pkg["adversarialProvenance"]["targetWeakener"] == "W-AR-05"


def test_default_manifest_refuse(tmp_path):
    """Second run without --force must refuse; exit 2."""
    out_dir = tmp_path / "adv_refuse"
    first = run_uofa(
        "adversarial",
        "generate",
        "--spec",
        "tests/adversarial/fixtures/spec_w_ar_05_valid.yaml",
        "--out",
        str(out_dir),
        "--model",
        "mock",
        "--allow-circular-model",
        env={"UOFA_ADVERSARIAL_MOCK_FIXTURE": str(MOCK_FIXTURE)},
    )
    assert first.returncode == 0, first.stderr

    second = run_uofa(
        "adversarial",
        "generate",
        "--spec",
        "tests/adversarial/fixtures/spec_w_ar_05_valid.yaml",
        "--out",
        str(out_dir),
        "--model",
        "mock",
        "--allow-circular-model",
        env={"UOFA_ADVERSARIAL_MOCK_FIXTURE": str(MOCK_FIXTURE)},
    )
    assert second.returncode == 2, f"expected 2, got {second.returncode}\n{second.stderr}"
    assert "manifest" in (second.stderr.lower() + second.stdout.lower())

    third = run_uofa(
        "adversarial",
        "generate",
        "--spec",
        "tests/adversarial/fixtures/spec_w_ar_05_valid.yaml",
        "--out",
        str(out_dir),
        "--model",
        "mock",
        "--allow-circular-model",
        "--force",
        env={"UOFA_ADVERSARIAL_MOCK_FIXTURE": str(MOCK_FIXTURE)},
    )
    assert third.returncode == 0, third.stderr

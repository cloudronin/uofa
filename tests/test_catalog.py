"""Tests for the `uofa catalog` command."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent


def _run(*extra_args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["python", "-m", "uofa_cli", "catalog", *extra_args],
        capture_output=True, text=True,
        cwd=str(REPO_ROOT),
    )


def test_catalog_lists_all_23_core_patterns():
    result = _run("--format", "json")
    assert result.returncode == 0
    records = json.loads(result.stdout)
    core = [r for r in records if r["pack"] == "core"]
    assert len(core) == 23, f"expected 23 core patterns, got {len(core)}: {[r['patternId'] for r in core]}"


def test_catalog_ported_rules_report_core_pack():
    """W-PROV-01, W-CON-02, W-CON-05 were ported from Python to Jena at v0.5.2.
    Post-v0.5.3 the per-row column is the source pack, not the engine — they
    belong to core alongside the rest of the base ruleset."""
    result = _run("--format", "json")
    assert result.returncode == 0
    records = json.loads(result.stdout)
    pids = {r["patternId"]: r for r in records}
    for pid in ("W-PROV-01", "W-CON-02", "W-CON-05"):
        assert pid in pids, f"{pid} missing from catalog"
        assert pids[pid]["pack"] == "core", (
            f"{pid} should report pack=core; got {pids[pid]['pack']}"
        )
        assert "engine" not in pids[pid], (
            f"{pid} still carries legacy 'engine' field; v0.5.3 renamed this to 'pack'"
        )


def test_catalog_includes_all_v0_5_additions():
    result = _run("--format", "json")
    assert result.returncode == 0
    records = json.loads(result.stdout)
    pids = {r["patternId"] for r in records}
    for pid in (
        "W-EP-03", "W-AL-02", "W-ON-02", "W-AR-03", "W-AR-04",
        "W-CON-01", "W-CON-02", "W-CON-03", "W-CON-04", "W-CON-05",
        "W-PROV-01",
    ):
        assert pid in pids, f"v0.5 pattern {pid} missing from catalog"


def test_catalog_excludes_deferred_compound_02():
    result = _run("--format", "json")
    assert result.returncode == 0
    records = json.loads(result.stdout)
    pids = {r["patternId"] for r in records}
    assert "COMPOUND-02" not in pids, "COMPOUND-02 is deferred and should not appear in the active catalog"


def test_catalog_nasa_pack_adds_6_patterns():
    # --pack must come AFTER the subcommand per CLI argparse scoping.
    result = _run("--pack", "nasa-7009b", "--format", "json")
    assert result.returncode == 0
    records = json.loads(result.stdout)
    nasa = [r for r in records if r["pack"] == "nasa-7009b"]
    assert len(nasa) == 6, f"expected 6 NASA patterns, got {len(nasa)}"


def test_catalog_table_format_includes_core_total():
    result = _run()
    assert result.returncode == 0
    assert "Pack: core" in result.stdout
    assert "23 patterns" in result.stdout


def test_catalog_honors_pack_flag():
    """Fix A: --pack nasa-7009b enumerates core + NASA, 29 total."""
    result = _run("--pack", "nasa-7009b")
    assert result.returncode == 0
    assert "W-NASA-01" in result.stdout
    assert "W-NASA-06" in result.stdout
    assert "Pack: nasa-7009b" in result.stdout
    assert "Total: 29 patterns" in result.stdout


def test_catalog_default_shows_core_only():
    """Fix A: default behaviour (no --pack) shows core only, no NASA rules."""
    result = _run()
    assert result.returncode == 0
    assert "Pack: core" in result.stdout
    assert "W-NASA" not in result.stdout
    assert "Total: 23 patterns" in result.stdout


def test_catalog_shows_pack_label_not_jena():
    """Fix A1: per-row source tag is pack-of-origin, not legacy [jena]."""
    result = _run("--pack", "nasa-7009b")
    assert result.returncode == 0
    assert "[jena]" not in result.stdout
    assert "[core]" in result.stdout
    assert "[nasa-7009b]" in result.stdout


def test_catalog_json_has_pack_field_not_engine():
    """Fix A1: JSON schema field is 'pack', not 'engine'."""
    result = _run("--pack", "nasa-7009b", "--format", "json")
    assert result.returncode == 0
    patterns = json.loads(result.stdout)
    assert len(patterns) == 29
    for p in patterns:
        assert "pack" in p
        assert "engine" not in p
        assert p["pack"] in ("core", "nasa-7009b")

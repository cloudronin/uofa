"""Tests for `uofa demo` (PR 5).

Confirms the bundled fixture exists, fits within the REQ-DIST-008 AC 4
size budget, and that the command exits 0 when the C1+C2+C3 pipeline can
reach the bundled engine assets. The full pipeline test relies on the
real Java + JAR being available (same condition as test_integration.py).
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest

from uofa_cli.commands import demo


REPO_ROOT = Path(__file__).resolve().parent.parent
JAVA_AVAILABLE = shutil.which("java") is not None
JENA_JAR = REPO_ROOT / "weakener-engine" / "target" / "uofa-weakener-engine-0.1.0.jar"
JENA_AVAILABLE = JAVA_AVAILABLE and JENA_JAR.exists()


def _bundled_demo_dir() -> Path:
    here = Path(__file__).resolve()
    pkg = here.parent.parent / "src" / "uofa_cli"
    return pkg / "_data" / "fixtures" / "demo"


def test_demo_fixture_exists_in_source_tree():
    fixture_dir = _bundled_demo_dir()
    assert (fixture_dir / "passage.txt").is_file()
    assert (fixture_dir / "uofa-demo-cou1.jsonld").is_file()
    assert (fixture_dir / "manifest.json").is_file()


def test_demo_fixture_under_10kb_total():
    """REQ-DIST-008 AC 4: bundled fixture adds < 10 KB to wheel size."""
    fixture_dir = _bundled_demo_dir()
    total = sum(p.stat().st_size for p in fixture_dir.rglob("*") if p.is_file())
    assert total < 10 * 1024, f"demo fixture is {total} bytes (>= 10 KB)"


def test_demo_manifest_includes_required_fields():
    import json
    fixture_dir = _bundled_demo_dir()
    manifest = json.loads((fixture_dir / "manifest.json").read_text())
    for field in ("title", "description", "passage_file", "uofa_file", "what_it_shows"):
        assert field in manifest, f"manifest missing '{field}'"
    assert manifest["passage_file"] == "passage.txt"
    assert manifest["uofa_file"] == "uofa-demo-cou1.jsonld"


@pytest.mark.skipif(not JENA_AVAILABLE, reason="demo requires Java + Jena JAR")
def test_demo_run_succeeds_end_to_end(monkeypatch, capsys):
    """Run `uofa demo --no-passage --no-jsonld` and assert exit 0."""
    args = type("Args", (), {"no_passage": True, "no_jsonld": True})()
    rc = demo.run(args)
    captured = capsys.readouterr()
    assert rc == 0, f"demo exit {rc}; stderr: {captured.err}"
    # Sanity: pipeline must have actually printed C1+C2+C3 results.
    assert "C2 SHACL" in captured.out
    assert "C1 Integrity" in captured.out
    assert "C3 Rules" in captured.out

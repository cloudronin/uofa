"""Phase F breadth check: PDEBench confirms the pack/SIP are not airfoil-specific.

This test is GATED behind the license precondition (required change #2): it runs
only when CC-BY-confirmed PDEBench fixtures + their LICENSE_MANIFEST.json are
present under tests/fixtures/interrogate/pdebench/. Until then it skips, so the
precondition cannot be silently bypassed and CI stays green without shipping any
NLE academic-use-only data. See that directory's LICENSE.md.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

PDEBENCH_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "interrogate" / "pdebench"
MANIFEST = PDEBENCH_DIR / "LICENSE_MANIFEST.json"

pytestmark = pytest.mark.skipif(
    not MANIFEST.is_file(),
    reason="PDEBench fixtures not vendored — license precondition not yet satisfied "
           "(see tests/fixtures/interrogate/pdebench/LICENSE.md)",
)


def test_committed_pdebench_fixtures_are_cc_by():
    """Every committed PDEBench fixture must be CC-BY (not the NLE carve-out)."""
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert manifest, "LICENSE_MANIFEST.json is empty"
    for entry in manifest:
        assert entry.get("license", "").upper().startswith("CC-BY"), (
            f"{entry.get('file')} is not CC-BY: {entry.get('license')!r}"
        )
        assert entry.get("source_doi"), f"{entry.get('file')} lacks a source DOI"
        fixture = PDEBENCH_DIR / entry["file"]
        assert fixture.is_file(), f"manifest lists missing fixture {entry['file']}"

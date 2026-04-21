"""Build the 8 SHACL-boundary xlsx templates under corpus/import-tests/.

Stub for commit 1 of the Pre-Tester QA Corpus v2 work; filled in by commit 2
with deterministic mutations on `tests/fixtures/import/generator.py` helpers.
"""

from __future__ import annotations

from pathlib import Path


def build_all(out_dir: Path) -> list[Path]:
    """Build every import-test fixture and return the list of written paths."""
    # Populated in commit 2 (reuses _clean_base_vv40 / _clean_base_nasa /
    # _mutate_* helpers from tests/fixtures/import/generator.py).
    return []

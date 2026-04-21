"""Build the Pre-Tester QA Corpus v2 — 18 deterministic test fixtures.

Usage:
    python corpus/build.py                # build everything
    python corpus/build.py --only edge    # build only edge-cases/
    python corpus/build.py --only import  # build only import-tests/

Outputs are written under corpus/edge-cases/ and corpus/import-tests/. Both
directories are .gitignore'd; regenerate by running this script or `make
corpus`. Idempotent: re-running overwrites existing files.

Dependencies (install via `pip install -e '.[corpus]'`):
    reportlab         — scanned + huge-appendix PDF generation
    msoffcrypto-tool  — password-protected .xlsx encryption
    openpyxl          — plain Excel generation (already a test dep)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

CORPUS_DIR = Path(__file__).resolve().parent
EDGE_DIR = CORPUS_DIR / "edge-cases"
IMPORT_DIR = CORPUS_DIR / "import-tests"

# Let the build script import tests/fixtures/import/generator.py without
# requiring a package-style layout or PYTHONPATH dance.
_REPO_ROOT = CORPUS_DIR.parent
sys.path.insert(0, str(_REPO_ROOT / "tests" / "fixtures" / "import"))


def _ensure_dirs() -> None:
    EDGE_DIR.mkdir(parents=True, exist_ok=True)
    IMPORT_DIR.mkdir(parents=True, exist_ok=True)


def build_edge_cases() -> list[Path]:
    """Build the 10 format-edge-case fixtures under corpus/edge-cases/."""
    from edge_case_builders import build_all as _build
    return _build(EDGE_DIR)


def build_import_tests() -> list[Path]:
    """Build the 8 SHACL-boundary xlsx templates under corpus/import-tests/."""
    from import_test_builders import build_all as _build
    return _build(IMPORT_DIR)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--only", choices=["edge", "import"], default=None,
                        help="restrict to one sub-corpus")
    args = parser.parse_args()

    _ensure_dirs()
    built: list[Path] = []

    if args.only in (None, "edge"):
        built.extend(build_edge_cases())
    if args.only in (None, "import"):
        built.extend(build_import_tests())

    print(f"✓ Built {len(built)} file(s):")
    for p in built:
        print(f"  {p.relative_to(_REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

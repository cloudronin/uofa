"""Pre-Tester QA Corpus v2 — SHACL boundary verification.

Per UofA_Pre_Tester_QA_Corpus_v2.md §"SHACL boundary testing": the 8
templates under corpus/import-tests/ must produce the exact pass/fail
outcomes documented in the spec's expected-results table. Error messages
on the three deliberate-error files must name the offending field so
testers know what to fix.

The spec's expected table assumed SHACL would catch the three error
cases. In practice the import layer catches them earlier (before SHACL
runs) with file+row+cell-named errors. Both satisfy the acceptance
criterion; this test pins the actual observed behavior.

Prerequisite: build the corpus first via `make corpus`. Tests
importorskip cleanly when the corpus directory is absent or openpyxl
is missing.
"""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
IMPORT_DIR = REPO_ROOT / "corpus" / "import-tests"

pytest.importorskip("openpyxl")


@dataclass
class ImportCase:
    filename: str
    pack: str           # "vv40" or "nasa-7009b"
    import_should_pass: bool
    shacl_should_conform: bool | None  # None when import fails (SHACL never runs)
    error_must_contain: str | None     # substring the user-facing error must include


CASES = [
    ImportCase("perfect-vv40.xlsx",            "vv40",       True,  True,  None),
    ImportCase("perfect-nasa.xlsx",            "nasa-7009b", True,  True,  None),
    ImportCase("minimal-7-factors.xlsx",       "vv40",       True,  True,  None),
    ImportCase("missing-required-fields.xlsx", "vv40",       False, None,  "Decision"),
    ImportCase("level-out-of-range.xlsx",      "vv40",       False, None,  "out of range"),
    ImportCase("typo-in-factor-name.xlsx",     "vv40",       False, None,  "Model Form Accuracy"),
    ImportCase("empty-rows.xlsx",              "vv40",       True,  True,  None),
    ImportCase("extra-columns.xlsx",           "vv40",       True,  True,  None),
]


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "uofa_cli", *args],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )


def _require_corpus(filename: str) -> Path:
    path = IMPORT_DIR / filename
    if not path.exists():
        pytest.skip(f"{filename} missing — run `make corpus` first")
    return path


@pytest.mark.parametrize("case", CASES, ids=lambda c: c.filename)
def test_corpus_import_boundary(case, tmp_path):
    xlsx = _require_corpus(case.filename)
    jsonld = tmp_path / (case.filename.replace(".xlsx", ".jsonld"))

    result = _run("import", str(xlsx), "--output", str(jsonld), "--pack", case.pack)

    if case.import_should_pass:
        assert result.returncode == 0, (
            f"{case.filename}: import should pass; got exit {result.returncode}\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
        assert jsonld.exists(), f"{case.filename}: import produced no output file"

        shacl_result = _run("shacl", str(jsonld), "--pack", case.pack)
        if case.shacl_should_conform:
            assert "Conforms" in shacl_result.stdout, (
                f"{case.filename}: SHACL expected to conform, got:\n"
                f"{shacl_result.stdout}"
            )
        else:
            assert "Conforms" not in shacl_result.stdout, (
                f"{case.filename}: SHACL expected to fail, but conformed"
            )
    else:
        # Import must fail with an actionable, file-named error.
        assert result.returncode != 0, (
            f"{case.filename}: import expected to fail, got exit 0"
        )
        combined = result.stdout + result.stderr
        assert "Traceback" not in combined, (
            f"{case.filename}: import produced a stack trace:\n{combined}"
        )
        assert "Error:" in combined, (
            f"{case.filename}: import failure has no 'Error:' prefix:\n{combined}"
        )
        assert case.error_must_contain in combined, (
            f"{case.filename}: error message missing required substring "
            f"{case.error_must_contain!r}:\n{combined}"
        )

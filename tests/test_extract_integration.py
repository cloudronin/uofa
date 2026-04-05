"""Integration tests for uofa extract — full CLI pipeline with mock provider."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    import openpyxl
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False

REPO_ROOT = Path(__file__).parent.parent
MORRISON_DIR = Path(__file__).parent / "fixtures" / "extract" / "morrison-evidence"


def run_uofa(*args, cwd=None):
    """Run uofa CLI as subprocess and return CompletedProcess."""
    cmd = [sys.executable, "-m", "uofa_cli", *args]
    env = {"PYTHONPATH": str(REPO_ROOT / "src")}

    import os
    full_env = os.environ.copy()
    full_env.update(env)

    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=cwd or str(REPO_ROOT),
        env=full_env,
    )


pytestmark = pytest.mark.skipif(not HAS_OPENPYXL, reason="openpyxl required")


class TestExtractHelp:
    def test_extract_in_help(self):
        result = run_uofa("--help")
        assert "extract" in result.stdout


class TestExtractNoSource:
    def test_no_source_error(self, tmp_path):
        result = run_uofa("extract", cwd=str(tmp_path))
        assert result.returncode == 1


class TestExtractEmptyFolder:
    def test_empty_folder(self, tmp_path):
        empty = tmp_path / "empty"
        empty.mkdir()
        result = run_uofa("extract", str(empty), "--model", "mock")
        assert result.returncode == 1
        assert "No supported files" in result.stderr or "No supported files" in result.stdout


@pytest.mark.skipif(not MORRISON_DIR.exists(), reason="Morrison evidence not available")
class TestExtractMorrisonMock:
    """Full pipeline test: Morrison evidence → mock LLM → Excel output."""

    def test_extract_succeeds(self, tmp_path):
        out = tmp_path / "output.xlsx"
        result = run_uofa(
            "extract", str(MORRISON_DIR),
            "--model", "mock",
            "--pack", "vv40",
            "--output", str(out),
        )
        # Print output for debugging
        if result.returncode != 0:
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
        assert result.returncode == 0

    def test_output_exists(self, tmp_path):
        out = tmp_path / "output.xlsx"
        run_uofa(
            "extract", str(MORRISON_DIR),
            "--model", "mock",
            "--pack", "vv40",
            "--output", str(out),
        )
        assert out.exists()

    def test_output_has_factors(self, tmp_path):
        out = tmp_path / "output.xlsx"
        run_uofa(
            "extract", str(MORRISON_DIR),
            "--model", "mock",
            "--pack", "vv40",
            "--output", str(out),
        )
        from uofa_cli.excel_constants import VV40_FACTOR_NAMES
        wb = openpyxl.load_workbook(out)
        ws = wb["Credibility Factors"]
        factors_found = []
        for row in range(1, ws.max_row + 1):
            val = ws.cell(row=row, column=1).value
            if val and val in VV40_FACTOR_NAMES:
                factors_found.append(val)
        assert len(factors_found) == 13

    def test_output_has_decision(self, tmp_path):
        out = tmp_path / "output.xlsx"
        run_uofa(
            "extract", str(MORRISON_DIR),
            "--model", "mock",
            "--pack", "vv40",
            "--output", str(out),
        )
        wb = openpyxl.load_workbook(out)
        ws = wb["Decision"]
        found = False
        for row in ws.iter_rows(values_only=True):
            if row and row[0] == "Accepted":
                found = True
        assert found

    def test_glob_filter(self, tmp_path):
        out = tmp_path / "output.xlsx"
        result = run_uofa(
            "extract", str(MORRISON_DIR),
            "--model", "mock",
            "--pack", "vv40",
            "--output", str(out),
            "--glob", "*.csv,*.txt",
        )
        assert result.returncode == 0
        # Output should mention only csv/txt files
        assert out.exists()

    def test_verbose_output(self, tmp_path):
        out = tmp_path / "output.xlsx"
        result = run_uofa(
            "extract", str(MORRISON_DIR),
            "--model", "mock",
            "--pack", "vv40",
            "--output", str(out),
            "--verbose",
        )
        assert result.returncode == 0
        assert "tokens" in result.stdout.lower()


class TestExtractTextOnly:
    """Test extraction with only text/csv files (no pdfplumber/python-docx needed)."""

    def test_extract_text_csv(self, tmp_path):
        # Create simple evidence files
        evidence = tmp_path / "evidence"
        evidence.mkdir()
        (evidence / "report.txt").write_text(
            "V&V Report\n\nThe CFD model was validated against experimental data.\n"
            "Software: ANSYS CFX v21.0 with ISO 9001 certification.\n"
            "Mesh convergence study: 3 levels, GCI = 1.2%.\n"
        )
        (evidence / "data.csv").write_text(
            "mesh_level,elements,gci_pct\nCoarse,100000,5.2\nMedium,400000,1.8\nFine,1600000,0.6\n"
        )

        out = tmp_path / "result.xlsx"
        result = run_uofa(
            "extract", str(evidence),
            "--model", "mock",
            "--pack", "vv40",
            "--output", str(out),
        )
        assert result.returncode == 0
        assert out.exists()

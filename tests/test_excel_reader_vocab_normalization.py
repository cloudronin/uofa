"""Regression: evidence_type vocabulary mismatch between extractor LLM and importer.

Bug context (May 2026): running ``uofa extract`` on NASA evidence with a real
LLM (qwen3.5:4b) produced ``Validation Results`` rows whose Type column held
descriptive domain labels like ``GridConvergenceStudy``, ``CodeVerification``,
``ExperimentalValidation``, ``NumericalSolverAssessment``,
``ModelLimitationAssessment`` — none of which are in the canonical
``EVIDENCE_TYPES`` enum. The importer then hard-failed with::

    Error: Sheet 'Validation Results', cell B3:
    'GridConvergenceStudy' is not a valid evidence type.
    Expected: ValidationResult, ReviewActivity, ProcessAttestation,
    DeploymentRecord, InputPedigreeLink

Fix: the reader normalizes unknown evidence_type values against the canonical
enum (fuzzy match → fallback to ``ValidationResult``) and emits a warning
instead of an error. This file pins the offending bytes from the actual demo
run so the bug cannot regress silently.

Fixture provenance: ``tests/fixtures/regression/extract-vocab-mismatch/``
contains the two .xlsx files produced by the NAFEMS demo extraction —
``aero-evidence-cou1-extracted.xlsx`` (5 invalid evidence_type values) and
``aero-evidence-cou2-extracted.xlsx`` (clean, used as a negative control).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    import openpyxl  # noqa: F401
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "regression" / "extract-vocab-mismatch"
COU1_XLSX = FIXTURE_DIR / "aero-evidence-cou1-extracted.xlsx"
COU2_XLSX = FIXTURE_DIR / "aero-evidence-cou2-extracted.xlsx"

pytestmark = pytest.mark.skipif(not HAS_OPENPYXL, reason="openpyxl required")


@pytest.mark.skipif(not COU1_XLSX.exists(), reason=f"missing fixture: {COU1_XLSX}")
class TestAeroCou1VocabMismatchNormalizes:
    """The cou1 file has 5 rows with non-canonical evidence_type strings.
    Importing it must succeed (no ImportError), normalize all 5 values to a
    member of EVIDENCE_TYPES, and emit one warning per substituted cell.
    """

    def test_import_succeeds(self):
        from uofa_cli.excel_reader import read_workbook
        data = read_workbook(COU1_XLSX, ["nasa-7009b"])
        # If normalization didn't kick in, read_workbook would have raised
        # ImportError. Reaching this assertion at all is half the test.
        assert data is not None
        assert "validation_results" in data

    def test_all_evidence_types_normalized_to_canonical(self):
        from uofa_cli.excel_reader import read_workbook
        from uofa_cli.excel_constants import EVIDENCE_TYPES
        data = read_workbook(COU1_XLSX, ["nasa-7009b"])
        types = [vr["evidence_type"] for vr in data["validation_results"]]
        # Every Type must now be a canonical enum value.
        bad = [t for t in types if t not in EVIDENCE_TYPES]
        assert not bad, f"unexpected non-canonical types post-normalization: {bad}"
        # And we should have actually read 5 rows (the original count).
        assert len(types) == 5

    def test_warnings_emitted_for_each_substitution(self):
        from uofa_cli.excel_reader import read_workbook
        data = read_workbook(COU1_XLSX, ["nasa-7009b"])
        warnings = data.get("_warnings", [])
        # 5 rows, all had non-canonical types → 5 normalization warnings.
        vocab_warnings = [w for w in warnings if "is not a canonical evidence type" in w]
        assert len(vocab_warnings) == 5, (
            f"expected 5 vocab-mismatch warnings, got {len(vocab_warnings)}: {vocab_warnings}"
        )
        # And each warning should name the original LLM-produced string for
        # transparency.
        joined = "\n".join(vocab_warnings)
        for original in ("GridConvergenceStudy", "CodeVerification",
                         "ExperimentalValidation", "NumericalSolverAssessment",
                         "ModelLimitationAssessment"):
            assert original in joined, f"warning for {original!r} missing"


@pytest.mark.skipif(not COU2_XLSX.exists(), reason=f"missing fixture: {COU2_XLSX}")
class TestAeroCou2CleanFileNoWarnings:
    """Negative control — the cou2 file has only canonical evidence_type
    values. Normalization must NOT trigger; warnings list stays empty.
    Guards against the lenient mode silently mutating clean inputs.
    """

    def test_import_succeeds(self):
        from uofa_cli.excel_reader import read_workbook
        data = read_workbook(COU2_XLSX, ["nasa-7009b"])
        assert data is not None
        assert len(data["validation_results"]) >= 1

    def test_no_vocab_warnings_emitted(self):
        from uofa_cli.excel_reader import read_workbook
        data = read_workbook(COU2_XLSX, ["nasa-7009b"])
        warnings = data.get("_warnings", [])
        vocab_warnings = [w for w in warnings if "is not a canonical evidence type" in w]
        assert vocab_warnings == [], (
            f"clean file should not produce vocab-mismatch warnings; got: {vocab_warnings}"
        )

    def test_canonical_evidence_type_preserved(self):
        from uofa_cli.excel_reader import read_workbook
        data = read_workbook(COU2_XLSX, ["nasa-7009b"])
        # cou2 row 3 in the source xlsx has evidence_type='ValidationResult'
        # already canonical. Verify it survived unchanged.
        types = [vr["evidence_type"] for vr in data["validation_results"]]
        assert "ValidationResult" in types

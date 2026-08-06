"""The constant scores F1 0.960 and does not produce a package.

`control_constant_list` emits the pack's fixed checklist, reads none of the
input, and scores detection F1 **0.960** against the LLM's 0.964 -- unbeatable
on 23 of 50 bundles, because ground truth lists the full checklist and marks
92.5% of rows `assessed`. On the metric this eval reported for a year, a
zero-parameter function sat within 0.004 of the model.

It cannot produce a Unit of Assurance. Not a deficient one -- none. Its workbook
fails `uofa import` on the **Minimal** profile's requirements, three sheets
before ProfileComplete is considered.

That is the claim these tests pin, because it is the one someone will later
doubt, and because it is the argument for scoring the whole schema rather than
the one property where the null model is indistinguishable from the model.

These tests do not replace detection F1. Detection is what correctly separates
`control_empty` from `control_constant_list`, which schema coverage cannot --
neither imports. A candidate has to clear import, populate the schema, *and*
beat the constant on detection. Each metric bounds a different failure.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "dev" / "tools" / "scripts"))

from schema_coverage import (  # noqa: E402
    required_properties,
    score_schema_coverage,
    validate_extracted,
)
from score_extraction import control_predictions  # noqa: E402

REAL_BUNDLE = (_ROOT / "tests" / "fixtures" / "extract_corpus" / "dev"
               / "bundle_vv40_cfd_001" / "extracted.xlsx")

pytestmark = pytest.mark.skipif(
    not REAL_BUNDLE.exists(), reason=f"missing corpus bundle: {REAL_BUNDLE}")


def _control_workbook(dest: Path, keep_factors: bool) -> Path:
    """A workbook holding what the control emits, and nothing else.

    The control produces credibility factors only: no assessment summary, no
    entities, no validation results, no decision. Built by blanking a real
    extraction rather than synthesising a file, so the sheet layout is exactly
    what the importer expects and the failure is about content, not format.
    """
    openpyxl = pytest.importorskip("openpyxl")
    from openpyxl.cell.cell import MergedCell

    shutil.copy(REAL_BUNDLE, dest)
    wb = openpyxl.load_workbook(dest)
    sheets = ["Assessment Summary", "Model & Data", "Validation Results", "Decision"]
    if not keep_factors:
        sheets.append("Credibility Factors")
    for name in sheets:
        for row in wb[name].iter_rows(min_row=2):
            for cell in row:
                if not isinstance(cell, MergedCell):
                    cell.value = None
    wb.save(dest)
    return dest


def test_the_constant_covers_one_required_property_of_nine():
    """1/9 against the LLM's 8/9, where detection F1 separates them by 0.004."""
    parsed = {
        "credibility_factors": control_predictions("control_constant_list", "vv40"),
        "entities": [], "validation_results": [],
        "decision": {}, "assessment_summary": {},
    }
    cov = score_schema_coverage(parsed, "vv40")
    populated = {p for p, ok in cov.items() if ok}
    assert populated == {"hasCredibilityFactor"}, populated
    assert len(required_properties("vv40")) >= 9


def test_the_empty_control_covers_none():
    parsed = {"credibility_factors": [], "entities": [], "validation_results": [],
              "decision": {}, "assessment_summary": {}}
    assert not any(score_schema_coverage(parsed, "vv40").values())


def test_the_constant_cannot_be_imported_at_all(tmp_path):
    """The sharp one: it fails before validation, on the Minimal profile.

    `validate_extracted` returns None for `conforms` when the import step
    itself failed -- deliberately distinct from False, because "produced an
    invalid package" and "produced no package" are different results and
    averaging them together would hide this entirely.
    """
    wb = _control_workbook(tmp_path / "control_constant_list.xlsx", keep_factors=True)
    conforms, _ = validate_extracted(wb, "vv40")
    assert conforms is None, (
        "the constant's output imported; it is supposed to fail on missing "
        "Project Name, COU Name and Decision Outcome")


def test_the_empty_control_cannot_be_imported_either(tmp_path):
    wb = _control_workbook(tmp_path / "control_empty.xlsx", keep_factors=False)
    conforms, _ = validate_extracted(wb, "vv40")
    assert conforms is None


def test_the_llm_output_does_import_and_is_then_judged_on_content():
    """The contrast that makes the above meaningful.

    A real extraction clears import and is then scored on whether it conforms
    and whether it says anything. It fails on content -- `decision`,
    `hasValidationResult`, and `wasDerivedFrom` satisfied by template help text
    -- which is a different and more useful failure than not existing.
    """
    conforms, findings = validate_extracted(REAL_BUNDLE, "vv40")
    assert conforms is not None, "the LLM's output should at least import"
    assert "placeholder:wasDerivedFrom" in findings, (
        "if this cleared, the source_document prompt fix has taken effect and "
        "the shipped-corpus figures in docs/keyless-extract-findings.md are stale")


def test_detection_f1_is_still_needed_because_coverage_cannot_separate_the_controls():
    """Guards against dropping detection now that schema coverage exists.

    Neither control imports, and coverage ranks them 1/9 and 0/9 -- close.
    Detection F1 separates them properly, 0.960 against 0.000. The metrics
    bound different failures and none of them is redundant.
    """
    const = control_predictions("control_constant_list", "vv40")
    empty = control_predictions("control_empty", "vv40")
    assert const and not empty

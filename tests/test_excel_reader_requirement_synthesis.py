"""Regression: missing Requirement entity from real-LLM extraction.

Bug context (May 25, 2026 — discovered during the post-AGENTS.md real-LLM
e2e run for NASA aero): qwen3.5:4b extracted ``aero-evidence-cou2/`` and
emitted Model + Dataset entities but no Requirement, with the description
"Model re-uses COU1 configuration with only operating point changes" —
the LLM decided the Requirement was inherited from cou1 and dropped it
even though the prompt is explicit ("MUST include at least one block with
entity_type: Requirement"). The importer then hard-failed with::

    Error: Sheet 'Model & Data' must have at least one row with
    Entity Type = 'Requirement'

Fix: the reader synthesizes a Requirement entity from the Assessment
Summary's cou_name + cou_description fields and emits a warning instead
of erroring (lenient mode). The writer applies the same synthesis at
write time so future extractions land with structurally-valid xlsx files
that the user can review and edit before importing.

This file pins the actual offending bytes from the real-LLM run so the
bug cannot regress silently. Fixture provenance:
``tests/fixtures/regression/extract-missing-requirement/aero-evidence-cou2-extracted.xlsx``
— qwen3.5:4b output, May 25 2026.

Negative control uses ``tests/fixtures/regression/extract-vocab-mismatch/
aero-evidence-cou1-extracted.xlsx`` which DOES have a Requirement, to
verify the lenient mode doesn't synthesize spuriously on clean inputs.
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

MISSING_REQ_XLSX = (Path(__file__).parent / "fixtures" / "regression"
                    / "extract-missing-requirement"
                    / "aero-evidence-cou2-extracted.xlsx")
CLEAN_CONTROL_XLSX = (Path(__file__).parent / "fixtures" / "regression"
                      / "extract-vocab-mismatch"
                      / "aero-evidence-cou1-extracted.xlsx")

pytestmark = pytest.mark.skipif(not HAS_OPENPYXL, reason="openpyxl required")


@pytest.mark.skipif(not MISSING_REQ_XLSX.exists(),
                    reason=f"missing fixture: {MISSING_REQ_XLSX}")
class TestAeroCou2MissingRequirementSynthesizes:
    """The cou2 fixture has 0 Requirement entities — the LLM emitted only
    Model + Dataset. Importing it must succeed via lenient synthesis, the
    synthesized Requirement must come from the Assessment Summary's COU
    fields, and exactly one warning must explain the auto-fill.
    """

    def test_import_succeeds(self):
        from uofa_cli.excel_reader import read_workbook
        data = read_workbook(MISSING_REQ_XLSX, ["nasa-7009b"])
        # If synthesis didn't kick in, read_workbook would have raised
        # ImportError. Reaching this assertion is half the test.
        assert data is not None
        assert "entities" in data

    def test_synthesized_requirement_present(self):
        from uofa_cli.excel_reader import read_workbook
        data = read_workbook(MISSING_REQ_XLSX, ["nasa-7009b"])
        requirements = [e for e in data["entities"] if e["entity_type"] == "Requirement"]
        assert len(requirements) == 1, (
            f"expected exactly 1 synthesized Requirement, got {len(requirements)}"
        )

    def test_synthesized_requirement_uses_cou_context(self):
        from uofa_cli.excel_reader import read_workbook
        data = read_workbook(MISSING_REQ_XLSX, ["nasa-7009b"])
        req = next(e for e in data["entities"] if e["entity_type"] == "Requirement")
        # The synthesized name should be the cou_name from the summary,
        # which for this fixture is the cruise-steady-state COU label.
        # source field marks it as auto-synthesized so downstream code can
        # distinguish from real entities.
        assert req["source"] == "auto-synthesized"
        # Description should explain the synthesis and tell the user to review.
        assert "Auto-synthesized" in (req["description"] or "")
        assert "Review and replace" in (req["description"] or "")

    def test_warning_emitted(self):
        from uofa_cli.excel_reader import read_workbook
        data = read_workbook(MISSING_REQ_XLSX, ["nasa-7009b"])
        warnings = data.get("_warnings", [])
        synth_warnings = [w for w in warnings if "no Requirement entity" in w]
        assert len(synth_warnings) == 1, (
            f"expected 1 synthesis warning, got {len(synth_warnings)}: {warnings}"
        )
        # And the warning should tell the user to review the auto-fill.
        assert "Review the auto-filled row" in synth_warnings[0]


@pytest.mark.skipif(not CLEAN_CONTROL_XLSX.exists(),
                    reason=f"missing fixture: {CLEAN_CONTROL_XLSX}")
class TestAeroCou1CleanFileNoSynthesisWarning:
    """Negative control — the cou1 vocab-mismatch fixture HAS a Requirement
    entity. Lenient mode must NOT synthesize an extra one and must NOT
    emit a synthesis warning. Guards against the lenient path silently
    mutating clean inputs.
    """

    def test_import_succeeds(self):
        from uofa_cli.excel_reader import read_workbook
        data = read_workbook(CLEAN_CONTROL_XLSX, ["nasa-7009b"])
        assert data is not None
        requirements = [e for e in data["entities"] if e["entity_type"] == "Requirement"]
        # Exactly the one the LLM emitted; no synthetic extra.
        assert len(requirements) == 1
        assert requirements[0]["source"] != "auto-synthesized"

    def test_no_synthesis_warning(self):
        from uofa_cli.excel_reader import read_workbook
        data = read_workbook(CLEAN_CONTROL_XLSX, ["nasa-7009b"])
        warnings = data.get("_warnings", [])
        synth_warnings = [w for w in warnings if "no Requirement entity" in w]
        assert synth_warnings == [], (
            f"clean file should not trigger Requirement synthesis; got: {synth_warnings}"
        )

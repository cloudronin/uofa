"""End-to-end Morrison pipeline test: evidence → extract → import → check + rules.

Morrison (VV40 reference example: centrifugal blood pump hemolysis CFD) ships
as a single evidence folder containing files for both Contexts of Use
(``decision_rationale_cou1.pdf``, ``decision_rationale_cou2.pdf``, etc., per
``EVIDENCE_MANIFEST.txt``). Unlike the NASA aero case study, the evidence
is not pre-split per COU, so the chained e2e produces a single xlsx → single
jsonld pair, and the diff step lives in the existing pre-built-fixture test
(``TestDiff::test_diff_morrison_cou1_vs_cou2`` in ``test_integration.py``).

This file catches integration regressions across the
extract → import → check → rules surface for the VV40 pack — the same class
of regression the aero e2e catches for nasa-7009b. Today's vocab-mismatch
bug (LLM produced non-canonical evidence_type values, importer rejected
them) would have surfaced here on a real LLM run.

Mock variant runs in CI. Real-LLM variant is gated by ``UOFA_RUN_REAL_LLM=1``
and asserts loose plumbing rather than specific firings, because Morrison's
shared-folder evidence can't be reliably scoped to a single COU's expected
weakener pattern when extracted whole.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    import openpyxl  # noqa: F401
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False

from tests.test_extract_integration import run_uofa, MORRISON_DIR

REAL_LLM_ENABLED = os.environ.get("UOFA_RUN_REAL_LLM") == "1"

pytestmark = pytest.mark.skipif(not HAS_OPENPYXL, reason="openpyxl required")


# ── Shared chain runner ───────────────────────────────────────


def _extract_and_import_morrison(tmp_dir: Path, model: str):
    """Run extract → import for Morrison evidence, return (xlsx, jsonld) paths."""
    xlsx = tmp_dir / "morrison.xlsx"
    jsonld = tmp_dir / "morrison.jsonld"

    extract = run_uofa(
        "extract", str(MORRISON_DIR),
        "--model", model,
        "--pack", "vv40",
        "--output", str(xlsx),
    )
    assert extract.returncode == 0, (
        f"extract failed:\nSTDOUT: {extract.stdout}\nSTDERR: {extract.stderr}"
    )
    assert xlsx.exists(), f"extract did not produce {xlsx}"

    imp = run_uofa(
        "--pack", "vv40", "import", str(xlsx),
        "--output", str(jsonld),
    )
    assert imp.returncode == 0, (
        f"import failed:\nSTDOUT: {imp.stdout}\nSTDERR: {imp.stderr}"
    )
    assert jsonld.exists(), f"import did not produce {jsonld}"

    return xlsx, jsonld


# ── Mock variant: always runs in CI ───────────────────────────


@pytest.mark.skipif(not MORRISON_DIR.exists(), reason="Morrison evidence not available")
class TestMorrisonFullPipelineE2EMock:
    """Plumbing-level e2e: extract → import → check → rules for VV40 Morrison.

    Does NOT assert semantic rule firings (mock data is canned and doesn't
    reliably reproduce the COU1 weakener profile — see the per-step
    TestRules tests in test_integration.py, which use the pre-built
    morrison/cou1/uofa-morrison-cou1.jsonld fixture for that).
    """

    @pytest.fixture(scope="class")
    def chain(self, tmp_path_factory):
        tmp = tmp_path_factory.mktemp("morrison_e2e_mock")
        xlsx, jsonld = _extract_and_import_morrison(tmp, "mock")
        return {"tmp": tmp, "xlsx": xlsx, "jsonld": jsonld}

    def test_extract_produces_13_vv40_factors(self, chain):
        import openpyxl
        from uofa_cli.excel_constants import VV40_FACTOR_NAMES
        wb = openpyxl.load_workbook(chain["xlsx"])
        ws = wb["Credibility Factors"]
        found = [ws.cell(row=r, column=1).value for r in range(1, ws.max_row + 1)]
        vv40 = [v for v in found if v in VV40_FACTOR_NAMES]
        assert len(vv40) == 13, f"Morrison has {len(vv40)} VV40 factors, expected 13"

    def test_import_produces_valid_jsonld(self, chain):
        import json
        doc = json.loads(chain["jsonld"].read_text())
        assert "v0.5.jsonld" in str(doc.get("@context", "")), (
            "morrison.jsonld missing v0.5 context")
        assert "bindsRequirement" in doc, (
            "morrison.jsonld missing bindsRequirement")

    def test_rules_runs_without_crash(self, chain):
        result = run_uofa(
            "rules", str(chain["jsonld"]),
            "--pack", "vv40",
            "--build",
        )
        assert result.returncode == 0, (
            f"rules failed:\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}"
        )

    def test_check_runs_without_crash(self, chain):
        # Mock data may or may not satisfy every SHACL/C1 constraint; what we
        # require here is that `check` doesn't crash with a stack trace.
        # Specific pass/fail signal is exercised by TestCheck::test_check_morrison_all_pass
        # against the pre-built canonical fixture in test_integration.py.
        result = run_uofa(
            "check", str(chain["jsonld"]),
            "--pack", "vv40",
            "--skip-rules",  # skip Java-dependent C3 in plumbing test
        )
        # Both exit codes are acceptable plumbing outcomes; what we reject
        # is an unhandled crash (returncode > 1 or Python traceback in stderr).
        assert result.returncode in (0, 1), (
            f"check crashed unexpectedly (rc={result.returncode}):\n"
            f"STDOUT: {result.stdout}\nSTDERR: {result.stderr}"
        )
        assert "Traceback" not in result.stderr, (
            f"check produced a Python traceback:\n{result.stderr}"
        )


# ── Real-LLM variant: gated by env var ────────────────────────


@pytest.mark.skipif(not REAL_LLM_ENABLED,
                    reason="set UOFA_RUN_REAL_LLM=1 to run real-LLM e2e")
@pytest.mark.skipif(not MORRISON_DIR.exists(), reason="Morrison evidence not available")
class TestMorrisonFullPipelineE2ERealLLM:
    """Real-LLM e2e for Morrison.

    Assertions are intentionally loose — Morrison's shared evidence folder
    mixes COU1 + COU2 source material, so the LLM's extracted COU profile
    isn't predictable enough to assert a specific weakener firing pattern.
    What this variant catches: the LLM-output → import vocabulary gap (the
    class of bug that surfaced today via the NAFEMS aero demo), wheel
    bundling drift, and any regressions where the chain breaks but mocks
    pass.
    """

    @pytest.fixture(scope="class")
    def chain(self, tmp_path_factory):
        tmp = tmp_path_factory.mktemp("morrison_e2e_real")
        xlsx, jsonld = _extract_and_import_morrison(tmp, "ollama/qwen3.5:4b")
        return {"tmp": tmp, "xlsx": xlsx, "jsonld": jsonld}

    def test_extract_produces_13_vv40_factors(self, chain):
        import openpyxl
        from uofa_cli.excel_constants import VV40_FACTOR_NAMES
        wb = openpyxl.load_workbook(chain["xlsx"])
        ws = wb["Credibility Factors"]
        found = [ws.cell(row=r, column=1).value for r in range(1, ws.max_row + 1)]
        vv40 = [v for v in found if v in VV40_FACTOR_NAMES]
        assert len(vv40) == 13, f"Morrison has {len(vv40)} VV40 factors, expected 13"

    def test_rules_produces_some_firings_or_runs_clean(self, chain):
        result = run_uofa(
            "rules", str(chain["jsonld"]),
            "--pack", "vv40", "--build",
        )
        # Real LLM extractions of Morrison usually produce *some* weakener
        # firing (the assessment narrative cites multiple gaps); but if a
        # particular run produces a clean COU profile, that's also valid.
        # What we require is the rule engine completed without error.
        assert result.returncode == 0, (
            f"rules failed:\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}"
        )

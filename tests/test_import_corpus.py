"""Parameterized import tests driven by the test corpus manifest.

Run the corpus generator first:
    python tests/generate_test_corpus.py --output-dir tests/fixtures/import/

Then run these tests:
    pytest tests/test_import_corpus.py -v
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent
CORPUS_DIR = REPO_ROOT / "tests" / "fixtures" / "import"
MANIFEST_PATH = CORPUS_DIR / "tc_manifest.json"


def _load_manifest():
    if not MANIFEST_PATH.exists():
        return {}
    return json.loads(MANIFEST_PATH.read_text())


MANIFEST = _load_manifest()

# Skip all tests if corpus not generated
pytestmark = pytest.mark.skipif(
    not MANIFEST,
    reason="Test corpus not generated. Run: python tests/generate_test_corpus.py"
)


def run_uofa(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "uofa_cli", *args],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )


# ── Passing test cases ────────────────────────────────────────


PASSING_IDS = [tc_id for tc_id, tc in MANIFEST.items() if tc.get("expect") == "pass"]


@pytest.fixture(params=PASSING_IDS)
def passing_case(request, tmp_path):
    tc_id = request.param
    tc = MANIFEST[tc_id]
    xlsx = CORPUS_DIR / tc["file"]
    output = tmp_path / "output.jsonld"
    pack_args = []
    for p in tc["pack"]:
        pack_args += ["--pack", p]

    result = run_uofa("import", str(xlsx), "--output", str(output), *pack_args)
    assert result.returncode == 0, f"{tc_id} import failed: {result.stderr}"

    data = json.loads(output.read_text())
    return tc_id, tc, data, output


class TestPassingImport:
    """Tests for all passing test cases."""

    def test_valid_json(self, passing_case):
        _, _, data, _ = passing_case
        assert "@context" in data
        assert "id" in data

    def test_type_is_uofa(self, passing_case):
        _, _, data, _ = passing_case
        assert data["type"] == "UnitOfAssurance"

    def test_context_v04(self, passing_case):
        _, _, data, _ = passing_case
        ctx = data.get("@context", "")
        assert "v0.4" in str(ctx) or "v0_4" in str(ctx)

    def test_provenance_chain(self, passing_case):
        _, _, data, _ = passing_case
        chain = data.get("provenanceChain", [])
        assert len(chain) >= 1
        assert chain[-1]["activityType"] == "ImportActivity"
        assert "timestamp" in chain[-1]
        assert "toolVersion" in chain[-1]

    def test_factor_count(self, passing_case):
        tc_id, tc, data, _ = passing_case
        factors = data.get("hasCredibilityFactor", [])
        assert len(factors) == tc["factor_count"], (
            f"{tc_id}: expected {tc['factor_count']} factors, got {len(factors)}"
        )

    def test_validation_result_count(self, passing_case):
        tc_id, tc, data, _ = passing_case
        results = data.get("hasValidationResult", [])
        assert len(results) == tc["validation_result_count"], (
            f"{tc_id}: expected {tc['validation_result_count']} results, got {len(results)}"
        )

    def test_has_integrity_fields(self, passing_case):
        _, _, data, _ = passing_case
        assert data["hash"].startswith("sha256:")
        assert data["signature"].startswith("ed25519:")
        assert data["signatureAlg"] == "ed25519"
        assert data["canonicalizationAlg"] == "RDFC-1.0"

    def test_has_generated_time(self, passing_case):
        _, _, data, _ = passing_case
        assert "generatedAtTime" in data
        assert "T" in data["generatedAtTime"]

    def test_factor_standard_assignment(self, passing_case):
        tc_id, tc, data, _ = passing_case
        if "factor_standards" not in tc:
            return
        for factor in data.get("hasCredibilityFactor", []):
            assert "factorStandard" in factor, (
                f"{tc_id}: factor {factor['factorType']} missing factorStandard"
            )

    def test_uri_slugification(self, passing_case):
        tc_id, tc, data, _ = passing_case
        if "expected_id" not in tc:
            return
        assert data["id"] == tc["expected_id"], (
            f"{tc_id}: expected {tc['expected_id']}, got {data['id']}"
        )


# ── Error test cases ──────────────────────────────────────────


ERROR_IDS = [tc_id for tc_id, tc in MANIFEST.items() if tc.get("expect") == "error"]


@pytest.fixture(params=ERROR_IDS)
def error_case(request):
    tc_id = request.param
    tc = MANIFEST[tc_id]
    xlsx = CORPUS_DIR / tc["file"]
    pack_args = []
    for p in tc.get("pack", ["vv40"]):
        pack_args += ["--pack", p]

    result = run_uofa("import", str(xlsx), *pack_args)
    return tc_id, tc, result


# ── End-to-end roundtrip tests ────────────────────────────────

CONTEXT_FILE = str(REPO_ROOT / "spec" / "context" / "v0.4.jsonld")
KEY_FILE = REPO_ROOT / "keys" / "research.key"


def _import_sign_check(xlsx_path, output_path, packs):
    """Import → rewrite context to local → sign → check.

    Returns (import_result, check_result, doc).
    The @context is rewritten to local path so SHACL validation works
    without network access (same pattern as existing integration tests).
    """
    pack_args = []
    for p in packs:
        pack_args += ["--pack", p]

    # Step 1: Import
    import_result = run_uofa("import", str(xlsx_path), "--output", str(output_path), *pack_args)
    if import_result.returncode != 0:
        return import_result, None, None

    # Step 2: Rewrite @context to local path for offline SHACL validation
    doc = json.loads(output_path.read_text())
    doc["@context"] = CONTEXT_FILE
    output_path.write_text(json.dumps(doc, indent=2, sort_keys=True, ensure_ascii=False) + "\n")

    # Step 3: Sign
    sign_result = run_uofa("sign", str(output_path), "--key", str(KEY_FILE),
                           "--context", CONTEXT_FILE)
    if sign_result.returncode != 0:
        return import_result, sign_result, None

    # Step 4: Check (C1 integrity + C2 SHACL, skip C3 rules since Jena may not be available)
    check_result = run_uofa("check", str(output_path), "--skip-rules", *pack_args)

    # Reload signed doc
    doc = json.loads(output_path.read_text())
    return import_result, check_result, doc


class TestEndToEndImport:
    """End-to-end: import xlsx → sign → check passes for each pack and profile."""

    def test_vv40_complete_roundtrip(self, tmp_path):
        """TC-02: VV40 Complete (13 factors) → sign → C1+C2 pass."""
        xlsx = CORPUS_DIR / "tc02-vv40-complete-all-assessed.xlsx"
        output = tmp_path / "tc02.jsonld"

        import_r, check_r, doc = _import_sign_check(xlsx, output, ["vv40"])

        assert import_r.returncode == 0, f"Import failed: {import_r.stderr}"
        assert check_r.returncode == 0, (
            f"Check failed after import+sign:\nstdout: {check_r.stdout}\nstderr: {check_r.stderr}"
        )
        # Verify real integrity fields (not placeholders)
        assert doc["hash"] != "sha256:" + "0" * 64
        assert doc["signature"] != "ed25519:" + "0" * 128
        assert "ProfileComplete" in doc["conformsToProfile"]
        assert len(doc["hasCredibilityFactor"]) == 13
        assert all(f["factorStandard"] == "ASME-VV40-2018"
                    for f in doc["hasCredibilityFactor"])

    def test_nasa_complete_roundtrip(self, tmp_path):
        """TC-06: NASA Complete (19 factors) → sign → C1+C2 pass."""
        xlsx = CORPUS_DIR / "tc06-nasa-complete-19-factors.xlsx"
        output = tmp_path / "tc06.jsonld"

        import_r, check_r, doc = _import_sign_check(xlsx, output, ["nasa-7009b"])

        assert import_r.returncode == 0, f"Import failed: {import_r.stderr}"
        assert check_r.returncode == 0, (
            f"Check failed after import+sign:\nstdout: {check_r.stdout}\nstderr: {check_r.stderr}"
        )
        assert "ProfileComplete" in doc["conformsToProfile"]
        assert len(doc["hasCredibilityFactor"]) == 19
        # Verify NASA-only factors have correct standard
        nasa_factors = [f for f in doc["hasCredibilityFactor"]
                        if f["factorStandard"] == "NASA-STD-7009B"]
        assert len(nasa_factors) == 6
        # Verify NASA factors have assessmentPhase
        assert all("assessmentPhase" in f for f in nasa_factors)

    def test_vv40_minimal_roundtrip(self, tmp_path):
        """TC-01: VV40 Minimal → sign → C1+C2 pass."""
        xlsx = CORPUS_DIR / "tc01-vv40-minimal.xlsx"
        output = tmp_path / "tc01.jsonld"

        import_r, check_r, doc = _import_sign_check(xlsx, output, ["vv40"])

        assert import_r.returncode == 0, f"Import failed: {import_r.stderr}"
        assert check_r.returncode == 0, (
            f"Check failed after import+sign:\nstdout: {check_r.stdout}\nstderr: {check_r.stderr}"
        )
        assert "ProfileMinimal" in doc["conformsToProfile"]
        # Minimal has no factors
        assert "hasCredibilityFactor" not in doc or len(doc.get("hasCredibilityFactor", [])) == 0

    def test_nasa_minimal_roundtrip(self, tmp_path):
        """TC-09: NASA Minimal → sign → C1+C2 pass."""
        xlsx = CORPUS_DIR / "tc09-nasa-minimal.xlsx"
        output = tmp_path / "tc09.jsonld"

        import_r, check_r, doc = _import_sign_check(xlsx, output, ["nasa-7009b"])

        assert import_r.returncode == 0, f"Import failed: {import_r.stderr}"
        assert check_r.returncode == 0, (
            f"Check failed after import+sign:\nstdout: {check_r.stdout}\nstderr: {check_r.stderr}"
        )
        assert "ProfileMinimal" in doc["conformsToProfile"]

    def test_aero_hpt_blade_thermal_roundtrip(self, tmp_path):
        """TC-70: Aerospace HPT blade thermal (NASA, 19 factors, 3 gaps) → sign → C1+C2 pass."""
        xlsx = CORPUS_DIR / "tc70-aero-hpt-blade-thermal-gaps.xlsx"
        output = tmp_path / "tc70.jsonld"

        import_r, check_r, doc = _import_sign_check(xlsx, output, ["nasa-7009b"])

        assert import_r.returncode == 0, f"Import failed: {import_r.stderr}"
        assert check_r.returncode == 0, (
            f"Check failed after import+sign:\nstdout: {check_r.stdout}\nstderr: {check_r.stderr}"
        )

        # Profile and decision
        assert "ProfileComplete" in doc["conformsToProfile"]
        assert doc["decision"] == "Not accepted"

        # Factor counts: 19 total rows in sheet, 17 assessed (2 not-assessed excluded)
        factors = doc["hasCredibilityFactor"]
        assert len(factors) == 17

        # VV40 shared factors
        vv40 = [f for f in factors if f["factorStandard"] == "ASME-VV40-2018"]
        nasa = [f for f in factors if f["factorStandard"] == "NASA-STD-7009B"]
        assert len(vv40) == 12  # 13 - 1 not-assessed (numerical solver error)
        assert len(nasa) == 5   # 6 - 1 not-assessed (results uncertainty)

        # NASA factors have assessmentPhase
        for f in nasa:
            assert "assessmentPhase" in f, f"NASA factor {f['factorType']} missing assessmentPhase"

        # Gap 1: Discretization error — achieved < required
        disc = next(f for f in factors if f["factorType"] == "Discretization error")
        assert disc["requiredLevel"] == 3
        assert disc["achievedLevel"] == 1

        # Gap 2: Results uncertainty should NOT be in the output (not-assessed)
        ru_types = [f["factorType"] for f in factors]
        assert "Results uncertainty" not in ru_types

        # Gap 3: Validation result without UQ
        vrs = doc["hasValidationResult"]
        assert len(vrs) == 4
        paint_vr = next(v for v in vrs if "thermal-paint" in v.get("id", "").lower()
                        or "thermal paint" in v.get("name", "").lower())
        assert paint_vr["hasUncertaintyQuantification"] is False

        # Evidence types present
        types = {v["type"] for v in vrs}
        assert "ValidationResult" in types
        assert "ReviewActivity" in types

    def test_starter_xlsx_import_and_sign(self, tmp_path):
        """Existing starter file → import + sign succeeds.

        Note: the starter uses 'Conditional' decision and 'Other' device class
        which are valid domain values but outside the SHACL sh:in enum, so
        C2 SHACL may report violations. This test verifies the import pipeline
        and C1 integrity, not full SHACL conformance.
        """
        xlsx = REPO_ROOT / "examples" / "starters" / "uofa-starter-filled.xlsx"
        output = tmp_path / "starter.jsonld"

        import_r, check_r, doc = _import_sign_check(xlsx, output, ["vv40"])

        assert import_r.returncode == 0, f"Import failed: {import_r.stderr}"
        # C1 integrity should pass (hash + signature valid after signing)
        assert "Hash match" in check_r.stdout
        assert "Signature valid" in check_r.stdout
        assert "ProfileComplete" in doc["conformsToProfile"]
        assert len(doc["hasCredibilityFactor"]) > 0



    """Tests for all error test cases."""

    def test_error_exit_code(self, error_case):
        tc_id, tc, result = error_case
        assert result.returncode == tc["exit_code"], (
            f"{tc_id}: expected exit {tc['exit_code']}, got {result.returncode}\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )

    def test_error_message(self, error_case):
        tc_id, tc, result = error_case
        combined = result.stderr + result.stdout
        assert tc["error_contains"] in combined, (
            f"{tc_id}: expected '{tc['error_contains']}' in output\n"
            f"Got: {combined}"
        )

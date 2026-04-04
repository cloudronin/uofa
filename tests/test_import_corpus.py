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


class TestErrorImport:
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

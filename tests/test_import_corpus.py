"""Unified E2E import tests: structural + roundtrip + weakener count verification.

Fixtures are generated at test time from Python dicts — no committed xlsx files.
Weakener count tests require Java + Jena JAR and FAIL HARD if unavailable.

Run structural tests (no Java needed):
    pytest tests/test_import_corpus.py -k "Structural or Roundtrip" -v

Run weakener tests (requires Java + Jena):
    pytest tests/test_import_corpus.py -k "Weakener or TC70" -v

Full suite:
    pytest tests/test_import_corpus.py -v
"""

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

import importlib.util

_gen_path = Path(__file__).parent / "fixtures" / "import" / "generator.py"
_spec = importlib.util.spec_from_file_location("generator", _gen_path)
_generator = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_generator)
SPECS = _generator.SPECS
generate_fixture = _generator.generate_fixture

REPO_ROOT = Path(__file__).parent.parent
CONTEXT_FILE = str(REPO_ROOT / "spec" / "context" / "v0.4.jsonld")
KEY_FILE = REPO_ROOT / "keys" / "research.key"
TC70_XLSX = REPO_ROOT / "examples" / "starters" / "uofa-aero-hpt-blade-thermal-gaps.xlsx"

JAVA_AVAILABLE = shutil.which("java") is not None
JENA_JAR = REPO_ROOT / "weakener-engine" / "target" / "uofa-weakener-engine-0.1.0.jar"
JENA_AVAILABLE = JAVA_AVAILABLE and JENA_JAR.exists()

OPENPYXL_AVAILABLE = True
try:
    import openpyxl  # noqa: F401
except ImportError:
    OPENPYXL_AVAILABLE = False


def run_uofa(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "uofa_cli", *args],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )


# ── Session fixture: generate all xlsx files ──────────────────


@pytest.fixture(scope="session")
def fixture_dir(tmp_path_factory):
    """Generate all test xlsx files into a temp directory."""
    d = tmp_path_factory.mktemp("e2e_import")
    for name, spec in SPECS.items():
        generate_fixture(spec["data"], d / f"{name}.xlsx")
    return d


# ── Helpers ───────────────────────────────────────────────────


def _import_file(xlsx_path, output_path, packs):
    """Run uofa import and return (result, doc_or_None)."""
    pack_args = []
    for p in packs:
        pack_args += ["--pack", p]
    result = run_uofa("import", str(xlsx_path), "--output", str(output_path), *pack_args)
    doc = None
    if result.returncode == 0 and output_path.exists():
        doc = json.loads(output_path.read_text())
    return result, doc


def _import_sign_check(xlsx_path, output_path, packs):
    """Import → rewrite context → sign → SHACL check (no Java needed)."""
    pack_args = []
    for p in packs:
        pack_args += ["--pack", p]

    # Import
    result = run_uofa("import", str(xlsx_path), "--output", str(output_path), *pack_args)
    if result.returncode != 0:
        return result, None, None

    # Rewrite @context to local for offline SHACL
    doc = json.loads(output_path.read_text())
    doc["@context"] = CONTEXT_FILE
    output_path.write_text(json.dumps(doc, indent=2, sort_keys=True, ensure_ascii=False) + "\n")

    # Sign
    sign_r = run_uofa("sign", str(output_path), "--key", str(KEY_FILE), "--context", CONTEXT_FILE)
    if sign_r.returncode != 0:
        return result, sign_r, None

    # Check (C1+C2, skip rules)
    check_r = run_uofa("check", str(output_path), "--skip-rules", *pack_args)
    doc = json.loads(output_path.read_text())
    return result, check_r, doc


def _run_rules(jsonld_path, packs):
    """Run uofa rules --raw and parse weakener output."""
    pack_args = []
    for p in packs:
        pack_args += ["--pack", p]
    result = run_uofa("rules", str(jsonld_path), "--raw", *pack_args)
    return result, _parse_weakener_output(result.stdout)


def _parse_weakener_output(stdout: str) -> dict:
    """Parse uofa rules --raw output into structured counts."""
    patterns = {}
    total = 0

    for line in stdout.splitlines():
        m = re.search(r'SUMMARY:\s+(\d+)\s+weakener', line)
        if m:
            total = int(m.group(1))
        # Pattern lines: ⚠ W-AR-02 [Critical] — 1 hit(s)  or  ⚡ COMPOUND-01 [Critical] — 2 hit(s)
        m = re.search(r'[⚠⚡]\s+(W-[\w]+-\d+|COMPOUND-\d+)\s+\[\w+\]\s+.+?(\d+)\s+hit', line)
        if m:
            patterns[m.group(1)] = int(m.group(2))

    return {"total": total, "patterns": patterns}


# ── Parametrized ID lists ─────────────────────────────────────

PASSING_IDS = [k for k, v in SPECS.items() if v.get("expect_import") == "pass"]
ERROR_IDS = [k for k, v in SPECS.items() if v.get("expect_import") == "error"]
WEAKENER_IDS = [k for k, v in SPECS.items()
                if v.get("expect_import") == "pass" and v.get("expected_weakeners") is not None]
ROUNDTRIP_IDS = [k for k, v in SPECS.items()
                 if v.get("expect_import") == "pass" and v.get("expected_profile")]


# ── Structural tests (no Java needed) ────────────────────────


@pytest.mark.skipif(not OPENPYXL_AVAILABLE, reason="openpyxl not installed")
class TestImportStructural:
    """JSON shape assertions on imported files. No Java needed."""

    @pytest.fixture(params=PASSING_IDS)
    def imported(self, request, fixture_dir, tmp_path):
        name = request.param
        spec = SPECS[name]
        xlsx = fixture_dir / f"{name}.xlsx"
        output = tmp_path / "output.jsonld"
        result, doc = _import_file(xlsx, output, spec["packs"])
        assert result.returncode == 0, f"{name} import failed: {result.stderr}"
        return name, spec, doc

    def test_valid_json_ld(self, imported):
        _, _, doc = imported
        assert doc["type"] == "UnitOfAssurance"
        assert "@context" in doc
        assert "generatedAtTime" in doc

    def test_factor_count(self, imported):
        name, spec, doc = imported
        expected = spec.get("expected_factor_count")
        if expected is None:
            return
        actual = len(doc.get("hasCredibilityFactor", []))
        assert actual == expected, f"{name}: expected {expected} factors, got {actual}"

    def test_validation_result_count(self, imported):
        name, spec, doc = imported
        expected = spec.get("expected_vr_count")
        if expected is None:
            return
        actual = len(doc.get("hasValidationResult", []))
        assert actual == expected, f"{name}: expected {expected} VRs, got {actual}"

    def test_provenance_chain(self, imported):
        _, _, doc = imported
        chain = doc.get("provenanceChain", [])
        assert len(chain) >= 1
        assert chain[-1]["activityType"] == "ImportActivity"

    def test_uri_slugification(self, imported):
        name, spec, doc = imported
        expected_id = spec.get("expected_id")
        if expected_id:
            assert doc["id"] == expected_id


@pytest.mark.skipif(not OPENPYXL_AVAILABLE, reason="openpyxl not installed")
class TestImportErrors:
    """Error cases produce correct exit codes and messages."""

    @pytest.fixture(params=ERROR_IDS)
    def error_result(self, request, fixture_dir):
        name = request.param
        spec = SPECS[name]
        xlsx = fixture_dir / f"{name}.xlsx"
        result = run_uofa("import", str(xlsx), "--pack", spec["packs"][0])
        return name, spec, result

    def test_error_exit_code(self, error_result):
        name, _, result = error_result
        assert result.returncode == 1, f"{name}: expected exit 1, got {result.returncode}"

    def test_error_message(self, error_result):
        name, spec, result = error_result
        expected = spec["expect_error"]
        combined = result.stderr + result.stdout
        assert expected in combined, f"{name}: expected '{expected}' in output"


# ── Roundtrip tests (import → sign → SHACL, no Java) ─────────


@pytest.mark.skipif(not OPENPYXL_AVAILABLE, reason="openpyxl not installed")
class TestImportRoundtrip:
    """Import → sign → C1+C2 check passes for each profile."""

    @pytest.fixture(params=ROUNDTRIP_IDS)
    def roundtrip(self, request, fixture_dir, tmp_path):
        name = request.param
        spec = SPECS[name]
        xlsx = fixture_dir / f"{name}.xlsx"
        output = tmp_path / "output.jsonld"
        import_r, check_r, doc = _import_sign_check(xlsx, output, spec["packs"])
        return name, spec, import_r, check_r, doc

    def test_import_succeeds(self, roundtrip):
        name, _, import_r, _, _ = roundtrip
        assert import_r.returncode == 0, f"{name}: import failed: {import_r.stderr}"

    def test_shacl_passes(self, roundtrip):
        name, _, _, check_r, _ = roundtrip
        assert check_r.returncode == 0, (
            f"{name}: check failed:\nstdout: {check_r.stdout}\nstderr: {check_r.stderr}"
        )

    def test_integrity_valid(self, roundtrip):
        _, _, _, check_r, doc = roundtrip
        assert doc["hash"] != "sha256:" + "0" * 64
        assert "Hash match" in check_r.stdout


# ── Weakener count tests (requires Java + Jena) ──────────────


@pytest.mark.skipif(not OPENPYXL_AVAILABLE, reason="openpyxl not installed")
class TestImportWeakeners:
    """Import → sign → rules → assert exact weakener pattern IDs and counts.

    These tests FAIL HARD if Java/Jena is unavailable.
    """

    @pytest.fixture(params=WEAKENER_IDS)
    def weakener_result(self, request, fixture_dir, tmp_path):
        name = request.param
        spec = SPECS[name]

        if not JENA_AVAILABLE:
            pytest.fail(
                f"Java + Jena JAR required for weakener tests. "
                f"Install Java 17+ and run: cd weakener-engine && mvn package"
            )

        xlsx = fixture_dir / f"{name}.xlsx"
        output = tmp_path / "output.jsonld"

        # Import
        pack_args = []
        for p in spec["packs"]:
            pack_args += ["--pack", p]
        import_r = run_uofa("import", str(xlsx), "--output", str(output), *pack_args)
        assert import_r.returncode == 0, f"{name}: import failed: {import_r.stderr}"

        # Rewrite context + sign (needed for valid JSON-LD)
        doc = json.loads(output.read_text())
        doc["@context"] = CONTEXT_FILE
        output.write_text(json.dumps(doc, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
        sign_r = run_uofa("sign", str(output), "--key", str(KEY_FILE), "--context", CONTEXT_FILE)
        assert sign_r.returncode == 0, f"{name}: sign failed: {sign_r.stderr}"

        # Run rules
        rules_r, parsed = _run_rules(output, spec["packs"])
        return name, spec, rules_r, parsed

    def test_total_weakener_count(self, weakener_result):
        name, spec, _, parsed = weakener_result
        expected = spec["expected_weakeners"]["total"]
        assert parsed["total"] == expected, (
            f"{name}: expected {expected} total weakeners, got {parsed['total']}. "
            f"Patterns: {parsed['patterns']}"
        )

    def test_pattern_ids_and_counts(self, weakener_result):
        name, spec, _, parsed = weakener_result
        expected_patterns = spec["expected_weakeners"].get("patterns", {})
        for pid, expected_count in expected_patterns.items():
            actual = parsed["patterns"].get(pid, 0)
            assert actual == expected_count, (
                f"{name}: {pid} expected {expected_count}, got {actual}"
            )

    def test_no_unexpected_patterns(self, weakener_result):
        name, spec, _, parsed = weakener_result
        expected_pids = set(spec["expected_weakeners"].get("patterns", {}).keys())
        actual_pids = set(parsed["patterns"].keys())
        unexpected = actual_pids - expected_pids
        assert not unexpected, f"{name}: unexpected patterns: {unexpected}"


# ── TC-70 starter test (real xlsx, not generated) ─────────────


@pytest.mark.skipif(not OPENPYXL_AVAILABLE, reason="openpyxl not installed")
class TestTC70Starter:
    """The real TC-70 aerospace starter — 6 weakeners exact."""

    def test_tc70_import_roundtrip(self, tmp_path):
        """TC-70 imports and passes C1+C2."""
        if not TC70_XLSX.exists():
            pytest.skip(f"TC-70 starter not found: {TC70_XLSX}")
        output = tmp_path / "tc70.jsonld"
        import_r, check_r, doc = _import_sign_check(TC70_XLSX, output, ["nasa-7009b"])
        assert import_r.returncode == 0, f"Import failed: {import_r.stderr}"
        assert check_r.returncode == 0, f"Check failed: {check_r.stdout}"
        assert len(doc["hasCredibilityFactor"]) == 19

    def test_tc70_weakener_counts(self, tmp_path):
        """TC-70 produces exactly 6 weakeners: 3 L1 + 2 COMPOUND-01 + 1 COMPOUND-03."""
        if not TC70_XLSX.exists():
            pytest.skip(f"TC-70 starter not found: {TC70_XLSX}")
        if not JENA_AVAILABLE:
            pytest.fail(
                "Java + Jena JAR required. "
                "Install Java 17+ and run: cd weakener-engine && mvn package"
            )

        output = tmp_path / "tc70.jsonld"
        pack_args = ["--pack", "nasa-7009b"]
        run_uofa("import", str(TC70_XLSX), "--output", str(output), *pack_args)

        doc = json.loads(output.read_text())
        doc["@context"] = CONTEXT_FILE
        output.write_text(json.dumps(doc, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
        run_uofa("sign", str(output), "--key", str(KEY_FILE), "--context", CONTEXT_FILE)

        _, parsed = _run_rules(output, ["nasa-7009b"])
        assert parsed["total"] == 6, f"Expected 6 weakeners, got {parsed['total']}: {parsed['patterns']}"
        assert parsed["patterns"] == {
            "W-AR-02": 1,
            "W-EP-04": 1,
            "W-AR-05": 1,
            "COMPOUND-01": 2,
            "COMPOUND-03": 1,
        }

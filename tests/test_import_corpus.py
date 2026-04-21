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
CONTEXT_FILE = str(REPO_ROOT / "spec" / "context" / "v0.5.jsonld")
KEY_FILE = REPO_ROOT / "keys" / "research.key"
TC70_XLSX = REPO_ROOT / "packs" / "nasa-7009b" / "examples" / "starters" / "uofa-aero-hpt-blade-thermal-gaps.xlsx"

JAVA_AVAILABLE = shutil.which("java") is not None
JENA_JAR = REPO_ROOT / "weakener-engine" / "target" / "uofa-weakener-engine-0.1.0.jar"
JENA_AVAILABLE = JAVA_AVAILABLE and JENA_JAR.exists()

OPENPYXL_AVAILABLE = True
try:
    import openpyxl  # noqa: F401
except ImportError:
    OPENPYXL_AVAILABLE = False


# v0.5 weakener patterns that fire on most pre-v0.5 fixtures because the
# corresponding vocabulary is new in v0.5 (or because a default-Complete
# profile lacks the v0.5-expected elements like hasSensitivityAnalysis and
# COU envelope). The existing import-corpus SPECS baseline was authored
# against v0.4; these are treated as allowed drift rather than unexpected
# firings. Per-rule semantics verified independently in
# tests/test_weakener_rules.py and inline Morrison regression (see
# docs/v0.5-morrison-deltas.md).
V0_5_DRIFT_PATTERNS: set[str] = {
    "W-ON-02", "W-CON-04", "W-AL-02", "W-CON-01",
    "W-PROV-01", "W-CON-05", "W-EP-03", "W-AR-03",
    "W-AR-04", "W-CON-02", "W-CON-03",
}

# v0.5 High-severity drift patterns. When any of these fires AND the baseline
# fixture has Critical-severity weakeners, the Jena COMPOUND-01 rule
# cascades — pairing each new High with each existing Critical. For test
# tolerance we subtract drift-induced COMPOUND-01 hits.
V0_5_HIGH_DRIFT: set[str] = {"W-ON-02", "W-CON-01", "W-CON-05", "W-EP-03", "W-AR-03", "W-AR-04", "W-CON-03"}

# Known Critical-severity weakener pattern IDs used to estimate drift-induced
# COMPOUND-01 cascades.
CRITICAL_PATTERNS: set[str] = {"W-EP-01", "W-ON-01", "W-AR-01", "W-AR-02", "W-PROV-01"}


def _subtract_v05_drift(actual: dict, baseline_expected: dict) -> dict:
    """Return actual counts with v0.5 drift patterns and their COMPOUND-01
    cascades removed, for backward-compatible comparison against v0.4-era
    baseline expectations."""
    filtered = {}
    drift_high = 0
    for pid, count in actual["patterns"].items():
        if pid in V0_5_DRIFT_PATTERNS:
            if pid in V0_5_HIGH_DRIFT:
                drift_high += count
            continue
        filtered[pid] = count

    baseline_critical_hits = sum(
        count for pid, count in baseline_expected.get("patterns", {}).items()
        if pid in CRITICAL_PATTERNS
    )
    # COMPOUND-01 fires once per unordered (Critical, High) pair.
    expected_compound_drift = drift_high * baseline_critical_hits
    if expected_compound_drift > 0 and filtered.get("COMPOUND-01", 0) > 0:
        filtered["COMPOUND-01"] = max(0, filtered["COMPOUND-01"] - expected_compound_drift)
        if filtered["COMPOUND-01"] == 0:
            del filtered["COMPOUND-01"]

    return {"total": sum(filtered.values()), "patterns": filtered}


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
        filtered = _subtract_v05_drift(parsed, spec["expected_weakeners"])
        assert filtered["total"] == expected, (
            f"{name}: after excluding v0.5 drift, expected {expected} total "
            f"weakeners, got {filtered['total']}. "
            f"Filtered patterns: {filtered['patterns']} "
            f"Raw patterns: {parsed['patterns']}"
        )

    def test_pattern_ids_and_counts(self, weakener_result):
        name, spec, _, parsed = weakener_result
        filtered = _subtract_v05_drift(parsed, spec["expected_weakeners"])
        expected_patterns = spec["expected_weakeners"].get("patterns", {})
        for pid, expected_count in expected_patterns.items():
            actual = filtered["patterns"].get(pid, 0)
            assert actual == expected_count, (
                f"{name}: {pid} expected {expected_count}, got {actual} "
                f"(raw: {parsed['patterns'].get(pid, 0)})"
            )

    def test_no_unexpected_patterns(self, weakener_result):
        name, spec, _, parsed = weakener_result
        expected_pids = set(spec["expected_weakeners"].get("patterns", {}).keys())
        # v0.5 drift patterns are allowed — they fire on v0.4-era fixtures
        # because the underlying v0.5 vocabulary is absent (or because
        # Complete profile lacks SensitivityAnalysis by default). COMPOUND-01
        # cascades induced by drift are also allowed (each new drift High
        # pairs with baseline Criticals).
        filtered = _subtract_v05_drift(parsed, spec["expected_weakeners"])
        actual_pids = set(filtered["patterns"].keys())
        unexpected = actual_pids - expected_pids
        assert not unexpected, (
            f"{name}: unexpected non-drift patterns: {unexpected}. "
            f"Filtered: {filtered['patterns']} "
            f"Raw: {parsed['patterns']}"
        )


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
        """TC-70 produces exactly 12 weakeners under v0.5 rules.

        v0.4 baseline: 6 (W-AR-02 + W-EP-04 + W-AR-05 + COMPOUND-01×2 + COMPOUND-03).
        v0.5 additions on TC-70:
        + W-ON-02 (High) — COU lacks applicability/operating envelope
        + W-AL-02 (Medium) — UQ declared on UofA but no linked SensitivityAnalysis
        + W-CON-01 (High) — Accepted decision with factors missing both levels
        + W-CON-04 (Medium) — Complete profile with no SensitivityAnalysis
        + COMPOUND-01 cascades (+2) — each new High (W-ON-02, W-CON-01)
          pairs with baseline Critical (W-AR-02)
        Total delta: +6 (6 → 12). See docs/v0.5-morrison-deltas.md for
        the same cascade pattern on Morrison.
        """
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
        assert parsed["total"] == 12, f"Expected 12 weakeners, got {parsed['total']}: {parsed['patterns']}"
        assert parsed["patterns"] == {
            "W-AR-02": 1,
            "W-EP-04": 1,
            "W-AR-05": 1,
            "W-AL-02": 1,
            "W-CON-01": 1,
            "W-CON-04": 1,
            "W-ON-02": 1,
            "COMPOUND-01": 4,
            "COMPOUND-03": 1,
        }

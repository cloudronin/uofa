"""Integration tests for the uofa CLI.

Tests every subcommand against real example files to catch regressions.
Run with: pytest tests/test_integration.py -v
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

# ── Fixtures ──────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parent.parent
MORRISON = REPO_ROOT / "examples" / "morrison" / "cou1" / "uofa-morrison-cou1.jsonld"
MORRISON_COU2 = REPO_ROOT / "examples" / "morrison" / "cou2" / "uofa-morrison-cou2.jsonld"
MINIMAL_TEMPLATE = REPO_ROOT / "examples" / "templates" / "uofa-minimal-skeleton.jsonld"
COMPLETE_TEMPLATE = REPO_ROOT / "examples" / "templates" / "uofa-complete-skeleton.jsonld"

JAVA_AVAILABLE = shutil.which("java") is not None


def run_uofa(*args: str) -> subprocess.CompletedProcess:
    """Run a uofa CLI command and return the result."""
    return subprocess.run(
        [sys.executable, "-m", "uofa_cli", *args],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )


@pytest.fixture
def tmp_project(tmp_path):
    """Create a temporary directory with a copy of the minimal template."""
    uofa_file = tmp_path / "test-uofa.jsonld"
    shutil.copy(MINIMAL_TEMPLATE, uofa_file)
    return tmp_path, uofa_file


@pytest.fixture
def tmp_complete_project(tmp_path):
    """Create a temporary directory with a copy of the complete template."""
    uofa_file = tmp_path / "test-uofa-complete.jsonld"
    shutil.copy(COMPLETE_TEMPLATE, uofa_file)
    return tmp_path, uofa_file


# ── Test: uofa --help ─────────────────────────────────────────

class TestCLIBasics:
    def test_help(self):
        result = run_uofa("--help")
        assert result.returncode == 0
        assert "uofa_cli" in result.stdout or "validate" in result.stdout

    def test_version(self):
        result = run_uofa("--version")
        assert result.returncode == 0
        assert "0.2.0" in result.stdout

    def test_no_command_shows_help(self):
        result = run_uofa()
        assert result.returncode == 0
        assert "commands" in result.stdout or "validate" in result.stdout


# ── Test: uofa keygen ─────────────────────────────────────────

class TestKeygen:
    def test_keygen_creates_keypair(self, tmp_path):
        key_path = tmp_path / "test.key"
        result = run_uofa("keygen", str(key_path))
        assert result.returncode == 0

        assert key_path.exists(), "Private key not created"
        pub_path = key_path.with_suffix(".pub")
        assert pub_path.exists(), "Public key not created"

        # Verify PEM format
        assert key_path.read_text().startswith("-----BEGIN PRIVATE KEY-----")
        assert pub_path.read_text().startswith("-----BEGIN PUBLIC KEY-----")

    def test_keygen_creates_parent_dirs(self, tmp_path):
        key_path = tmp_path / "deep" / "nested" / "dir" / "test.key"
        result = run_uofa("keygen", str(key_path))
        assert result.returncode == 0
        assert key_path.exists()


# ── Test: uofa sign ───────────────────────────────────────────

class TestSign:
    def test_sign_fills_hash_and_signature(self, tmp_project):
        tmp_path, uofa_file = tmp_project

        # Generate key
        key_path = tmp_path / "test.key"
        run_uofa("keygen", str(key_path))

        # Sign
        result = run_uofa("sign", str(uofa_file), "--key", str(key_path))
        assert result.returncode == 0

        # Verify hash and signature were written
        with open(uofa_file) as f:
            doc = json.load(f)

        assert doc["hash"].startswith("sha256:"), f"Hash not set: {doc.get('hash')}"
        assert doc["signature"].startswith("ed25519:"), f"Signature not set: {doc.get('signature')}"
        assert len(doc["hash"]) == len("sha256:") + 64  # sha256 = 64 hex chars
        assert doc["hash"] != "sha256:0000000000000000000000000000000000000000000000000000000000000000"

    def test_sign_missing_key_fails(self, tmp_project):
        _, uofa_file = tmp_project
        result = run_uofa("sign", str(uofa_file), "--key", "/nonexistent/key.key")
        assert result.returncode != 0

    def test_sign_missing_file_fails(self):
        result = run_uofa("sign", "/nonexistent/file.jsonld", "--key", "keys/research.key")
        assert result.returncode != 0


# ── Test: uofa verify ─────────────────────────────────────────

class TestVerify:
    def test_verify_morrison_passes(self):
        result = run_uofa("verify", str(MORRISON))
        assert result.returncode == 0
        assert "Hash match" in result.stdout
        assert "Signature valid" in result.stdout

    def test_verify_unsigned_file_fails(self, tmp_project):
        _, uofa_file = tmp_project
        # Template has placeholder zeros — verification should fail
        result = run_uofa("verify", str(uofa_file))
        assert result.returncode != 0

    def test_sign_then_verify_roundtrip(self, tmp_project):
        tmp_path, uofa_file = tmp_project

        # Generate key, sign, then verify
        key_path = tmp_path / "test.key"
        pub_path = key_path.with_suffix(".pub")
        run_uofa("keygen", str(key_path))
        run_uofa("sign", str(uofa_file), "--key", str(key_path))

        result = run_uofa("verify", str(uofa_file), "--pubkey", str(pub_path))
        assert result.returncode == 0
        assert "Hash match" in result.stdout
        assert "Signature valid" in result.stdout

    def test_verify_tampered_file_fails(self, tmp_project):
        tmp_path, uofa_file = tmp_project

        # Sign the file
        key_path = tmp_path / "test.key"
        pub_path = key_path.with_suffix(".pub")
        run_uofa("keygen", str(key_path))
        run_uofa("sign", str(uofa_file), "--key", str(key_path))

        # Tamper with content
        with open(uofa_file) as f:
            doc = json.load(f)
        doc["name"] = "TAMPERED CONTENT"
        with open(uofa_file, "w") as f:
            json.dump(doc, f, indent=2)

        # Verify should fail
        result = run_uofa("verify", str(uofa_file), "--pubkey", str(pub_path))
        assert result.returncode != 0


# ── Test: uofa shacl ──────────────────────────────────────────

class TestShacl:
    def test_shacl_morrison_conforms(self):
        result = run_uofa("shacl", str(MORRISON))
        assert result.returncode == 0
        assert "Conforms" in result.stdout

    def test_shacl_minimal_template_conforms(self):
        """Templates with placeholder hashes should still pass SHACL (regex matches zeros)."""
        result = run_uofa("shacl", str(MINIMAL_TEMPLATE))
        assert result.returncode == 0

    def test_shacl_complete_template_conforms(self):
        result = run_uofa("shacl", str(COMPLETE_TEMPLATE))
        assert result.returncode == 0

    def test_shacl_invalid_file_fails(self, tmp_path):
        bad_file = tmp_path / "bad.jsonld"
        bad_file.write_text(json.dumps({
            "@context": "https://raw.githubusercontent.com/cloudronin/uofa/main/spec/context/v0.3.jsonld",
            "id": "https://example.org/bad",
            "type": "UnitOfAssurance",
            "conformsToProfile": "https://uofa.net/vocab#ProfileMinimal",
        }))
        result = run_uofa("shacl", str(bad_file))
        assert result.returncode != 0
        assert "violation" in result.stdout.lower() or "violation" in result.stderr.lower()

    def test_shacl_raw_mode(self):
        result = run_uofa("shacl", str(MORRISON), "--raw")
        assert result.returncode == 0
        assert "Conforms: True" in result.stdout

    def test_shacl_friendly_shows_fix_suggestions(self, tmp_path):
        """Friendly errors should include fix suggestions."""
        bad_file = tmp_path / "bad.jsonld"
        bad_file.write_text(json.dumps({
            "@context": "https://raw.githubusercontent.com/cloudronin/uofa/main/spec/context/v0.3.jsonld",
            "id": "https://example.org/bad",
            "type": "UnitOfAssurance",
            "conformsToProfile": "https://uofa.net/vocab#ProfileMinimal",
        }))
        result = run_uofa("shacl", str(bad_file))
        combined = result.stdout + result.stderr
        assert "Fix:" in combined or "fix" in combined.lower()


# ── Test: uofa rules ──────────────────────────────────────────

@pytest.mark.skipif(not JAVA_AVAILABLE, reason="Java not available")
class TestRules:
    def test_rules_morrison_detects_weakeners(self):
        result = run_uofa("rules", str(MORRISON), "--build")
        assert result.returncode == 0
        assert "weakener" in result.stdout
        assert "W-EP-01" in result.stdout
        assert "W-AL-01" in result.stdout
        assert "COMPOUND-01" in result.stdout

    def test_rules_missing_file_fails(self):
        result = run_uofa("rules", "/nonexistent/file.jsonld")
        assert result.returncode != 0


# ── Test: uofa check ──────────────────────────────────────────

class TestCheck:
    def test_check_morrison_all_pass(self):
        skip_rules = [] if JAVA_AVAILABLE else ["--skip-rules"]
        result = run_uofa("check", str(MORRISON), *skip_rules)
        assert result.returncode == 0
        assert "C2 SHACL" in result.stdout
        assert "C1 Integrity" in result.stdout

    def test_check_skip_rules(self):
        result = run_uofa("check", str(MORRISON), "--skip-rules")
        assert result.returncode == 0
        assert "skipped" in result.stdout

    @pytest.mark.skipif(not JAVA_AVAILABLE, reason="Java not available")
    def test_check_morrison_full_pipeline(self):
        result = run_uofa("check", str(MORRISON), "--build")
        assert result.returncode == 0
        assert "C2 SHACL" in result.stdout
        assert "C1 Integrity" in result.stdout
        assert "C3 Rules" in result.stdout

    def test_check_missing_file_fails(self):
        result = run_uofa("check", "/nonexistent/file.jsonld", "--skip-rules")
        assert result.returncode != 0


# ── Test: uofa validate ───────────────────────────────────────

class TestValidate:
    def test_validate_all_examples_conform(self):
        result = run_uofa("validate")
        assert result.returncode == 0
        assert "conform" in result.stdout.lower()

    def test_validate_custom_dir(self, tmp_path):
        """Validate on an empty dir should find no files."""
        result = run_uofa("validate", "--dir", str(tmp_path))
        assert result.returncode != 0  # no files found

    def test_validate_with_verify(self):
        result = run_uofa("validate", "--verify")
        assert result.returncode == 0
        assert "conform" in result.stdout.lower()
        assert "verified" in result.stdout.lower()


# ── Test: uofa schema ────────────────────────────────────────

class TestSchema:
    def test_schema_generates_file(self, tmp_path):
        output = tmp_path / "uofa.schema.json"
        result = run_uofa("schema", "--output", str(output))
        assert result.returncode == 0
        assert output.exists()

        with open(output) as f:
            schema = json.load(f)

        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        assert "oneOf" in schema  # Minimal vs Complete
        assert "CredibilityFactorShape" in schema.get("$defs", {})
        assert "WeakenerAnnotationShape" in schema.get("$defs", {})

    def test_schema_contains_factor_enum(self, tmp_path):
        output = tmp_path / "uofa.schema.json"
        run_uofa("schema", "--output", str(output))

        with open(output) as f:
            schema = json.load(f)

        # Find factorType enum in CredibilityFactorShape
        factor = schema["$defs"]["CredibilityFactorShape"]
        factor_type = factor["properties"].get("factorType", {})
        assert "enum" in factor_type
        assert "Software quality assurance" in factor_type["enum"]
        assert len(factor_type["enum"]) == 13  # V&V 40 Table 5-1

    def test_schema_contains_severity_enum(self, tmp_path):
        output = tmp_path / "uofa.schema.json"
        run_uofa("schema", "--output", str(output))

        with open(output) as f:
            schema = json.load(f)

        weakener = schema["$defs"]["WeakenerAnnotationShape"]
        severity = weakener["properties"].get("severity", {})
        assert "enum" in severity
        assert set(severity["enum"]) == {"Critical", "High", "Medium", "Low"}

    def test_schema_has_hash_pattern(self, tmp_path):
        output = tmp_path / "uofa.schema.json"
        run_uofa("schema", "--output", str(output))

        with open(output) as f:
            schema = json.load(f)

        # Check Minimal profile has hash pattern
        minimal_props = schema["oneOf"][0]["allOf"][1]["properties"]
        assert "pattern" in minimal_props.get("hash", {})
        assert "sha256" in minimal_props["hash"]["pattern"]


# ── Test: uofa init ───────────────────────────────────────────

class TestInit:
    def test_init_creates_project_structure(self, tmp_path):
        result = run_uofa("init", "test-project", "--dir", str(tmp_path))
        assert result.returncode == 0

        project_dir = tmp_path / "test-project"
        assert project_dir.exists()
        assert (project_dir / "test-project-cou1.jsonld").exists()
        assert (project_dir / "keys" / "test-project.key").exists()
        assert (project_dir / "keys" / "test-project.pub").exists()
        assert (project_dir / ".gitignore").exists()

        # Verify .gitignore excludes keys
        gitignore = (project_dir / ".gitignore").read_text()
        assert "*.key" in gitignore

    def test_init_template_has_project_name(self, tmp_path):
        run_uofa("init", "my-turbine", "--dir", str(tmp_path))
        uofa_file = tmp_path / "my-turbine" / "my-turbine-cou1.jsonld"

        with open(uofa_file) as f:
            doc = json.load(f)

        assert "my-turbine" in doc["id"]
        assert "my-turbine" in doc["name"]

    def test_init_complete_profile(self, tmp_path):
        result = run_uofa("init", "complete-project", "--profile", "complete", "--dir", str(tmp_path))
        assert result.returncode == 0

        uofa_file = tmp_path / "complete-project" / "complete-project-cou1.jsonld"
        with open(uofa_file) as f:
            doc = json.load(f)

        assert "ProfileComplete" in doc["conformsToProfile"]
        assert "hasCredibilityFactor" in doc

    def test_init_existing_dir_fails(self, tmp_path):
        (tmp_path / "existing").mkdir()
        result = run_uofa("init", "existing", "--dir", str(tmp_path))
        assert result.returncode != 0

    def test_init_then_sign_then_shacl_roundtrip(self, tmp_path):
        """Full end-to-end: init -> sign -> shacl validates."""
        run_uofa("init", "roundtrip", "--dir", str(tmp_path))

        project_dir = tmp_path / "roundtrip"
        uofa_file = project_dir / "roundtrip-cou1.jsonld"
        key_path = project_dir / "keys" / "roundtrip.key"

        # Sign
        result = run_uofa("sign", str(uofa_file), "--key", str(key_path))
        assert result.returncode == 0

        # SHACL validate
        result = run_uofa("shacl", str(uofa_file))
        assert result.returncode == 0
        assert "Conforms" in result.stdout


# ── Test: uofa diff ───────────────────────────────────────────

class TestDiff:
    def test_diff_identical_files(self):
        result = run_uofa("diff", str(MORRISON), str(MORRISON))
        assert result.returncode == 0
        assert "No divergence" in result.stdout

    def test_diff_different_weakener_profiles(self, tmp_path):
        """Create two files with different weakeners and verify divergence."""
        cou1 = tmp_path / "cou1.jsonld"
        cou2 = tmp_path / "cou2.jsonld"

        cou1.write_text(json.dumps({
            "@context": "https://raw.githubusercontent.com/cloudronin/uofa/main/spec/context/v0.3.jsonld",
            "id": "https://example.org/cou1", "type": "UnitOfAssurance",
            "name": "COU1",
            "hasWeakener": [
                {"type": "WeakenerAnnotation", "patternId": "W-AL-01", "severity": "High",
                 "affectedNode": "https://example.org/val1"},
                {"type": "WeakenerAnnotation", "patternId": "W-EP-01", "severity": "Critical",
                 "affectedNode": "https://example.org/claim1"},
            ]
        }))
        cou2.write_text(json.dumps({
            "@context": "https://raw.githubusercontent.com/cloudronin/uofa/main/spec/context/v0.3.jsonld",
            "id": "https://example.org/cou2", "type": "UnitOfAssurance",
            "name": "COU2",
            "hasWeakener": [
                {"type": "WeakenerAnnotation", "patternId": "W-EP-01", "severity": "Critical",
                 "affectedNode": "https://example.org/claim2"},
                {"type": "WeakenerAnnotation", "patternId": "W-AR-02", "severity": "Critical",
                 "affectedNode": "https://example.org/cou2"},
            ]
        }))

        result = run_uofa("diff", str(cou1), str(cou2))
        assert result.returncode == 0
        # Table-format output: divergent patterns marked
        assert "W-AL-01" in result.stdout
        assert "W-AR-02" in result.stdout
        assert "W-EP-01" in result.stdout
        assert "divergent" in result.stdout
        assert "same" in result.stdout
        # Divergence explanations section
        assert "Divergence Explanations" in result.stdout

    def test_diff_no_weakeners(self, tmp_path):
        """Two files with no weakeners should show no divergence."""
        f1 = tmp_path / "clean1.jsonld"
        f2 = tmp_path / "clean2.jsonld"
        for f in [f1, f2]:
            f.write_text(json.dumps({
                "@context": "https://raw.githubusercontent.com/cloudronin/uofa/main/spec/context/v0.3.jsonld",
                "id": "https://example.org/clean", "type": "UnitOfAssurance",
                "name": "Clean UofA",
            }))

        result = run_uofa("diff", str(f1), str(f2))
        assert result.returncode == 0
        assert "No divergence" in result.stdout

    def test_diff_missing_file_fails(self):
        result = run_uofa("diff", str(MORRISON), "/nonexistent/file.jsonld")
        assert result.returncode != 0

    def test_diff_identity_block(self):
        """COU identity metadata is displayed in the header."""
        result = run_uofa("diff", str(MORRISON), str(MORRISON))
        assert result.returncode == 0
        assert "COU Divergence Analysis" in result.stdout
        assert "Class II" in result.stdout
        assert "MRL 2" in result.stdout
        assert "Accepted" in result.stdout
        assert "Medium" in result.stdout

    def test_diff_morrison_cou1_vs_cou2(self):
        """Full Morrison demo: COU1 vs COU2 shows divergence with explanations."""
        result = run_uofa("diff", str(MORRISON), str(MORRISON_COU2))
        assert result.returncode == 0
        # Identity block shows both COUs
        assert "Class II" in result.stdout
        assert "Class III" in result.stdout
        # Weakener table present
        assert "Weakener Patterns" in result.stdout
        # Summary
        assert "divergence" in result.stdout
        # COU1 weakeners should appear as divergent since COU2 has empty hasWeakener
        assert "W-EP-01" in result.stdout

    def test_diff_compound_separation(self, tmp_path):
        """COMPOUND patterns appear in a separate sub-table."""
        cou1 = tmp_path / "cou1.jsonld"
        cou2 = tmp_path / "cou2.jsonld"

        cou1.write_text(json.dumps({
            "@context": "https://raw.githubusercontent.com/cloudronin/uofa/main/spec/context/v0.3.jsonld",
            "id": "https://example.org/cou1", "type": "UnitOfAssurance",
            "name": "COU1",
            "hasWeakener": [
                {"type": "WeakenerAnnotation", "patternId": "W-EP-01", "severity": "Critical",
                 "affectedNode": "https://example.org/claim1"},
                {"type": "WeakenerAnnotation", "patternId": "COMPOUND-01", "severity": "Critical",
                 "affectedNode": "https://example.org/cou1"},
            ]
        }))
        cou2.write_text(json.dumps({
            "@context": "https://raw.githubusercontent.com/cloudronin/uofa/main/spec/context/v0.3.jsonld",
            "id": "https://example.org/cou2", "type": "UnitOfAssurance",
            "name": "COU2",
            "hasWeakener": [
                {"type": "WeakenerAnnotation", "patternId": "W-EP-01", "severity": "Critical",
                 "affectedNode": "https://example.org/claim2"},
            ]
        }))

        result = run_uofa("diff", str(cou1), str(cou2))
        assert result.returncode == 0
        assert "Compound Patterns" in result.stdout
        assert "COMPOUND-01" in result.stdout

    def test_diff_severity_breakdown(self):
        """Summary section includes severity tier breakdown."""
        result = run_uofa("diff", str(MORRISON), str(MORRISON))
        assert result.returncode == 0
        assert "Critical" in result.stdout
        assert "High" in result.stdout

    def test_diff_minimal_profile_fallback(self, tmp_path):
        """Minimal profiles without COU metadata degrade gracefully."""
        f1 = tmp_path / "min1.jsonld"
        f2 = tmp_path / "min2.jsonld"
        for f in [f1, f2]:
            f.write_text(json.dumps({
                "@context": "https://raw.githubusercontent.com/cloudronin/uofa/main/spec/context/v0.3.jsonld",
                "id": "https://example.org/min", "type": "UnitOfAssurance",
                "name": "Minimal UofA",
            }))

        result = run_uofa("diff", str(f1), str(f2))
        assert result.returncode == 0
        assert "(not detected)" in result.stdout
        assert "No divergence" in result.stdout

    def test_diff_description_passthrough(self, tmp_path):
        """Weakener descriptions from annotations appear in explanations."""
        cou1 = tmp_path / "cou1.jsonld"
        cou2 = tmp_path / "cou2.jsonld"

        cou1.write_text(json.dumps({
            "@context": "https://raw.githubusercontent.com/cloudronin/uofa/main/spec/context/v0.3.jsonld",
            "id": "https://example.org/cou1", "type": "UnitOfAssurance",
            "name": "COU1",
            "hasWeakener": [
                {"type": "WeakenerAnnotation", "patternId": "W-AL-01", "severity": "High",
                 "affectedNode": "https://example.org/val1",
                 "description": "Missing UQ on validation result."},
            ]
        }))
        cou2.write_text(json.dumps({
            "@context": "https://raw.githubusercontent.com/cloudronin/uofa/main/spec/context/v0.3.jsonld",
            "id": "https://example.org/cou2", "type": "UnitOfAssurance",
            "name": "COU2",
            "hasWeakener": []
        }))

        result = run_uofa("diff", str(cou1), str(cou2))
        assert result.returncode == 0
        assert "Missing UQ on validation result." in result.stdout

    def test_diff_morrison_explanations_from_description(self):
        """Morrison COU1 weakener explanations come from the description field."""
        result = run_uofa("diff", str(MORRISON), str(MORRISON_COU2))
        assert result.returncode == 0
        # These come from the description field in the JSON-LD, not hardcoded
        assert "provenance chain is broken" in result.stdout
        assert "aleatory uncertainty is uncharacterized" in result.stdout


# ── Test: --repo-root flag works with subcommands ─────────────

class TestGlobalFlags:
    def test_repo_root_after_subcommand(self):
        result = run_uofa("verify", str(MORRISON), "--repo-root", str(REPO_ROOT))
        assert result.returncode == 0

    def test_no_color_flag(self):
        result = run_uofa("verify", str(MORRISON), "--no-color")
        assert result.returncode == 0
        # No ANSI escape codes in output
        assert "\033[" not in result.stdout


# ── Test: starter examples pass SHACL ─────────────────────────

class TestStarterExamples:
    def test_aero_starter_conforms(self):
        aero = REPO_ROOT / "examples" / "starters" / "uofa-aero-fatigue-minimal.jsonld"
        if aero.exists():
            result = run_uofa("shacl", str(aero))
            assert result.returncode == 0

    def test_structural_starter_conforms(self):
        bridge = REPO_ROOT / "examples" / "starters" / "uofa-structural-bridge-minimal.jsonld"
        if bridge.exists():
            result = run_uofa("shacl", str(bridge))
            assert result.returncode == 0


# ── Test: full round-trip (init -> edit -> sign -> check) ─────

class TestEndToEnd:
    def test_complete_workflow(self, tmp_path):
        """Simulates a real practitioner workflow end-to-end."""
        # 1. Init
        run_uofa("init", "e2e-project", "--profile", "complete", "--dir", str(tmp_path))
        project_dir = tmp_path / "e2e-project"
        uofa_file = project_dir / "e2e-project-cou1.jsonld"
        key_path = project_dir / "keys" / "e2e-project.key"
        pub_path = project_dir / "keys" / "e2e-project.pub"

        # 2. Customize the template
        with open(uofa_file) as f:
            doc = json.load(f)
        doc["name"] = "E2E Test — FEA bridge load rating"
        doc["hasContextOfUse"]["name"] = "COU1: Normal traffic loading"
        doc["hasDecisionRecord"]["rationale"] = "Model validated against field measurements."
        with open(uofa_file, "w") as f:
            json.dump(doc, f, indent=2, ensure_ascii=False)

        # 3. Sign
        result = run_uofa("sign", str(uofa_file), "--key", str(key_path))
        assert result.returncode == 0

        # 4. Verify
        result = run_uofa("verify", str(uofa_file), "--pubkey", str(pub_path))
        assert result.returncode == 0

        # 5. SHACL
        result = run_uofa("shacl", str(uofa_file))
        assert result.returncode == 0

        # 6. Full check (skip rules since this is a standalone file without Java dependency)
        result = run_uofa("check", str(uofa_file), "--skip-rules", "--pubkey", str(pub_path))
        assert result.returncode == 0
        assert "C2 SHACL" in result.stdout
        assert "C1 Integrity" in result.stdout

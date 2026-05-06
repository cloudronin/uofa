"""T8 production-OOS pytest harness covering spec §5.1–5.6.

Test sections:
  §5.1 Positive cases — 5 rules × 5 OOS calibration packages
  §5.2 Negative cases — rules vs in-scope packages
  §5.3 C3 regression with --oos — weakener firings unchanged
  §5.5 Backward-compat regression — default config byte-identical to baseline
  §5.6 Gating tests — CLI flag path, pack config path, force-off,
                       mutual exclusion, missing rule files

Spec reference: UofA_OOS_Productionization_Spec_v0_3.md §5.
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

import pytest

from uofa_cli.commands.check import run_structured
from uofa_cli.oos import config as oos_config
from uofa_cli.oos import runner as oos_runner
from uofa_cli.oos.snapshot import to_json, to_stable_dict


REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGES = REPO_ROOT / "specs/calibration/packages"
BASELINE_DIR = REPO_ROOT / "tests/fixtures/baseline_reports"
JAR = REPO_ROOT / "src/weakener-engine/target/uofa-weakener-engine-0.1.0.jar"
JAVA_AVAILABLE = shutil.which("java") is not None

needs_jar = pytest.mark.skipif(
    not (JAVA_AVAILABLE and JAR.exists()),
    reason="java + built JAR required",
)


def _check_args(file_path: Path, *, enable_oos: bool = False,
                disable_oos: bool = False) -> argparse.Namespace:
    """Build a minimal args namespace for check.run_structured()."""
    return argparse.Namespace(
        file=file_path,
        pubkey=None,
        context=None,
        rules=None,
        skip_rules=False,
        build=False,
        explain=False,
        explain_format="text",
        enable_oos=enable_oos,
        disable_oos=disable_oos,
    )


# ────────────────────────────────────────────────────────────────────────────
#  §5.1 Positive cases
# ────────────────────────────────────────────────────────────────────────────

POSITIVE_CASES = [
    ("cal-021", "oos_modelform_adequacy_warranted"),
    ("cal-022", "oos_tacit_knowledge_warranted"),
    ("cal-023", "oos_behavioral_compliance_warranted"),
    ("cal-024", "oos_jurisdictional_alignment_warranted"),
    ("cal-025", "oos_clinical_arbitration_warranted"),
]


@needs_jar
@pytest.mark.parametrize("cal_id,expected_rule", POSITIVE_CASES)
def test_51_positive_oos_firing_per_rule(cal_id: str, expected_rule: str):
    """§5.1 — each OOS rule fires on its corresponding calibration package."""
    pkg = PACKAGES / f"{cal_id}-out_of_scope-stub.jsonld"
    args = _check_args(pkg, enable_oos=True)
    result = run_structured(args)

    assert result.oos is not None, f"OOS phase did not run for {cal_id}"
    assert result.oos_error is None, f"OOS error: {result.oos_error}"

    firings = result.oos.firings
    matching = [f for f in firings if f["rule_name"] == expected_rule]
    assert len(matching) == 1, (
        f"Expected exactly 1 OOS firing of {expected_rule} on {cal_id}, "
        f"got {len(matching)}. All firings: {[f['rule_name'] for f in firings]}"
    )
    f = matching[0]
    assert f["verdict"] == "OUT-OF-SCOPE"
    assert "evidence_gap" in f
    assert "missing_evidence_type" in f["evidence_gap"]
    assert "would_support_defeater_evaluation" in f["evidence_gap"]
    assert "path_two_metadata" in f["evidence_gap"]


# ────────────────────────────────────────────────────────────────────────────
#  §5.2 Negative cases (over-firing discipline)
# ────────────────────────────────────────────────────────────────────────────

NEGATIVE_CASES = [
    "cal-001-correct_detection-inconsistent",
    "cal-005-correct_detection-incomplete-knowledge",
]


@needs_jar
@pytest.mark.parametrize("cal_stem", NEGATIVE_CASES)
def test_52_negative_no_spurious_firings(cal_stem: str):
    """§5.2 — in-scope packages produce zero OOS firings."""
    pkg = PACKAGES / f"{cal_stem}.jsonld"
    args = _check_args(pkg, enable_oos=True)
    result = run_structured(args)

    assert result.oos is not None
    assert result.oos.firings == [], (
        f"In-scope package {cal_stem} should produce no OOS firings, "
        f"got: {[f['rule_name'] for f in result.oos.firings]}"
    )


# ────────────────────────────────────────────────────────────────────────────
#  §5.3 C3 regression with --oos
# ────────────────────────────────────────────────────────────────────────────

@needs_jar
def test_53_c3_regression_with_oos_enabled():
    """§5.3 — C3 weakener firings unchanged when --oos is enabled."""
    pkg = PACKAGES / "cal-021-out_of_scope-stub.jsonld"

    # Baseline run (no --oos) → C3 firings via run_structured
    baseline_args = _check_args(pkg)
    baseline_result = run_structured(baseline_args)
    assert baseline_result.rules is not None
    baseline_firings = baseline_result.rules.firings

    # OOS-enabled run → C3 firings should be identical
    oos_args = _check_args(pkg, enable_oos=True)
    oos_result = run_structured(oos_args)
    assert oos_result.rules is not None
    oos_run_firings = oos_result.rules.firings

    assert oos_run_firings == baseline_firings, (
        f"C3 firings regressed when --oos enabled.\n"
        f"baseline: {baseline_firings}\n"
        f"with OOS: {oos_run_firings}"
    )


# ────────────────────────────────────────────────────────────────────────────
#  §5.5 Backward-compat regression (load-bearing)
# ────────────────────────────────────────────────────────────────────────────

@needs_jar
@pytest.mark.parametrize("cal_id", ["cal-021", "cal-022", "cal-023", "cal-024", "cal-025"])
def test_55_backward_compat_default_config(cal_id: str):
    """§5.5 — default config (no --oos flag, vv40 oos.enabled=false) produces
    byte-identical reports to the pre-v0.2 baselines.

    This is the load-bearing test for the omit-None serialization rule. If
    the `oos` field leaks into the JSON when disabled, this test catches it.
    """
    pkg = PACKAGES / f"{cal_id}-out_of_scope-stub.jsonld"
    args = _check_args(pkg)  # no --oos / --no-oos flags
    result = run_structured(args)

    fresh_json = to_json(result, repo_root=REPO_ROOT) + "\n"
    baseline_path = BASELINE_DIR / f"{cal_id}-out_of_scope-stub.json"
    assert baseline_path.exists(), f"Baseline missing: {baseline_path}"
    baseline_json = baseline_path.read_text()

    assert fresh_json == baseline_json, (
        f"Backward-compat regression on {cal_id}: snapshot diverged from "
        f"baseline. The OOS phase or snapshot serializer is leaking content "
        f"into the report when OOS is disabled."
    )


@needs_jar
def test_55_oos_field_absent_when_disabled():
    """§5.5 corollary — verify `oos` key is literally absent (not null)."""
    pkg = PACKAGES / "cal-021-out_of_scope-stub.jsonld"
    args = _check_args(pkg)
    result = run_structured(args)
    snap = to_stable_dict(result, repo_root=REPO_ROOT)
    assert "oos" not in snap, (
        f"`oos` key must be absent (not null) when OOS is disabled. "
        f"Top-level keys: {sorted(snap.keys())}"
    )
    assert "oos_error" not in snap


# ────────────────────────────────────────────────────────────────────────────
#  §5.6 Gating tests
# ────────────────────────────────────────────────────────────────────────────

@needs_jar
def test_56_cli_flag_force_on_path():
    """§5.6a — --oos against default vv40 (oos.enabled=false) → firings present,
    source=cli_flag_force_on."""
    pkg = PACKAGES / "cal-021-out_of_scope-stub.jsonld"
    args = _check_args(pkg, enable_oos=True)
    result = run_structured(args)

    assert result.oos is not None
    assert result.oos.config.source == oos_config.SOURCE_CLI_FORCE_ON
    assert len(result.oos.firings) >= 1

    snap = to_stable_dict(result, repo_root=REPO_ROOT)
    assert snap["oos"]["provenance"]["source"] == oos_config.SOURCE_CLI_FORCE_ON


@needs_jar
def test_56_pack_config_path_via_fixture(tmp_path):
    """§5.6b — fixture pack (oos.enabled:true), no --oos flag → firings present,
    source=pack_config.

    Builds a fake repo root with the committed fixture pack symlinked into
    `packs/`. Drives the resolver + runner directly (not the full CLI, which
    would require monkeypatching the paths module's global cache).
    """
    fake_root = tmp_path / "fake-repo"
    (fake_root / "spec" / "schemas").mkdir(parents=True)
    (fake_root / "spec" / "schemas" / "uofa_shacl.ttl").write_text("# stub\n")
    (fake_root / "packs").mkdir()
    fixture_pack = REPO_ROOT / "tests/fixtures/packs/vv40_oos_enabled"
    (fake_root / "packs" / "vv40_oos_enabled").symlink_to(fixture_pack)

    cfg = oos_config.resolve("vv40_oos_enabled", root=fake_root)
    assert cfg.enabled is True
    assert cfg.source == oos_config.SOURCE_PACK_CONFIG
    assert len(cfg.rule_files) == 1

    pkg = PACKAGES / "cal-021-out_of_scope-stub.jsonld"
    result = oos_runner.run_structured(pkg, cfg, root=REPO_ROOT)
    assert result is not None
    assert len(result.firings) == 1
    assert result.firings[0]["rule_name"] == "oos_modelform_adequacy_warranted"


@needs_jar
def test_56_force_off_path():
    """§5.6c — --no-oos against any pack → oos field absent from report
    despite pack config potentially being enabled."""
    pkg = PACKAGES / "cal-021-out_of_scope-stub.jsonld"
    args = _check_args(pkg, disable_oos=True)
    result = run_structured(args)

    assert result.oos is None
    snap = to_stable_dict(result, repo_root=REPO_ROOT)
    assert "oos" not in snap


def test_56_mutual_exclusion_raises():
    """§5.6d — --oos and --no-oos together → OOSConfigError before any work."""
    with pytest.raises(oos_config.OOSConfigError, match="mutually exclusive"):
        oos_config.resolve("vv40", enable_flag=True, disable_flag=True)


def test_56_missing_rule_files_raises(tmp_path):
    """§5.6e — --oos against a pack with no oos.rule_files → clear error."""
    fake_root = tmp_path / "fake-repo"
    pack_dir = fake_root / "packs" / "no_oos_pack"
    pack_dir.mkdir(parents=True)
    (pack_dir / "pack.json").write_text('{"name": "no_oos_pack"}')
    (fake_root / "spec" / "schemas").mkdir(parents=True)
    (fake_root / "spec" / "schemas" / "uofa_shacl.ttl").write_text("# stub\n")

    with pytest.raises(oos_config.OOSConfigError, match="does not declare OOS rules"):
        oos_config.resolve("no_oos_pack", enable_flag=True, root=fake_root)


# ────────────────────────────────────────────────────────────────────────────
#  Test report JSON (per spec §5.4)
# ────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session", autouse=True)
def _emit_test_report(request):
    """Write a structured test report after the session per spec §5.4."""
    yield
    # Collect all OOS-related test outcomes from the session.
    report = {
        "test_id": "production_oos_v0.1",
        "pytest_session_finish_status": getattr(request.session, "exitstatus", None),
    }
    out = REPO_ROOT / "tests/oos/test_report.json"
    try:
        out.write_text(json.dumps(report, indent=2) + "\n")
    except Exception:
        pass  # don't let the report-emit fail the session

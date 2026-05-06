"""T6c smoke tests for `uofa_cli.oos.config` and `uofa_cli.oos.runner`.

Coverage at this stage:
  - Resolver: all 5 paths from spec §2.2 resolution order
  - Runner: disabled-config short-circuit + enabled-config end-to-end on cal-021

Full §5.1–5.6 test plan lives in T8 (`tests/oos/test_production_oos.py`).
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from uofa_cli.oos import config as oos_config
from uofa_cli.oos import runner as oos_runner

REPO_ROOT = Path(__file__).resolve().parents[2]
JAR = REPO_ROOT / "src/weakener-engine/target/uofa-weakener-engine-0.1.0.jar"
JAVA_AVAILABLE = shutil.which("java") is not None


# ────────────────────────────────────────────────────────────────────────────
#  Resolver tests (no Java required)
# ────────────────────────────────────────────────────────────────────────────

def test_resolve_mutual_exclusion_raises():
    with pytest.raises(oos_config.OOSConfigError, match="mutually exclusive"):
        oos_config.resolve("vv40", enable_flag=True, disable_flag=True)


def test_resolve_disable_flag_returns_force_off():
    cfg = oos_config.resolve("vv40", disable_flag=True)
    assert cfg.enabled is False
    assert cfg.source == oos_config.SOURCE_CLI_FORCE_OFF
    assert cfg.rule_files == []


def test_resolve_default_no_oos_section_returns_default_omitted():
    """vv40/pack.json currently has no `oos` section — pre-T7 baseline."""
    cfg = oos_config.resolve("vv40")
    # vv40/pack.json may or may not have "oos" depending on T7 wiring.
    # Either way, default behavior should be enabled=False.
    assert cfg.enabled is False
    assert cfg.source in (
        oos_config.SOURCE_PACK_DEFAULT_OMITTED,
        oos_config.SOURCE_PACK_CONFIG,  # if T7 has wired { enabled: false }
    )


def test_resolve_enable_flag_without_rule_files_raises(tmp_path, monkeypatch):
    """Force-on against a pack that has no oos.rule_files → clear error."""
    # Use vv40 if pack.json has no rule_files OR a fake pack.
    # Simulate by building a minimal pack in tmp.
    fake_root = tmp_path / "fake-repo"
    pack_dir = fake_root / "packs" / "fakepak"
    pack_dir.mkdir(parents=True)
    (pack_dir / "pack.json").write_text('{"name": "fakepak"}')
    # Also need a marker for find_repo_root to accept fake_root
    (fake_root / "spec" / "schemas").mkdir(parents=True)
    (fake_root / "spec" / "schemas" / "uofa_shacl.ttl").write_text("# stub\n")

    with pytest.raises(oos_config.OOSConfigError, match="does not declare OOS rules"):
        oos_config.resolve("fakepak", enable_flag=True, root=fake_root)


def test_resolve_pack_config_enabled_with_rule_files(tmp_path):
    """Pack config with oos.enabled:true and rule_files → SOURCE_PACK_CONFIG."""
    fake_root = tmp_path / "fake-repo"
    pack_dir = fake_root / "packs" / "fakepak"
    rules_dir = pack_dir / "rules"
    rules_dir.mkdir(parents=True)
    (rules_dir / "test.rules").write_text("# stub\n")
    (pack_dir / "pack.json").write_text(
        '{"name": "fakepak", '
        '"oos": {"enabled": true, "rule_files": ["rules/test.rules"]}}'
    )
    (fake_root / "spec" / "schemas").mkdir(parents=True)
    (fake_root / "spec" / "schemas" / "uofa_shacl.ttl").write_text("# stub\n")

    cfg = oos_config.resolve("fakepak", root=fake_root)
    assert cfg.enabled is True
    assert cfg.source == oos_config.SOURCE_PACK_CONFIG
    assert len(cfg.rule_files) == 1
    assert cfg.rule_files[0].name == "test.rules"


def test_resolve_pack_config_enabled_but_missing_rule_files_raises(tmp_path):
    """Pack config with enabled:true but no rule_files → error."""
    fake_root = tmp_path / "fake-repo"
    pack_dir = fake_root / "packs" / "fakepak"
    pack_dir.mkdir(parents=True)
    (pack_dir / "pack.json").write_text(
        '{"name": "fakepak", "oos": {"enabled": true}}'
    )
    (fake_root / "spec" / "schemas").mkdir(parents=True)
    (fake_root / "spec" / "schemas" / "uofa_shacl.ttl").write_text("# stub\n")

    with pytest.raises(oos_config.OOSConfigError, match="no .*rule_files.* declared"):
        oos_config.resolve("fakepak", root=fake_root)


def test_resolve_enable_flag_nonexistent_rule_file_raises(tmp_path):
    """Pack declares rule_files but file doesn't exist on disk → error."""
    fake_root = tmp_path / "fake-repo"
    pack_dir = fake_root / "packs" / "fakepak"
    pack_dir.mkdir(parents=True)
    (pack_dir / "pack.json").write_text(
        '{"name": "fakepak", '
        '"oos": {"enabled": false, "rule_files": ["rules/nonexistent.rules"]}}'
    )
    (fake_root / "spec" / "schemas").mkdir(parents=True)
    (fake_root / "spec" / "schemas" / "uofa_shacl.ttl").write_text("# stub\n")

    with pytest.raises(oos_config.OOSConfigError, match="does not exist"):
        oos_config.resolve("fakepak", enable_flag=True, root=fake_root)


# ────────────────────────────────────────────────────────────────────────────
#  Runner tests (require Java + built JAR)
# ────────────────────────────────────────────────────────────────────────────

def test_runner_returns_none_when_disabled():
    """Disabled config → caller-friendly None (no JVM spawn)."""
    cfg = oos_config.OOSConfig(enabled=False, rule_files=[],
                                source=oos_config.SOURCE_CLI_FORCE_OFF)
    pkg = REPO_ROOT / "specs/calibration/packages/cal-021-out_of_scope-stub.jsonld"
    result = oos_runner.run_structured(pkg, cfg)
    assert result is None


@pytest.mark.skipif(not JAVA_AVAILABLE, reason="java not on PATH")
@pytest.mark.skipif(not JAR.exists(), reason="JAR not built; run mvn package")
def test_runner_invokes_engine_on_cal021():
    """End-to-end: resolver synthesizes an enabled config, runner invokes JAR."""
    rule_file = REPO_ROOT / "packs/vv40/rules/oos/oos_v0.1.rules"
    assert rule_file.exists(), f"OOS rule file missing: {rule_file}"

    cfg = oos_config.OOSConfig(
        enabled=True,
        rule_files=[rule_file],
        source=oos_config.SOURCE_CLI_FORCE_ON,
    )
    pkg = REPO_ROOT / "specs/calibration/packages/cal-021-out_of_scope-stub.jsonld"
    result = oos_runner.run_structured(pkg, cfg, root=REPO_ROOT)

    assert result is not None
    assert result.returncode == 0
    assert len(result.firings) == 1, (
        f"Expected exactly 1 OOS firing for cal-021 (model-form rule); "
        f"got {len(result.firings)}: {result.firings}"
    )
    firing = result.firings[0]
    assert firing["rule_name"] == "oos_modelform_adequacy_warranted"
    assert firing["verdict"] == "OUT-OF-SCOPE"
    assert "evidence_gap" in firing
    assert "missing_evidence_type" in firing["evidence_gap"]
    assert "would_support_defeater_evaluation" in firing["evidence_gap"]
    assert "path_two_metadata" in firing["evidence_gap"]
    # Provenance derived from config.source
    assert result.provenance["source"] == oos_config.SOURCE_CLI_FORCE_ON
    assert len(result.provenance["rule_files_loaded"]) == 1


@pytest.mark.skipif(not JAVA_AVAILABLE, reason="java not on PATH")
@pytest.mark.skipif(not JAR.exists(), reason="JAR not built; run mvn package")
def test_runner_zero_firings_on_in_scope_package():
    """In-scope package → no OOS firings; result.firings is empty list."""
    rule_file = REPO_ROOT / "packs/vv40/rules/oos/oos_v0.1.rules"
    cfg = oos_config.OOSConfig(
        enabled=True,
        rule_files=[rule_file],
        source=oos_config.SOURCE_CLI_FORCE_ON,
    )
    pkg = REPO_ROOT / "specs/calibration/packages/cal-001-correct_detection-inconsistent.jsonld"
    result = oos_runner.run_structured(pkg, cfg, root=REPO_ROOT)
    assert result is not None
    assert result.firings == []

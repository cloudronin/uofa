"""Phase E: cal-surr-* calibration packages drive the full check pipeline.

The committed packages under specs/calibration/packages/cal-surr-*.jsonld are
calibration anchors: each fires exactly its target detector through the real
extract->check path (SHACL -> derivation pre-pass -> C3 rules -> OOS).

- cal-surr-01/02/02b/03 calibrate the C3 W-SURR catalog (W-SURR-02 exercises
  BOTH severity arms: 02 = Not Accepted -> Critical, 02b = unrecorded -> High).
- cal-surr-04/05 calibrate the productive-OOS rules.

Skipped when the Jena engine (Java + built JAR) is unavailable.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from uofa_cli import paths
from uofa_cli.commands.check import run_structured

REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGES_DIR = REPO_ROOT / "specs" / "calibration" / "packages"


def _engine_available() -> bool:
    try:
        paths.java_executable()
    except Exception:
        return False
    return paths.jar_path().exists()


pytestmark = pytest.mark.skipif(
    not _engine_available(), reason="Jena engine (Java + built JAR) not available"
)


def _cal(prefix: str) -> Path:
    matches = sorted(PACKAGES_DIR.glob(f"{prefix}-*.jsonld"))
    assert matches, f"no calibration package matching {prefix}-*"
    return matches[0]


def _check_args(path: Path, *, enable_oos: bool = False) -> argparse.Namespace:
    # active_packs threaded explicitly (P2d-3): check resolves the active set via
    # paths.resolve_active_packs(args), which reads args.active_packs.
    return argparse.Namespace(
        file=path, pubkey=None, context=None, rules=None, skip_rules=False,
        build=False, enable_oos=enable_oos, disable_oos=False,
        no_color=True, verbose=False, repo_root=None, pack=["surrogate"],
        active_packs=["surrogate"],
    )


def _rule_firings(path: Path) -> dict:
    result = run_structured(_check_args(path))
    assert result.rules is not None and result.rules.returncode == 0, (
        getattr(result, "rules_error", None) or "rule engine error"
    )
    return {f["patternId"]: f["severity"] for f in (result.rules.firings or [])}


def _oos_rule_names(path: Path) -> list[dict]:
    result = run_structured(_check_args(path, enable_oos=True))
    assert result.oos is not None and result.oos.returncode == 0, (
        getattr(result, "oos_error", None) or result.oos.raw_stderr[:300]
    )
    return result.oos.firings or []


# ── C3 calibration ──────────────────────────────────────────────────────────


class TestC3Calibration:
    def test_cal_surr_01_fires_w_surr_01(self):
        assert _rule_firings(_cal("cal-surr-01")).get("W-SURR-01") == "High"

    def test_cal_surr_02_fires_w_surr_02_critical(self):
        # "cal-surr-02-*" matches cal-surr-02-... but not cal-surr-02b-...
        assert _rule_firings(_cal("cal-surr-02")).get("W-SURR-02") == "Critical"

    def test_cal_surr_02b_fires_w_surr_02_high(self):
        assert _rule_firings(_cal("cal-surr-02b")).get("W-SURR-02") == "High"

    def test_cal_surr_03_fires_w_surr_03(self):
        # Containment via the derivation pre-pass (pack derivations.enabled=true).
        assert _rule_firings(_cal("cal-surr-03")).get("W-SURR-03") == "High"


# ── Productive-OOS calibration ───────────────────────────────────────────────


class TestOOSCalibration:
    def test_cal_surr_04_fires_calibration_provenance_oos(self):
        names = {f.get("rule_name") for f in _oos_rule_names(_cal("cal-surr-04"))}
        assert "oos_surr_calibration_provenance_warranted" in names

    def test_cal_surr_05_fires_model_comparison_oos(self):
        firings = _oos_rule_names(_cal("cal-surr-05"))
        names = {f.get("rule_name") for f in firings}
        assert "oos_surr_model_comparison_warranted" in names
        # productive-OOS carries an actionable evidence gap
        for f in firings:
            if f.get("rule_name") == "oos_surr_model_comparison_warranted":
                assert f.get("evidence_gap")

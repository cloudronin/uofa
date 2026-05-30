"""Phase B: W-SURR-01/02/03 weakener firing tests (real Jena engine).

W-SURR-01 and W-SURR-02 are pure Jena and run via the rules engine directly.
W-SURR-03 consumes the derived _evalOutsideEnvelope flag, so it runs through the
derivation pre-pass first (the same derive -> rules path `uofa check` uses); the
containment derivation is also asserted in isolation via derived_only mode.

Skipped when the Jena engine (Java + built JAR) is unavailable, mirroring the
repo's gating of engine-dependent tests.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from uofa_cli import paths
from uofa_cli.commands import rules as rules_mod
from uofa_cli.derivations import config as derivation_config
from uofa_cli.derivations import runner as derivation_runner

SURR = "https://uofa.net/vocab/surrogate#"
CONTEXT = "https://raw.githubusercontent.com/cloudronin/uofa/main/spec/context/v0.5.jsonld"
BASE = "https://uofa.net/surrtest"


def _engine_available() -> bool:
    try:
        paths.java_executable()
    except Exception:
        return False
    return paths.jar_path().exists()


pytestmark = pytest.mark.skipif(
    not _engine_available(), reason="Jena engine (Java + built JAR) not available"
)


@pytest.fixture(autouse=True)
def _active_surrogate():
    prev = paths.get_active_pack()
    paths.set_active_pack(["surrogate"])
    yield
    paths.set_active_pack(prev)


# ── fixture builders (full IRIs for uofa-surr: terms; @vocab covers core) ──


def _envelope():
    return {
        "id": f"{BASE}/env",
        "type": f"{SURR}TrainingEnvelope",
        f"{SURR}hasDimension": [
            {"id": f"{BASE}/env/re", "type": f"{SURR}EnvelopeDimension",
             f"{SURR}dimensionName": "reynolds", f"{SURR}minBound": 2000000.0, f"{SURR}maxBound": 6000000.0},
            {"id": f"{BASE}/env/aoa", "type": f"{SURR}EnvelopeDimension",
             f"{SURR}dimensionName": "aoa", f"{SURR}minBound": -5.0, f"{SURR}maxBound": 15.0},
        ],
    }


def _eval_point(reynolds=3000000.0, aoa=4.0):
    return {
        "id": f"{BASE}/ep",
        "type": f"{SURR}EvaluationPoint",
        f"{SURR}hasCoordinate": [
            {"id": f"{BASE}/ep/re", "type": f"{SURR}PointCoordinate",
             f"{SURR}coordinateName": "reynolds", f"{SURR}coordinateValue": reynolds},
            {"id": f"{BASE}/ep/aoa", "type": f"{SURR}PointCoordinate",
             f"{SURR}coordinateName": "aoa", f"{SURR}coordinateValue": aoa},
        ],
    }


def _eval_region(re_min, re_max):
    return {
        "id": f"{BASE}/er",
        "type": f"{SURR}EvaluationRegion",
        f"{SURR}hasDimension": [
            {"id": f"{BASE}/er/re", "type": f"{SURR}EnvelopeDimension",
             f"{SURR}dimensionName": "reynolds", f"{SURR}minBound": re_min, f"{SURR}maxBound": re_max},
        ],
    }


def _base_pkg(**extra):
    pkg = {
        "@context": CONTEXT,
        "id": f"{BASE}/pkg",
        "type": ["UnitOfAssurance", "CredibilityEvidencePackage"],
        "conformsToProfile": "https://uofa.net/vocab#ProfileMinimal",
        "name": "surrogate rule fixture",
        f"{SURR}trainingEnvelope": _envelope(),
        f"{SURR}evaluationPoint": _eval_point(),
    }
    pkg.update(extra)
    return pkg


def _constraint(with_evidence: bool):
    pc = {"id": f"{BASE}/pc", "type": f"{SURR}PhysicsConstraint",
          f"{SURR}constraintId": "mass-conservation"}
    if with_evidence:
        pc[f"{SURR}hasConstraintCheckEvidence"] = {
            "id": f"{BASE}/pc/check", "type": f"{SURR}ConstraintCheckEvidence",
        }
    return pc


def _parent_snapshot(decision):
    snap = {"id": f"{BASE}/parent", "type": f"{SURR}ParentModelSnapshot",
            f"{SURR}parentCOU": "uofa:parent-rans",
            f"{SURR}snapshotTimestamp": "2026-05-30T00:00:00Z"}
    if decision is not None:
        snap[f"{SURR}parentDecision"] = decision
    return snap


def _write(tmp_path: Path, name: str, pkg: dict) -> Path:
    path = tmp_path / f"{name}.jsonld"
    path.write_text(json.dumps(pkg), encoding="utf-8")
    return path


def _firings(path: Path) -> dict:
    args = argparse.Namespace(
        file=path, rules=None, context=paths.context_file(),
        build=False, raw=False, format="summary", output=None,
    )
    result = rules_mod.run_structured(args)
    return {f["patternId"]: f["severity"] for f in result.firings}


def _firings_with_derivations(path: Path) -> dict:
    cfg = derivation_config.resolve("surrogate")
    deriv = derivation_runner.run(path, cfg, context_path=paths.context_file())
    enriched = deriv.enriched_package_path
    try:
        args = argparse.Namespace(
            file=enriched, rules=None, context=paths.context_file(),
            build=False, raw=False, format="summary", output=None,
        )
        result = rules_mod.run_structured(args)
        return {f["patternId"]: f["severity"] for f in result.firings}
    finally:
        if enriched is not None:
            enriched.unlink(missing_ok=True)


# ── W-SURR-01 — physics-constraint evidence missing ────────────────────────


class TestWSurr01:
    def test_fires_when_constraint_unchecked(self, tmp_path):
        pkg = _base_pkg()
        pkg[f"{SURR}declaredPhysicsConstraint"] = _constraint(with_evidence=False)
        firings = _firings(_write(tmp_path, "w01_pos", pkg))
        assert firings.get("W-SURR-01") == "High"

    def test_silent_when_constraint_checked(self, tmp_path):
        pkg = _base_pkg()
        pkg[f"{SURR}declaredPhysicsConstraint"] = _constraint(with_evidence=True)
        firings = _firings(_write(tmp_path, "w01_neg", pkg))
        assert "W-SURR-01" not in firings


# ── W-SURR-02 — unvalidated parent credibility (severity split) ────────────


class TestWSurr02:
    def test_critical_when_parent_not_accepted(self, tmp_path):
        pkg = _base_pkg()
        pkg[f"{SURR}parentModelSnapshot"] = _parent_snapshot("Not Accepted")
        firings = _firings(_write(tmp_path, "w02_crit", pkg))
        assert firings.get("W-SURR-02") == "Critical"

    def test_high_when_parent_decision_unrecorded(self, tmp_path):
        pkg = _base_pkg()
        pkg[f"{SURR}parentModelSnapshot"] = _parent_snapshot(None)
        firings = _firings(_write(tmp_path, "w02_high", pkg))
        assert firings.get("W-SURR-02") == "High"

    def test_silent_when_parent_accepted(self, tmp_path):
        pkg = _base_pkg()
        pkg[f"{SURR}parentModelSnapshot"] = _parent_snapshot("Accepted")
        firings = _firings(_write(tmp_path, "w02_neg", pkg))
        assert "W-SURR-02" not in firings


# ── W-SURR-03 — extrapolation beyond training envelope (containment) ───────


class TestWSurr03Derivation:
    def test_flag_materialized_when_point_outside(self, tmp_path):
        pkg = _base_pkg(**{f"{SURR}evaluationPoint": _eval_point(reynolds=8000000.0)})
        cfg = derivation_config.resolve("surrogate")
        deriv = derivation_runner.run(
            _write(tmp_path, "w03_derive_pos", pkg),
            cfg, context_path=paths.context_file(), derived_only=True,
        )
        try:
            text = deriv.derived_only_path.read_text(encoding="utf-8")
            assert "_evalOutsideEnvelope" in text
        finally:
            deriv.derived_only_path.unlink(missing_ok=True)

    def test_flag_absent_when_point_inside(self, tmp_path):
        pkg = _base_pkg()  # in-envelope by construction
        cfg = derivation_config.resolve("surrogate")
        deriv = derivation_runner.run(
            _write(tmp_path, "w03_derive_neg", pkg),
            cfg, context_path=paths.context_file(), derived_only=True,
        )
        try:
            text = deriv.derived_only_path.read_text(encoding="utf-8")
            assert "_evalOutsideEnvelope" not in text
        finally:
            deriv.derived_only_path.unlink(missing_ok=True)


class TestWSurr03Rule:
    def test_fires_when_point_outside(self, tmp_path):
        pkg = _base_pkg(**{f"{SURR}evaluationPoint": _eval_point(reynolds=8000000.0)})
        firings = _firings_with_derivations(_write(tmp_path, "w03_pos", pkg))
        assert firings.get("W-SURR-03") == "High"

    def test_fires_when_region_outside(self, tmp_path):
        pkg = _base_pkg()
        del pkg[f"{SURR}evaluationPoint"]
        pkg[f"{SURR}evaluationRegion"] = _eval_region(re_min=5500000.0, re_max=7000000.0)
        firings = _firings_with_derivations(_write(tmp_path, "w03_region", pkg))
        assert firings.get("W-SURR-03") == "High"

    def test_silent_when_point_inside(self, tmp_path):
        pkg = _base_pkg()  # reynolds=3e6, aoa=4 — inside the envelope
        firings = _firings_with_derivations(_write(tmp_path, "w03_neg", pkg))
        assert "W-SURR-03" not in firings

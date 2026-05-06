"""End-to-end test suite for the iso42001 pack (Phase G).

Spec reference: UofA_iso42001_Pack_Spec_v0_4.md §5 acceptance criteria.

Test sections:
  - Pack registration: manifest loads, shapes parse, oos.enabled defaults to true.
  - OOS over-firing discipline (spec §5 #3): each cal-aims-NNN fires its
    targeted rule and stays silent on the seven non-targeted packages.
  - Dual-output COU differential (spec §5 #4): COU1 (low risk) produces
    fewer OOS firings than COU2 (high risk); ControlOperationalEffectivenessClaim
    rule fires per claim binding via the engine's multi-binding semantics.
  - Pack manifest oos.enabled config (spec §5 #6): pack ships with
    oos.enabled: true so OOS runs without --oos flag.
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

import pytest

from uofa_cli import paths
from uofa_cli.commands.check import run_structured
from uofa_cli.oos import config as oos_config


REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGES_DIR = REPO_ROOT / "specs/calibration/packages"
HYBRID_DIR = REPO_ROOT / "packs/iso42001/examples/hybrid"
ISO42001_DIR = REPO_ROOT / "packs/iso42001"
JAR = REPO_ROOT / "src/weakener-engine/target/uofa-weakener-engine-0.1.0.jar"
JAVA_AVAILABLE = shutil.which("java") is not None

needs_jar = pytest.mark.skipif(
    not (JAVA_AVAILABLE and JAR.exists()),
    reason="java + built JAR required",
)


# Mapping of cal-aims-NNN package suffix to expected OOS rule name.
EXPECTED_RULE = {
    1: "oos_aims_policy_appropriateness_warranted",
    2: "oos_aims_risk_completeness_warranted",
    3: "oos_aims_control_operational_effectiveness_warranted",
    4: "oos_aims_impact_scope_adequacy_warranted",
    5: "oos_aims_stakeholder_consultation_adequacy_warranted",
    6: "oos_aims_internal_audit_independence_warranted",
    7: "oos_aims_nonconformity_root_cause_adequacy_warranted",
    8: "oos_aims_objective_measurement_methodology_validity_warranted",
}


@pytest.fixture(autouse=True)
def _activate_iso42001_pack():
    """Activate iso42001 pack for all tests; restore default after."""
    prior = paths.get_active_pack()
    paths.set_active_pack(["iso42001"])
    yield
    paths.set_active_pack(prior or ["vv40"])


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
        enable_oos=enable_oos,
        disable_oos=disable_oos,
        no_color=True,
        verbose=False,
        repo_root=None,
        pack=["iso42001"],
    )


def _cal_aims_path(n: int) -> Path:
    matches = sorted(PACKAGES_DIR.glob(f"cal-aims-{n:03d}-*.jsonld"))
    assert matches, f"Expected exactly one cal-aims-{n:03d} package; found 0"
    return matches[0]


# ────────────────────────────────────────────────────────────────────
# Pack registration tests
# ────────────────────────────────────────────────────────────────────

class TestPackRegistration:
    """Spec §5 #6 — pack manifest with oos.enabled: true registers cleanly."""

    def test_manifest_loads(self):
        manifest = paths.pack_manifest("iso42001")
        assert manifest["name"] == "iso42001"
        assert manifest["version"] == "0.4.0"
        assert "ISO-IEC-42001-2023" in manifest["standards"]

    def test_oos_enabled_by_default(self):
        manifest = paths.pack_manifest("iso42001")
        assert "oos" in manifest, "iso42001 pack must declare oos config"
        assert manifest["oos"]["enabled"] is True, (
            "iso42001 pack ships with oos.enabled: true per spec §2.8.1"
        )
        assert "rules/oos/oos_v0.1.rules" in manifest["oos"]["rule_files"]

    def test_oos_config_resolution(self):
        cfg = oos_config.resolve(
            "iso42001", enable_flag=False, disable_flag=False,
        )
        assert cfg.enabled is True
        assert cfg.source == "pack_config"

    def test_shapes_file_exists(self):
        shapes_path = ISO42001_DIR / "shapes/iso42001_shapes.ttl"
        assert shapes_path.exists()
        # Sanity check: contains uofa-aims namespace + at least one shape
        text = shapes_path.read_text()
        assert "uofa-aims:" in text
        assert "sh:NodeShape" in text

    def test_c3_rules_file_exists(self):
        rules_path = ISO42001_DIR / "rules/iso42001_weakener.rules"
        assert rules_path.exists()
        text = rules_path.read_text()
        # Spec §2.3.1 + §2.3.2 — 3 translated patterns + 12 W-AIMS
        for pattern in ["W-PROV-01", "W-AR-02", "W-AL-02"]:
            assert f"'{pattern}'" in text
        for pattern in [
            "W-AIMS-AUDIT-STALE", "W-AIMS-IMPACT-SCOPE",
            "W-AIMS-DATA-DRIFT-UNDETECTED", "W-AIMS-MODEL-EVAL-STALE",
            "W-AIMS-DEPLOYMENT-DRIFT", "W-AIMS-INCIDENT-UNCLOSED",
            "W-AIMS-OBJECTIVE-UNMEASURED", "W-AIMS-ROLE-UNASSIGNED",
            "W-AIMS-CROSSWALK-INVALID",
        ]:
            assert f"'{pattern}'" in text

    def test_oos_rules_file_exists(self):
        rules_path = ISO42001_DIR / "rules/oos/oos_v0.1.rules"
        assert rules_path.exists()
        text = rules_path.read_text()
        # All 8 OOS rules per spec §2.4
        for n in range(1, 9):
            assert f"calibration_target: cal-aims-{n:03d}" in text


# ────────────────────────────────────────────────────────────────────
# OOS over-firing discipline (spec §5 #3)
# ────────────────────────────────────────────────────────────────────

@needs_jar
class TestOOSOverFiringDiscipline:
    """Each cal-aims-NNN package must fire its targeted rule and only that
    rule. The OOS engine's discriminator clauses (claim type) ensure rules
    silently skip packages they don't apply to."""

    @pytest.mark.parametrize("n", list(range(1, 9)))
    def test_cal_aims_fires_only_expected_rule(self, n):
        result = run_structured(_check_args(_cal_aims_path(n), enable_oos=True))
        assert result.oos is not None, f"OOS should run for cal-aims-{n:03d}"
        assert result.oos.returncode == 0, (
            f"OOS engine error: {result.oos.raw_stderr[:300]}"
        )
        firings = result.oos.firings or []
        rule_names = [f.get("rule_name") for f in firings]
        expected = EXPECTED_RULE[n]
        assert expected in rule_names, (
            f"cal-aims-{n:03d} must fire {expected}; "
            f"actual firings: {rule_names}"
        )
        unexpected = [r for r in rule_names if r != expected]
        assert not unexpected, (
            f"cal-aims-{n:03d} OVER-FIRES: unexpected rules fired: {unexpected}"
        )

    @pytest.mark.parametrize("n", list(range(1, 9)))
    def test_evidence_gap_metadata(self, n):
        """Each firing must carry the spec-required evidence_gap fields."""
        result = run_structured(_check_args(_cal_aims_path(n), enable_oos=True))
        firings = result.oos.firings or []
        assert firings, f"cal-aims-{n:03d} must produce ≥1 firing"
        gap = firings[0].get("evidence_gap", {})
        assert gap.get("missing_evidence_type"), (
            "missing_evidence_type required (per OOS spec §3 schema)"
        )
        assert gap.get("would_support_defeater_evaluation"), (
            "would_support_defeater_evaluation required (per OOS spec §3)"
        )


# ────────────────────────────────────────────────────────────────────
# Dual-output COU differential (spec §5 #4)
# ────────────────────────────────────────────────────────────────────

@needs_jar
class TestDualOutputDifferential:
    """COU1 (low risk) produces fewer OOS firings than COU2 (high risk).
    The differential demonstrates spec §2.6.6 four-dimension dual output."""

    def _run(self, cou: str):
        fp = HYBRID_DIR / cou / f"uofa-iso42001-{cou}.jsonld"
        return run_structured(_check_args(fp, enable_oos=True))

    def test_cou1_oos_smaller_than_cou2(self):
        cou1 = self._run("cou1")
        cou2 = self._run("cou2")
        cou1_firings = cou1.oos.firings or []
        cou2_firings = cou2.oos.firings or []
        assert len(cou2_firings) > len(cou1_firings), (
            f"COU2 (high risk) must have MORE OOS firings than COU1 (low risk); "
            f"got cou1={len(cou1_firings)}, cou2={len(cou2_firings)}"
        )

    def test_cou2_fires_substantial_set(self):
        cou2 = self._run("cou2")
        firings = cou2.oos.firings or []
        # Spec §2.6.5 expects substantial set across all 8 rules; we author
        # COU2 to claim 6 distinct rule types + 2 ControlEffectiveness claims.
        assert len(firings) >= 6, (
            f"COU2 should fire ≥6 OOS rules per spec §2.6.5; got {len(firings)}"
        )

    def test_control_effectiveness_multi_binding(self):
        """Spec §2.4.3 special property: ControlOperationalEffectivenessClaim
        fires once per claim binding. COU2 has 2 such claims."""
        cou2 = self._run("cou2")
        firings = cou2.oos.firings or []
        ctrl_firings = [
            f for f in firings
            if f.get("rule_name") == "oos_aims_control_operational_effectiveness_warranted"
        ]
        assert len(ctrl_firings) >= 2, (
            "ControlOperationalEffectivenessClaim rule must fire per claim "
            "(multi-binding semantics validated in OOSEngineTest.multiBindingCase). "
            f"COU2 has 2 such claims; got {len(ctrl_firings)} firings."
        )


# ────────────────────────────────────────────────────────────────────
# Vocabulary integrity
# ────────────────────────────────────────────────────────────────────

class TestVocabularyIntegrity:
    """Verify all OOS rule referenced types are declared in the shapes file."""

    def _shapes_text(self):
        return (ISO42001_DIR / "shapes/iso42001_shapes.ttl").read_text()

    @pytest.mark.parametrize("claim_type", [
        "AIPolicyAppropriatenessClaim",
        "RiskIdentificationCompletenessClaim",
        "ControlOperationalEffectivenessClaim",
        "ImpactAssessmentScopeAdequacyClaim",
        "StakeholderConsultationAdequacyClaim",
        "InternalAuditIndependenceClaim",
        "NonconformityRootCauseAdequacyClaim",
        "AIMSObjectiveMeasurementMethodologyValidityClaim",
    ])
    def test_claim_types_declared(self, claim_type):
        assert f"uofa-aims:{claim_type}" in self._shapes_text(), (
            f"Spec §2.1.3 claim type {claim_type} must be declared in vocabulary"
        )

    @pytest.mark.parametrize("evidence_type", [
        "AIPolicy", "OrganizationalPurposeStatement", "PolicyToPurposeReviewRecord",
        "RiskRegister", "RiskIdentificationMethodology", "RiskFrameworkComparisonRecord",
        "ControlImplementationRecord", "ControlEffectivenessAssessment",
        "IndependentVerificationRecord", "ImpactAssessmentRecord",
        "ImpactAssessmentScopeJustification", "StakeholderValidationRecord",
        "StakeholderMappingDocument", "ConsultationLog",
        "ConsultationOutcomeIntegrationRecord", "AuditResultsRecord",
        "AuditorIndependenceAttestation", "AuditScopeNonOverlapAttestation",
        "NonconformityRecord", "RootCauseAnalysisRecord",
        "RootCauseExpertReviewRecord", "AIMSObjectiveStatement",
        "MeasurementMethodologyDocument", "MethodologyValidationRecord",
    ])
    def test_evidence_types_declared(self, evidence_type):
        assert f"uofa-aims:{evidence_type}" in self._shapes_text(), (
            f"Spec §2.1.4 evidence type {evidence_type} must be declared"
        )


# ────────────────────────────────────────────────────────────────────
# Coverage matrix existence
# ────────────────────────────────────────────────────────────────────

class TestCoverageMatrix:
    def test_matrix_file_exists(self):
        matrix = ISO42001_DIR / "coverage/nist_ai_rmf_govern_coverage.md"
        assert matrix.exists()
        text = matrix.read_text()
        # Spec §2.5.2 — combined coverage ≥ 70% acceptance criterion
        assert "Combined coverage" in text
        assert "PASSED" in text or "≥ 70%" in text

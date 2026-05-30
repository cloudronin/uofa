"""Firewall + contract tests for the SIP evidence-bundle schema (SIP §5, §8 / G3).

Asserts:
- a complete, well-formed bundle validates;
- a signed bundle (integrity fields present) still validates;
- the schema rejects ANY forbidden verdict field, parametrized over
  FORBIDDEN_TOKENS so the test grows automatically with the firewall list;
- the denylist defends freeform objects (provenance/config), not only the
  closed top level;
- the on-disk schema's root denylist stays in lockstep with forbidden.py;
- parentDecision is NOT a false positive for the forbidden 'decision' token.
"""

from __future__ import annotations

import jsonschema
import pytest

from uofa_cli.interrogate.forbidden import FORBIDDEN_TOKENS
from uofa_cli.interrogate.schema import load_schema, validate_bundle


def _base_bundle(**overrides) -> dict:
    """A complete, schema-valid SIP bundle (AirfRANS-shaped), minus signing."""
    bundle = {
        "bundleId": "sip-bundle-0001",
        "sipVersion": "0.1.0",
        "schemaVersion": "sip-evidence-bundle/v0.1",
        "generatedAt": "2026-05-30T12:00:00Z",
        "subject": {
            "surrogateId": "airfrans-baseline-mlp",
            "modelVersion": "1.0.0",
            "surrogateType": "data-driven-emulator",
            "modelFingerprint": "sha256:abc123",
            "adapterRef": "examples.airfrans.adapter.AirfRANSAdapter",
        },
        "declaredScope": {
            "trainingEnvelope": {
                "dimensions": [
                    {"name": "reynolds", "min": 2.0e6, "max": 6.0e6},
                    {"name": "aoa", "min": -5.0, "max": 15.0, "units": "deg"},
                ]
            },
            "evaluationPoint": {
                "coordinates": [
                    {"name": "reynolds", "value": 3.0e6},
                    {"name": "aoa", "value": 4.0, "units": "deg"},
                ]
            },
            "declaredPhysicsConstraint": [
                {
                    "constraintId": "mass-conservation",
                    "description": "div(u) = 0 within tolerance",
                    "kind": "conservation",
                }
            ],
        },
        "measurementProvenance": [
            {
                "measurementId": "m-residuals-cl",
                "producedBy": {"library": "numpy", "version": "1.26.4"},
                "config": {"norm": "l2"},
                "seed": 42,
                "runEnvironment": {"python": "3.11.8", "platform": "darwin"},
            }
        ],
        "measurements": {
            "referenceResiduals": [
                {
                    "quantityOfInterest": "lift_coefficient",
                    "statistics": {"count": 200, "mean": 0.012, "max": 0.08, "rms": 0.02},
                    "measurementRef": "m-residuals-cl",
                }
            ],
            "envelopeCoverage": {
                "benchmarkSpansEnvelope": True,
                "evaluationPointInEnvelope": True,
            },
            "physicsConstraintResidual": [
                {
                    "constraintId": "mass-conservation",
                    "statistics": {"mean": 1e-6, "max": 1e-4},
                }
            ],
            "uqCalibration": {
                "surrogateUQMethod": "conformal-prediction",
                "empiricalCoverage": 0.91,
                "nominalCoverage": 0.9,
            },
        },
        "parentModelSnapshot": {
            "parentCOU": "uofa:airfrans-rans-parent",
            "parentDecision": "Accepted",
            "parentMRL": 4,
            "parentSignatureTimestamp": "2026-01-15T00:00:00Z",
            "snapshotTimestamp": "2026-05-30T11:00:00Z",
        },
        "completeness": {
            "fieldsPresent": [
                "referenceResiduals",
                "envelopeCoverage",
                "physicsConstraintResidual",
                "uqCalibration",
            ],
            "fieldsDeliberatelyOmitted": [],
        },
        "provenance": {
            "@context": "http://www.w3.org/ns/prov#",
            "activity": {"id": "sip:run/0001", "type": "prov:Activity"},
            "entities": [
                {"id": "sip:surrogate", "type": "prov:Entity"},
                {"id": "sip:bundle", "type": "prov:Entity", "wasGeneratedBy": "sip:run/0001"},
            ],
        },
    }
    bundle.update(overrides)
    return bundle


class TestValidBundle:
    def test_complete_bundle_validates(self) -> None:
        validate_bundle(_base_bundle())  # no exception

    def test_signed_bundle_validates(self) -> None:
        bundle = _base_bundle()
        bundle.update(
            {
                "hash": "sha256:deadbeef",
                "signature": "ed25519:cafef00d",
                "signatureAlg": "ed25519",
                "canonicalizationAlg": "RDFC-1.0",
            }
        )
        validate_bundle(bundle)

    def test_parent_snapshot_optional(self) -> None:
        bundle = _base_bundle()
        del bundle["parentModelSnapshot"]
        validate_bundle(bundle)

    def test_parent_decision_absent_allowed(self) -> None:
        # W-SURR-02 'High' arm: parent decision not recorded (≠ Not Accepted).
        bundle = _base_bundle()
        del bundle["parentModelSnapshot"]["parentDecision"]
        validate_bundle(bundle)

    def test_evaluation_region_instead_of_point(self) -> None:
        bundle = _base_bundle()
        del bundle["declaredScope"]["evaluationPoint"]
        bundle["declaredScope"]["evaluationRegion"] = {
            "dimensions": [{"name": "reynolds", "min": 5.5e6, "max": 7.0e6}]
        }
        validate_bundle(bundle)


class TestFirewall:
    @pytest.mark.parametrize("token", FORBIDDEN_TOKENS)
    def test_forbidden_token_rejected_at_root(self, token: str) -> None:
        bundle = _base_bundle()
        bundle[token] = "PASS"
        with pytest.raises(jsonschema.ValidationError):
            validate_bundle(bundle)

    @pytest.mark.parametrize("token", FORBIDDEN_TOKENS)
    def test_forbidden_token_rejected_in_freeform_provenance(self, token: str) -> None:
        # provenance is an open object; the propertyNames denylist is the
        # active defense there (additionalProperties is not false).
        bundle = _base_bundle()
        bundle["provenance"][token] = "PASS"
        with pytest.raises(jsonschema.ValidationError):
            validate_bundle(bundle)

    def test_unknown_field_rejected(self) -> None:
        bundle = _base_bundle()
        bundle["someRandomField"] = 1
        with pytest.raises(jsonschema.ValidationError):
            validate_bundle(bundle)

    def test_nested_forbidden_in_measurements_rejected(self) -> None:
        bundle = _base_bundle()
        bundle["measurements"]["verdict"] = "PASS"
        with pytest.raises(jsonschema.ValidationError):
            validate_bundle(bundle)

    def test_measurement_region_denylist_in_lockstep_with_forbidden_module(self) -> None:
        # Addendum A5: the denylist is scoped to the measurement region (e.g. the
        # provenance freeform object), not the whole-bundle root.
        schema = load_schema()
        enum = schema["properties"]["provenance"]["propertyNames"]["not"]["enum"]
        assert set(enum) == set(FORBIDDEN_TOKENS), (
            "the measurement-region propertyNames denylist has drifted from "
            "src/uofa_cli/interrogate/forbidden.py FORBIDDEN_TOKENS"
        )

    def test_root_denylist_removed(self) -> None:
        # The whole-bundle denylist is gone (superseded by the signature-scoped
        # rule, A5); root additionalProperties:false still blocks stray fields.
        assert "propertyNames" not in load_schema()

    def test_parent_decision_not_a_false_positive(self) -> None:
        # 'decision' is forbidden as a bundle field, but parentDecision (the
        # parent COU's recorded decision, inherited provenance per §5.6) is
        # legitimate and must validate.
        bundle = _base_bundle()
        assert bundle["parentModelSnapshot"]["parentDecision"] == "Accepted"
        validate_bundle(bundle)


def _engineer_decision() -> dict:
    return {
        "decidedBy": "sha256:engineerkeyfingerprint",
        "acceptanceCriterion": "lift coefficient within 3% of reference over the training envelope",
        "decisionValue": "Accepted",
        "decisionRationale": "residuals within tolerance across the envelope",
        "decidedAt": "2026-05-30T13:00:00Z",
        "decisionSignature": "ed25519:deadbeef",
    }


class TestEngineerDecision:
    """Addendum A5: decision content is valid ONLY inside the engineerDecision block."""

    def test_signed_decision_block_with_accepted_validates(self) -> None:
        bundle = _base_bundle()
        bundle["engineerDecision"] = _engineer_decision()
        validate_bundle(bundle)  # 'Accepted' is permitted here

    def test_decision_block_requires_signature(self) -> None:
        bundle = _base_bundle()
        block = _engineer_decision()
        del block["decisionSignature"]
        bundle["engineerDecision"] = block
        with pytest.raises(jsonschema.ValidationError):
            validate_bundle(bundle)

    def test_decision_value_enum_enforced(self) -> None:
        bundle = _base_bundle()
        bundle["engineerDecision"] = {**_engineer_decision(), "decisionValue": "totally accepted"}
        with pytest.raises(jsonschema.ValidationError):
            validate_bundle(bundle)

    def test_decision_content_at_root_rejected(self) -> None:
        bundle = _base_bundle()
        bundle["decisionValue"] = "Accepted"  # outside the block → breach
        with pytest.raises(jsonschema.ValidationError):
            validate_bundle(bundle)

    def test_decision_content_in_measurements_rejected(self) -> None:
        bundle = _base_bundle()
        bundle["measurements"]["decisionValue"] = "Accepted"
        with pytest.raises(jsonschema.ValidationError):
            validate_bundle(bundle)

    def test_scoped_walker_exempts_block_but_catches_measurement_region(self) -> None:
        from uofa_cli.interrogate.forbidden import find_forbidden_in_measurement_region
        bundle = _base_bundle()
        # A forbidden token inside engineerDecision is exempt (signature governs it).
        bundle["engineerDecision"] = {**_engineer_decision(), "accepted": True}
        assert list(find_forbidden_in_measurement_region(bundle)) == []
        # The same token in the measurement region is caught.
        bundle["measurements"]["accepted"] = True
        assert "accepted" in [tok for _, tok in find_forbidden_in_measurement_region(bundle)]

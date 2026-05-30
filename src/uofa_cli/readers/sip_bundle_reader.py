"""v2 native SIP-bundle reader (SIP §7.3 v2, Addendum A6).

Maps a verified SIP evidence bundle directly to a `packs/surrogate` JSON-LD
UofA package, skipping the LLM extract step for measured fields. This is the
"one thin import adapter" of the staged-ingestion plan: it re-verifies the
bundle's signatures, validates the contract, then translates SIP §5 fields onto
the surrogate-pack vocabulary per the §7.4 field-to-pattern map.

Verification before mapping (A6):
  1. measurement signature MUST verify (else refuse — tampered/stale/wrong key);
  2. an engineerDecision is mapped to the UofA package's attributed decision
     ONLY when its signature verifies against the supplied human key over the
     correct scope; a missing/unverifiable decision yields a valid measurement
     package with NO inferred acceptance.
Both upstream signatures are preserved as provenance; UofA re-signs its own
package on import as usual.
"""

from __future__ import annotations

import json
from pathlib import Path

from uofa_cli.interrogate import signing
from uofa_cli.interrogate.schema import validate_bundle

CONTEXT_URL = "https://raw.githubusercontent.com/cloudronin/uofa/main/spec/context/v0.5.jsonld"
SURR = "https://uofa.net/vocab/surrogate#"


def read_sip_bundle(bundle_path: Path, *, measurement_pubkey: Path,
                    decision_pubkey: Path | None = None) -> dict:
    """Verify a SIP bundle and map it to a surrogate-pack JSON-LD package.

    Raises ValueError if the file is not a SIP bundle, fails schema validation,
    or its measurement signature does not verify.
    """
    bundle = json.loads(Path(bundle_path).read_text(encoding="utf-8"))
    if not signing.is_sip_bundle(bundle):
        raise ValueError(f"{bundle_path} is not a SIP evidence bundle (schemaVersion mismatch)")

    validate_bundle(bundle)  # contract + firewall (rejects forbidden decision content)

    hash_ok, sig_ok = signing.verify_measurement(bundle, Path(measurement_pubkey))
    if not (hash_ok and sig_ok):
        raise ValueError(
            "SIP measurement signature does not verify — refusing to import "
            "(tampered, stale, or wrong measurement key)."
        )

    decision = _verified_decision(bundle, decision_pubkey)
    return _map_to_jsonld(bundle, decision)


def _verified_decision(bundle: dict, decision_pubkey: Path | None) -> dict | None:
    """Return the engineer decision iff its signature verifies; else None (A6)."""
    block = bundle.get("engineerDecision")
    if not isinstance(block, dict) or decision_pubkey is None:
        return None
    ok, _reason = signing.verify_decision(bundle, Path(decision_pubkey))
    if not ok:
        return None
    return {
        "value": block.get("decisionValue"),
        "decidedBy": block.get("decidedBy"),
        "decidedAt": block.get("decidedAt"),
        "rationale": block.get("decisionRationale"),
        "criterion": block.get("acceptanceCriterion"),
    }


def _map_to_jsonld(bundle: dict, decision: dict | None) -> dict:
    subject = bundle.get("subject", {})
    scope = bundle.get("declaredScope", {})
    measurements = bundle.get("measurements", {})
    base = f"https://uofa.net/sip-import/{bundle.get('bundleId', 'bundle')}"

    doc: dict = {
        "@context": CONTEXT_URL,
        "id": base,
        "type": ["UnitOfAssurance", "CredibilityEvidencePackage"],
        "conformsToProfile": "https://uofa.net/vocab#ProfileMinimal",
        "name": f"SIP-imported surrogate COU — {subject.get('surrogateId', '?')}",
        # COU-framing fields the measurement bundle does not carry are neutral
        # defaults for the practitioner to refine; the risk profile is a COU
        # decision, not a measured quantity.
        "couName": f"COU for surrogate {subject.get('surrogateId', '?')}",
        "intendedUse": "Imported from a SIP measurement bundle; refine COU framing.",
        "assuranceLevel": "Medium",
        "modelRiskLevel": 2,
        "modelVersion": subject.get("modelVersion"),  # W-AR-04 reuse
        "hasContextOfUse": {
            "id": f"{base}/cou",
            "type": "ContextOfUse",
            "name": "SIP-imported context of use",
            "intendedUse": "Imported from a SIP measurement bundle.",
            # W-ON-02 stays silent because the operating envelope IS declared.
            "hasOperatingEnvelope": f"{base}/env",
        },
    }

    # ── Declared scope → training envelope (W-ON-02 presence, W-SURR-03 containment)
    training = scope.get("trainingEnvelope", {})
    doc[f"{SURR}trainingEnvelope"] = {
        "id": f"{base}/env",
        "type": f"{SURR}TrainingEnvelope",
        f"{SURR}hasDimension": [
            {"id": f"{base}/env/{d['name']}", "type": f"{SURR}EnvelopeDimension",
             f"{SURR}dimensionName": d["name"], f"{SURR}minBound": d["min"], f"{SURR}maxBound": d["max"]}
            for d in training.get("dimensions", [])
        ],
    }
    if scope.get("evaluationPoint"):
        doc[f"{SURR}evaluationPoint"] = {
            "id": f"{base}/ep", "type": f"{SURR}EvaluationPoint",
            f"{SURR}hasCoordinate": [
                {"id": f"{base}/ep/{c['name']}", "type": f"{SURR}PointCoordinate",
                 f"{SURR}coordinateName": c["name"], f"{SURR}coordinateValue": c["value"]}
                for c in scope["evaluationPoint"].get("coordinates", [])
            ],
        }
    if scope.get("evaluationRegion"):
        doc[f"{SURR}evaluationRegion"] = {
            "id": f"{base}/er", "type": f"{SURR}EvaluationRegion",
            f"{SURR}hasDimension": [
                {"id": f"{base}/er/{d['name']}", "type": f"{SURR}EnvelopeDimension",
                 f"{SURR}dimensionName": d["name"], f"{SURR}minBound": d["min"], f"{SURR}maxBound": d["max"]}
                for d in scope["evaluationRegion"].get("dimensions", [])
            ],
        }

    # ── Physics constraints: a measured residual IS the check evidence (W-SURR-01).
    # A declared constraint with no matching physicsConstraintResidual has no
    # check evidence → W-SURR-01 fires (the auditability gap made real from
    # measured evidence).
    measured_constraints = {r.get("constraintId") for r in measurements.get("physicsConstraintResidual", [])}
    constraint_nodes = []
    for constraint in scope.get("declaredPhysicsConstraint", []):
        cid = constraint["constraintId"]
        node = {"id": f"{base}/pc/{cid}", "type": f"{SURR}PhysicsConstraint", f"{SURR}constraintId": cid}
        if constraint.get("kind"):
            node[f"{SURR}constraintKind"] = constraint["kind"]
        if cid in measured_constraints:
            node[f"{SURR}hasConstraintCheckEvidence"] = {
                "id": f"{base}/pc/{cid}/check", "type": f"{SURR}ConstraintCheckEvidence",
                "name": f"Measured constraint residual for {cid} (from SIP)",
            }
        constraint_nodes.append(node)
    if constraint_nodes:
        doc[f"{SURR}declaredPhysicsConstraint"] = constraint_nodes

    # ── Surrogate UQ method (W-AL-02 reuse maps here).
    uq_method = measurements.get("uqCalibration", {}).get("surrogateUQMethod")
    if uq_method:
        doc[f"{SURR}surrogateUQMethod"] = uq_method

    # ── Benchmark provenance (envelopeCoverage → W-SURR-04 candidate support).
    doc[f"{SURR}hasBenchmarkProvenance"] = {
        "id": f"{base}/benchprov", "type": f"{SURR}BenchmarkProvenance",
        "name": "Benchmark provenance imported from the SIP bundle",
    }

    # ── Embedded parent snapshot (W-SURR-02).
    snapshot = bundle.get("parentModelSnapshot")
    if isinstance(snapshot, dict):
        node = {"id": f"{base}/parent", "type": f"{SURR}ParentModelSnapshot",
                f"{SURR}parentCOU": snapshot.get("parentCOU"),
                f"{SURR}snapshotTimestamp": snapshot.get("snapshotTimestamp")}
        if snapshot.get("parentDecision") is not None:
            node[f"{SURR}parentDecision"] = snapshot["parentDecision"]
        if snapshot.get("parentMRL") is not None:
            node[f"{SURR}parentMRL"] = str(snapshot["parentMRL"])
        doc[f"{SURR}parentModelSnapshot"] = node

    # ── Attributed engineer decision — ONLY when its signature verified (A4/A6).
    # 'decision'/'outcome' are legitimate in the UofA package (the firewall
    # applies to the SIP bundle's measurement region, not here).
    if decision and decision.get("value"):
        doc["decision"] = decision["value"]
        doc["hasDecisionRecord"] = {
            "id": f"{base}/decision", "type": "DecisionRecord",
            "outcome": decision["value"], "actor": decision.get("decidedBy"),
            "decidedAt": decision.get("decidedAt"), "rationale": decision.get("rationale"),
        }

    # ── Preserve the upstream SIP signatures as provenance (A6 step 4).
    sip_provenance = {
        "sipBundleId": bundle.get("bundleId"),
        "sipBundleHash": bundle.get("hash"),
        "sipMeasurementSignature": bundle.get("signature"),
        "sipMeasurementSignatureVerified": True,
    }
    if decision:
        sip_provenance["engineerDecisionVerified"] = True
        sip_provenance["engineerDecisionSignature"] = bundle.get("engineerDecision", {}).get("decisionSignature")
    doc["sipProvenance"] = sip_provenance

    return doc

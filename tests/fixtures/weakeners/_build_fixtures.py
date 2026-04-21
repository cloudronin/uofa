"""Generator for v0.5 weakener-rule unit-test fixtures.

Writes minimal JSON-LD files under tests/fixtures/weakeners/{pattern_id}/
for positive/negative/boundary cases. Run once:

    python tests/fixtures/weakeners/_build_fixtures.py

Fixtures use the v0.5 context and conform to the UofA profile where needed.
Kept deliberately minimal — each fixture isolates the rule-specific
preconditions. SHACL validity is not required (uofa rules runs Jena
inference regardless).

Delete this script after running if you don't want it committed — the
generated JSON-LD files are the test surface; the generator itself is
a convenience.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
# Fixtures live at tests/fixtures/weakeners/{pid}/*.jsonld — 4 levels deep
# under the repo root, so the relative context path needs ../../../../.
CTX = "../../../../spec/context/v0.5.jsonld"

# Shared JSON-LD signing boilerplate for minimal-profile fixtures.
SIG = {
    "generatedAtTime": "2026-04-01T00:00:00Z",
    "hash": "sha256:" + "a" * 64,
    "signature": "ed25519:" + "b" * 64,
    "hasDecisionRecord": "https://example.org/dr/x",
}


def _base(pid: str, suffix: str = "") -> dict:
    """Minimal Complete-profile UofA that satisfies most structural checks."""
    uri = f"https://example.org/uofa/{pid.lower()}-{suffix or 'base'}"
    return {
        "@context": CTX,
        "id": uri,
        "type": "UnitOfAssurance",
        "conformsToProfile": "https://uofa.net/vocab#ProfileComplete",
        "bindsRequirement": "https://example.org/req/r1",
        "bindsClaim": "https://example.org/claim/c1",
        "bindsModel": "https://example.org/model/m1",
        "bindsDataset": "https://example.org/dataset/d1",
        "hasContextOfUse": "https://example.org/cou/cou1",
        "hasValidationResult": ["https://example.org/result/vr1"],
        "wasDerivedFrom": "https://example.org/prior",
        "wasAttributedTo": "https://example.org/actor",
        "modelRiskLevel": 3,
        "hasCredibilityFactor": [
            {
                "type": "CredibilityFactor",
                "factorType": "Model form",
                "factorStatus": "assessed",
                "requiredLevel": 3,
                "achievedLevel": 3,
            }
        ],
        "hasSensitivityAnalysis": "https://example.org/sa/sa1",
        "criteriaSet": "https://example.org/criteria/set1",
        **SIG,
    }


def write(path: Path, doc: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=2) + "\n")


# ═════════════════════════════════════════════════════════════════════════════
# W-ON-02 — Unbounded Applicability
# ═════════════════════════════════════════════════════════════════════════════
pid = "W-ON-02"
d = ROOT / pid

# Positive: COU has neither applicability constraint nor operating envelope
pos = _base(pid, "pos")
pos["hasContextOfUse"] = {
    "id": "https://example.org/cou/cou1", "type": "ContextOfUse",
    "intendedUse": "Demo",
}
write(d / "positive.jsonld", pos)

# Negative: COU has hasApplicabilityConstraint
neg = _base(pid, "neg")
neg["hasContextOfUse"] = {
    "id": "https://example.org/cou/cou1", "type": "ContextOfUse",
    "hasApplicabilityConstraint": "https://example.org/constraint/c1",
}
write(d / "negative.jsonld", neg)

# ═════════════════════════════════════════════════════════════════════════════
# W-AR-03 — Inference Method Mismatch
# ═════════════════════════════════════════════════════════════════════════════
pid = "W-AR-03"
d = ROOT / pid

# Positive: requirement requires 'simulation', activity type is 'inspection'
pos = _base(pid, "pos")
pos["bindsRequirement"] = {
    "id": "https://example.org/req/r1", "type": "Requirement",
    "requiredVerificationMethod": "simulation",
}
pos["hasValidationResult"] = [{
    "id": "https://example.org/result/vr1", "type": "ValidationResult",
    "wasGeneratedBy": {
        "id": "https://example.org/activity/a1", "type": "VerificationActivity",
        "activityType": "inspection",
    },
}]
write(d / "positive.jsonld", pos)

# Negative: required == actual
neg = _base(pid, "neg")
neg["bindsRequirement"] = {
    "id": "https://example.org/req/r1", "type": "Requirement",
    "requiredVerificationMethod": "simulation",
}
neg["hasValidationResult"] = [{
    "id": "https://example.org/result/vr1", "type": "ValidationResult",
    "wasGeneratedBy": {
        "id": "https://example.org/activity/a1", "type": "VerificationActivity",
        "activityType": "simulation",
    },
}]
write(d / "negative.jsonld", neg)

# Boundary: no requiredVerificationMethod → rule should NOT fire
bnd = _base(pid, "bnd")
bnd["hasValidationResult"] = [{
    "id": "https://example.org/result/vr1", "type": "ValidationResult",
    "wasGeneratedBy": {
        "id": "https://example.org/activity/a1", "type": "VerificationActivity",
        "activityType": "inspection",
    },
}]
write(d / "boundary.jsonld", bnd)

# ═════════════════════════════════════════════════════════════════════════════
# W-AL-02 — Sensitivity Gap
# ═════════════════════════════════════════════════════════════════════════════
pid = "W-AL-02"
d = ROOT / pid

# Positive: UQ present on a result, no hasSensitivityAnalysis on UofA
pos = _base(pid, "pos")
pos.pop("hasSensitivityAnalysis", None)
pos["hasValidationResult"] = [{
    "id": "https://example.org/result/vr1", "type": "ValidationResult",
    "hasUncertaintyQuantification": True,
}]
write(d / "positive.jsonld", pos)

# Negative: UQ present AND sensitivity analysis linked
neg = _base(pid, "neg")
neg["hasValidationResult"] = [{
    "id": "https://example.org/result/vr1", "type": "ValidationResult",
    "hasUncertaintyQuantification": True,
}]
# keep hasSensitivityAnalysis from base
write(d / "negative.jsonld", neg)

# Boundary: SensitivityAnalysis class instance exists but no property link.
# Uses wasDerivedFrom to attach it to the graph's default context (avoids the
# @graph-named-graph pitfall). Rule should still fire (no hasSensitivityAnalysis edge).
bnd = _base(pid, "bnd")
bnd.pop("hasSensitivityAnalysis", None)
bnd["hasValidationResult"] = [{
    "id": "https://example.org/result/vr1", "type": "ValidationResult",
    "hasUncertaintyQuantification": True,
}]
bnd["wasDerivedFrom"] = {
    "id": "https://example.org/sa/floating", "type": "SensitivityAnalysis",
}
write(d / "boundary.jsonld", bnd)

# ═════════════════════════════════════════════════════════════════════════════
# W-EP-03 — Stale Input Data
# ═════════════════════════════════════════════════════════════════════════════
pid = "W-EP-03"
d = ROOT / pid

# Positive: dataset vintage predates modelRevisionDate
pos = _base(pid, "pos")
pos["modelRevisionDate"] = "2024-06-01T00:00:00Z"
pos["hasValidationResult"] = [{
    "id": "https://example.org/result/vr1", "type": "ValidationResult",
    "wasGeneratedBy": {
        "id": "https://example.org/activity/a1", "type": "VerificationActivity",
        "used": {
            "id": "https://example.org/dataset/d1", "type": "Dataset",
            "dataVintage": "2018-01-01T00:00:00Z",
        },
    },
}]
write(d / "positive.jsonld", pos)

# Negative: dataset vintage AFTER modelRevisionDate
neg = _base(pid, "neg")
neg["modelRevisionDate"] = "2024-06-01T00:00:00Z"
neg["hasValidationResult"] = [{
    "id": "https://example.org/result/vr1", "type": "ValidationResult",
    "wasGeneratedBy": {
        "id": "https://example.org/activity/a1", "type": "VerificationActivity",
        "used": {
            "id": "https://example.org/dataset/d1", "type": "Dataset",
            "dataVintage": "2025-01-01T00:00:00Z",
        },
    },
}]
write(d / "negative.jsonld", neg)

# Boundary: dataset vintage EQUALS modelRevisionDate → NOT less-than, no fire
bnd = _base(pid, "bnd")
bnd["modelRevisionDate"] = "2024-06-01T00:00:00Z"
bnd["hasValidationResult"] = [{
    "id": "https://example.org/result/vr1", "type": "ValidationResult",
    "wasGeneratedBy": {
        "id": "https://example.org/activity/a1", "type": "VerificationActivity",
        "used": {
            "id": "https://example.org/dataset/d1", "type": "Dataset",
            "dataVintage": "2024-06-01T00:00:00Z",
        },
    },
}]
write(d / "boundary.jsonld", bnd)

# ═════════════════════════════════════════════════════════════════════════════
# W-AR-04 — Model Version Drift
# ═════════════════════════════════════════════════════════════════════════════
pid = "W-AR-04"
d = ROOT / pid

# Positive: validated v2.0; current v2.1
pos = _base(pid, "pos")
pos["currentModelVersion"] = "2.1"
pos["hasValidationResult"] = [{
    "id": "https://example.org/result/vr1", "type": "ValidationResult",
    "wasGeneratedBy": {
        "id": "https://example.org/activity/a1", "type": "VerificationActivity",
        "used": {
            "id": "https://example.org/cfg/c1", "type": "ModelConfiguration",
            "modelVersion": "2.0",
        },
    },
}]
write(d / "positive.jsonld", pos)

# Negative: versions match
neg = _base(pid, "neg")
neg["currentModelVersion"] = "2.1"
neg["hasValidationResult"] = [{
    "id": "https://example.org/result/vr1", "type": "ValidationResult",
    "wasGeneratedBy": {
        "id": "https://example.org/activity/a1", "type": "VerificationActivity",
        "used": {
            "id": "https://example.org/cfg/c1", "type": "ModelConfiguration",
            "modelVersion": "2.1",
        },
    },
}]
write(d / "negative.jsonld", neg)

# ═════════════════════════════════════════════════════════════════════════════
# W-CON-03 — Future-dated Evidence
# ═════════════════════════════════════════════════════════════════════════════
pid = "W-CON-03"
d = ROOT / pid

# Positive: evidence timestamp > signature timestamp
pos = _base(pid, "pos")
pos["signatureTimestamp"] = "2025-01-01T00:00:00Z"
pos["hasEvidence"] = {
    "id": "https://example.org/ev/e1", "type": "ValidationResult",
    "evidenceTimestamp": "2025-12-01T00:00:00Z",
}
write(d / "positive.jsonld", pos)

# Negative: evidence timestamp < signature timestamp
neg = _base(pid, "neg")
neg["signatureTimestamp"] = "2025-01-01T00:00:00Z"
neg["hasEvidence"] = {
    "id": "https://example.org/ev/e1", "type": "ValidationResult",
    "evidenceTimestamp": "2024-06-01T00:00:00Z",
}
write(d / "negative.jsonld", neg)

# Boundary: evidence timestamp == signature timestamp → equality is NOT later
bnd = _base(pid, "bnd")
bnd["signatureTimestamp"] = "2025-01-01T00:00:00Z"
bnd["hasEvidence"] = {
    "id": "https://example.org/ev/e1", "type": "ValidationResult",
    "evidenceTimestamp": "2025-01-01T00:00:00Z",
}
write(d / "boundary.jsonld", bnd)

# ═════════════════════════════════════════════════════════════════════════════
# W-CON-05 — Activity-Evidence Consistency
# ═════════════════════════════════════════════════════════════════════════════
pid = "W-CON-05"
d = ROOT / pid

# Positive: hasVerificationActivity declared; no evidence wasGeneratedBy it
pos = _base(pid, "pos")
pos["hasVerificationActivity"] = {
    "id": "https://example.org/activity/orphan", "type": "VerificationActivity",
    "activityType": "simulation",
}
# hasEvidence absent entirely
write(d / "positive.jsonld", pos)

# Negative: activity declared AND evidence links back
neg = _base(pid, "neg")
neg["hasVerificationActivity"] = "https://example.org/activity/a1"
neg["hasEvidence"] = {
    "id": "https://example.org/ev/e1", "type": "ValidationResult",
    "wasGeneratedBy": "https://example.org/activity/a1",
}
write(d / "negative.jsonld", neg)

# ═════════════════════════════════════════════════════════════════════════════
# W-PROV-01 — Provenance Chain Incomplete (Python)
# ═════════════════════════════════════════════════════════════════════════════
pid = "W-PROV-01"
d = ROOT / pid

# Positive: Claim → wasDerivedFrom → ValidationResult → (nothing upstream,
# not marked foundational) → fire at the ValidationResult.
# Inline-nested because @graph on a node with @id creates a named graph in
# JSON-LD 1.1; Jena only sees the default graph.
pos = _base(pid, "pos")
pos["bindsClaim"] = {
    "id": "https://example.org/claim/c1",
    "type": "AssuranceClaim",
    "wasDerivedFrom": {
        "id": "https://example.org/result/vr-orphan",
        "type": "ValidationResult",
        # no upstream, no isFoundationalEvidence → fires at this node
    },
}
write(d / "positive.jsonld", pos)

# Negative: chain terminates at an isFoundationalEvidence = true node
neg = _base(pid, "neg")
neg["bindsClaim"] = {
    "id": "https://example.org/claim/c1",
    "type": "AssuranceClaim",
    "wasDerivedFrom": {
        "id": "https://example.org/dataset/root",
        "type": "Dataset",
        "isFoundationalEvidence": True,
    },
}
write(d / "negative.jsonld", neg)

# ═════════════════════════════════════════════════════════════════════════════
# W-CON-01 — Factor-Decision Consistency
# ═════════════════════════════════════════════════════════════════════════════
pid = "W-CON-01"
d = ROOT / pid

# Positive: Accepted decision, factor with neither requiredLevel nor achievedLevel
pos = _base(pid, "pos")
pos["hasDecisionRecord"] = {
    "id": "https://example.org/dr/x", "type": "DecisionRecord",
    "outcome": "Accepted",
}
pos["hasCredibilityFactor"] = [{
    "type": "CredibilityFactor",
    "factorType": "Model form",
    "factorStatus": "assessed",
    # no requiredLevel, no achievedLevel → fires
}]
write(d / "positive.jsonld", pos)

# Negative: Accepted decision but factor has both levels
neg = _base(pid, "neg")
neg["hasDecisionRecord"] = {
    "id": "https://example.org/dr/x", "type": "DecisionRecord",
    "outcome": "Accepted",
}
# keep base factor with requiredLevel=3 achievedLevel=3
write(d / "negative.jsonld", neg)

# Boundary: only one of requiredLevel/achievedLevel absent → NOT fire
bnd = _base(pid, "bnd")
bnd["hasDecisionRecord"] = {
    "id": "https://example.org/dr/x", "type": "DecisionRecord",
    "outcome": "Accepted",
}
bnd["hasCredibilityFactor"] = [{
    "type": "CredibilityFactor",
    "factorType": "Model form",
    "factorStatus": "assessed",
    "requiredLevel": 3,
    # no achievedLevel
}]
write(d / "boundary.jsonld", bnd)

# ═════════════════════════════════════════════════════════════════════════════
# W-CON-02 — Identifier Resolution (Python)
# ═════════════════════════════════════════════════════════════════════════════
pid = "W-CON-02"
d = ROOT / pid

# Positive: referencesIdentifier points to something not in the graph and
# is a fragment URI (not an HTTP URL).
pos = _base(pid, "pos")
pos["referencesIdentifier"] = "urn:dangling:ref-nowhere-xyz"
write(d / "positive.jsonld", pos)

# Negative: referencesIdentifier points to a subject in the graph.
# Inline-nest the COU so it becomes a subject (has predicates) rather than
# a bare object reference.
neg = _base(pid, "neg")
neg["hasContextOfUse"] = {
    "id": "https://example.org/cou/cou1",
    "type": "ContextOfUse",
    "intendedUse": "demo",
    "hasApplicabilityConstraint": "https://example.org/constraint/c1",
}
neg["referencesIdentifier"] = "https://example.org/cou/cou1"  # resolves locally
write(d / "negative.jsonld", neg)

# ═════════════════════════════════════════════════════════════════════════════
# W-CON-04 — Profile-Structure Consistency
# ═════════════════════════════════════════════════════════════════════════════
pid = "W-CON-04"
d = ROOT / pid

# Positive: Complete profile, no hasSensitivityAnalysis
pos = _base(pid, "pos")
pos.pop("hasSensitivityAnalysis", None)
write(d / "positive.jsonld", pos)

# Negative: Minimal profile (rule does not apply) OR Complete with SA
neg = _base(pid, "neg")
# base already has hasSensitivityAnalysis; keep it
write(d / "negative.jsonld", neg)


if __name__ == "__main__":
    print(f"Fixtures written under: {ROOT}")

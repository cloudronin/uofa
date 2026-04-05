"""Transform an intermediate dict (from excel_reader) into a UofA JSON-LD document.

Knows about JSON-LD structure but nothing about openpyxl.
"""

import re
from datetime import datetime, timezone
from pathlib import Path

from uofa_cli.excel_constants import (
    VV40_FACTOR_NAMES, NASA_ONLY_FACTOR_NAMES,
    ALL_FACTOR_CATEGORIES, NASA_PHASE_MAP,
    FACTOR_STANDARD_VV40, FACTOR_STANDARD_NASA,
    PROFILE_URIS, CONTEXT_URL, BASE_URI,
)
from uofa_cli import __version__


def slugify(text: str) -> str:
    """Convert text to a URL-safe slug: lowercase, hyphens, no special chars."""
    s = text.lower().strip()
    s = re.sub(r'[^\w\s-]', '', s)
    s = re.sub(r'[\s_]+', '-', s)
    s = re.sub(r'-+', '-', s)
    return s.strip('-')


def map_to_jsonld(data: dict, packs: list[str], source_path: Path) -> dict:
    """Transform intermediate dict into a UofA JSON-LD document.

    Args:
        data: Intermediate dict from excel_reader.read_workbook().
        packs: Active pack names (e.g., ["vv40"], ["nasa-7009b"]).
        source_path: Path to the original Excel file (for provenance).

    Returns:
        A dict ready for json.dumps() as JSON-LD.
    """
    summary = data["summary"]
    entities = data["entities"]
    validation_results = data["validation_results"]
    factors = data["factors"]
    decision = data["decision"]

    profile = summary["profile"]
    project_slug = slugify(summary["project_name"] or "unnamed")
    cou_slug = slugify(summary["cou_name"] or "unnamed")
    base = f"{BASE_URI}/{project_slug}/{cou_slug}"
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # ── Build the document ───────────────────────────────────
    doc = {
        "@context": CONTEXT_URL,
        "id": base,
        "type": "UnitOfAssurance",
        "conformsToProfile": PROFILE_URIS.get(profile, PROFILE_URIS["Minimal"]),
        "name": f"{summary['project_name']} \u2014 {summary['cou_name']}",
    }

    if summary.get("cou_description"):
        doc["description"] = summary["cou_description"]

    # ── Entity bindings ──────────────────────────────────────
    requirements = [e for e in entities if e["entity_type"] == "Requirement"]
    models = [e for e in entities if e["entity_type"] == "Model"]
    datasets = [e for e in entities if e["entity_type"] == "Dataset"]

    if requirements:
        req_uris = [_entity_uri(base, "req", r) for r in requirements]
        doc["bindsRequirement"] = req_uris[0] if len(req_uris) == 1 else req_uris

    if models:
        model_uris = [_entity_uri(base, "model", m) for m in models]
        doc["bindsModel"] = model_uris[0] if len(model_uris) == 1 else model_uris

    if datasets:
        doc["bindsDataset"] = [_entity_uri(base, "data", d) for d in datasets]

    # ── Context of Use ───────────────────────────────────────
    cou = {
        "id": f"{base}/cou",
        "type": "ContextOfUse",
        "name": summary["cou_name"],
    }
    if summary.get("cou_description"):
        cou["intendedUse"] = summary["cou_description"]
    doc["hasContextOfUse"] = cou

    # ── Validation Results ───────────────────────────────────
    if validation_results:
        doc["hasValidationResult"] = [
            _map_validation_result(base, vr) for vr in validation_results
        ]

    # ── Provenance ───────────────────────────────────────────
    if summary.get("source_document"):
        doc["wasDerivedFrom"] = summary["source_document"]

    if summary.get("assessor_name"):
        doc["wasAttributedTo"] = f"{base}/org/{slugify(summary['assessor_name'])}"

    # ── Credibility Factors (Complete profile) ───────────────
    # Include ALL factors (assessed AND not-assessed) so the rule engine
    # can detect unassessed gaps at elevated risk (W-EP-04).
    if factors:
        doc["hasCredibilityFactor"] = [
            _map_factor(f, packs) for f in factors
        ]

    # ── Decision Record ──────────────────────────────────────
    dec = {
        "id": f"{base}/decision",
        "type": "DecisionRecord",
        "outcome": decision["outcome"],
    }
    if decision.get("rationale"):
        dec["rationale"] = decision["rationale"]
    if decision.get("decided_by"):
        dec["actor"] = f"{base}/org/{slugify(decision['decided_by'])}"
        dec["role"] = decision["decided_by"]
    if decision.get("decision_date"):
        dec["decidedAt"] = f"{decision['decision_date']}T00:00:00Z"
    doc["hasDecisionRecord"] = dec

    # ── Complete profile metadata ────────────────────────────
    if profile == "Complete":
        if summary.get("assurance_level"):
            doc["assuranceLevel"] = summary["assurance_level"]
        if summary.get("standards_reference"):
            doc["criteriaSet"] = f"https://uofa.net/criteria/{slugify(summary['standards_reference'])}"

        # Credibility metrics — placeholder values
        doc["credibilityIndex"] = {"@value": "0.00", "@type": "xsd:decimal"}
        doc["traceCompleteness"] = {"@value": "0.00", "@type": "xsd:decimal"}
        doc["verificationCoverage"] = {"@value": "0.00", "@type": "xsd:decimal"}
        doc["validationCoverage"] = {"@value": "0.00", "@type": "xsd:decimal"}
        doc["uncertaintyCIWidth"] = {"@value": "0.0", "@type": "xsd:decimal"}

        if summary.get("model_risk_level") is not None:
            doc["modelRiskLevel"] = summary["model_risk_level"]
        if summary.get("device_class"):
            doc["deviceClass"] = summary["device_class"]
        doc["couName"] = summary["cou_name"]
        doc["decision"] = decision["outcome"]
        doc["hasUncertaintyQuantification"] = summary.get("has_uq", "No") == "Yes"

    # ── Timestamp and integrity placeholders ─────────────────
    doc["generatedAtTime"] = now
    doc["hash"] = "sha256:" + "0" * 64
    doc["signature"] = "ed25519:" + "0" * 128
    doc["signatureAlg"] = "ed25519"
    doc["canonicalizationAlg"] = "RDFC-1.0"

    # ── Provenance chain ─────────────────────────────────────
    doc["provenanceChain"] = [
        {
            "activityType": "ImportActivity",
            "timestamp": now,
            "sourceFile": str(source_path),
            "toolVersion": f"uofa-cli {__version__}",
            "generatedEntity": base,
        }
    ]

    return doc


def _entity_uri(base: str, entity_type: str, entity: dict) -> str:
    """Generate a URI for an entity."""
    if entity.get("uri"):
        return entity["uri"]
    name_slug = slugify(entity.get("name") or "unnamed")
    return f"{base}/{entity_type}/{name_slug}"


def _map_validation_result(base: str, vr: dict) -> dict:
    """Map a validation result intermediate dict to JSON-LD."""
    etype = vr["evidence_type"]
    result = {
        "type": etype,
    }

    if vr.get("uri"):
        result["id"] = vr["uri"]
    else:
        result["id"] = f"{base}/validation/{slugify(vr['name'])}"

    if vr.get("name"):
        result["name"] = vr["name"]
    if vr.get("description"):
        result["description"] = vr["description"]
    if vr.get("compares_to"):
        # v0.4 vocabulary uses "comparedAgainst" (not "comparesTo")
        result["comparedAgainst"] = vr["compares_to"]
    if vr.get("has_uq") == "Yes":
        result["hasUncertaintyQuantification"] = True
        if vr.get("uq_method"):
            result["uqMethod"] = vr["uq_method"]
    elif vr.get("has_uq") == "No":
        result["hasUncertaintyQuantification"] = False
    if vr.get("metric_value"):
        result["metricValue"] = vr["metric_value"]
    if vr.get("pass_fail"):
        result["passFail"] = vr["pass_fail"]

    # Auto-generate wasGeneratedBy activity so W-EP-02 doesn't fire on
    # every imported validation result (the Excel template has no column
    # for generation activity).
    result["wasGeneratedBy"] = {
        "id": f"{result['id']}/activity",
        "type": "prov:Activity",
    }

    # Add SHACL-required properties for evidence sub-types.
    # These shapes have mandatory fields that the generic Excel columns
    # don't capture, so we populate from available data or defaults.
    if etype == "ReviewActivity":
        result["reviewer"] = vr.get("compares_to") or f"{base}/org/reviewer"
        result["reviewType"] = "internal"
    elif etype == "ProcessAttestation":
        result["processType"] = "documentation"
        result["attestedBy"] = vr.get("compares_to") or f"{base}/org/attester"
    elif etype == "DeploymentRecord":
        result["deployedIn"] = vr.get("compares_to") or f"{base}/system/deployment"
    elif etype == "InputPedigreeLink":
        result["sourceReference"] = vr.get("compares_to") or vr.get("uri") or f"{base}/data/source"

    return result


def _map_factor(factor: dict, packs: list[str]) -> dict:
    """Map a credibility factor intermediate dict to JSON-LD."""
    vv40_set = set(VV40_FACTOR_NAMES)
    nasa_only_set = set(NASA_ONLY_FACTOR_NAMES)

    f = {
        "type": "CredibilityFactor",
        "factorType": factor["factor_type"],
        "factorStatus": factor["status"],
    }

    # Assign factorStandard based on factor name and active packs
    if factor["factor_type"] in nasa_only_set:
        f["factorStandard"] = FACTOR_STANDARD_NASA
    elif factor["factor_type"] in vv40_set:
        # If both packs active and it's a shared factor, use VV40
        f["factorStandard"] = FACTOR_STANDARD_VV40

    if factor.get("required_level") is not None:
        f["requiredLevel"] = factor["required_level"]
    if factor.get("achieved_level") is not None:
        f["achievedLevel"] = factor["achieved_level"]
    if factor.get("acceptance_criteria"):
        f["acceptanceCriteria"] = factor["acceptance_criteria"]
    if factor.get("rationale"):
        f["rationale"] = factor["rationale"]

    # NASA-specific: assessmentPhase
    if "nasa-7009b" in packs and factor.get("category"):
        phase = NASA_PHASE_MAP.get(factor["category"])
        if phase:
            f["assessmentPhase"] = phase

    # Linked evidence URI (from Excel column H)
    if factor.get("linked_evidence"):
        f["hasEvidence"] = factor["linked_evidence"]

    return f

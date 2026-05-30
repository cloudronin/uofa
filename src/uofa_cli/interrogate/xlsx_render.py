"""v1 staged ingestion — render a SIP bundle into the human-review authoring view.

Per the staged-ingestion design (SIP §7.3 v1): the signed JSON bundle is the
CANONICAL artifact and is never lossily flattened. This module maps the bundle's
measured evidence into the rows of the import-ready authoring view — one
Validation-Results row per measurement carrying a short scalar summary and a
link to the canonical bundle, with the full numeric arrays living in that linked
artifact. It flows through the existing extract -> review -> import on-ramp with
ZERO core change.

Two firewall-critical properties hold here, by construction:
  - every Validation-Results row leaves ``pass_fail`` EMPTY — SIP measures, it
    never authors a verdict; the Validation Results sheet's pass/fail column is
    a decision the human reviewer fills, not SIP;
  - the Decision is left blank for the practitioner — SIP must not author it
    (the import Decision sheet's verdict belongs to the COU, not the instrument).

``render_review_rows`` returns the sheet-row data structure. Serializing those
rows to the exact import .xlsx layout reuses the existing workbook writer; the
v2 native SIP-bundle reader (skipping the xlsx round-trip for measured fields)
is the durable path.
"""

from __future__ import annotations

from typing import Any


def _round(value: Any, ndigits: int = 6):
    return round(value, ndigits) if isinstance(value, (int, float)) else value


def render_review_rows(bundle: dict, *, bundle_artifact_uri: str) -> dict:
    """Map a SIP bundle to the import-ready human-review rows.

    ``bundle_artifact_uri`` is the location of the canonical signed JSON bundle,
    linked from each measurement row so the lossless arrays remain reachable.
    """
    subject = bundle.get("subject", {})
    measurements = bundle.get("measurements", {})

    assessment_summary = {
        "project_name": subject.get("surrogateId", ""),
        "cou_name": "",          # reviewer fills the COU framing
        "model_risk_level": "",  # reviewer
        "assurance_level": "",   # reviewer
        "surrogate_type": subject.get("surrogateType", ""),
        "evidence_bundle": bundle_artifact_uri,
    }

    model_and_data = [
        {"entity_type": "Model", "name": subject.get("surrogateId", ""),
         "version": subject.get("modelVersion", ""), "identifier": subject.get("adapterRef", "")},
        {"entity_type": "Dataset", "name": "benchmark", "identifier": bundle_artifact_uri},
        {"entity_type": "Dataset", "name": "reference", "identifier": bundle_artifact_uri},
    ]

    validation_results: list[dict] = []
    for residual in measurements.get("referenceResiduals", []):
        stats = residual.get("statistics", {})
        validation_results.append({
            "name": f"reference-residual: {residual.get('quantityOfInterest', '')}",
            "evidence_type": "ConstraintCheckEvidence",
            "metric_value": _round(stats.get("rms")),
            "pass_fail": "",  # FIREWALL: SIP never authors a verdict
            "identifier": bundle_artifact_uri,
            "description": (
                f"RMS reference residual for {residual.get('quantityOfInterest', '')}; "
                f"full distribution arrays in the linked signed bundle"
            ),
        })

    for constraint in measurements.get("physicsConstraintResidual", []):
        stats = constraint.get("statistics", {})
        validation_results.append({
            "name": f"constraint-residual: {constraint.get('constraintId', '')}",
            "evidence_type": "ConstraintCheckEvidence",
            "metric_value": _round(stats.get("max")),
            "pass_fail": "",
            "identifier": bundle_artifact_uri,
            "description": f"max constraint residual for {constraint.get('constraintId', '')}",
        })

    coverage = measurements.get("envelopeCoverage", {})
    validation_results.append({
        "name": "envelope-coverage",
        "evidence_type": "ValidationResult",
        "metric_value": "",
        "pass_fail": "",
        "identifier": bundle_artifact_uri,
        "description": (
            f"benchmarkSpansEnvelope={coverage.get('benchmarkSpansEnvelope')}, "
            f"evaluationPointInEnvelope={coverage.get('evaluationPointInEnvelope')}"
        ),
    })

    uq = measurements.get("uqCalibration", {})
    if uq.get("empiricalCoverage") is not None:
        validation_results.append({
            "name": "uq-calibration",
            "evidence_type": "ValidationResult",
            "metric_value": _round(uq.get("empiricalCoverage")),
            "pass_fail": "",
            "identifier": bundle_artifact_uri,
            "description": f"empirical coverage via {uq.get('surrogateUQMethod')}",
        })

    # Decision is left entirely to the human reviewer — SIP authors no verdict.
    decision = {"outcome": "", "rationale": "", "review_date": ""}

    return {
        "assessment_summary": assessment_summary,
        "model_and_data": model_and_data,
        "validation_results": validation_results,
        "decision": decision,
        "bundle_artifact": bundle_artifact_uri,
    }

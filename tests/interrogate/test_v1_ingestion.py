"""v1 staged-ingestion view tests (SIP §7.3 v1).

The authoring view is the decision-package side of the on-ramp, so a pass_fail
column and a Decision sheet legitimately EXIST there — the firewall property is
that SIP leaves them EMPTY (the reviewer authors the verdict) and links the
canonical signed bundle for the lossless arrays.
"""

from __future__ import annotations

from uofa_cli.interrogate.xlsx_render import render_review_rows

BUNDLE_URI = "evidence/sip-bundle-0001.json"


def _bundle() -> dict:
    return {
        "subject": {"surrogateId": "airfrans-mlp", "modelVersion": "1.0.0",
                    "surrogateType": "data-driven-emulator", "adapterRef": "m:A"},
        "measurements": {
            "referenceResiduals": [
                {"quantityOfInterest": "lift_coefficient", "statistics": {"rms": 0.0123}},
                {"quantityOfInterest": "drag_coefficient", "statistics": {"rms": 0.0456}},
            ],
            "physicsConstraintResidual": [
                {"constraintId": "mass-conservation", "statistics": {"max": 1e-4}},
            ],
            "envelopeCoverage": {"benchmarkSpansEnvelope": True, "evaluationPointInEnvelope": False},
            "uqCalibration": {"surrogateUQMethod": "conformal-prediction", "empiricalCoverage": 0.91},
        },
    }


def test_one_validation_row_per_measurement():
    rows = render_review_rows(_bundle(), bundle_artifact_uri=BUNDLE_URI)
    names = [r["name"] for r in rows["validation_results"]]
    assert any("lift_coefficient" in n for n in names)
    assert any("drag_coefficient" in n for n in names)
    assert any("mass-conservation" in n for n in names)
    assert any(n == "envelope-coverage" for n in names)
    assert any(n == "uq-calibration" for n in names)


def test_pass_fail_left_empty_on_every_row():
    rows = render_review_rows(_bundle(), bundle_artifact_uri=BUNDLE_URI)
    # FIREWALL: SIP never authors a verdict — the reviewer fills pass_fail.
    assert all(r["pass_fail"] == "" for r in rows["validation_results"])


def test_decision_left_for_reviewer():
    rows = render_review_rows(_bundle(), bundle_artifact_uri=BUNDLE_URI)
    assert rows["decision"]["outcome"] == ""
    assert rows["decision"]["rationale"] == ""


def test_canonical_bundle_is_linked():
    rows = render_review_rows(_bundle(), bundle_artifact_uri=BUNDLE_URI)
    assert rows["bundle_artifact"] == BUNDLE_URI
    # Every measurement row links back to the lossless signed bundle.
    assert all(r["identifier"] == BUNDLE_URI for r in rows["validation_results"])
    assert rows["assessment_summary"]["evidence_bundle"] == BUNDLE_URI

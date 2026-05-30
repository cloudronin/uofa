"""Addendum A3: the at-a-glance comparison renders the expected sections and
carries no verdict/recommendation language."""

from __future__ import annotations

from uofa_cli.interrogate.comparison import render_comparison
from uofa_cli.interrogate.forbidden import FORBIDDEN_TOKENS


def _bundle() -> dict:
    return {
        "subject": {"surrogateId": "airfrans-mlp", "surrogateType": "data-driven-emulator", "modelVersion": "1.0.0"},
        "measurements": {
            "referenceResiduals": [
                {"quantityOfInterest": "lift_coefficient", "statistics": {"count": 200, "mean": 0.012, "rms": 0.02, "max": 0.08}},
                {"quantityOfInterest": "drag_coefficient", "statistics": {"count": 200, "mean": 0.05, "rms": 0.06, "max": 0.2}},
            ],
            "envelopeCoverage": {"benchmarkSpansEnvelope": True, "evaluationPointInEnvelope": False},
            "physicsConstraintResidual": [{"constraintId": "mass-conservation", "statistics": {"mean": 1e-6, "max": 1e-4}}],
            "uqCalibration": {"surrogateUQMethod": "conformal-prediction", "empiricalCoverage": 0.91, "nominalCoverage": 0.9},
        },
    }


def test_render_has_all_sections():
    out = render_comparison(_bundle())
    assert "Reference residuals" in out
    assert "Envelope coverage" in out
    assert "Physics-constraint residuals" in out
    assert "UQ calibration" in out
    assert "lift_coefficient" in out and "drag_coefficient" in out


def test_render_flags_out_of_envelope_and_worst_residual():
    out = render_comparison(_bundle())
    assert "extrapolation" in out.lower()  # eval point outside envelope
    assert "largest reference residual" in out.lower()
    assert "drag_coefficient" in out  # the worst by max


def test_render_carries_no_verdict_token():
    out = render_comparison(_bundle()).lower()
    for token in FORBIDDEN_TOKENS:
        assert token.lower() not in out, f"comparison leaked verdict token {token!r}"
    for word in ["recommend", "should ", "looks good", "pass", "fail"]:
        assert word not in out

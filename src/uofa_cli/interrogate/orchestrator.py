"""Measurement orchestrator (SIP §3 component 3).

Invokes the adapter and the measurement wrappers, and records library +
version + config + seed + runEnvironment per measurement family (SIP §5.4), so
the orchestration is itself part of the provenance. It computes; it never
thresholds.
"""

from __future__ import annotations

import importlib.metadata
import platform
import sys

from uofa_cli.interrogate import measurements as M
from uofa_cli.interrogate.loader import Benchmark, Reference


def _lib_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except Exception:
        return "unknown"


def _run_environment() -> dict:
    return {"python": sys.version.split()[0], "platform": platform.platform()}


def run_measurements(adapter, benchmark: Benchmark, reference: Reference,
                     scope: dict, *, seed: int | None = None) -> tuple[dict, list]:
    """Return ``(measurements, measurement_provenance)`` per the SIP contract.

    ``scope`` is the practitioner's declared-scope dict (trainingEnvelope,
    evaluationPoint/Region, declaredPhysicsConstraint, surrogateUQMethod).
    """
    numpy_version = _lib_version("numpy")
    sip_version = _lib_version("uofa")
    run_env = _run_environment()

    predicted = adapter.predict(benchmark.inputs)

    reference_residuals = []
    for qoi, ref_values in reference.reference.items():
        if qoi not in predicted:
            continue
        reference_residuals.append({
            "quantityOfInterest": qoi,
            "statistics": M.residual_statistics(predicted[qoi], ref_values),
            "measurementRef": "m-residuals",
        })

    env_dims = scope.get("trainingEnvelope", {}).get("dimensions", [])
    eval_point = None
    if scope.get("evaluationPoint"):
        eval_point = {c["name"]: c["value"]
                      for c in scope["evaluationPoint"].get("coordinates", [])}
    coverage = M.envelope_coverage(env_dims, benchmark.input_names, benchmark.inputs, eval_point)
    coverage["measurementRef"] = "m-envelope"

    physics = []
    for constraint in scope.get("declaredPhysicsConstraint", []):
        cid = constraint["constraintId"]
        residual_field = reference.constraint_fields.get(cid)
        if residual_field is None:
            continue
        physics.append({
            "constraintId": cid,
            "statistics": M.constraint_residual_statistics(residual_field),
            "measurementRef": "m-physics",
        })

    uq = {"surrogateUQMethod": scope.get("surrogateUQMethod")}
    for qoi, (lower, upper) in reference.uq_intervals.items():
        if qoi in reference.reference:
            uq["empiricalCoverage"] = M.uq_empirical_coverage(
                lower, upper, reference.reference[qoi]
            )
            uq["measurementRef"] = "m-uq"
            break

    measurements = {
        "referenceResiduals": reference_residuals,
        "envelopeCoverage": coverage,
        "physicsConstraintResidual": physics,
        "uqCalibration": uq,
    }

    provenance = [
        {"measurementId": "m-residuals",
         "producedBy": {"library": "numpy", "version": numpy_version},
         "config": {"metric": "abs-residual-statistics"}, "seed": seed,
         "runEnvironment": run_env},
        {"measurementId": "m-envelope",
         "producedBy": {"library": "uofa-sip", "version": sip_version},
         "config": {"method": "per-dimension-containment"}, "seed": seed,
         "runEnvironment": run_env},
        {"measurementId": "m-physics",
         "producedBy": {"library": "numpy", "version": numpy_version},
         "config": {"metric": "constraint-residual-statistics"}, "seed": seed,
         "runEnvironment": run_env},
        {"measurementId": "m-uq",
         "producedBy": {"library": "numpy", "version": numpy_version},
         "config": {"method": "empirical-interval-coverage"}, "seed": seed,
         "runEnvironment": run_env},
    ]

    measured_families = ["referenceResiduals", "envelopeCoverage"]
    if physics:
        measured_families.append("physicsConstraintResidual")
    if "empiricalCoverage" in uq:
        measured_families.append("uqCalibration")

    return measurements, provenance, measured_families

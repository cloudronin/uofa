"""Interrogation measurements — thin numpy wrappers (SIP §4, §5.5).

SIP computes; it does not threshold. Each function returns plain Python
numbers (JSON-serializable) shaped to the SIP contract's ``statistics`` blocks.
``numpy`` is imported lazily so ``import uofa_cli.interrogate`` stays cheap; it
ships in the ``[interrogate]`` extra.

The principle is "orchestrate, do not reimplement": for residual statistics the
library *is* numpy, recorded in measurement provenance. Post-hoc UQ (conformal)
intervals are supplied by the caller — SIP computes their empirical coverage,
it does not fit them.
"""

from __future__ import annotations

from typing import Any

from uofa_cli.interrogate.measurement_method import MeasurementContext, MeasurementMethod


def _np():
    try:
        import numpy as np
    except ImportError as exc:  # pragma: no cover - exercised only without the extra
        raise RuntimeError(
            "numpy is required for SIP measurements. "
            "Install with: pip install uofa[interrogate]"
        ) from exc
    return np


def residual_statistics(predicted: Any, reference: Any) -> dict:
    """Distribution statistics of (predicted - reference) for one QoI."""
    np = _np()
    diff = np.asarray(predicted, dtype=float).ravel() - np.asarray(reference, dtype=float).ravel()
    if diff.size == 0:
        return {"count": 0, "mean": None, "min": None, "max": None,
                "rms": None, "l2": None, "stddev": None}
    absdiff = np.abs(diff)
    return {
        "count": int(diff.size),
        "mean": float(absdiff.mean()),
        "min": float(absdiff.min()),
        "max": float(absdiff.max()),
        "rms": float(np.sqrt((diff ** 2).mean())),
        "l2": float(np.linalg.norm(diff)),
        "stddev": float(diff.std()),
    }


def envelope_coverage(
    envelope_dimensions: list[dict],
    input_names: list[str],
    inputs: Any,
    evaluation_point: dict | None,
) -> dict:
    """Flags: does the benchmark span the envelope, is the eval point inside it.

    ``envelope_dimensions`` is ``[{"name","min","max"}, ...]``; ``inputs`` is an
    ``N x D`` array whose columns are named by ``input_names``;
    ``evaluation_point`` is ``{name: value}`` (or None).
    """
    np = _np()
    arr = np.asarray(inputs, dtype=float)
    if arr.ndim == 1:
        arr = arr.reshape(-1, 1)
    name_to_col = {name: i for i, name in enumerate(input_names)}

    spans = None
    if envelope_dimensions and arr.size:
        spans = True
        for dim in envelope_dimensions:
            col = name_to_col.get(dim["name"])
            if col is None or col >= arr.shape[1]:
                spans = False
                break
            column = arr[:, col]
            if not (column.min() <= dim["min"] and column.max() >= dim["max"]):
                spans = False
                break

    inside = None
    if evaluation_point and envelope_dimensions:
        inside = True
        bounds = {d["name"]: (d["min"], d["max"]) for d in envelope_dimensions}
        for name, value in evaluation_point.items():
            lo_hi = bounds.get(name)
            if lo_hi is None:
                continue
            lo, hi = lo_hi
            if not (lo <= float(value) <= hi):
                inside = False
                break

    return {"benchmarkSpansEnvelope": spans, "evaluationPointInEnvelope": inside}


def constraint_residual_statistics(residual_field: Any) -> dict:
    """Distribution statistics of |residual| of a conservation/invariant check."""
    np = _np()
    field = np.abs(np.asarray(residual_field, dtype=float).ravel())
    if field.size == 0:
        return {"count": 0, "mean": None, "max": None, "rms": None}
    return {
        "count": int(field.size),
        "mean": float(field.mean()),
        "max": float(field.max()),
        "rms": float(np.sqrt((field ** 2).mean())),
    }


def uq_empirical_coverage(lower: Any, upper: Any, reference: Any) -> float:
    """Fraction of reference values that fall within [lower, upper]."""
    np = _np()
    lo = np.asarray(lower, dtype=float).ravel()
    hi = np.asarray(upper, dtype=float).ravel()
    ref = np.asarray(reference, dtype=float).ravel()
    n = min(lo.size, hi.size, ref.size)
    if n == 0:
        return 0.0
    inside = (ref[:n] >= lo[:n]) & (ref[:n] <= hi[:n])
    return float(inside.mean())


# ── The four open-core measurement methods (the first measurement pack) ──────
#
# Each wraps one of the functions above as a `MeasurementMethod`, reproducing the
# exact block shapes the orchestrator emitted before the §3 refactor — so the
# byte-identical golden gate (tests/interrogate/test_bundle_golden.py) holds.
# They `compute`, they never threshold; provenance ids are declared here, not
# hardcoded in the orchestrator.


class ResidualMeasurement(MeasurementMethod):
    """Per-QoI residual statistics of surrogate outputs vs the reference set."""

    capability_id = "measurement:reference-residuals"
    output_key = "referenceResiduals"
    provenance_id = "m-residuals"

    def compute(self, ctx: MeasurementContext) -> list:
        out = []
        for qoi, ref_values in ctx.reference.reference.items():
            if qoi not in ctx.predicted:
                continue
            out.append({
                "quantityOfInterest": qoi,
                "statistics": residual_statistics(ctx.predicted[qoi], ref_values),
                "measurementRef": self.provenance_id,
            })
        return out

    def provenance(self, ctx: MeasurementContext) -> dict:
        return {
            "measurementId": self.provenance_id,
            "producedBy": {"library": "numpy", "version": ctx.numpy_version},
            "config": {"metric": "abs-residual-statistics"},
            "seed": ctx.seed,
            "runEnvironment": ctx.run_env,
        }


class EnvelopeMeasurement(MeasurementMethod):
    """Whether the benchmark spans the training envelope and the eval point is inside it."""

    capability_id = "measurement:envelope-coverage"
    output_key = "envelopeCoverage"
    provenance_id = "m-envelope"

    def compute(self, ctx: MeasurementContext) -> dict:
        env_dims = ctx.scope.get("trainingEnvelope", {}).get("dimensions", [])
        eval_point = None
        if ctx.scope.get("evaluationPoint"):
            eval_point = {c["name"]: c["value"]
                          for c in ctx.scope["evaluationPoint"].get("coordinates", [])}
        coverage = envelope_coverage(
            env_dims, ctx.benchmark.input_names, ctx.benchmark.inputs, eval_point
        )
        coverage["measurementRef"] = self.provenance_id
        return coverage

    def provenance(self, ctx: MeasurementContext) -> dict:
        return {
            "measurementId": self.provenance_id,
            "producedBy": {"library": "uofa-sip", "version": ctx.sip_version},
            "config": {"method": "per-dimension-containment"},
            "seed": ctx.seed,
            "runEnvironment": ctx.run_env,
        }


class PhysicsConstraintMeasurement(MeasurementMethod):
    """Per-constraint residual statistics of conservation/invariant checks."""

    capability_id = "measurement:physics-residuals"
    output_key = "physicsConstraintResidual"
    provenance_id = "m-physics"

    def compute(self, ctx: MeasurementContext) -> list:
        out = []
        for constraint in ctx.scope.get("declaredPhysicsConstraint", []):
            cid = constraint["constraintId"]
            residual_field = ctx.reference.constraint_fields.get(cid)
            if residual_field is None:
                continue
            out.append({
                "constraintId": cid,
                "statistics": constraint_residual_statistics(residual_field),
                "measurementRef": self.provenance_id,
            })
        return out

    def provenance(self, ctx: MeasurementContext) -> dict:
        return {
            "measurementId": self.provenance_id,
            "producedBy": {"library": "numpy", "version": ctx.numpy_version},
            "config": {"metric": "constraint-residual-statistics"},
            "seed": ctx.seed,
            "runEnvironment": ctx.run_env,
        }

    def is_present(self, block: Any) -> bool:
        # Present only when at least one declared constraint had a residual field.
        return bool(block)


class UQCalibrationMeasurement(MeasurementMethod):
    """Empirical coverage of the surrogate's prediction intervals (+ the method used)."""

    capability_id = "measurement:uq-calibration"
    output_key = "uqCalibration"
    provenance_id = "m-uq"

    def compute(self, ctx: MeasurementContext) -> dict:
        uq = {"surrogateUQMethod": ctx.scope.get("surrogateUQMethod")}
        for qoi, (lower, upper) in ctx.reference.uq_intervals.items():
            if qoi in ctx.reference.reference:
                uq["empiricalCoverage"] = uq_empirical_coverage(
                    lower, upper, ctx.reference.reference[qoi]
                )
                uq["measurementRef"] = self.provenance_id
                break
        return uq

    def provenance(self, ctx: MeasurementContext) -> dict:
        return {
            "measurementId": self.provenance_id,
            "producedBy": {"library": "numpy", "version": ctx.numpy_version},
            "config": {"method": "empirical-interval-coverage"},
            "seed": ctx.seed,
            "runEnvironment": ctx.run_env,
        }

    def is_present(self, block: Any) -> bool:
        # Present only when an empirical coverage was actually computed.
        return "empiricalCoverage" in block


def default_methods() -> list[MeasurementMethod]:
    """The four open-core measurement methods, in canonical emit order.

    Order is load-bearing: it fixes the ``measurements`` key order and the
    ``measurementProvenance`` order that the byte-identical golden gate pins
    across the §3 refactor. New methods (premium packs) append after these.
    """
    return [
        ResidualMeasurement(),
        EnvelopeMeasurement(),
        PhysicsConstraintMeasurement(),
        UQCalibrationMeasurement(),
    ]

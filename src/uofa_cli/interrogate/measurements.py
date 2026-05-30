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

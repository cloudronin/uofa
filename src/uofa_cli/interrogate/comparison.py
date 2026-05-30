"""At-a-glance surrogate-vs-reference comparison (Addendum A3).

The product value is almost entirely in this comparison being readable at a
glance. ``render_comparison`` turns a SIP bundle's measurements into a legible
plain-text view: residual distribution per QoI, envelope coverage, physics-
constraint residuals, UQ calibration, and a factual notes block calling out
where the surrogate degrades or crosses out of the declared envelope.

It reports measurements only — **no threshold, no pass, no verdict, no
recommendation**. SIP reports; the engineer decides. Surfaced by
``uofa interrogate`` (after emit) and by ``uofa decision review`` (facts, then
stop). Returns a string so it is testable and free of ANSI noise.
"""

from __future__ import annotations

from typing import Any


def _fmt(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, float):
        return f"{value:.4g}"
    return str(value)


def _flag(value: Any) -> str:
    if value is True:
        return "yes"
    if value is False:
        return "no"
    return "unknown"


def render_comparison(bundle: dict) -> str:
    """Return a legible plain-text surrogate-vs-reference comparison."""
    subject = bundle.get("subject", {})
    measurements = bundle.get("measurements", {})
    lines: list[str] = []

    lines.append(
        f"Surrogate-vs-reference comparison — {subject.get('surrogateId', '?')} "
        f"({subject.get('surrogateType', '?')}, v{subject.get('modelVersion', '?')})"
    )
    lines.append("")

    # Reference residuals per QoI
    residuals = measurements.get("referenceResiduals", [])
    lines.append("Reference residuals (surrogate vs reference set):")
    if residuals:
        lines.append(f"  {'QoI':<28}{'count':>8}{'mean':>12}{'rms':>12}{'max':>12}")
        for entry in residuals:
            stats = entry.get("statistics", {})
            lines.append(
                f"  {str(entry.get('quantityOfInterest', '?')):<28}"
                f"{_fmt(stats.get('count')):>8}{_fmt(stats.get('mean')):>12}"
                f"{_fmt(stats.get('rms')):>12}{_fmt(stats.get('max')):>12}"
            )
    else:
        lines.append("  (none reported)")
    lines.append("")

    # Envelope coverage
    coverage = measurements.get("envelopeCoverage", {})
    lines.append("Envelope coverage:")
    lines.append(f"  benchmark spans the declared envelope : {_flag(coverage.get('benchmarkSpansEnvelope'))}")
    lines.append(f"  evaluation point inside the envelope  : {_flag(coverage.get('evaluationPointInEnvelope'))}")
    lines.append("")

    # Physics-constraint residuals
    physics = measurements.get("physicsConstraintResidual", [])
    if physics:
        lines.append("Physics-constraint residuals:")
        lines.append(f"  {'constraint':<28}{'mean':>12}{'max':>12}")
        for entry in physics:
            stats = entry.get("statistics", {})
            lines.append(
                f"  {str(entry.get('constraintId', '?')):<28}"
                f"{_fmt(stats.get('mean')):>12}{_fmt(stats.get('max')):>12}"
            )
        lines.append("")

    # UQ calibration
    uq = measurements.get("uqCalibration", {})
    lines.append("UQ calibration:")
    lines.append(
        f"  method: {_fmt(uq.get('surrogateUQMethod'))}   "
        f"empirical coverage: {_fmt(uq.get('empiricalCoverage'))}   "
        f"nominal: {_fmt(uq.get('nominalCoverage'))}"
    )
    lines.append("")

    # Factual notes — where it degrades / crosses out of envelope (no verdict)
    notes = list(_notes(measurements))
    if notes:
        lines.append("Notes:")
        lines.extend(f"  - {note}" for note in notes)

    return "\n".join(lines)


def _notes(measurements: dict):
    coverage = measurements.get("envelopeCoverage", {})
    if coverage.get("evaluationPointInEnvelope") is False:
        yield "evaluation point is OUTSIDE the declared training envelope (extrapolation)"
    if coverage.get("benchmarkSpansEnvelope") is False:
        yield "benchmark set does not span the full declared envelope"
    residuals = measurements.get("referenceResiduals", [])
    worst = None
    for entry in residuals:
        max_val = entry.get("statistics", {}).get("max")
        if isinstance(max_val, (int, float)) and (worst is None or max_val > worst[1]):
            worst = (entry.get("quantityOfInterest", "?"), max_val)
    if worst is not None:
        yield f"largest reference residual: {worst[0]} (max={_fmt(worst[1])})"

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

from uofa_cli import firewall
from uofa_cli.interrogate import measurement_method as mm
from uofa_cli.interrogate import measurements as M
from uofa_cli.interrogate.loader import Benchmark, Reference


def _lib_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except Exception:
        return "unknown"


def _run_environment() -> dict:
    return {"python": sys.version.split()[0], "platform": platform.platform()}


def _effective_methods() -> list[mm.MeasurementMethod]:
    """The measurement methods this run emits, in stable order, deduped by id.

    Open-core defaults first (their order fixes the ``measurements`` /
    ``measurementProvenance`` key order the golden gate pins), then any
    measurement capabilities the active packs declare (``payload.impl``), then
    methods registered imperatively via ``register_measurement``. Recomputed per
    run from the CURRENT active set, so packs contribute through the interface
    with no orchestrator change and nothing lingers across runs.
    """
    methods: list[mm.MeasurementMethod] = []
    seen: set[str] = set()
    for source in (M.default_methods(), mm.pack_measurement_methods(), mm.extra_measurements()):
        for method in source:
            if method.capability_id in seen:
                continue
            seen.add(method.capability_id)
            methods.append(method)
    return methods


def run_measurements(adapter, benchmark: Benchmark, reference: Reference,
                     scope: dict, *, seed: int | None = None) -> tuple[dict, list, list]:
    """Return ``(measurements, measurement_provenance, fields_present)``.

    Discovers measurement methods through the :class:`MeasurementMethod`
    interface + registry and invokes each over a single
    :class:`MeasurementContext`, rather than calling the four functions by
    hardcoded attribute reference. Each method declares its own provenance id
    (no hardcoded ids here) and whether its output counts as present.

    ``scope`` is the practitioner's declared-scope dict (trainingEnvelope,
    evaluationPoint/Region, declaredPhysicsConstraint, surrogateUQMethod).
    """
    numpy_version = _lib_version("numpy")
    sip_version = _lib_version("uofa")
    run_env = _run_environment()

    predicted = adapter.predict(benchmark.inputs)
    ctx = mm.MeasurementContext(
        predicted=predicted, benchmark=benchmark, reference=reference,
        scope=scope, seed=seed, run_env=run_env,
        numpy_version=numpy_version, sip_version=sip_version,
    )

    measurements: dict = {}
    provenance: list = []
    fields_present: list = []
    for method in _effective_methods():
        block = method.compute(ctx)
        # Every measurement output crosses the firewall chokepoint (§0/§4): a
        # method that tried to emit a verdict/decision — or a non-measurement-
        # shaped scalar — is denied here, fail-closed, before it enters the bundle.
        firewall.enforce_crossing(block, placement=firewall.PLACEMENT_MEASUREMENT)
        measurements[method.output_key] = block
        provenance.append(method.provenance(ctx))
        if method.is_present(block):
            fields_present.append(method.output_key)

    return measurements, provenance, fields_present

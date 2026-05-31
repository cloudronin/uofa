"""P3 §3 acceptance — a measurement method drops in as a pack through the interface.

Two registration paths, both proven here:
- imperative: ``register_measurement(stub)`` → the stub appears in the bundle
  end-to-end through ``run_interrogation`` with NO orchestrator/core change, the
  four open-core methods still lead in canonical order, and the stub's
  provenance + fieldsPresent entry are stamped (the spec's "an alternative
  measurement method ... appears in the bundle through the interface" gate);
- manifest-driven: the core pack's ``measurement:core-default`` capability's
  ``payload.impl`` resolves to the four default methods, and a non-measurement
  pack contributes none — the loader half of the wiring.

The byte-identical golden gate (test_bundle_golden.py) covers the no-extra path;
this file covers the *extension* path.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from uofa_cli import paths
from uofa_cli.interrogate import measurement_method as mm
from uofa_cli.interrogate.measurement_method import MeasurementContext, MeasurementMethod

FIXTURES = Path(__file__).parent / "fixtures"
ADAPTER = FIXTURES / "golden_adapter.py"

_DEFAULT_KEYS = ["referenceResiduals", "envelopeCoverage",
                 "physicsConstraintResidual", "uqCalibration"]
_DEFAULT_CAP_IDS = [
    "measurement:reference-residuals", "measurement:envelope-coverage",
    "measurement:physics-residuals", "measurement:uq-calibration",
]


class _SecondMetric(MeasurementMethod):
    """A trivial second distance metric — the spec's stub extensibility case."""

    capability_id = "measurement:second-metric"
    output_key = "secondMetric"
    provenance_id = "m-second"

    def compute(self, ctx: MeasurementContext) -> list:
        return [{"quantityOfInterest": "cl", "value": 1.5, "measurementRef": self.provenance_id}]

    def provenance(self, ctx: MeasurementContext) -> dict:
        return {
            "measurementId": self.provenance_id,
            "producedBy": {"library": "stub-metric", "version": "0"},
            "seed": ctx.seed,
            "runEnvironment": ctx.run_env,
        }


@pytest.fixture
def restore_registry():
    """Snapshot/restore the extras registry so a registered stub can't leak."""
    snap = mm.snapshot_extra_measurements()
    try:
        yield
    finally:
        mm.restore_extra_measurements(snap)


def _run(tmp_path: Path) -> dict:
    np = pytest.importorskip("numpy")
    from uofa_cli.interrogate import run_interrogation

    bench = tmp_path / "bench.npz"
    ref = tmp_path / "ref.npz"
    out = tmp_path / "bundle.json"
    np.savez(bench,
             inputs=np.array([[4.0e6, 5.0, 2.0, 12.0], [4.0e6, 8.0, 3.0, 14.0]]),
             input_names=np.array(["reynolds", "aoa", "g1", "g2"]))
    np.savez(ref, **{"ref__cl": np.array([0.5, 0.8]), "ref__cd": np.array([0.02, 0.03])})
    scope = {
        "subject": {"surrogateId": "stub", "modelVersion": "1.0",
                    "surrogateType": "data-driven-emulator", "modelFingerprint": "sha256:stub"},
        "trainingEnvelope": {"dimensions": [{"name": "reynolds", "min": 3.0e6, "max": 5.0e6}]},
        "surrogateUQMethod": "conformal",
    }
    result = run_interrogation(
        adapter_ref=f"{ADAPTER}:GoldenAdapter",
        benchmark_path=bench, reference_path=ref, scope=scope, output_path=out,
        key_path=None, bundle_id="stub-fixture",
        generated_at="2026-01-01T00:00:00Z", sip_version="stub", seed=0,
    )
    return result["bundle"]


def test_registered_method_appears_in_bundle(tmp_path, restore_registry):
    # Baseline: with no extra, the bundle carries exactly the four default keys.
    base = _run(tmp_path)
    assert list(base["measurements"].keys()) == _DEFAULT_KEYS

    # Drop in a second metric through the interface — no core/orchestrator change.
    mm.register_measurement(_SecondMetric())
    bundle = _run(tmp_path)

    keys = list(bundle["measurements"].keys())
    assert keys[:4] == _DEFAULT_KEYS          # defaults still lead, canonical order
    assert keys[4] == "secondMetric"          # the new method appends after
    assert bundle["measurements"]["secondMetric"][0]["value"] == 1.5
    assert "secondMetric" in bundle["completeness"]["fieldsPresent"]
    assert any(p["measurementId"] == "m-second" for p in bundle["measurementProvenance"])


def test_registry_dedupes_by_capability_id(tmp_path, restore_registry):
    # Re-registering the same capability is idempotent (replace-in-place).
    mm.register_measurement(_SecondMetric())
    mm.register_measurement(_SecondMetric())
    bundle = _run(tmp_path)
    assert list(bundle["measurements"].keys()).count("secondMetric") == 1


def test_register_measurement_rejects_non_method():
    with pytest.raises(TypeError):
        mm.register_measurement(object())  # not a MeasurementMethod


def test_register_measurement_requires_identity(restore_registry):
    class _NoId(MeasurementMethod):
        def compute(self, ctx): return []
        def provenance(self, ctx): return {}
    with pytest.raises(ValueError):
        mm.register_measurement(_NoId())  # capability_id/output_key/provenance_id unset


def test_manifest_impl_resolves_to_default_methods():
    # The core pack's measurement:core-default capability → the four methods.
    methods = mm.pack_measurement_methods(["core"])
    assert [m.capability_id for m in methods] == _DEFAULT_CAP_IDS
    assert [m.output_key for m in methods] == _DEFAULT_KEYS


def test_non_measurement_pack_contributes_no_methods():
    assert mm.pack_measurement_methods(["vv40"]) == []


def test_core_measurement_capability_passes_load_gate():
    # CORE_INTERFACE_VERSIONS now knows the measurement interface, so core's own
    # measurement capability is accepted at the load gate (no "unknown interface").
    assert paths.CORE_INTERFACE_VERSIONS.get("measurement") == "1.0"
    paths.validate_active_packs()  # core + active set, incl. core's measurement cap


def test_bad_impl_raises_loudly(tmp_path):
    # A measurement capability whose impl can't be imported fails loudly — a
    # misconfigured active pack must not silently degrade.
    with pytest.raises((ImportError, AttributeError, ValueError, ModuleNotFoundError)):
        mm._impl_to_methods("uofa_cli.interrogate.measurements:does_not_exist")

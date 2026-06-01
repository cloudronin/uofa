"""Addendum A14.5: `uofa interrogate init` guided-setup obligations."""

from __future__ import annotations

import argparse
import json

from uofa_cli.commands import interrogate
from uofa_cli.interrogate import init_wizard as wiz
from uofa_cli.interrogate.schema import validate_bundle


def _init_subparser_options() -> list[str]:
    parser = argparse.ArgumentParser()
    interrogate.add_arguments(parser)
    for action in parser._actions:
        choices = getattr(action, "choices", None)
        if isinstance(choices, dict) and "init" in choices:
            return [s for a in choices["init"]._actions for s in a.option_strings]
    return []


def _init_args(tmp_path, **over):
    ns = argparse.Namespace(
        interrogate_cmd="init", out_dir=tmp_path,
        model=None, docs=None, benchmark=None, reference=None,
        yes=True, scope=None, output_names=None, input_names=None,
    )
    for key, value in over.items():
        setattr(ns, key, value)
    return ns


def _write_scope(tmp_path, *, provenanced=True):
    scope = wiz.build_scope(
        subject={"surrogateId": "s", "modelVersion": "1", "surrogateType": "PINN", "modelFingerprint": "x"},
        envelope_dimensions=[{"name": "reynolds", "min": 1.0, "max": 5.0}, {"name": "aoa", "min": -5.0, "max": 15.0}],
        physics_constraints=[],
        provenance={"trainingEnvelope.reynolds": "entered-by-engineer", "trainingEnvelope.aoa": "entered-by-engineer",
                    "evaluationPoint.reynolds": "entered-by-engineer", "evaluationPoint.aoa": "entered-by-engineer"},
        evaluation_point=[{"name": "reynolds", "value": 3.0}, {"name": "aoa", "value": 5.0}],
    )
    if not provenanced:
        scope["scopeProvenance"].pop("evaluationPoint.aoa", None)
    path = tmp_path / "scope.json"
    path.write_text(json.dumps(scope), encoding="utf-8")
    return path


def test_noninteractive_flags_exist_now():
    # The deliberate A14.1 reversal: --yes / --non-interactive exist for scripts/CI,
    # but they require a pre-written --scope and stay provenanced (behavior tests below).
    opts = _init_subparser_options()
    assert opts, "interrogate init subparser not found"
    for expected in ["--yes", "--non-interactive", "--scope", "--output-names"]:
        assert expected in opts


def test_noninteractive_requires_scope_file(tmp_path):
    # No silent default: --yes without --scope is a loud usage error, writes nothing.
    args = _init_args(tmp_path, scope=None, output_names="cl")
    assert interrogate.run(args) == 2
    assert not (tmp_path / "sip_scope.json").exists()


def test_noninteractive_requires_output_names(tmp_path):
    # The scope does not carry the adapter QoIs; they must be named explicitly.
    args = _init_args(tmp_path, scope=_write_scope(tmp_path), output_names=None)
    assert interrogate.run(args) == 2
    assert not (tmp_path / "sip_adapter.py").exists()


def test_noninteractive_rejects_unprovenanced_scope(tmp_path):
    # The no-silent-scope invariant holds in --yes mode: an untagged field fails loudly.
    args = _init_args(tmp_path, scope=_write_scope(tmp_path, provenanced=False), output_names="cl")
    assert interrogate.run(args) == 1


def test_noninteractive_adopts_scope_and_writes_adapter(tmp_path):
    args = _init_args(tmp_path, scope=_write_scope(tmp_path),
                      output_names="lift_coefficient,drag_coefficient")
    assert interrogate.run(args) == 0
    adapter = (tmp_path / "sip_adapter.py").read_text()
    assert "class GeneratedAdapter(ModelAdapter)" in adapter
    assert "lift_coefficient" in adapter and "drag_coefficient" in adapter
    written = json.loads((tmp_path / "sip_scope.json").read_text())
    assert wiz.unprovenanced_scope_fields(written) == []
    # input names are derived from the scope's declared envelope dimensions.
    assert [d["name"] for d in written["trainingEnvelope"]["dimensions"]] == ["reynolds", "aoa"]


def test_scope_provenance_required_per_field():
    scope = wiz.build_scope(
        subject={"surrogateId": "s"},
        envelope_dimensions=[{"name": "re", "min": 1.0, "max": 2.0}],
        physics_constraints=[],
        provenance={"trainingEnvelope.re": "entered-by-engineer"},
        evaluation_point=[{"name": "re", "value": 1.5}],
    )
    # The evaluation-point field lacks a provenance tag → flagged (no silent scope).
    assert "evaluationPoint.re" in wiz.unprovenanced_scope_fields(scope)
    scope["scopeProvenance"]["evaluationPoint.re"] = "entered-by-engineer"
    assert wiz.unprovenanced_scope_fields(scope) == []


def test_provenance_tags_ride_into_the_bundle_contract():
    # The bundle schema carries declaredScope.scopeProvenance (A14.1).
    bundle = {
        "bundleId": "b", "sipVersion": "0.1.0", "schemaVersion": "sip-evidence-bundle/v0.1",
        "generatedAt": "2026-05-30T12:00:00Z",
        "subject": {"surrogateId": "s", "modelVersion": "1", "surrogateType": "PINN",
                    "modelFingerprint": "sha256:x", "adapterRef": "m:A"},
        "declaredScope": {
            "trainingEnvelope": {"dimensions": [{"name": "re", "min": 1.0, "max": 2.0}]},
            "declaredPhysicsConstraint": [],
            "scopeProvenance": {"trainingEnvelope.re": "extracted-from:card.pdf;confirmed-by-engineer"},
        },
        "measurementProvenance": [{"measurementId": "m1", "producedBy": {"library": "numpy", "version": "1.26"}}],
        "measurements": {
            "referenceResiduals": [], "envelopeCoverage": {"benchmarkSpansEnvelope": True, "evaluationPointInEnvelope": True},
            "physicsConstraintResidual": [], "uqCalibration": {"surrogateUQMethod": None},
        },
        "provenance": {"activity": {"id": "sip:run", "type": "prov:Activity"}},
        "completeness": {"fieldsPresent": [], "fieldsDeliberatelyOmitted": []},
    }
    validate_bundle(bundle)  # scopeProvenance is part of the frozen contract


def test_smoke_test_fails_at_setup_on_incomplete_adapter():
    class Incomplete:
        def predict(self, x):
            raise NotImplementedError("complete the torch model load, then re-run init")

    ok, msg = wiz.smoke_test_adapter(Incomplete(), [[1, 2]], ["cl"])
    assert not ok and "raised at setup" in msg


def test_smoke_test_fails_on_wrong_output_shape():
    class WrongShape:
        def predict(self, x):
            return [0.0]  # not a dict of QoI -> array

    ok, msg = wiz.smoke_test_adapter(WrongShape(), [[1, 2]], ["cl"])
    assert not ok


def test_generated_adapter_is_model_adapter_subclass():
    src = wiz.generate_adapter_source(
        class_name="GeneratedAdapter", model_format="onnx", model_path="m.onnx",
        input_names=["re"], output_names=["cl"],
    )
    assert "class GeneratedAdapter(ModelAdapter)" in src
    assert "def predict" in src


def test_init_never_generates_reference_values():
    scope = wiz.build_scope(
        subject={"surrogateId": "s"},
        envelope_dimensions=[{"name": "re", "min": 1.0, "max": 2.0}],
        physics_constraints=[],
        provenance={"trainingEnvelope.re": "entered-by-engineer"},
    )
    flat = json_dumps_lower(scope)
    assert "ref__" not in flat and "reference" not in flat


def json_dumps_lower(obj) -> str:
    import json
    return json.dumps(obj).lower()

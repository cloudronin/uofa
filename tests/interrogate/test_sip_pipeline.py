"""SIP pipeline tests (Step 4): adapter contract, full run_interrogation,
PROV-DM well-formedness, signing round-trip, and the CLI no-verdict firewall.

These exercise the real measurement + signing path but need no model framework
— a tiny EchoAdapter stands in for the user's surrogate. numpy + jsonschema
come from the [interrogate] extra.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

np = pytest.importorskip("numpy")
pytest.importorskip("jsonschema")

from uofa_cli import integrity
from uofa_cli.interrogate import run_interrogation
from uofa_cli.interrogate.adapter import ModelAdapter, load_adapter
from uofa_cli.interrogate.forbidden import FORBIDDEN_TOKENS, find_forbidden_property_names
from uofa_cli.interrogate.prov import find_orphan_entities
from uofa_cli.interrogate.schema import validate_bundle

N = 50

_ADAPTER_SRC = '''
import numpy as np
from uofa_cli.interrogate.adapter import ModelAdapter

class EchoAdapter(ModelAdapter):
    """Returns near-reference predictions for the lift_coefficient QoI."""
    def predict(self, inputs):
        n = len(inputs)
        return {"lift_coefficient": np.zeros(n)}

class NotAnAdapter:
    pass
'''


@pytest.fixture
def adapter_file(tmp_path) -> Path:
    path = tmp_path / "echo_adapter.py"
    path.write_text(_ADAPTER_SRC, encoding="utf-8")
    return path


@pytest.fixture
def benchmark_file(tmp_path) -> Path:
    path = tmp_path / "benchmark.npz"
    inputs = np.column_stack([
        np.linspace(2.0e6, 6.0e6, N),   # reynolds spans the envelope
        np.linspace(-5.0, 15.0, N),     # aoa spans the envelope
    ])
    np.savez(path, inputs=inputs, input_names=np.array(["reynolds", "aoa"]))
    return path


@pytest.fixture
def reference_file(tmp_path) -> Path:
    path = tmp_path / "reference.npz"
    np.savez(
        path,
        **{
            "ref__lift_coefficient": np.zeros(N),
            "constraint__mass_conservation": np.full(N, 1e-6),
            "lower__lift_coefficient": np.full(N, -0.1),
            "upper__lift_coefficient": np.full(N, 0.1),
        },
    )
    return path


def _scope() -> dict:
    return {
        "subject": {
            "surrogateId": "echo-surrogate",
            "modelVersion": "1.0.0",
            "surrogateType": "data-driven-emulator",
            "modelFingerprint": "sha256:echo",
        },
        "trainingEnvelope": {
            "dimensions": [
                {"name": "reynolds", "min": 2.0e6, "max": 6.0e6},
                {"name": "aoa", "min": -5.0, "max": 15.0},
            ]
        },
        "evaluationPoint": {
            "coordinates": [
                {"name": "reynolds", "value": 3.0e6},
                {"name": "aoa", "value": 4.0},
            ]
        },
        "declaredPhysicsConstraint": [
            {"constraintId": "mass_conservation", "description": "div(u)=0", "kind": "conservation"}
        ],
        "surrogateUQMethod": "conformal-prediction",
        "parentModelSnapshot": {
            "parentCOU": "uofa:parent-rans",
            "parentDecision": "Accepted",
            "parentMRL": 4,
            "snapshotTimestamp": "2026-05-30T00:00:00Z",
        },
        "completeness": {"fieldsDeliberatelyOmitted": []},
    }


def _run(adapter_file, benchmark_file, reference_file, output, key=None):
    return run_interrogation(
        adapter_ref=f"{adapter_file}:EchoAdapter",
        benchmark_path=benchmark_file,
        reference_path=reference_file,
        scope=_scope(),
        output_path=output,
        key_path=key,
        bundle_id="sip-bundle-test",
        generated_at="2026-05-30T12:00:00Z",
    )


# ── Adapter contract ───────────────────────────────────────────────────────


class TestAdapter:
    def test_load_adapter_from_file(self, adapter_file):
        adapter = load_adapter(f"{adapter_file}:EchoAdapter")
        assert isinstance(adapter, ModelAdapter)
        out = adapter.predict(np.zeros((3, 2)))
        assert "lift_coefficient" in out and len(out["lift_coefficient"]) == 3

    def test_load_adapter_rejects_non_adapter(self, adapter_file):
        with pytest.raises(ValueError):
            load_adapter(f"{adapter_file}:NotAnAdapter")


# ── Full pipeline ──────────────────────────────────────────────────────────


class TestPipeline:
    def test_unsigned_bundle_is_schema_valid(self, adapter_file, benchmark_file, reference_file, tmp_path):
        out = tmp_path / "bundle.json"
        result = _run(adapter_file, benchmark_file, reference_file, out)
        assert result["signed"] is False
        validate_bundle(result["bundle"])  # no exception
        qois = [r["quantityOfInterest"] for r in result["bundle"]["measurements"]["referenceResiduals"]]
        assert "lift_coefficient" in qois

    def test_measurements_populated(self, adapter_file, benchmark_file, reference_file, tmp_path):
        out = tmp_path / "bundle.json"
        m = _run(adapter_file, benchmark_file, reference_file, out)["bundle"]["measurements"]
        # benchmark spans the envelope and eval point is inside it
        assert m["envelopeCoverage"]["benchmarkSpansEnvelope"] is True
        assert m["envelopeCoverage"]["evaluationPointInEnvelope"] is True
        # physics constraint residual computed from the provided field
        assert any(p["constraintId"] == "mass_conservation" for p in m["physicsConstraintResidual"])
        # UQ empirical coverage computed from provided intervals (ref=0 inside [-.1,.1] => 1.0)
        assert m["uqCalibration"]["empiricalCoverage"] == pytest.approx(1.0)

    def test_no_forbidden_field_in_bundle(self, adapter_file, benchmark_file, reference_file, tmp_path):
        out = tmp_path / "bundle.json"
        bundle = _run(adapter_file, benchmark_file, reference_file, out)["bundle"]
        assert list(find_forbidden_property_names(bundle)) == []

    def test_provenance_has_no_orphans(self, adapter_file, benchmark_file, reference_file, tmp_path):
        out = tmp_path / "bundle.json"
        bundle = _run(adapter_file, benchmark_file, reference_file, out)["bundle"]
        # The W-PROV-01 condition: every entity reachable from the run.
        assert find_orphan_entities(bundle["provenance"]) == []

    def test_signed_bundle_verifies(self, adapter_file, benchmark_file, reference_file, tmp_path):
        key = tmp_path / "sip.key"
        integrity.generate_keypair(key)
        out = tmp_path / "bundle.json"
        result = _run(adapter_file, benchmark_file, reference_file, out, key=key)
        assert result["signed"] is True
        hash_ok, sig_ok = integrity.verify_file(out, key.with_suffix(".pub"))
        assert hash_ok and sig_ok


# ── CLI no-verdict firewall ────────────────────────────────────────────────


class TestCommandFirewall:
    def test_interrogate_command_emits_no_verdict(
        self, adapter_file, benchmark_file, reference_file, tmp_path, capsys
    ):
        from uofa_cli.commands import interrogate as cmd

        scope_file = tmp_path / "scope.json"
        scope_file.write_text(json.dumps(_scope()), encoding="utf-8")
        out = tmp_path / "bundle.json"
        args = argparse.Namespace(
            adapter=f"{adapter_file}:EchoAdapter",
            benchmark=benchmark_file,
            reference=reference_file,
            scope=scope_file,
            output=out,
            key=None,
            seed=7,
        )
        rc = cmd.run(args)
        assert rc == 0
        printed = capsys.readouterr().out.lower()
        # The command surface must carry no decision token.
        for token in FORBIDDEN_TOKENS:
            assert token.lower() not in printed, f"decision token {token!r} leaked into output"

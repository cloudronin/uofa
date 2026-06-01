"""P3 regression gate — the SIP bundle stays byte-identical across the §3
measurement-interface refactor.

Builds a deterministic bundle from a fixed adapter + benchmark + reference +
scope (all four measurement families exercised), normalizes the env-varying
fields (library versions, runEnvironment, rounded floats), and asserts it equals
a committed golden. Captured BEFORE the refactor — the 4-function default
measurement pack MUST reproduce this bundle exactly (the spec's hard gate).

Regenerate the golden intentionally with:  python tests/interrogate/test_bundle_golden.py
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"
GOLDEN = FIXTURES / "golden_bundle.json"
ADAPTER = FIXTURES / "golden_adapter.py"

# Env-varying keys normalized out (orthogonal to the measurement refactor).
_ENV_KEYS = {"version", "python", "platform"}


def _normalize(obj):
    """Recursively normalize env-varying values + round floats for cross-numpy stability.

    Beyond the ``version``/``python``/``platform`` keys, two more things are
    env-varying and must be scrubbed or the gate is host-pinned (and leaks an
    absolute home path, AGENTS.md §10):
      - the PROV-DM block embeds library versions inside SoftwareAgent identifiers
        (``sip:agent/numpy@1.26.4``), labels (``numpy 1.26.4``), and the activity's
        ``wasAssociatedWith`` refs — CI installs a different numpy/uofa;
      - ``subject.adapterRef`` is the absolute path to the fixture adapter, which
        differs per checkout (``/Users/...`` vs ``/workspaces/...``).
    """
    if isinstance(obj, dict):
        is_agent = obj.get("type") == "prov:SoftwareAgent"
        out = {}
        for k, v in obj.items():
            if k in _ENV_KEYS:
                out[k] = "<env>"
            elif is_agent and k == "label" and isinstance(v, str) and " " in v:
                out[k] = v.rsplit(" ", 1)[0] + " <env>"  # "numpy 1.26.4" → "numpy <env>"
            else:
                out[k] = _normalize(v)
        return out
    if isinstance(obj, list):
        return [_normalize(x) for x in obj]
    if isinstance(obj, float):
        return round(obj, 10)
    if isinstance(obj, str):
        if obj.startswith("sip:agent/") and "@" in obj:
            return obj.rsplit("@", 1)[0] + "@<env>"  # "sip:agent/numpy@1.26.4" → "...@<env>"
        if str(ADAPTER) in obj:
            return obj.replace(str(ADAPTER), "<adapter>")  # abs adapterRef path → stable
    return obj


def _serialize(bundle: dict) -> str:
    # No sort_keys → preserves insertion order, so a key-order change is caught (byte-identical).
    return json.dumps(_normalize(bundle), indent=2, ensure_ascii=False)


def _build_bundle(tmp_path: Path) -> dict:
    np = pytest.importorskip("numpy")
    from uofa_cli.interrogate import run_interrogation

    bench = tmp_path / "bench.npz"
    ref = tmp_path / "ref.npz"
    out = tmp_path / "bundle.json"
    np.savez(
        bench,
        inputs=np.array([[4.0e6, 5.0, 2.0, 12.0], [4.0e6, 8.0, 3.0, 14.0]]),
        input_names=np.array(["reynolds", "aoa", "g1", "g2"]),
    )
    np.savez(
        ref,
        **{
            "ref__cl": np.array([0.5, 0.8]),
            "ref__cd": np.array([0.02, 0.03]),
            "constraint__continuity": np.array([0.001, -0.002, 0.0015]),
            "lower__cl": np.array([0.45, 0.75]),
            "upper__cl": np.array([0.55, 0.85]),
        },
    )
    scope = {
        "subject": {"surrogateId": "golden", "modelVersion": "1.0",
                    "surrogateType": "data-driven-emulator", "modelFingerprint": "sha256:golden"},
        "trainingEnvelope": {"dimensions": [
            {"name": "reynolds", "min": 3.0e6, "max": 5.0e6},
            {"name": "aoa", "min": -2.5, "max": 12.5},
        ]},
        "evaluationPoint": {"coordinates": [
            {"name": "reynolds", "value": 4.0e6}, {"name": "aoa", "value": 5.0},
        ]},
        "declaredPhysicsConstraint": [
            {"constraintId": "continuity", "description": "mass conservation residual",
             "kind": "conservation"},
        ],
        "surrogateUQMethod": "conformal",
    }
    result = run_interrogation(
        adapter_ref=f"{ADAPTER}:GoldenAdapter",
        benchmark_path=bench, reference_path=ref, scope=scope, output_path=out,
        key_path=None, bundle_id="golden-fixture",
        generated_at="2026-01-01T00:00:00Z", sip_version="golden", seed=0,
    )
    return result["bundle"]


def test_bundle_matches_golden(tmp_path):
    actual = _serialize(_build_bundle(tmp_path))
    assert GOLDEN.exists(), "golden_bundle.json missing — regenerate intentionally (see module docstring)"
    assert actual == GOLDEN.read_text(encoding="utf-8"), (
        "SIP bundle drifted from the golden — the §3 measurement-interface refactor "
        "must reproduce it byte-for-byte (modulo normalized env fields)."
    )


if __name__ == "__main__":  # intentional golden (re)capture
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        text = _serialize(_build_bundle(Path(d)))
    GOLDEN.write_text(text, encoding="utf-8")
    print(f"captured golden ({len(text)} bytes) → {GOLDEN}")

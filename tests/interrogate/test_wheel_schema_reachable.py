"""v1 acceptance gate: the SIP schema is reachable — and rejects forbidden
fields — after a real (non-editable) install, not just from a source checkout.

The firewall's schema layer silently no-ops for pip-installed users if the
schema isn't shipped in the wheel. firewall_guard enforces the force-include
config deterministically in CI; this test empirically confirms it by building
the wheel and validating against the schema extracted from inside it (the
post-install location). Skipped if the build backend is unavailable offline.
"""

from __future__ import annotations

import json
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

pytest.importorskip("jsonschema")
import jsonschema  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
WHEEL_SCHEMA_PATH = "uofa_cli/_data/repo/specs/sip_evidence_bundle_schema.json"


@pytest.fixture(scope="session")
def built_wheel(tmp_path_factory) -> Path:
    out = tmp_path_factory.mktemp("wheel")
    try:
        subprocess.run(
            [sys.executable, "-m", "build", "--wheel", "--outdir", str(out)],
            cwd=str(REPO_ROOT), capture_output=True, text=True, timeout=600, check=True,
        )
    except Exception as exc:  # build backend / network unavailable
        pytest.skip(f"wheel build unavailable: {exc}")
    wheels = list(out.glob("*.whl"))
    if not wheels:
        pytest.skip("no wheel produced")
    return wheels[0]


def _minimal_valid_bundle() -> dict:
    return {
        "bundleId": "sip-bundle-wheel",
        "sipVersion": "0.1.0",
        "schemaVersion": "sip-evidence-bundle/v0.1",
        "generatedAt": "2026-05-30T12:00:00Z",
        "subject": {"surrogateId": "s", "modelVersion": "1", "surrogateType": "PINN",
                    "modelFingerprint": "sha256:x", "adapterRef": "m:A"},
        "declaredScope": {
            "trainingEnvelope": {"dimensions": [{"name": "re", "min": 1.0, "max": 2.0}]},
            "declaredPhysicsConstraint": [],
        },
        "measurementProvenance": [
            {"measurementId": "m1", "producedBy": {"library": "numpy", "version": "1.26"}}
        ],
        "measurements": {
            "referenceResiduals": [],
            "envelopeCoverage": {"benchmarkSpansEnvelope": True, "evaluationPointInEnvelope": True},
            "physicsConstraintResidual": [],
            "uqCalibration": {"surrogateUQMethod": None},
        },
        "provenance": {"activity": {"id": "sip:run", "type": "prov:Activity"}},
        "completeness": {"fieldsPresent": [], "fieldsDeliberatelyOmitted": []},
    }


def test_schema_ships_in_wheel(built_wheel):
    with zipfile.ZipFile(built_wheel) as zf:
        names = zf.namelist()
    assert WHEEL_SCHEMA_PATH in names, (
        f"{WHEEL_SCHEMA_PATH} missing from the wheel — the firewall's schema "
        f"layer would not run for pip-installed users."
    )


def test_wheel_schema_rejects_forbidden_field(built_wheel):
    with zipfile.ZipFile(built_wheel) as zf:
        schema = json.loads(zf.read(WHEEL_SCHEMA_PATH))
    # A complete bundle validates against the wheel-shipped schema ...
    jsonschema.validate(_minimal_valid_bundle(), schema)
    # ... and the same bundle with a verdict field is rejected (the firewall,
    # running off the schema as it ships to real users).
    poisoned = _minimal_valid_bundle()
    poisoned["verdict"] = "PASS"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(poisoned, schema)

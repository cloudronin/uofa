"""`uofa evidence seal --mesh-study` and the fold into a signed package.

Run as subprocesses through the real CLI. The property that matters is the
same one tests/solver/test_pipeline_e2e.py guards for the rest of the sidecar:
the record is folded BEFORE the package is hashed, so it sits inside the
signature, and an edit to it breaks verification.

Data: an upstream SimEval oracle table with a synthetic reported value
(tests/fixtures/mesh_study/README.md).
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
FIXTURES = REPO / "tests" / "fixtures" / "mesh_study"
TEMPLATE = REPO / "packs" / "vv40" / "templates" / "uofa-starter-filled.xlsx"
TABLE = "upstream_n3_const_r.csv"

STUDY = {
    "id": "synthetic-n3",
    "forFactorType": "Discretization error",
    "table": TABLE,
    "quantityColumn": "qoi",
    "refinement": {"column": "mesh_size", "kind": "mesh-size"},
    "formalOrder": 1.0,
    "reported": {"value": 0.3, "units": "%", "basis": "relative",
                 "source": "synthetic value for this test"},
}


def _uofa(*args, cwd):
    return subprocess.run([sys.executable, "-m", "uofa_cli.cli", "--no-color", *args],
                          cwd=cwd, capture_output=True, text=True)


def _declare(work, *studies, name="study.json"):
    (work / name).write_text(json.dumps(
        {"schemaVersion": "uofa-mesh-study/v0.1", "studies": list(studies)}))
    return name


@pytest.fixture
def work(tmp_path):
    work = tmp_path / "work"
    (work / "evidence").mkdir(parents=True)
    shutil.copy(FIXTURES / TABLE, work / "evidence" / TABLE)
    assert _uofa("keygen", "demo.key", cwd=work).returncode == 0
    return work


def test_seal_without_mesh_study_adds_nothing(work):
    """Null control: no flag, no new key, no new readout section."""
    sealed = _uofa("evidence", "seal", "evidence", "-o", "ev.json", cwd=work)
    assert sealed.returncode == 0, sealed.stderr
    assert "calculationVerification" not in json.loads((work / "ev.json").read_text())
    assert "What the mesh study says" not in sealed.stdout


def test_seal_records_the_study_and_reads_it_out(work):
    pytest.importorskip("matplotlib")
    sealed = _uofa("evidence", "seal", "evidence", "--mesh-study", _declare(work, STUDY),
                   "-o", "ev.json", cwd=work)
    assert sealed.returncode == 0, sealed.stderr
    [record] = json.loads((work / "ev.json").read_text())["calculationVerification"]
    assert record["cvStudyId"] == "synthetic-n3" and record["cvStatus"] == "computed"
    assert record["cvSourceMember"] == TABLE
    out = sealed.stdout
    assert out.index("What the solver artifacts say") < out.index("What the mesh study says")
    assert "synthetic-n3 (Discretization error): computed, method N3_mono" in out


def test_inventory_reads_out_but_writes_no_sidecar(work):
    inv = _uofa("evidence", "inventory", "evidence", "--mesh-study", _declare(work, STUDY), cwd=work)
    assert inv.returncode == 0, inv.stderr
    assert "What the mesh study says" in inv.stdout
    assert not list(work.glob("*evidence.json"))


def test_malformed_declaration_stops_before_anything_is_written(work):
    typo = dict(STUDY, formalorder=1.0)     # not a key the schema knows
    typo.pop("formalOrder")
    sealed = _uofa("evidence", "seal", "evidence", "--mesh-study", _declare(work, typo),
                   "-o", "ev.json", cwd=work)
    assert sealed.returncode != 0
    assert "unknown key" in sealed.stdout + sealed.stderr
    assert not (work / "ev.json").exists()


def test_unsealed_table_is_recorded_not_run(work):
    missing = dict(STUDY, table="not-in-folder.csv")
    sealed = _uofa("evidence", "seal", "evidence", "--mesh-study", _declare(work, missing),
                   "-o", "ev.json", cwd=work)
    assert sealed.returncode == 0, sealed.stderr
    [record] = json.loads((work / "ev.json").read_text())["calculationVerification"]
    assert (record["cvStatus"], record["cvReason"]) == ("not-run", "table-not-sealed")


def _seal_and_import(work, out="pkg.jsonld", *, with_evidence=True):
    if with_evidence:
        sealed = _uofa("evidence", "seal", "evidence", "--mesh-study", _declare(work, STUDY),
                       "-o", "ev.json", cwd=work)
        assert sealed.returncode == 0, sealed.stderr
    args = ["import", str(TEMPLATE), "-o", out, "--sign", "--key", "demo.key"]
    if with_evidence:
        args[2:2] = ["--evidence", "ev.json"]
    imported = _uofa(*args, cwd=work)
    assert imported.returncode == 0, imported.stdout + imported.stderr
    return json.loads((work / out).read_text())


def test_record_is_folded_inside_the_signature(work):
    pytest.importorskip("matplotlib")
    doc = _seal_and_import(work)
    sidecar = json.loads((work / "ev.json").read_text())
    assert doc["calculationVerification"] == sidecar["calculationVerification"]
    verified = _uofa("verify", "pkg.jsonld", "--pubkey", "demo.pub", cwd=work)
    assert verified.returncode == 0, verified.stdout + verified.stderr

    # Folded before hashing: editing the record breaks the signature.
    doc["calculationVerification"][0]["cvGciAbsolute"] = 99.0
    (work / "tampered.jsonld").write_text(json.dumps(doc, indent=2, sort_keys=True))
    assert _uofa("verify", "tampered.jsonld", "--pubkey", "demo.pub", cwd=work).returncode != 0


def test_fold_adds_no_shacl_violations(work):
    """No shape is closed, so the undeclared cv* terms pass C2 untouched.
    Asserted rather than assumed, as the existing fold test does."""
    _seal_and_import(work, "sealed.jsonld")
    _seal_and_import(work, "plain.jsonld", with_evidence=False)
    sealed = _uofa("shacl", "sealed.jsonld", cwd=work).stdout
    plain = _uofa("shacl", "plain.jsonld", cwd=work).stdout
    assert _violations(sealed) == _violations(plain)
    assert "calculationVerification" not in sealed and "cvStatus" not in sealed


def _violations(text: str) -> str:
    import re
    found = re.search(r"(\d+) violation", text)
    return found.group(1) if found else "0"

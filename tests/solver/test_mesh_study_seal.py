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
    # Folded as sealed, plus the IRI the fold gives each record.
    [folded] = doc["calculationVerification"]
    assert folded["id"] == f"{doc['id']}/calculation-verification/synthetic-n3"
    assert [{k: v for k, v in r.items() if k != "id"} for r in doc["calculationVerification"]] \
        == sidecar["calculationVerification"]
    assert "id" not in sidecar["calculationVerification"][0]   # the seal itself is unchanged
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


# ── The IRI the fold gives each record ──────────────────────────────────────
# The engine names a finding's affected node by its IRI; a record with none
# read `affected: null`. Unit cases for the naming; the readout itself is
# tested through the CLI in tests/test_calcverif_rules.py and
# tests/test_calcverif_pipeline_e2e.py.

def _named(doc):
    from uofa_cli.commands.import_excel import _name_study_records
    _name_study_records(doc)
    return doc


def test_fold_names_each_record_under_the_package():
    doc = _named({"id": "https://example.org/p", "calculationVerification": [
        {"cvStudyId": "max-velocity", "cvStatus": "computed"},
        {"cvStudyId": "helicity", "cvStatus": "computed"}]})
    ids = [r["id"] for r in doc["calculationVerification"]]
    assert ids == ["https://example.org/p/calculation-verification/max-velocity",
                   "https://example.org/p/calculation-verification/helicity"]
    assert list(doc["calculationVerification"][0])[0] == "id"   # first key, for the reader
    assert doc["calculationVerification"][0]["cvStatus"] == "computed"


def test_fold_name_is_one_to_one_with_the_study_id():
    """Percent-encoded, not slugified: ids a slug would merge stay apart, and
    a '/' cannot shorten the name the engine prints."""
    doc = _named({"id": "urn:p", "calculationVerification": [
        {"cvStudyId": "Max Velocity"}, {"cvStudyId": "max-velocity"}, {"cvStudyId": "a/b"}]})
    ids = [r["id"] for r in doc["calculationVerification"]]
    assert ids == ["urn:p/calculation-verification/Max%20Velocity",
                   "urn:p/calculation-verification/max-velocity",
                   "urn:p/calculation-verification/a%2Fb"]


def test_fold_mints_nothing_it_cannot_ground():
    """A record that has an id keeps it; no package id or no study id -> no id."""
    keep = _named({"id": "urn:p", "calculationVerification": [
        {"id": "urn:already", "cvStudyId": "s"}, {"cvStatus": "not-run"}]})
    assert keep["calculationVerification"] == [{"id": "urn:already", "cvStudyId": "s"},
                                               {"cvStatus": "not-run"}]
    no_base = _named({"calculationVerification": [{"cvStudyId": "s"}]})
    assert no_base["calculationVerification"] == [{"cvStudyId": "s"}]
    assert _named({"id": "urn:p"}) == {"id": "urn:p"}

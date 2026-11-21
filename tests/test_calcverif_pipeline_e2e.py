"""Calculation verification, end to end through the real CLI.

AGENTS.md section 13: test the pipeline, not the step. Each case runs
evidence folder -> `uofa evidence seal --mesh-study` -> `uofa import
--evidence ... --sign --check` on the filled vv40 starter workbook, with and
without `--calcverif`.

- docs/examples/calcverif-starter: upstream oracle table, synthetic reported
  value. W-CV-01 must fire with the switch and nothing W-CV without it.
- docs/examples/calcverif-vena-cava: upstream's IVC study (Craven 2018), no
  formal order and no reported value, as upstream itself declares it. The W-CV
  rules load and must report nothing.

Also the regeneration no-op for the starter's committed expected sidecar
(AGENTS.md section 13: every derived committed artifact needs one).
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from uofa_cli import paths

REPO = Path(__file__).resolve().parents[1]
EXAMPLES = REPO / "docs" / "examples"
TEMPLATE = REPO / "packs" / "vv40" / "templates" / "uofa-starter-filled.xlsx"

JENA_AVAILABLE = shutil.which("java") is not None and paths.jar_path().exists()
pytestmark = pytest.mark.usefixtures("calcverif_extra")


@pytest.fixture
def calcverif_extra():
    pytest.importorskip("matplotlib")


def _uofa(*args, cwd):
    return subprocess.run([sys.executable, "-m", "uofa_cli.cli", "--no-color", *args],
                          cwd=cwd, capture_output=True, text=True)


def _workspace(tmp_path, example):
    work = tmp_path / example
    shutil.copytree(EXAMPLES / example, work)
    for stray in ("expected-evidence.json", "evidence.json"):
        (work / stray).unlink(missing_ok=True)
    assert _uofa("keygen", "demo.key", cwd=work).returncode == 0
    return work


def _seal(work):
    sealed = _uofa("evidence", "seal", "evidence", "--mesh-study", "study.json",
                   "-o", "evidence.json", cwd=work)
    assert sealed.returncode == 0, sealed.stdout + sealed.stderr
    return sealed


def _import(work, out, *extra):
    return _uofa("import", str(TEMPLATE), "--evidence", "evidence.json", "--pack", "vv40",
                 "-o", out, "--sign", "--key", "demo.key", "--check", *extra, cwd=work)


def _w_cv(text: str) -> dict[str, int]:
    return {m.group(1): int(m.group(2))
            for m in re.finditer(r"(W-CV-\d{2}) \[[A-Za-z]+\] — (\d+) hit", text)}


def _violations(text: str) -> str:
    found = re.search(r"(\d+) violation", text)
    return found.group(1) if found else "0"


def test_starter_expected_sidecar_regenerates(tmp_path):
    work = tmp_path / "starter"
    shutil.copytree(EXAMPLES / "calcverif-starter", work)
    _seal(work)
    regenerated = json.loads((work / "evidence.json").read_text())
    committed = json.loads((EXAMPLES / "calcverif-starter" / "expected-evidence.json").read_text())
    for doc in (regenerated, committed):
        doc.pop("generatedAt")      # the only field two runs may differ in
    assert regenerated == committed


@pytest.mark.skipif(not JENA_AVAILABLE, reason="weakener engine JAR not built")
def test_starter_pipeline_reports_w_cv_01_only_with_the_switch(tmp_path):
    work = _workspace(tmp_path, "calcverif-starter")
    sealed = _seal(work)
    assert "oracle-n3 (Discretization error): computed, method N3_mono" in sealed.stdout
    assert "reported 0.3 % relative (diverges)" in sealed.stdout

    on = _import(work, "on.jsonld", "--calcverif")
    assert _w_cv(on.stdout) == {"W-CV-01": 1}, on.stdout
    assert "calculation-verification rules on (--calcverif)" in on.stdout

    off = _import(work, "off.jsonld")
    assert _w_cv(off.stdout) == {} and "W-CV" not in off.stdout

    # The fold reached the signed package, and C1 holds.
    doc = json.loads((work / "on.jsonld").read_text())
    assert doc["calculationVerification"][0]["cvGciComparison"] == "diverges"
    assert _uofa("verify", "on.jsonld", "--pubkey", "demo.pub", cwd=work).returncode == 0

    # The switch changes nothing but the W-CV lines: same C2 result, same exit.
    assert _violations(on.stdout) == _violations(off.stdout)
    assert on.returncode == off.returncode


@pytest.mark.skipif(not JENA_AVAILABLE, reason="weakener engine JAR not built")
def test_vena_cava_pipeline_is_silent_by_structure(tmp_path):
    work = _workspace(tmp_path, "calcverif-vena-cava")
    _seal(work)
    records = json.loads((work / "evidence.json").read_text())["calculationVerification"]
    assert [r["cvStudyId"] for r in records] == ["ivc-max-velocity", "ivc-helicity"]
    for r in records:
        assert r["cvStatus"] == "computed" and r["cvMethod"] == "largeN_mono"
        assert len(r["cvLevel"]) == 8 and r["cvDimension"] == 3
        assert "cvFormalOrder" not in r and r["cvOrderAgreement"] == "no-formal-order"
        assert r["cvSafetyFactor"] == 3.0
        assert r["cvTripletConcern"] == "false"
        assert "cvReportedGci" not in r and "cvGciComparison" not in r

    on = _import(work, "on.jsonld", "--calcverif")
    assert "calculation-verification rules on (--calcverif)" in on.stdout
    assert _w_cv(on.stdout) == {}, on.stdout
    doc = json.loads((work / "on.jsonld").read_text())
    assert len(doc["calculationVerification"]) == 2
    assert _uofa("verify", "on.jsonld", "--pubkey", "demo.pub", cwd=work).returncode == 0


# ── The vena cava README's tamper demonstration ─────────────────────────────
# The commands are read out of the README and run as written, so the README
# and these tests cannot drift apart. The only substitution is the
# interpreter: `python3`/`python` become this test's interpreter.

VENA_README = EXAMPLES / "calcverif-vena-cava" / "README.md"


def _readme_python_c(index: int) -> str:
    """The code of the index-th `python3 -c '...'` command in the README."""
    import shlex
    lines = [ln for ln in VENA_README.read_text().splitlines() if ln.startswith("python3 -c '")]
    argv = shlex.split(lines[index])
    assert argv[:2] == ["python3", "-c"]
    return argv[2]


def _readme_heredoc() -> str:
    text = VENA_README.read_text()
    body = text.split("python - <<'EOF'\n", 1)[1].split("\nEOF\n", 1)[0]
    assert "mesh_study.run_studies" in body
    return body


def _run_py(code: str, cwd):
    return subprocess.run([sys.executable, "-c", code], cwd=cwd, capture_output=True, text=True)


def _signed_vena_cava(tmp_path):
    work = _workspace(tmp_path, "calcverif-vena-cava")
    _seal(work)
    imported = _uofa("import", str(TEMPLATE), "--evidence", "evidence.json", "--pack", "vv40",
                     "-o", "vena-cava.jsonld", "--sign", "--key", "demo.key", cwd=work)
    assert imported.returncode == 0, imported.stdout + imported.stderr
    return work


def test_vena_cava_quiet_change_breaks_the_signature(tmp_path):
    """README step 2: one recorded number edited in a copy -> verify fails."""
    work = _signed_vena_cava(tmp_path)
    assert _uofa("verify", "vena-cava.jsonld", "--pubkey", "demo.pub", cwd=work).returncode == 0

    altered = work / "vena-cava.DELIBERATELY-ALTERED.jsonld"
    shutil.copy(work / "vena-cava.jsonld", altered)
    edit = _run_py(_readme_python_c(0), work)
    assert edit.returncode == 0 and "edited 1 value" in edit.stdout, edit.stderr

    # Exactly one line differs, and it is max velocity's relative index.
    before = (work / "vena-cava.jsonld").read_text().splitlines()
    after = altered.read_text().splitlines()
    changed = [(a, b) for a, b in zip(before, after) if a != b]
    assert len(before) == len(after) and len(changed) == 1
    assert '"cvGciRelative": 0.0005' in changed[0][1]
    doc = json.loads(altered.read_text())
    assert doc["calculationVerification"][0]["cvStudyId"] == "ivc-max-velocity"
    assert doc["calculationVerification"][0]["cvGciRelative"] == 0.0005
    assert doc["calculationVerification"][0]["cvGciRelative"] < \
        json.loads((work / "vena-cava.jsonld").read_text())["calculationVerification"][0]["cvGciRelative"]

    verified = _uofa("verify", altered.name, "--pubkey", "demo.pub", cwd=work)
    assert verified.returncode != 0, verified.stdout
    assert "✗ Measurement hash match" in verified.stdout


def test_vena_cava_changed_table_does_not_run_against_original_seal(tmp_path):
    """README step 3: an edited copy of the table, read against the original
    seal's digests -> not-run / table-not-sealed for both studies."""
    work = _workspace(tmp_path, "calcverif-vena-cava")
    _seal(work)
    snippet = _readme_heredoc()

    # Control: the same snippet on the unaltered folder computes both studies.
    control = _run_py(snippet.replace('"DELIBERATELY-ALTERED-evidence"', '"evidence"'), work)
    assert control.returncode == 0, control.stderr
    assert control.stdout.count("computed, method largeN_mono") == 2

    altered = work / "DELIBERATELY-ALTERED-evidence"
    altered.mkdir()
    shutil.copy(work / "evidence" / "ivc_mesh_study.csv", altered / "ivc_mesh_study.csv")
    edit = _run_py(_readme_python_c(1), work)
    assert edit.returncode == 0 and "edited 1 value" in edit.stdout, edit.stderr
    diff = [(a, b) for a, b in zip((work / "evidence" / "ivc_mesh_study.csv").read_text().splitlines(),
                                   (altered / "ivc_mesh_study.csv").read_text().splitlines()) if a != b]
    assert diff == [("102500000,0.25233,0.45549", "102500000,0.25333,0.45549")]

    rerun = _run_py(snippet, work)
    assert rerun.returncode == 0, rerun.stderr
    assert rerun.stdout.count("not run (table-not-sealed)") == 2
    assert rerun.stdout.count("the bytes read from ivc_mesh_study.csv are not the bytes the seal recorded") == 2
    assert "computed" not in rerun.stdout

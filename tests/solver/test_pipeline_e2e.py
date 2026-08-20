"""Drive the fixture folder through the whole path and check what survives.

AGENTS.md §13: "Test the pipeline, not the step. A component is not done until
its output has been through the command that consumes it." The cited failure is
this exact shape -- the keyless extractor was tested to xlsx and never through
`uofa import`.

The property that matters here is ORDER: the seal has to be folded in before
the package is hashed, or the manifest sits beside a signed document and proves
nothing about it.
"""

from __future__ import annotations

import json
import subprocess
import sys

import pytest


def _uofa(*args, cwd):
    return subprocess.run(
        [sys.executable, "-m", "uofa_cli.cli", "--no-color", *args],
        cwd=cwd, capture_output=True, text=True)


@pytest.fixture
def workspace(tmp_path, evidence_folder):
    (tmp_path / "work").mkdir()
    work = tmp_path / "work"
    target = work / "evidence"
    target.mkdir()
    for path in evidence_folder.iterdir():
        (target / path.name).write_bytes(path.read_bytes())
    assert _uofa("keygen", "demo.key", cwd=work).returncode == 0
    return work


def test_evidence_folder_to_signed_package(workspace):
    seal = _uofa("evidence", "seal", "evidence", "-o", "evidence.json",
                 cwd=workspace)
    assert seal.returncode == 0, seal.stderr

    extract = _uofa("extract", "evidence", "--keyless", "--pack", "vv40",
                    "-o", "extracted.xlsx", cwd=workspace)
    assert extract.returncode == 0, extract.stderr
    # The hand-off must name the sidecar step when solver artifacts were read.
    assert "--evidence evidence.json" in extract.stdout

    _adjudicate(workspace / "extracted.xlsx", workspace / "reviewed.xlsx")

    imported = _uofa("import", "reviewed.xlsx", "--evidence", "evidence.json",
                     "-o", "pkg.jsonld", "--sign", "--key", "demo.key",
                     cwd=workspace)
    assert imported.returncode == 0, imported.stderr

    doc = json.loads((workspace / "pkg.jsonld").read_text())
    assert doc["artifactManifest"], "the seal must reach the package"
    assert {a["name"] for a in doc["absentArtifact"]} == {
        "ds.dat", "file.rst", "solve.out"}

    verified = _uofa("verify", "pkg.jsonld", "--pubkey", "demo.pub",
                     cwd=workspace)
    assert verified.returncode == 0, verified.stdout


def test_tampering_with_a_sealed_digest_breaks_the_signature(workspace):
    """Proves the fold happens BEFORE hashing.

    If the manifest were merely written alongside the package, editing a digest
    would leave the signature intact -- and the seal would be decoration.
    """
    _uofa("evidence", "seal", "evidence", "-o", "evidence.json", cwd=workspace)
    _uofa("extract", "evidence", "--keyless", "--pack", "vv40",
          "-o", "extracted.xlsx", cwd=workspace)
    _adjudicate(workspace / "extracted.xlsx", workspace / "reviewed.xlsx")
    _uofa("import", "reviewed.xlsx", "--evidence", "evidence.json",
          "-o", "pkg.jsonld", "--sign", "--key", "demo.key", cwd=workspace)
    assert _uofa("verify", "pkg.jsonld", "--pubkey", "demo.pub",
                 cwd=workspace).returncode == 0

    doc = json.loads((workspace / "pkg.jsonld").read_text())
    doc["artifactManifest"][0]["sha256"] = "sha256:" + "0" * 64
    (workspace / "tampered.jsonld").write_text(json.dumps(doc, indent=2,
                                                          sort_keys=True))
    assert _uofa("verify", "tampered.jsonld", "--pubkey", "demo.pub",
                 cwd=workspace).returncode != 0


def test_the_evidence_fold_adds_no_shacl_violations(workspace):
    """packs/core/shapes/uofa_shacl.ttl declares no `sh:closed` shape, so the
    undeclared evidence terms should pass C2 untouched. Asserted rather than
    assumed, because closing a shape later would break this quietly."""
    _uofa("evidence", "seal", "evidence", "-o", "evidence.json", cwd=workspace)
    _uofa("extract", "evidence", "--keyless", "--pack", "vv40",
          "-o", "extracted.xlsx", cwd=workspace)
    _adjudicate(workspace / "extracted.xlsx", workspace / "reviewed.xlsx")
    _uofa("import", "reviewed.xlsx", "--evidence", "evidence.json",
          "-o", "sealed.jsonld", "--sign", "--key", "demo.key", cwd=workspace)
    _uofa("import", "reviewed.xlsx", "-o", "plain.jsonld", "--sign",
          "--key", "demo.key", cwd=workspace)

    sealed = _uofa("shacl", "sealed.jsonld", cwd=workspace).stdout
    plain = _uofa("shacl", "plain.jsonld", cwd=workspace).stdout
    assert _violations(sealed) == _violations(plain)
    for term in ("artifactManifest", "solverFact", "absentArtifact"):
        assert term not in sealed


def test_import_rejects_a_document_that_is_not_a_sidecar(workspace):
    (workspace / "not-a-sidecar.json").write_text('{"schemaVersion": "other/v1"}')
    _uofa("extract", "evidence", "--keyless", "--pack", "vv40",
          "-o", "extracted.xlsx", cwd=workspace)
    _adjudicate(workspace / "extracted.xlsx", workspace / "reviewed.xlsx")
    result = _uofa("import", "reviewed.xlsx", "--evidence", "not-a-sidecar.json",
                   "-o", "pkg.jsonld", cwd=workspace)
    assert result.returncode != 0
    assert "not an evidence sidecar" in (result.stdout + result.stderr)


def _violations(text: str) -> str:
    import re
    found = re.search(r"(\d+) violation", text)
    return found.group(1) if found else "0"


def _adjudicate(src, dest):
    """Stand in for the human review step: fill only what import requires."""
    openpyxl = pytest.importorskip("openpyxl")
    book = openpyxl.load_workbook(src)
    book["Assessment Summary"]["B3"] = "F1717 compression-bending, non-cannulated"
    book["Decision"]["A3"] = "Accepted"
    book.save(dest)


def test_evidence_fold_survives_the_protocol_check_gate(workspace):
    """The two flags are independent and must compose.

    `--evidence` and `--protocol-check` were added on separate branches and met
    for the first time in a merge, so neither side's tests covered the pair. The
    gate exits non-zero on an unreviewed workbook by design; what matters here is
    that it fails for ITS OWN reasons (anchors, logs, namespace) and that the
    evidence fold still lands in the signed package underneath it.
    """
    _uofa("evidence", "seal", "evidence", "-o", "evidence.json", cwd=workspace)
    _uofa("extract", "evidence", "--keyless", "--pack", "vv40",
          "-o", "extracted.xlsx", cwd=workspace)
    _adjudicate(workspace / "extracted.xlsx", workspace / "reviewed.xlsx")

    gated = _uofa("import", "reviewed.xlsx", "--evidence", "evidence.json",
                  "--protocol-check", "-o", "gated.jsonld", "--sign",
                  "--key", "demo.key", cwd=workspace)
    assert gated.returncode != 0, "the gate must fail an unreviewed workbook"

    # It failed on its own checks, not on anything the evidence fold added.
    # Scope this to the protocol-check section: the fold prints its own progress
    # line ("Evidence sidecar folded in: 2 artifactManifest, ...") earlier in the
    # same stream, so a whole-stdout search finds that and proves nothing.
    section = gated.stdout[gated.stdout.index("protocol-check:"):]
    for term in ("artifactManifest", "solverFact", "absentArtifact",
                 "corroboration", "sourcePin"):
        assert term not in section, f"the gate is objecting to {term}"

    # And the fold still reached the signed package.
    doc = json.loads((workspace / "gated.jsonld").read_text())
    assert doc["artifactManifest"]
    assert doc["signature"].startswith("ed25519:")

    ungated = _uofa("import", "reviewed.xlsx", "--evidence", "evidence.json",
                    "-o", "plain.jsonld", "--sign", "--key", "demo.key",
                    cwd=workspace)
    assert ungated.returncode == 0, "without the gate the same import succeeds"

"""Sealing an evidence folder: digests, honest blanks, and pins.

The claim under test is the one the demo makes before any extractor runs --
integrity, provenance and completeness established over proprietary archives
without the software that wrote them.
"""

from __future__ import annotations

import json
import zipfile

import pytest

from uofa_cli.furnishers import pins
from uofa_cli.solver import detect, seal as sealmod

FETCHED = "2026-08-20T00:00:00Z"


def test_seals_every_file_and_every_member(evidence_folder):
    seal = sealmod.seal_folder(evidence_folder)
    assert seal.n_files == 2                      # mini.wbpz + notes.txt
    assert seal.n_members > 8
    for art in seal.artifacts:
        assert art.sha256.startswith("sha256:")
        for m in art.members:
            assert m.sha256.startswith("sha256:")


def test_unread_artifacts_carry_a_reason(evidence_folder):
    """The honest-blank contract applied to bytes.

    A `.mechdb` we cannot parse is a legitimate outcome; a `.mechdb` that is
    silently absent from the manifest is a misrepresentation of the package.
    """
    seal = sealmod.seal_folder(evidence_folder)
    unread = [m for a in seal.artifacts for m in a.members if not m.read]
    assert unread, "the fixture carries binaries with no reader"
    for m in unread:
        assert m.reason, f"{m.path} sealed unread with no reason"
    kinds = {m.kind for m in unread}
    assert detect.MECHANICAL_DB in kinds
    assert detect.HDF5_CONTAINER in kinds


def test_no_pins_without_a_source_map(evidence_folder):
    """Re-derivability is only claimed when a real URL was supplied.

    Deriving a per-file link from a collection URL would produce a pin that
    404s, turning a re-derivation claim into a dead end.
    """
    seal = sealmod.seal_folder(evidence_folder)
    assert seal.source_pins == []
    assert any("no source pins" in line for line in sealmod.summarise(seal))


def test_source_map_produces_re_derivable_pins(evidence_folder):
    seal = sealmod.seal_folder(
        evidence_folder,
        source_map={"mini.wbpz": "https://osf.io/n4pjz/files/osfstorage/EXAMPLE"},
        fetched_at=FETCHED)
    assert len(seal.source_pins) == 1
    pin = seal.source_pins[0]
    assert pin["pinType"] == "artifact"
    assert pin["supports"] == "re-derivation"
    assert pin["fetchedAt"] == FETCHED
    archive_art = next(a for a in seal.artifacts if a.path == "mini.wbpz")
    assert pin["contentHash"] == archive_art.sha256
    assert pins.re_derivable({"sourcePin": seal.source_pins})


def test_unmatched_source_map_is_reported(evidence_folder):
    seal = sealmod.seal_folder(evidence_folder,
                               source_map={"nothing.wbpz": "https://example.invalid/x"})
    assert any("matched no file" in w for w in seal.warnings)


def test_bundle_fields_use_camelcase_and_add_no_context_terms(evidence_folder):
    """These keys ride `@vocab` into `uofa:<term>`.

    A snake_case key would mint `uofa:empty_dirs` beside `uofa:sourcePin` and
    read as if a different author wrote it; and nothing here may be added to
    spec/context/v0.5.jsonld, which is inlined into the hash preimage.
    """
    seal = sealmod.seal_folder(
        evidence_folder, source_map={"mini.wbpz": "https://example.invalid/x"},
        fetched_at=FETCHED)
    fields = sealmod.bundle_fields(seal)
    assert set(fields) == {"artifactManifest", "sourcePin"}
    for art in fields["artifactManifest"]:
        for key in art:
            assert "_" not in key, f"{key} is not camelCase"
            for member in art.get("members", []):
                assert all("_" not in k for k in member)


def test_sidecar_round_trips(evidence_folder, tmp_path):
    seal = sealmod.seal_folder(evidence_folder, fetched_at=FETCHED)
    out = tmp_path / "evidence.json"
    sealmod.write_sidecar(seal, out)
    doc = json.loads(out.read_text())
    assert doc["schemaVersion"] == sealmod.SIDECAR_SCHEMA
    assert len(doc["artifactManifest"]) == seal.n_files


def test_tampering_with_one_member_changes_only_its_digest(evidence_folder):
    """Make the check fail once, on purpose (AGENTS.md §13).

    A seal nobody has watched fail is a seal nobody knows works. Flip a byte in
    one member and the manifest must name that member and no other.
    """
    before = sealmod.seal_folder(evidence_folder)
    wbpz = evidence_folder / "mini.wbpz"

    target = "mini_files/user_files/DesignPointLog.csv"
    with zipfile.ZipFile(wbpz) as z:
        contents = {n: z.read(n) for n in z.namelist() if not n.endswith("/")}
        dirs = [n for n in z.namelist() if n.endswith("/")]
    contents[target] = contents[target].replace(b"967479362", b"967479363")
    with zipfile.ZipFile(wbpz, "w", zipfile.ZIP_DEFLATED) as z:
        for d in dirs:
            z.writestr(d, b"")
        for name, body in contents.items():
            z.writestr(name, body)

    after = sealmod.seal_folder(evidence_folder)
    b = {m.path: m.sha256 for a in before.artifacts for m in a.members}
    a = {m.path: m.sha256 for art in after.artifacts for m in art.members}
    changed = {k for k in b if b[k] != a.get(k)}
    assert changed == {target}
    # And the archive's own digest moves, so the OSF pin would no longer verify.
    assert (next(x for x in before.artifacts if x.path == "mini.wbpz").sha256
            != next(x for x in after.artifacts if x.path == "mini.wbpz").sha256)


def test_seal_needs_no_optional_dependency(evidence_folder, monkeypatch):
    """Run the check with the thing removed (AGENTS.md §13).

    The seal path is stdlib-only by design; if it ever grows an import of an
    optional extra this fails rather than degrading in the field.
    """
    import builtins
    blocked = {"ansys", "pdfplumber", "openpyxl", "litellm", "chardet"}
    real_import = builtins.__import__

    def guard(name, *a, **kw):
        if name.split(".")[0] in blocked:
            raise ImportError(f"{name} blocked by test")
        return real_import(name, *a, **kw)

    monkeypatch.setattr(builtins, "__import__", guard)
    seal = sealmod.seal_folder(evidence_folder)
    assert seal.n_files == 2

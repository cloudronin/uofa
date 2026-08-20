"""Archive traversal: streaming, and the guards on untrusted input.

An evidence archive is untrusted even when it comes from a journal's
supplementary material, and the one in the real folder is 405 MB, so neither
"trust the central directory" nor "extract it and walk that" is available.
"""

from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from uofa_cli.solver import archive, detect


def test_scan_classifies_the_whole_tree(mini_wbpz):
    scan = archive.scan(mini_wbpz)
    assert scan.kind == detect.WORKBENCH_ARCHIVE
    kinds = {m.name: m.kind for m in scan.members if not m.is_dir}
    assert kinds["mini.wbpj"] == detect.WORKBENCH_PROJECT
    assert kinds["mini_files/dp0/SYS/ENGD/EngineeringData.xml"] == detect.ENGINEERING_DATA
    assert kinds["mini_files/dp0/act.dat"] == detect.HDF5_CONTAINER
    assert kinds["mini_files/dp0/global/MECH/mini.mechdb"] == detect.MECHANICAL_DB
    assert kinds["mini_files/dp0/designPoint.wbdp"] == detect.DESIGN_POINT_TABLE
    assert kinds["mini_files/user_files/DesignPointLog.csv"] == detect.TABULAR
    assert kinds["mini_files/session_files/journal1.wbjn"] == detect.WORKBENCH_JOURNAL
    assert kinds["mini_files/dp0/global/MECH/console.hist"] == detect.EMPTY


def test_empty_solver_directory_is_reported(mini_wbpz):
    """An empty `MECH/` is how a results-stripped archive shows up structurally.

    It is a completeness fact, so it has to survive the walk rather than being
    dropped as an uninteresting directory entry.
    """
    scan = archive.scan(mini_wbpz)
    assert "mini_files/dp0/SYS/MECH/" in scan.empty_dirs


def test_every_member_is_digested(mini_wbpz):
    scan = archive.scan(mini_wbpz)
    files = [m for m in scan.members if not m.is_dir]
    assert files
    for m in files:
        assert m.sha256.startswith("sha256:") and len(m.sha256) == 71


def test_digest_matches_a_plain_read_of_the_member(mini_wbpz):
    """Streaming in chunks must give the same answer as reading it whole."""
    import hashlib
    scan = archive.scan(mini_wbpz)
    m = next(m for m in scan.members if m.name == "mini.wbpj")
    raw = archive.read_member(mini_wbpz, "mini.wbpj")
    assert m.sha256 == "sha256:" + hashlib.sha256(raw).hexdigest()


def test_build_is_reproducible(tmp_path):
    """Two builds of the same tree give byte-identical archives.

    Without this the fixture's own digest moves between runs and the seal tests
    can only assert shapes, never values.
    """
    from tests.solver.conftest import MINI, build_wbpz
    a = build_wbpz(MINI, tmp_path / "a.wbpz").read_bytes()
    b = build_wbpz(MINI, tmp_path / "b.wbpz").read_bytes()
    assert a == b


# ── guards ───────────────────────────────────────────────────


def _zip_with(tmp_path: Path, names_and_bodies) -> Path:
    p = tmp_path / "evil.zip"
    with zipfile.ZipFile(p, "w") as z:
        for name, body in names_and_bodies:
            z.writestr(name, body)
    return p


@pytest.mark.parametrize("evil", [
    "../../etc/passwd",
    "/etc/passwd",
    "C:\\Windows\\System32\\x.dll",
    "a/../../b",
])
def test_traversal_names_are_dropped_with_a_warning(tmp_path, evil):
    p = _zip_with(tmp_path, [(evil, b"x"), ("ok.txt", b"y")])
    scan = archive.scan(p)
    assert [m.name for m in scan.members if not m.is_dir] == ["ok.txt"]
    assert any("unsafe path" in w for w in scan.warnings)


def test_member_count_cap(tmp_path, monkeypatch):
    monkeypatch.setattr(archive, "MAX_MEMBERS", 3)
    p = _zip_with(tmp_path, [(f"f{i}.txt", b"x") for i in range(5)])
    with pytest.raises(archive.ArchiveRefused, match="over the"):
        archive.scan(p)


def test_declared_expansion_cap(tmp_path, monkeypatch):
    monkeypatch.setattr(archive, "MAX_TOTAL_UNCOMPRESSED", 100)
    p = _zip_with(tmp_path, [("big.txt", b"x" * 5000)])
    with pytest.raises(archive.ArchiveRefused, match="uncompressed bytes"):
        archive.scan(p)


def test_read_member_refuses_an_oversized_member(tmp_path, monkeypatch):
    monkeypatch.setattr(archive, "MAX_MEMBER_READ", 16)
    p = _zip_with(tmp_path, [("big.txt", b"x" * 1000)])
    with pytest.raises(archive.ArchiveRefused, match="read cap"):
        archive.read_member(p, "big.txt")


def test_nested_archives_are_recorded_not_descended(tmp_path):
    """Depth-1 keeps the walk bounded. A Workbench project has no legitimate
    reason to nest an archive, so one is reported and left alone."""
    inner = _zip_with(tmp_path, [("deep.txt", b"z")])
    p = tmp_path / "outer.zip"
    with zipfile.ZipFile(p, "w") as z:
        z.writestr("inner.zip", inner.read_bytes())
    scan = archive.scan(p)
    names = [m.name for m in scan.members if not m.is_dir]
    assert names == ["inner.zip"]
    assert scan.members[0].kind == detect.ZIP_ARCHIVE
    assert not scan.members[0].readable

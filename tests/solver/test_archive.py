"""Archive traversal: streaming, and the guards on untrusted input.

An evidence archive is untrusted even when it comes from a journal's
supplementary material, and the one in the real folder is 405 MB, so neither
"trust the central directory" nor "extract it and walk that" is available.
"""

from __future__ import annotations

import subprocess
import zipfile
from pathlib import Path

import pytest

from uofa_cli.solver import archive, detect

from tests.solver.conftest import MINI


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


def test_every_fixture_file_is_tracked_by_git():
    """The fixture on disk and the fixture in the repository must be the same set.

    Regression, and a nastier one than it looks. The tree was staged with
    `git add <dir>`, which skips ignored paths **without a word**, and the
    repository's global `*.log` rule matched
    `mini_files/user_files/optiSLang_protocol.log` -- the deliberately UTF-16LE
    file. The archive then built from 11 files on the author's machine and 10 in
    CI, so every local run passed and the pinned-digest test below failed on a
    fresh clone with a missing key.

    `.gitignore` now re-includes this tree, but a negation only ever protects
    the pattern someone remembered. This checks the property directly, so the
    next rule that swallows a fixture fails here with the filename rather than
    as a puzzling digest mismatch on somebody else's checkout.
    """
    repo = MINI.parents[3]
    if not (repo / ".git").exists():
        pytest.skip("not a git checkout")

    tracked = subprocess.run(
        ["git", "ls-files", "-z", "--", str(MINI.relative_to(repo))],
        cwd=repo, capture_output=True, text=True, check=True)
    on_disk = {p.relative_to(repo).as_posix() for p in MINI.rglob("*") if p.is_file()}
    in_git = {name for name in tracked.stdout.split("\0") if name}

    assert on_disk - in_git == set(), (
        "fixture file(s) present on disk but not tracked — a .gitignore rule is "
        "swallowing them and CI will build a different archive")
    assert in_git - on_disk == set(), "tracked fixture file(s) missing from disk"


def test_fixture_member_digests_are_pinned(mini_wbpz):
    """Guard the fixture's byte-exactness across checkouts.

    `.gitattributes` marks tests/fixtures/solver as `-text` so git never
    normalises it. Without that, `.project_cache` and `.skipped_files_on_archive`
    (CRLF on purpose, mirroring real Workbench output) and the UTF-16LE
    `optiSLang_protocol.log` are rewritten on checkout and every digest below
    moves -- silently, and only on someone else's machine.

    Member digests are pinned rather than the archive's own: deflate output can
    differ between zlib builds, but member *content* cannot.
    """
    scan = archive.scan(mini_wbpz)
    got = {m.name: m.sha256 for m in scan.members if not m.is_dir}
    assert got == {
        "mini.wbpj":
            "sha256:5e67f30276b1191998932107ec484e05f3c659acddcf928066858e2ac74e0235",
        "mini_files/.project_cache":
            "sha256:fd55da2014bb97644e8ca770b91c75eed2735480827c96d2a964587421bf43d4",
        "mini_files/.skipped_files_on_archive":
            "sha256:c251cba7efd5e859966eb638cfa9a60c0ee18475bb5ea4f23fa00431db2cf73b",
        "mini_files/dp0/SYS/ENGD/EngineeringData.xml":
            "sha256:3e7169e819128a8fe391a34d0f70bc666140a723ba7bbb3158f481c2184a2594",
        "mini_files/dp0/act.dat":
            "sha256:a84c51a01d2160760a8aa11b72f729e11d460d7cc9a8f80d70803ea13096632e",
        "mini_files/dp0/designPoint.wbdp":
            "sha256:ce7d0519b087da4d55cb7f82bbac3df4151ff5d1eb621095d40ed9310a50dbcc",
        "mini_files/dp0/global/MECH/console.hist":
            "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "mini_files/dp0/global/MECH/mini.mechdb":
            "sha256:2895e36e6ee8318551fffa8c2f1db99415b71bcc4b98b2676f26a7b3983dc098",
        "mini_files/session_files/journal1.wbjn":
            "sha256:c1e4898bb53e403d575412c1d86356238faaad6d0b7334a76af7a2e154470ae6",
        "mini_files/user_files/DesignPointLog.csv":
            "sha256:2a19a2c28152aab2cedf0e8c3577d96d852acf72d71e43f006acaa87b4dae669",
        "mini_files/user_files/optiSLang_protocol.log":
            "sha256:cf5895da91fa0fb471825d6b1f220606ae65de75cc6dfe07b12c45e75cf87986",
    }

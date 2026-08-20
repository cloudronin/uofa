"""Fixtures for the solver-artifact ingest tests.

The `.wbpz` is built from a committed file tree rather than committed as a
binary blob. Two reasons: a reviewer can read a diff of the tree and cannot read
a diff of a zip, and the empty `MECH/` directory that is the structural
signature of a results-stripped archive cannot be committed to git at all.
Directories to recreate are declared in `EMPTY_DIRS` beside the tree.

The build is deterministic -- fixed member timestamps, sorted names, stored
compression -- so the archive's own digest is stable across runs and machines.
"""

from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "solver"
MINI = FIXTURES / "mini_project"

# Any constant works; it just must not be "now", or the archive digest moves.
_FIXED_TIME = (2024, 11, 21, 9, 0, 0)


def build_wbpz(src: Path, dest: Path) -> Path:
    """Zip `src` to `dest` reproducibly, recreating declared empty directories."""
    files = sorted(p for p in src.rglob("*")
                   if p.is_file() and p.name != "EMPTY_DIRS")
    empty_dirs = []
    decl = src / "EMPTY_DIRS"
    if decl.exists():
        empty_dirs = [line.strip() for line in decl.read_text().splitlines()
                      if line.strip() and not line.startswith("#")]

    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as z:
        for name in empty_dirs:
            info = zipfile.ZipInfo(name, date_time=_FIXED_TIME)
            info.external_attr = 0o40755 << 16 | 0x10  # directory
            z.writestr(info, b"")
        for path in files:
            rel = path.relative_to(src).as_posix()
            info = zipfile.ZipInfo(rel, date_time=_FIXED_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, path.read_bytes())
    return dest


@pytest.fixture
def mini_wbpz(tmp_path: Path) -> Path:
    """A miniature Workbench archive, shaped like the real OSF ones."""
    return build_wbpz(MINI, tmp_path / "mini.wbpz")


@pytest.fixture
def evidence_folder(tmp_path: Path, mini_wbpz: Path) -> Path:
    """An evidence folder holding one archive and one loose document."""
    folder = tmp_path / "evidence"
    folder.mkdir()
    mini_wbpz.rename(folder / "mini.wbpz")
    (folder / "notes.txt").write_text("Study notes.\n", encoding="utf-8")
    return folder

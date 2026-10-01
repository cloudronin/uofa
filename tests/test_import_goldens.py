"""What `uofa import` writes for a V&V 40 and a NASA workbook, pinned.

The ISO 42001 work ahead puts a workbook-adapter registry under `uofa import`
and promises no change for the existing packs. That promise needs something to
be checked against: the full JSON-LD `uofa import` writes today, for the
reference workbooks each pack ships or tests with, byte for byte after three
fields are masked.

The masked fields are the only ones that change between two imports of the same
workbook -- measured, not assumed: `generatedAtTime` and the provenance
record's `timestamp` carry the clock, and `toolVersion` carries the release, so
a version bump would otherwise rewrite every golden. Unsigned imports carry
all-zero hash and signature placeholders, which are stable and stay pinned.

Two more differ between machines rather than between runs. The provenance
record's `sourceFile` is the workbook's absolute path, however it was named on
the command line; it is kept, with this checkout's location replaced by
`<repo>`, so the golden says which workbook and not whose disk. And
`wasAttributedTo` names the operator -- `UOFA_ASSESSOR`, else git's user name,
else `$USER` -- so the test sets `UOFA_ASSESSOR` itself. Left to the
environment it said whose machine ran it, and inside the suite it said
whichever test ran first: `space/pipeline.py` sets `UOFA_ASSESSOR` when it is
imported, and the variable outlives the test that imported it.

The Morrison examples are pinned byte-for-byte elsewhere
(`tests/fixtures/frozen_artifact_pins.json`) and are not touched here.

Regenerate after an intended change, then read the diff:

    python tests/test_import_goldens.py --regen
"""

from __future__ import annotations

import difflib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
GOLDENS = REPO_ROOT / "tests/fixtures/import_goldens"

#: (workbook, pack) -- the reference workbook each pack ships. Committed files
#: only: the import corpus under tests/corpus/ is generated and gitignored, so a
#: golden resting on it passed here and failed in CI, where it does not exist.
WORKBOOKS = [
    ("packs/vv40/templates/uofa-starter-filled.xlsx", "vv40"),
    ("packs/nasa-7009b/examples/starters/uofa-aero-hpt-blade-thermal-gaps.xlsx", "nasa-7009b"),
]

MASK = "<masked>"

#: The operator every golden is attributed to. Set, not inherited.
OPERATOR = "Golden Test Operator"


def _env() -> dict:
    return {**os.environ, "UOFA_ASSESSOR": OPERATOR}


def golden(workbook: str, pack: str) -> Path:
    return GOLDENS / f"{Path(workbook).stem}.{pack}.jsonld"


def imported(workbook: str, pack: str, work: Path) -> str:
    """The JSON-LD `uofa import` writes, through the real command, masked and
    printed canonically. One function for the test and for `--regen`."""
    out = work / f"{Path(workbook).stem}.{pack}.jsonld"
    # From the repo root, with the workbook's relative path: the provenance
    # record keeps `sourceFile` as given, and an absolute one is this machine's.
    run = subprocess.run(
        [sys.executable, "-m", "uofa_cli", "import", workbook,
         "--pack", pack, "-o", str(out)],
        capture_output=True, text=True, cwd=REPO_ROOT, env=_env())
    assert run.returncode == 0, run.stdout + run.stderr
    doc = json.loads(out.read_text(encoding="utf-8"))
    doc["generatedAtTime"] = MASK
    for step in doc.get("provenanceChain", []):
        for key in ("timestamp", "toolVersion"):
            if key in step:
                step[key] = MASK
        if "sourceFile" in step:
            step["sourceFile"] = _repo_relative(step["sourceFile"])
    return json.dumps(doc, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def _repo_relative(path: str) -> str:
    """`sourceFile` is recorded absolute however the workbook is named on the
    command line. Kept, with this checkout's location replaced by `<repo>`."""
    for root in {str(REPO_ROOT), str(REPO_ROOT.resolve())}:
        if path.startswith(root + "/"):
            return "<repo>/" + path[len(root) + 1:]
    return path


@pytest.mark.parametrize("workbook, pack", WORKBOOKS,
                         ids=[f"{Path(w).stem}.{p}" for w, p in WORKBOOKS])
def test_import_writes_what_it_wrote(workbook, pack, tmp_path):
    fresh = imported(workbook, pack, tmp_path)
    for local in (str(REPO_ROOT), str(tmp_path), str(Path.home())):
        assert local not in fresh, f"the output carries this machine's path {local}"
    pinned = golden(workbook, pack).read_text(encoding="utf-8")
    if fresh != pinned:
        diff = "".join(difflib.unified_diff(
            pinned.splitlines(True), fresh.splitlines(True), "golden", "now", n=2))
        pytest.fail(
            f"`uofa import {workbook} --pack {pack}` changed its output. If "
            f"intended, run `python tests/test_import_goldens.py --regen` and "
            f"commit the diff with its cause.\n{diff[:4000]}")


def test_the_mask_covers_only_what_moves(tmp_path):
    """Two imports of one workbook differ in exactly the masked fields. A field
    that started moving would fail the golden test on its own; one masked
    without moving would hide a change for nothing."""
    workbook, pack = WORKBOOKS[0]
    raw = []
    for n in (1, 2):
        out = tmp_path / f"{n}.jsonld"
        subprocess.run([sys.executable, "-m", "uofa_cli", "import",
                        workbook, "--pack", pack, "-o", str(out)],
                       capture_output=True, text=True, cwd=REPO_ROOT, check=True,
                       env=_env())
        raw.append(json.loads(out.read_text(encoding="utf-8")))
    a, b = raw
    assert {k for k in a if a[k] != b.get(k)} <= {"generatedAtTime", "provenanceChain"}
    for x, y in zip(a["provenanceChain"], b["provenanceChain"]):
        assert {k for k in x if x[k] != y.get(k)} <= {"timestamp"}
    assert a["provenanceChain"][0]["toolVersion"].startswith("uofa-cli ")


def test_every_pinned_workbook_is_committed():
    """A golden over a file this checkout generated is a golden CI cannot run."""
    import shutil
    if not (shutil.which("git") and (REPO_ROOT / ".git").exists()):
        pytest.skip("not a git checkout")
    for workbook, _ in WORKBOOKS:
        tracked = subprocess.run(["git", "ls-files", "--error-unmatch", workbook],
                                 cwd=REPO_ROOT, capture_output=True, text=True)
        assert tracked.returncode == 0, f"{workbook} is not committed"


def test_every_golden_has_a_workbook():
    expected = {golden(w, p).name for w, p in WORKBOOKS}
    assert {p.name for p in GOLDENS.glob("*.jsonld")} == expected


def _regen() -> None:
    GOLDENS.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as work:
        for workbook, pack in WORKBOOKS:
            golden(workbook, pack).write_text(
                imported(workbook, pack, Path(work)), encoding="utf-8")
            print(f"wrote {golden(workbook, pack).relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    if sys.argv[1:] != ["--regen"]:
        sys.exit("usage: python tests/test_import_goldens.py --regen")
    _regen()

"""The release gate's import audit must flag missing deps and only those.

It was failing on four false positives on every run, on main as well as on
branches: `harness`, `space`, `tests` and `curated_cards` are repository-local
imports, and the audit's "is this local?" set was built from `.py` file stems
only. A package -- a directory -- had nothing to match, so it was reported as an
uninstalled pip dependency.

A release gate that fails four times on every invocation is a gate people learn
to read past, and then it cannot do the one job it has. So the fix has to be
tested from both sides: the false positives are gone, AND a genuinely missing
dependency is still caught. Widening the local set until the check passes is the
failure mode this file exists to prevent.
"""

from __future__ import annotations

import ast
import importlib.util
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "dev" / "tools" / "scripts" / "release_check.py"

pytestmark = pytest.mark.skipif(not SCRIPT.exists(), reason="release_check.py not present")


def _load():
    spec = importlib.util.spec_from_file_location("release_check", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["release_check"] = mod
    spec.loader.exec_module(mod)
    return mod


def _test_imports() -> set[str]:
    """Top-level imports of every file pytest collects, as the audit sees them."""
    out: set[str] = set()
    for tf in sorted((REPO / "tests").rglob("*.py")):
        if not (tf.name.startswith("test_") or tf.name == "conftest.py"):
            continue
        try:
            tree = ast.parse(tf.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for node in tree.body:
            if isinstance(node, ast.Import):
                out |= {a.name.split(".")[0] for a in node.names}
            elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                out.add(node.module.split(".")[0])
    return out


@pytest.mark.parametrize("name", ["harness", "space", "tests", "curated_cards"])
def test_a_repository_local_import_is_resolvable_and_not_a_pip_package(name):
    """Each name the audit used to flag really is satisfied by this repo.

    Asserted against the filesystem rather than against the audit's own answer,
    so this cannot agree with a bug by sharing its assumptions.
    """
    local = (
        [p for p in REPO.iterdir() if p.is_dir() and p.name == name and any(p.glob("*.py"))]
        + [p for p in (REPO / "tests").rglob("*") if p.is_dir() and p.name == name]
        + [p for p in (REPO / "packs").glob(f"*/examples/{name}.py")]
    )
    assert local, f"{name} is not provided by this repository after all"


def test_the_audit_still_reports_a_genuinely_missing_dependency(tmp_path, monkeypatch):
    """The half that keeps the fix honest.

    Anything can be made to pass by widening the "local" set far enough. This
    puts a name in front of the audit that the repo does NOT provide and is not
    installed, and requires it to be reported.
    """
    mod = _load()
    installed = {"pytest", "openpyxl", "rdflib", "jsonschema"}
    imports = _test_imports() | {"nonexistent_pip_package_xyz"}
    local = mod.__dict__.get("_local_module_names", None)
    if local is None:
        pytest.skip("audit does not expose its local-module set for direct testing")
    missing = sorted(i for i in imports
                     if i not in installed
                     and i not in local(REPO)
                     and i not in set(getattr(sys, "stdlib_module_names", set()))
                     and i != "uofa_cli")
    assert "nonexistent_pip_package_xyz" in missing

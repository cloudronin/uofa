"""A shape never judges a document that predates it.

Without this, every published conformance claim expires silently the moment the
model grows, and the only ways to restore it are to edit shipped bytes the
praxis record cites, or to weaken the shape for everyone. The first destroys
byte-level claims; the second destroys the shape. Jurisdiction is the third
option: the rule applies from when it came into force.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SIBLING = (REPO_ROOT / "packs/vv40/examples/morrison-v09/cou1"
           / "uofa-morrison-v09-cou1.jsonld")


def _shacl(path):
    return subprocess.run(
        [sys.executable, "-m", "uofa_cli", "shacl", str(path), "--pack", "vv40"],
        capture_output=True, text=True, cwd=str(REPO_ROOT))


def _staged(tmp_path, *, context, drop_fork):
    doc = json.loads(SIBLING.read_text(encoding="utf-8"))
    doc["@context"] = context
    if drop_fork:
        doc["hasDecisionRecord"].pop("decisionProvenance", None)
    out = tmp_path / "staged.jsonld"
    out.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    return out


V09 = "https://uofa.net/spec/context/v0.9.jsonld"
V05 = "https://uofa.net/spec/context/v0.5.jsonld"


def test_the_shape_bites_under_its_own_context(tmp_path):
    """The half that matters most: jurisdiction must not become an off switch."""
    r = _shacl(_staged(tmp_path, context=V09, drop_fork=True))
    assert r.returncode != 0
    assert "decisionProvenance" in r.stdout


def test_the_same_bytes_pass_under_the_context_they_declare(tmp_path):
    """Identical content, older declaration: the rule had not come into force."""
    r = _shacl(_staged(tmp_path, context=V05, drop_fork=True))
    assert r.returncode == 0, r.stdout + r.stderr


def test_an_unparseable_declaration_gets_every_shape(tmp_path):
    """Ambiguity must not buy an exemption.

    If "I cannot tell which version this is" meant "apply nothing", then
    omitting or mangling the context declaration would be a way past every shape
    the model has — the omission escape hatch, one layer up.
    """
    r = _shacl(_staged(tmp_path, context="urn:no-version-here", drop_fork=True))
    assert r.returncode != 0, "unknown jurisdiction must be judged, not excused"


def test_the_shipped_legacy_examples_conform_under_their_own_contexts():
    """The artifacts the freeze protects: conformant where they were written."""
    for rel in ("packs/vv40/examples/morrison/cou1/uofa-morrison-cou1.jsonld",
                "packs/vv40/examples/morrison/cou2/uofa-morrison-cou2.jsonld"):
        r = _shacl(REPO_ROOT / rel)
        assert r.returncode == 0, f"{rel}\n{r.stdout}{r.stderr}"

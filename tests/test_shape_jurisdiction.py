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


# ─────────────────────────────────────────────────────────────────────────────
# The other bound.
#
# `introducedIn` can only widen a rule's reach forward, which is enough until a
# CLOSED set grows. The day `not-recoverable` entered at v0.9, the shape
# enumerating that set had exactly the two options this module's docstring
# rejects: widen the published list, so v0.8 documents start accepting a term
# v0.8 cannot mean; or leave it, so v0.9 documents are refused for using v0.9's
# own vocabulary. `retiredIn` is the third option, and it is the same one --
# the rule applies until the rule that replaced it came into force.
# ─────────────────────────────────────────────────────────────────────────────

def _with_token(tmp_path, context, token, name):
    doc = json.loads(SIBLING.read_text(encoding="utf-8"))
    doc["@context"] = context
    for factor in doc.get("hasCredibilityFactor", []):
        if isinstance(factor, dict) and factor.get("requiredLevel") is not None:
            factor["requiredLevelProvenance"] = token
    out = tmp_path / name
    out.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    return out


V08 = "https://uofa.net/spec/context/v0.8.jsonld"


def test_v0_8_keeps_the_vocabulary_it_was_published_with(tmp_path):
    """A retired shape does not stop judging the documents it had jurisdiction
    over. If it did, retirement would be deletion and every v0.8 conformance
    claim would quietly widen."""
    r = _shacl(_with_token(tmp_path, V08, "not-recoverable", "v08.jsonld"))
    assert r.returncode != 0
    assert "requiredLevelProvenance must be one of" in r.stdout
    assert "not-recoverable" not in r.stdout.split("must be one of")[1][:200], (
        "v0.8's message offered a term v0.8 cannot mean")


def test_the_same_token_is_lawful_under_the_version_that_introduced_it(tmp_path):
    """And the retired shape must not reach it -- that is the whole point."""
    r = _shacl(_with_token(tmp_path, V09, "not-recoverable", "v09.jsonld"))
    assert "requiredLevelProvenance must be one of" not in r.stdout, r.stdout[:600]


def test_retirement_is_exclusive_of_its_own_version():
    """A shape retired IN v0.9 was in force through v0.8 and is silent from v0.9.

    Off by one here is not cosmetic: inclusive retirement would silence the rule
    for the last version it actually governed.
    """
    from rdflib import Graph, Literal, URIRef

    from uofa_cli.shacl_friendly import _UOFA_NS, _apply_jurisdiction

    def _survives(declared):
        g = Graph()
        shape = URIRef("urn:shape:retired")
        g.add((shape, URIRef(_UOFA_NS + "retiredIn"), Literal("v0.9")))
        g.add((shape, URIRef("urn:p"), Literal("x")))

        class _Doc:
            pass

        import json as _json
        import tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".jsonld", delete=False) as fh:
            fh.write(_json.dumps({"@context": f"https://uofa.net/spec/context/{declared}.jsonld"}))
            path = fh.name
        _apply_jurisdiction(g, path)
        return (shape, URIRef("urn:p"), Literal("x")) in g

    assert _survives("v0.8"), "the rule was silenced for a version it governed"
    assert not _survives("v0.9"), "the rule outlived the rule that replaced it"
    assert not _survives("v1.0")

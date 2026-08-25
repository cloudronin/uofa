"""Validation resolves the context the DOCUMENT declares, not the toolchain's.

The rule was already ruled correct in this repo for hashing -- `resolve_context`
prefers the document's own `@context`, after a toolchain-default preference
re-hashed five shipped packages. Validation never got the same rule: `rules`,
`diff` and `mutation` each passed `paths.context_file()`, hardcoded at v0.5.

Two consequences, in opposite directions:

- a **v0.8** package was expanded against v0.5, so the rules engine could not
  see `requiredLevelProvenance` at all -- the terms it was being asked to check
  were simply absent from its vocabulary;
- a **v0.5** package validated against a newer context loses the fourteen terms
  v0.7 removed, and their absence reports as violations of the document rather
  than of the substitution.

Both vanish when the document picks its own context. The fallback is computed
from what the checkout ships rather than written down, because a hardcoded v0.8
here is the same bug as the hardcoded v0.5 it replaces, one version later.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from uofa_cli import integrity, paths

REPO = Path(__file__).resolve().parents[1]
CTX = REPO / "spec" / "context"
BASE = "https://raw.githubusercontent.com/cloudronin/uofa/main/spec/context/"


def _terms(path: Path) -> set:
    return set(json.loads(path.read_text(encoding="utf-8"))["@context"])


def test_the_fallback_is_the_newest_context_shipped_not_a_written_down_one():
    newest = max((p for p in CTX.glob("v*.jsonld")),
                 key=lambda p: tuple(int(d) for d in __import__("re").findall(r"\d+", p.name)))
    assert paths.latest_context_file() == newest
    assert paths.latest_context_file() != paths.context_file(), (
        "validation and signing must not share a default: moving the signing "
        "default re-hashes every document that reaches it")


def test_a_v0_5_document_keeps_the_terms_v0_7_removed():
    """The direction that punishes age. Fourteen terms left the vocabulary at
    v0.7; a v0.5 document validated against a newer context loses all fourteen
    and reports their absence as its own fault."""
    path, note = integrity.context_for_document({"@context": BASE + "v0.5.jsonld"})
    assert path.name == "v0.5.jsonld"
    assert note == "", "a resolvable declaration needs no fallback note"

    dropped = _terms(CTX / "v0.5.jsonld") - _terms(paths.latest_context_file())
    assert dropped, "v0.5 and the newest context are identical; this test is vacuous"
    assert dropped <= _terms(path), (
        "the document was resolved to a context missing terms it was written "
        f"with: {sorted(dropped)[:4]}")


def test_a_v0_8_document_resolves_to_a_context_defining_its_own_terms():
    path, note = integrity.context_for_document({"@context": BASE + "v0.8.jsonld"})
    assert note == ""
    assert {"requiredLevelProvenance", "hasLevelAffirmation"} <= _terms(path), (
        "the rules engine would expand this package against a vocabulary that "
        "does not define the terms it is being asked to validate")


@pytest.mark.parametrize("doc,fragment", [
    ({"id": "x"}, "no context declared"),
    ({"@context": {"uofa": "https://example.org/"}}, "inlines its context"),
    ({"@context": BASE + "v9.9.jsonld"}, "not resolvable in this checkout"),
])
def test_every_fallback_is_named_never_silent(doc, fragment):
    """A validation run that quietly substitutes a vocabulary is how this class
    of bug survives: the output looks like a clean run against the file you
    named. Each fallback says which context it used and why."""
    path, note = integrity.context_for_document(doc)
    assert path == paths.latest_context_file()
    assert fragment in note
    assert path.name in note, "the note must name the context actually used"


def test_a_relative_reference_beside_the_document_wins(tmp_path):
    """Same order `resolve_context` uses: a path relative to the document is the
    most specific answer available and is preferred over URL mapping."""
    (tmp_path / "local.jsonld").write_text(json.dumps({"@context": {"x": "http://x/"}}))
    doc = tmp_path / "d.jsonld"
    doc.write_text(json.dumps({"@context": "local.jsonld"}))
    path, note = integrity.context_for_file(doc)
    assert path == tmp_path / "local.jsonld"
    assert note == ""


def test_an_unreadable_document_falls_back_and_says_so(tmp_path):
    """Unreadable is not empty -- it takes the fallback with a note, never a
    silent default that looks like a successful resolution."""
    bad = tmp_path / "broken.jsonld"
    bad.write_text("{not json")
    path, note = integrity.context_for_file(bad)
    assert path == paths.latest_context_file()
    assert "could not read" in note

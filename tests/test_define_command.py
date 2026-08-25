"""``uofa define`` answers for every term a user can collide with.

The gate the plan set: every one of the constrained property names resolves
without a miss, and a term the current context dropped says so rather than
reporting "not found" -- its IRI is live and packages pinned to an older context
still carry it.
"""

from __future__ import annotations

import json

import pytest

from uofa_cli import paths, vocab
from uofa_cli.commands import define

rdflib = pytest.importorskip("rdflib")
from rdflib import Graph, URIRef  # noqa: E402
from rdflib.namespace import SH  # noqa: E402


class _Args:
    def __init__(self, **kw):
        self.term = kw.get("term")
        self.search = kw.get("search")
        self.list_terms = kw.get("list_terms", False)
        self.all_packs = kw.get("all_packs", False)
        self.format = kw.get("format", "text")
        self.active_packs = kw.get("active_packs")


def _all_packs() -> list[str]:
    return [p for p in paths.list_packs(paths.find_repo_root()) if p != "core"]


def _constrained_names() -> list[str]:
    files = paths.all_shacl_schemas(paths.find_repo_root(), active=_all_packs())
    g = Graph()
    for f in files:
        g.parse(str(f), format="turtle")
    return sorted({
        str(o).rsplit("#", 1)[-1].rsplit("/", 1)[-1]
        for o in g.objects(None, SH.path) if isinstance(o, URIRef)
    })


def test_every_constrained_property_resolves(capsys):
    """No misses across the full set a violation can name."""
    names = _constrained_names()
    assert len(names) > 100, "expected the full constrained set"

    missed = []
    for name in names:
        rc = define.run(_Args(term=name, all_packs=True, format="json"))
        capsys.readouterr()
        if rc != 0:
            missed.append(name)
    assert not missed, f"uofa define could not resolve: {missed}"


def test_dropped_term_resolves_and_says_it_is_not_current(capsys):
    rc = define.run(_Args(term="reviewDate", all_packs=True))
    out = capsys.readouterr().out
    assert rc == 0, "a dropped term must resolve, not 404"
    assert "not in the current context" in out
    assert "v0.4" in out and "v0.6" in out, "should name the range it was live for"


def test_undefined_term_says_so_rather_than_printing_nothing(capsys):
    """A miss and an undefined term look identical to a user unless we say."""
    rc = define.run(_Args(term="reviewDate", all_packs=True))
    out = capsys.readouterr().out
    assert rc == 0
    assert "no definition" in out.lower()


def test_deprecated_term_is_marked(capsys):
    rc = define.run(_Args(term="frameworkTransfers", all_packs=True))
    out = capsys.readouterr().out
    assert rc == 0
    assert "deprecated" in out
    # Added and removed inside one version: read as (v0.6), not (v0.6 to v0.6).
    assert "v0.6 to v0.6" not in out


def test_unknown_term_fails_and_suggests_a_next_step(capsys):
    rc = define.run(_Args(term="hasContextOfUze", all_packs=True))
    out = capsys.readouterr().out
    assert rc == 1
    assert "--search" in out


def test_term_outside_the_active_packs_is_found_and_flagged(capsys):
    """An aims term is real even when the invocation loaded only vv40."""
    rc = define.run(_Args(term="auditDate", active_packs=["vv40"]))
    out = capsys.readouterr().out
    assert rc == 0
    assert "iso42001" in out
    assert "active pack set" in out


def test_json_output_is_machine_readable(capsys):
    define.run(_Args(term="hasContextOfUse", all_packs=True, format="json"))
    payload = json.loads(capsys.readouterr().out)
    assert payload["iri"].endswith("#hasContextOfUse")
    assert payload["definition"]
    assert payload["domain"].endswith("#UnitOfAssurance")


def test_definitions_come_from_the_graph_not_a_copy(capsys):
    """The command must not grow its own definitions.

    Same guard as the violation path: compare against the index, which reads
    the shapes, so a hardcoded string in this module would fail.
    """
    define.run(_Args(term="hasContextOfUse", all_packs=True, format="json"))
    payload = json.loads(capsys.readouterr().out)
    term = vocab.lookup("hasContextOfUse", all_packs=True)
    assert payload["definition"] == term.comment


def test_search_matches_labels_and_definitions(capsys):
    rc = define.run(_Args(search="context of use", all_packs=True, format="json"))
    hits = json.loads(capsys.readouterr().out)
    assert rc == 0 and hits
    names = {h["name"] for h in hits}
    assert "ContextOfUse" in names

    rc = define.run(_Args(search="zzzz-no-such-text", all_packs=True))
    capsys.readouterr()
    assert rc == 1


def test_list_scope_follows_the_pack_set(capsys):
    define.run(_Args(list_terms=True, active_packs=["vv40"], format="json"))
    narrow = json.loads(capsys.readouterr().out)
    define.run(_Args(list_terms=True, all_packs=True, format="json"))
    wide = json.loads(capsys.readouterr().out)

    assert len(narrow) < len(wide)
    assert not any(t["namespace"] == "aims" for t in narrow)
    assert any(t["namespace"] == "aims" for t in wide)


def test_the_last_live_version_is_the_last_context_that_had_the_term(capsys):
    """Computed from the contexts, so it cannot pass by coincidence.

    `test_dropped_term_resolves_and_says_it_is_not_current` pins "v0.4" and
    "v0.6" as literals, and for a while it passed for the wrong reason: the
    range end was reconstructed as "one version before the newest context",
    which happened to equal the right answer only while `reviewDate` had been
    dropped in exactly the newest context. Adding v0.8 broke the coincidence and
    the command began reporting v0.7 -- a version that never carried the term.

    This asserts the relationship instead of the strings: whatever the newest
    context is, the range must end at the last context that actually defines
    the term.
    """
    import json as _json
    import re as _re

    ctx_dir = paths.find_repo_root() / "spec" / "context"
    versions = sorted(
        (p for p in ctx_dir.glob("v*.jsonld")),
        key=lambda p: [int(d) for d in _re.findall(r"\d+", p.name)])
    carrying = [p.stem for p in versions
                if "reviewDate" in _json.loads(p.read_text(encoding="utf-8"))["@context"]]
    assert carrying, "reviewDate is in no context; this test needs a new subject"
    assert "reviewDate" not in _json.loads(
        versions[-1].read_text(encoding="utf-8"))["@context"], (
        "reviewDate is back in the newest context, so it is no longer a dropped term")

    rc = define.run(_Args(term="reviewDate", all_packs=True))
    out = capsys.readouterr().out
    assert rc == 0
    assert f"to {carrying[-1]}" in out, (
        f"reported range does not end at {carrying[-1]}, the last context "
        f"carrying the term:\n{out}")
    assert f"to {versions[-1].stem}" not in out, (
        "the range names the newest context, which does not carry the term")

"""The CLI's view of the vocabulary agrees with the shapes it is built from.

``uofa_cli.vocab`` exists so that violation messages, ``uofa define`` and the
site generator all read one source instead of each keeping a copy. These tests
pin the properties that make that true, and are written against the graph rather
than against literals wherever the answer can be computed -- so that describing
more pack terms does not require editing this file.
"""

from __future__ import annotations

import pytest

from uofa_cli import paths, vocab

rdflib = pytest.importorskip("rdflib")
from rdflib import Graph, URIRef  # noqa: E402
from rdflib.namespace import RDFS, SH  # noqa: E402


def _all_pack_names() -> list[str]:
    return [p for p in paths.list_packs(paths.find_repo_root()) if p != "core"]


def _graph(active: list[str]) -> tuple[Graph, list]:
    files = paths.all_shacl_schemas(paths.find_repo_root(), active=active)
    g = Graph()
    for f in files:
        g.parse(str(f), format="turtle")
    return g, files


def test_shape_files_are_distinct_after_resolution():
    """The loader must never hand back the same file twice.

    ``spec/schemas/uofa_shacl.ttl`` is a symlink to
    ``packs/core/shapes/uofa_shacl.ttl``. Loading both parses core twice, which
    re-mints its blank nodes and duplicates every property shape, so each
    ``sh:message`` would be collected twice and pack attribution would be wrong.

    This asserts the invariant rather than a shape count, so it fails on the
    symlink and never on legitimately adding a new shape.
    """
    files = paths.all_shacl_schemas(paths.find_repo_root(), active=_all_pack_names())
    resolved = [f.resolve() for f in files]
    assert len(resolved) == len(set(resolved)), (
        f"the same file is loaded more than once: {sorted(str(f) for f in files)}"
    )


def test_every_constrained_property_is_indexed():
    """Everything that can appear in a violation is in the index."""
    active = _all_pack_names()
    g, _ = _graph(active)
    sh_paths = {str(o) for o in g.objects(None, SH.path) if isinstance(o, URIRef)}

    idx = vocab.index(all_packs=True)
    indexed = {iri for iri, t in idx.items() if t.packs}

    assert indexed == sh_paths, (
        f"missing from index: {sorted(sh_paths - indexed)}; "
        f"spurious: {sorted(indexed - sh_paths)}"
    )


def test_definition_coverage_matches_the_graph():
    """Coverage is read from the graph, not asserted as a literal.

    Describing more pack terms should make this pass with a better number, not
    require editing the test.
    """
    active = _all_pack_names()
    g, _ = _graph(active)
    sh_paths = {str(o) for o in g.objects(None, SH.path) if isinstance(o, URIRef)}
    authored = {p for p in sh_paths if g.value(URIRef(p), RDFS.comment)}

    idx = vocab.index(all_packs=True)
    from_index = {p for p in sh_paths if idx[p].comment}

    # Every authored comment is reflected...
    assert authored <= from_index
    # ...and the only additions are terms UofA does not own, covered by the gloss.
    extra = from_index - authored
    assert all(idx[p].namespace == "external" for p in extra), (
        f"a uofa: term gained a definition from somewhere other than the graph: "
        f"{sorted(p for p in extra if idx[p].namespace != 'external')}"
    )


def test_pack_scope_changes_what_is_visible():
    """A caller sees the packs it asked for, and no more.

    The default pack set cannot see aims or surrogate terms, which is why a
    violation lookup has to be given the packs that produced it.
    """
    default = {iri for iri, t in vocab.index().items() if t.packs}
    everything = {iri for iri, t in vocab.index(all_packs=True).items() if t.packs}

    assert default < everything
    assert not any(i.startswith(vocab.AIMS_NS) for i in default)
    assert any(i.startswith(vocab.AIMS_NS) for i in everything)


def test_external_terms_are_glossed_and_attributed():
    """The five non-UofA paths get a meaning, and never claim a uofa: IRI."""
    idx = vocab.index(all_packs=True)
    external = [t for t in idx.values() if t.packs and t.namespace == "external"]
    assert external, "expected prov/dcterms/schema paths in the shapes"
    for t in external:
        assert t.comment, f"{t.name} has no gloss"
        assert t.source, f"{t.name} renders a definition with no attribution"
        assert not t.iri.startswith("https://uofa.net/vocab"), (
            f"{t.name} is not a UofA term and must not claim a uofa: IRI"
        )


def test_sh_message_is_never_used_as_a_definition():
    """A constraint message states a rule; it must not be served as meaning.

    80 of the 108 paths carry an sh:message. Using one as a fallback would put
    text in the Means: slot that says something the reader did not ask for and
    that already renders as Required.
    """
    idx = vocab.index(all_packs=True)
    for t in idx.values():
        if not t.messages or not t.comment:
            continue
        assert t.comment not in t.messages, (
            f"{t.name}'s definition is one of its sh:message strings"
        )

    # An undefined term must stay undefined even when it carries constraint
    # messages, which is the whole temptation. Asserted against a constructed
    # case rather than against whatever the repo currently leaves undefined:
    # an earlier version of this test required the undefined set to be
    # non-empty, and then describing the last pack terms emptied it and the
    # guard failed on its own success.
    graph = Graph()
    for f in paths.all_shacl_schemas(paths.find_repo_root(), active=_all_pack_names()):
        graph.parse(str(f), format="turtle")

    constrained_without_comment = URIRef("https://uofa.net/vocab#notATermAnyoneDefined")
    assert graph.value(constrained_without_comment, RDFS.comment) is None
    assert vocab.definition_in(graph, str(constrained_without_comment)) is None, (
        "a term with no rdfs:comment must yield no definition, whatever else "
        "the shapes say about it"
    )

    # And for any term that is undefined today, the same must hold.
    for t in (t for t in idx.values() if t.packs and not t.comment):
        assert vocab.definition(t.iri, active=_all_pack_names()) is None, (
            f"{t.name} has no definition but definition() returned one"
        )


def test_version_ordering_is_numeric():
    """v0.10 must not sort before v0.2.

    Lexicographic ordering would backdate every term's `since` and pick the
    wrong current version. The same bug was found and fixed in the Node
    extractor.
    """
    assert vocab._version_key("v0.10") > vocab._version_key("v0.2")
    assert vocab._version_key("v0.7") > vocab._version_key("v0.6")
    assert sorted(["v0.10", "v0.2", "v0.7"], key=vocab._version_key) == [
        "v0.2", "v0.7", "v0.10"
    ]


def test_dropped_and_deprecated_terms_are_marked():
    """A term the current context dropped stays resolvable and says so."""
    idx = vocab.index(all_packs=True)

    review = vocab.lookup("reviewDate", all_packs=True)
    assert review is not None, "a dropped term must still resolve"
    assert review.since == "v0.4"
    assert review.dropped_in is not None
    assert review.comment is None  # the repository has no definition; do not invent one

    live = vocab.lookup("hasContextOfUse", all_packs=True)
    assert live.dropped_in is None

    deprecated = [t for t in idx.values() if t.deprecated]
    assert {t.name for t in deprecated} == {
        "agreementMakesNonDispositive", "factorConstraintWarrants",
        "frameworkTransfers", "sustainedDefeaterJustified",
        "thresholdDistanceModulates",
    }


def test_owl_deprecated_false_does_not_mark_a_term():
    """`false` is the RDF default and says nothing.

    Carried over from the Node extractor's test suite when that reader was
    removed. rdflib returns a typed Literal here, and a naive truthiness check
    on the node would mark every term that explicitly says it is *not*
    deprecated.
    """
    from rdflib import Graph as G

    g = G()
    g.parse(data="""
        @prefix uofa: <https://uofa.net/vocab#> .
        @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
        @prefix owl: <http://www.w3.org/2002/07/owl#> .
        uofa:gone a rdf:Property ; owl:deprecated true .
        uofa:here a rdf:Property ; owl:deprecated false .
    """, format="turtle")
    owl_dep = URIRef("http://www.w3.org/2002/07/owl#deprecated")
    assert bool(g.value(URIRef("https://uofa.net/vocab#gone"), owl_dep)) is True
    assert bool(g.value(URIRef("https://uofa.net/vocab#here"), owl_dep)) is False


def test_a_pattern_containing_a_character_class_survives():
    """uofa:hash's sh:pattern contains [a-f0-9].

    The regex reader this replaced had to stop each property shape at a line
    that is only a closing bracket, because cutting at the first "]" truncated
    inside that character class and silently dropped both the pattern and the
    message. Kept as a regression test now that rdflib does the parsing.
    """
    term = vocab.lookup("hash", all_packs=True)
    patterns = [c["pattern"] for c in term.constraints if c.get("pattern")]
    assert patterns, "uofa:hash should carry a pattern constraint"
    assert any("a-f0-9" in p for p in patterns)
    assert any("hexdigest" in (c.get("message") or "") for c in term.constraints)


def test_enumerations_are_captured():
    """sh:in is the most directly useful thing a page can show.

    The regex reader counted terms with an sh:in as constrained but captured
    nothing to render, so the site reported more constrained terms than it
    displayed constraints for.
    """
    assert any(c.get("in") == "Low, Medium, High"
               for c in vocab.lookup("assuranceLevel", all_packs=True).constraints)


def test_an_sh_or_datatype_reports_both_alternatives():
    """credibilityIndex is decimal OR double, and must not read as just one."""
    dts = [c["datatype"] for c in vocab.lookup("credibilityIndex", all_packs=True).constraints
           if c.get("datatype")]
    assert dts and all("or" in d for d in dts), dts


def test_lookup_resolves_names_iris_and_json_keys():
    assert vocab.lookup("https://uofa.net/vocab#hasContextOfUse", all_packs=True)
    assert vocab.lookup("hasContextOfUse", all_packs=True)
    assert vocab.lookup("nonexistentTermName", all_packs=True) is None


def test_case_only_pairs_never_resolve_to_each_other():
    """acceptanceCriteria and AcceptanceCriteria mean different things."""
    prop = vocab.lookup("acceptanceCriteria", all_packs=True)
    cls = vocab.lookup("AcceptanceCriteria", all_packs=True)
    assert prop.kind == "Property"
    assert cls.kind == "Class"
    assert prop.iri != cls.iri

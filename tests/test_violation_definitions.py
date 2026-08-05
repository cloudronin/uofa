"""A validation failure tells the user what the field means, not just its name.

Before this, a violation gave a property name, a constraint and a fix string.
A user who did not already know what ``hasContextOfUse`` was could not evaluate
any of them, and the definition that would have told them lived only on a web
page.

Every assertion here compares against the shapes graph **at test time**. That is
deliberate: the failure mode being guarded against is a second hand-maintained
copy of the definitions growing inside the CLI, which is exactly what
``_FIX_SUGGESTIONS`` is and what the PROFILE_URIS bug was. A test comparing
against a pasted literal would not notice.
"""

from __future__ import annotations

import json

import pytest

from uofa_cli import paths, shacl_friendly

rdflib = pytest.importorskip("rdflib")
from rdflib import Graph, URIRef  # noqa: E402
from rdflib.namespace import RDFS  # noqa: E402

CORE = "https://uofa.net/vocab#"


@pytest.fixture(scope="module")
def shapes():
    files = paths.all_shacl_schemas(paths.find_repo_root(), active=["vv40"])
    g = Graph()
    for f in files:
        g.parse(str(f), format="turtle")
    return g, files


@pytest.fixture
def failing_package(tmp_path):
    """A Complete-profile package missing nearly everything it must declare."""
    p = tmp_path / "bad.jsonld"
    p.write_text(json.dumps({
        "@context": str(paths.context_file()),
        "id": "https://example.org/demo/cou1",
        "type": "UnitOfAssurance",
        "conformsToProfile": f"{CORE}ProfileComplete",
        "couName": "demo",
    }), encoding="utf-8")
    return p


def test_violations_carry_the_definition_from_the_graph(shapes, failing_package):
    g, files = shapes
    conforms, violations = shacl_friendly.run_shacl_multi(failing_package, files)
    assert not conforms and violations

    checked = 0
    for v in violations:
        iri = v.get("path_iri")
        if not iri:
            continue
        comment = g.value(URIRef(iri), RDFS.comment)
        if comment is None:
            continue
        assert v["means"] == str(comment), (
            f"{v['path']}: means does not match rdfs:comment in the graph"
        )
        checked += 1
    assert checked >= 5, "expected several core properties with definitions to fire"


def test_rendered_output_contains_the_definition(shapes, failing_package, capsys):
    g, files = shapes
    _, violations = shacl_friendly.run_shacl_multi(failing_package, files)
    shacl_friendly.print_violations(violations)
    out = capsys.readouterr().out

    target = next(v for v in violations if v["path"] == "hasContextOfUse")
    comment = str(g.value(URIRef(f"{CORE}hasContextOfUse"), RDFS.comment))
    # Wrapped across lines, so compare on words rather than the whole string.
    first_words = " ".join(comment.split()[:6])
    assert "Means:" in out
    assert first_words in out, f"expected the graph's definition in stdout: {first_words!r}"


def test_definition_never_falls_back_to_sh_message(shapes, failing_package):
    """sh:message says what the rule is; it must not be served as meaning.

    80 of the 108 constrained paths carry one, so it is the tempting fallback
    and the one that would quietly mislead: it reads like a definition while
    stating something else, and it already renders as Required.
    """
    g, files = shapes
    _, violations = shacl_friendly.run_shacl_multi(failing_package, files)
    for v in violations:
        means = v.get("means")
        if not means:
            continue
        assert means != v.get("requirement"), f"{v['path']}: means restates the constraint"
        assert means != v.get("message"), f"{v['path']}: means is the sh:message"


def test_external_terms_are_attributed_and_not_claimed(shapes, failing_package):
    """UofA does not own prov:generatedAtTime and must not appear to."""
    _, violations = shacl_friendly.run_shacl_multi(failing_package, shapes[1])
    prov = [v for v in violations if v.get("path_iri", "").startswith("http://www.w3.org/ns/prov#")]
    assert prov, "expected the prov:* paths to fire on a package missing them"
    for v in prov:
        assert v["means"].startswith("(PROV-O)"), (
            f"{v['path']}: an external definition must say whose it is"
        )


def test_missing_definition_omits_the_line_rather_than_guessing(shapes):
    """No definition means no Means: line. Never a name-derived guess."""
    assert shacl_friendly._means(f"{CORE}thisTermDoesNotExist", shapes[0]) == ""
    assert shacl_friendly._means("", shapes[0]) == ""

    rendered = shacl_friendly._wrap_means("", "         Means:    ", 19)
    assert rendered == []


def test_a_broken_lookup_cannot_break_validation_output(shapes, failing_package, monkeypatch):
    """The user is already looking at an error; do not add a traceback to it."""
    from uofa_cli import vocab

    def boom(*a, **k):
        raise RuntimeError("graph exploded")

    monkeypatch.setattr(vocab, "definition_in", boom)
    monkeypatch.setattr(vocab, "definition", boom)

    conforms, violations = shacl_friendly.run_shacl_multi(failing_package, shapes[1])
    assert not conforms and violations
    assert all(v.get("means") == "" for v in violations)

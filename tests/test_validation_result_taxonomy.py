"""Everything attached by uofa:hasValidationResult is actually a validation result.

Core defines uofa:ValidationResult as "a recorded comparison between what the
model predicted and what was measured". The surrogate pack honours that: its
ConstraintCheckEvidence, CalibrationEvidence and ModelComparisonRecord all
declare `rdfs:subClassOf uofa:ValidationResult`.

The iso42001 pack attaches two of its own classes with the same property, and
they do not agree with each other:

  ModelEvaluationReport   requires evaluatedModelVersion + testSetCoverage, so
                          it does record model output against held-out truth.
                          It now declares the subclass.
  AuditResultsRecord      requires auditedFunction + auditDate + auditFindings.
                          It examines how the management system operates. It is
                          not a validation result and does not claim to be.

This test exists because that disagreement blocks declaring
`rdfs:range uofa:ValidationResult` on the core property: the range would entail
that every attached node IS a ValidationResult, and one shipped package still
attaches something that is not. It guards against new violations and makes the
remaining one visible rather than forgotten.
"""

from __future__ import annotations

import json

import pytest

from uofa_cli import paths

rdflib = pytest.importorskip("rdflib")
from rdflib import Graph, URIRef  # noqa: E402
from rdflib.namespace import RDFS  # noqa: E402

CORE = "https://uofa.net/vocab#"
VALIDATION_RESULT = URIRef(CORE + "ValidationResult")

# COU1 of the iso42001 hybrid case is a governance-only context of use: an
# internal LLM retrieval assistant whose evidence is policy, scope, roles, risk
# register, data provenance and an AIMS controls audit. It has no model
# evaluation, but ProfileMinimal requires `hasValidationResult` minCount 1, so
# it points the property at the same audit record it already carries under
# `hasEvidence`.
#
# That is a shape-fit problem, not a typo: a pure AIMS package may genuinely
# have nothing to validate. Resolving it means either giving COU1 a real
# evaluation or letting ProfileMinimal accept a package that has none. Once it
# is resolved, delete this exception and declare the range in
# packs/core/shapes/uofa_shacl.ttl.
KNOWN_EXCEPTIONS = {
    "https://uofa.net/iso42001/hybrid/cou1/audit": "AuditResultsRecord",
}


def _shapes_graph() -> Graph:
    g = Graph()
    root = paths.find_repo_root()
    for ttl in sorted(root.glob("packs/*/shapes/*.ttl")):
        g.parse(str(ttl), format="turtle")
    return g


def _is_validation_result(g: Graph, cls: URIRef) -> bool:
    """Transitive rdfs:subClassOf closure up to uofa:ValidationResult."""
    seen: set[URIRef] = set()
    stack = [cls]
    while stack:
        c = stack.pop()
        if c == VALIDATION_RESULT:
            return True
        if c in seen:
            continue
        seen.add(c)
        stack.extend(g.objects(c, RDFS.subClassOf))
    return False


def _types_of(node) -> list[str]:
    t = node.get("@type") or node.get("type")
    if t is None:
        return []
    return [t] if isinstance(t, str) else list(t)


def _expand(t: str) -> str:
    return t if t.startswith("http") else CORE + t


def _attached_targets():
    """(source pack, target IRI, [type IRIs]) for every hasValidationResult edge.

    Bare IRIs with no node anywhere in the corpus are skipped: the context types
    this property as @id, so an external reference is legitimate and asserts
    nothing about its type either way.
    """
    root = paths.find_repo_root()
    files = sorted(root.glob("packs/*/examples/**/*.jsonld"))
    docs = [(f, json.loads(f.read_text(encoding="utf-8"))) for f in files]

    known: dict[str, list[str]] = {}

    def index(node):
        if isinstance(node, list):
            for n in node:
                index(n)
        elif isinstance(node, dict):
            nid = node.get("@id") or node.get("id")
            types = _types_of(node)
            if nid and types:
                known[nid] = [_expand(t) for t in types]
            for v in node.values():
                index(v)

    for _, d in docs:
        index(d)

    out = []

    def walk(pack, node):
        if isinstance(node, list):
            for n in node:
                walk(pack, n)
        elif isinstance(node, dict):
            for key, value in node.items():
                if key == "hasValidationResult":
                    for item in (value if isinstance(value, list) else [value]):
                        if isinstance(item, dict):
                            ref = item.get("@id") or item.get("id")
                            types = [_expand(t) for t in _types_of(item)] or known.get(ref)
                        else:
                            ref, types = item, known.get(item)
                        if types:
                            out.append((pack, ref, types))
                walk(pack, value)

    for f, d in docs:
        walk(f.relative_to(root).parts[1], d)
    return out


def test_attached_nodes_are_validation_results():
    g = _shapes_graph()
    violations = []
    for pack, ref, types in _attached_targets():
        if any(_is_validation_result(g, URIRef(t)) for t in types):
            continue
        if ref in KNOWN_EXCEPTIONS:
            continue
        violations.append((pack, ref, [t.rsplit("#", 1)[-1] for t in types]))

    assert not violations, (
        "hasValidationResult attaches nodes that are not uofa:ValidationResult "
        f"and are not a known exception: {violations}. Either declare "
        "rdfs:subClassOf uofa:ValidationResult on the class, or attach the node "
        "with a property that fits it (hasEvidence, usually)."
    )


def test_model_evaluation_report_is_a_validation_result():
    g = _shapes_graph()
    cls = URIRef("https://uofa.net/vocab/aims#ModelEvaluationReport")
    assert _is_validation_result(g, cls), (
        "ModelEvaluationReport requires evaluatedModelVersion and testSetCoverage, "
        "so it records model output against held-out truth and should subclass "
        "uofa:ValidationResult"
    )


def test_audit_results_record_is_not_a_validation_result():
    # Pinned deliberately: an AIMS audit examines the management system, not the
    # model. Making it a ValidationResult to satisfy a shape would let a package
    # claim model validation it never performed.
    g = _shapes_graph()
    cls = URIRef("https://uofa.net/vocab/aims#AuditResultsRecord")
    assert not _is_validation_result(g, cls), (
        "an internal AIMS audit is not a comparison of model output against "
        "measurement; it must not become a uofa:ValidationResult"
    )


def test_known_exceptions_are_still_real():
    """Delete an exception once it is fixed, rather than letting it go stale."""
    targets = {ref: types for _, ref, types in _attached_targets()}
    for ref, expected_type in KNOWN_EXCEPTIONS.items():
        assert ref in targets, (
            f"{ref} is listed as a known exception but nothing attaches it with "
            "hasValidationResult any more. Remove it from KNOWN_EXCEPTIONS, and "
            "if the list is now empty declare rdfs:range uofa:ValidationResult "
            "on uofa:hasValidationResult in packs/core/shapes/uofa_shacl.ttl."
        )
        assert any(t.endswith("#" + expected_type) for t in targets[ref]), (
            f"{ref} is no longer a {expected_type}; re-check the exception"
        )

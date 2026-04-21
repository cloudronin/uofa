"""W-PROV-01: Provenance Chain Incomplete.

Forward-chaining Jena rules cannot cleanly express transitive-closure absence
(i.e., "traverse prov:wasDerivedFrom+ and find a node that has no upstream AND
is not marked foundational"). This rule is implemented in Python as a
post-Jena pass over the canonical RDF graph.

Semantics:
- Start from every Claim reachable from a UnitOfAssurance via bindsClaim.
- Transitively follow prov:wasDerivedFrom, prov:wasGeneratedBy, prov:used
  edges upstream.
- At each node, if it has no upstream edge AND it is not explicitly marked
  `uofa:isFoundationalEvidence = true`, emit W-PROV-01 (Critical) on that node.

Rationale for "foundational" marker: nodes without upstream edges are either
genuine provenance roots (a standards document, a real-world dataset) or
gaps in the documented chain. The marker disambiguates.
"""

from __future__ import annotations

from pathlib import Path
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF

UOFA = Namespace("https://uofa.net/vocab#")
PROV = Namespace("http://www.w3.org/ns/prov#")

# Upstream edges that W-PROV-01 traces backwards from a Claim.
UPSTREAM_PREDICATES = (PROV.wasDerivedFrom, PROV.wasGeneratedBy, PROV.used)


def detect_w_prov_01(jsonld_path: Path, context_path: Path | None = None) -> list[dict]:
    """Detect W-PROV-01 annotations in a UofA JSON-LD file.

    Returns a list of annotation dicts shaped like:
        {"patternId": "W-PROV-01", "severity": "Critical",
         "affectedNode": "https://...", "description": "..."}

    Context file is optional; rdflib can expand the JSON-LD against its
    embedded @context reference. Passing an explicit context is only needed
    when the embedded reference is unreachable.
    """
    g = Graph()
    g.parse(str(jsonld_path), format="json-ld")

    # Every UofA's Claim is the traversal start point.
    claims = set()
    for uofa in g.subjects(RDF.type, UOFA.UnitOfAssurance):
        for claim in g.objects(uofa, UOFA.bindsClaim):
            claims.add(claim)

    if not claims:
        return []

    # BFS upstream from each claim; collect visited nodes.
    visited: set[URIRef] = set()
    frontier: list[URIRef] = list(claims)
    while frontier:
        node = frontier.pop()
        if node in visited or not isinstance(node, URIRef):
            continue
        visited.add(node)
        for pred in UPSTREAM_PREDICATES:
            for upstream in g.objects(node, pred):
                if isinstance(upstream, URIRef) and upstream not in visited:
                    frontier.append(upstream)

    # Identify gaps: nodes in the visited set that have no upstream edges
    # and are not marked foundational.
    annotations: list[dict] = []
    for node in sorted(visited, key=str):
        if node in claims:
            # The claim itself is the start of the trace; W-EP-01 handles
            # the "no wasDerivedFrom" case directly. W-PROV-01 flags gaps
            # deeper in the chain.
            continue

        has_upstream = any(
            any(g.objects(node, pred)) for pred in UPSTREAM_PREDICATES
        )
        if has_upstream:
            continue

        # No upstream — is it marked foundational?
        foundational = False
        for value in g.objects(node, UOFA.isFoundationalEvidence):
            if isinstance(value, Literal) and str(value).lower() in ("true", "1"):
                foundational = True
                break
        if foundational:
            continue

        annotations.append({
            "patternId": "W-PROV-01",
            "severity": "Critical",
            "affectedNode": str(node),
            "description": (
                "Provenance chain terminates at a node that has no upstream "
                "derivation/generation/use edge and is not marked "
                "uofa:isFoundationalEvidence=true — chain is incomplete."
            ),
        })

    return annotations

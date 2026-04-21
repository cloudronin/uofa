"""W-CON-05: Activity-Evidence Consistency.

A VerificationActivity declared on a UofA via `uofa:hasVerificationActivity`
with no Evidence linked to it via `prov:wasGeneratedBy` is a procedural
placeholder, not real verification.

Implementation note: expressed as a two-stage Jena rule this pattern has a
forward-RETE ordering bug (noValue evaluates before the stage-1 marker lands,
producing false positives on activities that DO have evidence). Python
post-pass walks the complete graph once and avoids the ordering issue.
"""

from __future__ import annotations

from pathlib import Path
from rdflib import Graph, Namespace, URIRef
from rdflib.namespace import RDF

UOFA = Namespace("https://uofa.net/vocab#")
PROV = Namespace("http://www.w3.org/ns/prov#")


def detect_w_con_05(jsonld_path: Path, context_path: Path | None = None) -> list[dict]:
    """Detect W-CON-05 annotations in a UofA JSON-LD file.

    For each VerificationActivity declared on a UofA via
    `uofa:hasVerificationActivity`, check if any Evidence in the graph
    references it via `prov:wasGeneratedBy`. If none does, emit W-CON-05.
    """
    g = Graph()
    g.parse(str(jsonld_path), format="json-ld")

    # Collect activities referenced by any evidence via wasGeneratedBy.
    activities_with_evidence: set[URIRef] = set()
    for _ev, act in g.subject_objects(PROV.wasGeneratedBy):
        if isinstance(act, URIRef):
            activities_with_evidence.add(act)

    annotations: list[dict] = []
    for uofa in g.subjects(RDF.type, UOFA.UnitOfAssurance):
        for act in g.objects(uofa, UOFA.hasVerificationActivity):
            if not isinstance(act, URIRef):
                continue
            if act in activities_with_evidence:
                continue
            annotations.append({
                "patternId": "W-CON-05",
                "severity": "High",
                "affectedNode": str(act),
                "description": (
                    "VerificationActivity is declared on the UofA but no "
                    "Evidence is linked via prov:wasGeneratedBy — the activity "
                    "is a procedural placeholder rather than real verification."
                ),
            })

    return annotations

"""W-CON-02: Identifier Resolution.

A UofA that references an external identifier (URI via `uofa:referencesIdentifier`)
whose target IRI is not a subject of any triple in the graph — i.e., a dangling
internal reference — is inconsistent. The reference points nowhere that the
document itself describes.

Scope (v0.5): local-graph resolution only. No HTTP fetches or external registries.
A documented external-fetch hint (`schema:url` on the referenced IRI, or the
referenced IRI being an absolute HTTP(S) URL itself) is treated as acceptable;
the rule only fires on references whose targets neither resolve locally nor carry
an external-fetch hint.
"""

from __future__ import annotations

from pathlib import Path
from rdflib import Graph, Namespace, URIRef
from rdflib.namespace import RDF

UOFA = Namespace("https://uofa.net/vocab#")
SCHEMA = Namespace("https://schema.org/")


def detect_w_con_02(jsonld_path: Path, context_path: Path | None = None) -> list[dict]:
    """Detect W-CON-02 annotations in a UofA JSON-LD file.

    Returns a list of annotation dicts:
        {"patternId": "W-CON-02", "severity": "Medium",
         "affectedNode": <referencing-node>, "description": "..."}
    """
    g = Graph()
    g.parse(str(jsonld_path), format="json-ld")

    # Collect the set of subjects in the graph; a dangling reference is any
    # object of `uofa:referencesIdentifier` that is not also a subject somewhere.
    subjects = set(g.subjects())

    annotations: list[dict] = []
    for subj, obj in g.subject_objects(UOFA.referencesIdentifier):
        if not isinstance(obj, URIRef):
            continue

        # Resolves locally?
        if obj in subjects:
            continue

        # Documented external-fetch hint? (schema:url on the referenced IRI,
        # or the IRI is itself an absolute HTTP(S) URL that could be fetched)
        if any(g.objects(obj, SCHEMA.url)):
            continue
        iri = str(obj)
        if iri.startswith(("http://", "https://")):
            # An absolute URL is a self-documenting external reference — the
            # fetch path is the IRI itself. Treat as acceptable for v0.5.
            continue

        annotations.append({
            "patternId": "W-CON-02",
            "severity": "Medium",
            "affectedNode": str(subj),
            "description": (
                f"UofA references identifier <{iri}> which does not resolve "
                "within the graph and has no documented external-fetch hint."
            ),
        })

    return annotations

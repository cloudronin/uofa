#!/usr/bin/env python3
"""
validate_morrison_cou1.py
─────────────────────────
Validates uofa-morrison-cou1.jsonld against uofa_shacl.ttl using pySHACL.

The JSON-LD references its context as an external file:
    "@context": "uofa_v0_2.jsonld"

This script resolves that reference from the local filesystem before
parsing, so no network access is needed.

Expected directory layout (all three files in the same folder):
    ./uofa-morrison-cou1.jsonld   ← data graph
    ./uofa_v0_2.jsonld            ← JSON-LD context (schema v0.2)
    ./uofa_shacl.ttl              ← SHACL shapes
    ./validate_morrison_cou1.py   ← this script

Requirements:
    pip install pyshacl rdflib

Usage:
    python validate_morrison_cou1.py
    python validate_morrison_cou1.py --data path/to/cou1.jsonld \
                                     --context path/to/uofa_v0_2.jsonld \
                                     --shapes path/to/uofa_shacl.ttl
"""

import argparse
import json
import sys
from pathlib import Path

from pyshacl import validate
from rdflib import Graph, Namespace, URIRef


# ── Namespaces ──────────────────────────────────────────────────────
UOFA = Namespace("https://uofa.net/vocab#")
PROV = Namespace("http://www.w3.org/ns/prov#")


def resolve_context(data_path: Path, context_path: Path) -> str:
    """
    Load the JSON-LD data file and its external @context file,
    merge them in-memory, and return the combined JSON string.

    This avoids rdflib's inconsistent handling of relative @context
    file references across versions and platforms.
    """
    with open(data_path, "r", encoding="utf-8") as f:
        doc = json.load(f)

    ctx_ref = doc.get("@context")

    # If @context is already an inline object, nothing to resolve
    if isinstance(ctx_ref, dict):
        print(f"  @context is already inline — no external file to resolve.")
        return json.dumps(doc)

    # If @context is a string, resolve it from the filesystem
    if isinstance(ctx_ref, str):
        # Try the explicit context_path first, then resolve relative
        # to the data file's directory
        if context_path.exists():
            resolved = context_path
        else:
            resolved = data_path.parent / ctx_ref
            if not resolved.exists():
                print(f"  ERROR: Cannot resolve @context \"{ctx_ref}\"")
                print(f"         Tried: {context_path}")
                print(f"         Tried: {resolved}")
                sys.exit(1)

        print(f"  Resolved @context \"{ctx_ref}\" → {resolved}")

        with open(resolved, "r", encoding="utf-8") as f:
            ctx_doc = json.load(f)

        # The context file is a JSON-LD context document with a
        # top-level "@context" key — extract the inner object
        if "@context" in ctx_doc:
            doc["@context"] = ctx_doc["@context"]
        else:
            doc["@context"] = ctx_doc

        return json.dumps(doc)

    # If @context is an array (multi-context), resolve each string entry
    if isinstance(ctx_ref, list):
        resolved_ctx = []
        for entry in ctx_ref:
            if isinstance(entry, str):
                p = data_path.parent / entry
                if p.exists():
                    with open(p, "r", encoding="utf-8") as f:
                        c = json.load(f)
                    resolved_ctx.append(c.get("@context", c))
                else:
                    resolved_ctx.append(entry)  # keep URL as-is
            else:
                resolved_ctx.append(entry)
        doc["@context"] = resolved_ctx
        return json.dumps(doc)

    return json.dumps(doc)


def run_validation(data_path: Path, context_path: Path, shapes_path: Path):
    """Parse, validate, and print diagnostics."""

    print("=" * 70)
    print("  UofA pySHACL Validator")
    print("=" * 70)

    # ── Resolve external context and parse data graph ───────────────
    print(f"\n  Data file:    {data_path}")
    print(f"  Context file: {context_path}")
    print(f"  Shapes file:  {shapes_path}")
    print()

    merged_json = resolve_context(data_path, context_path)

    data = Graph()
    data.parse(data=merged_json, format="json-ld")
    print(f"  Data graph:   {len(data)} triples loaded.\n")

    # ── Load SHACL shapes ──────────────────────────────────────────
    shapes = Graph()
    shapes.parse(str(shapes_path), format="turtle")
    print(f"  Shapes graph: {len(shapes)} triples loaded.\n")

    # ── Run pySHACL ────────────────────────────────────────────────
    conforms, results_graph, results_text = validate(
        data,
        shacl_graph=shapes,
        inference="rdfs",
        abort_on_first=False,
        meta_shacl=False,
        advanced=True,
    )

    print("=" * 70)
    tag = "CONFORMS ✓" if conforms else "DOES NOT CONFORM ✗"
    print(f"  SHACL VALIDATION RESULT: {tag}")
    print("=" * 70)
    print()
    print(results_text)

    # ── Diagnostics ────────────────────────────────────────────────
    print("=" * 70)
    print("  DIAGNOSTIC: Key RDF triples on the UofA node")
    print("=" * 70)

    uofa_node = URIRef("https://uofa.net/morrison/cou1")

    checks = [
        ("conformsToProfile",    UOFA.conformsToProfile),
        ("bindsRequirement",     UOFA.bindsRequirement),
        ("hasContextOfUse",      UOFA.hasContextOfUse),
        ("bindsModel",           UOFA.bindsModel),
        ("bindsDataset",         UOFA.bindsDataset),
        ("hasValidationResult",  UOFA.hasValidationResult),
        ("hasDecisionRecord",    UOFA.hasDecisionRecord),
        ("hasCredibilityFactor", UOFA.hasCredibilityFactor),
        ("hasWeakener",          UOFA.hasWeakener),
        ("hash",                 UOFA.hash),
        ("signature",            UOFA.signature),
        ("assuranceLevel",       UOFA.assuranceLevel),
        ("criteriaSet",          UOFA.criteriaSet),
        ("credibilityIndex",     UOFA.credibilityIndex),
        ("wasDerivedFrom",       PROV.wasDerivedFrom),
        ("wasAttributedTo",      PROV.wasAttributedTo),
        ("generatedAtTime",      PROV.generatedAtTime),
    ]

    for label, pred in checks:
        objects = list(data.objects(uofa_node, pred))
        count = len(objects)
        status = "✓" if count > 0 else "✗ MISSING"
        vals = [str(o)[:70] for o in objects[:3]]
        print(f"  {status} {label}: {count} value(s)  {vals}")

    cf_count = len(list(data.objects(uofa_node, UOFA.hasCredibilityFactor)))
    wa_count = len(list(data.objects(uofa_node, UOFA.hasWeakener)))
    print(f"\n  CredibilityFactor nodes: {cf_count} (need >=1)")
    print(f"  WeakenerAnnotation nodes: {wa_count} (zero is valid)")

    return 0 if conforms else 1


def main():
    parser = argparse.ArgumentParser(
        description="Validate a UofA JSON-LD instance against SHACL shapes."
    )
    parser.add_argument(
        "--data",
        type=Path,
        default=Path("uofa-morrison-cou1.jsonld"),
        help="Path to the JSON-LD data file (default: uofa-morrison-cou1.jsonld)",
    )
    parser.add_argument(
        "--context",
        type=Path,
        default=Path("uofa_v0_2.jsonld"),
        help="Path to the JSON-LD context file (default: uofa_v0_2.jsonld)",
    )
    parser.add_argument(
        "--shapes",
        type=Path,
        default=Path("uofa_shacl.ttl"),
        help="Path to the SHACL shapes file (default: uofa_shacl.ttl)",
    )
    args = parser.parse_args()

    # Validate that files exist
    for label, path in [
        ("Data", args.data),
        ("Context", args.context),
        ("Shapes", args.shapes),
    ]:
        if not path.exists():
            print(f"ERROR: {label} file not found: {path}")
            print(
                "       Place all three files in the same directory, "
                "or use --data / --context / --shapes flags."
            )
            sys.exit(1)

    sys.exit(run_validation(args.data, args.context, args.shapes))


if __name__ == "__main__":
    main()

"""uofa schema — generate JSON Schema from the SHACL shapes (single source of truth)."""

import json
from pathlib import Path

from rdflib import Graph, Namespace, Literal, URIRef, BNode
from rdflib.collection import Collection

from uofa_cli.output import step_header, result_line, info
from uofa_cli import paths

HELP = "generate JSON Schema from SHACL shapes"

SH = Namespace("http://www.w3.org/ns/shacl#")
XSD = Namespace("http://www.w3.org/2001/XMLSchema#")
UOFA = Namespace("https://uofa.net/vocab#")
PROV = Namespace("http://www.w3.org/ns/prov#")

# Map XSD datatypes to JSON Schema types
_XSD_TYPE_MAP = {
    str(XSD.string): {"type": "string"},
    str(XSD.integer): {"type": "integer"},
    str(XSD.decimal): {"type": "number"},
    str(XSD.double): {"type": "number"},
    str(XSD.dateTime): {"type": "string", "format": "date-time"},
    str(XSD.boolean): {"type": "boolean"},
}

# Friendly property names from path URIs
_PATH_LABELS = {
    str(UOFA.bindsRequirement): "bindsRequirement",
    str(UOFA.bindsClaim): "bindsClaim",
    str(UOFA.bindsModel): "bindsModel",
    str(UOFA.bindsDataset): "bindsDataset",
    str(UOFA.hasContextOfUse): "hasContextOfUse",
    str(UOFA.hasValidationResult): "hasValidationResult",
    str(UOFA.hasDecisionRecord): "hasDecisionRecord",
    str(UOFA.hasCredibilityFactor): "hasCredibilityFactor",
    str(UOFA.hasWeakener): "hasWeakener",
    str(UOFA.conformsToProfile): "conformsToProfile",
    str(UOFA.hash): "hash",
    str(UOFA.signature): "signature",
    str(UOFA.signatureAlg): "signatureAlg",
    str(UOFA.canonicalizationAlg): "canonicalizationAlg",
    str(UOFA.assuranceLevel): "assuranceLevel",
    str(UOFA.criteriaSet): "criteriaSet",
    str(UOFA.credibilityIndex): "credibilityIndex",
    str(UOFA.traceCompleteness): "traceCompleteness",
    str(UOFA.verificationCoverage): "verificationCoverage",
    str(UOFA.validationCoverage): "validationCoverage",
    str(UOFA.uncertaintyCIWidth): "uncertaintyCIWidth",
    str(UOFA.factorType): "factorType",
    str(UOFA.requiredLevel): "requiredLevel",
    str(UOFA.achievedLevel): "achievedLevel",
    str(UOFA.patternId): "patternId",
    str(UOFA.severity): "severity",
    str(UOFA.affectedNode): "affectedNode",
    str(UOFA.actor): "actor",
    str(UOFA.role): "role",
    str(UOFA.outcome): "outcome",
    str(UOFA.rationale): "rationale",
    str(UOFA.decidedAt): "decidedAt",
    str(UOFA.intendedUse): "intendedUse",
    str(PROV.generatedAtTime): "generatedAtTime",
    str(PROV.wasDerivedFrom): "wasDerivedFrom",
    str(PROV.wasAttributedTo): "wasAttributedTo",
    str(PROV.wasGeneratedBy): "wasGeneratedBy",
}


def add_arguments(parser):
    parser.add_argument("--output", "-o", type=Path,
                        help="output path (default: spec/schemas/uofa.schema.json)")


def _collect_list(g: Graph, node) -> list:
    """Collect items from an RDF list (rdf:first/rdf:rest chain)."""
    try:
        return list(Collection(g, node))
    except Exception:
        return []


def _property_name(path_uri) -> str:
    """Extract a JSON property name from a SHACL path URI."""
    uri = str(path_uri)
    return _PATH_LABELS.get(uri, uri.rsplit("#", 1)[-1].rsplit("/", 1)[-1])


def _extract_property_schema(g: Graph, prop_node) -> tuple[str, dict, bool]:
    """Extract JSON Schema for a single sh:property constraint.

    Returns (property_name, schema_dict, is_required).
    """
    path = g.value(prop_node, SH.path)
    if not path:
        return None, None, False

    name = _property_name(path)
    schema = {}
    required = False
    description_parts = []

    # sh:minCount → required
    min_count = g.value(prop_node, SH.minCount)
    if min_count and int(min_count) >= 1:
        required = True

    # sh:message → description
    message = g.value(prop_node, SH.message)
    if message:
        description_parts.append(str(message))

    # sh:datatype → type
    datatype = g.value(prop_node, SH.datatype)
    if datatype:
        schema.update(_XSD_TYPE_MAP.get(str(datatype), {"type": "string"}))

    # sh:nodeKind sh:IRI → string (URI)
    node_kind = g.value(prop_node, SH.nodeKind)
    if node_kind == SH.IRI:
        schema["type"] = "string"
        schema["format"] = "iri"

    # sh:in → enum
    in_list = g.value(prop_node, SH["in"])
    if in_list:
        items = _collect_list(g, in_list)
        enum_values = [str(v) for v in items]
        if enum_values:
            schema["enum"] = enum_values

    # sh:pattern → pattern
    pattern = g.value(prop_node, SH.pattern)
    if pattern:
        schema["pattern"] = str(pattern)
        schema.setdefault("type", "string")

    # sh:minInclusive / sh:maxInclusive → minimum / maximum
    min_val = g.value(prop_node, SH.minInclusive)
    if min_val is not None:
        schema["minimum"] = float(str(min_val))

    max_val = g.value(prop_node, SH.maxInclusive)
    if max_val is not None:
        schema["maximum"] = float(str(max_val))

    # sh:or for datatype alternatives (e.g., decimal or double)
    or_list = g.value(prop_node, SH["or"])
    if or_list and not schema.get("type"):
        or_items = _collect_list(g, or_list)
        types = set()
        for item in or_items:
            dt = g.value(item, SH.datatype)
            if dt:
                mapped = _XSD_TYPE_MAP.get(str(dt), {})
                if "type" in mapped:
                    types.add(mapped["type"])
        if types:
            schema["type"] = "number" if "number" in types else list(types)[0]

    # sh:node → reference to another shape
    node_ref = g.value(prop_node, SH.node)
    if node_ref:
        ref_name = str(node_ref).rsplit("#", 1)[-1]
        schema["$ref"] = f"#/$defs/{ref_name}"

    # Default to string if no type determined
    if not schema.get("type") and not schema.get("$ref") and not schema.get("enum"):
        schema["type"] = "string"

    if description_parts:
        schema["description"] = " ".join(description_parts)

    return name, schema, required


def _extract_shape(g: Graph, shape_uri) -> dict:
    """Extract a JSON Schema object from a SHACL NodeShape."""
    properties = {}
    required_fields = []

    for prop_node in g.objects(shape_uri, SH.property):
        name, prop_schema, is_required = _extract_property_schema(g, prop_node)
        if name and prop_schema:
            properties[name] = prop_schema
            if is_required:
                required_fields.append(name)

    result = {"type": "object", "properties": properties}
    if required_fields:
        result["required"] = sorted(required_fields)

    return result


def _generate_schema(shacl_path: Path) -> dict:
    """Generate a complete JSON Schema from the SHACL shapes file."""
    g = Graph()
    g.parse(str(shacl_path), format="turtle")

    # Extract the main shapes
    minimal = _extract_shape(g, UOFA.UnitOfAssurance_MinimalBody)
    complete = _extract_shape(g, UOFA.UnitOfAssurance_CompleteBody)
    factor = _extract_shape(g, UOFA.CredibilityFactorShape)
    weakener = _extract_shape(g, UOFA.WeakenerAnnotationShape)

    # Build the combined schema using oneOf for Minimal vs Complete
    # Add common metadata fields to both profiles
    common_fields = {
        "@context": {
            "type": "string",
            "description": "JSON-LD context URI",
        },
        "id": {
            "type": "string",
            "format": "iri",
            "description": "Unique identifier for this UofA",
        },
        "type": {
            "const": "UnitOfAssurance",
            "description": "Must be UnitOfAssurance",
        },
        "conformsToProfile": {
            "type": "string",
            "enum": [
                "https://uofa.net/vocab#ProfileMinimal",
                "https://uofa.net/vocab#ProfileComplete",
            ],
            "description": "Which profile this UofA conforms to",
        },
        "name": {
            "type": "string",
            "description": "Human-readable name for this UofA",
        },
        "description": {
            "type": "string",
            "description": "Longer description of what this assessment covers",
        },
        "signatureAlg": {
            "type": "string",
            "description": "Signature algorithm (e.g., ed25519)",
        },
        "canonicalizationAlg": {
            "type": "string",
            "description": "Canonicalization algorithm (e.g., RDFC-1.0)",
        },
    }

    # Merge common fields into both profiles
    for profile in [minimal, complete]:
        profile["properties"] = {**common_fields, **profile["properties"]}

    # CredibilityFactor and WeakenerAnnotation need type field
    factor["properties"]["type"] = {"const": "CredibilityFactor"}
    weakener["properties"]["type"] = {"const": "WeakenerAnnotation"}

    # hasCredibilityFactor and hasWeakener should be arrays of objects
    if "hasCredibilityFactor" in complete["properties"]:
        complete["properties"]["hasCredibilityFactor"] = {
            "type": "array",
            "items": {"$ref": "#/$defs/CredibilityFactorShape"},
            "minItems": 1,
            "description": "Per-factor credibility assessments (V&V 40 Table 5-1)",
        }
    if "hasWeakener" in complete["properties"]:
        complete["properties"]["hasWeakener"] = {
            "type": "array",
            "items": {"$ref": "#/$defs/WeakenerAnnotationShape"},
            "description": "Detected quality gaps (optional — zero weakeners is valid)",
        }

    # hasValidationResult and bindsDataset can be arrays
    for profile in [minimal, complete]:
        for field in ["hasValidationResult", "bindsDataset"]:
            if field in profile["properties"]:
                existing = profile["properties"][field]
                profile["properties"][field] = {
                    "oneOf": [
                        existing,
                        {"type": "array", "items": existing},
                    ]
                }

    # hasContextOfUse can be inline object or IRI
    cou_inline = {
        "type": "object",
        "properties": {
            "id": {"type": "string", "format": "iri"},
            "type": {"const": "ContextOfUse"},
            "name": {"type": "string"},
            "description": {"type": "string"},
            "intendedUse": {"type": "string"},
        },
        "required": ["id", "type"],
    }
    for profile in [minimal, complete]:
        if "hasContextOfUse" in profile["properties"]:
            profile["properties"]["hasContextOfUse"] = {
                "oneOf": [
                    {"type": "string", "format": "iri"},
                    cou_inline,
                ],
                "description": "V&V 40 Context of Use (IRI or inline object)",
            }

    # hasDecisionRecord can be inline object or IRI
    decision_inline = {
        "type": "object",
        "properties": {
            "id": {"type": "string", "format": "iri"},
            "type": {"const": "DecisionRecord"},
            "actor": {"type": "string", "format": "iri"},
            "role": {"type": "string"},
            "outcome": {"type": "string", "enum": ["Accepted", "Rejected"]},
            "rationale": {"type": "string"},
            "decidedAt": {"type": "string", "format": "date-time"},
        },
        "required": ["id", "type", "outcome"],
    }
    for profile in [minimal, complete]:
        if "hasDecisionRecord" in profile["properties"]:
            profile["properties"]["hasDecisionRecord"] = {
                "oneOf": [
                    {"type": "string", "format": "iri"},
                    decision_inline,
                ],
                "description": "Credibility decision record (IRI or inline object)",
            }

    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://uofa.net/schemas/uofa.schema.json",
        "title": "Unit of Assurance (UofA)",
        "description": "Schema for UofA evidence packages. Generated from SHACL shapes — do not edit by hand. Regenerate with: uofa schema",
        "type": "object",
        "oneOf": [
            {
                "title": "Minimal Profile",
                "description": "Lightweight evidence package for audit trails and pipeline capture",
                "allOf": [
                    {"properties": {"conformsToProfile": {"const": "https://uofa.net/vocab#ProfileMinimal"}}},
                    minimal,
                ],
            },
            {
                "title": "Complete Profile",
                "description": "Full V&V 40 credibility assessment for regulatory submissions",
                "allOf": [
                    {"properties": {"conformsToProfile": {"const": "https://uofa.net/vocab#ProfileComplete"}}},
                    complete,
                ],
            },
        ],
        "$defs": {
            "CredibilityFactorShape": factor,
            "WeakenerAnnotationShape": weakener,
        },
    }

    return schema


def run(args) -> int:
    shacl = paths.shacl_schema()
    if not shacl.exists():
        raise FileNotFoundError(f"SHACL shapes not found: {shacl}")

    step_header("Generating JSON Schema from SHACL shapes")

    schema = _generate_schema(shacl)

    output = args.output or (paths.find_repo_root() / "spec" / "schemas" / "uofa.schema.json")
    output.parent.mkdir(parents=True, exist_ok=True)

    with open(output, "w") as f:
        json.dump(schema, f, indent=2, ensure_ascii=False)
        f.write("\n")

    # Count what was extracted
    n_props = sum(
        len(branch["allOf"][1].get("properties", {}))
        for branch in schema["oneOf"]
    )
    n_defs = len(schema.get("$defs", {}))

    result_line("Schema generated", True, str(output))
    info(f"  {n_props} properties across 2 profiles, {n_defs} definitions")
    info(f"  Source: {shacl}")
    info(f"  Add to your editor: set \"$schema\" in your .jsonld files")

    return 0

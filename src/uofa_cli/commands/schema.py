"""uofa schema — generate JSON Schema (or Python constants) from SHACL shapes."""

from __future__ import annotations

import json
import re
import textwrap
from pathlib import Path

from rdflib import Graph, Namespace, Literal, URIRef, BNode
from rdflib.collection import Collection

from uofa_cli.output import step_header, result_line, info
from uofa_cli import paths

HELP = "generate JSON Schema or import constants from SHACL shapes"

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
                        help="output path (default depends on --emit format)")
    parser.add_argument("--emit", choices=["json", "python"], default="json",
                        help="output format: json (JSON Schema, default) or python (import constants)")


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


# ── Python constants generation ──────────────────────────────


def _extract_sparql_not_in(g: Graph, shape_uri) -> list[str]:
    """Extract factor names from SPARQL NOT IN (...) constraints.

    The VV40 and NASA shapes use sh:sparql with a SELECT query containing
    a NOT IN (...) list of factor name strings.  We regex-parse the query
    text since rdflib doesn't execute SPARQL constraints natively.
    """
    names = []
    for sparql_node in g.objects(shape_uri, SH.sparql):
        select = g.value(sparql_node, SH.select)
        if not select:
            continue
        select_str = str(select)
        # Match NOT IN ( "name1", "name2", ... )
        match = re.search(r'NOT\s+IN\s*\((.*?)\)', select_str, re.DOTALL)
        if not match:
            continue
        block = match.group(1)
        names.extend(re.findall(r'"([^"]+)"', block))
    return names


def _extract_sparql_level_range(g: Graph, shape_uri) -> dict[str, tuple[int, int]]:
    """Extract level ranges from SPARQL FILTER constraints.

    Returns dict with keys 'required' and/or 'achieved' mapping to (min, max).
    """
    ranges = {}
    for sparql_node in g.objects(shape_uri, SH.sparql):
        select = g.value(sparql_node, SH.select)
        if not select:
            continue
        select_str = str(select)
        # Match patterns like ?rl < 1 || ?rl > 5
        for var, key in [("?rl", "required"), ("?al", "achieved")]:
            pattern = re.escape(var) + r'\s*<\s*(\d+)\s*\|\|\s*' + re.escape(var) + r'\s*>\s*(\d+)'
            m = re.search(pattern, select_str)
            if m:
                ranges[key] = (int(m.group(1)), int(m.group(2)))
    return ranges


def _extract_sh_in_values(g: Graph, shape_uri, property_path) -> list[str]:
    """Extract sh:in enum values for a specific property within a shape."""
    for prop_node in g.objects(shape_uri, SH.property):
        path = g.value(prop_node, SH.path)
        if path and str(path) == str(property_path):
            in_list = g.value(prop_node, SH["in"])
            if in_list:
                return [str(v) for v in _collect_list(g, in_list)]
    return []


def _extract_sh_range(g: Graph, shape_uri, property_path) -> tuple[int, int] | None:
    """Extract sh:minInclusive/sh:maxInclusive for a property within a shape."""
    for prop_node in g.objects(shape_uri, SH.property):
        path = g.value(prop_node, SH.path)
        if path and str(path) == str(property_path):
            lo = g.value(prop_node, SH.minInclusive)
            hi = g.value(prop_node, SH.maxInclusive)
            if lo is not None and hi is not None:
                return (int(float(str(lo))), int(float(str(hi))))
    return None


def _extract_evidence_types(g: Graph) -> list[str]:
    """Extract evidence class names from sh:targetClass declarations."""
    evidence_shapes = [
        UOFA.ReviewActivityShape,
        UOFA.ProcessAttestationShape,
        UOFA.DeploymentRecordShape,
        UOFA.InputPedigreeLinkShape,
    ]
    types = ["ValidationResult"]  # always present as default
    for shape in evidence_shapes:
        for cls in g.objects(shape, SH.targetClass):
            local = str(cls).rsplit("#", 1)[-1]
            if local not in types:
                types.append(local)
    return types


def _generate_python_constants(shacl_paths: list[Path]) -> str:
    """Generate Python constants module from SHACL shapes."""
    g = Graph()
    source_files = []
    for p in shacl_paths:
        if p.exists():
            g.parse(str(p), format="turtle")
            source_files.append(str(p))

    # ── Core shape extractions ───────────────────────────────
    factor_statuses = _extract_sh_in_values(g, UOFA.CredibilityFactorShape, UOFA.factorStatus)
    assessment_phases = _extract_sh_in_values(g, UOFA.CredibilityFactorShape, UOFA.assessmentPhase)
    core_level_range = _extract_sh_range(g, UOFA.CredibilityFactorShape, UOFA.requiredLevel)
    decision_outcomes = _extract_sh_in_values(g, UOFA.UnitOfAssurance_CompleteBody, UOFA.decision)
    device_classes = _extract_sh_in_values(g, UOFA.UnitOfAssurance_CompleteBody, UOFA.deviceClass)
    assurance_levels = _extract_sh_in_values(g, UOFA.UnitOfAssurance_CompleteBody, UOFA.assuranceLevel)
    mrl_range = _extract_sh_range(g, UOFA.UnitOfAssurance_CompleteBody, UOFA.modelRiskLevel)
    evidence_types = _extract_evidence_types(g)

    # Profile URIs from sh:in on conformsToProfile
    profile_uris = _extract_sh_in_values(g, UOFA.UnitOfAssurance_ProfileShape, UOFA.conformsToProfile)
    profiles = [u.rsplit("#Profile", 1)[-1] for u in profile_uris if "#Profile" in u]

    # ── VV40 pack extractions ────────────────────────────────
    vv40_factors = _extract_sparql_not_in(g, UOFA.VV40CredibilityFactorShape)
    vv40_ranges = _extract_sparql_level_range(g, UOFA.VV40LevelRangeShape)
    vv40_level_range = vv40_ranges.get("required", (1, 5))

    # ── NASA pack extractions ────────────────────────────────
    nasa_all_factors = _extract_sparql_not_in(g, UOFA.NASA7009BCredibilityFactorShape)
    nasa_ranges = _extract_sparql_level_range(g, UOFA.NASA7009BLevelRangeShape)
    nasa_level_range = nasa_ranges.get("required", (0, 4))

    # NASA-only = all NASA minus VV40
    vv40_set = set(vv40_factors)
    nasa_only_factors = [f for f in nasa_all_factors if f not in vv40_set]

    # ── Format Python source ─────────────────────────────────
    def _fmt_list(items, indent=4):
        if not items:
            return "[]"
        lines = ["["]
        for item in items:
            lines.append(f'{" " * indent}"{item}",')
        lines.append("]")
        return "\n".join(lines)

    def _fmt_tuple_list(pairs, indent=4):
        """Format list of (name, category) tuples."""
        if not pairs:
            return "[]"
        lines = ["["]
        for name, cat in pairs:
            lines.append(f'{" " * indent}("{name}", "{cat}"),')
        lines.append("]")
        return "\n".join(lines)

    source_list = "\n".join(f"#     {s}" for s in source_files)

    lines = []
    lines.append('"""Excel import constants — generated from SHACL shapes.')
    lines.append("")
    lines.append("DO NOT EDIT the SHACL-derived section below. Regenerate with:")
    lines.append("    uofa schema --emit python -o src/uofa_cli/excel_constants.py")
    lines.append("")
    lines.append("Source shapes:")
    for s in source_files:
        lines.append(f"    {s}")
    lines.append('"""')
    lines.append("")
    lines.append("# ── SHACL-derived constants (do not edit) ─────────────────────")
    lines.append("")
    lines.append(f"VV40_FACTOR_NAMES: list[str] = {_fmt_list(vv40_factors)}")
    lines.append("")
    lines.append(f"NASA_ALL_FACTOR_NAMES: list[str] = {_fmt_list(nasa_all_factors)}")
    lines.append("")
    lines.append(f"NASA_ONLY_FACTOR_NAMES: list[str] = {_fmt_list(nasa_only_factors)}")
    lines.append("")
    lines.append(f"VV40_LEVEL_RANGE: tuple[int, int] = {vv40_level_range}")
    lines.append(f"NASA_LEVEL_RANGE: tuple[int, int] = {nasa_level_range}")
    lines.append(f"CORE_LEVEL_RANGE: tuple[int, int] = {core_level_range or (0, 5)}")
    lines.append(f"MRL_RANGE: tuple[int, int] = {mrl_range or (1, 5)}")
    lines.append("")
    lines.append(f"VALID_FACTOR_STATUSES: list[str] = {_fmt_list(factor_statuses)}")
    lines.append("")
    lines.append(f"VALID_ASSESSMENT_PHASES: list[str] = {_fmt_list(assessment_phases)}")
    lines.append("")
    lines.append(f"VALID_DECISION_OUTCOMES: list[str] = {_fmt_list(decision_outcomes)}")
    lines.append("")
    lines.append(f"VALID_DEVICE_CLASSES: list[str] = {_fmt_list(device_classes)}")
    lines.append("")
    lines.append(f"VALID_ASSURANCE_LEVELS: list[str] = {_fmt_list(assurance_levels)}")
    lines.append("")
    lines.append(f"VALID_PROFILES: list[str] = {_fmt_list(profiles)}")
    lines.append("")
    lines.append(f"EVIDENCE_TYPES: list[str] = {_fmt_list(evidence_types)}")
    lines.append("")
    lines.append("")
    lines.append("# ── Excel-specific constants (hand-maintained) ────────────────")
    lines.append("")
    lines.append('SHEET_NAMES: dict[str, str] = {')
    lines.append('    "summary": "Assessment Summary",')
    lines.append('    "model_data": "Model & Data",')
    lines.append('    "validation": "Validation Results",')
    lines.append('    "factors": "Credibility Factors",')
    lines.append('    "decision": "Decision",')
    lines.append("}")
    lines.append("")
    lines.append("# Row/column layout for each sheet")
    lines.append("HEADER_ROW = 3          # Row with column headers (rows 1-2 are title + instructions)")
    lines.append("DATA_START_ROW = 4      # First data row for Model & Data, Validation Results")
    lines.append("FACTOR_START_ROW = 5    # First factor data row in Credibility Factors")
    lines.append("")
    lines.append("# Factor type -> display category (for Excel template grouping)")
    lines.append(f"VV40_FACTOR_CATEGORIES: list[tuple[str, str]] = {_fmt_tuple_list(_vv40_categories())}")
    lines.append("")
    lines.append(f"NASA_ONLY_FACTOR_CATEGORIES: list[tuple[str, str]] = {_fmt_tuple_list(_nasa_categories())}")
    lines.append("")
    lines.append("ALL_FACTOR_CATEGORIES: list[tuple[str, str]] = VV40_FACTOR_CATEGORIES + NASA_ONLY_FACTOR_CATEGORIES")
    lines.append("")
    lines.append("# NASA category -> assessmentPhase mapping")
    lines.append('NASA_PHASE_MAP: dict[str, str] = {')
    lines.append('    "NASA \\u2014 Capability": "capability",')
    lines.append('    "NASA \\u2014 Results": "results",')
    lines.append("}")
    lines.append("")
    lines.append("# Profile name -> JSON-LD URI")
    lines.append('PROFILE_URIS: dict[str, str] = {')
    lines.append('    "Minimal": "https://uofa.net/vocab#ProfileMinimal",')
    lines.append('    "Complete": "https://uofa.net/vocab#ProfileComplete",')
    lines.append("}")
    lines.append("")
    lines.append("# Factor standard assignment")
    lines.append('FACTOR_STANDARD_VV40 = "ASME-VV40-2018"')
    lines.append('FACTOR_STANDARD_NASA = "NASA-STD-7009B"')
    lines.append("")
    lines.append('CONTEXT_URL = "https://raw.githubusercontent.com/cloudronin/uofa/main/spec/context/v0.4.jsonld"')
    lines.append('BASE_URI = "https://uofa.net/instances"')
    lines.append("")

    return "\n".join(lines)


def _vv40_categories():
    """VV40 factor (name, category) pairs — hand-maintained."""
    return [
        ("Software quality assurance", "Verification \u2014 Code"),
        ("Numerical code verification", "Verification \u2014 Code"),
        ("Discretization error", "Verification \u2014 Calculation"),
        ("Numerical solver error", "Verification \u2014 Calculation"),
        ("Use error", "Verification \u2014 Calculation"),
        ("Model form", "Validation \u2014 Model"),
        ("Model inputs", "Validation \u2014 Model"),
        ("Test samples", "Validation \u2014 Comparator"),
        ("Test conditions", "Validation \u2014 Comparator"),
        ("Equivalency of input parameters", "Validation \u2014 Assessment"),
        ("Output comparison", "Validation \u2014 Assessment"),
        ("Relevance of the quantities of interest", "Applicability"),
        ("Relevance of the validation activities to the COU", "Applicability"),
    ]


def _nasa_categories():
    """NASA-only factor (name, category) pairs — hand-maintained."""
    return [
        ("Data pedigree", "NASA \u2014 Capability"),
        ("Development technical review", "NASA \u2014 Capability"),
        ("Development process and product management", "NASA \u2014 Capability"),
        ("Results uncertainty", "NASA \u2014 Results"),
        ("Results robustness", "NASA \u2014 Results"),
        ("Use history", "NASA \u2014 Capability"),
    ]


def run(args) -> int:
    if args.emit == "python":
        return _run_python(args)
    return _run_json(args)


def _run_python(args) -> int:
    """Generate Python constants from SHACL shapes (core + all packs)."""
    step_header("Generating Python constants from SHACL shapes")

    shacl_files = paths.all_shacl_schemas()
    # Also load any pack shapes not in active packs (we want all packs)
    root = paths.find_repo_root()
    for pack_name in paths.list_packs(root):
        try:
            manifest = paths.pack_manifest(pack_name, root=root)
            shapes_rel = manifest.get("shapes")
            if shapes_rel:
                shapes_path = paths.pack_dir(pack_name, root=root) / shapes_rel
                if shapes_path.exists() and shapes_path not in shacl_files:
                    shacl_files.append(shapes_path)
        except (FileNotFoundError, KeyError):
            pass

    source = _generate_python_constants(shacl_files)

    output = args.output or (root / "src" / "uofa_cli" / "excel_constants.py")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(source)

    result_line("Constants generated", True, str(output))
    info(f"  Source shapes: {len(shacl_files)} files")
    info(f"  Regenerate after SHACL changes: uofa schema --emit python")

    return 0


def _run_json(args) -> int:
    """Generate JSON Schema from SHACL shapes (existing behavior)."""
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

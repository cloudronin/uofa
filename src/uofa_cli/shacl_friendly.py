"""Translate SHACL validation results into user-friendly messages."""

from pathlib import Path

from pyshacl import validate as shacl_validate
from rdflib import Graph, Namespace, URIRef

from uofa_cli.output import color, severity_badge, result_line, info

SH = Namespace("http://www.w3.org/ns/shacl#")
UOFA = Namespace("https://uofa.net/vocab#")
PROV = Namespace("http://www.w3.org/ns/prov#")

# ── Fix suggestions keyed on the property path IRI ───────────

_FIX_SUGGESTIONS = {
    str(UOFA.bindsRequirement):    "Add an IRI linking to the requirement this UofA substantiates.",
    str(UOFA.hasContextOfUse):     "Every UofA must declare a V&V 40 Context of Use.",
    str(UOFA.hasValidationResult): "Add at least one validation result IRI.",
    str(UOFA.hasDecisionRecord):   "Add a DecisionRecord with actor, outcome, and rationale.",
    str(UOFA.bindsModel):          "Add an IRI identifying the computational model assessed.",
    str(UOFA.bindsDataset):        "Add IRI(s) for the dataset(s) used in validation.",
    str(UOFA.hasCredibilityFactor): "Add at least one CredibilityFactor with factorType, requiredLevel, achievedLevel.",
    str(UOFA.conformsToProfile):   "Set conformsToProfile to ProfileMinimal or ProfileComplete.",
    str(UOFA.hash):                "Run `uofa sign FILE --key KEY` to generate a valid hash.",
    str(UOFA.signature):           "Run `uofa sign FILE --key KEY` to generate a valid signature.",
    str(UOFA.factorType):          "Must be a valid factor name for the active pack (use --pack to select).",
    str(UOFA.requiredLevel):       "Must be an integer 1-5.",
    str(UOFA.achievedLevel):       "Must be an integer 1-5.",
    str(UOFA.assuranceLevel):      "Must be Low, Medium, or High.",
    str(UOFA.patternId):           "Must match pattern W-XX-NN (e.g., W-EP-01).",
    str(UOFA.severity):            "Must be Critical, High, Medium, or Low.",
    str(PROV.generatedAtTime):     "Add an ISO 8601 timestamp (e.g., 2026-01-15T00:00:00Z).",
    str(PROV.wasDerivedFrom):      "Link to the prior artifact (report, DOI, or parent UofA).",
    str(PROV.wasAttributedTo):     "Identify the responsible actor or organization.",
}

# Severity assignment based on property path
_PROPERTY_SEVERITY = {
    str(UOFA.hash):       "Critical",
    str(UOFA.signature):  "Critical",
    str(UOFA.conformsToProfile): "Critical",
    str(UOFA.hasContextOfUse):   "High",
    str(UOFA.bindsRequirement):  "High",
    str(UOFA.hasDecisionRecord): "High",
}


def run_shacl_multi(data_path: Path, shacl_paths: list) -> tuple[bool, list[dict]]:
    """Run SHACL validation with multiple shape files and return (conforms, violations)."""
    if len(shacl_paths) == 1:
        return run_shacl(data_path, shacl_paths[0])

    combined = Graph()
    for p in shacl_paths:
        combined.parse(str(p), format="turtle")

    return _run_shacl_graph(data_path, combined)


def run_shacl(data_path: Path, shacl_path: Path) -> tuple[bool, list[dict]]:
    """Run SHACL validation and return (conforms, violations).

    Each violation is a dict with keys: path, message, fix, severity.
    """
    conforms, results_graph, results_text = shacl_validate(
        data_graph=str(data_path),
        shacl_graph=str(shacl_path),
        data_graph_format="json-ld",
    )

    if conforms:
        return True, []

    violations = []
    for result in results_graph.subjects(SH.resultSeverity, None):
        path_node = results_graph.value(result, SH.resultPath)
        message_node = results_graph.value(result, SH.resultMessage)
        component_node = results_graph.value(result, SH.sourceConstraintComponent)
        source_node = results_graph.value(result, SH.sourceShape)

        path_str = str(path_node) if path_node else ""
        message = str(message_node) if message_node else "Validation failed"
        component = str(component_node) if component_node else ""
        source = str(source_node) if source_node else ""

        # Handle the sh:or dispatcher violation specially
        if "OrConstraintComponent" in component and "ProfileShape" in source:
            violations.append({
                "path": "Profile",
                "message": "Required fields for the declared profile are missing.",
                "fix": "Check that all required fields for your profile are present. "
                       "Run `uofa shacl FILE --raw` for details.",
                "severity": "Critical",
            })
            continue

        # Extract the local name from the path URI for display
        path_label = path_str.rsplit("#", 1)[-1].rsplit("/", 1)[-1] if path_str else "unknown"

        fix = _FIX_SUGGESTIONS.get(path_str, "")
        severity = _PROPERTY_SEVERITY.get(path_str, "Medium")

        violations.append({
            "path": path_label,
            "message": message,
            "fix": fix,
            "severity": severity,
        })

    # Sort by severity: Critical first
    severity_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
    violations.sort(key=lambda v: severity_order.get(v["severity"], 4))

    return False, violations


def _run_shacl_graph(data_path: Path, shacl_graph) -> tuple[bool, list[dict]]:
    """Run SHACL validation with a pre-built shapes Graph."""
    conforms, results_graph, results_text = shacl_validate(
        data_graph=str(data_path),
        shacl_graph=shacl_graph,
        data_graph_format="json-ld",
    )

    if conforms:
        return True, []

    violations = []
    for result in results_graph.subjects(SH.resultSeverity, None):
        path_node = results_graph.value(result, SH.resultPath)
        message_node = results_graph.value(result, SH.resultMessage)
        component_node = results_graph.value(result, SH.sourceConstraintComponent)
        source_node = results_graph.value(result, SH.sourceShape)

        path_str = str(path_node) if path_node else ""
        message = str(message_node) if message_node else "Validation failed"
        component = str(component_node) if component_node else ""
        source = str(source_node) if source_node else ""

        if "OrConstraintComponent" in component and "ProfileShape" in source:
            violations.append({
                "path": "Profile",
                "message": "Required fields for the declared profile are missing.",
                "fix": "Check that all required fields for your profile are present. "
                       "Run `uofa shacl FILE --raw` for details.",
                "severity": "Critical",
            })
            continue

        path_label = path_str.rsplit("#", 1)[-1].rsplit("/", 1)[-1] if path_str else "unknown"
        fix = _FIX_SUGGESTIONS.get(path_str, "")
        severity = _PROPERTY_SEVERITY.get(path_str, "Medium")

        violations.append({
            "path": path_label,
            "message": message,
            "fix": fix,
            "severity": severity,
        })

    severity_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
    violations.sort(key=lambda v: severity_order.get(v["severity"], 4))

    return False, violations


def print_violations(violations: list[dict]):
    """Print formatted violation messages."""
    for v in violations:
        badge = severity_badge(v["severity"])
        path = color(v["path"], "bold")
        print(f"  {badge} {path}: {v['message']}")
        if v["fix"]:
            print(f"         {color('Fix:', 'cyan')} {v['fix']}")


def print_results(conforms: bool, violations: list[dict]):
    """Print SHACL validation results with friendly formatting."""
    if conforms:
        result_line("SHACL validation", True, "Conforms")
    else:
        result_line("SHACL validation", False, f"{len(violations)} violation(s)")
        print()
        print_violations(violations)

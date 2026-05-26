"""Translate SHACL validation results into user-friendly messages."""

from __future__ import annotations

from pathlib import Path

from pyshacl import validate as shacl_validate
from rdflib import Graph, Namespace, URIRef

from uofa_cli.output import color, severity_badge, result_line, info

SH = Namespace("http://www.w3.org/ns/shacl#")
UOFA = Namespace("https://uofa.net/vocab#")
PROV = Namespace("http://www.w3.org/ns/prov#")

# Profile-body shape IRIs used by the OR-constraint drill-in. The wrapper
# ``UnitOfAssurance_ProfileShape`` declares an sh:or with these two branches;
# pyshacl rolls all inner failures into a single OrConstraintComponent
# violation. We re-validate against the specific body shape the doc claimed
# to surface the actual missing/invalid fields.
_PROFILE_BODY_SHAPES = {
    str(UOFA.ProfileComplete): str(UOFA.UnitOfAssurance_CompleteBody),
    str(UOFA.ProfileMinimal):  str(UOFA.UnitOfAssurance_MinimalBody),
}

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


import threading

# Phase 2.5 v0.5.15.1: pyshacl + rdflib are NOT thread-safe under
# concurrent calls in the same process. The adversarial runner uses
# ``ThreadPoolExecutor`` (runner.py:514) for parallel spec generation;
# under high concurrency (parallel >= 5) every SHACL call returns
# spurious ``conforms=False`` with empty violations, causing the runner
# to incorrectly mark every variant as SHACL-failing. Phase B.9
# validation surfaced this with v0.5.15 tool-use because faster LLM
# responses tightened the SHACL-call window — pre-v0.5.15's slower
# free-form generation had wider gaps between SHACL calls and
# experienced the bug at much lower frequency.
#
# Fix: serialize SHACL calls via a module-level lock. The LLM call
# remains parallel; only the SHACL validation step is serialized.
# Performance impact is minimal (SHACL takes ~50-200ms per package
# vs ~30-90s LLM call) but correctness is restored.
#
# RLock (reentrant) so run_shacl_multi can call run_shacl without
# self-deadlock when only one shacl_path is provided.
_SHACL_LOCK = threading.RLock()


def run_shacl_multi(data_path: Path, shacl_paths: list) -> tuple[bool, list[dict]]:
    """Run SHACL validation with multiple shape files and return (conforms, violations).

    Thread-safe: serializes pyshacl/rdflib calls via _SHACL_LOCK to avoid
    cross-thread state corruption (Phase 2.5 v0.5.15.1 fix).
    """
    with _SHACL_LOCK:
        if len(shacl_paths) == 1:
            return run_shacl(data_path, shacl_paths[0])

        combined = Graph()
        for p in shacl_paths:
            combined.parse(str(p), format="turtle")

        return _run_shacl_graph(data_path, combined)


def _shape_local_name(component_iri: str) -> str:
    """Extract the local name from a SHACL constraint-component IRI.

    E.g. ``http://www.w3.org/ns/shacl#MinCountConstraintComponent`` → ``MinCount``.
    """
    local = component_iri.rsplit("#", 1)[-1]
    return local[: -len("ConstraintComponent")] if local.endswith("ConstraintComponent") else local


def _describe_constraint(component_iri: str, result_node, results_graph: Graph,
                          shacl_graph: Graph, path_iri: str) -> str:
    """Build a one-line 'Required:' description for a violation.

    Reads constraint-specific properties off the source-shape definition in
    the SHACL graph (e.g. sh:minCount, sh:nodeKind, sh:pattern, sh:in,
    sh:datatype) so the message reflects what the shape actually demands —
    not just a generic 'constraint failed' string.
    """
    kind = _shape_local_name(component_iri)
    # The source shape on the result is usually the *property shape* (a
    # blank node); pull the per-property constraint values from that node.
    source_shape = results_graph.value(result_node, SH.sourceShape)
    if source_shape is None:
        return kind

    def _g(predicate):
        return shacl_graph.value(source_shape, predicate)

    if kind == "MinCount":
        n = _g(SH.minCount)
        return f"minCount {n}" if n is not None else "at least one value"
    if kind == "MaxCount":
        n = _g(SH.maxCount)
        return f"maxCount {n}" if n is not None else "at most one value"
    if kind == "NodeKind":
        nk = _g(SH.nodeKind)
        nk_local = str(nk).rsplit("#", 1)[-1] if nk else "IRI"
        return f"value must be a {nk_local}"
    if kind == "Datatype":
        dt = _g(SH.datatype)
        return f"datatype {str(dt).rsplit('#', 1)[-1]}" if dt else "specific datatype"
    if kind == "Pattern":
        pattern = _g(SH.pattern)
        return f"matches pattern {pattern!s}" if pattern else "matches a pattern"
    if kind == "In":
        # sh:in points at an RDF list; collect its members
        in_node = _g(SH["in"])
        if in_node is not None:
            from rdflib.collection import Collection
            items = list(Collection(shacl_graph, in_node))
            return "one of " + "{" + ", ".join(str(x) for x in items) + "}"
        return "one of an enumerated set"
    if kind == "MinInclusive":
        v = _g(SH.minInclusive)
        return f"≥ {v}"
    if kind == "MaxInclusive":
        v = _g(SH.maxInclusive)
        return f"≤ {v}"
    if kind == "HasValue":
        v = _g(SH.hasValue)
        return f"must equal {v}"
    # Fallback: surface the constraint-kind name for any unhandled type.
    return kind


def _format_actual(value_node, path_iri: str, kind: str) -> str:
    """Format the actual value found at the failing path.

    sh:value is omitted in pyshacl reports for MinCount violations (because
    nothing was found at that path); report it as MISSING. For other
    constraint types, return the string form of the value.
    """
    if value_node is None or kind == "MinCount":
        return "MISSING"
    return str(value_node)


def _smart_fix(path_iri: str, component_iri: str, actual: str) -> str:
    """Compose a fix suggestion targeted to the constraint type.

    Prefers a path-specific suggestion (from _FIX_SUGGESTIONS) when one
    exists; falls back to a constraint-type-specific template otherwise.
    """
    if path_iri in _FIX_SUGGESTIONS:
        return _FIX_SUGGESTIONS[path_iri]
    kind = _shape_local_name(component_iri)
    if kind == "MinCount":
        return "Add this field to the xlsx and re-import."
    if kind == "NodeKind" and "literal" not in actual.lower():
        return f"Provide a valid IRI; got literal {actual!r}. Check the source xlsx for placeholder text."
    if kind == "In":
        return f"Edit the cell to exactly one of the allowed values (got {actual!r})."
    if kind == "Pattern":
        return f"Edit to match the expected pattern (got {actual!r})."
    return ""


def _drill_into_or_failure(data_g: Graph, shacl_graph) -> list[dict]:
    """Surface inner constraint failures hidden behind the profile-OR.

    The UnitOfAssurance_ProfileShape wraps the body shapes in an sh:or, so
    pyshacl collapses all inner failures into a single OrConstraintComponent
    violation. We sidestep that by directly walking the property shapes of
    whichever body shape the document claims via conformsToProfile, then
    evaluating each property's constraints against the data graph ourselves.

    pyshacl's own re-validation via use_shapes turned out to be too
    restrictive (the body shape references other shapes that get filtered
    out, producing an internal "Shape pointed to by sh:node does not exist"
    error). Manual constraint walking is more reliable here because the
    set of constraint kinds we need is small and well-defined.

    Returns a list of enriched violation dicts (path, requirement, actual,
    fix, severity, profile). Falls back to the legacy single-line rollup
    when drill-in isn't possible (no conformsToProfile in doc, unknown
    profile, no UofA instance, body shape not found).
    """
    # rdflib's Graph.value(predicate=..., subject=None) is flaky on JSON-LD-
    # imported graphs; iterate via objects() which is unambiguous.
    profile_iri = next(iter(data_g.objects(predicate=UOFA.conformsToProfile)), None)
    profile_iri = str(profile_iri) if profile_iri is not None else None
    target_iri = _PROFILE_BODY_SHAPES.get(profile_iri) if profile_iri else None
    if not target_iri:
        return [_or_rollup_violation()]

    # Normalize shacl_graph to a Graph so we can introspect property shapes.
    if isinstance(shacl_graph, Graph):
        shapes_g = shacl_graph
    else:
        shapes_g = Graph()
        shapes_g.parse(str(shacl_graph), format="turtle")

    from rdflib import RDF, URIRef
    focus_nodes = list(data_g.subjects(RDF.type, UOFA.UnitOfAssurance))
    if not focus_nodes:
        return [_or_rollup_violation()]
    focus = focus_nodes[0]  # one UofA per document; if multiple, validate the first

    target_ref = URIRef(target_iri)
    if (target_ref, RDF.type, SH.NodeShape) not in shapes_g and \
       not any(shapes_g.triples((target_ref, SH.property, None))):
        return [_or_rollup_violation()]

    profile_label = profile_iri.rsplit("#", 1)[-1] if profile_iri else "unknown"
    inner: list[dict] = []
    for prop_shape in shapes_g.objects(target_ref, SH.property):
        viol = _check_property_shape(focus, prop_shape, shapes_g, data_g, profile_label)
        if viol is not None:
            inner.append(viol)

    if not inner:
        return [_or_rollup_violation()]

    severity_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
    inner.sort(key=lambda v: severity_order.get(v["severity"], 4))
    return inner


def _check_property_shape(focus, prop_shape, shapes_g: Graph, data_g: Graph,
                          profile_label: str) -> dict | None:
    """Check one sh:property shape against the focus node; return a
    violation dict or None if all constraints on this property pass.

    Reports the FIRST constraint failure for the property (per pyshacl's
    behavior). Covers the constraint types this codebase's shapes use:
    minCount, nodeKind, datatype, pattern, sh:in, minInclusive,
    maxInclusive, maxCount.
    """
    from rdflib import Literal, URIRef
    from rdflib.collection import Collection

    path = shapes_g.value(prop_shape, SH.path)
    if path is None:
        return None
    path_iri = str(path)
    path_label = path_iri.rsplit("#", 1)[-1].rsplit("/", 1)[-1]

    values = list(data_g.objects(focus, path))
    severity = _PROPERTY_SEVERITY.get(path_iri, "High")

    def viol(requirement: str, actual: str, component: str) -> dict:
        return {
            "path": path_label,
            "requirement": requirement,
            "actual": actual,
            "fix": _smart_fix(path_iri, component, actual),
            "severity": severity,
            "profile": profile_label,
        }

    # minCount: how many values are present at this path
    min_count = shapes_g.value(prop_shape, SH.minCount)
    if min_count is not None and len(values) < int(min_count):
        return viol(f"minCount {int(min_count)}", "MISSING",
                    "http://www.w3.org/ns/shacl#MinCountConstraintComponent")

    # No values + no minCount → the property is optional and absent; pass.
    if not values:
        return None

    # The constraints below apply per-value; report the first value that
    # fails (matches pyshacl behavior on this codebase's shapes).
    max_count = shapes_g.value(prop_shape, SH.maxCount)
    if max_count is not None and len(values) > int(max_count):
        return viol(f"maxCount {int(max_count)}", f"{len(values)} values found",
                    "http://www.w3.org/ns/shacl#MaxCountConstraintComponent")

    node_kind = shapes_g.value(prop_shape, SH.nodeKind)
    if node_kind is not None:
        nk_local = str(node_kind).rsplit("#", 1)[-1]
        for v in values:
            if nk_local == "IRI" and not isinstance(v, URIRef):
                return viol("value must be an IRI", _value_repr(v),
                            "http://www.w3.org/ns/shacl#NodeKindConstraintComponent")
            if nk_local == "Literal" and not isinstance(v, Literal):
                return viol("value must be a Literal", _value_repr(v),
                            "http://www.w3.org/ns/shacl#NodeKindConstraintComponent")

    datatype = shapes_g.value(prop_shape, SH.datatype)
    if datatype is not None:
        from rdflib.namespace import XSD
        dt_local = str(datatype).rsplit("#", 1)[-1]
        for v in values:
            if not isinstance(v, Literal):
                return viol(f"datatype {dt_local}", _value_repr(v),
                            "http://www.w3.org/ns/shacl#DatatypeConstraintComponent")
            # Per RDF 1.1, plain literals (datatype=None) are implicitly
            # xsd:string. pyshacl's sh:datatype xsd:string accepts them.
            if v.datatype is None and str(datatype) == str(XSD.string):
                continue
            if str(v.datatype or "") != str(datatype):
                return viol(f"datatype {dt_local}", _value_repr(v),
                            "http://www.w3.org/ns/shacl#DatatypeConstraintComponent")

    pattern = shapes_g.value(prop_shape, SH.pattern)
    if pattern is not None:
        import re
        rx = re.compile(str(pattern))
        for v in values:
            if not rx.match(str(v)):
                return viol(f"matches pattern {pattern}", _value_repr(v),
                            "http://www.w3.org/ns/shacl#PatternConstraintComponent")

    in_list = shapes_g.value(prop_shape, SH["in"])
    if in_list is not None:
        allowed = [str(x) for x in Collection(shapes_g, in_list)]
        for v in values:
            if str(v) not in allowed:
                return viol("one of {" + ", ".join(allowed) + "}", _value_repr(v),
                            "http://www.w3.org/ns/shacl#InConstraintComponent")

    min_incl = shapes_g.value(prop_shape, SH.minInclusive)
    if min_incl is not None:
        for v in values:
            try:
                if float(v) < float(min_incl):
                    return viol(f"≥ {min_incl}", _value_repr(v),
                                "http://www.w3.org/ns/shacl#MinInclusiveConstraintComponent")
            except (TypeError, ValueError):
                pass

    max_incl = shapes_g.value(prop_shape, SH.maxInclusive)
    if max_incl is not None:
        for v in values:
            try:
                if float(v) > float(max_incl):
                    return viol(f"≤ {max_incl}", _value_repr(v),
                                "http://www.w3.org/ns/shacl#MaxInclusiveConstraintComponent")
            except (TypeError, ValueError):
                pass

    return None


def _value_repr(v) -> str:
    """One-line preview of an rdflib value for the 'Actual:' display."""
    s = str(v)
    return s if len(s) <= 80 else s[:77] + "..."


def _or_rollup_violation() -> dict:
    """Legacy fallback when drill-in can't recover specifics."""
    return {
        "path": "Profile",
        "message": "Required fields for the declared profile are missing.",
        "fix": "Check that all required fields for your profile are present. "
               "Run `uofa shacl FILE --raw` for details.",
        "severity": "Critical",
    }


def _load_data_graph(data_path: Path) -> Graph:
    """Pre-parse a JSON-LD data file into an rdflib Graph.

    Workaround for a pyshacl ↔ rdflib interaction bug: when pyshacl is
    given ``data_graph=<path-string>`` it routes the file through an
    internal IO[bytes] stream that is sometimes consumed before
    rdflib's JSON-LD parser reads it, surfacing as
    ``orjson.JSONDecodeError: unexpected character: line 1 column 1
    (char 0)`` even though the file is non-empty and valid. Loading
    the data graph with rdflib directly first, then handing the
    parsed Graph to pyshacl, is reliable.
    """
    g = Graph()
    g.parse(str(data_path), format="json-ld")
    return g


def run_shacl(data_path: Path, shacl_path: Path) -> tuple[bool, list[dict]]:
    """Run SHACL validation and return (conforms, violations).

    Each violation is a dict with keys: path, message, fix, severity.

    Note: when called from ``run_shacl_multi`` the lock is already held;
    this internal acquire is reentrant-friendly because callers either
    use the multi-path (lock held) or the single-path (no concurrent
    callers from runner). The ``with`` here makes the function safe
    to call directly from external code (CLI, tests).
    """
    with _SHACL_LOCK:
        return _run_shacl_locked(data_path, shacl_path)


def _run_shacl_locked(data_path: Path, shacl_path: Path) -> tuple[bool, list[dict]]:
    data_g = _load_data_graph(data_path)
    # Pre-parse the shacl file once — we may need to re-validate against a
    # subset of shapes for the OR-constraint drill-in.
    shacl_g = Graph()
    shacl_g.parse(str(shacl_path), format="turtle")
    conforms, results_graph, results_text = shacl_validate(
        data_graph=data_g,
        shacl_graph=shacl_g,
    )

    if conforms:
        return True, []

    violations = _collect_violations(data_g, results_graph, shacl_g)
    return False, violations


def _run_shacl_graph(data_path: Path, shacl_graph) -> tuple[bool, list[dict]]:
    """Run SHACL validation with a pre-built shapes Graph.

    Uses :func:`_load_data_graph` to side-step the pyshacl path-loading bug.
    """
    data_g = _load_data_graph(data_path)
    conforms, results_graph, results_text = shacl_validate(
        data_graph=data_g,
        shacl_graph=shacl_graph,
    )

    if conforms:
        return True, []

    violations = _collect_violations(data_g, results_graph, shacl_graph)
    return False, violations


def _collect_violations(data_g: Graph, results_graph: Graph,
                        shacl_graph) -> list[dict]:
    """Walk pyshacl's ValidationResults and produce the violations list.

    For the OR-constraint dispatcher on UnitOfAssurance_ProfileShape, drill
    into the specific profile body shape the document claims so the inner
    failures (missing fields, bad IRIs, off-enum values) are surfaced
    rather than collapsed into a single "required fields missing" message.
    """
    violations: list[dict] = []
    for result in results_graph.subjects(SH.resultSeverity, None):
        path_node = results_graph.value(result, SH.resultPath)
        message_node = results_graph.value(result, SH.resultMessage)
        component_node = results_graph.value(result, SH.sourceConstraintComponent)
        source_node = results_graph.value(result, SH.sourceShape)

        path_str = str(path_node) if path_node else ""
        message = str(message_node) if message_node else "Validation failed"
        component = str(component_node) if component_node else ""
        source = str(source_node) if source_node else ""

        # OR-constraint on the profile dispatcher: drill into the specific
        # profile body shape declared by the document and surface its
        # inner failures (this is the load-bearing fix).
        if "OrConstraintComponent" in component and "ProfileShape" in source:
            violations.extend(_drill_into_or_failure(data_g, shacl_graph))
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
    return violations


def print_violations(violations: list[dict]):
    """Print formatted violation messages.

    Renders the drilled-in fields (requirement / actual / profile) when
    they are present, falling back to the legacy single-line format for
    pre-drill-in violations (e.g. those from non-OR constraint failures).
    """
    # If any violation carries a profile tag, prepend a single-line summary
    # so the user knows which body shape the inner failures came from.
    profile_tags = {v.get("profile") for v in violations if v.get("profile")}
    if profile_tags:
        tag = next(iter(profile_tags))
        print(f"  {color('Declared profile:', 'cyan')} {tag} — "
              f"{len([v for v in violations if v.get('profile')])} field(s) failed")
        print()

    for v in violations:
        badge = severity_badge(v["severity"])
        path = color(v["path"], "bold")
        # New (drilled-in) format: requirement + actual + fix.
        if "requirement" in v:
            print(f"  {badge} {path}")
            print(f"         {color('Required:', 'dim')} {v['requirement']}")
            print(f"         {color('Actual:  ', 'dim')} {v['actual']}")
            if v.get("fix"):
                print(f"         {color('Fix:     ', 'cyan')} {v['fix']}")
        else:
            # Legacy single-line format for non-drill-in violations.
            print(f"  {badge} {path}: {v.get('message', '')}")
            if v.get("fix"):
                print(f"         {color('Fix:', 'cyan')} {v['fix']}")


def print_results(conforms: bool, violations: list[dict]):
    """Print SHACL validation results with friendly formatting."""
    if conforms:
        result_line("SHACL validation", True, "Conforms")
    else:
        result_line("SHACL validation", False, f"{len(violations)} violation(s)")
        print()
        print_violations(violations)

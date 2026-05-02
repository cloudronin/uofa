"""Context extractors for interpretation prompts (spec v0.4 §4.3).

Each context bundle is the deterministic input to one LLM call. The
extractors operate on the structured outputs produced by the refactored
commands (`RulesResult.firings`, `DiffResult.weakeners_*`,
`ShaclResult.violations`) plus the package's parsed JSON-LD document.

Context dataclasses are frozen and JSON-serializable so they can be cached
by content hash (spec §4.7) without surprises.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


# ── Common context (every per-item prompt gets these) ──────


@dataclass(frozen=True)
class PackContext:
    """Pack metadata visible to the prompt template.

    Templates reference `pack.name`, `pack.standard`, `pack.profile`. The
    extractor pulls these from `pack.json` via `paths.pack_manifest`.
    """

    name: str
    standard: str | None = None     # e.g. "ASME-VV40-2018"
    profile: str | None = None      # e.g. "complete" | "minimal"


@dataclass(frozen=True)
class CouContext:
    """Context-of-Use metadata when present on the package."""

    name: str = ""
    description: str = ""
    device_class: str = ""
    model_risk_level: str = ""


# ── Per-item context bundles ────────────────────────────────


@dataclass(frozen=True)
class FiringContext:
    """Context for a single rule firing (spec §4.3 — rules / check).

    Two evidence-related fields populated by Round 1's enriched extractor:

    - `affected_evidence`: list of resolved-node summary dicts, one per
      `affected_node` IRI in the firing. Each summary carries `iri`, `kind`
      (e.g. "CredibilityFactor"), `label` (the human-readable name like
      "Use error" for a credibility factor), `status`, `levels`, and
      optional `description`. The prompt template iterates this list to
      tell the model exactly *what* fired — the SME-flagged gap from
      Round 0.
    - `constituent_firings`: for COMPOUND patterns, the resolved
      summaries of the constituent weakener firings that triggered the
      compound. Empty for non-compound patterns.

    `affected_node` (singular str) is preserved for back-compat with
    pre-Round-1 callers; it carries the first IRI when multiple
    affected nodes exist.
    """

    pattern_id: str
    severity: str
    hits: int
    affected_node: str = ""
    description: str = ""
    evidence_excerpt: str = ""
    pack: PackContext | None = None
    cou: CouContext | None = None
    # Round 1 (P-B iteration) additions:
    affected_evidence: tuple[dict, ...] = ()  # tuple for frozen dataclass; list-like for templates
    constituent_firings: tuple[dict, ...] = ()

    def to_template_vars(self) -> dict:
        """Flat namespace for Jinja2 template substitution.

        Spec §6.3 namespace: `firing`, `evidence`, `pack`, `cou`. The
        Round 1 prompt template iterates `firing.affected_evidence` (list
        of summary dicts) and `firing.constituent_firings` (list of
        compound-source summaries) directly. The legacy `evidence` scalar
        remains for templates that want a synthesized excerpt.
        """
        return {
            "firing": {
                "patternId": self.pattern_id,
                "severity": self.severity,
                "hits": self.hits,
                "affectedNode": self.affected_node,
                "description": self.description,
                "affected_evidence": list(self.affected_evidence),
                "constituent_firings": list(self.constituent_firings),
            },
            "evidence": self.evidence_excerpt,
            "pack": asdict(self.pack) if self.pack else {},
            "cou": asdict(self.cou) if self.cou else {},
        }


@dataclass(frozen=True)
class DifferenceContext:
    """Context for a single diff difference (spec §4.3 — diff)."""

    pattern_id: str
    severity: str
    only_in: str                # "A" | "B"
    cou_with: CouContext | None = None
    cou_without: CouContext | None = None
    description: str = ""       # from the .rules file when available
    pack: PackContext | None = None

    def to_template_vars(self) -> dict:
        return {
            "difference": {
                "patternId": self.pattern_id,
                "severity": self.severity,
                "onlyIn": self.only_in,
                "description": self.description,
            },
            "before": asdict(self.cou_without) if self.cou_without else {},
            "after": asdict(self.cou_with) if self.cou_with else {},
            "pack": asdict(self.pack) if self.pack else {},
        }


@dataclass(frozen=True)
class ViolationContext:
    """Context for a single SHACL violation (spec §4.3 — shacl)."""

    constraint_path: str        # e.g. "uofa:hasContextOfUse"
    severity: str
    affected_node: str
    expected: str = ""
    actual: str = ""
    description: str = ""       # constraint description / fix suggestion
    pack: PackContext | None = None

    def to_template_vars(self) -> dict:
        return {
            "violation": {
                "constraint": self.constraint_path,
                "severity": self.severity,
                "affectedNode": self.affected_node,
                "description": self.description,
            },
            "expected": self.expected,
            "actual": self.actual,
            "pack": asdict(self.pack) if self.pack else {},
        }


# ── Extractors ─────────────────────────────────────────────


def extract_pack_context(pack_name: str) -> PackContext:
    """Pull pack metadata from the active pack's manifest."""
    try:
        from uofa_cli import paths  # noqa: PLC0415
        manifest = paths.pack_manifest(pack_name)
        standards = manifest.get("standards") or []
        return PackContext(
            name=pack_name,
            standard=standards[0] if standards else None,
            profile=manifest.get("profile"),
        )
    except (FileNotFoundError, KeyError):
        return PackContext(name=pack_name)


def extract_cou_context(package_doc: dict) -> CouContext:
    """Pull COU identity from a parsed UofA JSON-LD document."""
    cou = package_doc.get("hasContextOfUse", {})
    if isinstance(cou, str):
        cou = {}
    name = cou.get("name", package_doc.get("name", "")) or ""
    description = cou.get("description", "") or ""

    # Cheap regex parses to match diff.py's identity extraction
    import re
    text = f"{name} {description}"
    device_class = ""
    m = re.search(r"Class\s+(I{1,3}V?)", text, re.IGNORECASE)
    if m:
        device_class = f"Class {m.group(1)}"
    model_risk_level = ""
    m = re.search(r"Model Risk Level\s+(\d+)", text, re.IGNORECASE)
    if m:
        model_risk_level = f"MRL {m.group(1)}"

    return CouContext(
        name=name,
        description=description,
        device_class=device_class,
        model_risk_level=model_risk_level,
    )


def extract_firing_contexts(
    firings: list[dict],
    package_doc: dict,
    pack_name: str,
    *,
    jsonld_firings: list[dict] | None = None,
    individual_annotations: list[dict] | None = None,
) -> list[FiringContext]:
    """Build FiringContexts from `RulesResult.firings` (summary parse) plus
    optional richer engine output for Round 1 evidence enrichment.

    Two-tier inputs:
    - `firings`: the summary-mode parse (patternId/severity/hits only).
      Always present.
    - `jsonld_firings`: from `rules.parse_firings_jsonld()`, one dict per
      patternId carrying `affected_nodes` (list of IRIs) and
      `escalation_sources` (for compounds). When provided, drives the
      `affected_evidence` field on the resulting FiringContexts.
    - `individual_annotations`: from `rules.parse_individual_annotations()`,
      one dict per individual annotation keyed by blank-node `id`. Used
      to resolve compound `escalation_sources` IRIs back to constituent
      firings. Required when populating `constituent_firings` for any
      COMPOUND-* pattern; optional otherwise.

    When `jsonld_firings` is None, behaves like the pre-Round-1 extractor
    (legacy path): only patternId/severity/hits/description. This keeps the
    standalone `uofa explain --from-file` flow working when callers pass a
    cached envelope without engine re-invocation data.
    """
    from uofa_cli.commands.rules import load_pattern_descriptions  # noqa: PLC0415

    pack = extract_pack_context(pack_name)
    cou = extract_cou_context(package_doc)
    pattern_descriptions = load_pattern_descriptions(pack_name)

    # Index the rich data by patternId for quick lookup against `firings`.
    jsonld_by_pid: dict[str, dict] = {}
    if jsonld_firings:
        jsonld_by_pid = {f["patternId"]: f for f in jsonld_firings if "patternId" in f}
    annotations_by_id: dict[str, dict] = {}
    if individual_annotations:
        annotations_by_id = {a["id"]: a for a in individual_annotations if a.get("id")}

    contexts: list[FiringContext] = []
    for f in firings:
        pid = str(f.get("patternId", ""))
        rich = jsonld_by_pid.get(pid, {})

        # Description preference: per-firing (engine in jsonld may carry one),
        # then pack-level from .rules file headers, then empty.
        description = (
            str(f.get("description", ""))
            or str(rich.get("description", ""))
            or pattern_descriptions.get(pid, "")
        )

        affected_iris: list[str] = list(rich.get("affected_nodes", []))
        affected_evidence = tuple(
            _summarize_node(_resolve_node_in_doc(package_doc, iri) or {"@id": iri, "id": iri})
            for iri in affected_iris
        )

        constituent_firings: tuple[dict, ...] = ()
        if pid.startswith("COMPOUND") and annotations_by_id:
            constituent_firings = tuple(
                _summarize_constituent(annotations_by_id[src_id], package_doc)
                for src_id in rich.get("escalation_sources", [])
                if src_id in annotations_by_id
            )

        contexts.append(FiringContext(
            pattern_id=pid,
            severity=str(f.get("severity", "Medium")),
            hits=int(f.get("hits", 0)),
            affected_node=affected_iris[0] if affected_iris else "",
            description=description,
            pack=pack,
            cou=cou,
            affected_evidence=affected_evidence,
            constituent_firings=constituent_firings,
        ))
    return contexts


# ── Round 1 (P-B iteration) helpers ────────────────────────


def _resolve_node_in_doc(package_doc: dict, iri: str) -> dict | None:
    """Walk the package JSON-LD looking for a node whose `id`/`@id` matches `iri`.

    JSON-LD packages mix compact (`id`) and expanded (`@id`) forms; this
    helper checks both. Returns the first match (breadth-first; depth
    capped to avoid getting stuck on cyclic graph refs).
    """
    if not iri:
        return None

    # Bounded BFS — packages are typically a few hundred nodes deep at most.
    queue: list[object] = [package_doc]
    seen_obj_ids: set[int] = set()
    visited_count = 0
    while queue and visited_count < 10_000:  # hard cap; production packages stay well below
        node = queue.pop(0)
        visited_count += 1
        oid = id(node)
        if oid in seen_obj_ids:
            continue
        seen_obj_ids.add(oid)

        if isinstance(node, dict):
            nid = node.get("@id") or node.get("id")
            if isinstance(nid, str) and nid == iri:
                return node
            queue.extend(node.values())
        elif isinstance(node, list):
            queue.extend(node)
    return None


# Field aliases — JSON-LD packages use mixed naming. These tuples define
# the lookup priority for each summary field.
_LABEL_FIELDS = ("factorType", "name", "label", "title", "description")
_KIND_FIELDS = ("type", "@type")
_STATUS_FIELDS = ("factorStatus", "status", "decision", "outcome")
_REQUIRED_LEVEL_FIELDS = ("requiredLevel", "required_level", "levelRequired")
_ACHIEVED_LEVEL_FIELDS = ("achievedLevel", "achieved_level", "levelAchieved")


def _summarize_node(node: dict) -> dict:
    """Reduce a resolved JSON-LD node to the fields the prompt cares about.

    Always returns a dict (never None) so the template can iterate
    safely. Missing fields are empty strings rather than absent keys.

    Output shape:
        {
            "iri":         "<full IRI>",
            "kind":        "CredibilityFactor",   # type/category
            "label":       "Use error",            # human-readable name
            "status":      "not-assessed",
            "required":    "",                     # str — empty if missing
            "achieved":    "",
            "description": "",
        }

    For credibility factors specifically (the most common affected node),
    `label` is the regulatory-affairs-readable name (`factorType`).
    """
    iri = ""
    if isinstance(node, dict):
        iri = str(node.get("@id") or node.get("id") or "")

    return {
        "iri": iri,
        "kind": _str_first(node, _KIND_FIELDS),
        "label": _str_first(node, _LABEL_FIELDS),
        "status": _str_first(node, _STATUS_FIELDS),
        "required": _str_first(node, _REQUIRED_LEVEL_FIELDS),
        "achieved": _str_first(node, _ACHIEVED_LEVEL_FIELDS),
        "description": str(node.get("description") or ""),
    }


def _summarize_constituent(annotation: dict, package_doc: dict) -> dict:
    """Reduce one constituent firing of a COMPOUND to a prompt-ready dict.

    `annotation` comes from `rules.parse_individual_annotations()`. We
    additionally resolve its `affected_node` IRI in the package so the
    prompt can say "W-AL-01 (Missing Uncertainty Quantification) on the
    'Use error' factor" rather than just "W-AL-01 fired on _:b1".
    """
    affected_iri = annotation.get("affected_node", "")
    affected_node = _resolve_node_in_doc(package_doc, affected_iri) if affected_iri else None
    return {
        "patternId": annotation.get("patternId", ""),
        "severity": annotation.get("severity", ""),
        "description": annotation.get("description", ""),
        "affected": _summarize_node(affected_node or {"@id": affected_iri, "id": affected_iri}),
    }


def _str_first(node, keys: tuple[str, ...]) -> str:
    """Return first present-and-non-empty value for any of `keys` as str.

    Treats `None` as missing but `0` / `False` / `""` as values to consider
    (since `achievedLevel: 0` is meaningful and `""` empty-string means
    "explicitly empty" — we want to keep walking for a better key).
    """
    if not isinstance(node, dict):
        return ""
    for k in keys:
        v = node.get(k)
        if v is None:
            continue
        if isinstance(v, list):
            joined = ", ".join(str(item) for item in v if item is not None)
            if joined:
                return joined
            continue
        s = str(v)
        if s:  # non-empty after stringification ('0' counts; '' doesn't)
            return s
    return ""


def extract_difference_contexts(
    only_a: list[str],
    only_b: list[str],
    weakeners_a: list[dict],
    weakeners_b: list[dict],
    cou_identity_a: dict,
    cou_identity_b: dict,
    pack_name: str,
) -> list[DifferenceContext]:
    """Build DifferenceContexts from a DiffResult.

    Uses the shape produced by `diff.run_structured()`. `only_a`/`only_b`
    are sorted patternId lists; `weakeners_a`/`weakeners_b` carry the rich
    dict (with severity, optional description).
    """
    pack = extract_pack_context(pack_name)
    cou_a = CouContext(
        name=cou_identity_a.get("cou_name", ""),
        device_class=cou_identity_a.get("device_class", ""),
        model_risk_level=cou_identity_a.get("model_risk_level", ""),
    )
    cou_b = CouContext(
        name=cou_identity_b.get("cou_name", ""),
        device_class=cou_identity_b.get("device_class", ""),
        model_risk_level=cou_identity_b.get("model_risk_level", ""),
    )

    by_pid_a = {w["patternId"]: w for w in weakeners_a if "patternId" in w}
    by_pid_b = {w["patternId"]: w for w in weakeners_b if "patternId" in w}

    out: list[DifferenceContext] = []
    for pid in only_a:
        w = by_pid_a.get(pid, {})
        out.append(DifferenceContext(
            pattern_id=pid,
            severity=str(w.get("severity", "Medium")),
            only_in="A",
            cou_with=cou_a,
            cou_without=cou_b,
            description=str(w.get("description", "")),
            pack=pack,
        ))
    for pid in only_b:
        w = by_pid_b.get(pid, {})
        out.append(DifferenceContext(
            pattern_id=pid,
            severity=str(w.get("severity", "Medium")),
            only_in="B",
            cou_with=cou_b,
            cou_without=cou_a,
            description=str(w.get("description", "")),
            pack=pack,
        ))
    return out


def extract_violation_contexts(
    violations: list[dict],
    pack_name: str,
) -> list[ViolationContext]:
    """Build ViolationContexts from a ShaclResult.violations list.

    `violations` shape per `shacl_friendly.run_shacl_multi`: each dict
    carries at minimum `path`, `message`, `severity`, `focus_node`, and
    optionally `expected` / `actual` / `fix_suggestion` (key names depend
    on the extractor; we look up several aliases).
    """
    pack = extract_pack_context(pack_name)
    return [
        ViolationContext(
            constraint_path=str(_first(v, ("path", "constraint", "result_path"), "")),
            severity=str(_first(v, ("severity",), "Medium")),
            affected_node=str(_first(v, ("focus_node", "node", "affected_node"), "")),
            expected=str(_first(v, ("expected", "expected_value"), "")),
            actual=str(_first(v, ("actual", "actual_value", "value"), "")),
            description=str(_first(v, ("fix_suggestion", "message", "description"), "")),
            pack=pack,
        )
        for v in violations
    ]


def _first(d: dict, keys: tuple[str, ...], default: Any) -> Any:
    """Return d[k] for the first k in keys that's present and truthy."""
    for k in keys:
        v = d.get(k)
        if v not in (None, ""):
            return v
    return default

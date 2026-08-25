"""Mutation engine — apply one operator at one site, prove the mutant is live.

Phase 2.5a §1.1. The engine's job is to make the manifest true by construction
rather than by assertion, so three things are load-bearing:

1. **Load through the CLI's own path.** A mutant the CLI cannot load is a defect
   in the mutator, not a finding about the catalog (parent C1's emittability rule).
2. **Liveness by RDF canonicalization, not by JSON.** `integrity.canonicalize_and_hash`
   is sorted-key JSON (see its own docstring and INV-4 §3), so a JSON-visible edit
   that vanishes on expansion would read as live. Liveness uses
   `rdflib.compare.to_isomorphic`, which compares the graphs the engine actually sees.
3. **Record what changed, not what was intended.** Site, before/after and the diff
   hash all come from the graph diff. Only the target pattern — the label being
   injected — comes from the operator, because that IS the ground truth being
   declared.
"""

from __future__ import annotations

import sys

import hashlib
import json
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path

from rdflib import Graph
from rdflib.compare import to_isomorphic, graph_diff

from uofa_cli import integrity, paths
from uofa_cli.mutation import operators as ops

LIVE = "LIVE"
EQUIVALENT = "EQUIVALENT"       # canonicalization erased it; excluded from the denominator
UNCHANGED = "UNCHANGED"         # the operator did not apply


# ── loading ────────────────────────────────────────────────────────────────

def expand(doc: dict) -> Graph:
    """Expand a package to RDF through the shipped context.

    Two package shapes exist in the repo, and a flat-only reader silently sees an
    empty graph for the second — which is how an earlier pass read the NASA HPT
    packages as empty when they are `@graph`-form:

        flat    properties at the top level, `@context` present
        @graph  properties inside `@graph`, `@context` absent
    """
    # The document's own context. A @graph-form package declares none and takes
    # the named fallback rather than a silent v0.5 default.
    ctx_path, ctx_note = integrity.context_for_document(doc)
    if ctx_note:
        # **stderr, not stdout.** The note must be impossible to miss and must
        # not become data: `check-counts.mjs` parses this command's stdout as
        # JSON, and a diagnostic line printed there turned a valid run into
        # "stdout was not JSON". Never-silent is a property of the message
        # reaching a reader, not of which stream carries it.
        print(f"  {ctx_note}", file=sys.stderr)
    ctx = json.loads(Path(ctx_path).read_text(encoding="utf-8"))["@context"]
    if "@graph" in doc:
        payload = {"@context": ctx, "@graph": doc["@graph"]}
    else:
        payload = dict(doc)
        payload["@context"] = ctx
    g = Graph()
    g.parse(data=json.dumps(payload), format="json-ld")
    return g


def load_substrate(path: str | Path) -> tuple[dict, Graph]:
    doc = json.loads(Path(path).read_text(encoding="utf-8"))
    return doc, expand(doc)


# ── liveness ───────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Diff:
    verdict: str
    added: tuple[str, ...]
    removed: tuple[str, ...]
    diff_hash: str

    @property
    def is_live(self) -> bool:
        return self.verdict == LIVE


def _fmt(triple) -> str:
    return " ".join(t.n3() for t in triple)


def diff_graphs(before: Graph, after: Graph) -> Diff:
    """Canonical graph diff. EQUIVALENT means the edit did not survive expansion."""
    _, only_before, only_after = graph_diff(to_isomorphic(before), to_isomorphic(after))
    removed = tuple(sorted(_fmt(t) for t in only_before))
    added = tuple(sorted(_fmt(t) for t in only_after))
    verdict = LIVE if (added or removed) else EQUIVALENT
    payload = json.dumps({"added": added, "removed": removed}, sort_keys=True)
    return Diff(verdict, added, removed, hashlib.sha256(payload.encode()).hexdigest())


# ── site discovery + application ───────────────────────────────────────────
# Sites are *mutation points*, which is not the same as element counts. W-SI-02
# fires on the absence of a whole property, so `bindsRequirement` with one value
# and `hasValidationResult` with six are two sites, not seven. The step-1
# inventory counted elements and therefore overstated W-SI-02; the engine is the
# authority and `site_table()` re-derives the counts.

def _results(doc: dict) -> list:
    vrs = doc.get("hasValidationResult") or []
    return [vrs] if isinstance(vrs, (dict, str)) else list(vrs)


def _result_prop_sites(prop: str):
    def find(doc: dict) -> list[dict]:
        return [
            {"kind": "result-prop", "index": i, "prop": prop,
             "path": f"hasValidationResult[{i}].{prop}"}
            for i, r in enumerate(_results(doc))
            if isinstance(r, dict) and r.get(prop) is not None
        ]
    return find


def _apply_result_prop(doc: dict, site: dict) -> dict:
    d = deepcopy(doc)
    d["hasValidationResult"][site["index"]].pop(site["prop"], None)
    return d


def _root_prop_sites(*props: str):
    def find(doc: dict) -> list[dict]:
        return [{"kind": "root-prop", "prop": p, "path": p}
                for p in props if doc.get(p) is not None]
    return find


def _apply_root_prop(doc: dict, site: dict) -> dict:
    d = deepcopy(doc)
    d.pop(site["prop"], None)
    return d


_UPSTREAM = ("wasDerivedFrom", "wasGeneratedBy", "used")


def _walk(node, path=""):
    """Yield (json_path, dict) for every nested object in the document."""
    if isinstance(node, dict):
        yield path, node
        for k, v in node.items():
            yield from _walk(v, f"{path}.{k}" if path else k)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from _walk(v, f"{path}[{i}]")


def _provenance_sites(doc: dict) -> list[dict]:
    """Nodes whose upstream edge can be severed to make them chain-terminal.

    W-PROV-01 seeds provenance scope at the claim and extends UPSTREAM, so
    severing the *claim's* edge removes the whole subtree from scope and the rule
    fires LESS -- measured, see the report. An additive mutation has to make an
    already-in-scope node terminal while leaving it reachable, which means
    severing an edge on an INTERMEDIATE node, not on the claim.

    The claim is therefore excluded as a site. Whether any intermediate site is
    net-additive is an empirical question the site's own delta answers.
    """
    sites = []
    for path, obj in _walk(doc):
        if path in ("", "bindsClaim"):
            continue                          # root and claim excluded
        for prop in _UPSTREAM:
            if obj.get(prop) is None:
                continue
            vals = obj[prop] if isinstance(obj[prop], list) else [obj[prop]]
            for i in range(len(vals)):
                sites.append({"kind": "provenance-edge", "path": f"{path}.{prop}[{i}]",
                              "obj_path": path, "prop": prop, "index": i})
    return sites


def _resolve(doc: dict, path: str):
    cur = doc
    for part in path.split("."):
        if not part:
            continue
        while "[" in part:
            name, rest = part.split("[", 1)
            idx, part = rest.split("]", 1)
            if name:
                cur = cur[name]
            cur = cur[int(idx)]
        if part:
            cur = cur[part]
    return cur


def _apply_provenance_edge(doc: dict, site: dict) -> dict:
    d = deepcopy(doc)
    obj = _resolve(d, site["obj_path"])
    vals = obj[site["prop"]]
    if isinstance(vals, list):
        vals.pop(site["index"])
        if not vals:
            obj.pop(site["prop"])
    else:
        obj.pop(site["prop"])
    return d


# ── Class B: enrich, assert conformance, then violate ──────────────────────
#
# A Class B mutant is two edits and one fault. The edits are NOT equivalent and
# must not share a baseline:
#
#   substrate  --enrich-->  ENRICHED-CLEAN  --violate-->  mutant
#
# The delta baseline is ENRICHED-CLEAN, not the substrate. Diffing a Class B
# mutant against the raw substrate would fold the enrichment into the record and
# the manifest would claim the enrichment as part of the injected defect, which is
# exactly the "manifest derived from intent" failure the diff-derived rule exists
# to prevent.
#
# Conformance is asserted on ENRICHED-CLEAN, before violation, per addendum E: an
# enrichment that lands non-conformant produces a schema-caught mutant whose target
# rule never gets a fair test, and — since addendum F — that silently removes a
# gate-eligible pattern from a denominator already at 13. So it fails loudly.

class EnrichmentNotConformant(RuntimeError):
    """The enrichment broke the profile, so the violation would not be a fair test."""


def _iso(day: str) -> str:
    return f"{day}T00:00:00Z"


def _enrich_stale_dataset(doc: dict) -> dict:
    """W-EP-03: modelRevisionDate + a result -> activity -> dataset chain."""
    d = deepcopy(doc)
    base = str(d.get("id", "https://uofa.net/pkg")).rstrip("/")
    d["modelRevisionDate"] = _iso("2026-03-01")
    results = _results(d)
    target = results[0] if results and isinstance(results[0], dict) else None
    if target is None:                      # bare-IRI results: inline the first
        iri = results[0] if results else f"{base}/result/1"
        target = {"id": iri, "type": "ValidationResult"}
        d["hasValidationResult"] = [target] + [r for r in results[1:]]
    target["wasGeneratedBy"] = {
        "id": f"{base}/activity/enriched", "type": "VerificationActivity",
        "name": "validation run",
        "used": {"id": f"{base}/dataset/enriched", "type": "Dataset",
                 "name": "input dataset",
                 "dataVintage": _iso("2026-06-01")},   # AFTER the revision: clean
    }
    return d


def _violate_stale_dataset(doc: dict, site: dict) -> dict:
    d = deepcopy(doc)
    _results(d)[0]["wasGeneratedBy"]["used"]["dataVintage"] = _iso("2026-01-15")
    return d


def _enrich_version_drift(doc: dict) -> dict:
    """W-AR-04: currentModelVersion + a used -> ModelConfiguration carrying modelVersion."""
    d = deepcopy(doc)
    base = str(d.get("id", "https://uofa.net/pkg")).rstrip("/")
    d["currentModelVersion"] = "v2.1.0"
    results = _results(d)
    target = results[0] if results and isinstance(results[0], dict) else None
    if target is None:
        iri = results[0] if results else f"{base}/result/1"
        target = {"id": iri, "type": "ValidationResult"}
        d["hasValidationResult"] = [target] + [r for r in results[1:]]
    target["wasGeneratedBy"] = {
        "id": f"{base}/activity/enriched-cfg", "type": "VerificationActivity",
        "name": "validation run",
        "used": {"id": f"{base}/config/enriched", "type": "ModelConfiguration",
                 "name": "solver configuration",
                 "modelVersion": "v2.1.0"},            # MATCHES: clean
    }
    return d


def _violate_version_drift(doc: dict, site: dict) -> dict:
    d = deepcopy(doc)
    _results(d)[0]["wasGeneratedBy"]["used"]["modelVersion"] = "v1.4.0"
    return d


def _enrich_future_evidence(doc: dict) -> dict:
    """W-CON-03: signatureTimestamp + hasEvidence carrying evidenceTimestamp."""
    d = deepcopy(doc)
    base = str(d.get("id", "https://uofa.net/pkg")).rstrip("/")
    d["signatureTimestamp"] = _iso("2026-05-01")
    d["hasEvidence"] = [{"id": f"{base}/evidence/enriched", "type": "Evidence",
                         "name": "supporting evidence",
                         "evidenceTimestamp": _iso("2026-04-01")}]   # BEFORE: clean
    return d


def _violate_future_evidence(doc: dict, site: dict) -> dict:
    d = deepcopy(doc)
    d["hasEvidence"][0]["evidenceTimestamp"] = _iso("2026-09-01")
    return d


def _enrich_method_match(doc: dict) -> dict:
    """W-AR-03: inline the requirement with a method, and give the activity a type."""
    d = deepcopy(doc)
    base = str(d.get("id", "https://uofa.net/pkg")).rstrip("/")
    req = d.get("bindsRequirement")
    req_iri = req if isinstance(req, str) else (req or {}).get("id", f"{base}/req/1")
    d["bindsRequirement"] = {"id": req_iri, "type": "Requirement",
                             "name": "verification requirement",
                             "requiredVerificationMethod": "mesh-convergence-study"}
    results = _results(d)
    target = results[0] if results and isinstance(results[0], dict) else None
    if target is None:
        iri = results[0] if results else f"{base}/result/1"
        target = {"id": iri, "type": "ValidationResult"}
        d["hasValidationResult"] = [target] + [r for r in results[1:]]
    target["wasGeneratedBy"] = {"id": f"{base}/activity/method", "type": "VerificationActivity",
                                "name": "verification activity",
                                "activityType": "mesh-convergence-study"}   # MATCHES: clean
    return d


def _violate_method_match(doc: dict, site: dict) -> dict:
    d = deepcopy(doc)
    _results(d)[0]["wasGeneratedBy"]["activityType"] = "expert-review"
    return d


def _enrich_identifier(doc: dict) -> dict:
    """W-CON-02: reference an identifier whose target resolves in-graph."""
    d = deepcopy(doc)
    base = str(d.get("id", "https://uofa.net/pkg")).rstrip("/")
    tgt = f"{base}/identifier/enriched"
    d["referencesIdentifier"] = {"id": tgt, "type": "Evidence",   # typed: resolves
                                 "name": "referenced artifact"}
    return d


def _violate_identifier(doc: dict, site: dict) -> dict:
    d = deepcopy(doc)
    d["referencesIdentifier"] = d["referencesIdentifier"]["id"]   # bare IRI: resolves nowhere
    return d


def _enrich_verification_activity(doc: dict) -> dict:
    """W-CON-05: declare an activity and link Evidence to it."""
    d = deepcopy(doc)
    base = str(d.get("id", "https://uofa.net/pkg")).rstrip("/")
    act = f"{base}/activity/declared"
    d["hasVerificationActivity"] = {"id": act, "type": "VerificationActivity",
                                    "name": "declared verification"}
    ev = d.get("hasEvidence")
    ev = list(ev) if isinstance(ev, list) else ([ev] if ev else [])
    ev.append({"id": f"{base}/evidence/for-activity", "type": "Evidence",
               "name": "evidence from the activity",
               "wasGeneratedBy": act})                             # linked: clean
    d["hasEvidence"] = ev
    return d


def _violate_verification_activity(doc: dict, site: dict) -> dict:
    d = deepcopy(doc)
    d["hasEvidence"] = [e for e in d["hasEvidence"]
                        if not str(e.get("id", "")).endswith("/evidence/for-activity")]
    return d


def _enrich_envelope(doc: dict) -> dict:
    """W-ON-02: ENRICH-TO-CLEAN. Every substrate already violates this rule, so a
    clean state has to be manufactured before the defect can be injected."""
    d = deepcopy(doc)
    cou = d.get("hasContextOfUse")
    if not isinstance(cou, dict):
        return d
    cou = deepcopy(cou)
    cou["hasOperatingEnvelope"] = {"id": f"{cou.get('id','cou')}/envelope",
                                   "type": "OperatingEnvelope",
                                   "name": "validity envelope"}
    d["hasContextOfUse"] = cou
    return d


def _violate_envelope(doc: dict, site: dict) -> dict:
    d = deepcopy(doc)
    d["hasContextOfUse"].pop("hasOperatingEnvelope", None)
    return d


def _enrich_dangling_provenance(doc: dict) -> dict:
    """W-PROV-01: put a terminal node in scope, suppressed by isFoundationalEvidence.

    The clean state relies on the very flag whose structural-vs-dispositional
    reading decided this pattern's MECHANICAL class under ruling 4 — and which
    appears in zero encodings. So this operator is also the only exercise the flag
    gets anywhere in the corpus.
    """
    d = deepcopy(doc)
    base = str(d.get("id", "https://uofa.net/pkg")).rstrip("/")
    claim = d.get("bindsClaim")
    if not isinstance(claim, dict):
        claim = {"id": claim or f"{base}/claim/1", "type": "AssuranceClaim",
                 "name": "assurance claim"}
    claim = deepcopy(claim)
    wdf = claim.get("wasDerivedFrom")
    wdf = list(wdf) if isinstance(wdf, list) else ([wdf] if wdf else [])
    wdf.append({"id": f"{base}/evidence/foundational", "type": "Evidence",
                "name": "foundational evidence",
                "isFoundationalEvidence": True})                    # suppressed: clean
    claim["wasDerivedFrom"] = wdf
    d["bindsClaim"] = claim
    return d


def _violate_dangling_provenance(doc: dict, site: dict) -> dict:
    d = deepcopy(doc)
    for n in d["bindsClaim"]["wasDerivedFrom"]:
        if isinstance(n, dict) and str(n.get("id", "")).endswith("/evidence/foundational"):
            n.pop("isFoundationalEvidence", None)
    return d


def _enrich_orphan_claim(doc: dict) -> dict:
    """W-EP-01: DEMONSTRATE, DO NOT SCORE.

    Types the claim `Claim` — the class the rule's guard names and the schema never
    declares — so the rule can bind at all. The paired contrast in the report types
    it `AssuranceClaim`, which is what `bindsClaim`'s rdfs:range actually declares
    and what every real encoding uses, and the rule stays silent through the same
    violation. That contrast is the finding; the row it cannot produce is not.
    """
    d = deepcopy(doc)
    base = str(d.get("id", "https://uofa.net/pkg")).rstrip("/")
    d["bindsClaim"] = {"id": f"{base}/claim/demo", "type": "Claim",
                       "name": "claim typed against the rule's guard",
                       "wasDerivedFrom": {"id": f"{base}/evidence/demo",
                                          "type": "Evidence", "name": "supporting evidence"}}
    return d


def _violate_orphan_claim(doc: dict, site: dict) -> dict:
    d = deepcopy(doc)
    d["bindsClaim"].pop("wasDerivedFrom", None)
    return d


_ENRICH_HOOKS: dict[str, tuple] = {
    "MUT-ANT-01": (_enrich_stale_dataset, _violate_stale_dataset),
    "MUT-ANT-02": (_enrich_version_drift, _violate_version_drift),
    "MUT-ANT-03": (_enrich_future_evidence, _violate_future_evidence),
    "MUT-ANT-04": (_enrich_method_match, _violate_method_match),
    "MUT-ANT-05": (_enrich_identifier, _violate_identifier),
    "MUT-ANT-06": (_enrich_verification_activity, _violate_verification_activity),
    "MUT-ANT-07": (_enrich_envelope, _violate_envelope),
    "MUT-ANT-08": (_enrich_orphan_claim, _violate_orphan_claim),
    "MUT-REF-01": (_enrich_dangling_provenance, _violate_dangling_provenance),
}


def _apply_strip_signature(doc: dict, site: dict) -> dict:
    """W-SI-01 models tamper, so it strips the signature from the SIGNED form.

    The hash stays: a package whose signature is gone but whose hash still covers
    the original bytes is exactly the artifact the rule exists to catch.
    """
    d = deepcopy(doc)
    d.pop("signature", None)
    return d


# Bind hooks onto the registry's Class A rows. Class B rows stay unbound until
# their enrichment operators land; `coverage()["implemented"]` counts what is real.
_HOOKS: dict[str, tuple] = {
    "MUT-DEL-01": (_result_prop_sites("hasUncertaintyQuantification"), _apply_result_prop),
    "MUT-DEL-02": (_result_prop_sites("comparedAgainst"), _apply_result_prop),
    "MUT-DEL-03": (_result_prop_sites("wasGeneratedBy"), _apply_result_prop),
    "MUT-DEL-04": (_root_prop_sites("hasContextOfUse"), _apply_root_prop),
    "MUT-DEL-05": (_root_prop_sites("signature"), _apply_strip_signature),
    "MUT-DEL-06": (_root_prop_sites("bindsRequirement", "hasValidationResult"), _apply_root_prop),
    "MUT-DEL-07": (_root_prop_sites("hasSensitivityAnalysis"), _apply_root_prop),
    "MUT-DEL-08": (_root_prop_sites("hasSensitivityAnalysis"), _apply_root_prop),

}


def _bind() -> tuple[ops.Operator, ...]:
    bound = []
    for op in ops.REGISTRY:
        hooks = _HOOKS.get(op.id)
        enrich = _ENRICH_HOOKS.get(op.id)
        if hooks:
            find, apply_fn = hooks
            bound.append(ops.Operator(**{**op.__dict__, "implemented": True,
                                         "find_sites": find, "apply": apply_fn}))
        elif enrich:
            enrich_fn, violate_fn = enrich
            # Class B always has exactly one site: the structure the operator
            # itself instantiates. Enumerating sites over a field the substrate
            # does not have would be meaningless.
            bound.append(ops.Operator(**{**op.__dict__, "implemented": True,
                                         "find_sites": lambda _doc: [{"kind": "enrichment",
                                                                      "path": "<instantiated>"}],
                                         "apply": violate_fn}))
        else:
            bound.append(op)
    return tuple(bound)


def findings(path: str | Path, packs=None) -> dict[str, int]:
    """Rule-engine findings for a package, in-process.

    The detection half of the loop is `uofa rules` — the production detector,
    which predates this harness and has no notion of a manifest. That is
    deliberate: a detector that could read the answer key would make the demo
    circular. Scoring lives in `uofa inject verify`, which knows the manifest;
    the detector never does.
    """
    import argparse

    from uofa_cli.commands import rules as rules_mod

    ns = argparse.Namespace(file=Path(path), rules=None, context=None, build=False,
                            raw=False, format="summary", output=None,
                            active_packs=packs)
    return {f["patternId"]: f.get("hits", 1) for f in rules_mod.run_structured(ns).firings}


def conformant(path: str | Path, pack: str = "vv40") -> bool | None:
    """Profile status via the CLI's own SHACL stage, in-process.

    In-process on purpose. A subprocess resolves the repo root from the *package's*
    location, so a mutant written outside the tree makes `uofa shacl` look for
    `spec/context/v0.5.jsonld` beside the mutant and fail — which reads as
    non-conformance unless someone checks stderr. That produced a clean-looking
    0/23 and then a clean-looking 23/23 before it was caught. Calling
    `shacl.run_structured` resolves paths from the process, not the argument.

    Also requires `2a1d3544` (fix(shacl): resolve @context from the shipped file)
    in the measuring branch; without it conformance readings are wrong rather than
    absent.

    Returns None only if the stage could not run — never conflated with False.
    """
    import argparse

    from uofa_cli.commands import shacl as shacl_mod

    ns = argparse.Namespace(file=Path(path), raw=False, active_packs=[pack],
                            explain=False, explain_format=None)
    try:
        return bool(shacl_mod.run_structured(ns).conforms)
    except Exception:                                    # noqa: BLE001
        return None                                      # harness fault, not a verdict


REGISTRY: tuple[ops.Operator, ...] = _bind()


def by_id(operator_id: str) -> ops.Operator:
    for op in REGISTRY:
        if op.id == operator_id:
            return op
    raise KeyError(f"no such operator: {operator_id}")


# ── the mutation itself ────────────────────────────────────────────────────

@dataclass(frozen=True)
class MutationRecord:
    operator_id: str
    target_pattern: str          # the declared label -- this IS the ground truth
    class_ab: str
    substrate: str
    substrate_sha256: str
    site: dict                   # observed, from discovery
    diff: Diff                   # observed, from the graph
    mutant_path: str | None
    gate_scored: bool
    enrichment: bool
    baseline: tuple[str, ...] = field(default=())   # A3 delta baseline, filled by the runner

    def to_json(self) -> dict:
        return {
            "operator": self.operator_id,
            "target_pattern": self.target_pattern,
            "class": self.class_ab,
            "enrichment": self.enrichment,
            "gate_scored": self.gate_scored,
            "substrate": self.substrate,
            "substrate_sha256": self.substrate_sha256,
            "site": self.site,
            "liveness": self.diff.verdict,
            "triples_added": list(self.diff.added),
            "triples_removed": list(self.diff.removed),
            "diff_sha256": self.diff.diff_hash,
            "mutant": self.mutant_path,
            "baseline_findings": list(self.baseline),
        }


def _sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def mutate(operator_id: str, substrate: str | Path, site_index: int = 0,
           out_dir: str | Path | None = None) -> MutationRecord:
    """Apply one operator at one site and prove the result is live."""
    op = by_id(operator_id)
    if not op.implemented:
        raise NotImplementedError(
            f"{op.id} ({op.pattern}) is Class {op.class_ab} and not yet built. "
            f"Antecedent required: {op.antecedent}"
        )
    substrate = Path(substrate)
    doc, before = load_substrate(substrate)

    sites = op.find_sites(doc)
    if not sites:
        return MutationRecord(op.id, op.pattern, op.class_ab, str(substrate),
                              _sha256(substrate), {"kind": "none"},
                              Diff(UNCHANGED, (), (), ""), None,
                              op.gate_scored, op.class_ab == "B")
    site = sites[site_index]
    mutated = op.apply(doc, site)
    d = diff_graphs(before, expand(mutated))

    mutant_path = None
    if out_dir is not None and d.is_live:
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        name = f"{substrate.stem}__{op.id}__site{site_index}.jsonld"
        mutant_path = str(out / name)
        Path(mutant_path).write_text(json.dumps(mutated, indent=1), encoding="utf-8")

    return MutationRecord(op.id, op.pattern, op.class_ab, str(substrate),
                          _sha256(substrate), site, d, mutant_path,
                          op.gate_scored, op.class_ab == "B")


def mutate_enriched(operator_id: str, substrate: str | Path,
                    out_dir: str | Path) -> tuple[MutationRecord, str]:
    """Class B: enrich, assert conformance, then violate.

    Returns (record, enriched_clean_path). The diff and the A3 delta baseline are
    both against ENRICHED-CLEAN, never against the raw substrate — folding the
    enrichment into the record would make the manifest claim it as part of the
    injected defect.

    Raises EnrichmentNotConformant if the enrichment breaks the profile. That is a
    hard stop rather than a logged row: under addendum F a non-conformant
    enrichment silently removes a gate-eligible pattern from a denominator of 13.
    """
    op = by_id(operator_id)
    enrich_fn, violate_fn = _ENRICH_HOOKS[operator_id]
    substrate = Path(substrate)
    doc, _ = load_substrate(substrate)

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    enriched = enrich_fn(doc)
    clean_path = out / f"{substrate.stem}__{op.id}__enriched-clean.jsonld"
    clean_path.write_text(json.dumps(enriched, indent=1), encoding="utf-8")

    status = conformant(clean_path)
    if status is not True:
        raise EnrichmentNotConformant(
            f"{op.id}: enrichment on {substrate.stem} is "
            f"{'non-conformant' if status is False else 'unverifiable'}; the target "
            f"rule would never get a fair test and {op.pattern} would leave the "
            f"gate denominator for an unrelated reason."
        )

    mutated = violate_fn(enriched, {"kind": "enrichment"})
    d = diff_graphs(expand(enriched), expand(mutated))
    mutant_path = None
    if d.is_live:
        mutant_path = str(out / f"{substrate.stem}__{op.id}__mutant.jsonld")
        Path(mutant_path).write_text(json.dumps(mutated, indent=1), encoding="utf-8")

    return (MutationRecord(op.id, op.pattern, op.class_ab, str(substrate),
                           _sha256(substrate), {"kind": "enrichment", "path": "<instantiated>"},
                           d, mutant_path, op.gate_scored, True),
            str(clean_path))


def site_table(substrates: dict[str, str]) -> dict:
    """Measured site counts per operator per substrate — the authority for `n`.

    Amendment A4 requires `n` in every reported row, and `n` is the number of
    live mutation sites, not the element count the step-1 inventory estimated.
    """
    table: dict = {}
    for op in REGISTRY:
        if not op.implemented:
            table[op.id] = {"pattern": op.pattern, "implemented": False, "sites": {}}
            continue
        per = {}
        for name, path in substrates.items():
            doc, _ = load_substrate(path)
            per[name] = len(op.find_sites(doc))
        table[op.id] = {"pattern": op.pattern, "implemented": True,
                        "sites": per, "n": sum(per.values())}
    return table

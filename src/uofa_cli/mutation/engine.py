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

import hashlib
import json
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path

from rdflib import Graph
from rdflib.compare import to_isomorphic, graph_diff

from uofa_cli import paths
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
    ctx = json.loads(Path(paths.context_file()).read_text())["@context"]
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
        if hooks:
            find, apply_fn = hooks
            bound.append(ops.Operator(**{**op.__dict__, "implemented": True,
                                         "find_sites": find, "apply": apply_fn}))
        else:
            bound.append(op)
    return tuple(bound)


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

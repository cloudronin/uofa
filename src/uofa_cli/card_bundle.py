"""Shared bridge: an extractor `ExtractionResult` (or curated/heuristic statuses)
-> the intermediate dict that `excel_mapper.map_to_jsonld` consumes -> a UofA
JSON-LD bundle.

Used by both the demo Space pipeline and the `uofa report` id path, so the two
build identical bundles from the same extraction. The Excel round-trip is
deliberately skipped (it is fragile and lossy). Lives CLI-side so the CLI never
depends on `space/`; `space/pipeline.py` re-imports these names.

(The card-text front end -- `deterministic_factor_statuses` and `card_to_bundle`
-- is defined below alongside the id-aware `uofa report` command.)
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from uofa_cli import paths
from uofa_cli.excel_constants import (
    ALL_FACTOR_CATEGORIES,
    MRM_NIST_DEFAULT_OUT_OF_SCOPE,
    MRM_NIST_FACTOR_NAMES,
)
from uofa_cli.excel_mapper import map_to_jsonld, slugify

# A model card declares no deployment context or risk tier, so the mrm-nist
# profile assesses every card against one disclosed assumption (surfaced in the
# reviewer/report readout so W-EP-04 fires against a STATED input, not a hidden
# one). Single source of truth, shared by the live Space path, the curated
# build-time run, and the `uofa report` id path.
MRM_NIST_ASSUMED_MRL = 3
MRM_NIST_RISK_ASSUMPTION = (
    "Evaluated as if bound for a moderate-risk deployment (assumed MRL 3); "
    "the source card declares no context of use or risk tier."
)

_CATEGORY_BY_FACTOR = dict(ALL_FACTOR_CATEGORIES)


def unwrap_value(obj):
    """Unwrap a FieldExtraction to its .value (or pass a plain value through)."""
    return getattr(obj, "value", obj)


def unwrap_fields(d: dict) -> dict:
    return {k: unwrap_value(v) for k, v in d.items()}


def parse_mrl(value) -> int | None:
    """Coerce a model-risk-level value ("MRL 2", "2", 2) to an int, mirroring
    excel_reader._read_summary so modelRiskLevel serializes as a valid xsd:integer
    (a bare string aborts the Jena engine with a DatatypeFormatException)."""
    if value is None:
        return None
    if isinstance(value, int):
        return value
    try:
        return int(str(value).upper().replace("MRL", "").strip())
    except (ValueError, TypeError):
        return None


def result_to_import_dict(result, pack: str, factor_edits: dict[str, str] | None = None) -> dict:
    """Map an ExtractionResult to the dict shape `map_to_jsonld` expects.

    `factor_edits` (factor_type -> status) overrides the extracted status for
    confirmed factors - the only user-mutable field in the confirm step.
    Profile is forced to "Complete" so all factors map and the rule engine can
    see unassessed gaps. A `decision.outcome` is synthesized because
    map_to_jsonld requires one; it is NEVER surfaced in the UI.
    """
    factor_edits = factor_edits or {}
    s = unwrap_fields(result.assessment_summary)
    summary = {
        "project_name": s.get("project_name") or "Uploaded evidence",
        "cou_name": s.get("cou_name") or "Context of use",
        "cou_description": s.get("cou_description"),
        "profile": "Complete",
        "device_class": s.get("device_class"),
        "model_risk_level": parse_mrl(s.get("model_risk_level")),
        "assurance_level": s.get("assurance_level"),
        "standards_reference": s.get("standards_reference"),
        "assessor_name": s.get("assessor_name"),
        "source_document": s.get("source_document"),
        "has_uq": s.get("has_uq", "No"),
    }

    entities = [e for e in (unwrap_fields(ent) for ent in result.model_and_data) if e.get("entity_type")]
    validation_results = [unwrap_fields(vr) for vr in result.validation_results]

    factors = []
    for raw in result.credibility_factors:
        f = unwrap_fields(raw)
        ftype = f.get("factor_type")
        if not ftype:
            continue
        factors.append({
            "factor_type": ftype,
            "category": _CATEGORY_BY_FACTOR.get(ftype),
            "required_level": f.get("required_level"),
            "achieved_level": f.get("achieved_level"),
            "acceptance_criteria": f.get("acceptance_criteria"),
            "rationale": f.get("rationale"),
            "status": factor_edits.get(ftype, f.get("status") or "not-assessed"),
            "linked_evidence": f.get("linked_evidence"),
        })

    d = unwrap_fields(result.decision)
    decision = {"outcome": "Not accepted", "rationale": d.get("rationale")}  # synthetic, never shown

    return {
        "summary": summary,
        "entities": entities,
        "validation_results": validation_results,
        "factors": factors,
        "decision": decision,
    }


def assign_factor_ids(doc: dict) -> None:
    """Give each credibility factor a stable IRI so weakener affectedNode IRIs
    resolve to factor names (without an @id they serialize as blank nodes)."""
    base = doc.get("id", "")
    for fac in doc.get("hasCredibilityFactor", []):
        if "id" not in fac and fac.get("factorType"):
            fac["id"] = f"{base}/factor/{slugify(fac['factorType'])}"


# ── Card text -> bundle (the `uofa report` id front end) ─────────────────────
#
# Two extraction paths, each with an honest provenance label surfaced in the
# readout: an LLM extractor (faithful, needs a model) and a deterministic
# README-keyword scan (no model, runs anywhere, explicitly APPROXIMATE). The
# deterministic map is intentionally coarse — its job is to produce a labelled
# best-effort readout, not to match the LLM. The LLM-vs-deterministic gap is
# tracked by tests/test_report_card.py so drift is visible, never silent.

PROV_LLM = "LLM extraction"
PROV_HEURISTIC = (
    "Heuristic - factor statuses inferred from README sections/keywords with no "
    "model; approximate"
)
PROV_HEURISTIC_FALLBACK = (
    "Heuristic - LLM extraction was unavailable, fell back to a README "
    "section/keyword scan; approximate"
)

# factor -> substrings that, if present in the lowercased card, mark it `assessed`.
# Coarse on purpose (see note above). A match flips even a default-scoped-out
# GOVERN/MANAGE factor to assessed (the card documented it).
_DET_KEYWORDS: dict[str, tuple[str, ...]] = {
    "Ownership and accountability": ("developed by", "point of contact", "contact:", "maintained by", "model authors", "developed and released by"),
    "Intended use": ("intended use", "intended to be used", "intended for", "## uses", "primary use", "use case"),
    "License and usage terms": ("license", "licence", "apache-2.0", "mit license", "cc-by", "usage terms", "terms of use", "acceptable use"),
    "Out-of-scope use": ("out-of-scope", "out of scope", "misuse", "should not be used", "not intended", "prohibited use"),
    "Task and domain context": ("trained on", "fine-tuned", "fine tuned", "pipeline_tag", "## model description", "architecture", "task:"),
    "Deployment setting": ("## usage", "how to use", "from transformers", "pip install", "inference", "```python"),
    "Known limitations": ("limitation", "bias, risks", "risks and limitations", "known issues", "failure mode", "caveat"),
    "Affected populations": ("affected", "demographic", "subgroup", "stakeholder", "representativeness", "population"),
    "Evaluation metrics": ("## evaluation", "## results", "accuracy", "f1", "bleu", "rouge", "perplexity", "benchmark", "mmlu", "| metric"),
    "Evaluation methodology": ("evaluation methodology", "evaluation protocol", "we evaluate", "eval harness", "evaluation setup", "evaluated on"),
    "Bias and fairness analysis": ("bias analysis", "fairness", "disparate", "demographic parity", "subgroup performance"),
    "Robustness and safety testing": ("robustness", "adversarial", "red team", "red-team", "safety eval", "stress test", "out-of-distribution"),
    "Test and evaluation data": ("test set", "evaluation data", "eval data", "validation set", "## training data", "test data", "datasets:"),
    "Mitigations and safeguards": ("mitigation", "safeguard", "guardrail", "safety filter", "content filter"),
    "Residual risk": ("residual risk", "remaining risk", "risk that remains"),
    "Monitoring and feedback": ("monitoring", "report issues", "feedback", "drift detection"),
    "Versioning and update policy": ("changelog", "version history", "release notes", "deprecat", "update policy"),
}


def _is_mrm_nist(pack: str) -> bool:
    p = (pack or "").lower()
    return "mrm-nist" in p or "mrm_nist" in p


def deterministic_factor_statuses(text: str, pack: str) -> dict[str, str]:
    """Coarse, no-LLM mapping of a model card to the 17 mrm-nist factor statuses by
    section/keyword presence. GOVERN/MANAGE organizational factors default
    scoped-out (a static card rarely performs them); everything else defaults
    not-assessed. APPROXIMATE by construction — the readout says so."""
    if not _is_mrm_nist(pack):
        raise ValueError("deterministic card parsing is only defined for the mrm-nist pack")
    low = (text or "").lower()
    out: dict[str, str] = {}
    for name in MRM_NIST_FACTOR_NAMES:
        if any(k in low for k in _DET_KEYWORDS.get(name, ())):
            out[name] = "assessed"
        elif name in MRM_NIST_DEFAULT_OUT_OF_SCOPE:
            out[name] = "scoped-out"
        else:
            out[name] = "not-assessed"
    return out


def _statuses_to_import_dict(statuses: dict[str, str], pack: str, model_id: str,
                             source_url: str | None) -> dict:
    """Minimal import dict from a status map (the deterministic path): no extracted
    entities or validation results, MRL fixed at the disclosed posture."""
    factors = [{"factor_type": n, "category": _CATEGORY_BY_FACTOR.get(n), "status": s}
               for n, s in statuses.items()]
    summary = {
        "project_name": model_id,
        "cou_name": f"{model_id} (model card)",
        "cou_description": None,
        "profile": "Complete",
        "device_class": None,
        "model_risk_level": MRM_NIST_ASSUMED_MRL if _is_mrm_nist(pack) else None,
        "assurance_level": "Low",
        "standards_reference": "NIST-AI-RMF-1.0" if _is_mrm_nist(pack) else None,
        "source_document": source_url or f"https://huggingface.co/{model_id}",
        "assessor_name": "UofA MRM-NIST assessment",
        "has_uq": "No",
    }
    return {"summary": summary, "entities": [], "validation_results": [], "factors": factors,
            "decision": {"outcome": "Not accepted",
                         "rationale": "Documentation-completeness assessment only."}}


def _prompt_path_for(pack: str) -> Path:
    pdir = paths.pack_dir(pack)
    manifest = json.loads((pdir / "pack.json").read_text(encoding="utf-8"))
    return pdir / manifest["prompt"]


def _llm_import_dict(text: str, pack: str, model: str | None, llm_config) -> dict:
    """Run the LLM extractor on the card text and adapt to the import dict. Forces
    the disclosed MRL posture + source provenance for mrm-nist so the readout's
    assumption holds regardless of model compliance. Raises on extractor failure."""
    from uofa_cli.document_reader import read_corpus
    from uofa_cli.llm_extractor import extract

    work = Path(tempfile.mkdtemp(prefix="uofa-card-"))
    (work / "card.md").write_text(text, encoding="utf-8")
    corpus = read_corpus([work / "card.md"])
    result = extract(corpus, model, pack, _prompt_path_for(pack), llm_config=llm_config)
    data = result_to_import_dict(result, pack)
    if _is_mrm_nist(pack):
        data["summary"]["model_risk_level"] = MRM_NIST_ASSUMED_MRL
        data["summary"].setdefault("standards_reference", "NIST-AI-RMF-1.0")
    return data


def card_to_bundle(text: str, pack: str, *, model_id: str, source_url: str | None = None,
                   model: str | None = None, llm_config=None,
                   allow_llm: bool = True) -> tuple[dict, str]:
    """Turn fetched card text into a UofA JSON-LD bundle. Returns (bundle,
    provenance_label). Uses the LLM extractor when allowed and a model/llm_config is
    available; otherwise (or if the extractor errors) falls back to the deterministic
    parser. The provenance label is surfaced verbatim in the rendered readout."""
    data = None
    provenance = PROV_HEURISTIC
    if allow_llm and (model or llm_config is not None):
        try:
            data = _llm_import_dict(text, pack, model, llm_config)
            backend = model or (f"{llm_config.backend}/{llm_config.model}" if llm_config else "model")
            provenance = f"{PROV_LLM} - {backend}"
        except Exception:
            data = None
            provenance = PROV_HEURISTIC_FALLBACK
    if data is None:
        data = _statuses_to_import_dict(deterministic_factor_statuses(text, pack), pack,
                                        model_id, source_url)

    bundle = map_to_jsonld(data, packs=[pack], source_path=Path(model_id))
    assign_factor_ids(bundle)
    return bundle, provenance

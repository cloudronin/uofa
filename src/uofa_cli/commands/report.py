"""uofa report — a credibility report for a bundle, or for a live model card.

Two source modes share one rendering path (the `uofa_cli.report_state` logic and
the six frozen invariants that also back the demo Space reviewer view, so every
surface tells one story):

  * a `.jsonld` bundle — deterministic, no LLM, no extraction (unchanged): reads
    the bundle's confirmed `factorStatus`, runs SHACL + the rule engine, and
    renders completeness + the weakener concerns (each attributed to the factor it
    implicates via the pack-declared focus map) + the structural result.

  * an HF model id (`owner/model`) or model URL — fetches the card and extracts
    factor statuses (LLM when a backend is configured, else a deterministic
    README scan), maps to a bundle, then runs the same report. The readout always
    states its extraction provenance, and a gated/absent card renders an honest
    no-card notice rather than a hollow all-weakeners page. The generated bundle
    is saved by default as the auditable, re-runnable source.

    uofa report package.jsonld --pack mrm-nist
    uofa report allenai/OLMo-2-1124-13B-Instruct --pack mrm-nist
    uofa report https://huggingface.co/owner/model --pack mrm-nist --deterministic
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from uofa_cli import paths
from uofa_cli.card_bundle import MRM_NIST_RISK_ASSUMPTION
from uofa_cli.output import error, info
from uofa_cli.report_state import (
    Status,
    assert_report_invariants,
    build_report_state,
    compute_findings,
    sev_label,
)

HELP = "render a credibility report for a bundle, or for an HF model id/URL (fetch + extract)"

_PACK_DISPLAY = {"vv40": "ASME V&V 40", "nasa-7009b": "NASA-STD-7009B", "mrm-nist": "NIST AI RMF"}

# Shown in place of the concerns section when sufficiency was not assessed (the
# heuristic README scan / no-card case). A keyword scan can support completeness
# but not sufficiency-level weakeners, so the readout declines them rather than
# asserting a verdict it cannot back.
_SUFFICIENCY_DECLINED = (
    "Sufficiency (weakener) analysis not assessed in heuristic mode - run with an "
    "LLM backend (--extract-backend ...) for sufficiency analysis."
)

# A pubkey path that does not exist, so SHACL/check runs without attempting
# signature verification on a possibly-unsigned bundle (report never signs).
_NO_PUBKEY = Path("/nonexistent/uofa-report-unsigned.pub")


def add_arguments(parser):
    parser.add_argument("source",
                        help="a UofA bundle (.jsonld), an HF model id (owner/model), "
                             "or an HF model URL")
    parser.add_argument("--format", default="text",
                        choices=["text", "markdown", "json"],
                        help="output format (default: text)")
    parser.add_argument("--output", type=Path, default=None,
                        help="write the report to FILE instead of stdout")
    # ── id/URL mode: fetch + extract ──
    parser.add_argument("--deterministic", action="store_true",
                        help="id mode: skip the LLM and map the card with the README "
                             "section/keyword scan (approximate; needs no model)")
    parser.add_argument("--revision", default=None,
                        help="id mode: model-card git revision (default: latest)")
    parser.add_argument("--save-bundle", metavar="PATH", type=Path, default=None,
                        help="id mode: write the generated bundle to PATH "
                             "(default: ./<owner>__<model>.mrm-nist.jsonld)")
    parser.add_argument("--no-save-bundle", action="store_true",
                        help="id mode: do not keep the generated bundle")
    parser.add_argument("--extract-backend", default=None,
                        choices=["ollama", "anthropic", "openai", "openai-compatible", "bundled", "mock"],
                        help="id mode: LLM backend for extraction (else README scan)")
    parser.add_argument("--extract-model", default=None,
                        help="id mode: model name on the chosen backend")
    parser.add_argument("--extract-base-url", default=None,
                        help="id mode: base URL for openai-compatible backends")


# ── bundle → analysis payload ───────────────────────────────────────────────


def _factor_nodes(bundle: dict) -> list[dict]:
    """Credibility-factor nodes, from either the inlined tree (top-level
    `hasCredibilityFactor`, as the Morrison bundles use) or a compact `@graph`
    array (nodes carrying a `factorType`). Expanded full-IRI JSON-LD is not
    handled — `run` guards on the empty result with a clear message."""
    inline = bundle.get("hasCredibilityFactor")
    if inline:
        return list(inline)
    graph = bundle.get("@graph")
    if isinstance(graph, list):
        return [n for n in graph if isinstance(n, dict) and n.get("factorType")]
    return []


def _factor_statuses(bundle: dict) -> dict[str, str]:
    """factorType -> confirmed factorStatus, straight from the bundle."""
    out: dict[str, str] = {}
    for fac in _factor_nodes(bundle):
        ftype = fac.get("factorType")
        if ftype:
            out[ftype] = fac.get("factorStatus") or "not-assessed"
    return out


def _context(bundle: dict, pack: str) -> dict:
    """Reviewer-facing context re-projected from the bundle. COU name/description
    prefer the ContextOfUse node, falling back to the UofA's own."""
    cou = bundle.get("hasContextOfUse") or {}
    if isinstance(cou, list):
        cou = cou[0] if cou else {}
    if not cou and isinstance(bundle.get("@graph"), list):  # compact @graph form
        cou = next((n for n in bundle["@graph"]
                    if isinstance(n, dict) and "ContextOfUse" in str(n.get("type", ""))), {})
    return {
        "cou_name": cou.get("name") or bundle.get("name"),
        "cou_description": cou.get("description") or bundle.get("description"),
        "standard": _PACK_DISPLAY.get(pack, pack),
        "pack": pack,
        "model_risk_level": bundle.get("modelRiskLevel"),
        "device_class": bundle.get("deviceClass"),
        # A bundle read off disk is not re-verified here; report makes no
        # authenticity claim (the reviewer panel branches on this being absent).
        "authenticity": {},
        # mrm-nist discloses its assumed risk posture; id-mode bundles carry their
        # own extraction provenance + documentation status so a saved bundle
        # re-runs to the identical readout. Absent on a vetted vv40/nasa bundle.
        "risk_assumption": MRM_NIST_RISK_ASSUMPTION if pack == "mrm-nist" else "",
        "extraction_provenance": bundle.get("_extractionProvenance", ""),
        "documentation_status": bundle.get("_documentationStatus", "present"),
        "sufficiency_assessed": bool(bundle.get("_sufficiencyAssessed", True)),
    }


def _shacl(file: Path, pack: str) -> dict:
    """SHACL conformance via the same check path the rest of the CLI uses,
    with rules skipped (firings come from the dedicated rules pass)."""
    from uofa_cli.commands import check as check_cmd

    args = argparse.Namespace(
        file=file, pubkey=_NO_PUBKEY, context=None, rules=None, skip_rules=True,
        build=False, active_packs=[pack], enable_oos=False, disable_oos=False,
        enable_derivations=False, disable_derivations=False,
    )
    cr = check_cmd.run_structured(args)
    return {
        "conforms": cr.shacl.conforms,
        "violations": [
            {"path": getattr(v, "path", None) or (v.get("path") if isinstance(v, dict) else None),
             "message": getattr(v, "message", None) or (v.get("message") if isinstance(v, dict) else None),
             "severity": getattr(v, "severity", None) or (v.get("severity") if isinstance(v, dict) else None)}
            for v in cr.shacl.violations
        ],
    }


def _firings(file: Path, pack: str) -> list[dict]:
    """Rich weakener firings via the Jena engine. Degrades to [] when the
    engine (Java/JAR) is absent — best-effort, matching the Space pipeline."""
    from uofa_cli.commands import rules as rules_mod

    args = argparse.Namespace(
        file=file, rules=None, context=None, build=False, raw=False,
        format="jsonld", output=None, active_packs=[pack],
    )
    try:
        rr = rules_mod.run_structured(args)
    except (FileNotFoundError, RuntimeError):
        return []
    return rules_mod.parse_firings_jsonld(rr.raw_stdout or "")


# ── renderers (read only from ReportState) ──────────────────────────────────


def _glance_severities(state) -> str:
    bits = [f"{state.severity_counts[k]} {sev_label(k)}"
            for k in ("Critical", "High", "Medium", "Low") if state.severity_counts.get(k)]
    return ", ".join(bits) or "none"


def _reconcile(state) -> str:
    level = f" at Level {state.risk_level}" if state.risk_level is not None else ""
    if state.required_all_accounted:
        tail = f"all factors required{level} are accounted for."
    else:
        bits = []
        if state.missing:
            k = len(state.missing)
            bits.append(f"{k} factor{'s' if k != 1 else ''} required{level} still "
                        f"{'need' if k != 1 else 'needs'} evidence")
        if state.open_high_count:
            m = state.open_high_count
            bits.append(f"{m} high-severity concern{'s' if m != 1 else ''} open")
        tail = "; ".join(bits) + " before this is review-ready."
    return f"{state.completeness_pct}% of all factors evidenced; {tail}"


def _render_text(state) -> str:
    L = []
    if state.documentation_status == "none":
        L.append("! NO MODEL CARD PUBLISHED — there is no documentation to assess.")
        L.append("  Every factor below is unassessed as a consequence; the concerns are the")
        L.append("  mechanical result of an absent card, not findings about a real one.")
        L.append("")
    L.append(f"CREDIBILITY REPORT — {state.cou_name}")
    L.append("=" * 60)
    L.append(f"Assessed against : {state.standard}")
    if state.risk_assumption:
        L.append(f"Risk posture     : {state.risk_assumption}")
    else:
        L.append(f"Risk tier        : {state.risk_level if state.risk_level is not None else 'Not stated'}")
    if state.extraction_provenance:
        L.append(f"Extraction       : {state.extraction_provenance}")
    if state.device_class:
        L.append(f"Device class     : {state.device_class}")
    L.append("")
    concerns_glance = _glance_severities(state) if state.sufficiency_assessed else "not assessed (heuristic mode)"
    L.append("AT A GLANCE")
    L.append(f"  Completeness      : {state.completeness_pct}%")
    L.append(f"  Factors evidenced : {state.n_evidenced} of {state.n_expected}")
    L.append(f"  Concerns          : {concerns_glance}")
    L.append(f"  Gate checks passed: {state.gates['passed']} of {state.gates['total']}")
    L.append(f"  {_reconcile(state)}")
    L.append("")
    L.append("CREDIBILITY FACTORS")
    rank = {Status.NOT_STATED: 0, Status.EVIDENCED: 1, Status.NOT_APPLICABLE: 2}
    for f in sorted(state.factors, key=lambda f: (rank[f.status], f.name)):
        L.append(f"  [{f.status.value:<14}] {f.name}")
    L.append("")
    L.append("CONCERNS FOUND")
    if not state.sufficiency_assessed:
        L.append(f"  {_SUFFICIENCY_DECLINED}")
    elif not state.concerns:
        L.append("  None flagged.")
    for c in state.concerns:
        hits = f" (seen {c.hits}x)" if c.hits > 1 else ""
        where = f"  Relates to: {', '.join(c.factors)}." if c.factors else ""
        L.append(f"  - {c.label} concern{hits}. {c.description}{where}")
    L.append("")
    L.append("WHAT IS STILL MISSING")
    if not state.missing:
        L.append("  Nothing required is missing.")
    for n in state.missing:
        L.append(f"  - {n}")
    return "\n".join(L) + "\n"


def _render_markdown(state) -> str:
    L = []
    if state.documentation_status == "none":
        L.append("> **No model card published — there is no documentation to assess.** "
                 "Every factor below is unassessed as a consequence; the concerns are the "
                 "mechanical result of an absent card, not findings about a real one.\n")
    L.append(f"# Credibility report — {state.cou_name}\n")
    L.append(f"- **Assessed against:** {state.standard}")
    if state.risk_assumption:
        L.append(f"- **Risk posture:** {state.risk_assumption}")
    else:
        L.append(f"- **Risk tier:** {state.risk_level if state.risk_level is not None else 'Not stated'}")
    if state.extraction_provenance:
        L.append(f"- **Extraction:** {state.extraction_provenance}")
    if state.device_class:
        L.append(f"- **Device class:** {state.device_class}")
    L.append("\n## At a glance\n")
    L.append(f"| Completeness | Factors evidenced | Concerns | Gate checks |")
    L.append("|---|---|---|---|")
    concerns_cell = _glance_severities(state) if state.sufficiency_assessed else "not assessed (heuristic)"
    L.append(f"| {state.completeness_pct}% | {state.n_evidenced} of {state.n_expected} "
             f"| {concerns_cell} | {state.gates['passed']} of {state.gates['total']} |")
    L.append(f"\n_{_reconcile(state)}_\n")
    L.append("## Credibility factors\n")
    L.append("| Factor | Status |")
    L.append("|---|---|")
    rank = {Status.NOT_STATED: 0, Status.EVIDENCED: 1, Status.NOT_APPLICABLE: 2}
    for f in sorted(state.factors, key=lambda f: (rank[f.status], f.name)):
        L.append(f"| {f.name} | {f.status.value} |")
    L.append("\n## Concerns found\n")
    if not state.sufficiency_assessed:
        L.append(f"_{_SUFFICIENCY_DECLINED}_")
    elif not state.concerns:
        L.append("No concerns were flagged.")
    for c in state.concerns:
        hits = f" (seen {c.hits}×)" if c.hits > 1 else ""
        where = f" Relates to: {', '.join(c.factors)}." if c.factors else ""
        L.append(f"- **{c.label} concern{hits}.** {c.description}{where}")
    L.append("\n## What is still missing\n")
    if not state.missing:
        L.append("Nothing required is missing.")
    for n in state.missing:
        L.append(f"- {n}")
    return "\n".join(L) + "\n"


def _render_json(state) -> str:
    payload = {
        "cou_name": state.cou_name,
        "standard": state.standard,
        "risk_level": state.risk_level,
        "risk_assumption": state.risk_assumption,
        "device_class": state.device_class,
        "documentation_status": state.documentation_status,
        "extraction_provenance": state.extraction_provenance,
        "sufficiency_assessed": state.sufficiency_assessed,
        "completeness_pct": state.completeness_pct,
        "n_evidenced": state.n_evidenced,
        "n_expected": state.n_expected,
        "n_required": state.n_required,
        "required_all_accounted": state.required_all_accounted,
        "open_high_count": state.open_high_count,
        "gates": state.gates,
        "factors": [
            {"name": f.name, "status": f.status.value, "required": f.required,
             "targeting_weakeners": list(f.targeting_weakeners)}
            for f in state.factors
        ],
        "concerns": [
            {"pattern_id": c.pattern_id, "severity": c.severity, "label": c.label,
             "description": c.description, "factors": list(c.factors), "hits": c.hits}
            for c in state.concerns
        ],
        "missing": list(state.missing),
        "severity_counts": state.severity_counts,
    }
    return json.dumps(payload, indent=2) + "\n"


_RENDERERS = {"text": _render_text, "markdown": _render_markdown, "json": _render_json}


# ── id mode: fetch + extract -> bundle ───────────────────────────────────────


def _configured_model_or_none() -> str | None:
    """The model the user has already configured (project uofa.toml or `uofa
    setup`), or None. Lets `uofa report owner/model` prefer the LLM when one is set
    up and fall back to the deterministic scan when none is."""
    try:
        from uofa_cli import setup_state
        proj = paths.find_project_root()
        cfg = paths.load_project_config(proj) if proj else {}
        if cfg.get("model"):
            return cfg["model"]
        s = setup_state.load_config()
        return s.model_tag if s else None
    except Exception:
        return None


def _resolve_extract_llm(args):
    """(model, llm_config) for the extractor. --deterministic -> (None, None) forces
    the README scan; explicit --extract-* -> a resolved llm_config; else a configured
    default model if one exists, otherwise (None, None) -> deterministic."""
    if getattr(args, "deterministic", False):
        return None, None
    if args.extract_backend or args.extract_model or args.extract_base_url:
        from uofa_cli.llm import resolve_llm_config
        ov: dict = {}
        if args.extract_backend:
            ov["backend"] = args.extract_backend
        if args.extract_model:
            ov["model"] = args.extract_model
        if args.extract_base_url:
            ov["base_url"] = args.extract_base_url
        if ov.get("backend") in ("anthropic", "openai"):
            ov.setdefault("api_key_env",
                          {"anthropic": "ANTHROPIC_API_KEY", "openai": "OPENAI_API_KEY"}[ov["backend"]])
        return None, resolve_llm_config(cli_overrides=ov)
    return _configured_model_or_none(), None


def _bundle_out_path(model_id: str, args) -> tuple[Path, bool]:
    """(path, kept). The generated bundle is the auditable, re-runnable source, so id
    mode keeps it by default -- but in a temp cache, NOT the working directory (a
    read-style command shouldn't litter cwd). --save-bundle PATH writes where asked;
    --no-save-bundle discards."""
    import tempfile
    if args.save_bundle:
        return args.save_bundle, True
    if args.no_save_bundle:
        return Path(tempfile.mkdtemp(prefix="uofa-report-")) / "bundle.jsonld", False
    base = Path(tempfile.gettempdir()) / "uofa-report-bundles"
    return base / f"{model_id.replace('/', '__')}.mrm-nist.jsonld", True


def _build_card_bundle(model_id: str, pack: str, args) -> Path | None:
    """Fetch the card and build + save a UofA bundle. Returns the bundle path, or
    None on a hard failure (gated/error). A missing/empty card is NOT a hard
    failure: it yields an honest no-card bundle (documentation_status=none)."""
    from uofa_cli import card_bundle
    from uofa_cli.hf_card import fetch_card

    fetched = fetch_card(model_id, getattr(args, "revision", None))
    if fetched.status in ("gated", "error"):
        error(fetched.detail or f"could not fetch a model card for {model_id}")
        return None

    source_url = f"https://huggingface.co/{model_id}"
    if fetched.status in ("notfound", "empty"):
        # No assessable card -> the honest no-card readout (every in-scope factor
        # unassessed) under a leading notice, never a hollow authoritative page.
        # Sufficiency is not assessed: there is nothing to weaken.
        bundle, _prov, _suff = card_bundle.card_to_bundle("", pack, model_id=model_id,
                                                          source_url=source_url, allow_llm=False)
        provenance, doc_status, sufficiency = "", "none", False
    else:
        model, llm_config = _resolve_extract_llm(args)
        bundle, provenance, sufficiency = card_bundle.card_to_bundle(
            fetched.text, pack, model_id=model_id, source_url=source_url,
            model=model, llm_config=llm_config,
            allow_llm=not getattr(args, "deterministic", False),
        )
        doc_status = "present"

    bundle["_extractionProvenance"] = provenance
    bundle["_documentationStatus"] = doc_status
    bundle["_sufficiencyAssessed"] = sufficiency
    if fetched.sha:
        bundle["_cardRevision"] = fetched.sha

    out_path, kept = _bundle_out_path(model_id, args)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(bundle, indent=2) + "\n", encoding="utf-8")
    if kept:
        info(f"Saved the generated bundle to {out_path}")
        info(f"  re-run deterministically with: uofa report {out_path} --pack {pack}")
    return out_path


# ── entry point ─────────────────────────────────────────────────────────────


def run(args) -> int:
    from uofa_cli.hf_card import resolve_source

    pack = (paths.resolve_active_packs(args) or ["vv40"])[0]
    kind, value = resolve_source(args.source)
    if kind == "error":
        raise ValueError(value)
    if kind == "id":
        bundle_path = _build_card_bundle(value, pack, args)
        if bundle_path is None:
            return 1
    else:
        bundle_path = Path(value)
        if not bundle_path.exists():
            raise FileNotFoundError(f"File not found: {bundle_path}")

    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    statuses = _factor_statuses(bundle)
    if not statuses:
        raise ValueError(
            f"No credibility factors found in {bundle_path} — is this a UofA evidence "
            "bundle? (report needs the inlined or compact-@graph form, not an "
            "expanded reasoned-output dump.)"
        )

    shacl = _shacl(bundle_path, pack)
    # Heuristic / no-card bundles decline sufficiency: skip the weakener engine so the
    # readout reports completeness only (the renderers show the declined notice).
    assess = bool(bundle.get("_sufficiencyAssessed", True))
    firings = _firings(bundle_path, pack) if assess else []
    analysis = compute_findings(pack, statuses, shacl, firings)
    analysis["context"] = _context(bundle, pack)

    state = build_report_state(analysis)        # no gloss CLI-side: canonical names
    assert_report_invariants(state)             # never emit a contradictory report

    rendered = _RENDERERS[args.format](state)
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
        info(f"Wrote {args.format} report to {args.output}")
    else:
        print(rendered, end="")
    return 0

"""uofa report — a deterministic credibility report for an evidence bundle.

Reads a `.jsonld` UofA package and renders one consistent report: completeness
(from the bundle's confirmed `factorStatus`), the weakener concerns the rule
engine fires (each attributed to the credibility factor it implicates, via the
pack-declared focus map), and the structural SHACL result. The same
`uofa_cli.report_state` logic and the six frozen invariants back the demo Space
reviewer view, so the CLI and the Space tell one story.

Pack-aware: pass `--pack nasa-7009b` for a NASA bundle so the factor universe
and focus map match. Fully deterministic — no LLM, no extraction.

    uofa report package.jsonld
    uofa report package.jsonld --format markdown
    uofa report package.jsonld --format json --output report.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from uofa_cli import paths
from uofa_cli.output import error, info
from uofa_cli.report_state import (
    Status,
    assert_report_invariants,
    build_report_state,
    compute_findings,
    sev_label,
)

HELP = "render a deterministic credibility report for a bundle (completeness + concerns)"

_PACK_DISPLAY = {"vv40": "ASME V&V 40", "nasa-7009b": "NASA-STD-7009B"}

# A pubkey path that does not exist, so SHACL/check runs without attempting
# signature verification on a possibly-unsigned bundle (report never signs).
_NO_PUBKEY = Path("/nonexistent/uofa-report-unsigned.pub")


def add_arguments(parser):
    parser.add_argument("file", type=Path, help="UofA evidence bundle (.jsonld)")
    parser.add_argument("--format", default="text",
                        choices=["text", "markdown", "json"],
                        help="output format (default: text)")
    parser.add_argument("--output", type=Path, default=None,
                        help="write to FILE instead of stdout")


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
    L.append(f"CREDIBILITY REPORT — {state.cou_name}")
    L.append("=" * 60)
    L.append(f"Assessed against : {state.standard}")
    L.append(f"Risk tier        : {state.risk_level if state.risk_level is not None else 'Not stated'}")
    if state.device_class:
        L.append(f"Device class     : {state.device_class}")
    L.append("")
    L.append("AT A GLANCE")
    L.append(f"  Completeness      : {state.completeness_pct}%")
    L.append(f"  Factors evidenced : {state.n_evidenced} of {state.n_expected}")
    L.append(f"  Concerns          : {_glance_severities(state)}")
    L.append(f"  Gate checks passed: {state.gates['passed']} of {state.gates['total']}")
    L.append(f"  {_reconcile(state)}")
    L.append("")
    L.append("CREDIBILITY FACTORS")
    rank = {Status.NOT_STATED: 0, Status.EVIDENCED: 1, Status.NOT_APPLICABLE: 2}
    for f in sorted(state.factors, key=lambda f: (rank[f.status], f.name)):
        L.append(f"  [{f.status.value:<14}] {f.name}")
    L.append("")
    L.append("CONCERNS FOUND")
    if not state.concerns:
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
    L.append(f"# Credibility report — {state.cou_name}\n")
    L.append(f"- **Assessed against:** {state.standard}")
    L.append(f"- **Risk tier:** {state.risk_level if state.risk_level is not None else 'Not stated'}")
    if state.device_class:
        L.append(f"- **Device class:** {state.device_class}")
    L.append("\n## At a glance\n")
    L.append(f"| Completeness | Factors evidenced | Concerns | Gate checks |")
    L.append("|---|---|---|---|")
    L.append(f"| {state.completeness_pct}% | {state.n_evidenced} of {state.n_expected} "
             f"| {_glance_severities(state)} | {state.gates['passed']} of {state.gates['total']} |")
    L.append(f"\n_{_reconcile(state)}_\n")
    L.append("## Credibility factors\n")
    L.append("| Factor | Status |")
    L.append("|---|---|")
    rank = {Status.NOT_STATED: 0, Status.EVIDENCED: 1, Status.NOT_APPLICABLE: 2}
    for f in sorted(state.factors, key=lambda f: (rank[f.status], f.name)):
        L.append(f"| {f.name} | {f.status.value} |")
    L.append("\n## Concerns found\n")
    if not state.concerns:
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
        "device_class": state.device_class,
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


# ── entry point ─────────────────────────────────────────────────────────────


def run(args) -> int:
    if not args.file.exists():
        raise FileNotFoundError(f"File not found: {args.file}")

    pack = (paths.resolve_active_packs(args) or ["vv40"])[0]
    bundle = json.loads(args.file.read_text(encoding="utf-8"))

    statuses = _factor_statuses(bundle)
    if not statuses:
        raise ValueError(
            f"No credibility factors found in {args.file} — is this a UofA evidence "
            "bundle? (report needs the inlined or compact-@graph form, not an "
            "expanded reasoned-output dump.)"
        )

    shacl = _shacl(args.file, pack)
    firings = _firings(args.file, pack)
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

"""uofa inject — deterministic single-fault mutation of a UofA package.

Phase 2.5a B2. Wraps `uofa_cli.mutation`; no logic lives here. Produces a mutant
plus a manifest whose site, before/after and diff hash come from the canonical
graph diff rather than from the operator's intent — the ground truth is true by
construction, which is the whole point of the arm.

Class B operators instantiate the rule's antecedent first, and their manifest
records the enriched-clean package as the comparison baseline. That distinction is
load-bearing: an enrichment mutant compared against the raw substrate would report
the enrichment as part of the injected defect.
"""

from __future__ import annotations

import json
from pathlib import Path

from uofa_cli.mutation import engine, operators
from uofa_cli.output import error, info, result_line, step_header

HELP = "inject a known flaw into a package and record it in a manifest"


def add_arguments(parser):
    parser.add_argument("--package", type=Path, required=True, help="substrate package")
    parser.add_argument("--out", type=Path, required=True, help="output directory")
    parser.add_argument("--pattern", help="target pattern id (e.g. W-AL-01)")
    parser.add_argument("--operator", help="operator id (e.g. MUT-DEL-01); overrides --pattern")
    parser.add_argument("--site", type=int, default=0, help="site index (default: 0)")
    parser.add_argument("--all", action="store_true", help="every operator at every site")
    parser.add_argument("--manifest", type=Path, help="manifest path (default: <out>/manifest.json)")
    parser.epilog = (
        "Examples:\n"
        "  uofa inject --pattern W-AL-01 --package pkg.jsonld --out /tmp/m\n"
        "  uofa inject --all --package pkg.jsonld --out /tmp/m\n"
    )


def _select(args) -> list:
    if args.operator:
        return [engine.by_id(args.operator)]
    if args.pattern:
        ops = [o for o in engine.REGISTRY if o.pattern == args.pattern]
        if not ops:
            raise KeyError(f"no operator targets {args.pattern}")
        return ops
    if args.all:
        return [o for o in engine.REGISTRY if o.implemented]
    raise ValueError("give --pattern, --operator, or --all")


def run(args) -> int:
    try:
        selected = _select(args)
    except (KeyError, ValueError) as exc:
        error(str(exc))
        return 2

    step_header("Injecting")
    records, skipped = [], []
    for op in selected:
        if not op.implemented:
            skipped.append((op, f"Class {op.class_ab}, not built"))
            continue
        try:
            if op.class_ab == "B":
                rec, clean = engine.mutate_enriched(op.id, args.package, args.out)
                entry = {**rec.to_json(), "enriched_clean": clean,
                         "expected_catch_layer": op.expected_catch_layer}
            else:
                doc, _ = engine.load_substrate(args.package)
                sites = op.find_sites(doc)
                if not sites:
                    skipped.append((op, "no site on this substrate"))
                    continue
                idxs = range(len(sites)) if args.all else [args.site]
                entry = None
                for i in idxs:
                    rec = engine.mutate(op.id, args.package, i, args.out)
                    if not rec.diff.is_live:
                        skipped.append((op, f"site {i}: {rec.diff.verdict}"))
                        continue
                    records.append({**rec.to_json(),
                                    "expected_catch_layer": op.expected_catch_layer})
                    info(f"  {op.id}  {op.pattern}  site {i}  -> {Path(rec.mutant_path).name}")
                continue
        except engine.EnrichmentNotConformant as exc:
            skipped.append((op, f"enrichment non-conformant: {exc}"))
            continue
        records.append(entry)
        info(f"  {op.id}  {op.pattern}  (enriched)  -> {Path(entry['mutant']).name}")

    manifest = args.manifest or Path(args.out) / "manifest.json"
    Path(manifest).parent.mkdir(parents=True, exist_ok=True)
    Path(manifest).write_text(json.dumps(
        {"substrate": str(args.package), "catalog_note": operators.GATE_DENOMINATOR_NOTE,
         "mutants": records}, indent=1, default=str) + "\n", encoding="utf-8")

    for op, why in skipped:
        info(f"  skipped {op.id} ({op.pattern}): {why}")
    result_line(f"{len(records)} mutant(s) written; manifest {manifest}", bool(records))
    return 0 if records else 1

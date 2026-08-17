"""uofa inject — deterministic single-fault mutation, and scoring of the result.

    uofa inject --pattern W-AL-01 --package pkg.jsonld --out /tmp/m
    uofa rules /tmp/m/<mutant>.jsonld                    # detection, blind
    uofa inject verify --manifest /tmp/m/manifest.json   # scoring, manifest-aware

Detection is deliberately NOT a subcommand here. `uofa rules` is the production
detector; it predates this harness and has no notion of a manifest, which is what
makes the middle step genuinely blind. A detector that could read the answer key
would make the demonstration circular. Scoring is the harness's job and lives in
`verify`.

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

HELP = "inject a known flaw and record it in a manifest; `inject verify` scores the result"


def add_arguments(parser):
    parser.add_argument("--package", type=Path, help="substrate package")
    parser.add_argument("--out", type=Path, help="output directory")
    parser.add_argument("--pattern", help="target pattern id (e.g. W-AL-01)")
    parser.add_argument("--operator", help="operator id (e.g. MUT-DEL-01); overrides --pattern")
    parser.add_argument("--site", type=int, default=0, help="site index (default: 0)")
    parser.add_argument("--all", action="store_true", help="every operator at every site")
    parser.add_argument("--manifest", type=Path, help="manifest path (default: <out>/manifest.json)")
    sub = parser.add_subparsers(dest="inject_command")
    v = sub.add_parser("verify", help="score detection against an injection manifest")
    v.add_argument("--manifest", type=Path, required=True, help="manifest from `uofa inject`")
    v.add_argument("--json", action="store_true", help="emit JSON")
    parser.epilog = (
        "Examples:\n"
        "  uofa inject --pattern W-AL-01 --package pkg.jsonld --out /tmp/m\n"
        "  uofa inject --all --package pkg.jsonld --out /tmp/m\n"
        "  uofa rules /tmp/m/<mutant>.jsonld\n"
        "  uofa inject verify --manifest /tmp/m/manifest.json\n"
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


def _verify(args) -> int:
    """Score every mutant in the manifest, delta against its OWN baseline.

    Two conditions per mutant: the declared target gains a finding, and no
    pre-existing finding disappears. The second is the one that earns its keep --
    a mutation that quietly suppresses a baseline finding passes an absolute
    check, and that signal is what exposed the W-PROV-01 operator's first design,
    where four sites looked like a clean miss and were in fact making the detector
    quieter.

    Suppressions are reported, not auto-failed. Every one measured so far has been
    a correct consequence: remove a structure, and a rule that needed it to bind
    stops firing. Exit is non-zero only on a missed injection.
    """
    m = json.loads(Path(args.manifest).read_text())
    packs = getattr(args, "active_packs", None)
    base_cache: dict[str, dict] = {}
    rows = []
    for r in m["mutants"]:
        if not r.get("mutant"):
            continue
        baseline_pkg = r.get("enriched_clean") or m["substrate"]
        if baseline_pkg not in base_cache:
            base_cache[baseline_pkg] = engine.findings(Path(baseline_pkg), packs)
        base = base_cache[baseline_pkg]
        obs = engine.findings(Path(r["mutant"]), packs)
        target = r["target_pattern"]
        suppressed = {p: base[p] - obs.get(p, 0) for p in base if obs.get(p, 0) < base[p]}
        rows.append({"operator": r["operator"], "pattern": target,
                     "mutant": Path(r["mutant"]).name,
                     "baseline": Path(baseline_pkg).name,
                     "injected": obs.get(target, 0) > base.get(target, 0),
                     "delta": obs.get(target, 0) - base.get(target, 0),
                     "baseline_intact": not suppressed, "suppressed": suppressed})

    if args.json:
        print(json.dumps({"manifest": str(args.manifest), "rows": rows}, indent=1))
        return 0 if all(r["injected"] for r in rows) else 1

    step_header("Verifying injections against the manifest")
    for r in rows:
        info(f"  {r['operator']:11} {r['pattern']:10} "
             f"{'DETECTED' if r['injected'] else 'MISSED':9} (delta {r['delta']:+d})")
        if r["suppressed"]:
            info(f"    suppressed baseline findings: {r['suppressed']}")
    missed = [r for r in rows if not r["injected"]]
    supp = [r for r in rows if not r["baseline_intact"]]
    if supp:
        info(f"  {len(supp)} mutant(s) suppressed a baseline finding — read each; "
             f"every case measured so far was a correct consequence, not a defect")
    result_line(f"{len(rows) - len(missed)}/{len(rows)} injections detected", not missed)
    return 1 if missed else 0


def run(args) -> int:
    if getattr(args, "inject_command", None) == "verify":
        return _verify(args)
    if not args.package or not args.out:
        error("give --package and --out, or use `uofa inject verify --manifest <path>`")
        return 2
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

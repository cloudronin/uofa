"""uofa inject-verify — score detection output against an injection manifest.

Delta-scored, never absolute (Phase 2.5a amendment A3). Each mutant is compared
against its own baseline — the substrate for a single-edit mutant, the
enriched-clean package for an enrichment mutant — on two conditions:

    injected   the declared target gains at least one finding
    intact     no baseline finding is suppressed

The second condition is the one that earns its keep. A mutation that suppresses a
baseline finding is invisible to an absolute check and is the more interesting
failure: the redesign of the W-PROV-01 operator came from exactly that signal,
where four sites looked like a clean miss and were in fact making the detector
quieter.

A suppression is reported, not automatically failed. Every suppression measured so
far has been a correct consequence — deleting a parent structure a second rule
needed in order to bind — so the verdict is the operator author's to read.

Exits non-zero on any missed injection.
"""

from __future__ import annotations

import json
from pathlib import Path

from uofa_cli.commands.detect import findings
from uofa_cli.output import error, info, result_line, step_header

HELP = "score detection against an injection manifest (delta-scored); non-zero on any miss"


def add_arguments(parser):
    parser.add_argument("--manifest", type=Path, required=True, help="manifest from `uofa inject`")
    parser.add_argument("--json", action="store_true", help="emit JSON")


def run(args) -> int:
    m = json.loads(Path(args.manifest).read_text())
    substrate = Path(m["substrate"])
    packs = getattr(args, "active_packs", None)
    base_cache: dict[str, dict] = {}

    rows = []
    for r in m["mutants"]:
        if not r.get("mutant"):
            continue
        baseline_pkg = r.get("enriched_clean") or str(substrate)
        if baseline_pkg not in base_cache:
            base_cache[baseline_pkg] = findings(Path(baseline_pkg), packs)
        base = base_cache[baseline_pkg]
        obs = findings(Path(r["mutant"]), packs)
        target = r["target_pattern"]
        suppressed = {p: base[p] - obs.get(p, 0) for p in base if obs.get(p, 0) < base[p]}
        rows.append({
            "operator": r["operator"], "pattern": target,
            "mutant": Path(r["mutant"]).name,
            "baseline": Path(baseline_pkg).name,
            "injected": obs.get(target, 0) > base.get(target, 0),
            "delta": obs.get(target, 0) - base.get(target, 0),
            "baseline_intact": not suppressed,
            "suppressed": suppressed,
        })

    if args.json:
        print(json.dumps({"manifest": str(args.manifest), "rows": rows}, indent=1))
        return 0 if all(r["injected"] for r in rows) else 1

    step_header("Verifying injections against the manifest")
    for r in rows:
        mark = "DETECTED" if r["injected"] else "MISSED"
        info(f"  {r['operator']:11} {r['pattern']:10} {mark:9} (delta {r['delta']:+d})")
        if r["suppressed"]:
            info(f"    suppressed baseline findings: {r['suppressed']}")

    missed = [r for r in rows if not r["injected"]]
    supp = [r for r in rows if not r["baseline_intact"]]
    if supp:
        info(f"  {len(supp)} mutant(s) suppressed a baseline finding — read each; "
             f"every case measured so far was a correct consequence, not a defect")
    result_line(f"{len(rows) - len(missed)}/{len(rows)} injections detected", not missed)
    return 1 if missed else 0

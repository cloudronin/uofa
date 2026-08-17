"""uofa detect — run detection on a package and report what fired.

Thin alias over the existing rule engine, so the demo's detect half is the
production path rather than a parallel one. With --manifest it additionally
reports whether the declared injected flaw was caught.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from uofa_cli.commands import rules as rules_mod
from uofa_cli.output import error, info, result_line, step_header

HELP = "detect weakeners in a package; with --manifest, check the injected flaw was caught"


def add_arguments(parser):
    parser.add_argument("--package", type=Path, required=True, help="package to assess")
    parser.add_argument("--manifest", type=Path, help="injection manifest to check against")
    parser.add_argument("--json", action="store_true", help="emit JSON")


def findings(package: Path, active_packs=None) -> dict[str, int]:
    ns = argparse.Namespace(file=package, rules=None, context=None, build=False,
                            raw=False, format="summary", output=None,
                            active_packs=active_packs)
    return {f["patternId"]: f.get("hits", 1) for f in rules_mod.run_structured(ns).firings}


def run(args) -> int:
    if not args.package.exists():
        error(f"File not found: {args.package}")
        return 1
    found = findings(args.package, getattr(args, "active_packs", None))

    if args.json:
        print(json.dumps({"package": str(args.package), "findings": found}, indent=1))
        return 0

    step_header("Detection")
    for pid, n in sorted(found.items()):
        info(f"  {pid}  {n} hit(s)")
    if not found:
        info("  no weakeners detected")

    if args.manifest:
        m = json.loads(Path(args.manifest).read_text())
        rows = [r for r in m["mutants"] if r.get("mutant") == str(args.package)]
        if not rows:
            error(f"manifest has no entry for {args.package}")
            return 2
        target = rows[0]["target_pattern"]
        caught = target in found
        result_line(f"declared flaw {target} {'DETECTED' if caught else 'MISSED'}", caught)
        return 0 if caught else 1
    return 0

"""The fourth cell — both NC corpora at both catalog versions. No LLM spend.

    PYTHONPATH=src python studies/phase2_5a/run_fourth_cell.py

Scope and predictions are fixed in advance at FOURTH-CELL-PREDECLARATION.md,
committed at `edafdb9f` before this file existed.

Design. The catalog version is the only variable: the rules file from tag v0.5.7
is passed through `uofa rules`' existing `--rules` override, with current code in
every cell. For a vv40 package `paths.all_rules_files` resolves to exactly one
file -- `packs/core/rules/uofa_weakener.rules` -- so swapping that file swaps the
whole catalog and nothing else. Both versions carry the same 21 rule ids.

Cells A and D are reproduction checks against committed figures (0/176 and
166/171), present because those were produced by 2026-04 code while these cells
use 2026-08 code. If they do not reproduce, the table is not comparable and that
is the finding.

`engine.findings` hardcodes `rules=None`, so this script builds the namespace
itself rather than widening the shipped signature for a study script's benefit.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, "src")

from uofa_cli.adversarial.classifier import _classify           # noqa: E402
from uofa_cli.commands import rules as rules_mod                # noqa: E402
from uofa_cli.mutation import engine as E                       # noqa: E402

P2 = Path("dev/build/adversarial/phase2")
OUT = Path("studies/phase2_5a/fourth_cell_results.json")
OLD_TAG = "v0.5.7"
RULES_PATH = "packs/core/rules/uofa_weakener.rules"

M5 = P2 / "2026-04-26"
HYBRID = P2 / "2026-04-29-v0512"
HOLDOUT = P2 / "holdout-2026-04-29-v0515"


def old_rules() -> Path:
    """Materialize the v0.5.7 catalog to a temp file."""
    blob = subprocess.run(["git", "show", f"{OLD_TAG}:{RULES_PATH}"],
                          capture_output=True, text=True, check=True).stdout
    fh = tempfile.NamedTemporaryFile("w", suffix=".rules", delete=False)
    fh.write(blob)
    fh.close()
    return Path(fh.name)


def findings_with(pkg: Path, rules: Path | None) -> dict[str, int]:
    """`engine.findings`, with the catalog file pinned. `rules=None` = current."""
    ns = argparse.Namespace(file=pkg, rules=rules, context=None, build=False,
                            raw=False, format="summary", output=None,
                            active_packs=["vv40"])
    return {f["patternId"]: f.get("hits", 1)
            for f in rules_mod.run_structured(ns).firings}


def nc_spec_dirs(corpus: Path):
    """NC spec dirs only. Joined on spec_id -> dirname; `out_dir` is pre-rename."""
    batch = json.loads((corpus / "batch_manifest.json").read_text())
    dirs = {d.name: d for d in corpus.glob("*/*") if d.is_dir()}
    for spec in batch.get("perSpecResults", []):
        if spec.get("coverage_intent") != "negative_control":
            continue
        d = dirs.get(spec.get("spec_id"))
        if d is not None:
            yield d, spec.get("spec_id"), spec.get("target_weakener")


def classify_one(job):
    d, spec_id, target, rules = job
    rows = []
    for pkg in sorted(d.glob("*.jsonld")):
        if "attempt" in pkg.name:            # SHACL-retry intermediates
            continue
        if E.conformant(pkg) is not True:
            rows.append({"spec": spec_id, "package": pkg.name,
                         "outcome": "GEN-INVALID", "gen_invalid": True})
            continue
        try:
            fired = findings_with(pkg, rules)
        except Exception:                    # noqa: BLE001
            rows.append({"spec": spec_id, "package": pkg.name,
                         "outcome": "GEN-INVALID", "gen_invalid": True})
            continue
        outcome, _hit = _classify("negative_control", target, fired, True)
        rows.append({"spec": spec_id, "package": pkg.name, "outcome": outcome,
                     "fired": sorted(fired)})
    return rows


def run_cell(label, corpus: Path, catalog: str, rules: Path | None, note: str):
    jobs = [(d, sid, tgt, rules) for d, sid, tgt in nc_spec_dirs(corpus)]
    print(f"\n[{label}] {corpus.name} @ {catalog} -- {len(jobs)} NC specs", flush=True)
    rows = []
    with ThreadPoolExecutor(max_workers=6) as ex:
        for r in ex.map(classify_one, jobs):
            rows.extend(r)

    evaluable = [r for r in rows if not r.get("gen_invalid")]
    clean = [r for r in evaluable if not r.get("fired")]
    by_rule: dict[str, int] = {}
    for r in evaluable:
        for rule in set(r.get("fired") or []):
            by_rule[rule] = by_rule.get(rule, 0) + 1

    rate = len(clean) / len(evaluable) if evaluable else None
    print(f"[{label}] NC clean = {len(clean)}/{len(evaluable)} = "
          f"{rate:.1%}" if evaluable else f"[{label}] no evaluable rows", flush=True)
    return {"cell": label, "corpus": str(corpus), "catalog": catalog, "note": note,
            "packages": len(rows), "gen_invalid": len(rows) - len(evaluable),
            "evaluable": len(evaluable), "clean": len(clean), "nc_clean_rate": rate,
            "firings_by_rule": dict(sorted(by_rule.items(), key=lambda kv: -kv[1])),
            "rows": rows}


def main() -> int:
    old = old_rules()
    print(f"v0.5.7 catalog materialized at {old}", flush=True)

    cells = [
        ("A", M5, "v0.5.7", old,
         "reproduction check -- committed figure is 0/176"),
        ("B", HOLDOUT, "v0.5.7", old,
         "THE RULED CELL -- regenerated holdout against the old catalog"),
        ("C", HYBRID, "v0.5.7", old,
         "tests INV-16's bounded inference -- predicted at or near 0%"),
        ("D", HOLDOUT, "v0.5.15.1", None,
         "reproduction check -- committed figure is 166/171"),
    ]
    results = [run_cell(*c) for c in cells]

    OUT.write_text(json.dumps(
        {"predeclaration": "studies/phase2_5a/FOURTH-CELL-PREDECLARATION.md @ edafdb9f",
         "old_catalog_tag": OLD_TAG, "cells": results}, indent=1) + "\n",
        encoding="utf-8")

    print(f"\n{'cell':<5}{'corpus':<28}{'catalog':<12}{'clean':>12}{'rate':>9}")
    print("-" * 68)
    for r in results:
        rate = f"{r['nc_clean_rate']:.1%}" if r["nc_clean_rate"] is not None else "n/a"
        print(f"{r['cell']:<5}{Path(r['corpus']).name:<28}{r['catalog']:<12}"
              f"{str(r['clean']) + '/' + str(r['evaluable']):>12}{rate:>9}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

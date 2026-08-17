"""M5 re-analysis — re-classify the M5 corpus at v0.5.15.1. No LLM spend.

    PYTHONPATH=src python studies/phase2_5a/run_arm_m5.py

Why this is free: adversarial packages are catalog-version-independent, and the
only rule-body change between the v0.5.13 holdout tag and v0.5.15.1 is one line --
`notEqual(?status, 'not-assessed')` added to W-CON-01 (v0.5.14). Everything else
in that diff is comments. So CE recall at v0.5.15.1 is a re-classification of a
committed corpus, not a regeneration, and the ~$30-50 in P25-A's scoping bought
holdout hygiene that a fixed-corpus two-version comparison does not need.

Why it does not use `uofa adversarial analyze`: the committed `batch_manifest.json`
records each spec's `out_dir` as `out/adversarial/phase2/...`, a path from before
`out/` was renamed to `dev/build/`. The analyzer resolves per-spec manifests
through those paths, finds none, skips all 39 specs, and **exits 0 having written
nothing**. The per-spec manifests are present and committed; only the roll-up's
pointers are stale. This script reads them directly and classifies with the
shipped `classifier._classify`, so the outcome labels are Phase 2's own.
"""

from __future__ import annotations

import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, "src")

from uofa_cli.adversarial.classifier import _classify           # noqa: E402
from uofa_cli.mutation import engine as E                        # noqa: E402

HOLDOUT = Path("dev/build/adversarial/phase2/2026-04-26")
OUT = Path("studies/phase2_5a/m5_results.json")


def spec_dirs():
    """Join the roll-up's metadata to the on-disk package directories.

    Two schemas, and neither alone is sufficient:
      batch_manifest.json  perSpecResults[]  snake_case, HAS coverage_intent and
                                             target_weakener, but its out_dir is
                                             the pre-rename `out/...` path
      <spec>/manifest.json                   camelCase, has specId, but carries
                                             NO intent and NO target

    So the join is on spec_id -> directory name, and `out_dir` is ignored entirely
    because it points at a tree that was renamed to dev/build/ two phases ago.
    """
    batch = json.loads((HOLDOUT / "batch_manifest.json").read_text())
    dirs = {d.name: d for d in HOLDOUT.glob("*/*") if d.is_dir()}
    for spec in batch.get("perSpecResults", []):
        d = dirs.get(spec.get("spec_id"))
        if d is None:
            continue
        yield d, {"spec_id": spec.get("spec_id"),
                  "coverage_intent": spec.get("coverage_intent"),
                  "target_weakener": spec.get("target_weakener")}


def one(args):
    d, man = args
    intent = man.get("coverage_intent")
    target = man.get("target_weakener")
    rows = []
    for pkg in sorted(d.glob("*.jsonld")):
        if "attempt" in pkg.name:            # SHACL-retry intermediates, not results
            continue
        # GEN-INVALID means the generator could not produce a valid package, and
        # Phase 2 excludes those from recall as "not measurable". `package_exists`
        # is the wrong proxy -- the files are on disk. The right test is profile
        # conformance: two CE specs (W-ON-01, W-SI-01) carry shaclFailed=20, all
        # twenty packages, which is exactly why the original analysis reported
        # them not-measurable. Counting them as hits inflated an earlier pass of
        # this script from 76.1% to 78.3%.
        if E.conformant(pkg) is not True:
            rows.append({"spec": man.get("spec_id"), "package": pkg.name,
                         "outcome": "GEN-INVALID", "target_fired": False,
                         "gen_invalid": True, "intent": intent, "target": target})
            continue
        try:
            fired = E.findings(pkg, ["vv40"])
        except Exception:                    # noqa: BLE001
            rows.append({"spec": man.get("spec_id"), "package": pkg.name,
                         "outcome": "GEN-INVALID", "target_fired": False,
                         "gen_invalid": True, "intent": intent, "target": target})
            continue
        outcome, hit = _classify(intent, target, fired, True)
        rows.append({"spec": man.get("spec_id"), "package": pkg.name,
                     "outcome": outcome, "target_fired": hit,
                     "intent": intent, "target": target,
                     "fired": sorted(fired)})
    return rows


def main() -> int:
    work = list(spec_dirs())
    print(f"specs: {len(work)}", flush=True)
    rows = []
    with ThreadPoolExecutor(max_workers=6) as ex:
        for r in ex.map(one, work):
            rows.extend(r)

    by_intent: dict[str, dict] = {}
    for r in rows:
        d = by_intent.setdefault(r["intent"], {"n": 0, "hits": 0, "clean": 0,
                                               "gen_invalid": 0})
        if r.get("gen_invalid"):
            d["gen_invalid"] += 1
            continue                          # excluded from the denominator
        d["n"] += 1
        d["hits"] += bool(r["target_fired"])
        if r["outcome"] == "COV-CLEAN-CORRECT":
            d["clean"] += 1

    ce = by_intent.get("confirm_existing", {"n": 0, "hits": 0})
    nc = by_intent.get("negative_control", {"n": 0, "clean": 0})
    summary = {
        "catalog_version": "v0.5.15.1",
        "corpus": str(HOLDOUT),
        "corpus_note": "M5 (2026-04-26) TRAINING corpus, re-classified at v0.5.15.1; packages unchanged. Optimistic relative to the v0.5.13 holdout -- see M5-REBASELINE-PREDECLARATION.md",
        "rule_delta_since_corpus": "one line: notEqual(?status,'not-assessed') on W-CON-01",
        "by_intent": by_intent,
        "ce_recall": (ce["hits"] / ce["n"]) if ce["n"] else None,
        "nc_clean_rate": (nc.get("clean", 0) / nc["n"]) if nc.get("n") else None,
        "rows": rows,
    }
    OUT.write_text(json.dumps(summary, indent=1) + "\n", encoding="utf-8")
    print(f"\n{'intent':20} {'n':>5} {'target fired':>13} {'clean':>7}")
    for k, v in sorted(by_intent.items(), key=lambda kv: str(kv[0])):
        k = str(k)
        print(f"{k:20} {v['n']:>5} {v['hits']:>13} {v.get('clean',0):>7}")
    if ce["n"]:
        print(f"\nCE recall @ v0.5.15.1 = {ce['hits']}/{ce['n']} = {ce['hits']/ce['n']:.1%}")
    if nc.get("n"):
        print(f"NC clean  @ v0.5.15.1 = {nc['clean']}/{nc['n']} = {nc['clean']/nc['n']:.1%}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

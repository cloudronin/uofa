"""Arm M — the deterministic mutation battery, scored against manifests.

Re-derivation script for studies/phase2_5a. Run from the repo root:

    PYTHONPATH=src python studies/phase2_5a/run_arm_m.py

Writes results.json (per-mutant manifest + scored rollups). A changed result is a
finding about the catalog, not a fixture to resync.

PRECONDITION: the measuring branch must contain 2a1d3544 (fix(shacl): resolve
@context from the shipped file). Without it every conformance reading is a
plausible-looking wrong answer rather than a failure — 0/23 and 23/23 were both
produced that way before it was spotted.

Scoring is DELTA, never absolute (amendment A3). Each mutant is compared against
its own baseline — the substrate for Class A, the enriched-clean package for
Class B — on two conditions:

    injected   the target pattern gains at least one finding
    intact     no baseline finding is suppressed

The second is the one that matters. It caught MUT-REF-01's original design, which
looked like a clean 4/4 miss and was actually a mutation that made the detector
quieter. An absolute check would have reported a rule defect that does not exist.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, "src")

from uofa_cli.mutation import engine as E, operators as O  # noqa: E402

SUBSTRATES = {
    "morrison/cou1": "packs/vv40/examples/morrison/cou1/uofa-morrison-cou1.jsonld",
    "morrison/cou2": "packs/vv40/examples/morrison/cou2/uofa-morrison-cou2.jsonld",
    "nagaraja/cou1": "packs/vv40/examples/nagaraja/cou1/uofa-nagaraja-cou1.jsonld",
}
OUT = Path("dev/build/phase2_5a/mutants")
FIRE = re.compile(r"[⚠⚡]\s+((?:W-[A-Z]+-\d{2}|COMPOUND-\d{2}))\s+\[(\w+)\]\s+—\s+(\d+)\s+hit")


def _cli(cmd: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["python", "-m", "uofa_cli", cmd, "--pack", "vv40", *args],
                          capture_output=True, text=True, timeout=300)


def findings(path) -> dict[str, int]:
    """Canonical, in-process. `uofa rules` is the detector; the harness never
    passes it a manifest, because it must stay blind to what was injected."""
    return E.findings(path, ["vv40"])


def catch_layers(path) -> list[str]:
    """Measured, and NOT exclusive.

    check.run_structured runs C2 → C1 → C2.5 → C3 with no short-circuit, so a
    non-conformant package still reaches the rule engine. 12 of 23 Class A mutants
    are caught by both layers; treating this as a single value would misfile them.
    """
    out = _cli("check", str(path)).stdout
    layers = []
    if "✗ C2 SHACL" in out:
        layers.append("schema")
    if any(f"⚠ {p}" in out or f"⚡ {p}" in out for p in O.MECHANICAL_PATTERNS):
        layers.append("rules")
    return layers


def score(baseline: dict[str, int], observed: dict[str, int], target: str) -> dict:
    injected = observed.get(target, 0) > baseline.get(target, 0)
    suppressed = {p: baseline[p] - observed.get(p, 0)
                  for p in baseline if observed.get(p, 0) < baseline[p]}
    return {"injected": injected, "baseline_intact": not suppressed,
            "suppressed": suppressed,
            "delta": observed.get(target, 0) - baseline.get(target, 0)}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    base = {n: findings(p) for n, p in SUBSTRATES.items()}
    rows: list[dict] = []

    for op in E.REGISTRY:
        if not op.implemented:
            continue
        if op.class_ab == "A":
            for sname, spath in SUBSTRATES.items():
                doc, _ = E.load_substrate(spath)
                for i in range(len(op.find_sites(doc))):
                    rec = E.mutate(op.id, spath, i, OUT)
                    if not rec.diff.is_live:
                        rows.append({**rec.to_json(), "scored": False,
                                     "reason": rec.diff.verdict})
                        continue
                    obs = findings(rec.mutant_path)
                    rows.append({**rec.to_json(), "substrate_key": sname, "scored": True,
                                 "conformant": E.conformant(rec.mutant_path),
                                 "expected_catch_layer": op.expected_catch_layer,
                                 "measured_catch_layer": catch_layers(rec.mutant_path),
                                 **score(base[sname], obs, op.pattern)})
        else:
            # Class B: one mutant per substrate, baseline is the enriched-clean pkg
            for sname, spath in SUBSTRATES.items():
                try:
                    rec, clean = E.mutate_enriched(op.id, spath, OUT)
                except E.EnrichmentNotConformant as exc:
                    rows.append({"operator": op.id, "target_pattern": op.pattern,
                                 "substrate_key": sname, "scored": False,
                                 "reason": f"enrichment non-conformant: {exc}"})
                    continue
                except Exception as exc:                     # noqa: BLE001
                    rows.append({"operator": op.id, "target_pattern": op.pattern,
                                 "substrate_key": sname, "scored": False,
                                 "reason": f"{type(exc).__name__}: {exc}"})
                    continue
                if not rec.mutant_path:
                    rows.append({**rec.to_json(), "substrate_key": sname,
                                 "scored": False, "reason": rec.diff.verdict})
                    continue
                cbase = findings(clean)
                obs = findings(rec.mutant_path)
                rows.append({**rec.to_json(), "substrate_key": sname, "scored": True,
                             "enriched_clean": clean,
                             "conformant": E.conformant(rec.mutant_path),
                             "expected_catch_layer": op.expected_catch_layer,
                             "measured_catch_layer": catch_layers(rec.mutant_path),
                             **score(cbase, obs, op.pattern)})

    gate = O.gate_denominator()
    scored = [r for r in rows if r.get("scored")]
    conformant_flawed = [r for r in scored if r.get("conformant")]

    per_pattern: dict[str, dict] = {}
    for r in scored:
        d = per_pattern.setdefault(r["target_pattern"], {"n": 0, "hits": 0,
                                                         "n_conformant": 0, "hits_conformant": 0,
                                                         "suppressing": 0})
        d["n"] += 1
        d["hits"] += bool(r["injected"])
        if r.get("conformant"):
            d["n_conformant"] += 1
            d["hits_conformant"] += bool(r["injected"])
        d["suppressing"] += (not r["baseline_intact"])

    results = {
        "catalog_version": "v0.5.15.1",
        "substrates": SUBSTRATES,
        "substrate_baselines": base,
        "gate": gate,
        "totals": {"mutants": len(rows), "scored": len(scored),
                   "conformant_but_flawed": len(conformant_flawed),
                   "schema_caught": len(scored) - len(conformant_flawed)},
        "per_pattern": per_pattern,
        "mutants": rows,
    }
    Path("studies/phase2_5a/results.json").write_text(
        json.dumps(results, indent=1, default=str) + "\n", encoding="utf-8")

    print(f"mutants {len(rows)}  scored {len(scored)}  "
          f"conformant-but-flawed {len(conformant_flawed)}  "
          f"schema-caught {len(scored)-len(conformant_flawed)}")
    print(f"gate denominator {gate['denominator']} "
          f"(excluded: {gate['excluded_unfireable'] + gate['excluded_no_conformant_mutant']})")
    print(f"\n{'pattern':11} {'n':>3} {'hits':>5} {'n_conf':>7} {'hits_conf':>10} {'suppressing':>12}")
    for p in sorted(per_pattern):
        d = per_pattern[p]
        print(f"{p:11} {d['n']:>3} {d['hits']:>5} {d['n_conformant']:>7} "
              f"{d['hits_conformant']:>10} {d['suppressing']:>12}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

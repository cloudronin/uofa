"""Wilson 95% score intervals for the Arm M per-pattern table.

W5 of the Ch4 Numbers and Repairs spec. Reads the committed `results.json`; adds
no measurement of its own.

    PYTHONPATH=src python studies/phase2_5a/wilson_intervals.py

Two denominators are reported per pattern, because the report's per-pattern table
carries both and they answer different questions:

  n            engine-measured mutation sites
  conformant n the gate denominator -- mutants that remained schema-conformant,
               so the rules layer is the thing under test

Three patterns (W-ON-01, W-SI-01, W-SI-02) have conformant n = 0: their mutants
are caught by the schema before rules run. They therefore have NO gate interval,
and their raw-n interval must not be quoted as a detection figure.

Writes `wilson_intervals.json` and prints a table.
"""
from __future__ import annotations

import json
import math
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
Z = 1.959963984540054  # two-sided 95%


def wilson(hits: int, n: int, z: float = Z) -> tuple[float, float] | None:
    """Wilson score interval. None when n == 0 (no interval exists)."""
    if n == 0:
        return None
    p = hits / n
    denom = 1.0 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = (z / denom) * math.sqrt(p * (1.0 - p) / n + z * z / (4.0 * n * n))
    return max(0.0, centre - half), min(1.0, centre + half)


def main() -> int:
    data = json.loads((HERE / "results.json").read_text())
    per = data["per_pattern"]
    gate = data["gate"]
    gate_patterns = set(gate["gate_patterns"])
    excluded_no_conformant = set(gate["excluded_no_conformant_mutant"])
    excluded_unfireable = set(gate["excluded_unfireable"])

    rows = []
    for pat in sorted(per):
        v = per[pat]
        raw = wilson(v["hits"], v["n"])
        conf = wilson(v["hits_conformant"], v["n_conformant"])
        rows.append({
            "pattern": pat,
            "n": v["n"], "hits": v["hits"],
            "n_conformant": v["n_conformant"], "hits_conformant": v["hits_conformant"],
            "wilson_raw": raw, "wilson_conformant": conf,
            "in_gate": pat in gate_patterns,
            "excluded_reason": ("no conformant mutant" if pat in excluded_no_conformant
                                else "unfireable" if pat in excluded_unfireable else None),
            "gate_floor_below_half": bool(conf and conf[0] < 0.5),
        })

    out = {"z": Z, "gate_denominator": gate["denominator"],
           "gate_partition": gate["partition"], "rows": rows}
    (HERE / "wilson_intervals.json").write_text(json.dumps(out, indent=2) + "\n")

    def fmt(iv):
        return "     —      " if iv is None else f"[{iv[0]:.3f}, {iv[1]:.3f}]"

    print(f"Wilson 95% intervals, z = {Z:.4f}\n")
    print(f"  {'pattern':12s} {'n':>2s} {'hits':>4s} {'Wilson (raw n)':>16s} "
          f"{'cn':>3s} {'ch':>3s} {'Wilson (conformant n)':>22s}  gate")
    for r in rows:
        mark = "gate" if r["in_gate"] else f"excl: {r['excluded_reason']}"
        print(f"  {r['pattern']:12s} {r['n']:2d} {r['hits']:4d} {fmt(r['wilson_raw']):>16s} "
              f"{r['n_conformant']:3d} {r['hits_conformant']:3d} "
              f"{fmt(r['wilson_conformant']):>22s}  {mark}")

    gated = [r for r in rows if r["in_gate"]]
    below = [r for r in gated if r["gate_floor_below_half"]]
    print(f"\n  gate patterns: {len(gated)} (denominator {gate['denominator']} "
          f"of partition {gate['partition']})")
    print(f"  gate patterns whose Wilson floor sits BELOW 0.5: {len(below)} of {len(gated)}")
    if len(below) == len(gated):
        print("  -> every gate pattern. At n=3 a perfect 3/3 gives a floor near 0.44;")
        print("     at n=1 a perfect 1/1 gives roughly 0.21. No gate row supports a")
        print("     point estimate without its interval printed beside it.")

    raw_clear = [r for r in rows if r["wilson_raw"] and r["wilson_raw"][0] >= 0.5]
    print(f"\n  patterns whose RAW-n floor clears 0.5: "
          f"{[r['pattern'] for r in raw_clear] or 'none'}")
    for r in raw_clear:
        if not r["in_gate"]:
            print(f"    NOTE {r['pattern']} clears on raw n={r['n']} but is excluded from"
                  f" the gate ({r['excluded_reason']}); its conformant n is"
                  f" {r['n_conformant']}, so this interval is NOT a rules-detection figure.")
    print(f"\n  wrote {(HERE / 'wilson_intervals.json').name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

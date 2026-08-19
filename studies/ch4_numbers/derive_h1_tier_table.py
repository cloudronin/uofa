"""Derive the H1 tier table by running the checks, not by finding prose.

E2 of the Ch4 numbers ledger. The tier table should not be located in a document
somewhere; it should be re-derived from the five committed substrate packages by
running the same checks the pipeline runs, so the ledger row is machine-backed
like every other row.

    python studies/ch4_numbers/derive_h1_tier_table.py

Reads each package for its recorded decision outcome and context of use, and
runs `uofa check` for SHACL conformance, integrity (hash + signature) and the
rules phase. Handles both serialisations in use: flat packages (Morrison,
Nagaraja) and `@graph`-wrapped ones (the NASA aerospace pair).

Writes `h1_tier_table.json` beside this file and prints the table. Exit 1 if any
package fails a check, because a substrate that stopped conforming is a finding
rather than a row.
"""
from __future__ import annotations

import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = pathlib.Path(__file__).resolve().parent / "h1_tier_table.json"

SUBSTRATES = [
    ("Morrison COU1", "packs/vv40/examples/morrison/cou1/uofa-morrison-cou1.jsonld", "vv40"),
    ("Morrison COU2", "packs/vv40/examples/morrison/cou2/uofa-morrison-cou2.jsonld", "vv40"),
    ("Nagaraja COU1", "packs/vv40/examples/nagaraja/cou1/uofa-nagaraja-cou1.jsonld", "vv40"),
    ("NASA take-off", "packs/nasa-7009b/examples/aerospace/uofa-aero-cou1-nasa7009b.jsonld", "nasa-7009b"),
    ("NASA cruise", "packs/nasa-7009b/examples/aerospace/uofa-aero-cou2-nasa7009b.jsonld", "nasa-7009b"),
]

MANDATORY = ["bindsClaim", "hasContextOfUse", "hasCredibilityFactor",
             "hasDecisionRecord", "signature", "hash"]


def unwrap(doc: dict) -> tuple[dict, str | None]:
    """Return (UnitOfAssurance node, defect) from either serialisation.

    Flat packages carry it at the root. A `@graph` form may wrap it. If no
    UnitOfAssurance node exists at all the file is not a source package, and
    that is reported rather than rendered as a pile of missing fields.
    """
    if "@graph" not in doc:
        return doc, None
    root = {k: v for k, v in doc.items() if k != "@graph"}
    kinds = set()
    for node in doc["@graph"]:
        for key in ("type", "@type"):
            t = node.get(key)
            for x in (t if isinstance(t, list) else [t]):
                if x:
                    kinds.add(str(x).split("#")[-1])
                if x and str(x).endswith("UnitOfAssurance"):
                    return {**node, **root}, None
    return root, ("no UnitOfAssurance node; @graph holds only "
                  + ", ".join(sorted(kinds)))


def phases(path: str, pack: str) -> dict[str, str]:
    """Run `uofa check` and read its per-phase verdicts."""
    r = subprocess.run(["uofa", "check", path, "--pack", pack],
                       capture_output=True, text=True, cwd=ROOT)
    out = r.stdout
    got = {}
    for label, key in (("C1 Integrity", "integrity"), ("C2 SHACL", "shacl"),
                       ("C3 Rules", "rules")):
        m = re.search(r"([✓✗])\s+" + re.escape(label), out)
        got[key] = ("pass" if m.group(1) == "✓" else "FAIL") if m else "not reported"
    return got


def main() -> int:
    rows, failures = [], []
    for name, rel, pack in SUBSTRATES:
        doc = json.loads((ROOT / rel).read_text())
        u, defect = unwrap(doc)
        dr = u.get("hasDecisionRecord") or {}
        cou = u.get("hasContextOfUse") or {}
        missing = [] if defect else [f for f in MANDATORY if f not in u]
        ph = phases(rel, pack)
        # An engine-output snapshot has weakeners as DATA. Distinguish that from
        # rules firing, or a test asserting a pattern name passes for the wrong
        # reason -- see INV-22 for the same shape in the OOS calibration set.
        inferred = None
        if defect:
            r = subprocess.run(["uofa", "rules", rel, "--pack", pack, "--format", "summary"],
                               capture_output=True, text=True, cwd=ROOT)
            m = re.search(r"Inferred (\d+) new triples", r.stdout + r.stderr)
            inferred = int(m.group(1)) if m else None
        row = {
            "substrate": name, "path": rel, "pack": pack,
            "serialisation": "@graph" if "@graph" in doc else "flat",
            "decision": (dr.get("outcome") if isinstance(dr, dict) else dr) or "—",
            "cou": (cou.get("name") if isinstance(cou, dict) else None) or "—",
            "mrl": u.get("modelRiskLevel", "—"),
            "profile": str(u.get("conformsToProfile", "—")).split("#")[-1],
            "completeness": ("NOT A SOURCE PACKAGE" if defect
                             else "complete" if not missing else f"missing {missing}"),
            "defect": defect,
            "triples_inferred": inferred,
            **ph,
        }
        rows.append(row)
        for k in ("integrity", "shacl"):
            if ph[k] != "pass":
                failures.append(f"{name}: {k} = {ph[k]}")
        if missing:
            failures.append(f"{name}: missing mandatory {missing}")
        if defect:
            failures.append(
                f"{name}: {defect}. `uofa rules` inferred {inferred} new triples, so any "
                f"weakener it prints is read back from the file, not detected.")

    OUT.write_text(json.dumps({"substrates": rows}, indent=2) + "\n")

    hdr = f"  {'substrate':14s} {'ser':7s} {'decision':13s} {'MRL':>3s} {'complete':9s} {'SHACL':6s} {'integ':6s} {'rules':6s}"
    print(hdr)
    for r in rows:
        print(f"  {r['substrate']:14s} {r['serialisation']:7s} {str(r['decision'])[:13]:13s} "
              f"{str(r['mrl']):>3s} {('yes' if r['completeness']=='complete' else 'NO'):9s} "
              f"{r['shacl']:6s} {r['integrity']:6s} {r['rules']:6s}"
              + (f"   <- {r['defect']}, {r['triples_inferred']} triples inferred"
                 if r["defect"] else ""))
    print(f"\n  wrote {OUT.name}")

    if failures:
        print("\n  ESCALATION — a substrate failed a check it is expected to pass:",
              file=sys.stderr)
        for f in failures:
            print(f"    - {f}", file=sys.stderr)
        return 1
    print("  all five substrates pass completeness, SHACL and integrity")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

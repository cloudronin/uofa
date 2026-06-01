"""Apply the pre-registered read to an ablation output (PREREGISTRATION-*-n60).

Reads the raw scorecard JSON written by `ablation.py` and reports, on the hard-core
stratum:
  1. the lift table (danger / posture / escalation / coverage / ECE per condition),
  2. the PRIMARY test  Δ = danger(fired_flag) − danger(catalog_ablated)  with the
     pre-registered CONFIRM / FALSIFY / inconclusive verdict,
  3. the MECHANISM signature (share of fired_flag's dangerous false-OKs that are
     accept-residual-risk — the "flag → acknowledged risk → accept" fingerprint),
  4. the CLEAN read on paired-committed cells (escalate=False in BOTH conditions),
     which isolates commitment quality from commit rate.

Pure logic over the saved answers — no model, no Docker. Usage:

    python -m harness.bakeoff.read_ablation \
        --output harness/bakeoff/results/ablation-raw-n60-2026-05-31-qwen2.5-7b.json
"""
from __future__ import annotations

import argparse
import glob
import json
from pathlib import Path

from harness.bakeoff import score

# Pre-registered thresholds (PREREGISTRATION-2026-05-31-ablation-n60.md). Do not edit
# to fit a result — that is the whole point of pinning them in code.
CONFIRM_DELTA = 0.04
FALSIFY_DELTA = 0.02
MECHANISM_MIN_FRAC = 0.50
MIN_PAIRED_COMMITTED = 12


def _load_rows(corpus_dir: Path) -> list[dict]:
    return [json.loads(Path(f).read_text()) for f in sorted(glob.glob(str(corpus_dir / "*.json")))]


def _lift(card: dict) -> dict:
    return {
        "danger": card.get("dangerous_error_rate"),
        "posture": card.get("posture_accuracy"),
        "escal_rate": card.get("escalation_rate"),
        "cov": card.get("selective_coverage_at_alpha"),
        "ece": card.get("ece"),
        "n": card.get("n"),
    }


def _mechanism_signature(rows: list[dict], answers: list[dict], baseline: list[dict]) -> dict:
    """Dangerous false-OKs under fired_flag, with (a) the accept-residual-risk share
    (the 'flag → acknowledged risk' fingerprint) and (b) what catalog_ablated did on
    the SAME cell — to tell over-commitment (ff commits, ca escalates) from
    worse-commitment (both commit, ff wrong)."""
    by_id = {r["row_id"]: r for r in rows}
    base_by_id = {a.get("row_id"): a for a in baseline}
    harmful = [a for a in answers
               if (r := by_id.get(a.get("row_id"))) and score.score_row(r, a).action_bucket == "harmful"]
    if not harmful:
        return {"n_dangerous": 0, "accept_residual_risk_frac": None, "cells": []}
    arr = sum(1 for a in harmful if a.get("action_class") == "accept-residual-risk")

    def _harm_type(rid):
        b = base_by_id.get(rid)
        if b is None:
            return "?", None
        if b.get("escalate"):
            return "over-commitment (ff commits; ca escalates)", "escalate"
        bucket = score.score_row(by_id[rid], b).action_bucket
        if bucket == "harmful":
            return "shared-danger (both commit to false-OK)", b.get("action_class")
        return "worse-commitment (both commit; ff wrong, ca safe)", b.get("action_class")

    cells = []
    for a in harmful:
        ht, ca_act = _harm_type(a["row_id"])
        cells.append({"row_id": a.get("row_id"), "action_class": a.get("action_class"),
                      "escalate": a.get("escalate"), "harm_type": ht, "catalog_ablated_did": ca_act})
    return {"n_dangerous": len(harmful), "accept_residual_risk_frac": arr / len(harmful), "cells": cells}


def read(output_path: Path, corpus_dir: Path) -> dict:
    results = json.loads(output_path.read_text())
    rows = [r for r in _load_rows(corpus_dir) if r.get("hard_core")]  # pre-reg reads hard-core
    conds = list(results.keys())

    lift = {c: _lift(results[c]["hard_core"]) for c in conds}

    out: dict = {"n_hard_core": len(rows), "conditions": conds, "lift": lift}

    if "fired_flag" in results and "catalog_ablated" in results:
        dff = results["fired_flag"]["hard_core"]["dangerous_error_rate"]
        dca = results["catalog_ablated"]["hard_core"]["dangerous_error_rate"]
        delta = round(dff - dca, 4)
        if delta >= CONFIRM_DELTA and dff > 0:
            verdict = "CONFIRM (detect-without-meaning is harmful)"
        elif abs(delta) <= FALSIFY_DELTA:
            verdict = "FALSIFY (the n=24 inversion was noise)"
        else:
            verdict = "INCONCLUSIVE (do not stand on it; grow more)"
        out["primary"] = {"danger_fired_flag": dff, "danger_catalog_ablated": dca,
                          "delta": delta, "verdict": verdict}
        out["mechanism"] = _mechanism_signature(rows, results["fired_flag"].get("answers", []),
                                                 results["catalog_ablated"].get("answers", []))
        if out["mechanism"]["accept_residual_risk_frac"] is not None:
            out["mechanism"]["holds"] = out["mechanism"]["accept_residual_risk_frac"] >= MECHANISM_MIN_FRAC

    def _committed(a_label, b_label):
        if "answers" not in results.get(a_label, {}) or "answers" not in results.get(b_label, {}):
            return None
        cc = score.committed_comparison(rows, results[a_label]["answers"], results[b_label]["answers"],
                                        label_a=a_label, label_b=b_label)
        cc["powered"] = cc["n_paired_committed"] >= MIN_PAIRED_COMMITTED
        return cc

    out["committed"] = {k: v for k, v in {
        "fired_flag_vs_catalog_ablated": _committed("fired_flag", "catalog_ablated"),
        "full_vs_catalog_ablated": _committed("full", "catalog_ablated"),
    }.items() if v is not None}
    return out


def _print(rd: dict) -> None:
    print(f"\n=== pre-registered read (hard-core n={rd['n_hard_core']}) ===\n")
    print(f"{'condition':<20}{'danger':>8}{'posture':>9}{'escal':>8}{'cov@2%':>8}{'ece':>7}")
    for c, L in rd["lift"].items():
        er = L["escal_rate"]
        print(f"{c:<20}{L['danger']:>8.2f}{L['posture']:>9.2f}{(er if er is not None else 0):>8.2f}"
              f"{L['cov']:>8.2f}{L['ece']:>7.2f}")
    if "primary" in rd:
        p = rd["primary"]
        print(f"\nPRIMARY  Δ = danger(fired_flag) − danger(catalog_ablated) "
              f"= {p['danger_fired_flag']:.3f} − {p['danger_catalog_ablated']:.3f} = {p['delta']:+.3f}")
        print(f"         → {p['verdict']}")
        m = rd["mechanism"]
        if m["n_dangerous"]:
            print(f"MECHANISM  {m['n_dangerous']} dangerous false-OK(s) under fired_flag; "
                  f"accept-residual-risk share = {m['accept_residual_risk_frac']:.2f} "
                  f"(holds ≥{MECHANISM_MIN_FRAC}: {m.get('holds')})")
            for cell in m["cells"]:
                print(f"           - {cell['row_id']}  [ff: {cell['action_class']}]  "
                      f"{cell.get('harm_type','')}")
        else:
            print("MECHANISM  no dangerous false-OKs under fired_flag")
    for pair, cc in rd.get("committed", {}).items():
        a, b = pair.split("_vs_")
        print(f"\nCOMMITTED ({pair}) — cells committed (escalate=False) in BOTH: "
              f"n={cc['n_paired_committed']} (powered ≥{MIN_PAIRED_COMMITTED}: {cc['powered']})")
        for label in (a, b):
            s = cc[label]
            if s.get("n"):
                print(f"   {label:<18} danger={s['dangerous_error_rate']:.2f}  posture={s['posture_accuracy']:.2f}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Apply the pre-registered read to an ablation output.")
    ap.add_argument("--output", type=Path, required=True, help="ablation.py output JSON")
    ap.add_argument("--corpus", type=Path, default=Path("harness/bakeoff/corpus"))
    ap.add_argument("--emit", type=Path, help="also write the structured read to this JSON path")
    args = ap.parse_args()
    rd = read(args.output, args.corpus)
    _print(rd)
    if args.emit:
        args.emit.write_text(json.dumps(rd, indent=2) + "\n")
        print(f"\nwrote structured read → {args.emit}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

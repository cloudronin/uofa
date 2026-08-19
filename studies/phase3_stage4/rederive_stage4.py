"""Re-derive every number in the Stage 4 report from committed artifacts.

W1 of the Ch4 Numbers and Repairs spec. The report cites this script; nothing in
it is transcribed from a conversation. All inputs are force-tracked under
`dev/build/adversarial/` (see .gitignore lines 41-43), so this runs from a clean
clone.

    PYTHONPATH=src python studies/phase3_stage4/rederive_stage4.py

Writes `stage4_readouts.json` beside this file and prints a human-readable
summary. Exit 0 on success; non-zero if any structural invariant fails, because
a readout that silently drops rows is worse than one that stops.
"""
from __future__ import annotations

import collections
import csv
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
TRIAGE = ROOT / "dev/build/adversarial/phase3/triage"
RUN = ROOT / "dev/build/adversarial/phase3/production/run-1"
AGREE = ROOT / "dev/build/adversarial/phase3/adjudication/agreement_stats.json"
OUT = pathlib.Path(__file__).resolve().parent / "stage4_readouts.json"

EXPECTED_CASES = 4556
STRATA = ["CORRECT-DETECTION", "EXISTING-RULE-MISBEHAVIOR",
          "GENERATOR-ARTIFACT", "REAL-GAP", "OUT-OF-SCOPE"]

failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        failures.append(msg)


def load_judgments():
    """Per-judge records, keeping first and last verdict per case_id.

    `align_trios` (src/uofa_cli/adversarial/judge/triage.py) builds
    `{j.case_id: j for j in judgments}`, so the shipped pipeline is LAST-wins.
    First-wins is carried here only to measure the sensitivity (readout 5).
    """
    first, last, stats = {}, {}, {}
    for j in "ABC":
        f, l, n = {}, {}, 0
        for line in (RUN / f"judgments_{j}.jsonl").read_text().splitlines():
            if not line.strip():
                continue
            d = json.loads(line)
            cid = d["case_id"]
            n += 1
            if cid not in f:
                f[cid] = d["verdict"]
            l[cid] = d["verdict"]
        conflicts = sum(1 for k in f if f[k] != l[k])
        stats[j] = {"records": n, "distinct": len(l),
                    "extra_records": n - len(l), "self_conflicting": conflicts}
        first[j], last[j] = f, l
        check(len(l) == EXPECTED_CASES,
              f"judge {j}: {len(l)} distinct case_ids, expected {EXPECTED_CASES}")
    return first, last, stats


def majority(vs):
    top, n = collections.Counter(vs).most_common(1)[0]
    return top if n >= 2 else None


def main() -> int:
    first, last, retry = load_judgments()

    work = {r["case_id"]: r for r in csv.DictReader(
        (TRIAGE / "adjudication_worksheet.csv").open(encoding="utf-8"))}
    key = {r["case_id"]: r for r in csv.DictReader(
        (TRIAGE / "adjudication_sample_key.csv").open(encoding="utf-8"))}
    queue = {r["case_id"]: r for r in csv.DictReader(
        (TRIAGE / "adjudication_queue.csv").open(encoding="utf-8"))}

    check(len(work) == 71, f"worksheet has {len(work)} rows, expected 71")
    check(not (set(work) - set(key)), "worksheet case_ids missing from sample key")
    check(not (set(key) - set(work)), "sample-key case_ids missing from worksheet")
    check(all((r["author_verdict"] or "").strip() for r in work.values()),
          "worksheet has unadjudicated rows")

    # ---- 1. corpus-wide agreement (produced by `uofa adversarial adjudicate`)
    agreement = json.loads(AGREE.read_text()) if AGREE.exists() else {}
    check(agreement.get("case_count") == EXPECTED_CASES,
          f"agreement case_count {agreement.get('case_count')} != {EXPECTED_CASES}")

    # ---- 2. spot-check override rate, per stratum, weighted
    conv = {k: r for k, r in key.items() if r["queue_type"] == "CONVERGENT_SAMPLE"}
    check(len(conv) == 50, f"{len(conv)} convergent cases, expected 50")

    per_stratum, weighted = {}, 0.0
    for s in STRATA:
        ids = [k for k, r in conv.items() if r["stratum"] == s]
        w = float(conv[ids[0]]["stratum_weight"])
        over = [k for k in ids
                if work[k]["author_verdict"].strip()
                != conv[k]["ensemble_majority_verdict"].strip()]
        rate = len(over) / len(ids)
        weighted += w * rate
        per_stratum[s] = {
            "n": len(ids), "overridden": len(over), "rate": rate, "weight": w,
            "contribution": w * rate,
            "became": dict(collections.Counter(
                work[k]["author_verdict"].strip() for k in over)),
        }
    check(abs(sum(v["weight"] for v in per_stratum.values()) - 1.0) < 1e-4,
          "stratum weights do not sum to 1.0")

    # ---- 3. author versus judge, 21-case disagreement queue
    check(len(queue) == 21, f"{len(queue)} queue rows, expected 21")
    vs_judge = {}
    for j in "abc":
        vs_judge[j.upper()] = sum(
            1 for cid, r in queue.items()
            if (r.get(f"verdict_{j}") or "").strip()
            == work[cid]["author_verdict"].strip())
    matched_any = sum(
        1 for cid, r in queue.items()
        if work[cid]["author_verdict"].strip()
        in {(r.get(f"verdict_{j}") or "").strip() for j in "abc"})

    # ---- 4. author verdict distribution, by coverage intent
    verdicts = collections.Counter(
        r["author_verdict"].strip() for r in work.values())

    # ---- 5. dedup sensitivity (W2): does first-wins move any majority?
    moved = [cid for cid in conv
             if majority([first[j][cid] for j in "ABC"])
             != majority([last[j][cid] for j in "ABC"])]
    touched = sum(1 for cid in conv
                  if any(first[j][cid] != last[j][cid] for j in "ABC"))

    result = {
        "expected_cases": EXPECTED_CASES,
        "dedup_policy_shipped": "last-wins (align_trios)",
        "agreement": agreement,
        "retry_characterisation": retry,
        "override": {"per_stratum": per_stratum, "weighted_rate": weighted,
                     "target": 0.10, "verdict": "PASS" if weighted <= 0.10 else "FAIL"},
        "author_vs_judge": {"matches": vs_judge, "n": len(queue),
                            "matched_any_judge": matched_any},
        "author_verdicts": dict(verdicts),
        "dedup_sensitivity": {"majorities_changed": len(moved),
                              "convergent_cases_with_conflicting_retry": touched},
    }
    OUT.write_text(json.dumps(result, indent=2) + "\n")

    # ---------------- human-readable ----------------
    print(f"corpus-wide agreement  (N={agreement.get('case_count')} per pair, "
          f"dedup: last-wins via align_trios)")
    for k in ("cohen_kappa_AB", "cohen_kappa_AC", "cohen_kappa_BC",
              "fleiss_kappa", "raw_agreement_at_least_2of3"):
        if k in agreement:
            print(f"    {k:28s} {agreement[k]:.4f}")

    print("\nretry characterisation")
    for j, s in retry.items():
        print(f"    judge {j}: {s['records']:5d} records, {s['distinct']} distinct, "
              f"{s['extra_records']:4d} extra, {s['self_conflicting']:3d} self-conflicting")
    print(f"    total self-conflicting judge-case pairs: "
          f"{sum(s['self_conflicting'] for s in retry.values())}")

    print("\nspot-check override rate (50 convergent cases)")
    print(f"    {'stratum':28s} {'n':>3s} {'over':>5s} {'rate':>7s} {'weight':>8s} {'contrib':>9s}")
    for s in STRATA:
        v = per_stratum[s]
        print(f"    {s:28s} {v['n']:3d} {v['overridden']:5d} {v['rate']:7.3f} "
              f"{v['weight']:8.4f} {v['contribution']:9.4f}")
    print(f"    weighted = {weighted:.4f}   target <= 0.10   "
          f"{'PASS' if weighted <= 0.10 else 'FAIL'}")
    for s in STRATA:
        if per_stratum[s]["became"]:
            print(f"      {s} overrides became: {per_stratum[s]['became']}")

    print(f"\nauthor versus judge (21 disagreement cases)")
    for j, n in vs_judge.items():
        print(f"    judge {j}: {n}/21 ({n/21:.3f})")
    print(f"    matched some judge: {matched_any}/21 "
          f"-> {21 - matched_any} cases matched no judge")

    print(f"\nauthor verdict distribution (71 rows): {dict(verdicts)}")

    print(f"\ndedup sensitivity (W2)")
    print(f"    convergent majorities changed under first-wins: {len(moved)}")
    print(f"    convergent cases with any conflicting retry:    {touched}")

    print(f"\nwrote {OUT.relative_to(ROOT)}")
    if failures:
        print("\nFAILED INVARIANTS:", file=sys.stderr)
        for f in failures:
            print(f"  - {f}", file=sys.stderr)
        return 1
    print("all structural invariants passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

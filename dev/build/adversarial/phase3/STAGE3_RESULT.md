# Stage 3 — Triage result

**Date:** 2026-07-20
**Input:** the completed Stage 2 judgments, `production/run-1/judgments_{A,B,C}.jsonl` (4,556 cases judged by all three).
**Command:** `uofa adversarial triage --judgments-a/-b/-c … --out dev/build/adversarial/phase3/triage/`
**Config:** prompt `v1.1.0` (gate-7 RELAX path, see [`GATE7_DECISION.md`](GATE7_DECISION.md)); confidence floor 0.6; low-confidence routing on at threshold 0.5.
**Outputs:** `triage/triage_summary.json`, `triage/adjudication_queue.csv`, `triage/tier1_real_gap_candidates.csv`.

## 1. Bucket outcome

| Bucket | Cases | Share |
|---|---:|---:|
| CONVERGENT | 4,535 | 99.5% |
| **DISAGREEMENT** | **21** | **0.5%** |

The Stage 4 adjudication queue is **21 cases**: 15 `all_three_disagree` and 6 `two_disagree_one_uncertain`.

This is far below the pilot's projection. The 100-case pilot saw a 9% disagreement rate, which extrapolated to roughly 410 queued cases; the corpus-scale rate is 0.5%. Stage 4 is therefore a single sitting rather than a multi-week effort.

`low_confidence_forced_routed: 0`. The low-confidence routing control (spec Part 3.1, threshold 0.5) matched no cases. This is the outcome the calibration-v5 diagnosis predicted: Judges B and C miss the UNCERTAIN class at confidence 0.80 to 0.95, well above the routing threshold, so the control cannot catch that pattern. It ran as designed and is retained as a documented control, but it contributed nothing here and should not be described as if it did.

## 2. Ensemble verdict distribution (majority of 3, all 4,556 cases)

| Verdict | Cases | Share |
|---|---:|---:|
| CORRECT-DETECTION | 2,677 | 58.8% |
| EXISTING-RULE-MISBEHAVIOR | 1,161 | 25.5% |
| GENERATOR-ARTIFACT | 398 | 8.7% |
| **REAL-GAP** | **289** | **6.3%** |
| no majority | 21 | 0.5% |
| OUT-OF-SCOPE | 10 | 0.2% |

## 3. §6.7 Tier-1 breakdown of the 289 REAL-GAP cases

Of the 289 majority-REAL-GAP cases, 280 carry at least one §6.7 Tier-1 mapping and 9 cite no candidate. "≥2 judges" counts cases where two or more judges independently named the same Tier-1 id.

| Tier-1 id | cases, ≥1 judge | cases, ≥2 judges | support |
|---|---:|---:|---|
| W-EV-01 | 29 | 15 | yes |
| W-EV-02 | 76 | 53 | yes |
| W-REQ-01 | 48 | 36 | yes |
| W-CX-01 | 71 | 49 | yes |
| W-AR-06 | 69 | 42 | yes |
| W-AR-07 | 17 | 15 | yes |

**All 6 of 6 Tier-1 candidates carry majority-cited REAL-GAP support, against a gate requiring at least 3 of 6.** The margin is not thin: the smallest, W-AR-07, still has 15 cases with two or more judges converging on the same mapping.

W-AR-07 is worth noting separately. It was absent from the 30-case calibration set, which the Phase 3 status report flagged as a risk to this gate, since the ensemble had never been calibrated on it. It nonetheless produced 15 majority-backed instances at corpus scale.

Per-case mappings are in `triage/tier1_real_gap_candidates.csv` (310 rows, 280 distinct cases; one row per case and Tier-1 id, with per-judge verdicts and confidences). That file is the sampling frame for Stage 4.

## 4. What this does and does not establish

This is evidence toward the Tier-1 gate. It is not the gate formally closed. Two limits apply and both should be carried into Ch3.

**Stage 4 has not run.** These are ensemble candidates. The spec makes author adjudication the step that confirms a REAL-GAP, so the defensible present claim is that 6 of 6 Tier-1 candidates have majority-judge support, not that 6 of 6 are confirmed real gaps. Self-blinded adjudication of a sample is what converts the one into the other.

**The catalog version skew still applies.** These judgments were made against the 2026-04-26 corpus, which was generated with the catalog as it stood before the Phase 2.5 refinements took the negative-control clean rate from 0% to 97.1%. A gap the earlier catalog missed is not necessarily a gap in the current one, so some share of the 289 may already be closed. Completing Stage 2 did not address this, and it remains the largest single threat to the finding. Re-baselining Phase 2 on the v0.5.15.1 catalog, or scoping the claim explicitly to the catalog version under test, are the two available responses.

**On the 99.5% convergence rate.** High agreement is a real result, but it should not be read purely as ensemble strength. The calibration record shows the three judges converging on EXISTING-RULE-MISBEHAVIOR for cases the anchor labels UNCERTAIN, which presents as convergence rather than as disagreement. Some portion of the 99.5% is genuine agreement and some is shared blind spot, and the 25.5% ERM share is the place to look first. The 21-case queue measures where the judges disagreed, not the ensemble's total error.

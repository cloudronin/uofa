# Gate-7 result — calibration v5 (prompt v1.2.0)

**Date:** 2026-06-10 (run 2026-06-10T03:08:45Z)
**Iteration:** one only (spec Part 1). **Recommendation: RELAX.** Do not iterate again.

## Headline

The v1.2.0 UNCERTAIN-only §6 lever **worked for Judge B** (UNCERTAIN 20% → 60%; B now clears the per-class floor) but **gate 7 still fails on Judge C** (UNCERTAIN 0%). Judge C's recorded run also fails gate 5 (accuracy 63.3% < 80%), driven mostly by **5 Llama/SambaNova schema-validation hard-failures** (no verdict produced), not a clean prompt regression. v1.2.0 cannot be promoted; production runs on **v1.1.0**.

## Hard gates (v5, prompt v1.2.0)

| Gate | A | B | C |
|---|---|---|---|
| Accuracy ≥ 80% (gate 5) | 96.7% ✅ | 90.0% ✅ | **63.3% ❌** |
| Per-class ≥ 50%, UNCERTAIN (gate 7) | 80% ✅ | **60% ✅** | **0% ❌** |
| Pairwise κ ≥ 0.70 (gate 6) | AB 0.903 ✅ · AC 0.756 ✅ · BC 0.755 ✅ | | |

Fleiss κ (A,B,C) = 0.804. **all_pass = false.**

## Per-class accuracy (v5)

| Class | n | A | B | C |
|---|---:|---:|---:|---:|
| CORRECT-DETECTION | 5 | 100% | 100% | 80% |
| REAL-GAP | 5 | 100% | 100% | 40% |
| GENERATOR-ARTIFACT | 5 | 100% | 100% | 80% |
| EXISTING-RULE-MISBEHAVIOR | 5 | 100% | 80% | 80% |
| OUT-OF-SCOPE | 5 | 100% | 100% | 100% |
| **UNCERTAIN** | 5 | 80% | **60%** | **0%** |

## v4 (v1.1.0) → v5 (v1.2.0) deltas

| Metric | v4 (v1.1.0) | v5 (v1.2.0) | Δ |
|---|---:|---:|---:|
| A accuracy | 96.7% | 96.7% | 0.0 |
| B accuracy | 86.7% | 90.0% | +3.3 |
| C accuracy | 83.3% | 63.3% | **−20.0** (see note) |
| **B UNCERTAIN** | 20% | **60%** | **+40 → now passes** |
| C UNCERTAIN | 0% | 0% | 0 (still fails) |
| κ A/B | 0.879 | 0.903 | +0.024 |
| κ A/C | 0.838 | 0.756 | −0.082 |
| κ B/C | 0.875 | 0.755 | −0.120 |
| Fleiss | 0.863 | 0.804 | −0.059 |

## Judge C accuracy drop — characterization

- The v5 `judge_c_calibration.jsonl` holds **25 of 30 records**: 5 cases produced no valid verdict (Llama/SambaNova schema-validation failures that exhausted retries; the litellm error blocks in `calibrate_run.log`). A and B each have 30/30. The scorer counts the 5 missing cases as incorrect.
- On the 25 cases C answered, it was **19 correct (~76%)**. The 5 hard-failures account for most of the 83.3% → 63.3% fall.
- v4 (v1.1.0) had **30/30** C records and zero failures, so the failures are a property of this v5 run, not of v1.1.0. The v1.2.0 §6 additions lengthen the prompt slightly, which may marginally raise Llama truncation/malformation rate, but the accuracy drop cannot be cleanly attributed to a reasoning regression.
- C's verdict mix shifted REAL-GAP 5 → 2 and added 1 UNCERTAIN; C's UNCERTAIN accuracy stayed 0/5, consistent with the diagnosis that C absorbs ambiguous cases into EXISTING-RULE-MISBEHAVIOR at high confidence. The prompt lever did not move C.

## Regression check (spec Part 1.5)

- **PASS** requires B AND C ≥ 50% on UNCERTAIN with no prior-gate regression. C UNCERTAIN = 0% → PASS not met.
- v1.2.0's recorded run regresses gate 5 for C (63.3% < 80%) and lowers κ A/C and B/C (both stay ≥ 0.70). It is not a clean, promotable improvement.

## Recommendation: RELAX

Production runs on **v1.1.0** — the stable baseline where A/B/C are all ≥ 80%, all pairwise κ ≥ 0.70, and only the gate-7 UNCERTAIN floor is unmet (for B and C). The gate-7 floor is relaxed per the spec v1.7 §15.1 #7 amendment in `GATE7_DECISION.md`. One iteration spent; no further tuning.

## Operational note for Stage 2

Judge C (Llama via SambaNova) showed a **5/30 hard-failure rate** in this run. In production, `--resume` re-judges any case missing from any judge, so these self-heal across daily passes, but watch the C counts and the error column in `daily_status.log`; a persistent high C-failure rate would slow completion and add re-judge cost.

# Phase 2.5 Phase C — 450-package holdout validation

**Date**: 2026-04-29
**Catalog version under test**: v0.5.13 (commit `3401cef`, tag `v0.5.13-phase2v2-prompt-cleanup`)
**Holdout corpus**: `out/adversarial/phase2/holdout-2026-04-29-v0513/` (gitignored)
**Generation cost**: $44.44
**Total session cost**: $79.25 ($34.81 A+B + $44.44 C)

---

## TL;DR

**Band classification: MODERATE.** Holdout NC clean rate (87.5% of validated)
falls between the 70–90% moderate band and the ≥90% strong band. CE recall
generalizes essentially unchanged (-0.6 pp delta, well within sampling
variance). One actionable finding surfaced: a narrow precision bug in
W-CON-01 on `factorStatus='not-assessed'` factors at low MRL.

The catalog generalizes well on **sensitivity** (CE recall) and reasonably
on **specificity** (NC clean rate), with one specific predicate edge case
surfaced for future iteration.

---

## Catalog-level metrics: M5 baseline vs holdout

| Metric | M5 baseline (4605 pkg) | Holdout (483 pkg) | Δ |
|---|---|---|---|
| Total packages | 4605 | 483 | — |
| CE rows (target_weakener present) | 4005 | 420 | — |
| CE recall (target_rule_fired) | **69.2%** (2771/4005) | **68.6%** (288/420) | **−0.6 pp** |
| NC rows | 180 | 18 | — |
| NC clean rate (correct/total) | 95.0% (171/180) | 77.8% (14/18) | −17.2 pp |
| NC clean rate (correct/validated) | **97.2%** (171/176) | **87.5%** (14/16) | **−9.7 pp** |
| NC GEN-INVALID rate | 2.2% (4/180) | 11.1% (2/18) | +8.9 pp |
| GP MISS rate | 0.0% | 0.0% | 0 |

**CE recall: -0.6 pp.** Within sampling variance for a 420-package sample.
The catalog's sensitivity (does the right rule fire on a target?)
generalizes cleanly.

**NC clean rate (validated): -9.7 pp.** The catalog's specificity (do NCs
stay clean?) shows a measurable gap on fresh corpus. Two of 16 validated
NCs fire a rule (vs M5's 5 of 176).

**NC GEN-INVALID rate: +8.9 pp.** Higher generation-failure rate on the
holdout reflects the LLM token-limit / SHACL-retry issues observed in
Phase B (NC-3 / NC-4 Complete-profile content runs hot at 10K-12K
max_tokens). This is a pipeline issue, not a catalog issue.

---

## Per-rule NC firings: M5 vs holdout

| Rule | M5 NC firings | Holdout NC firings | Note |
|---|---|---|---|
| W-EP-04 | 5 | 0 | Holdout had no NC-7 / MRL>2 + not-assessed cases |
| W-CON-01 | 0 | **2** | **NEW finding** — not-assessed factors at low MRL |
| W-CON-04 | 0 | 0 | ✓ |
| W-ON-02 | 0 | 0 | ✓ |
| W-AR-02 | 0 | 0 | ✓ |
| W-AR-01 | 0 | 0 | ✓ |
| COMPOUND-* | 0 | 0 | ✓ |

The 2 W-CON-01 firings are on **NC-2 (Minimal Morrison COU1)** packages
where factors have `factorStatus='not-assessed'` (no levels declared).

---

## Investigation: W-CON-01 firings on NC-2

Both holdout NC-2 packages (`adv-2026-p2-202-nc-clean-minimal-morrison-cou1
v01 / v02`) fire W-CON-01 because:

```
W-CON-01 predicate (v0.5.12):
  outcome == 'Accepted' AND
  factor.factorStatus != 'scoped-out' AND
  factor.factorStatus != 'not-applicable' AND
  noValue(requiredLevel) AND noValue(achievedLevel)
```

The guard excludes `scoped-out` and `not-applicable` but NOT `not-assessed`.
So a factor with `factorStatus='not-assessed'` and missing levels DOES
fire the rule.

**Is the firing legitimate?** Mostly no:
- Per Morrison COU1's documented narrative: "(6 factors not assessed
  (acceptable at MRL 2))"
- Per V&V 40 spec: at MRL 2 (low risk), some factors can legitimately be
  marked not-assessed without compromising the credibility argument
- W-EP-04 already handles the high-MRL case (`factorStatus='not-assessed'`
  AND modelRiskLevel > 2)
- W-CON-01 firing on the same factors at MRL ≤ 2 is **redundant /
  spurious**

**Why M5 didn't catch this**: M5's NC-2 corpus had 18 packages (3
subtleties × 3 base_cous × 2 variants). M5 was processed with
`--base-cou-override`. Those base_cous (cou1 + cou2 + nagaraja) have
varying MRLs. Some packages may have inherited higher MRL where
`factorStatus='not-assessed'` is correctly flagged by W-EP-04. The
specific "Minimal + low MRL + not-assessed factor" combination wasn't
exercised in M5 — but IS the default in the holdout when no
`--base-cou-override` is supplied.

This is a real generalization gap. It would benefit from a v0.5.14
predicate refinement adding `notEqual(?status, 'not-assessed')` to the
W-CON-01 guard (deferring not-assessed concerns to W-EP-04 entirely).

---

## Per-battery distribution

| Battery | Holdout count | M5 proportion target | Actual proportion |
|---|---|---|---|
| confirm_existing | 420 | 86.96% | 86.96% ✓ |
| negative_controls | 18 | 3.91% | 3.73% ≈ |
| gap_probe | 35 | 7.17% | 7.25% ✓ |
| interaction | 10 | 1.95% | 2.07% ✓ |

Distribution matches M5 proportions cleanly.

---

## Outcome class breakdown

| Outcome class | M5 | Holdout |
|---|---|---|
| COV-HIT-PLUS (CE: target rule + bystanders fire) | 2861 | 297 |
| COV-WRONG (CE: target rule didn't fire) | 1184 | 125 |
| GEN-INVALID (SHACL retry exhausted) | 384 | 45 |
| COV-CLEAN-CORRECT (NC: 0 firings) | 171 | 14 |
| COV-CLEAN-WRONG (NC: rules fired) | 5 | 2 |

---

## Band classification proposal

Per the plan's three bands:

| Band | Criterion | Result |
|---|---|---|
| Strong | NC clean ≥ 90% AND recall within 5 pp | **NO** — NC clean 87.5% < 90% |
| Moderate | NC clean 70–90% AND recall within 10 pp | **YES** — 87.5% ∈ [70, 90], recall delta 0.6pp ≤ 10pp |
| Weak | NC clean < 70% OR recall drop > 15 pp | NO |

**Recommended band: MODERATE.** Catalog generalizes credibly with one
specific actionable finding (W-CON-01 / not-assessed predicate gap).

**Slide 19 / Paper A messaging implications**:
- ✓ "Phase 2.5 catalog refinement validated on 483-package fresh holdout
  corpus: CE recall 68.6% (M5 baseline 69.2%, delta -0.6 pp within
  sampling variance), NC clean rate 87.5% on validated NCs."
- ⚠ Honest caveat: "One precision bug surfaced (W-CON-01 firing on
  `factorStatus='not-assessed'` factors at MRL ≤ 2; defers to v0.5.14
  predicate refinement)."

---

## What this validates

1. **CE recall is robust**: -0.6 pp delta on 420 fresh CE packages is
   strong evidence the catalog generalizes for sensitivity. The Phase 2.5
   rule-tightening work didn't fit M5 in a fragile way.

2. **NC clean rate generalizes mostly**: 87.5% is a meaningful gap from
   M5's 97.2% but not catastrophic. Both gaps trace to a single
   identifiable cause (W-CON-01 not-assessed handling).

3. **No regression on fixed rules**: W-ON-02, W-AR-02, W-CON-04, W-AR-01,
   COMPOUND-01/03 all show 0 NC firings on the holdout — the v0.5.10/11/12
   fixes generalize cleanly.

4. **Pipeline robustness gap**: GEN-INVALID rate up from 2.2% to 11.1%.
   The pipeline halts on token-limit / SHACL-retry exhaustion more often
   on fresh runs than on the M5 corpus (which was filtered to clean
   variants). Phase 2 v3 should investigate whether to bump max_tokens
   further or move to streaming generation.

---

## What this surfaces (for future work)

### Issue #1: W-CON-01 predicate gap on `factorStatus='not-assessed'`

**Symptom**: 2 of 16 validated NCs fire W-CON-01 on
`factorStatus='not-assessed'` factors at MRL=2.

**Diagnosis**: v0.5.12 W-CON-01 predicate guard added
`notEqual(?status, 'scoped-out')` and `notEqual(?status, 'not-applicable')`
but missed `notEqual(?status, 'not-assessed')`. The Phase 2.5 spec
treated 'not-assessed' as W-EP-04's domain (which checks MRL>2). At
MRL≤2 the case falls through both rules — W-EP-04 doesn't fire (MRL
threshold), W-CON-01 fires (predicate gap).

**Recommendation**: v0.5.14 predicate refinement adding
`notEqual(?status, 'not-assessed')` to W-CON-01. This would also need
re-validation on M5 to ensure no CE recall regression (W-CON-01 CE
targets explicitly emit `factorStatus='assessed'`, so the change should
be safe).

### Issue #2: Pipeline GEN-INVALID rate

**Symptom**: 11.1% NC GEN-INVALID rate on holdout vs 2.2% on M5
(filtered).

**Diagnosis**: LLM token-limit / SHACL-retry exhaustion. Mostly seen on
Complete-profile NCs that hit max_tokens before completing the rich
content.

**Recommendation**: Phase 2 v3 — bump max_tokens to 16K for Complete
NCs OR investigate streaming generation.

---

## Cumulative catalog progression

| Milestone | Recall | NC clean (val) | Source |
|---|---|---|---|
| M5 baseline (v0.5.7) | 0.7339 | 0/176 = 0.0% | post-M5 analyze |
| v0.5.12.1 (post-Phase 2.5) | held | 175/180 = 97.2% | after_w_ar_01.csv |
| **v0.5.13 holdout** | **68.6%** (vs M5 69.2%, -0.6) | **14/16 = 87.5%** | this report |

---

## Final outcome: MODERATE band (user-confirmed 2026-04-29)

User confirmed band classification on 2026-04-29 with directive to
proceed with both follow-up fixes after tagging:

1. **v0.5.14 W-CON-01 predicate refinement** — fix the not-assessed
   gap surfaced by the holdout
2. **Pipeline GEN-INVALID fix** — bump max_tokens / address LLM
   token-limit truncation

### Slide 19 / Paper A messaging (suggested)

Honest moderate-band wording for the talk and paper:

> "Phase 2.5 catalog refinement was validated on a 450-package fresh
> holdout corpus (M5-proportional distribution; 21 CE / 9 NC / 7 GP /
> 2 INT specs). CE recall: 68.6% (M5 baseline 69.2%, Δ −0.6 pp within
> sampling variance). NC clean rate: 87.5% on validated NCs (M5
> baseline 97.2%, Δ −9.7 pp). The Phase 2.5 rule fixes generalize for
> sensitivity (CE recall) without measurable regression. NC clean
> rate shows a moderate gap traced to a single predicate edge case
> (W-CON-01 firing on `factorStatus='not-assessed'` factors at low
> MRL), addressed in v0.5.14."

### Tag

`holdout-v0513-validation` (annotated, pushed). Corpus dir gitignored
per established Phase 2.5 convention; the patch tools, spec yamls,
and driver scripts under `tools/phase2_5/` are the deterministic
regenerator.

### Cumulative Phase 2.5 evidence chain

- M5 baseline (2026-04-26): catalog under test
- v0.5.7-v0.5.12: rule-tightening + corpus-regen iterations
- v0.5.12.1 (2026-04-28): generator-hook consistency + production bug fix
- v0.5.13 (2026-04-28): NC prompt cleanup; hooks retained
- **v0.5.13 holdout (2026-04-29): MODERATE band — generalization validated**
- v0.5.14 (forthcoming): W-CON-01 not-assessed guard + max_tokens bump

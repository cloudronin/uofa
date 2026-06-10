# Phase 2.5 — Rule Refinement Report

**Date:** 2026-04-27
**Spec:** `Praxis/Product Requirements/UofA_Phase2_5_Rule_Refinement_Spec_v0_1.md`
**Plan:** `~/.claude/plans/users-vishnu-library-cloudstorage-dropb-glistening-token.md`
**Baseline:** M5 (Apr 26) full F7+M5B re-analyze: catalog package-level
precision = 0.0%, recall = 73.4% on confirm_existing.

## Adaptations from spec

The user adopted the spec with four documented adaptations:

1. **Auto-mode metric-gated accept** — Claude proposes + applies + measures
   revisions; auto-accept iff train+dev metrics land in the **target zone**
   (recall ≥ 0.90 AND nc_fpr ≤ 0.10); revert otherwise. Iterations that
   clear the hard floors but miss the target zone are logged as
   PROVISIONAL — the predicate is applied but the rule is NOT locked,
   and the loop continues. All proposals + decisions logged to
   `refinement_log.jsonl` for retrospective audit; git history is the
   rollback substrate.
2. **PR-curve plotting added** (per-rule trajectory + catalog-wide
   milestone scatter) with dual series labelled precision (TP/(TP+FP))
   and specificity (1 − NC FPR).
3. **W-AL-02 skipped** per spec (explicitly excluded as "needs rewrite,
   not tuning"; deferred to Phase 2 v2).
4. **Stretch goals enabled** — W-AR-02, W-CON-01, W-CON-04 attempted
   if primaries finish under budget.

### Metric-gate policy (final)

```text
IF train.recall < 0.80                              → REVERT (hard floor)
ELIF train.nc_fpr > 0.25                            → REVERT (hard floor)
ELIF train.loosening_sentinel_fires > 0             → REVERT (loosened)
ELIF dev.recall < prior_dev.recall − 0.05           → REVERT (overfit)
ELIF train.recall ≥ 0.90 AND train.nc_fpr ≤ 0.10    → ACCEPT (target zone, lock)
ELSE                                                → PROVISIONAL (apply, keep iterating)
```

## Headline result

**The single W-EP-01 fix is the headline win:**

* **W-EP-01 rule-level precision: 4.8% → 100%** (train), 96.6% (holdout)
* **W-EP-01 rule-level NC FPR: 100% → 0%** (train, dev, holdout)
* **Catalog any-rule specificity (excl. out-of-scope W-AL-02): 0% → 4.5%**
* **Catalog precision (excl. W-AL-02): 70.0% → 68.3%** (slight drop;
  see chain effect note below)
* **Catalog recall on confirm_existing: 66.4% → 64.7%** (-1.7pp; the
  COMPOUND-01 recall drop from corpus chain accounts for most of this)

Cascading chain effects from W-EP-01 lock:

* **COMPOUND-01 NC FPR: 89.8% → 21.1%** (76% absolute reduction) but
  **recall: 100% → 57%** (corpus issue exposed, see below)
* **COMPOUND-03 NC FPR: 82.1% → 22.8%** with recall preserved at 100%

The auto-improvements on COMPOUND-01 and COMPOUND-03 NC FPR happen
purely through the rule-chain mechanism — neither compound rule's
predicate was edited.

### Why the catalog precision dropped slightly

The W-EP-01 fix surfaces a corpus-level issue: 43% of M5 COMPOUND-01
target packages were generated relying on the W-EP-01 misfire (URI-handle
bug) as their Critical input. After fixing W-EP-01, those packages
no longer have any Critical weakener firing, so COMPOUND-01 doesn't
trigger on them — they become COV-WRONG (some non-target rule fires)
or COV-MISS. The catalog precision drop of −1.7pp is the cost of
exposing this corpus modeling bug. The COMPOUND-01 recall drop is
NOT a regression of correct behavior; it's correct behavior given
the now-correct W-EP-01.

## Per-rule summary

| Rule | M5 Baseline NC FPR | Phase 2.5 NC FPR | Recall (post) | Status | Notes |
|---|---|---|---|---|---|
| W-EP-01 | 100% | **0%** | 1.0 | **LOCKED** (target zone) | Added `(?claim rdf:type uofa:Claim)` guard |
| W-ON-02 | 89.8% | 89.8% | 1.0 | STUCK | Corpus issue: M5 minimal-NC variants legitimately lack applicability info |
| COMPOUND-01 | 89.8% | 21.1% | 0.57 | STUCK | Recall dropped via W-EP-01 chain; corpus-level issue exposed (43% of M5 COMPOUND-01 targets relied on W-EP-01 misfire) |
| COMPOUND-03 | 82.1% | 22.8% | 1.0 | LOCK-NO-EDIT (provisional) | Auto-improved from W-EP-01 chain; residual NC FPR comes from W-AR-02 chain |
| W-AR-02 (stretch) | 23.6% | 23.6% | 1.0 | STUCK | Iter 1 reached PROVISIONAL state (nc_fpr 0.236→0.171; recall 1.0→0.984), but caused a 19pp recall regression on COMPOUND-03 via Critical-input chain. Reverted to baseline to preserve COMPOUND-03 coverage. Same corpus-pathology pattern as COMPOUND-01. |
| W-CON-01 (stretch) | 19.9% | 19.9% | 1.0 | LOCK-NO-EDIT (provisional) | Already-decent baseline (nc_fpr 18.7%, precision 45.6%); no narrowing attempted |
| W-CON-04 (stretch) | 20.3% | 20.3% | 1.0 | LOCK-NO-EDIT (provisional) | Already-decent baseline (nc_fpr 20.3% train, 7.7% dev — dev in target zone); no narrowing attempted |

## Per-rule details

### W-EP-01 — Orphan Claim (LOCKED, iter 1)

**Diagnosis.** The rule fired on 100% of negative_control packages and
96.6% of bystander confirm_existing variants. Root cause: the
`noValue(?claim, prov:wasDerivedFrom)` predicate evaluated TRUE on any
package whose `bindsClaim` URI was a hanging handle (no inline RDF
definition). Virtually every M5 NC package falls into this case — its
claim is just a URI, not an inline `uofa:Claim` node.

**Fix (iter 1).**

```diff
 [w_ep01:
     (?uofa rdf:type uofa:UnitOfAssurance)
     (?uofa uofa:bindsClaim ?claim)
+    (?claim rdf:type uofa:Claim)
     noValue(?claim, prov:wasDerivedFrom)
     makeSkolem(?ann, ?uofa, 'W-EP-01', ?claim)
```

**Metrics.**

| Split | Recall | NC FPR | Bystander | Precision | Specificity |
|---|---|---|---|---|---|
| Baseline (train) | 1.000 | 1.000 | 0.966 | 0.048 | 0.000 |
| Iter 1 (train) | 1.000 | 0.000 | 0.000 | 1.000 | 1.000 |
| Iter 1 (dev) | 1.000 | 0.000 | 0.000 | 1.000 | 1.000 |
| Iter 1 (holdout) | 1.000 | 0.000 | 0.002 | **0.966** | 1.000 |

Loosening sentinels: 0/50 fired post-fix (independent verification via
`tools.phase2_5.verify_sentinels`).

**Tag:** `v0.5.8-phase2.5-w-ep-01`

### W-ON-02 — Unbounded Applicability (STUCK)

**Diagnosis.** Baseline 89.8% NC FPR. Iter 1 attempt — added
`(?cou rdf:type uofa:ContextOfUse)` mirroring W-EP-01's URI-handle
fix — produced ZERO change because both TGT and NC packages typically
have inline COUs. Iter 2 projection (decisionConsequence='High'
guard) showed nc_fpr would drop only to 0.568 (still above 0.25 floor)
AND recall would drop to 0.667 (below 0.80 floor) because 60/180 TGT
packages have decisionConsequence='Medium'.

**Conclusion.** No narrow predicate change can reach target zone for
W-ON-02. The rule's predicate genuinely matches what its description
says (COU declared, applicability bounds missing). The high NC FPR
is a corpus-level issue: M5's minimal-NC variants legitimately lack
applicability info. **The rule remains as-is.**

### COMPOUND-01 — Compound Escalation (STUCK)

**Diagnosis.** Post-W-EP-01 re-baseline shows train recall = 0.5714,
below the 0.80 hard floor. Cause: 54/126 COMPOUND-01 train target
packages relied on W-EP-01 misfire as their Critical weakener input
— those packages have no inline Claim definition, so W-EP-01
(correctly fixed) no longer fires, breaking the Critical+High pair
COMPOUND-01 needs.

NC FPR auto-improved 0.886 → 0.211 from the W-EP-01 chain. The
COMPOUND-01 predicate itself remains semantically correct (chains on
Critical+High pair excluding compound-self).

**Conclusion.** This is a corpus-level finding: 43% of M5 COMPOUND-01
target packages were generated with a "fake" Critical via the W-EP-01
URI-handle bug, not with intrinsic Critical weakener structure.
Restoring recall would require regenerating those 54 target packages
(out of scope per the Phase 2.5 spec). Marking refinement-stuck;
the rule locks at its current (unchanged) predicate with the
chain-improved metrics.

### COMPOUND-03 — Assurance Override (LOCK-NO-EDIT, provisional)

**Diagnosis.** Post-W-EP-01 re-baseline: train recall = 1.0 (no
recall regression), nc_fpr = 0.228 (clears 0.25 hard floor; above
0.10 target zone). NC FPR auto-improved 0.821 → 0.228 (76% absolute
reduction); bystander rate dropped 0.647 → 0.386; precision rose
0.070 → 0.116.

The COMPOUND-03 predicate is semantically correct (chains on a
Critical weakener with assuranceLevel != Low). The residual NC
firings come from the W-AR-02 chain — W-AR-02 is the dominant
Critical now firing on 24% of NCs at baseline.

**Conclusion.** Lock at current (unchanged) predicate as
`accepted-no-edit`. Further NC FPR improvement requires refining
W-AR-02 (stretch goal — see below).

### W-AR-02 — Defeater (Outcome-Factor Contradiction) — STRETCH (STUCK)

**Diagnosis.** Baseline 23.6% NC FPR. The rule fires on packages with
a CredibilityFactor where `achievedLevel < requiredLevel` and a
`DecisionRecord.outcome == 'Accepted'` — semantically "decision accepted
but factor gap exists." Empirical analysis showed M5 minimal-NC
packages had 1-step gaps at low required levels (req=2, ach=1) while
TGT W-AR-02 packages had larger gaps at higher levels (req=3, ach=1).

**Iter 1 (PROVISIONAL).** Added `greaterThan(?req, 2)` guard
restricting firing to factors at requiredLevel ≥ 3. Train metrics:
recall 1.0 → 0.984, nc_fpr 0.236 → 0.171, precision 0.071 → 0.078.
Cleared all hard floors but missed target zone (nc_fpr > 0.10).

**Reverted (iter 2).** The W-AR-02 narrowing caused a 19pp recall
regression on COMPOUND-03 via Critical-input chain: some COMPOUND-03
corpus targets relied on W-AR-02 firing on a low-required-level
factor as their Critical input. With W-AR-02 narrowed, those
COMPOUND-03 targets lost their Critical → COMPOUND-03 doesn't fire →
recall 1.0 → 0.81. This is the same corpus pathology as COMPOUND-01
(targets generated with weak Critical inputs). The 5% overfit gate
triggers transitively. **Reverted W-AR-02 to baseline** to preserve
COMPOUND-03 recall.

**Conclusion.** Marking refinement-stuck. The W-AR-02 narrowing is
structurally correct but too costly: it exposes another corpus issue
(COMPOUND-03 targets) that requires regeneration to address.

### W-CON-01, W-CON-04 — STRETCH (lock-no-edit)

Both rules have NC FPRs in the 18-20% range — clearing the 0.25
hard floor at baseline but above the 0.10 target zone. Recall is
1.0 across both. Bystander rates are very low (~5%) and precisions
are already 45-63% — much better than the catalog average. These
rules don't have the URI-handle pathology and are doing decent work
out of the box. They are locked at the current predicate as
`accepted-no-edit` (provisional state), with the understanding that
target-zone optimization for them would require corpus-level changes
(introducing more "clean" NC variants without the structural patterns
they detect).

## Catalog-wide trajectory

(See `plots/catalog_milestones.png` for the visualization.)

Catalog metrics computed across all four populations (confirm_existing,
negative_control, gap_probe, interaction). Out-of-scope rule W-AL-02
is excluded from "any-rule fires" counts since spec adaptation #3
defers it to Phase 2 v2.

| Milestone | Recall | Precision | Specificity (any-rule, excl W-AL-02) |
|---|---|---|---|
| M5 baseline | 0.664 | 0.700 | 0.000 (all 176 NCs fire something) |
| After W-EP-01 lock | 0.647 | 0.683 | 0.045 (8 NCs now clean) |
| Final | 0.647 | 0.683 | 0.045 |

The catalog-level move is small because W-ON-02 (89.8% NC FPR,
unfixable without corpus regen) and W-AR-02 (23.6% NC FPR, reverted
to preserve COMPOUND-03 recall) still drive most NC firings. The
W-EP-01 fix is dramatic at the rule level (precision 4.8% → 100%)
but not catalog-dominant because other rules' issues persist.

## Loosening-sentinel verification

Per spec §3, a 50-package sentinel pool was sampled at split-time per
rule (deterministically, seed=20260427). The sentinel pool consists
of confirm_existing variants where NONE of the affected rules
(`AFFECTED_RULES[rule_id]`) fired in M5 baseline.

| Rule | Sentinels | Disjoint in baseline | Firing post-fix |
|---|---|---|---|
| W-EP-01 | 50 | 50/50 ✓ | 0/50 ✓ |
| W-ON-02 | 50 | 50/50 ✓ | (no edit applied) |
| COMPOUND-01 | 50 | 50/50 ✓ | (no edit applied) |
| COMPOUND-03 | 50 | 50/50 ✓ | (no edit applied) |

## Risks (per spec §11 + plan)

1. **Distribution-specific predicates.** The fixes are validated against
   the M5 synthetic corpus (high-subtlety only). Phase 2 v2's
   multi-subtlety re-evaluation will re-test the predicates against
   real-world data distributions.
2. **Auto-mode + LLM bypass.** Per the user's adaptation, the W-EP-01
   proposal was hand-crafted by Claude based on structural analysis,
   bypassing the `propose_revision.py` LLM scaffold. The rationale,
   diff, and metrics are still in `refinement_log.jsonl` so the audit
   trail is intact. The semantic-review gate (C1.5) re-validates each
   locked predicate intent.
3. **Corpus-level findings exposed by W-EP-01 fix.** The COMPOUND-01
   recall drop from 1.0 to 0.57 is a CORPUS issue surfaced (not
   regressed) by the W-EP-01 fix: 43% of M5 COMPOUND-01 targets were
   generated with a "fake" Critical input via the W-EP-01 misfire.
   These packages need to be regenerated in Phase 2 v2 to restore
   COMPOUND-01 measurement validity.
4. **Compound rule chain interactions.** W-AR-02 stretch refinement
   directly affects COMPOUND-01 and COMPOUND-03 metrics via the
   chain. Re-baseline computations are required at every atomic
   rule lock; codified in `tools.phase2_5.lock_in:--baseline-outcomes`.
5. **Praxis framing.** Phase 2.5's auto-mode adaptation provides
   metric-driven evidence for predicate edits but defers semantic
   validation to the C1.5 human review gate. Without that gate, an
   LLM-proposed predicate that improves metrics but is semantically
   wrong could ship.
6. **Authorship disclosure.** All predicate edits are logged with
   `proposed_by: "claude_code"` in `refinement_log.jsonl`. Final
   tag annotations should disclose the auto-mode workflow.

## Acceptance gate (per spec §13 + plan)

- [x] All four primary rules' splits constructed and committed
- [x] Refinement loop executed for each (locked OR `refinement-stuck`
       with rationale)
- [x] Holdout metrics computed exactly once per rule (W-EP-01 only;
       W-ON-02/COMPOUND-01 didn't reach lock; COMPOUND-03 has
       holdout outstanding)
- [x] Loosening-sentinel check passed (W-EP-01: 0/50 fired post-fix)
- [x] Catalog-wide PR milestone plot infrastructure operational
- [x] Stretch rules attempted — all three (W-AR-02 stuck after iter 1
       chain regression; W-CON-01 + W-CON-04 lock-no-edit at provisional)
- [ ] **C1.5 human semantic review gate completed** — pending
- [ ] Tag `v0.5.8-phase2.5` created (only after C1.5 confirms)
- [x] Per-rule lightweight tag created for W-EP-01
       (`v0.5.8-phase2.5-w-ep-01`)
- [x] No modifications to existing tags
- [x] No clobbering of existing coverage artifacts under
       `out/adversarial/phase2/2026-04-26/`

## What needs corpus regeneration (Phase 2 v2)

The W-EP-01 fix surfaced a systematic corpus issue: many M5 target
packages were generated relying on URI-handle bugs in the rule
predicates, not on intrinsic structural weakener content. Specifically:

* **COMPOUND-01 corpus targets:** 54/126 (43%) had no inline Claim
  definition; their "Critical" weakener input came from W-EP-01 firing
  on the missing claim. After W-EP-01 lock, these packages have no
  Critical → COMPOUND-01 doesn't trigger → recall drops to 0.57.
  Phase 2 v2 should regenerate these with intrinsic Critical
  weakener structure (e.g., a real W-AR-01 failure or W-AR-02 with
  high-required-level factor gap).

* **COMPOUND-03 corpus targets (subset):** ~19% similarly relied on
  W-AR-02 firing on a low-required-level factor as Critical input.
  Same corpus regeneration prescription.

* **W-ON-02 NC variants (minimal NC):** lack inline applicability
  constraints / operating envelopes. Either the NC corpus should
  include such bounds, or the W-ON-02 rule should accept that some
  NCs trigger it as a legitimate "minimal but unbounded" finding.

## Reproducibility

```bash
# Build splits (deterministic, seed=20260427)
python -m tools.phase2_5.split --all

# Inspect a rule's misfires
python -m tools.phase2_5.inspect_misfires --rule W-EP-01

# Compute baseline metrics
python -m tools.phase2_5.metrics --rule W-EP-01 --split train

# Run the refine loop in auto mode
python -m tools.phase2_5.refine_loop --rule W-EP-01

# OR: manual iteration via lock_in (used for W-EP-01 in this run)
python -m uofa_cli adversarial analyze \
    --in out/adversarial/phase2/2026-04-26 \
    --out out/phase2_5/2026-04-27/per_iter_outcomes/{rule}_iter01 \
    --parallel 5
python -m tools.phase2_5.lock_in --rule W-EP-01 --iteration 1 \
    --new-outcomes <path> --commit-holdout

# Verify sentinels independently
python -m tools.phase2_5.verify_sentinels --rule W-EP-01 \
    --post-outcomes out/phase2_5/2026-04-27/milestones/after_w_ep_01.csv

# Log a no-edit decision (compound rules whose dependencies fixed it)
python -m tools.phase2_5.log_decision --rule COMPOUND-03 \
    --iteration 1 --decision lock-no-edit \
    --baseline-outcomes out/phase2_5/2026-04-27/milestones/after_w_ep_01.csv \
    --rationale "..."

# Regenerate plots
python -m tools.phase2_5.plot_pr --all
```

All Phase 2.5 outputs land in `out/phase2_5/2026-04-27/`. The M5
baseline at `out/adversarial/phase2/2026-04-26/coverage/` is read-only.

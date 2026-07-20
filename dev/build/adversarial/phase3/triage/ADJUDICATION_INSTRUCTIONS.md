# Stage 4 adjudication — instructions

**Worksheet:** `adjudication_worksheet.csv` — 21 cases, 35 columns.
**Scope:** the DISAGREEMENT queue from Stage 3 triage, every case where the production trio failed to reach a 2-of-3 verdict. 15 are `all_three_disagree`, 6 are `two_disagree_one_uncertain`.

The worksheet contains **the case evidence only**. The judges' verdicts and reasoning are deliberately not in it, so your verdict is independent by construction and the author-versus-judge agreement statistic stays interpretable. Their verdicts are in `adjudication_queue.csv` if you want to compare afterwards, but read that only once you have recorded your own.

## The question you are answering

For each case: **did the catalog behave correctly on this package?** That decomposes into two sub-questions, in order.

1. **Does the package actually instantiate the defeater it was asked to?** Compare `target_weakener` against the package evidence in columns 13 to 29. If it does not, the verdict is `GENERATOR-ARTIFACT` regardless of what the engine did, because the catalog cannot be faulted for missing something that is not there.
2. **If it does, did the engine respond correctly?** Compare `expected_rule` and `target_rule_fired` against `rules_fired`.

## Columns

**What the generator was asked to build (3 to 8).** `target_weakener` is the defeater it was told to instantiate, `defeater_type` is the D1/D2/D3 class, `source_taxonomy` is the literature origin, `subtlety` is how hidden it was told to make it. For the 7 `gap_probe` cases these read `(none - gap_probe)`: those probe literature defeaters the catalog has no rule for, so nothing firing is the expected outcome and `REAL-GAP` is the live hypothesis.

**What the engine did (9 to 12).** `engine_outcome` is `COV-HIT` (target rule fired), `COV-WRONG` (target did not fire but something else did), `COV-CLEAN-WRONG` (a clean control that fired anyway), or `GEN-INVALID` (failed SHACL). `rules_fired` is everything that fired. In this queue: 16 `COV-WRONG`, 5 `COV-HIT`.

**What the package says (13 to 29).** This is your evidence.
- `package_description`, `cou_intended_use`, `cou_decision_consequence`, `cou_model_influence` — what is being claimed and how much the model matters.
- `profile` — `ProfileMinimal` or `ProfileComplete`. Minimal packages legitimately omit fields Complete requires, which matters when judging whether an omission is a defeater or just the profile.
- `decision`, `assurance_level`, `model_risk_level` — the assessment outcome and how much rigor was required.
- **`factors_detail`** — every credibility factor as `factorType [status] req/ach AC=yes|MISSING :: acceptance criteria`. This is usually where the defeater lives.
- Three pre-computed flags, since these are the common defeater shapes: **`factors_missing_acceptance_criteria`** (the W-AR-01 undermining shape), **`factors_not_assessed`** (the W-CON-01 shape), **`factors_below_required_level`** (achieved under required, an accepted-with-shortfall shape).
- `validation_results`, `declared_weakeners`, `decision_rationale`.

**`package_in_bundle` (30)** — read the full package when the summary is not enough:
```
tar -xzf dev/build/adversarial/phase2/2026-04-26/judge_ready_bundle.tgz \
    -O judge_ready_bundle/packages/<case_id>.jsonld | jq .
```

## What you fill in (31 to 35)

**`author_verdict`** — one of, spelled exactly:
`CORRECT-DETECTION`, `REAL-GAP`, `GENERATOR-ARTIFACT`, `EXISTING-RULE-MISBEHAVIOR`, `OUT-OF-SCOPE`, `UNCERTAIN`.

| Verdict | Use when |
|---|---|
| `CORRECT-DETECTION` | The package instantiates the defeater and the target rule caught it, for the right reason. |
| `REAL-GAP` | The package instantiates a genuine defeater the catalog has no rule for. This is the class that drives catalog extension, so hold it to the evidence. |
| `GENERATOR-ARTIFACT` | The package does not actually instantiate the intended defeater. The generator failed. |
| `EXISTING-RULE-MISBEHAVIOR` | A rule fired but wrongly: wrong rule, false positive, or right rule for the wrong reason. |
| `OUT-OF-SCOPE` | The bundle is structurally complete but lacks the evidence needed to evaluate the defeater. Say which evidence is missing. |
| `UNCERTAIN` | After inspecting the package, two or more verdicts each stay defensible and none dominates. A genuine tie, not a hard case you would rather not call. |

**`author_section_6_7`** — only when the verdict is `REAL-GAP`. Use a Tier-1 id if one fits (`W-EV-01`, `W-EV-02`, `W-REQ-01`, `W-CX-01`, `W-AR-06`, `W-AR-07`), otherwise name the pattern.

**`author_confidence`** — 0.0 to 1.0. Reflect real uncertainty rather than defaulting high.

**`author_rationale`** — a sentence or two on what decided it. A reviewer will read this, so write it for them.

**`author_notes`** — anything else.

## One caveat worth carrying

These packages were generated on 2026-04-26 against the catalog **before** the Phase 2.5 refinements took the negative-control clean rate from 0% to 97.1%. A gap the earlier catalog missed is not necessarily a gap in the current one. If you mark something `REAL-GAP` and suspect v0.5.15.1 already closed it, say so in `author_notes`. This is the version-skew issue in `PHASE3_STATUS_REPORT.md`, and it is still open.

## After you finish

Save as CSV in place. Corpus-wide agreement statistics:

```
uofa adversarial adjudicate \
  --judgments-a dev/build/adversarial/phase3/production/run-1/judgments_A.jsonl \
  --judgments-b dev/build/adversarial/phase3/production/run-1/judgments_B.jsonl \
  --judgments-c dev/build/adversarial/phase3/production/run-1/judgments_C.jsonl \
  --out dev/build/adversarial/phase3/adjudication/
```

That yields the three pairwise Cohen's kappa values, Fleiss' kappa, and per-pair confusion matrices.

**Still outstanding beyond this queue.** The spec also expects a blinded spot-check of CONVERGENT cases, to measure how often you would overturn the ensemble where it agreed, against a target override rate at or below 0.10. That sample is not in this worksheet and can be drawn separately. Adjudicating only the disagreements measures where the judges disagreed with each other, which is not the same as measuring whether the ensemble was right.

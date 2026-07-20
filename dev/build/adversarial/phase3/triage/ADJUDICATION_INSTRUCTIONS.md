# Stage 4 adjudication — instructions

**Worksheet:** `adjudication_worksheet.csv` — 71 cases, 35 columns.

The worksheet holds two queues, deliberately mixed together:

- **21 DISAGREEMENT cases** — every case where the production trio failed to reach a 2-of-3 verdict (15 `all_three_disagree`, 6 `two_disagree_one_uncertain`). This is the required Stage 4 queue.
- **50 CONVERGENT spot-check cases** — a stratified sample of cases the trio agreed on, to measure how often you would overturn the ensemble where it was confident. The spec targets an override rate at or below 0.10.

**You cannot tell which is which, and that is intentional.** The rows are shuffled (seed 20260720) and carry no queue label. If you could see that a case was one the judges agreed on, you would unconsciously treat it as already settled, which is precisely the bias the spot-check exists to detect. The mapping lives in `adjudication_sample_key.csv`. **Do not open that file until you have finished.**

For the same reason the worksheet contains **case evidence only**: no judge verdicts, no judge reasoning. Your verdict is therefore independent by construction, which is what makes both the author-versus-judge agreement statistic and the override rate interpretable. Judge verdicts for the 21 disagreements are in `adjudication_queue.csv`, again for afterwards only.

Because the order is random, any prefix of the sheet is a valid random subset of both queues. If you want to split the work, doing rows 1 to 35 today and the rest later costs you nothing statistically.

### How the sample was drawn

Stratified by the ensemble's majority verdict, not proportional. A proportional 50-case sample would have contained about 3 REAL-GAP cases, too few to say anything about the Tier-1 claim, so REAL-GAP is deliberately over-weighted. Per-stratum override rates are therefore the primary readout, and `adjudication_sample_key.csv` carries each stratum's population and weight so a population-level estimate can be recovered by reweighting.

| Stratum | Sampled | Population | Weight |
|---|---:|---:|---:|
| CORRECT-DETECTION | 15 | 2,677 | 0.5903 |
| EXISTING-RULE-MISBEHAVIOR | 12 | 1,161 | 0.2560 |
| GENERATOR-ARTIFACT | 8 | 398 | 0.0878 |
| REAL-GAP | 12 | 289 | 0.0637 |
| OUT-OF-SCOPE | 3 | 10 | 0.0022 |

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

Then open `adjudication_sample_key.csv` and join on `case_id` to get two readouts.

**Author versus judge agreement**, over the 21 disagreement cases: how your verdict relates to each judge's, which is what the disagreement queue was for.

**Spot-check override rate**, over the 50 convergent cases: the share where your verdict differs from `ensemble_majority_verdict`. Compute it per stratum, since the sample is stratified rather than proportional. For a population estimate, reweight by the `stratum_weight` column:

```
override_rate = Σ (stratum_weight × per-stratum override rate)
```

The spec target is 0.10 or lower. Note the precision honestly: 12 REAL-GAP cases can distinguish "rare" from "common" but cannot pin a rate to two decimal places, and with 3 of 10 OUT-OF-SCOPE cases that stratum is indicative only.

The REAL-GAP stratum is the one to read closely. Those 12 cases are the direct check on whether the 289 REAL-GAP verdicts underpinning the 6-of-6 Tier-1 result hold up under author review. If you overturn a meaningful share of them, that is a finding about the Tier-1 claim, not just about the ensemble.

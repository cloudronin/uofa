# Credibility report — allenai/OLMo-2-13B-Instruct (model card)

- **Assessed against:** NIST AI RMF
- **Risk posture:** Evaluated as if bound for a moderate-risk deployment (assumed MRL 3); the source card declares no context of use or risk tier.

## At a glance

| Completeness | Factors evidenced | Concerns | Gate checks |
|---|---|---|---|
| 35% | 6 of 17 | 2 Critical, 9 High, 2 Moderate | 0 of 2 |

_35% of all factors evidenced; 6 factors required at Level 3 still need evidence; 11 high-severity concerns open before this is review-ready._

## Credibility factors

| Factor | Status |
|---|---|
| Affected populations | Not stated |
| Bias and fairness analysis | Not stated |
| Evaluation methodology | Not stated |
| Evaluation metrics | Not stated |
| Out-of-scope use | Not stated |
| Robustness and safety testing | Not stated |
| Deployment setting | Evidenced |
| Intended use | Evidenced |
| Known limitations | Evidenced |
| License and usage terms | Evidenced |
| Task and domain context | Evidenced |
| Test and evaluation data | Evidenced |
| Mitigations and safeguards | Not applicable |
| Monitoring and feedback | Not applicable |
| Ownership and accountability | Not applicable |
| Residual risk | Not applicable |
| Versioning and update policy | Not applicable |

## [1] Documentation completeness — concerns found

- **High concern (seen 5×).** Credibility factor is not assessed but model risk level exceeds 2 — unassessed factors at elevated risk weaken the credibility argument. Relates to: Bias and fairness analysis, Out-of-scope use, Affected populations, Evaluation methodology, Robustness and safety testing.
- **High concern.** Context of Use has neither an applicability constraint nor an operating envelope — the COU is declared but its boundary of validity is undocumented. Relates to: Out-of-scope use.

## [2] Evaluation sufficiency — NIST AI 800-3 / V&V 40 validation-evidence

- **Critical concern.** A generalized performance claim rests on a sample with no stated relationship to the population it generalizes over - the claim is broader than the evidence supporting it. Relates to: Item sampling.
- **High concern (seen 8×).** Validation result has no uncertainty quantification — aleatory uncertainty is uncharacterized. Relates to: Evaluation metrics, Score and uncertainty.
- **High concern (seen 9×).** Validation result has no comparedAgainst link — comparator data source is absent. Relates to: Evaluation methodology.
- **High concern (seen 9×).** Reported evaluation states no context-of-use relevance - the decision this score would inform is unstated. Relates to: Context-of-use relevance. _(common: most published models state no context of use)_
- **High concern (seen 9×).** Reported evaluation states no determinism floor - sampling settings and per-model run-to-run spread are uncharacterized, so the score is one draw reported as a measurement. Relates to: Harness determinism.
- **High concern (seen 9×).** Reported benchmark score carries no account of how its items sample the target population - benchmark accuracy cannot be read as generalized accuracy. Relates to: Item sampling.
- **High concern (seen 9×).** Reported score is not calibrated against a null, chance, or comprehension-free baseline - the floor the score must clear to mean anything is unstated. Relates to: Null calibration.
- **Moderate concern (seen 9×).** No capability-confound control stated - the reported separation may be attributable to general capability rather than to the construct the benchmark claims to measure. Relates to: Construct validity.

_MRL not supplied - compound risk escalation not assessed. Pass --mrl to state the risk level of the decision this evidence informs._

## Package-level concerns

_Whole-assessment findings; they belong to neither section alone._

- **Critical concern (seen 9×).** Critical and High severity weakeners coexist — compounding risk escalation.
- **High concern.** UofA is missing bindsRequirement — incomplete profile binding.
- **Moderate concern.** UofA conforms to ProfileComplete but declares no SensitivityAnalysis — a Complete profile is structurally expected to document sensitivity analysis alongside uncertainty quantification.

## What is still missing

- Out-of-scope use
- Affected populations
- Evaluation metrics
- Evaluation methodology
- Bias and fairness analysis
- Robustness and safety testing

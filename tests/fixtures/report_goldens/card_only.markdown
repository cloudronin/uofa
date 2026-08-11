# Credibility report — allenai/OLMo-2-13B-Instruct (model card)

- **Assessed against:** NIST AI RMF
- **Risk posture:** Evaluated as if bound for a moderate-risk deployment (assumed MRL 3); the source card declares no context of use or risk tier.

## At a glance

| Completeness | Factors evidenced | Concerns | Gate checks |
|---|---|---|---|
| 41% | 7 of 17 | 3 High, 1 Moderate | 0 of 2 |

_41% of all factors evidenced; 5 factors required at Level 3 still need evidence; 3 high-severity concerns open before this is review-ready._

## Credibility factors

| Factor | Status |
|---|---|
| Affected populations | Not stated |
| Bias and fairness analysis | Not stated |
| Evaluation methodology | Not stated |
| Out-of-scope use | Not stated |
| Robustness and safety testing | Not stated |
| Deployment setting | Evidenced |
| Evaluation metrics | Evidenced |
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

- **High concern (seen 5×).** Credibility factor is not assessed but model risk level exceeds 2 — unassessed factors at elevated risk weaken the credibility argument. Relates to: Affected populations, Evaluation methodology, Robustness and safety testing, Bias and fairness analysis, Out-of-scope use.
- **High concern.** Context of Use has neither an applicability constraint nor an operating envelope — the COU is declared but its boundary of validity is undocumented. Relates to: Out-of-scope use.

## [2] Evaluation sufficiency — NIST AI 800-3 / V&V 40 validation-evidence

_No reported evaluation to assess - sufficiency N/A. Nothing was found to assess, which is not the same as finding nothing wrong._

## Package-level concerns

_Whole-assessment findings; they belong to neither section alone._

- **High concern (seen 2×).** UofA is missing hasValidationResult — incomplete profile binding.
- **Moderate concern.** UofA conforms to ProfileComplete but declares no SensitivityAnalysis — a Complete profile is structurally expected to document sensitivity analysis alongside uncertainty quantification.

## What is still missing

- Out-of-scope use
- Affected populations
- Evaluation methodology
- Bias and fairness analysis
- Robustness and safety testing

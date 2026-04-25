# Phase 2 gap_probe specs

This directory contains the gap_probe coverage-experiment specs prescribed
by `UofA_Adversarial_Gen_Phase2_Spec_v1_7.md` §7.

## Count reconciliation (22 vs 23)

The v1.7 spec contains a count discrepancy that this README documents:

- **§3 scope summary** declares `New gap_probe templates | 23`
- **§7 prescriptive table** enumerates **22 rows** (numbered 1–22)
- **Shipped here**: 22 spec YAMLs covering all 22 §7 rows verbatim

The §3 figure is a roundup error. There is no 23rd row in §7. The 22
specs in this directory cover every §7 row that exists.

§13.1 gate #5 wording was updated in the v1.7 spec to reflect this:
"All 22 gap_probe templates from §7 (1 §3 count discrepancy reconciled
in `specs/gap_probe/README.md`)."

## Filename ↔ §7 row mapping

The spec §7 column "Spec file" lists canonical filenames using slightly
different conventions than what shipped here. The mapping below is the
authoritative ground truth:

| §7 row | §7 spec file (canonical) | Shipped here as | source_taxonomy |
|---|---|---|---|
| 1 | `gohar_ev_data_drift.yaml` | `gohar_ev_data_drift.yaml` | gohar/evidence_validity/data-drift |
| 2 | `gohar_ev_inadequate_metric.yaml` | `gohar_ev_inadequate_metrics.yaml` | gohar/evidence_validity/inadequate-metrics |
| 3 | `gohar_ev_coverage_gap.yaml` | `gohar_ev_coverage_edge_cases.yaml` | gohar/evidence_validity/coverage-edge-cases |
| 4 | `gohar_ev_fidelity.yaml` | `gohar_ev_fidelity.yaml` | gohar/evidence_validity/fidelity |
| 5 | `gohar_ev_ml_variance.yaml` | `gohar_ev_model_variance.yaml` | gohar/evidence_validity/model-variance |
| 6 | `gohar_ev_ml_robustness.yaml` | `gohar_ev_robustness.yaml` | gohar/evidence_validity/robustness |
| 7 | `gohar_req_missing.yaml` | `gohar_req_missing.yaml` | gohar/requirements/missing |
| 8 | `gohar_req_incorrect.yaml` | `gohar_req_incorrect.yaml` | gohar/requirements/incorrect |
| 9 | `gohar_req_ambiguous.yaml` | `gohar_req_ambiguous.yaml` | gohar/requirements/ambiguous |
| 10 | `gohar_req_stale.yaml` | `gohar_req_stale.yaml` | gohar/requirements/stale |
| 11 | `gohar_req_inconsistent.yaml` | `gohar_req_inconsistent.yaml` | gohar/requirements/inconsistent |
| 12 | `gohar_ctx_faults_physical.yaml` | `gohar_ctx_faults_physical.yaml` | gohar/contextual/faults-physical |
| 13 | `gohar_ctx_faults_software.yaml` | `gohar_ctx_faults_software.yaml` | gohar/contextual/faults-software |
| 14 | `gohar_ctx_human_errors.yaml` | `gohar_ctx_human_errors.yaml` | gohar/contextual/human-errors |
| 15 | `gohar_ctx_configuration.yaml` | `gohar_ctx_configuration.yaml` | gohar/contextual/configuration |
| 16 | `gohar_ctx_environmental.yaml` | `gohar_ctx_environmental_factors.yaml` | gohar/contextual/environmental-factors |
| 17 | `greenwell_suf_hasty_generalization.yaml` | `greenwell_suf_hasty_inductive_generalization.yaml` | greenwell/sufficiency/hasty-inductive-generalization |
| 18 | `greenwell_suf_arguing_from_ignorance.yaml` | `greenwell_suf_arguing_from_ignorance.yaml` | greenwell/sufficiency/arguing-from-ignorance |
| 19 | `greenwell_suf_necessary_sufficient.yaml` | `greenwell_suf_confusion_necessary_sufficient.yaml` | greenwell/sufficiency/confusion-necessary-sufficient |
| 20 | `clarissa_eliminative_absent.yaml` | `clarissa_wf_eliminative_argumentation.yaml` | clarissa-machinery/workflow/eliminative-argumentation |
| 21 | `clarissa_residual_risk_unjustified.yaml` | `clarissa_wf_residual_risk_justification.yaml` | clarissa-machinery/workflow/residual-risk-justification |
| 22 | `clarissa_precondition_unverified.yaml` | `clarissa_wf_theory_preconditions.yaml` | clarissa-machinery/workflow/theory-preconditions |

The shipped filenames use `<family>_<short_category>_<leaf_underscored>.yaml`
(e.g., `gohar_ev_*`, `clarissa_wf_*`) for visual grouping in directory
listings; the canonical content is identical to the §7 row in each case.

## See also

- `packs/core/source_taxonomies.json` — registry that all `source_taxonomy`
  values resolve against
- `UofA_Adversarial_Gen_Phase2_Spec_v1_7.md` §7 — the prescriptive table
- `UofA_Phase2_M4_Cleanup_Spec.md` — the cleanup that produced this README

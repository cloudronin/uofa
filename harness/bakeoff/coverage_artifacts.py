"""Raw unstructured evidence-package prose for the coverage experiment (Experiment B).

K1 in the coverage experiment hands the model these artifacts — naturalistic model-card /
validation-report excerpts for the 31 defeaters NVIDIA's guardrails emit no signal for —
with NO SIP fields and NO catalog. Each artifact CONTAINS the defeater's facts but does
NOT flag them: the test is whether a capable model reading the raw docs *surfaces* the
credibility problem that SIP's extraction + the catalog (K2 = `full`) make explicit.

Authoring discipline (so the experiment is valid):
- The defeater's facts are PRESENT (a buried methods/results line), never absent — K1 must
  have a fair shot. Cells whose defeater was "hidden in code" in the catalog ablation are
  rendered with the fact surfaced into the prose (documented-but-buried), so the test is
  whether the model *connects* it, not whether it is psychic.
- No conclusion words (leakage, circular, out-of-distribution, inadequate, biased, not
  validated): the facts are stated, the judgment is left to the reader — same de-naming
  discipline as `measures_raw`.
- Controls present the alarming surface AND the offsetting fact, both neutrally, so the
  fair read is to accept (the over-action trap survives into prose).
"""
from __future__ import annotations

RAW_ARTIFACTS: dict[str, str] = {
    # ── D-CCB: data provenance / methodology ─────────────────────────────────
    "surr-dccb10-augmented-not-real": (
        "Model card — fatigue-life surrogate. Trained on 50,000 microstructure-to-life pairs. "
        "To broaden coverage, 40,000 of those pairs (80%) were produced by a generative "
        "microstructure synthesizer conditioned on the measured specimens; the remaining 10,000 "
        "are physical test specimens. The synthesizer was tuned to reproduce the first- and "
        "second-order grain statistics of the measured set. The held-out validation set of 5,000 "
        "pairs was sampled from the same pooled corpus; validation MAE is 1.5%. The surrogate is "
        "proposed to qualify components from predicted fatigue life."),
    "surr-dccb10-uncorrected-sensor-drift": (
        "Validation report — compressor efficiency surrogate. The surrogate reproduces the test "
        "measurements to 0.8% across 1,200 logged points collected over a six-month rig campaign. "
        "Instrumentation notes: the primary mass-flow sensor accumulated a +3.0% calibration shift "
        "over the campaign, recorded in the run metadata. Measurements were ingested as logged. "
        "The surrogate's predicted efficiency feeds an acceptance decision."),
    "surr-dccb10-vintage-regime": (
        "Model card — actuator response surrogate. Training data is current (collected last "
        "quarter), 4,000 operating points. All logged points were recorded during normal "
        "steady, low-load operation. The surrogate is proposed to predict transient response "
        "during high-load events; high-load transient operation does not appear in the logged "
        "operating record. Single-step fit error on the logged data is 1.1%."),
    "surr-dccb11-undocumented-clipping": (
        "Methods — extreme-load screening surrogate. Validation error on the processed dataset is "
        "0.6%. Preprocessing: input features standardized; regression targets capped at the 95th "
        "percentile of the raw distribution before training to stabilize the loss. The surrogate "
        "is proposed to screen extreme-load contingencies — events above the 95th percentile of "
        "load — for a grid-reliability decision."),
    "surr-dccb12-seed-sensitivity": (
        "Results — property surrogate. Reported test accuracy 98.5%, from a single training run "
        "(one random seed). Run-to-run variability across seeds was not measured. The architecture "
        "family is one for which published replications report wide run-to-run spread on small "
        "datasets. The single-run accuracy is cited as the basis for acceptance."),
    "surr-dccb12-suspected-feature-leakage": (
        "Model card — materials screening surrogate. Validation accuracy 94% on a properly "
        "held-out split. Inputs include a panel of composition descriptors and one post-hoc "
        "laboratory measurement taken on the finished specimen. The provenance of that lab "
        "feature relative to the prediction target is not described. The surrogate screens "
        "candidate materials on the predicted property."),
    "surr-dccb12-temporal-leakage": (
        "Validation report — load forecasting surrogate. Validation error 0.9%. The dataset is an "
        "hourly time series with strong autocorrelation; train and validation samples were "
        "assigned by a uniform random split across the full series, so validation timestamps are "
        "interleaved with training timestamps. The surrogate is deployed to forecast load ahead "
        "of time for a dispatch decision."),
    "surr-dccb13-tuned-on-validation": (
        "Methods — emulator. Reported validation accuracy 96%. Hyperparameters were selected by a "
        "grid search that maximized accuracy on the reported validation set; no separate test set "
        "was held back. The validation accuracy is cited as the credibility basis for acceptance."),
    "surr-dccb14-circular-reference": (
        "Validation report — multiphysics surrogate. The surrogate agrees with the reference to "
        "1.5% across the domain. The reference used as truth is a fast reduced-order model; its own "
        "accuracy for this context of use has not been established against high-fidelity simulation "
        "or experiment. No independent high-fidelity or experimental check is included."),
    "surr-dccb14-repro-gap": (
        "Submission package — surrogate for a regulated filing that requires independent "
        "reproducibility. Results are strong and cryptographically signed. The package does not "
        "include the trained weights, a pinned software environment, or the scripts needed to "
        "reproduce the reported results. The narrative and the signed result tables are provided."),
    "surr-dccb15-rare-failure-class": (
        "Model card — fault-detection surrogate. Overall classification accuracy 98.5% on a large, "
        "representative dataset. The dataset is 97% nominal-operation examples; the rare-fault class "
        "the surrogate is meant to flag is 0.3% of training examples. Performance broken out for the "
        "rare-fault class is not reported. The surrogate raises maintenance-safety actions on the "
        "rare-fault flag."),
    # ── D-PD: applicability / inheritance ────────────────────────────────────
    "surr-dpd01-different-bc": (
        "Validation report — heat-transfer surrogate. Validated across 200 operating cases with "
        "low error. Every training and validation case imposes a fixed-temperature (Dirichlet) "
        "wall condition. The surrogate is proposed for a case with a convective (Robin) wall "
        "condition; no training or validation case used a convective wall."),
    "surr-dpd01-old-version-revalidated-control": (
        "Model card — flow surrogate, version 2. The current release line is at version 4. For this "
        "context of use, version 2 was explicitly re-validated against a current reference and "
        "achieved 3% error. The version 3 and 4 changes are documented as feature additions outside "
        "this COU's operating regime. Version 2 is proposed for the flow decision."),
    "surr-dpd02-transfer-no-revalidation": (
        "Validation report — geomechanics surrogate. Reported validation error 2.0%. The validation "
        "was performed on a sandstone reservoir. The surrogate is now applied to a carbonate "
        "reservoir, whose constitutive behaviour differs from sandstone. No re-validation on the "
        "carbonate system is included. Predicted subsidence feeds an injection-plan decision."),
    "surr-dpd03-omitted-but-not-asserted-control": (
        "Model card — coefficient surrogate. The evidence package covers steady-state validation, "
        "uncertainty quantification, and provenance. Transient-response evidence is not included. "
        "The stated context of use is a steady-state coefficient only; the scope statement "
        "explicitly declares transient behaviour out of scope and discloses the omission."),
    # ── D-VAL: validation methodology ────────────────────────────────────────
    "surr-dval08-climate-tails": (
        "Validation report — climate emulator. Aggregate skill score 0.96, computed as a bulk RMSE "
        "skill over all days. Skill restricted to extreme events is not reported. The emulator "
        "screens an adaptation decision keyed to 99.9th-percentile extreme events."),
    "surr-dval08-fewsamples-analytic-control": (
        "Validation report — orbital-mechanics surrogate. Validated at 6 points placed at the "
        "domain corners and center. The governing system has an exact closed-form (two-body "
        "Keplerian) solution, against which the maximum error across the 6 points is 1e-6. The "
        "surrogate informs a maneuver decision within the two-body regime."),
    "surr-dval08-high-but-conservative-control": (
        "Validation report — pressure-vessel stress surrogate. Validation error is 12%. The error is "
        "one-sided across every validation case: the surrogate over-predicts stress in all of them. "
        "The directionality is documented. The decision requires predicted stress to remain below an "
        "allowable limit."),
    "surr-dval08-leakage": (
        "Methods — design-metric emulator. Reported validation error 0.012. Feature normalization "
        "statistics were computed on the full dataset (training and validation together) before the "
        "split, and the train and validation simulations share random seeds. The validation error "
        "is offered as the sign-off basis for a design metric."),
    "surr-dval08-metric-mismatch": (
        "Validation report — pharmacokinetic surrogate. Validated against held-out data with R^2 "
        "0.97 on the full concentration-time curve. Error on the time-to-peak-concentration (Tmax) "
        "is not separately reported. The dosing-interval decision the surrogate informs is set by "
        "Tmax."),
    "surr-dval08-modesterror-but-within-tolerance-control": (
        "Validation report — screening surrogate. Validation error 8%. The stated context of use is "
        "an early screening stage with a documented, COU-tied acceptance tolerance of 15%; the "
        "reported error is within that tolerance. Provenance of the tolerance is documented."),
    "surr-dval08-no-independent-validation": (
        "Model card — battery-thermal surrogate. Training-set R^2 is 0.998. All reported performance "
        "metrics are computed on the training set; no independent validation set is included. The "
        "surrogate's predicted cell temperature sets a thermal-runaway safety margin."),
    "surr-dval08-proxy-qoi": (
        "Validation report — battery-degradation surrogate. Validated on capacity fade with 2% "
        "error. The end-of-life decision the surrogate drives is set by internal-resistance growth, "
        "not capacity fade. Capacity fade and internal resistance track closely in historical data "
        "but diverge under the fast-charge profile of this use. Internal-resistance error is not "
        "reported."),
    "surr-dval08-single-point-validation": (
        "Validation report — combustion surrogate. Validated against experiment with 0.5% error at "
        "one operating point (one equivalence ratio). The context of use sweeps equivalence ratio "
        "from 0.6 to 1.4, a range over which the chemistry is strongly nonlinear; one of the swept "
        "points lies at the validated condition."),
    # ── D-VER: verification ──────────────────────────────────────────────────
    "surr-dver05-mms-only": (
        "Verification summary — stress-concentration surrogate. Code verification by the method of "
        "manufactured solutions passed at the expected order of accuracy. Solution verification for "
        "the application configuration — a notched component under combined load — is not included, "
        "and application residuals are not linked to the verified order. The predicted stress "
        "concentration feeds a fatigue decision."),
    "surr-dver06-coverage-hole": (
        "Verification summary — aerodynamics surrogate. Benchmark sample density is good across the "
        "operating box on a box-average basis. The context of use is the high-Reynolds, high-"
        "angle-of-attack corner; the per-cell sample count in that corner is 0. Coverage is reported "
        "as a box-average. The prediction feeds a stall-margin decision."),
    "surr-dver06-mesh-marginal": (
        "Verification summary — FEA surrogate. A mesh-convergence study is included and the trend is "
        "monotone toward an asymptote. The grid-convergence index at the finest mesh is 8%. The "
        "context-of-use acceptance tolerance for the quantity of interest is 5%. The asymptotic "
        "value is not yet reached at the finest mesh studied."),
    "surr-dver06-resolution-hole": (
        "Verification summary — neural operator. Verified at resolutions from 32x32 up to 512x512, "
        "reported as a range-average. The context of use queries the operator at 1024x1024 for a "
        "fine-scale decision; 1024x1024 is not in the verification set."),
    "surr-dver06-steady-for-transient": (
        "Verification summary — internal-flow surrogate. Solution-verification residuals are low and "
        "documented; all verification was performed in steady-state. The context of use is a fast "
        "transient pressure spike for a surge-margin decision. Transient-mode verification is not "
        "included."),
    "surr-surr02-parent-rejected": (
        "Model card — RANS-closure surrogate. The surrogate reproduces its parent model to R^2 0.99 "
        "with high overlap in context of use. The parent model's recorded credibility decision for "
        "this application is Not Accepted. The relationship between the surrogate and the parent's "
        "recorded decision is not addressed in this package."),
    "surr-surr02-parent-rejected-thermal": (
        "Model card — thermal surrogate. The surrogate reproduces its CFD thermal reference to 0.8% "
        "NRMSE for the same context of use. The reference CFD model carries a recorded decision of "
        "Not Accepted for this COU, with the open finding that mesh independence was not "
        "demonstrated. This package does not revisit that finding."),
}

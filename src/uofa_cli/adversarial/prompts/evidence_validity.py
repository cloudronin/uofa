"""Gohar Evidence-Validity gap_probe templates (Phase 2 spec §7 rows 1-6).

Each template instantiates a Gohar 2025 Evidence-Validity sub-type that does
not cleanly map to any current UofA rule. Expected outcome class is COV-MISS;
the classifier annotates each MISS with the §6.7 candidate (W-EV-01,
W-EV-02, W-EV-03 where applicable). See Gohar Table III.
"""

from __future__ import annotations

from uofa_cli.adversarial.prompts.base import (
    BASE_SYSTEM_PROMPT,
    build_user_prompt,
    validate_subtlety_examples,
)

PROMPT_VERSION = "v1.0.0"

SYSTEM_PROMPT = BASE_SYSTEM_PROMPT


# ----- shared subtlety helper (these gap_probes share the gradient pattern) -----


def _gp_subtlety(low: str, medium: str, high: str) -> dict[str, str]:
    out = {"low": low, "medium": medium, "high": high}
    validate_subtlety_examples(out)
    return out


def _gp_render(spec, context, *, description, task, trigger, subtlety):
    return BASE_SYSTEM_PROMPT, build_user_prompt(
        weakener=spec.source_taxonomy or "(gap_probe)",
        weakener_description=description,
        defeater_type=f"gap_probe — {spec.source_taxonomy}",
        subtlety=spec.subtlety,
        subtlety_guidance=subtlety[spec.subtlety],
        base_cou_identity=context.get("identity"),
        context_of_use=context.get("context_of_use"),
        factor_scaffold=context.get("factor_scaffold", []),
        context_url=context.get("context_url", ""),
        decision=spec.decision,
        task=task,
        trigger_block=trigger,
    )


# ----- data-drift -----

DATA_DRIFT_DESC = (
    "Gohar Evidence-Validity 'Data Drift' — validation dataset is contemporary "
    "with model release but the operating envelope expanded after validation, "
    "and no re-calibration evidence is linked"
)
DATA_DRIFT_TASK = (
    "generate a UnitOfAssurance whose narrative documents an expansion of the "
    "operating envelope (e.g., new patient population, new flow regime) AFTER "
    "the model's validation campaign, without linking any re-validation "
    "evidence."
)
DATA_DRIFT_TRIGGER = (
    "Use a fully-formed package (Complete profile fields). The narrative on "
    "ContextOfUse.intendedUse should describe a recently-expanded operating "
    "envelope. No new ValidationResult covering the expanded range is "
    "emitted; existing ValidationResults pre-date the envelope expansion."
)
DATA_DRIFT_SUBTLETY = _gp_subtlety(
    low="Envelope expanded years ago; no validation in the new range. Narrative says 'use case has grown'.",
    medium="Envelope expanded recently; narrative says 're-validation planned' without producing it.",
    high="Envelope expansion is subtle (e.g., one extra patient subgroup); narrative argues prior validation 'covers' it without showing the test points.",
)


def _r_data_drift(spec, context):
    return _gp_render(
        spec, context,
        description=DATA_DRIFT_DESC,
        task=DATA_DRIFT_TASK,
        trigger=DATA_DRIFT_TRIGGER,
        subtlety=DATA_DRIFT_SUBTLETY,
    )


# ----- inadequate-metrics -----

INADEQUATE_METRICS_DESC = (
    "Gohar Evidence-Validity 'Inadequate Metrics' — validation metrics chosen "
    "do not actually measure what the COU's question of interest needs"
)
INADEQUATE_METRICS_TASK = (
    "generate a UnitOfAssurance where ValidationResults report metrics that "
    "are technically correct but do not address the COU's actual quantity "
    "of interest (e.g., R^2 on training data when the COU asks about "
    "prediction error in deployment)."
)
INADEQUATE_METRICS_TRIGGER = (
    "Emit ValidationResults whose `name` and `description` reference metrics "
    "(R^2, RMSE, Pearson correlation, etc.) that don't speak to the COU's "
    "question. Narrative should make the metric choice look reasonable on "
    "first read."
)
INADEQUATE_METRICS_SUBTLETY = _gp_subtlety(
    low="Metric is clearly wrong (e.g., training accuracy reported for a COU about deployment failure rate).",
    medium="Metric is adjacent (e.g., aggregate RMSE reported for a COU about worst-case error).",
    high="Metric is plausibly relevant but misses one dimension of the QoI (e.g., scalar magnitude when the COU needs both magnitude and direction).",
)


def _r_inadequate_metrics(spec, context):
    return _gp_render(
        spec, context,
        description=INADEQUATE_METRICS_DESC,
        task=INADEQUATE_METRICS_TASK,
        trigger=INADEQUATE_METRICS_TRIGGER,
        subtlety=INADEQUATE_METRICS_SUBTLETY,
    )


# ----- coverage-edge-cases -----

COVERAGE_EDGE_DESC = (
    "Gohar Evidence-Validity 'Coverage / Edge Cases' — validation samples "
    "cover the typical operating range but omit the edge cases the COU "
    "explicitly asks about"
)
COVERAGE_EDGE_TASK = (
    "generate a UnitOfAssurance whose ValidationResults span the nominal "
    "operating range but explicitly do NOT include the edge cases the COU "
    "names (extreme inputs, rare events, boundary conditions)."
)
COVERAGE_EDGE_TRIGGER = (
    "Emit a ContextOfUse.intendedUse that names specific edge cases "
    "(e.g., 'including high-shear-stress regions' or 'including extreme "
    "patient ages'). ValidationResults should not include any test points "
    "in those regions; narrative says 'edge cases studied separately' "
    "without linking that work."
)
COVERAGE_EDGE_SUBTLETY = _gp_subtlety(
    low="Edge cases named, no validation in those regions, narrative omits any reference to them.",
    medium="Edge cases studied 'in companion work' that is not linked.",
    high="Edge cases included as a single sample at the boundary; the rest of the validation distribution is in the bulk.",
)


def _r_coverage_edge(spec, context):
    return _gp_render(
        spec, context,
        description=COVERAGE_EDGE_DESC,
        task=COVERAGE_EDGE_TASK,
        trigger=COVERAGE_EDGE_TRIGGER,
        subtlety=COVERAGE_EDGE_SUBTLETY,
    )


# ----- fidelity -----

FIDELITY_DESC = (
    "Gohar Evidence-Validity 'Fidelity' — model fidelity to the physical "
    "system has gaps that the validation does not test, and no fidelity "
    "trade study is documented"
)
FIDELITY_TASK = (
    "generate a UnitOfAssurance where the model deliberately abstracts a "
    "physically real effect (e.g., omits a coupling term) and the "
    "validation does not test the impact of that abstraction."
)
FIDELITY_TRIGGER = (
    "ContextOfUse.description names a physical phenomenon present in the "
    "real system. The model description (bindsModel name + narrative) "
    "explicitly excludes that phenomenon. No ValidationResult tests how "
    "much that exclusion matters."
)
FIDELITY_SUBTLETY = _gp_subtlety(
    low="Excluded phenomenon is significant (turbulence, plasticity); narrative just notes 'simplified model'.",
    medium="Excluded phenomenon is secondary; narrative argues 'low impact' without quantifying.",
    high="Excluded phenomenon is mentioned in narrative as 'sensitivity studied informally'; no SensitivityAnalysis link.",
)


def _r_fidelity(spec, context):
    return _gp_render(
        spec, context,
        description=FIDELITY_DESC,
        task=FIDELITY_TASK,
        trigger=FIDELITY_TRIGGER,
        subtlety=FIDELITY_SUBTLETY,
    )


# ----- model-variance (ML-AI) -----

MODEL_VARIANCE_DESC = (
    "Gohar Evidence-Validity 'Model Variance' — for ML/AI models, training "
    "with different random seeds produces materially different predictions, "
    "and the variance is not characterized in the package"
)
MODEL_VARIANCE_TASK = (
    "generate a UnitOfAssurance for an ML/AI model where the bindsModel is "
    "an ML model. ValidationResults report a single training run's "
    "performance with no discussion of seed-to-seed variance."
)
MODEL_VARIANCE_TRIGGER = (
    "bindsModel narrative describes an ML model (neural network, random "
    "forest, transformer). ValidationResults report point-estimate metrics "
    "without any mention of training-seed variance, ensemble averages, "
    "or model-variance UQ."
)
MODEL_VARIANCE_SUBTLETY = _gp_subtlety(
    low="Single training run, no mention of variance at all.",
    medium="Narrative says 'reproducibility studied informally' without numbers.",
    high="Two seed runs reported, agreement claimed without statistical bounds.",
)


def _r_model_variance(spec, context):
    return _gp_render(
        spec, context,
        description=MODEL_VARIANCE_DESC,
        task=MODEL_VARIANCE_TASK,
        trigger=MODEL_VARIANCE_TRIGGER,
        subtlety=MODEL_VARIANCE_SUBTLETY,
    )


# ----- robustness (ML-AI) -----

ROBUSTNESS_DESC = (
    "Gohar Evidence-Validity 'Robustness' — for ML/AI models, behavior "
    "under distribution shift, noise, or adversarial perturbation is not "
    "characterized; only nominal-condition validation is reported"
)
ROBUSTNESS_TASK = (
    "generate a UnitOfAssurance for an ML/AI model whose ValidationResults "
    "report nominal-condition performance without any robustness or "
    "distribution-shift testing."
)
ROBUSTNESS_TRIGGER = (
    "bindsModel narrative describes an ML model. ValidationResults are "
    "all on the test set drawn from the same distribution as training. "
    "No noise injection, no covariate shift study, no adversarial "
    "evaluation is linked."
)
ROBUSTNESS_SUBTLETY = _gp_subtlety(
    low="No mention of robustness or distribution shift at all.",
    medium="Narrative says 'real-world distribution shift studied separately'; no link.",
    high="One out-of-distribution sample is reported; narrative claims model 'generalizes' without statistical evidence.",
)


def _r_robustness(spec, context):
    return _gp_render(
        spec, context,
        description=ROBUSTNESS_DESC,
        task=ROBUSTNESS_TASK,
        trigger=ROBUSTNESS_TRIGGER,
        subtlety=ROBUSTNESS_SUBTLETY,
    )


_RENDERERS = {
    "data-drift": _r_data_drift,
    "inadequate-metrics": _r_inadequate_metrics,
    "coverage-edge-cases": _r_coverage_edge,
    "fidelity": _r_fidelity,
    "model-variance": _r_model_variance,
    "robustness": _r_robustness,
}


def render(spec, context: dict) -> tuple[str, str]:
    leaf = (spec.source_taxonomy or "").rsplit("/", 1)[-1]
    fn = _RENDERERS.get(leaf)
    if fn is None:
        raise NotImplementedError(
            f"evidence_validity does not handle source_taxonomy "
            f"{spec.source_taxonomy!r}"
        )
    return fn(spec, context)

"""Gohar Contextual gap_probe templates (Phase 2 spec §7 rows 12-16).

Six sub-types in Gohar Table II: faults-physical, faults-software,
human-errors, configuration, monitoring (deferred), environmental-factors.
Phase 2 spec §7 covers 5 of them (skips monitoring).

This module hosts ALL contextual templates; spec rows 12-16 land here
across Milestones 2 (faults-physical, faults-software) and 3 (the rest).
"""

from __future__ import annotations

from uofa_cli.adversarial.prompts.base import (
    BASE_SYSTEM_PROMPT,
    build_user_prompt,
    validate_subtlety_examples,
)

PROMPT_VERSION = "v1.0.0"

SYSTEM_PROMPT = BASE_SYSTEM_PROMPT


def _gp_subtlety(low, medium, high):
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


# ----- faults-physical (M2) -----

FAULTS_PHYS_DESC = (
    "Gohar Contextual 'Faults — Physical' — physical faults (sensor failure, "
    "actuator wear, electrical short) that the system can encounter in "
    "operation are not represented in the validation campaign or the model"
)
FAULTS_PHYS_TASK = (
    "generate a UnitOfAssurance whose ContextOfUse narrative implies "
    "operation in conditions where physical hardware faults are possible "
    "(harsh environment, long duty cycle), but the model and ValidationResults "
    "assume nominal hardware behavior throughout."
)
FAULTS_PHYS_TRIGGER = (
    "ContextOfUse.description references operational conditions (e.g., "
    "'24/7 industrial deployment', 'in vivo'). Model narrative does not "
    "include any fault states. ValidationResults are all on nominal "
    "hardware. No FaultMode entity is linked."
)
FAULTS_PHYS_SUBTLETY = _gp_subtlety(
    "No mention of hardware faults at all.",
    "Narrative says 'fault tolerance documented elsewhere' without link.",
    "One fault mode tested; the dominant operational fault modes are not.",
)


def _r_faults_physical(spec, context):
    return _gp_render(
        spec, context,
        description=FAULTS_PHYS_DESC,
        task=FAULTS_PHYS_TASK,
        trigger=FAULTS_PHYS_TRIGGER,
        subtlety=FAULTS_PHYS_SUBTLETY,
    )


# ----- faults-software (M2) -----

FAULTS_SW_DESC = (
    "Gohar Contextual 'Faults — Software' — software faults (race "
    "conditions, numerical instability, edge-case crashes) that the system "
    "can encounter are not modeled or validated against"
)
FAULTS_SW_TASK = (
    "generate a UnitOfAssurance whose model is software-intensive (e.g., "
    "FEA solver, ML pipeline) but the validation does not exercise "
    "software-fault modes (crashes, numerical NaN, race conditions)."
)
FAULTS_SW_TRIGGER = (
    "Model narrative describes software components. ValidationResults all "
    "report 'nominal completion'. No mention of solver convergence "
    "failure, numerical instability, or runtime exceptions."
)
FAULTS_SW_SUBTLETY = _gp_subtlety(
    "No software-fault discussion at all.",
    "Narrative says 'solver robustness studied informally' without metrics.",
    "One solver-failure case mentioned; the dominant numerical-failure modes are not exercised.",
)


def _r_faults_software(spec, context):
    return _gp_render(
        spec, context,
        description=FAULTS_SW_DESC,
        task=FAULTS_SW_TASK,
        trigger=FAULTS_SW_TRIGGER,
        subtlety=FAULTS_SW_SUBTLETY,
    )


# ----- human-errors (M3) -----

HUMAN_ERRORS_DESC = (
    "Gohar Contextual 'Human Errors' — operator/user errors (misuse, "
    "incorrect inputs, training gaps) that the system encounters in real "
    "deployment are not modeled or validated"
)
HUMAN_ERRORS_TASK = (
    "generate a UnitOfAssurance for a system that has a human-in-the-loop "
    "but ValidationResults assume correct user inputs throughout. No use "
    "error modes are characterized."
)
HUMAN_ERRORS_TRIGGER = (
    "ContextOfUse references an operator role (clinician, pilot, technician). "
    "ValidationResults are all on correctly-formatted inputs. No "
    "use-error or misuse evaluation is linked. Use-error CredibilityFactor "
    "(if present) is 'not-assessed' without justification."
)
HUMAN_ERRORS_SUBTLETY = _gp_subtlety(
    "No mention of operator behavior at all.",
    "Narrative says 'use-error evaluation per IEC 62366 in companion document'; no link.",
    "One use-error scenario reported; common operator errors not covered.",
)


def _r_human_errors(spec, context):
    return _gp_render(
        spec, context,
        description=HUMAN_ERRORS_DESC,
        task=HUMAN_ERRORS_TASK,
        trigger=HUMAN_ERRORS_TRIGGER,
        subtlety=HUMAN_ERRORS_SUBTLETY,
    )


# ----- configuration (M3, §6.7 W-CX-01 candidate) -----

CONFIGURATION_DESC = (
    "Gohar Contextual 'Configuration' — configuration parameters that the "
    "system depends on are not pinned, documented, or validated; "
    "deployment may use different settings than validation"
)
CONFIGURATION_TASK = (
    "generate a UnitOfAssurance whose model has tunable configuration "
    "parameters (mesh size, learning rate, threshold). ValidationResults "
    "use specific values but the package does not pin those values for "
    "deployment."
)
CONFIGURATION_TRIGGER = (
    "Model narrative names configuration parameters. ValidationResults "
    "report results 'at the chosen settings'. No `bindsConfiguration` or "
    "settings node is linked. ContextOfUse does not constrain the "
    "deployment configuration."
)
CONFIGURATION_SUBTLETY = _gp_subtlety(
    "No mention of configuration at all; deployment values unspecified.",
    "Configuration mentioned in narrative; values not in structured fields.",
    "Configuration partially pinned (some values), but a key parameter is left to deployment-time choice.",
)


def _r_configuration(spec, context):
    return _gp_render(
        spec, context,
        description=CONFIGURATION_DESC,
        task=CONFIGURATION_TASK,
        trigger=CONFIGURATION_TRIGGER,
        subtlety=CONFIGURATION_SUBTLETY,
    )


# ----- environmental-factors (M3) -----

ENVIRONMENTAL_DESC = (
    "Gohar Contextual 'Environmental Factors' — operating environment "
    "parameters (temperature, pressure, EM interference) that affect "
    "system behavior are not characterized in the validation"
)
ENVIRONMENTAL_TASK = (
    "generate a UnitOfAssurance whose deployment environment varies in "
    "ways that affect the model (temperature drift, electromagnetic "
    "interference, ambient pressure), but ValidationResults are all under "
    "lab conditions."
)
ENVIRONMENTAL_TRIGGER = (
    "ContextOfUse describes a real-world deployment environment. "
    "ValidationResults narrative says 'tested in laboratory at 22°C, "
    "atmospheric pressure'. No environmental-sensitivity study is linked. "
    "Operating envelope (if present) does not bound the environmental "
    "parameters."
)
ENVIRONMENTAL_SUBTLETY = _gp_subtlety(
    "Environment not bounded; lab-only validation.",
    "Environment mentioned in narrative; range studied informally.",
    "One environmental dimension tested (temperature); others (humidity, EMI) ignored.",
)


def _r_environmental(spec, context):
    return _gp_render(
        spec, context,
        description=ENVIRONMENTAL_DESC,
        task=ENVIRONMENTAL_TASK,
        trigger=ENVIRONMENTAL_TRIGGER,
        subtlety=ENVIRONMENTAL_SUBTLETY,
    )


_RENDERERS = {
    "faults-physical": _r_faults_physical,
    "faults-software": _r_faults_software,
    "human-errors": _r_human_errors,
    "configuration": _r_configuration,
    "environmental-factors": _r_environmental,
}


def render(spec, context: dict) -> tuple[str, str]:
    leaf = (spec.source_taxonomy or "").rsplit("/", 1)[-1]
    fn = _RENDERERS.get(leaf)
    if fn is None:
        raise NotImplementedError(
            f"contextual does not handle {spec.source_taxonomy!r}"
        )
    return fn(spec, context)

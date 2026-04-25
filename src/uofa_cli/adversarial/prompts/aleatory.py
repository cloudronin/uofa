"""Aleatory uncertainty weakeners — W-AL-01 (no UQ) and W-AL-02 (UQ
without sensitivity analysis)."""

from __future__ import annotations

from uofa_cli.adversarial.prompts.base import (
    BASE_SYSTEM_PROMPT,
    build_user_prompt,
    validate_subtlety_examples,
)

PROMPT_VERSION = "v1.0.0"

SYSTEM_PROMPT = BASE_SYSTEM_PROMPT


W_AL_01_DESCRIPTION = (
    "missing uncertainty quantification — at least one ValidationResult "
    "has no `hasUncertaintyQuantification` link, leaving aleatory "
    "uncertainty uncharacterized"
)
W_AL_01_TASK = (
    "generate a UnitOfAssurance package where at least one ValidationResult "
    "inline object lacks the `hasUncertaintyQuantification` field. The "
    "package's top-level `hasUncertaintyQuantification` may be true or "
    "false; the rule fires on the per-result field."
)
W_AL_01_TRIGGER = (
    "Emit at least one ValidationResult inline object with `id`, `type`, "
    "`name` but WITHOUT `hasUncertaintyQuantification`. Other "
    "ValidationResults may have it set to a UQ node IRI; at least one "
    "must lack the field."
)
W_AL_01_SUBTLETY = {
    "low": (
        "All ValidationResults lack the field. Narrative does not "
        "discuss uncertainty at all."
    ),
    "medium": (
        "About half lack the field. Narrative discusses uncertainty in "
        "prose without linking specific UQ artifacts."
    ),
    "high": (
        "Exactly one ValidationResult lacks the field, and that one is "
        "described in narrative as having 'inherent variability assessed "
        "qualitatively' — leaving the structured UQ link absent."
    ),
}
validate_subtlety_examples(W_AL_01_SUBTLETY)


def _render_w_al_01(spec, context):
    return BASE_SYSTEM_PROMPT, build_user_prompt(
        weakener=spec.target_weakener,
        weakener_description=W_AL_01_DESCRIPTION,
        defeater_type="Aleatory — missing UQ",
        subtlety=spec.subtlety,
        subtlety_guidance=W_AL_01_SUBTLETY[spec.subtlety],
        base_cou_identity=context.get("identity"),
        context_of_use=context.get("context_of_use"),
        factor_scaffold=context.get("factor_scaffold", []),
        context_url=context.get("context_url", ""),
        decision=spec.decision,
        task=W_AL_01_TASK,
        trigger_block=W_AL_01_TRIGGER,
    )


# ----- W-AL-02: UQ declared but no sensitivity analysis -----

W_AL_02_DESCRIPTION = (
    "sensitivity gap — UQ is declared on the package "
    "(`hasUncertaintyQuantification: true`) but no `hasSensitivityAnalysis` "
    "is linked, so the dominant input drivers are uncharacterized"
)
W_AL_02_TASK = (
    "generate a UnitOfAssurance package with "
    "`hasUncertaintyQuantification: true` (top-level) but NO "
    "`hasSensitivityAnalysis` field on the UofA."
)
W_AL_02_TRIGGER = (
    "Emit `hasUncertaintyQuantification: true` on the UnitOfAssurance "
    "(top-level boolean). Do NOT emit `hasSensitivityAnalysis` "
    "(or its IRI) anywhere in the package."
)
W_AL_02_SUBTLETY = {
    "low": (
        "UQ is described in narrative as 'comprehensive Monte Carlo across "
        "all inputs' but no sensitivity link exists. Sensitivity is not "
        "mentioned at all."
    ),
    "medium": (
        "UQ narrative mentions sensitivity in passing ('we plan to extend "
        "with sensitivity analysis') without linking a SensitivityAnalysis "
        "artifact."
    ),
    "high": (
        "UQ narrative cites a 'screening sensitivity study' verbally but "
        "the structured `hasSensitivityAnalysis` link is absent. Reviewer "
        "would assume the link was simply not encoded."
    ),
}
validate_subtlety_examples(W_AL_02_SUBTLETY)


W_AL_02_EXTRA_SCHEMA_RULES = (
    "- `hasUncertaintyQuantification`: top-level boolean on UnitOfAssurance.\n"
    "- `hasSensitivityAnalysis`: omit entirely (do not write it as null)."
)


def _render_w_al_02(spec, context):
    return BASE_SYSTEM_PROMPT, build_user_prompt(
        weakener=spec.target_weakener,
        weakener_description=W_AL_02_DESCRIPTION,
        defeater_type="Aleatory — sensitivity gap",
        subtlety=spec.subtlety,
        subtlety_guidance=W_AL_02_SUBTLETY[spec.subtlety],
        base_cou_identity=context.get("identity"),
        context_of_use=context.get("context_of_use"),
        factor_scaffold=context.get("factor_scaffold", []),
        context_url=context.get("context_url", ""),
        decision=spec.decision,
        task=W_AL_02_TASK,
        trigger_block=W_AL_02_TRIGGER,
        extra_schema_rules=W_AL_02_EXTRA_SCHEMA_RULES,
    )


_RENDERERS = {
    "W-AL-01": _render_w_al_01,
    "W-AL-02": _render_w_al_02,
}


def render(spec, context: dict) -> tuple[str, str]:
    fn = _RENDERERS.get(spec.target_weakener)
    if fn is None:
        raise NotImplementedError(
            f"aleatory does not handle {spec.target_weakener!r}"
        )
    return fn(spec, context)

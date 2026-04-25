"""Ontological uncertainty weakeners — W-ON-01 (missing COU) and W-ON-02
(unbounded applicability)."""

from __future__ import annotations

from uofa_cli.adversarial.prompts.base import (
    BASE_SYSTEM_PROMPT,
    build_user_prompt,
    validate_subtlety_examples,
)

PROMPT_VERSION = "v1.0.0"

SYSTEM_PROMPT = BASE_SYSTEM_PROMPT


# Note: W-ON-01 fires when there is no `hasContextOfUse` at all. For
# adversarial generation we cannot omit hasContextOfUse and still pass
# SHACL Complete (it is required). Phase 2 confirm_existing for W-ON-01
# therefore generates the rare-but-possible Minimal-profile package whose
# Minimal SHACL allows hasContextOfUse to be absent. The classifier is
# expected to accept this as the documented W-ON-01 scope.

W_ON_01_DESCRIPTION = (
    "missing Context of Use — the UnitOfAssurance has no `hasContextOfUse` "
    "field, leaving intended-use scope undefined"
)
W_ON_01_TASK = (
    "generate a Minimal-profile UnitOfAssurance package that omits "
    "`hasContextOfUse` entirely. Use `conformsToProfile: \"https://uofa.net/"
    "vocab#ProfileMinimal\"` so the SHACL Complete shape (which requires "
    "hasContextOfUse) does not apply."
)
W_ON_01_TRIGGER = (
    "Emit `conformsToProfile: \"https://uofa.net/vocab#ProfileMinimal\"`. "
    "Do NOT emit `hasContextOfUse` anywhere. Provide enough other fields "
    "(bindsRequirement, hasDecisionRecord) to pass MinimalBody SHACL."
)
W_ON_01_SUBTLETY = {
    "low": (
        "Package has bindsRequirement and a DecisionRecord but no narrative "
        "anywhere describing where the model would be used. Reviewer can "
        "tell at a glance the use scope is undefined."
    ),
    "medium": (
        "The package narrative paragraphs implicitly suggest a use scope "
        "('this model has been applied in clinical research') without any "
        "structured ContextOfUse."
    ),
    "high": (
        "The package's Claim and Requirement nodes are written richly and "
        "imply a clear use scope, but the structured `hasContextOfUse` "
        "link is absent. Reviewer might assume the COU lives in the "
        "Claim/Requirement prose."
    ),
}
validate_subtlety_examples(W_ON_01_SUBTLETY)


def _render_w_on_01(spec, context):
    return BASE_SYSTEM_PROMPT, build_user_prompt(
        weakener=spec.target_weakener,
        weakener_description=W_ON_01_DESCRIPTION,
        defeater_type="Ontological — missing COU",
        subtlety=spec.subtlety,
        subtlety_guidance=W_ON_01_SUBTLETY[spec.subtlety],
        base_cou_identity=context.get("identity"),
        context_of_use=None,
        factor_scaffold=context.get("factor_scaffold", []),
        context_url=context.get("context_url", ""),
        decision=spec.decision,
        task=W_ON_01_TASK,
        trigger_block=W_ON_01_TRIGGER,
    )


# ----- W-ON-02: unbounded applicability -----

W_ON_02_DESCRIPTION = (
    "unbounded applicability — the ContextOfUse declares neither "
    "`hasApplicabilityConstraint` nor `hasOperatingEnvelope`, so the "
    "model's range of valid use is unspecified"
)
W_ON_02_TASK = (
    "generate a UnitOfAssurance whose ContextOfUse inline object has no "
    "`hasApplicabilityConstraint` link AND no `hasOperatingEnvelope` "
    "link. Other ContextOfUse fields (name, description, deviceClass) "
    "may be fully populated."
)
W_ON_02_TRIGGER = (
    "Emit `hasContextOfUse` as a fully-formed inline object including "
    "`id`, `type: \"ContextOfUse\"`, `name`, `description`, `intendedUse`, "
    "`deviceClass`, `modelInfluence`, `decisionConsequence`. Do NOT emit "
    "`hasApplicabilityConstraint` or `hasOperatingEnvelope` on that object."
)
W_ON_02_SUBTLETY = {
    "low": (
        "ContextOfUse is sparse — name, description, and deviceClass only. "
        "No envelope, no applicability constraint."
    ),
    "medium": (
        "ContextOfUse is well-described in prose, references operating "
        "ranges in `description`, but lacks the structured envelope/"
        "constraint links."
    ),
    "high": (
        "ContextOfUse `description` enumerates operating ranges in detail "
        "(temperature, pressure, flow regime). The reader assumes these "
        "are the operating envelope, but no `hasOperatingEnvelope` link "
        "is emitted."
    ),
}
validate_subtlety_examples(W_ON_02_SUBTLETY)


def _render_w_on_02(spec, context):
    return BASE_SYSTEM_PROMPT, build_user_prompt(
        weakener=spec.target_weakener,
        weakener_description=W_ON_02_DESCRIPTION,
        defeater_type="Ontological — unbounded applicability",
        subtlety=spec.subtlety,
        subtlety_guidance=W_ON_02_SUBTLETY[spec.subtlety],
        base_cou_identity=context.get("identity"),
        context_of_use=context.get("context_of_use"),
        factor_scaffold=context.get("factor_scaffold", []),
        context_url=context.get("context_url", ""),
        decision=spec.decision,
        task=W_ON_02_TASK,
        trigger_block=W_ON_02_TRIGGER,
    )


_RENDERERS = {
    "W-ON-01": _render_w_on_01,
    "W-ON-02": _render_w_on_02,
}


def render(spec, context: dict) -> tuple[str, str]:
    fn = _RENDERERS.get(spec.target_weakener)
    if fn is None:
        raise NotImplementedError(
            f"ontological does not handle {spec.target_weakener!r}"
        )
    return fn(spec, context)

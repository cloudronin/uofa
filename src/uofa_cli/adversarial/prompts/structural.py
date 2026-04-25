"""Structural integrity weakeners — W-SI-01 (missing signature) and
W-SI-02 (incomplete profile binding)."""

from __future__ import annotations

from uofa_cli.adversarial.prompts.base import (
    BASE_SYSTEM_PROMPT,
    build_user_prompt,
    validate_subtlety_examples,
)

PROMPT_VERSION = "v1.0.0"

SYSTEM_PROMPT = BASE_SYSTEM_PROMPT


W_SI_01_DESCRIPTION = (
    "missing digital signature — the UnitOfAssurance has no `signature` "
    "field, so structural integrity is unverifiable"
)
W_SI_01_TASK = (
    "generate a Minimal-profile UnitOfAssurance package that omits "
    "`signature` entirely. Use `conformsToProfile: \"https://uofa.net/"
    "vocab#ProfileMinimal\"` (Complete profile requires signature)."
)
W_SI_01_TRIGGER = (
    "Emit `conformsToProfile: \"https://uofa.net/vocab#ProfileMinimal\"`. "
    "Emit `hash` as a valid sha256 string but DO NOT emit `signature`. "
    "Other fields (bindsRequirement, hasDecisionRecord) populated normally."
)
W_SI_01_SUBTLETY = {
    "low": (
        "Package has hash but no signature. No mention of signing in "
        "narrative."
    ),
    "medium": (
        "Package has hash, narrative says 'pending signature workflow' "
        "but signature field is absent."
    ),
    "high": (
        "Package has hash and a `signatureAlg: \"ed25519\"` field "
        "(declared algorithm) but the actual `signature` value is omitted. "
        "Looks like a partially-signed artifact."
    ),
}
validate_subtlety_examples(W_SI_01_SUBTLETY)


def _render_w_si_01(spec, context):
    return BASE_SYSTEM_PROMPT, build_user_prompt(
        weakener=spec.target_weakener,
        weakener_description=W_SI_01_DESCRIPTION,
        defeater_type="Structural — missing signature",
        subtlety=spec.subtlety,
        subtlety_guidance=W_SI_01_SUBTLETY[spec.subtlety],
        base_cou_identity=context.get("identity"),
        context_of_use=context.get("context_of_use"),
        factor_scaffold=context.get("factor_scaffold", []),
        context_url=context.get("context_url", ""),
        decision=spec.decision,
        task=W_SI_01_TASK,
        trigger_block=W_SI_01_TRIGGER,
    )


# ----- W-SI-02: missing bindsRequirement -----

W_SI_02_DESCRIPTION = (
    "incomplete profile binding — the UnitOfAssurance is missing one of "
    "the required binds* properties (typically `bindsRequirement`)"
)
W_SI_02_TASK = (
    "generate a Minimal-profile UnitOfAssurance package that omits "
    "`bindsRequirement` entirely. Use Minimal profile so the Complete "
    "SHACL bindRequirement requirement does not apply at validation time."
)
W_SI_02_TRIGGER = (
    "Emit `conformsToProfile: \"https://uofa.net/vocab#ProfileMinimal\"`. "
    "Do NOT emit `bindsRequirement` anywhere. Other fields normal."
)
W_SI_02_SUBTLETY = {
    "low": (
        "Package has no requirement reference at all — neither in "
        "structured form nor in prose."
    ),
    "medium": (
        "Package narrative paragraphs reference 'project requirements' "
        "in prose but the structured `bindsRequirement` IRI is absent."
    ),
    "high": (
        "Package binds Claim, Model, and Dataset properly. The narrative "
        "describes requirements, and an inline Requirement object even "
        "exists somewhere in the package — but the top-level "
        "`bindsRequirement` link to it is omitted."
    ),
}
validate_subtlety_examples(W_SI_02_SUBTLETY)


def _render_w_si_02(spec, context):
    return BASE_SYSTEM_PROMPT, build_user_prompt(
        weakener=spec.target_weakener,
        weakener_description=W_SI_02_DESCRIPTION,
        defeater_type="Structural — missing bindsRequirement",
        subtlety=spec.subtlety,
        subtlety_guidance=W_SI_02_SUBTLETY[spec.subtlety],
        base_cou_identity=context.get("identity"),
        context_of_use=context.get("context_of_use"),
        factor_scaffold=context.get("factor_scaffold", []),
        context_url=context.get("context_url", ""),
        decision=spec.decision,
        task=W_SI_02_TASK,
        trigger_block=W_SI_02_TRIGGER,
    )


_RENDERERS = {
    "W-SI-01": _render_w_si_01,
    "W-SI-02": _render_w_si_02,
}


def render(spec, context: dict) -> tuple[str, str]:
    fn = _RENDERERS.get(spec.target_weakener)
    if fn is None:
        raise NotImplementedError(
            f"structural does not handle {spec.target_weakener!r}"
        )
    return fn(spec, context)

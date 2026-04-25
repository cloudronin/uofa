"""Epistemic uncertainty weakeners — W-EP-01 through W-EP-04.

The four W-EP rules detect epistemic gaps in the provenance / pedigree
of evidence backing the UofA's claim:

- W-EP-01 [Critical] — Claim has no ``prov:wasDerivedFrom`` to any Evidence
- W-EP-02 [High]     — ValidationResult has no ``prov:wasGeneratedBy`` Activity
- W-EP-03 [High]     — Dataset ``dataVintage`` predates UofA ``modelRevisionDate``
- W-EP-04 [High]     — Factor unassessed at modelRiskLevel > 2
"""

from __future__ import annotations

from uofa_cli.adversarial.prompts.base import (
    BASE_SYSTEM_PROMPT,
    build_user_prompt,
    validate_subtlety_examples,
)

PROMPT_VERSION = "v1.0.0"

SYSTEM_PROMPT = BASE_SYSTEM_PROMPT


# ----- W-EP-01: orphan claim, no provenance to evidence -----

W_EP_01_DESCRIPTION = (
    "orphan claim — bindsClaim references a Claim node that has no "
    "prov:wasDerivedFrom link to any Evidence; the claim is unsupported"
)
W_EP_01_TASK = (
    "generate a UnitOfAssurance package whose `bindsClaim` IRI resolves to "
    "an inline Claim node that does NOT carry `prov:wasDerivedFrom`. The "
    "claim should look meaningful (purpose, statement, scope) but lack the "
    "structured derivation link to Evidence."
)
W_EP_01_TRIGGER = (
    "Emit `bindsClaim` as an IRI on the UnitOfAssurance and include an "
    "inline Claim object in the package (or referenced by IRI) that has "
    "`type: \"Claim\"` and a `name` and `description` but does NOT have "
    "`prov:wasDerivedFrom` (or `wasDerivedFrom`). Other package nodes "
    "(ValidationResult etc.) MAY have wasDerivedFrom; the Claim itself "
    "must lack it."
)
W_EP_01_SUBTLETY = {
    "low": (
        "The Claim is brief (one sentence) and has no provenance fields "
        "at all. The package text mentions evidence in passing but does "
        "not link any IRI to the claim."
    ),
    "medium": (
        "The Claim has a thorough description and references a body of "
        "supporting work in prose, but the structured `prov:wasDerivedFrom` "
        "link is absent. A reviewer scanning prose would think the claim "
        "is supported."
    ),
    "high": (
        "The Claim is richly described, the package includes ValidationResults "
        "with full provenance chains to Evidence, and at first glance the "
        "claim appears well-supported. The omission is that the Claim "
        "itself does not link to any Evidence — only the ValidationResults do."
    ),
}
validate_subtlety_examples(W_EP_01_SUBTLETY)


def _render_w_ep_01(spec, context):
    return BASE_SYSTEM_PROMPT, build_user_prompt(
        weakener=spec.target_weakener,
        weakener_description=W_EP_01_DESCRIPTION,
        defeater_type="Epistemic — orphan claim",
        subtlety=spec.subtlety,
        subtlety_guidance=W_EP_01_SUBTLETY[spec.subtlety],
        base_cou_identity=context.get("identity"),
        context_of_use=context.get("context_of_use"),
        factor_scaffold=context.get("factor_scaffold", []),
        context_url=context.get("context_url", ""),
        decision=spec.decision,
        task=W_EP_01_TASK,
        trigger_block=W_EP_01_TRIGGER,
    )


# ----- W-EP-02: validation result without generation activity -----

W_EP_02_DESCRIPTION = (
    "broken provenance on a validation result — at least one "
    "ValidationResult has no `prov:wasGeneratedBy` link to a generation "
    "Activity"
)
W_EP_02_TASK = (
    "generate a UnitOfAssurance package where at least one ValidationResult "
    "inline object does NOT carry `prov:wasGeneratedBy`. The narrative "
    "may discuss the testing/simulation that produced the result, but the "
    "structured Activity link is missing."
)
W_EP_02_TRIGGER = (
    "Emit at least one ValidationResult inline object with `id`, `type`, "
    "`name`, optionally `comparedAgainst`, but NOT `prov:wasGeneratedBy` "
    "(or `wasGeneratedBy`). Other ValidationResults may have it; at least "
    "one must lack it."
)
W_EP_02_SUBTLETY = {
    "low": (
        "All ValidationResults lack `wasGeneratedBy`. The narrative is "
        "thin on how the results were produced."
    ),
    "medium": (
        "About half the ValidationResults lack the link. The narrative "
        "uses general terms ('experiments were performed') without naming "
        "the specific activity for each result."
    ),
    "high": (
        "Exactly one ValidationResult lacks the link, and that one has "
        "the most detailed prose narrative. A reviewer might assume the "
        "narrative substitutes for the structured activity reference."
    ),
}
validate_subtlety_examples(W_EP_02_SUBTLETY)


def _render_w_ep_02(spec, context):
    return BASE_SYSTEM_PROMPT, build_user_prompt(
        weakener=spec.target_weakener,
        weakener_description=W_EP_02_DESCRIPTION,
        defeater_type="Epistemic — missing generation activity",
        subtlety=spec.subtlety,
        subtlety_guidance=W_EP_02_SUBTLETY[spec.subtlety],
        base_cou_identity=context.get("identity"),
        context_of_use=context.get("context_of_use"),
        factor_scaffold=context.get("factor_scaffold", []),
        context_url=context.get("context_url", ""),
        decision=spec.decision,
        task=W_EP_02_TASK,
        trigger_block=W_EP_02_TRIGGER,
    )


# ----- W-EP-03: stale input data -----

W_EP_03_DESCRIPTION = (
    "stale input data — at least one Dataset's `dataVintage` predates the "
    "UofA's `modelRevisionDate`, so the dataset reflects a prior model build"
)
W_EP_03_TASK = (
    "generate a UnitOfAssurance package that declares `modelRevisionDate` "
    "and at least one bindsDataset whose Dataset node carries a "
    "`dataVintage` earlier than that revision date."
)
W_EP_03_TRIGGER = (
    "Emit `modelRevisionDate: \"<later-iso8601>\"` on the UnitOfAssurance. "
    "Emit at least one Dataset (referenced from bindsDataset) with "
    "`dataVintage: \"<earlier-iso8601>\"` strictly before modelRevisionDate. "
    "Use ISO-8601 dateTime format for both."
)
W_EP_03_SUBTLETY = {
    "low": (
        "Dataset vintage is years before the model revision (2018 vs 2026). "
        "The narrative does not address re-validation."
    ),
    "medium": (
        "Vintage is a few months before revision (2025-Q4 vs 2026-Q1). "
        "Narrative says re-validation is 'planned' without showing it."
    ),
    "high": (
        "Vintage is a few weeks before revision. Narrative argues the "
        "model change was 'not material' to the dataset's relevance "
        "without producing the formal re-validation."
    ),
}
validate_subtlety_examples(W_EP_03_SUBTLETY)


W_EP_03_EXTRA_SCHEMA_RULES = (
    "- `modelRevisionDate`: top-level ISO-8601 dateTime on the UnitOfAssurance.\n"
    "- `dataVintage`: ISO-8601 dateTime on a Dataset inline object."
)


def _render_w_ep_03(spec, context):
    return BASE_SYSTEM_PROMPT, build_user_prompt(
        weakener=spec.target_weakener,
        weakener_description=W_EP_03_DESCRIPTION,
        defeater_type="Epistemic — stale input data",
        subtlety=spec.subtlety,
        subtlety_guidance=W_EP_03_SUBTLETY[spec.subtlety],
        base_cou_identity=context.get("identity"),
        context_of_use=context.get("context_of_use"),
        factor_scaffold=context.get("factor_scaffold", []),
        context_url=context.get("context_url", ""),
        decision=spec.decision,
        task=W_EP_03_TASK,
        trigger_block=W_EP_03_TRIGGER,
        extra_schema_rules=W_EP_03_EXTRA_SCHEMA_RULES,
    )


# ----- W-EP-04: unassessed factor at elevated risk -----

W_EP_04_DESCRIPTION = (
    "unassessed factor at elevated risk — at least one CredibilityFactor "
    "has factorStatus 'not-assessed' while the package's modelRiskLevel "
    "exceeds 2 (so the factor's absence materially weakens credibility)"
)
W_EP_04_TASK = (
    "generate a UnitOfAssurance package with `modelRiskLevel: 3` (or higher) "
    "and at least one CredibilityFactor inline object with "
    "`factorStatus: \"not-assessed\"`. The not-assessed factor should be "
    "one of the V&V 40 Table 5-1 factor names."
)
W_EP_04_TRIGGER = (
    "Set `modelRiskLevel` to 3, 4, or 5 on the UnitOfAssurance. Emit at "
    "least one CredibilityFactor with `factorStatus: \"not-assessed\"`. "
    "The factor must omit requiredLevel and achievedLevel (since it is "
    "not assessed). Other factors may be 'assessed' with full data."
)
W_EP_04_SUBTLETY = {
    "low": (
        "modelRiskLevel is 5 (highest) and several factors are unassessed. "
        "Decision rationale does not justify the gaps."
    ),
    "medium": (
        "modelRiskLevel is 3 and two or three factors are unassessed. "
        "Rationale waves at 'beyond scope' without concrete justification."
    ),
    "high": (
        "modelRiskLevel is 3 and exactly one factor is unassessed. The "
        "factor's narrative argues it 'does not apply to the COU' without "
        "actually using factorStatus 'not-applicable' (which would be "
        "the right encoding)."
    ),
}
validate_subtlety_examples(W_EP_04_SUBTLETY)


W_EP_04_EXTRA_SCHEMA_RULES = (
    "- `modelRiskLevel`: integer 1..5 (top-level on the UnitOfAssurance).\n"
    "- A `not-assessed` CredibilityFactor must omit requiredLevel and\n"
    "  achievedLevel — those fields belong only on assessed factors."
)


def _render_w_ep_04(spec, context):
    return BASE_SYSTEM_PROMPT, build_user_prompt(
        weakener=spec.target_weakener,
        weakener_description=W_EP_04_DESCRIPTION,
        defeater_type="Epistemic — unassessed factor at elevated risk",
        subtlety=spec.subtlety,
        subtlety_guidance=W_EP_04_SUBTLETY[spec.subtlety],
        base_cou_identity=context.get("identity"),
        context_of_use=context.get("context_of_use"),
        factor_scaffold=context.get("factor_scaffold", []),
        context_url=context.get("context_url", ""),
        decision=spec.decision,
        task=W_EP_04_TASK,
        trigger_block=W_EP_04_TRIGGER,
        extra_schema_rules=W_EP_04_EXTRA_SCHEMA_RULES,
    )


_RENDERERS = {
    "W-EP-01": _render_w_ep_01,
    "W-EP-02": _render_w_ep_02,
    "W-EP-03": _render_w_ep_03,
    "W-EP-04": _render_w_ep_04,
}


def render(spec, context: dict) -> tuple[str, str]:
    fn = _RENDERERS.get(spec.target_weakener)
    if fn is None:
        raise NotImplementedError(
            f"epistemic does not handle {spec.target_weakener!r}"
        )
    return fn(spec, context)

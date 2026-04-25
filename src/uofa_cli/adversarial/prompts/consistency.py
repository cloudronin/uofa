"""UofA-native consistency weakeners — W-CON-01 through W-CON-05.

- W-CON-01 [High]   — Accepted decision but factor lacks both required and achieved levels
- W-CON-02 [Medium] — referencesIdentifier target does not resolve in graph
- W-CON-03 [High]   — evidenceTimestamp later than signatureTimestamp
- W-CON-04 [Medium] — Complete profile missing SensitivityAnalysis
- W-CON-05 [High]   — VerificationActivity declared, no Evidence linked via wasGeneratedBy
"""

from __future__ import annotations

from uofa_cli.adversarial.prompts.base import (
    BASE_SYSTEM_PROMPT,
    build_user_prompt,
    validate_subtlety_examples,
)

PROMPT_VERSION = "v1.0.0"

SYSTEM_PROMPT = BASE_SYSTEM_PROMPT


# ----- W-CON-01: factor-decision consistency -----

W_CON_01_DESCRIPTION = (
    "factor-decision inconsistency — the package's decision is Accepted "
    "but at least one CredibilityFactor has neither requiredLevel nor "
    "achievedLevel; the decision is not grounded in the structured factor "
    "evidence"
)
W_CON_01_TASK = (
    "generate a UnitOfAssurance with `hasDecisionRecord.outcome: \"Accepted\"` "
    "and at least one CredibilityFactor that omits BOTH requiredLevel AND "
    "achievedLevel."
)
W_CON_01_TRIGGER = (
    "Emit at least one CredibilityFactor inline object with "
    "`factorStatus: \"assessed\"` (or any other value) but neither "
    "`requiredLevel` nor `achievedLevel`. The hasDecisionRecord.outcome "
    "must be 'Accepted'."
)
W_CON_01_SUBTLETY = {
    "low": (
        "Several factors have no level data; rationale fields are sparse "
        "or missing. Decision rationale doesn't engage with factor levels."
    ),
    "medium": (
        "One or two factors lack level data. Rationale field has a generic "
        "explanation that is not factor-specific."
    ),
    "high": (
        "Exactly one factor lacks level data, and that factor has a "
        "richly-written rationale field describing 'qualitative assessment'. "
        "Reviewer might let this pass without checking for the structured "
        "level fields."
    ),
}
validate_subtlety_examples(W_CON_01_SUBTLETY)


def _render_w_con_01(spec, context):
    return BASE_SYSTEM_PROMPT, build_user_prompt(
        weakener=spec.target_weakener,
        weakener_description=W_CON_01_DESCRIPTION,
        defeater_type="Consistency — factor-decision",
        subtlety=spec.subtlety,
        subtlety_guidance=W_CON_01_SUBTLETY[spec.subtlety],
        base_cou_identity=context.get("identity"),
        context_of_use=context.get("context_of_use"),
        factor_scaffold=context.get("factor_scaffold", []),
        context_url=context.get("context_url", ""),
        decision="Accepted",  # W-CON-01 specifically requires Accepted
        task=W_CON_01_TASK,
        trigger_block=W_CON_01_TRIGGER,
    )


# ----- W-CON-02: identifier resolution -----

W_CON_02_DESCRIPTION = (
    "unresolved identifier reference — at least one `referencesIdentifier` "
    "value points to an IRI that does not declare an `rdf:type` anywhere "
    "in the package's graph and has no external-fetch hint"
)
W_CON_02_TASK = (
    "generate a UnitOfAssurance with at least one `referencesIdentifier` "
    "field whose target IRI is not declared as a node in the package "
    "(no rdf:type for that IRI). The reference looks like a real DOI or "
    "ORCID but the package does not include the referenced node."
)
W_CON_02_TRIGGER = (
    "Emit `referencesIdentifier` with an IRI value (e.g., a DOI or ORCID "
    "URL). Do NOT include a top-level node in the package whose `id` "
    "matches that IRI and that has a `type`. The reference dangles."
)
W_CON_02_SUBTLETY = {
    "low": (
        "Reference is a clearly-fake DOI (`10.0000/fake-paper`). No "
        "narrative supports the reference."
    ),
    "medium": (
        "Reference is a plausibly-shaped DOI for a paper that is not "
        "actually inlined in the package. Narrative cites the paper "
        "indirectly."
    ),
    "high": (
        "Reference is a real-looking DOI (`10.1016/j.ymeth.2024.03.003`) "
        "with rich narrative around it. The reference is not resolved "
        "in the local graph and there is no `referencesExternalSource` "
        "or fetch hint."
    ),
}
validate_subtlety_examples(W_CON_02_SUBTLETY)


W_CON_02_EXTRA_SCHEMA_RULES = (
    "- `referencesIdentifier`: IRI string. Do not also emit a node with\n"
    "  matching `id` and `type` for the referenced IRI."
)


def _render_w_con_02(spec, context):
    return BASE_SYSTEM_PROMPT, build_user_prompt(
        weakener=spec.target_weakener,
        weakener_description=W_CON_02_DESCRIPTION,
        defeater_type="Consistency — unresolved identifier",
        subtlety=spec.subtlety,
        subtlety_guidance=W_CON_02_SUBTLETY[spec.subtlety],
        base_cou_identity=context.get("identity"),
        context_of_use=context.get("context_of_use"),
        factor_scaffold=context.get("factor_scaffold", []),
        context_url=context.get("context_url", ""),
        decision=spec.decision,
        task=W_CON_02_TASK,
        trigger_block=W_CON_02_TRIGGER,
        extra_schema_rules=W_CON_02_EXTRA_SCHEMA_RULES,
    )


# ----- W-CON-03: future-dated evidence -----

W_CON_03_DESCRIPTION = (
    "future-dated evidence — at least one piece of evidence carries an "
    "`evidenceTimestamp` strictly later than the UofA's "
    "`signatureTimestamp` (evidence created after the package was signed)"
)
W_CON_03_TASK = (
    "generate a UnitOfAssurance that declares `signatureTimestamp` and "
    "at least one Evidence (or ValidationResult) with `evidenceTimestamp` "
    "strictly after that signature timestamp."
)
W_CON_03_TRIGGER = (
    "Emit `signatureTimestamp: \"<earlier-iso8601>\"` on the UnitOfAssurance. "
    "Emit at least one Evidence/ValidationResult node with "
    "`evidenceTimestamp: \"<later-iso8601>\"` that is strictly after the "
    "signature timestamp."
)
W_CON_03_SUBTLETY = {
    "low": (
        "Evidence is dated years after signature (2024 sign, 2027 evidence). "
        "Narrative does not address the discrepancy."
    ),
    "medium": (
        "Evidence dated weeks after signature. Narrative says the package "
        "was 'updated post-signing' without re-signing."
    ),
    "high": (
        "Evidence dated minutes/hours after signature. Looks like a "
        "race-condition artifact; the timestamps could plausibly be "
        "misread without close inspection."
    ),
}
validate_subtlety_examples(W_CON_03_SUBTLETY)


W_CON_03_EXTRA_SCHEMA_RULES = (
    "- `signatureTimestamp`: top-level ISO-8601 dateTime on UnitOfAssurance.\n"
    "- `evidenceTimestamp`: ISO-8601 dateTime on Evidence/ValidationResult."
)


def _render_w_con_03(spec, context):
    return BASE_SYSTEM_PROMPT, build_user_prompt(
        weakener=spec.target_weakener,
        weakener_description=W_CON_03_DESCRIPTION,
        defeater_type="Consistency — future-dated evidence",
        subtlety=spec.subtlety,
        subtlety_guidance=W_CON_03_SUBTLETY[spec.subtlety],
        base_cou_identity=context.get("identity"),
        context_of_use=context.get("context_of_use"),
        factor_scaffold=context.get("factor_scaffold", []),
        context_url=context.get("context_url", ""),
        decision=spec.decision,
        task=W_CON_03_TASK,
        trigger_block=W_CON_03_TRIGGER,
        extra_schema_rules=W_CON_03_EXTRA_SCHEMA_RULES,
    )


# ----- W-CON-04: profile-structure consistency -----

W_CON_04_DESCRIPTION = (
    "profile-structure inconsistency — the package conforms to "
    "ProfileComplete but declares no `hasSensitivityAnalysis` link, "
    "violating the v0.5 Complete-profile expectation"
)
W_CON_04_TASK = (
    "generate a Complete-profile UnitOfAssurance "
    "(`conformsToProfile: \"https://uofa.net/vocab#ProfileComplete\"`) "
    "without any `hasSensitivityAnalysis` field."
)
W_CON_04_TRIGGER = (
    "Emit `conformsToProfile: \"https://uofa.net/vocab#ProfileComplete\"` "
    "and ALL Complete SHACL fields (bindsRequirement, hasContextOfUse, "
    "bindsModel, bindsDataset, hasValidationResult, wasDerivedFrom, "
    "wasAttributedTo, generatedAtTime, hash, signature, modelRiskLevel). "
    "Do NOT emit `hasSensitivityAnalysis`. Discussion of UQ in narrative "
    "is fine; only the structured link must be absent."
)
W_CON_04_SUBTLETY = {
    "low": (
        "No discussion of sensitivity at all in narrative."
    ),
    "medium": (
        "Narrative mentions a 'screening sensitivity' that was performed "
        "but no SensitivityAnalysis node or link is emitted."
    ),
    "high": (
        "ValidationResults reference an 'UQ campaign' that included "
        "sensitivity. The reader assumes the link will be present; only "
        "the missing structured field reveals the gap."
    ),
}
validate_subtlety_examples(W_CON_04_SUBTLETY)


def _render_w_con_04(spec, context):
    return BASE_SYSTEM_PROMPT, build_user_prompt(
        weakener=spec.target_weakener,
        weakener_description=W_CON_04_DESCRIPTION,
        defeater_type="Consistency — profile/sensitivity",
        subtlety=spec.subtlety,
        subtlety_guidance=W_CON_04_SUBTLETY[spec.subtlety],
        base_cou_identity=context.get("identity"),
        context_of_use=context.get("context_of_use"),
        factor_scaffold=context.get("factor_scaffold", []),
        context_url=context.get("context_url", ""),
        decision=spec.decision,
        task=W_CON_04_TASK,
        trigger_block=W_CON_04_TRIGGER,
    )


# ----- W-CON-05: activity declared but no evidence linked -----

W_CON_05_DESCRIPTION = (
    "activity-evidence consistency gap — at least one VerificationActivity "
    "is declared via `hasVerificationActivity` but no Evidence is linked "
    "to that activity via `prov:wasGeneratedBy`"
)
W_CON_05_TASK = (
    "generate a UnitOfAssurance whose `hasVerificationActivity` "
    "references an Activity inline object that has no Evidence pointing "
    "to it via `prov:wasGeneratedBy`."
)
W_CON_05_TRIGGER = (
    "Emit `hasVerificationActivity` linking to an Activity (inline or by "
    "IRI). The Activity may have name/description/activityType but no "
    "Evidence/ValidationResult in the package emits "
    "`prov:wasGeneratedBy` pointing back to that Activity's IRI."
)
W_CON_05_SUBTLETY = {
    "low": (
        "Activity is declared but no narrative around what it produced. "
        "ValidationResults look unrelated."
    ),
    "medium": (
        "Activity is well-described in prose, ValidationResults discuss "
        "its outputs in narrative, but `prov:wasGeneratedBy` links point "
        "to a different Activity (or are absent)."
    ),
    "high": (
        "Activity has rich metadata. Some ValidationResults DO have "
        "`prov:wasGeneratedBy` pointing to other activities. The declared "
        "VerificationActivity has no incoming wasGeneratedBy from any "
        "Evidence or ValidationResult — looks like an orphan declaration."
    ),
}
validate_subtlety_examples(W_CON_05_SUBTLETY)


def _render_w_con_05(spec, context):
    return BASE_SYSTEM_PROMPT, build_user_prompt(
        weakener=spec.target_weakener,
        weakener_description=W_CON_05_DESCRIPTION,
        defeater_type="Consistency — activity/evidence",
        subtlety=spec.subtlety,
        subtlety_guidance=W_CON_05_SUBTLETY[spec.subtlety],
        base_cou_identity=context.get("identity"),
        context_of_use=context.get("context_of_use"),
        factor_scaffold=context.get("factor_scaffold", []),
        context_url=context.get("context_url", ""),
        decision=spec.decision,
        task=W_CON_05_TASK,
        trigger_block=W_CON_05_TRIGGER,
    )


_RENDERERS = {
    "W-CON-01": _render_w_con_01,
    "W-CON-02": _render_w_con_02,
    "W-CON-03": _render_w_con_03,
    "W-CON-04": _render_w_con_04,
    "W-CON-05": _render_w_con_05,
}


def render(spec, context: dict) -> tuple[str, str]:
    fn = _RENDERERS.get(spec.target_weakener)
    if fn is None:
        raise NotImplementedError(
            f"consistency does not handle {spec.target_weakener!r}"
        )
    return fn(spec, context)

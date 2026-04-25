"""D1 undermining (acceptance-criteria absence) prompt — Phase 2 W-AR-01.

W-AR-01 detects credibility factors that declare a `requiredLevel` but omit
the `acceptanceCriteria` link that documents the basis for that requirement.
Severity: Critical. The defeater undermines the rebuttal that the factor is
genuinely justified.
"""

from __future__ import annotations

from uofa_cli.adversarial.prompts.base import (
    BASE_SYSTEM_PROMPT,
    build_user_prompt,
    validate_subtlety_examples,
)

PROMPT_VERSION = "v1.0.0"

SYSTEM_PROMPT = BASE_SYSTEM_PROMPT

WEAKENER_DESCRIPTION = (
    "missing acceptance criteria — a credibility factor declares a "
    "requiredLevel but no `acceptanceCriteria` field documents the "
    "rationale for that level"
)

TASK = (
    "generate a UnitOfAssurance package where at least one CredibilityFactor "
    "carries `requiredLevel` but has NO `acceptanceCriteria` field. The "
    "factor's narrative may discuss what the level means, but the structured "
    "`acceptanceCriteria` link MUST be absent."
)

TRIGGER_BLOCK = (
    "Emit at least one CredibilityFactor inline object with `requiredLevel` "
    "set (integer 1..5) and `factorStatus: \"assessed\"` but WITHOUT an "
    "`acceptanceCriteria` key. Other factors MAY include `acceptanceCriteria`; "
    "at least one MUST omit it. Do not write `acceptanceCriteria: null` or "
    "an empty string — the key must be entirely absent from that factor's "
    "JSON object."
)

SUBTLETY_GUIDANCE = {
    "low": (
        "Make the omission obvious. Several factors should be missing "
        "`acceptanceCriteria`, and the rationale narrative for those factors "
        "should be sparse or generic."
    ),
    "medium": (
        "One or two factors should be missing `acceptanceCriteria`, but the "
        "rationale field still tells a coherent story. The reader has to "
        "look at the structured properties to notice the gap."
    ),
    "high": (
        "Exactly one factor should be missing `acceptanceCriteria`, and that "
        "factor should have a particularly long, well-written rationale "
        "field — the kind a reviewer would scan and assume the criteria "
        "were documented elsewhere. Plausible deniability without the "
        "structured link."
    ),
}

validate_subtlety_examples(SUBTLETY_GUIDANCE)


def render(spec, context: dict) -> tuple[str, str]:
    user = build_user_prompt(
        weakener=spec.target_weakener,
        weakener_description=WEAKENER_DESCRIPTION,
        defeater_type="D1 — undermining (acceptance-criteria absence)",
        subtlety=spec.subtlety,
        subtlety_guidance=SUBTLETY_GUIDANCE[spec.subtlety],
        base_cou_identity=context.get("identity"),
        context_of_use=context.get("context_of_use"),
        factor_scaffold=context.get("factor_scaffold", []),
        context_url=context.get("context_url", ""),
        decision=spec.decision,
        task=TASK,
        trigger_block=TRIGGER_BLOCK,
    )
    return SYSTEM_PROMPT, user

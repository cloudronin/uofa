"""D2 rebutting (contradictory result with Accepted decision) — Phase 2 W-AR-02.

W-AR-02 detects credibility factors where ``achievedLevel`` is below
``requiredLevel`` while the surrounding decision outcome is Accepted —
i.e., the decision contradicts the structured evidence. Severity: Critical.
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
    "rebutting defeater — at least one CredibilityFactor reports "
    "achievedLevel below requiredLevel while the package's decision is "
    "Accepted, contradicting the structural evidence"
)

TASK = (
    "generate a UnitOfAssurance package whose hasDecisionRecord.outcome is "
    "Accepted but at least one CredibilityFactor has achievedLevel strictly "
    "below requiredLevel. The decision rationale should appear plausible on "
    "a quick read but the structured level shortfall remains."
)

TRIGGER_BLOCK = (
    "Emit at least one CredibilityFactor inline object with both "
    "`requiredLevel` and `achievedLevel` integers where achievedLevel < "
    "requiredLevel (e.g., requiredLevel: 3, achievedLevel: 1). The factor's "
    "factorStatus must be 'assessed'. The hasDecisionRecord.outcome MUST "
    "be 'Accepted'."
)

SUBTLETY_GUIDANCE = {
    "low": (
        "Make the contradiction obvious. Multiple factors should show "
        "achievedLevel two or more steps below requiredLevel, and the "
        "decision rationale should be a single short sentence with no "
        "discussion of the shortfall."
    ),
    "medium": (
        "One or two factors show achievedLevel one step below requiredLevel. "
        "The rationale acknowledges general engineering caveats but does "
        "not address the specific shortfall."
    ),
    "high": (
        "Exactly one factor has achievedLevel one step below requiredLevel. "
        "The rationale is long, well-written, and offers indirect "
        "justifications (sample size, prior experience, expert judgment) "
        "that don't formally close the level gap. The kind of acceptance "
        "language a reviewer might let pass on first read."
    ),
}

validate_subtlety_examples(SUBTLETY_GUIDANCE)


def render(spec, context: dict) -> tuple[str, str]:
    user = build_user_prompt(
        weakener=spec.target_weakener,
        weakener_description=WEAKENER_DESCRIPTION,
        defeater_type="D2 — rebutting (decision contradicts evidence)",
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

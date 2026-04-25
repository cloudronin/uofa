"""Multi-target interaction templates (Phase 2 spec §7.3).

Six INT templates that instantiate two or more weakeners simultaneously
to test COMPOUND-01 / COMPOUND-03 cascade behavior. INT-1..INT-4 are
expected COMPOUND firings; INT-5 is the threshold-correctness control
(should NOT fire COMPOUND-01); INT-6 tests COMPOUND-03.

Dispatch is by ``spec_id`` since each INT specifies a distinct combination.
``coverage_intent: interaction``; ``target_weakener`` may name the primary
weakener while the secondary weaknesses come from the trigger block.
"""

from __future__ import annotations

from uofa_cli.adversarial.prompts.base import (
    BASE_SYSTEM_PROMPT,
    build_user_prompt,
    validate_subtlety_examples,
)

PROMPT_VERSION = "v1.0.0"

SYSTEM_PROMPT = BASE_SYSTEM_PROMPT


def _int_subtlety(low, medium, high):
    out = {"low": low, "medium": medium, "high": high}
    validate_subtlety_examples(out)
    return out


def _int_render(spec, context, *, description, task, trigger, subtlety):
    return BASE_SYSTEM_PROMPT, build_user_prompt(
        weakener=spec.target_weakener or "(interaction)",
        weakener_description=description,
        defeater_type=f"interaction — {spec.spec_id}",
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


INT_CONFIGS = {
    "int-1-critical-plus-high": {
        "description": "INT-1 — W-EP-01 (Critical) + W-AL-01 (High); expects COMPOUND-01",
        "task": (
            "generate a UnitOfAssurance that simultaneously triggers W-EP-01 "
            "(orphan claim with no prov:wasDerivedFrom) AND W-AL-01 (at "
            "least one ValidationResult missing hasUncertaintyQuantification). "
            "Both weakeners must coexist on the same UofA so COMPOUND-01 "
            "cascades."
        ),
        "trigger": (
            "(a) `bindsClaim` references a Claim with NO `prov:wasDerivedFrom`.\n"
            "(b) At least one ValidationResult lacks `hasUncertaintyQuantification`.\n"
            "Both must hold simultaneously."
        ),
        "subtlety": _int_subtlety(
            "Both weaknesses obvious; multiple Validation results lacking UQ; Claim has no provenance discussion.",
            "Single weakener of each severity; narrative does not address either.",
            "Both weaknesses embedded in an otherwise complete package; reviewer must inspect structured fields.",
        ),
    },
    "int-2-two-criticals": {
        "description": "INT-2 — W-EP-01 + W-AR-02 (both Critical); expects COMPOUND-01",
        "task": (
            "generate a package triggering both W-EP-01 (orphan claim) and "
            "W-AR-02 (achievedLevel < requiredLevel under Accepted decision). "
            "Both Critical; COMPOUND-01 cascades."
        ),
        "trigger": (
            "(a) Claim has no `prov:wasDerivedFrom`.\n"
            "(b) At least one CredibilityFactor has achievedLevel < "
            "requiredLevel; hasDecisionRecord.outcome is Accepted."
        ),
        "subtlety": _int_subtlety(
            "Multiple shortfall factors; broken provenance is conspicuous.",
            "Single shortfall factor; provenance gap is one specific Claim.",
            "Borderline shortfall (one step below); provenance gap is implicit.",
        ),
    },
    "int-3-high-assurance-with-gaps": {
        "description": "INT-3 — W-AR-05 (High) + assuranceLevel: High; expects COMPOUND-03",
        "task": (
            "generate a package with `assuranceLevel: \"High\"` and at least "
            "one ValidationResult lacking `comparedAgainst` (W-AR-05 High). "
            "The High assurance with a Critical weakener cascades COMPOUND-03."
        ),
        "trigger": (
            "(a) Top-level `assuranceLevel: \"High\"`.\n"
            "(b) At least one ValidationResult missing `comparedAgainst`."
        ),
        "subtlety": _int_subtlety(
            "Multiple ValidationResults lack comparator; assuranceLevel High is unjustified.",
            "Single ValidationResult lacks comparator; assuranceLevel High in narrative as well.",
            "Single ValidationResult lacks comparator narrative-style; structured field still says High.",
        ),
    },
    "int-4-three-way": {
        "description": "INT-4 — W-EP-01 + W-AL-01 + W-AR-05 (Critical+High+High); expects COMPOUND-01 multi",
        "task": (
            "generate a package triggering W-EP-01, W-AL-01, AND W-AR-05 "
            "all on the same UofA. COMPOUND-01 should fire multiple times "
            "from the (Critical, High) pairings."
        ),
        "trigger": (
            "(a) Claim with no `prov:wasDerivedFrom` (W-EP-01 Critical).\n"
            "(b) ValidationResult missing `hasUncertaintyQuantification` (W-AL-01 High).\n"
            "(c) ValidationResult missing `comparedAgainst` (W-AR-05 High)."
        ),
        "subtlety": _int_subtlety(
            "Multiple separate ValidationResults each missing one of UQ/comparator.",
            "Two ValidationResults; one missing UQ, one missing comparator.",
            "Single ValidationResult missing both UQ and comparator; one Claim with no provenance.",
        ),
    },
    "int-5-critical-plus-medium": {
        "description": "INT-5 — W-EP-01 (Critical) + W-AL-02 (Medium); expects COMPOUND-01 NOT to fire",
        "task": (
            "generate a package with W-EP-01 (Critical) and W-AL-02 (Medium "
            "— UQ declared but no SensitivityAnalysis). Per COMPOUND-01's "
            "Critical+High threshold, this combination should NOT cascade. "
            "INT-5 tests threshold correctness."
        ),
        "trigger": (
            "(a) Claim with no `prov:wasDerivedFrom`.\n"
            "(b) Top-level `hasUncertaintyQuantification: true` AND no "
            "`hasSensitivityAnalysis`. (Medium severity.)\n"
            "Critical and Medium coexist, but COMPOUND-01 needs Critical "
            "and High. The classifier should record COV-HIT on each but "
            "NOT COMPOUND-01."
        ),
        "subtlety": _int_subtlety(
            "Both weaknesses obvious.",
            "Both weaknesses present, narrative neutral.",
            "Both weaknesses embedded in otherwise full package.",
        ),
    },
    "int-6-accepted-with-critical": {
        "description": "INT-6 — W-AR-02 + decision Accepted; expects COMPOUND-03",
        "task": (
            "generate a package with W-AR-02 (achievedLevel < requiredLevel "
            "under Accepted decision) AND `assuranceLevel: \"Medium\"` so "
            "the assurance level is inconsistent with the Critical weakener "
            "(COMPOUND-03 fires)."
        ),
        "trigger": (
            "(a) `assuranceLevel: \"Medium\"` (or \"High\") at top level.\n"
            "(b) At least one CredibilityFactor with achievedLevel < "
            "requiredLevel.\n"
            "(c) `hasDecisionRecord.outcome: \"Accepted\"`."
        ),
        "subtlety": _int_subtlety(
            "Multiple shortfall factors; assuranceLevel High.",
            "Single shortfall factor; assuranceLevel Medium.",
            "Borderline shortfall (one step below); assuranceLevel Medium.",
        ),
    },
}


def render(spec, context: dict) -> tuple[str, str]:
    sid = spec.spec_id.lower()
    cfg = None
    for key in INT_CONFIGS:
        if key in sid:
            cfg = INT_CONFIGS[key]
            break
    if cfg is None:
        raise NotImplementedError(
            f"multi_target does not handle spec_id {spec.spec_id!r}. "
            f"Known archetype keys: {sorted(INT_CONFIGS)}"
        )
    return _int_render(
        spec, context,
        description=cfg["description"],
        task=cfg["task"],
        trigger=cfg["trigger"],
        subtlety=cfg["subtlety"],
    )

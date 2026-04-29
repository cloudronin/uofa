"""Negative-control templates (Phase 2 spec §7.2).

Ten clean-package templates (NC-1..NC-10) that should produce zero rule
firings. The classifier annotates each as COV-CLEAN-CORRECT (zero firings,
desired) or COV-CLEAN-WRONG (one or more firings, precision bug). The
false-positive rate computed from these is the catalog's published
precision number.

Per spec §7.2, NC specs use ``coverage_intent: negative_control`` and
``source_taxonomy: control/none``. Dispatch is by ``spec_id`` since each
NC targets a distinct clean-package archetype.
"""

from __future__ import annotations

from uofa_cli.adversarial.prompts.base import (
    BASE_SYSTEM_PROMPT,
    build_user_prompt,
    validate_subtlety_examples,
)

PROMPT_VERSION = "v1.0.0"

SYSTEM_PROMPT = BASE_SYSTEM_PROMPT


# Subtlety isn't really applicable for negative controls — they should be
# uniformly clean. We keep the three keys to share the snapshot/render
# infrastructure with confirm_existing/gap_probe; all three yield similar
# output, with "low" being the most explicitly clean and "high" being the
# most plausibly-borderline-clean.

CLEAN_TRIGGER = (
    "Emit a COMPLETELY clean UnitOfAssurance package. Every required field "
    "is populated correctly. Every CredibilityFactor is either 'assessed' "
    "with both `requiredLevel` and `achievedLevel` (and achievedLevel >= "
    "requiredLevel) AND `acceptanceCriteria` linked, OR 'scoped-out' / "
    "'not-applicable' WITH a documented rationale. Provenance chain is "
    "complete back to foundational evidence. ValidationResults all have "
    "`comparedAgainst`, `prov:wasGeneratedBy`, and `hasUncertaintyQuantification` "
    "links. The decision rationale is detailed and grounded in the structured "
    "evidence. NO weakener should fire on this package."
)


def _clean_subtlety(low, medium, high):
    out = {"low": low, "medium": medium, "high": high}
    validate_subtlety_examples(out)
    return out


def _nc_render(spec, context, *, description, task, subtlety):
    # Phase 2.5 v0.5.10/12.1: pre-LLM COU augmentation injects placeholder
    # hasApplicabilityConstraint + hasOperatingEnvelope. The post-LLM
    # mutation hook in generator.py (also added v0.5.12.1) is the safety
    # net for the LLM dropping these fields. CE / gap_probe / interaction
    # templates intentionally skip this so W-ON-02 confirm_existing
    # targets still trigger the rule.
    #
    # Phase 2.5 v0.5.13: prompt cleanup. The extra_schema_rules block is
    # rewritten to be DIRECTIVE rather than conditional. Phase A revealed
    # that the v0.5.12 conditional wording ("if Complete, include SA")
    # was misread by the LLM as license to switch to Minimal to avoid
    # emitting SA. The v0.5.13 wording requires substantive content from
    # the LLM directly; the post-LLM hooks remain as safety net for
    # non-compliant runs.
    from copy import deepcopy
    from uofa_cli.adversarial.skeleton import _augment_cou_with_envelope_stubs
    cou = context.get("context_of_use")
    if isinstance(cou, dict):
        cou = _augment_cou_with_envelope_stubs(deepcopy(cou))
    return BASE_SYSTEM_PROMPT, build_user_prompt(
        weakener="(negative_control)",
        weakener_description=description,
        defeater_type="negative_control — clean package",
        subtlety=spec.subtlety,
        subtlety_guidance=subtlety[spec.subtlety],
        base_cou_identity=context.get("identity"),
        context_of_use=cou,
        factor_scaffold=context.get("factor_scaffold", []),
        context_url=context.get("context_url", ""),
        decision=spec.decision,
        task=task,
        trigger_block=CLEAN_TRIGGER,
        extra_schema_rules=NC_SCHEMA_REQUIREMENTS,
    )


# Phase 2.5 v0.5.13 NC schema requirements — directive form replacing the
# v0.5.12 conditional wording. Each numbered requirement is a hard rule;
# violations cause spurious weakener firings (well-documented in
# v0_phase2v2_summary.md).
NC_SCHEMA_REQUIREMENTS = (
    "NC schema requirements (non-negotiable):\n"
    "\n"
    "1. CONFORMING PROFILE OVERRIDES base COU profile when the task says so.\n"
    "   The base COU's identity block is preserved verbatim EXCEPT for\n"
    "   `conformsToProfile`, which the per-archetype task instruction\n"
    "   may override (e.g. NC-1/3/4 require `uofa:ProfileComplete`).\n"
    "\n"
    "2. If `conformsToProfile` is `uofa:ProfileComplete`:\n"
    "   - Emit `hasSensitivityAnalysis` as an inline SensitivityAnalysis\n"
    "     object on the UofA with id, type, name, description (1-2\n"
    "     sentences of substantive content describing what was varied\n"
    "     and the response — NOT a placeholder stub).\n"
    "   - Emit `hasContextOfUse.hasOperatingEnvelope` as an inline\n"
    "     OperatingEnvelope with concrete bounds (e.g. flow rate ranges,\n"
    "     geometry tolerances). DO NOT emit a placeholder stub.\n"
    "   - Emit `hasContextOfUse.hasApplicabilityConstraint` as an inline\n"
    "     ApplicabilityConstraint object describing the in-scope domain.\n"
    "\n"
    "3. For every CredibilityFactor with `factorStatus: \"assessed\"`:\n"
    "   - BOTH `requiredLevel` AND `achievedLevel` MUST be present (1-5).\n"
    "   - `acceptanceCriteria` MUST be an inline AcceptanceCriteria\n"
    "     object (not just an IRI string).\n"
    "\n"
    "4. For factors with `factorStatus` of `\"scoped-out\"` or\n"
    "   `\"not-applicable\"`:\n"
    "   - DO NOT emit `requiredLevel` or `achievedLevel` — those imply\n"
    "     the factor was intended to be assessed.\n"
    "   - `rationale` MUST explain why the factor is scoped-out / N/A.\n"
    "\n"
    "5. If `hasDecisionRecord.outcome == \"Accepted\"` AND any factor\n"
    "   has `achievedLevel < requiredLevel`:\n"
    "   - `hasDecisionRecord.hasOffsetRationale` MUST be an inline\n"
    "     OffsetRationale referencing the shortfall factor and explaining\n"
    "     why the acceptance is justified despite the gap.\n"
)


# ----- per-NC content keyed by spec_id leaf -----

NC_CONFIGS = {
    "nc-clean-full-morrison-cou1": {
        "description": "NC-1 fully-assessed Morrison COU1 archetype",
        "task": (
            "generate a Complete-profile UofA. EMIT "
            "`conformsToProfile: 'https://uofa.net/vocab#ProfileComplete'` "
            "(override the base COU's profile if it differs — this NC "
            "tests the Complete-profile pathway). Cover all 13 V&V 40 "
            "factors as 'assessed' with consistent levels (requiredLevel "
            "<= achievedLevel for each), full provenance, UQ present, "
            "acceptance criteria documented per factor as inline "
            "AcceptanceCriteria objects, decision Accepted. INCLUDE inline "
            "`hasSensitivityAnalysis` (substantive content describing what "
            "was varied and the response — NOT a placeholder), "
            "`hasContextOfUse.hasApplicabilityConstraint`, and "
            "`hasContextOfUse.hasOperatingEnvelope` with concrete bounds."
        ),
        "subtlety": _clean_subtlety(
            "Heavy narrative emphasis on each factor's assessment.",
            "Standard narrative depth, all required structured fields populated.",
            "Concise narrative; relies on structured fields to carry the assessment.",
        ),
    },
    "nc-clean-minimal-morrison-cou1": {
        "description": "NC-2 Minimal-profile Morrison archetype",
        "task": (
            "generate a Minimal-profile UofA with just the required Minimal "
            "fields populated correctly. Profile-Minimal SHACL applies, "
            "Profile-Complete fields are not required."
        ),
        "subtlety": _clean_subtlety(
            "All Minimal fields populated, no extras.",
            "All Minimal fields populated plus a few clarifying optional fields.",
            "All Minimal fields populated plus extensive optional metadata.",
        ),
    },
    "nc-clean-full-morrison-cou2": {
        "description": "NC-3 fully-assessed Morrison COU2 archetype (MRL 5)",
        "task": (
            "generate a Complete-profile UofA at modelRiskLevel 5. EMIT "
            "`conformsToProfile: 'https://uofa.net/vocab#ProfileComplete'` "
            "(this NC tests the Complete-profile high-MRL pathway). "
            "All 13 factors are assessed at high rigor with both "
            "requiredLevel AND achievedLevel populated and inline "
            "AcceptanceCriteria objects per factor. Full UQ + INLINE "
            "`hasSensitivityAnalysis` SensitivityAnalysis object "
            "(method, dominant factors, sample size — substantive "
            "content). Decision Accepted with thorough rationale. "
            "Include `hasContextOfUse.hasApplicabilityConstraint` and "
            "`hasContextOfUse.hasOperatingEnvelope` with concrete bounds."
        ),
        "subtlety": _clean_subtlety(
            "Heavy structured field population; minimal narrative.",
            "Balanced structured + narrative.",
            "Rich narrative; structured fields fully populated.",
        ),
    },
    "nc-clean-full-nagaraja": {
        "description": "NC-4 fully-assessed Nagaraja COU1 archetype (orthopedic)",
        "task": (
            "generate a Complete-profile orthopedic-domain UofA at MRL 3. "
            "EMIT `conformsToProfile: 'https://uofa.net/vocab#ProfileComplete'` "
            "(this NC tests Complete-profile orthopedic pathway). "
            "Cover all 13 V&V 40 factors with appropriate rigor (both "
            "requiredLevel AND achievedLevel populated; inline "
            "AcceptanceCriteria per assessed factor). Use Nagaraja COU1 as "
            "the structural template. INCLUDE inline `hasSensitivityAnalysis` "
            "(substantive content), `hasContextOfUse.hasApplicabilityConstraint`, "
            "and `hasContextOfUse.hasOperatingEnvelope` with concrete bounds."
        ),
        "subtlety": _clean_subtlety(
            "Standard fully-assessed Nagaraja form.",
            "Variant base COU language; same factor coverage.",
            "Different orthopedic procedure narrative; same factor structure.",
        ),
    },
    "nc-clean-scoped-out-factors": {
        "description": "NC-5 factors marked scoped-out with rationale",
        "task": (
            "generate a UofA where a subset of factors are 'scoped-out' "
            "with documented rationale. Scoped-out factors MUST: "
            "(a) have `factorStatus: \"scoped-out\"`, "
            "(b) carry a thorough `rationale` field explaining the scoping "
            "decision, AND "
            "(c) NOT emit `requiredLevel` or `achievedLevel` (those imply "
            "intended-assessment, contradicting the scoped-out status). "
            "The remaining factors are 'assessed' with both levels and "
            "inline acceptanceCriteria."
        ),
        "subtlety": _clean_subtlety(
            "Two factors scoped-out, rationale paragraph each.",
            "Three factors scoped-out, brief rationale each.",
            "One factor scoped-out at a marginal call, with extensive rationale.",
        ),
    },
    "nc-clean-not-applicable-factors": {
        "description": "NC-6 factors marked not-applicable with rationale",
        "task": (
            "generate a UofA where a subset of factors are 'not-applicable' "
            "(e.g., NASA-only factors on a V&V 40 case). Not-applicable "
            "factors MUST: "
            "(a) have `factorStatus: \"not-applicable\"`, "
            "(b) carry a thorough `rationale` field explaining why the "
            "factor doesn't apply, AND "
            "(c) NOT emit `requiredLevel` or `achievedLevel` (those imply "
            "intended-assessment, contradicting the N/A status). "
            "The remaining factors are 'assessed' with both levels and "
            "inline acceptanceCriteria."
        ),
        "subtlety": _clean_subtlety(
            "Multiple factors not-applicable with explicit reasoning.",
            "Two factors not-applicable; brief rationale.",
            "One factor not-applicable at a borderline call, extensive rationale.",
        ),
    },
    "nc-clean-rejected-decision": {
        "description": "NC-7 valid Not-accepted decision",
        "task": (
            "generate a UofA whose decision is 'Not accepted' with "
            "documented rationale. The rejection is justified by EITHER:\n"
            "  (a) factors with `achievedLevel < requiredLevel` AND "
            "      `factorStatus: \"assessed\"` — rejection is the response "
            "      to the documented shortfall, no offset is being claimed; OR\n"
            "  (b) factors with `factorStatus: \"scoped-out\"` AND a "
            "      rationale explaining what was excluded — the rejection "
            "      cites the scoping decision.\n"
            "DO NOT use `factorStatus: \"not-assessed\"` at modelRiskLevel > 2. "
            "That fires W-EP-04 (correctly: an unassessed factor at elevated "
            "risk is a credibility gap, not a rejection rationale)."
        ),
        "subtlety": _clean_subtlety(
            "Multiple factors below required level; decision Not accepted with thorough rationale.",
            "One critical factor below required level; rejection rationale documents it.",
            "Borderline rejection — factors marginally below; rationale defends the threshold.",
        ),
    },
    "nc-clean-partial-envelope": {
        "description": "NC-8 explicit operating envelope with bounded applicability",
        "task": (
            "generate a UofA whose ContextOfUse declares both "
            "`hasApplicabilityConstraint` and `hasOperatingEnvelope` as "
            "INLINE objects (id, type, name, description) with concrete "
            "bounds (e.g., flow rates 1-7 L/min, geometry tolerances). "
            "The model and validation cover the declared envelope. This "
            "tests that bounded-applicability is correctly recognized as "
            "clean (no W-ON-02 firing). DO NOT emit narrative-only "
            "envelope mentions; the rule checks for the structured property."
        ),
        "subtlety": _clean_subtlety(
            "Tight envelope; validation covers it densely.",
            "Moderate envelope; validation covers boundary points.",
            "Wide envelope; validation samples sparse but honest about coverage gaps.",
        ),
    },
    "nc-clean-low-confidence-but-documented": {
        "description": "NC-9 low confidence honestly documented",
        "task": (
            "generate a UofA where evidence carries explicitly-low "
            "confidence scores or wide uncertainty bounds, but those are "
            "documented honestly with appropriate rationale (rather than "
            "covered up). The decision either accepts the limitation as "
            "residual risk OR rejects accordingly. If `conformsToProfile` "
            "is `uofa:ProfileComplete`, INCLUDE inline `hasSensitivityAnalysis` "
            "documenting which uncertain inputs drive the wide bounds."
        ),
        "subtlety": _clean_subtlety(
            "Evidence confidence ~50%; decision Not accepted with clear rationale.",
            "Evidence confidence borderline; decision Accepted with documented residual.",
            "Evidence confidence high but with one explicitly-flagged gap, fully justified.",
        ),
    },
    "nc-clean-compound-free": {
        "description": "NC-10 no Critical+High coexistence; no compound triggers",
        "task": (
            "generate a UofA that may have isolated weaknesses but NEVER a "
            "Critical and a High weakener on the same node simultaneously, "
            "and NEVER a declared assurance level inconsistent with the "
            "weakener profile. This tests that COMPOUND-01 / COMPOUND-03 "
            "do not over-fire."
        ),
        "subtlety": _clean_subtlety(
            "No weakeners at all; explicitly clean.",
            "One Medium weakener acknowledged; no Critical or High.",
            "One High weakener present; no Critical at the same node.",
        ),
    },
}


def render(spec, context: dict) -> tuple[str, str]:
    # spec_id is like 'adv-test-nc-clean-full-morrison-cou1'. Extract the
    # NC archetype suffix for dispatch.
    sid = spec.spec_id.lower()
    cfg = None
    matched_key = None
    for key in NC_CONFIGS:
        if sid.endswith(key) or key in sid:
            cfg = NC_CONFIGS[key]
            matched_key = key
            break
    if cfg is None:
        raise NotImplementedError(
            f"negative_controls does not handle spec_id {spec.spec_id!r}. "
            f"Known archetype keys: {sorted(NC_CONFIGS)}"
        )
    return _nc_render(
        spec, context,
        description=cfg["description"],
        task=cfg["task"],
        subtlety=cfg["subtlety"],
    )

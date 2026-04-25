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
    return BASE_SYSTEM_PROMPT, build_user_prompt(
        weakener="(negative_control)",
        weakener_description=description,
        defeater_type="negative_control — clean package",
        subtlety=spec.subtlety,
        subtlety_guidance=subtlety[spec.subtlety],
        base_cou_identity=context.get("identity"),
        context_of_use=context.get("context_of_use"),
        factor_scaffold=context.get("factor_scaffold", []),
        context_url=context.get("context_url", ""),
        decision=spec.decision,
        task=task,
        trigger_block=CLEAN_TRIGGER,
    )


# ----- per-NC content keyed by spec_id leaf -----

NC_CONFIGS = {
    "nc-clean-full-morrison-cou1": {
        "description": "NC-1 fully-assessed Morrison COU1 archetype",
        "task": (
            "generate a Complete-profile UofA covering all 13 V&V 40 factors "
            "as 'assessed' with consistent levels (requiredLevel <= "
            "achievedLevel for each), full provenance, UQ present, "
            "acceptance criteria documented per factor, decision Accepted."
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
            "generate a Complete-profile UofA at modelRiskLevel 5 with all "
            "13 factors assessed at high rigor, full UQ + sensitivity "
            "analysis linked, decision Accepted with thorough rationale."
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
            "generate a Complete-profile orthopedic-domain UofA at MRL 3 "
            "covering all 13 V&V 40 factors with appropriate rigor. Use "
            "Nagaraja COU1 as the structural template."
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
            "with documented rationale. The scoped-out factors carry a "
            "valid `factorStatus: \"scoped-out\"` AND a thorough "
            "rationale field; the remaining factors are 'assessed'."
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
            "(e.g., NASA-only factors on a V&V 40 case). All not-applicable "
            "factors carry a documented rationale."
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
            "documented rationale. This is a CLEAN negative example — the "
            "rejection is justified by the structured evidence (factors "
            "below required level, weaknesses acknowledged), so no rule "
            "should fire spuriously."
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
            "generate a UofA whose ContextOfUse declares both an "
            "`hasApplicabilityConstraint` and an `hasOperatingEnvelope` "
            "with concrete bounds. The model and validation cover the "
            "declared envelope. This tests that bounded-applicability is "
            "correctly recognized as clean (no W-ON-02 firing)."
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
            "residual risk OR rejects accordingly."
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

"""CLARISSA-machinery gap_probe templates (Phase 2 spec §7 rows 20-22).

Three sub-types from Varadarajan et al. 2024 (CLARISSA workflow):
eliminative-argumentation, residual-risk-justification, theory-preconditions.

§6.7 candidates: W-AR-06 (eliminative absent), W-AR-07 (residual-risk
unjustified), W-ON-03 Tier 2 (precondition unverified).

CRITICAL CONSTRAINT: per spec §8.2, generators MUST NOT emit the v0.6
reserved properties (uofa:residualRiskJustification, uofa:consideredAlternative,
uofa:knownLimitation). The CLARISSA gap_probes target the ABSENCE of these
properties as the defeater condition; the prompt enforces non-emission.
"""

from __future__ import annotations

from uofa_cli.adversarial.prompts.base import (
    BASE_SYSTEM_PROMPT,
    build_user_prompt,
    validate_subtlety_examples,
)

PROMPT_VERSION = "v1.0.0"

SYSTEM_PROMPT = BASE_SYSTEM_PROMPT


def _gp_subtlety(low, medium, high):
    out = {"low": low, "medium": medium, "high": high}
    validate_subtlety_examples(out)
    return out


def _gp_render(spec, context, *, description, task, trigger, subtlety):
    return BASE_SYSTEM_PROMPT, build_user_prompt(
        weakener=spec.source_taxonomy or "(gap_probe)",
        weakener_description=description,
        defeater_type=f"gap_probe — {spec.source_taxonomy}",
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


ELIMINATIVE_DESC = (
    "CLARISSA workflow 'Eliminative-Argumentation Absent' — the package's "
    "argument structure does not consider plausible alternative conclusions "
    "and rule them out (eliminative argumentation)"
)
ELIMINATIVE_TASK = (
    "generate a UnitOfAssurance where the decision rationale presents only "
    "the supportive argument and does not enumerate or refute alternative "
    "conclusions. The package narrative is one-sided — only why the claim "
    "holds, never why competing claims do not."
)
ELIMINATIVE_TRIGGER = (
    "Decision rationale supports the Accepted decision with positive "
    "evidence only. There is no structured `consideredAlternative` field "
    "(this property is RESERVED for v0.6 — DO NOT EMIT IT). The narrative "
    "does not mention any alternative conclusions or counter-considerations."
)
ELIMINATIVE_SUBTLETY = _gp_subtlety(
    "Rationale is one paragraph supporting Accepted; no alternatives discussed.",
    "Rationale acknowledges 'other interpretations exist' without naming them.",
    "Rationale enumerates risks but presents them as already-accepted residuals; no rejected alternative is documented.",
)


def _r_eliminative(spec, context):
    return _gp_render(spec, context, description=ELIMINATIVE_DESC, task=ELIMINATIVE_TASK,
                      trigger=ELIMINATIVE_TRIGGER, subtlety=ELIMINATIVE_SUBTLETY)


RESIDUAL_DESC = (
    "CLARISSA workflow 'Residual-Risk Unjustified' — the package "
    "acknowledges a known limitation but does not document why the residual "
    "risk is acceptable"
)
RESIDUAL_TASK = (
    "generate a UnitOfAssurance whose narrative or weakener annotations "
    "acknowledge a limitation, but no `residualRiskJustification` is "
    "documented (this v0.6 property is RESERVED — do not emit; instead "
    "use plain narrative to describe the limitation without justifying "
    "its residual risk)."
)
RESIDUAL_TRIGGER = (
    "ValidationResults narrative or factor `rationale` text describes a "
    "limitation (e.g., 'edge cases not fully covered'). The decision "
    "rationale is Accepted. NO `residualRiskJustification` field is "
    "emitted (per spec §8.2 reserved-property guard) and the narrative "
    "does not contain a paragraph explaining why the residual is "
    "acceptable for the COU."
)
RESIDUAL_SUBTLETY = _gp_subtlety(
    "Limitation flagged in narrative; decision is Accepted with no risk discussion.",
    "Limitation flagged; rationale waves at 'standard practice' as the residual-risk acceptance.",
    "Limitation flagged; rationale claims 'risk is acceptable' without explaining why.",
)


def _r_residual(spec, context):
    return _gp_render(spec, context, description=RESIDUAL_DESC, task=RESIDUAL_TASK,
                      trigger=RESIDUAL_TRIGGER, subtlety=RESIDUAL_SUBTLETY)


PRECONDITION_DESC = (
    "CLARISSA workflow 'Theory-Preconditions Unverified' — the assurance "
    "argument relies on a theoretical precondition (e.g., 'this method "
    "applies if assumption X holds') and the package does not verify "
    "that X holds for the COU"
)
PRECONDITION_TASK = (
    "generate a UnitOfAssurance whose model or method narrative cites a "
    "theoretical assumption (linearity, ergodicity, IID, etc.) and the "
    "package does not include a ValidationResult that checks whether the "
    "assumption holds for the COU."
)
PRECONDITION_TRIGGER = (
    "Model narrative references a theoretical precondition explicitly. No "
    "ValidationResult tests that precondition. ContextOfUse may operate in "
    "a regime where the assumption is questionable. AcceptanceCriteria do "
    "not address the assumption."
)
PRECONDITION_SUBTLETY = _gp_subtlety(
    "Assumption cited, no test of it at all.",
    "Assumption cited; narrative says 'assumption broadly applicable' without test.",
    "Assumption cited; one validation point happens to satisfy the assumption but the broader COU range may not.",
)


def _r_precondition(spec, context):
    return _gp_render(spec, context, description=PRECONDITION_DESC, task=PRECONDITION_TASK,
                      trigger=PRECONDITION_TRIGGER, subtlety=PRECONDITION_SUBTLETY)


_RENDERERS = {
    "eliminative-argumentation": _r_eliminative,
    "residual-risk-justification": _r_residual,
    "theory-preconditions": _r_precondition,
}


def render(spec, context: dict) -> tuple[str, str]:
    leaf = (spec.source_taxonomy or "").rsplit("/", 1)[-1]
    fn = _RENDERERS.get(leaf)
    if fn is None:
        raise NotImplementedError(
            f"clarissa_machinery does not handle {spec.source_taxonomy!r}"
        )
    return fn(spec, context)

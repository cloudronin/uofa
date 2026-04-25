"""Greenwell logical-fallacy gap_probe templates (Phase 2 spec §7 rows 17-19).

Three sub-types from Greenwell 2006 §3.3 Sufficiency:
hasty-inductive-generalization, arguing-from-ignorance, confusion-necessary-sufficient.

Per spec §6.7 these are W-SUF-01 (hasty), W-SUF-02 (arguing-from-ignorance)
candidates plus the necessary-sufficient confusion case. Expected outcome
class is COV-MISS — UofA does not currently have a sufficiency-fallacy rule.
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


HASTY_DESC = (
    "Greenwell sufficiency 'Hasty Inductive Generalization' — the package's "
    "decision generalizes from a small number of test cases to the full "
    "operating range without statistical justification"
)
HASTY_TASK = (
    "generate a UnitOfAssurance whose ValidationResults cover only a small "
    "number of test points (n = 1-3), and the rationale generalizes that "
    "performance to the full COU operating range without statistical "
    "argument."
)
HASTY_TRIGGER = (
    "ValidationResults narrative names a tiny sample (e.g., 'three "
    "experiments at the nominal operating point'). Decision rationale says "
    "'the model is validated for the full operating range' or similar "
    "broad claim."
)
HASTY_SUBTLETY = _gp_subtlety(
    "n=1 sample, decision rationale claims full-range validation.",
    "n=3 samples at one corner, decision rationale claims full-envelope coverage.",
    "n=5-10 samples spanning a narrow band; rationale extrapolates to a wider band without bounds.",
)


def _r_hasty(spec, context):
    return _gp_render(spec, context, description=HASTY_DESC, task=HASTY_TASK,
                      trigger=HASTY_TRIGGER, subtlety=HASTY_SUBTLETY)


IGNORANCE_DESC = (
    "Greenwell sufficiency 'Arguing from Ignorance' — the rationale argues a "
    "claim is true because no evidence has been found that it's false, "
    "without showing what was looked for"
)
IGNORANCE_TASK = (
    "generate a UnitOfAssurance whose decision rationale argues acceptance "
    "by absence of contradicting evidence ('no failures observed'), without "
    "documenting what kinds of failures were sought or what coverage the "
    "search achieved."
)
IGNORANCE_TRIGGER = (
    "Decision rationale uses absence-of-evidence language: 'no failure "
    "modes have been observed', 'no contraindications reported', 'we have "
    "not encountered any issues'. No structured field documents the failure "
    "mode catalog that was checked."
)
IGNORANCE_SUBTLETY = _gp_subtlety(
    "Decision rationale is exclusively 'no failures observed', no detail.",
    "Rationale lists failure modes considered but coverage of the catalog is incomplete.",
    "Rationale appears thorough; the coverage claim is implicit ('comprehensive screening').",
)


def _r_ignorance(spec, context):
    return _gp_render(spec, context, description=IGNORANCE_DESC, task=IGNORANCE_TASK,
                      trigger=IGNORANCE_TRIGGER, subtlety=IGNORANCE_SUBTLETY)


NS_DESC = (
    "Greenwell sufficiency 'Confusion of Necessary and Sufficient Conditions' — "
    "the package treats a necessary safety property as if it were sufficient "
    "for the COU's broader safety goal"
)
NS_TASK = (
    "generate a UnitOfAssurance whose decision argues a single necessary "
    "property as if it were sufficient (e.g., 'has a fault detector, "
    "therefore the system is safe')."
)
NS_TRIGGER = (
    "Decision rationale highlights ONE safety property (a fault detector, a "
    "redundancy, an alarm) and treats its presence as the sufficient "
    "condition for the COU goal. Other safety conditions are not addressed "
    "or are 'not-assessed' factors."
)
NS_SUBTLETY = _gp_subtlety(
    "Single property cited as the only safety argument.",
    "Two or three properties cited; decision rationale treats them as cumulatively sufficient without formal argument.",
    "Necessary properties documented in factors; rationale's logic implicitly equates the conjunction with sufficiency.",
)


def _r_ns(spec, context):
    return _gp_render(spec, context, description=NS_DESC, task=NS_TASK,
                      trigger=NS_TRIGGER, subtlety=NS_SUBTLETY)


_RENDERERS = {
    "hasty-inductive-generalization": _r_hasty,
    "arguing-from-ignorance": _r_ignorance,
    "confusion-necessary-sufficient": _r_ns,
}


def render(spec, context: dict) -> tuple[str, str]:
    leaf = (spec.source_taxonomy or "").rsplit("/", 1)[-1]
    fn = _RENDERERS.get(leaf)
    if fn is None:
        raise NotImplementedError(
            f"logical_fallacies does not handle {spec.source_taxonomy!r}"
        )
    return fn(spec, context)

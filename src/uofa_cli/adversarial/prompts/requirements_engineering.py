"""Gohar Requirements gap_probe templates (Phase 2 spec §7 rows 7-11).

Five sub-types from Gohar Table IV: missing, incorrect, ambiguous,
stale, inconsistent. Expected outcome class for most is COV-MISS;
'stale' may produce COV-WRONG via W-CON-03; 'incorrect' may COV-WRONG
via W-AR-01.
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


MISSING_DESC = (
    "Gohar Requirements 'Missing' — a safety-relevant requirement that "
    "should bind to the package's claim is not declared in the requirement "
    "set, leaving an obligation unstated"
)
MISSING_TASK = (
    "generate a UnitOfAssurance whose narrative discusses a safety property "
    "the system needs but the structured Requirement (linked from "
    "bindsRequirement) does not name that property among its obligations."
)
MISSING_TRIGGER = (
    "Narrative on ContextOfUse / Claim mentions an intended safety property "
    "(e.g., 'must operate at < 4 mm/s tip speed'). The Requirement's "
    "description omits that property — only some other requirements are listed."
)
MISSING_SUBTLETY = _gp_subtlety(
    "Critical property mentioned in narrative, not in any Requirement.",
    "Property mentioned in narrative; Requirement says 'other safety properties enumerated separately'.",
    "Property hinted at in narrative; Requirement covers a related but weaker bound.",
)


def _r_missing(spec, context):
    return _gp_render(spec, context, description=MISSING_DESC, task=MISSING_TASK,
                      trigger=MISSING_TRIGGER, subtlety=MISSING_SUBTLETY)


INCORRECT_DESC = (
    "Gohar Requirements 'Incorrect' — a Requirement is stated but its "
    "specified threshold or condition does not actually correspond to the "
    "physical safety boundary"
)
INCORRECT_TASK = (
    "generate a UnitOfAssurance where the Requirement specifies a numeric "
    "threshold that is wrong (too lenient or too strict for the physical "
    "regime the COU describes). Narrative does not flag the inconsistency."
)
INCORRECT_TRIGGER = (
    "Requirement carries `requirementText` (or similar) with a numeric bound. "
    "ContextOfUse / Claim narrative implies a different bound (more or less "
    "stringent). The mismatch is not addressed in any AcceptanceCriteria."
)
INCORRECT_SUBTLETY = _gp_subtlety(
    "Wrong by an order of magnitude.",
    "Wrong by 30-50%.",
    "Wrong by 10-15% — within rounding-error of plausible.",
)


def _r_incorrect(spec, context):
    return _gp_render(spec, context, description=INCORRECT_DESC, task=INCORRECT_TASK,
                      trigger=INCORRECT_TRIGGER, subtlety=INCORRECT_SUBTLETY)


AMBIGUOUS_DESC = (
    "Gohar Requirements 'Ambiguous' — the Requirement is stated but its "
    "wording admits multiple plausible interpretations, leaving compliance "
    "underspecified"
)
AMBIGUOUS_TASK = (
    "generate a UnitOfAssurance whose Requirement is written in language "
    "that supports multiple readings (e.g., 'minimal impact', 'reasonable "
    "performance')."
)
AMBIGUOUS_TRIGGER = (
    "Requirement narrative uses unquantified terms. AcceptanceCriteria links "
    "exist but their text is also vague. Reviewer cannot determine whether "
    "the package satisfies the Requirement from the structured fields alone."
)
AMBIGUOUS_SUBTLETY = _gp_subtlety(
    "Requirement is one sentence with no numbers ('the model shall be safe').",
    "Requirement uses 'industry standard' language without referencing a specific standard.",
    "Requirement uses precise-sounding terms whose meaning depends on a guideline that isn't cited.",
)


def _r_ambiguous(spec, context):
    return _gp_render(spec, context, description=AMBIGUOUS_DESC, task=AMBIGUOUS_TASK,
                      trigger=AMBIGUOUS_TRIGGER, subtlety=AMBIGUOUS_SUBTLETY)


STALE_DESC = (
    "Gohar Requirements 'Stale' — the Requirement reflects an older version "
    "of the standard or product baseline that has since been superseded; "
    "the package binds to it without flagging the staleness"
)
STALE_TASK = (
    "generate a UnitOfAssurance whose Requirement cites a standard version "
    "or revision that is older than the model's bindsModel / dataVintage. "
    "The narrative may not flag the staleness."
)
STALE_TRIGGER = (
    "Requirement cites a specific standard with a year/version (e.g., "
    "'ASME V&V 40-2018'). bindsModel narrative or `currentModelVersion` "
    "implies a later baseline (e.g., '2026-q1'). No update mechanism is "
    "documented."
)
STALE_SUBTLETY = _gp_subtlety(
    "Requirement cites a standard from 5+ years ago.",
    "Requirement cites a standard from 1-2 years ago that has since been revised.",
    "Requirement cites the latest revision but the underlying technical content has been updated by an addendum that is not referenced.",
)


def _r_stale(spec, context):
    return _gp_render(spec, context, description=STALE_DESC, task=STALE_TASK,
                      trigger=STALE_TRIGGER, subtlety=STALE_SUBTLETY)


INCONSISTENT_DESC = (
    "Gohar Requirements 'Inconsistent' — two requirements bound to the same "
    "claim contradict each other (one allows what the other forbids)"
)
INCONSISTENT_TASK = (
    "generate a UnitOfAssurance whose `bindsRequirement` references a "
    "Requirement that internally contradicts itself, OR the package binds "
    "two Requirements whose specifications are mutually exclusive."
)
INCONSISTENT_TRIGGER = (
    "Either: (a) Requirement narrative declares two thresholds that "
    "cannot both hold; or (b) the package emits multiple Requirement "
    "nodes (via additional fields) where one allows X and another forbids "
    "X."
)
INCONSISTENT_SUBTLETY = _gp_subtlety(
    "Direct contradiction (X must be true; X must not be true).",
    "Contradiction in different units (e.g., 'safe up to 80 mph' and 'must operate at 130 km/h').",
    "Contradiction emerges only when the requirements are read together with the COU's actual operating point.",
)


def _r_inconsistent(spec, context):
    return _gp_render(spec, context, description=INCONSISTENT_DESC, task=INCONSISTENT_TASK,
                      trigger=INCONSISTENT_TRIGGER, subtlety=INCONSISTENT_SUBTLETY)


_RENDERERS = {
    "missing": _r_missing,
    "incorrect": _r_incorrect,
    "ambiguous": _r_ambiguous,
    "stale": _r_stale,
    "inconsistent": _r_inconsistent,
}


def render(spec, context: dict) -> tuple[str, str]:
    leaf = (spec.source_taxonomy or "").rsplit("/", 1)[-1]
    fn = _RENDERERS.get(leaf)
    if fn is None:
        raise NotImplementedError(
            f"requirements_engineering does not handle "
            f"{spec.source_taxonomy!r}"
        )
    return fn(spec, context)

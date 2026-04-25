"""Compound weakeners — COMPOUND-01 (Critical+High coexistence) and
COMPOUND-03 (assurance level inconsistency).

These templates intentionally instantiate two or more Level-1 defeaters
on the same package so the COMPOUND rules cascade. Per spec §13.4 L1
(RESOLVED in v0.5.2), all weakener rules now evaluate in Jena and
COMPOUND-01 / -03 observe the full weakener graph.
"""

from __future__ import annotations

from uofa_cli.adversarial.prompts.base import (
    BASE_SYSTEM_PROMPT,
    build_user_prompt,
    validate_subtlety_examples,
)

PROMPT_VERSION = "v1.0.0"

SYSTEM_PROMPT = BASE_SYSTEM_PROMPT


# ----- COMPOUND-01: Critical + High coexist -----

COMPOUND_01_DESCRIPTION = (
    "compound risk escalation — the package has Critical-severity weakeners "
    "AND High-severity weakeners on the same UnitOfAssurance, so the "
    "compound rule emits one COMPOUND-01 annotation per (Critical, High) "
    "pair"
)
COMPOUND_01_TASK = (
    "generate a UnitOfAssurance package that triggers at least one "
    "Critical weakener AND at least one High weakener on the same UofA. "
    "Use W-EP-01 (orphan claim — Critical) and W-AL-01 (missing UQ — High) "
    "as the canonical pair."
)
COMPOUND_01_TRIGGER = (
    "Trigger BOTH conditions in the same package:\n"
    "(a) Critical: bindsClaim references a Claim that has NO "
    "`prov:wasDerivedFrom` (W-EP-01).\n"
    "(b) High: at least one ValidationResult has NO "
    "`hasUncertaintyQuantification` (W-AL-01).\n"
    "Both conditions must hold simultaneously. The COMPOUND-01 rule "
    "emits one annotation for each (Critical, High) pair detected."
)
COMPOUND_01_SUBTLETY = {
    "low": (
        "Both weaknesses are obvious. Multiple ValidationResults missing "
        "UQ, Claim with no provenance at all."
    ),
    "medium": (
        "Single weakener of each severity. Narrative addresses neither."
    ),
    "high": (
        "Single weakener of each severity, both deeply embedded in an "
        "otherwise full and well-narrated package. Reviewer must scan "
        "structured fields carefully to spot both."
    ),
}
validate_subtlety_examples(COMPOUND_01_SUBTLETY)


def _render_compound_01(spec, context):
    return BASE_SYSTEM_PROMPT, build_user_prompt(
        weakener=spec.target_weakener,
        weakener_description=COMPOUND_01_DESCRIPTION,
        defeater_type="Compound — Critical + High coexistence",
        subtlety=spec.subtlety,
        subtlety_guidance=COMPOUND_01_SUBTLETY[spec.subtlety],
        base_cou_identity=context.get("identity"),
        context_of_use=context.get("context_of_use"),
        factor_scaffold=context.get("factor_scaffold", []),
        context_url=context.get("context_url", ""),
        decision=spec.decision,
        task=COMPOUND_01_TASK,
        trigger_block=COMPOUND_01_TRIGGER,
    )


# ----- COMPOUND-03: assurance level inconsistency -----

COMPOUND_03_DESCRIPTION = (
    "assurance-level overstatement — the UofA declares "
    "`assuranceLevel: \"Medium\"` or \"High\" while at least one Critical "
    "weakener fires; the declared assurance level cannot be supported"
)
COMPOUND_03_TASK = (
    "generate a UnitOfAssurance with `assuranceLevel: \"High\"` "
    "(or \"Medium\") AND at least one Critical weakener (e.g., W-AR-01, "
    "W-AR-02, or W-EP-01). The declared assurance is inconsistent with the "
    "structural evidence."
)
COMPOUND_03_TRIGGER = (
    "Emit `assuranceLevel: \"High\"` (or \"Medium\") on the UofA. Then "
    "trigger one Critical weakener — the simplest is W-AR-02 "
    "(achievedLevel < requiredLevel with Accepted decision). The assurance "
    "level field plus the Critical weakener together fire COMPOUND-03."
)
COMPOUND_03_SUBTLETY = {
    "low": (
        "AssuranceLevel declared High; multiple obvious Critical weaknesses."
    ),
    "medium": (
        "AssuranceLevel declared Medium; one Critical weakness embedded "
        "without rationale."
    ),
    "high": (
        "AssuranceLevel declared Medium; single Critical weakness in a "
        "richly-narrated package. The declared level looks reasonable "
        "from prose alone."
    ),
}
validate_subtlety_examples(COMPOUND_03_SUBTLETY)


COMPOUND_03_EXTRA_SCHEMA_RULES = (
    "- `assuranceLevel`: top-level string on UnitOfAssurance, one of\n"
    "  \"Low\", \"Medium\", \"High\"."
)


def _render_compound_03(spec, context):
    return BASE_SYSTEM_PROMPT, build_user_prompt(
        weakener=spec.target_weakener,
        weakener_description=COMPOUND_03_DESCRIPTION,
        defeater_type="Compound — assurance level overstatement",
        subtlety=spec.subtlety,
        subtlety_guidance=COMPOUND_03_SUBTLETY[spec.subtlety],
        base_cou_identity=context.get("identity"),
        context_of_use=context.get("context_of_use"),
        factor_scaffold=context.get("factor_scaffold", []),
        context_url=context.get("context_url", ""),
        decision=spec.decision,
        task=COMPOUND_03_TASK,
        trigger_block=COMPOUND_03_TRIGGER,
        extra_schema_rules=COMPOUND_03_EXTRA_SCHEMA_RULES,
    )


_RENDERERS = {
    "COMPOUND-01": _render_compound_01,
    "COMPOUND-03": _render_compound_03,
}


def render(spec, context: dict) -> tuple[str, str]:
    fn = _RENDERERS.get(spec.target_weakener)
    if fn is None:
        raise NotImplementedError(
            f"compound does not handle {spec.target_weakener!r}"
        )
    return fn(spec, context)

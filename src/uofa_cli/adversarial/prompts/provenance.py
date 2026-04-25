"""Provenance-chain weakener — W-PROV-01.

W-PROV-01 [Critical] detects nodes reachable from the bindsClaim provenance
scope that have no upstream `prov:wasDerivedFrom` / `wasGeneratedBy` /
`used` edge AND are NOT marked `uofa:isFoundationalEvidence`. The
provenance chain terminates at a node that should not be a chain root.
"""

from __future__ import annotations

from uofa_cli.adversarial.prompts.base import (
    BASE_SYSTEM_PROMPT,
    build_user_prompt,
    validate_subtlety_examples,
)

PROMPT_VERSION = "v1.0.0"

SYSTEM_PROMPT = BASE_SYSTEM_PROMPT


W_PROV_01_DESCRIPTION = (
    "broken provenance chain root — a node reachable from the Claim's "
    "provenance scope has no upstream provenance edge and is not marked "
    "`uofa:isFoundationalEvidence: true`, so the chain dead-ends at "
    "non-foundational evidence"
)
W_PROV_01_TASK = (
    "generate a UnitOfAssurance package with a multi-hop provenance chain "
    "where at least one intermediate node has no `prov:wasDerivedFrom`, "
    "no `prov:wasGeneratedBy`, and no `prov:used` edge — and is NOT marked "
    "`uofa:isFoundationalEvidence: true`."
)
W_PROV_01_TRIGGER = (
    "Build a chain like Claim -> wasDerivedFrom -> ValidationResult -> "
    "wasGeneratedBy -> Activity -> used -> Dataset. Then introduce one "
    "intermediate node (e.g., a Result that links via wasDerivedFrom from "
    "the Claim) that has none of the upstream prov:* edges and does not "
    "carry `uofa:isFoundationalEvidence: true`. Other nodes in the chain "
    "may be foundational; only this one is the orphan."
)
W_PROV_01_SUBTLETY = {
    "low": (
        "The orphan node has no narrative around it — looks clearly "
        "incomplete."
    ),
    "medium": (
        "The orphan has a description that says 'derived from prior "
        "experimental work' without an IRI link. Reviewer might assume "
        "the link is implicit."
    ),
    "high": (
        "The orphan is described as 'a synthesis of multiple prior "
        "studies' with rich narrative. The reader assumes "
        "`isFoundationalEvidence: true` was just not encoded."
    ),
}
validate_subtlety_examples(W_PROV_01_SUBTLETY)


W_PROV_01_EXTRA_SCHEMA_RULES = (
    "- `uofa:isFoundationalEvidence`: boolean on Evidence nodes that mark\n"
    "  the legitimate roots of the provenance chain.\n"
    "- `prov:wasDerivedFrom`, `prov:wasGeneratedBy`, `prov:used`: IRI links\n"
    "  carrying provenance scope from claim toward foundational evidence."
)


def render(spec, context: dict) -> tuple[str, str]:
    return BASE_SYSTEM_PROMPT, build_user_prompt(
        weakener=spec.target_weakener,
        weakener_description=W_PROV_01_DESCRIPTION,
        defeater_type="Provenance — orphan chain node",
        subtlety=spec.subtlety,
        subtlety_guidance=W_PROV_01_SUBTLETY[spec.subtlety],
        base_cou_identity=context.get("identity"),
        context_of_use=context.get("context_of_use"),
        factor_scaffold=context.get("factor_scaffold", []),
        context_url=context.get("context_url", ""),
        decision=spec.decision,
        task=W_PROV_01_TASK,
        trigger_block=W_PROV_01_TRIGGER,
        extra_schema_rules=W_PROV_01_EXTRA_SCHEMA_RULES,
    )

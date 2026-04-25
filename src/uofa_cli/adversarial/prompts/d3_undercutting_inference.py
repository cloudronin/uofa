"""D3 undercutting prompts — hosts both W-AR-05 (Phase 1 baseline,
comparator absence/mismatch) and W-AR-03 (Phase 2 add, inference method
mismatch).

The W-AR-05 path remains module-level for snapshot-stability with Phase 1
fixtures. The W-AR-03 path uses the Phase 2 shared scaffolding from
``base.py``. The module-level :func:`render` dispatches by
``spec.target_weakener``.
"""

from __future__ import annotations

import json

from uofa_cli.adversarial.prompts.base import (
    BASE_SYSTEM_PROMPT,
    build_user_prompt,
    validate_subtlety_examples,
)

PROMPT_VERSION = "v1.1.0"

SYSTEM_PROMPT = """\
You generate synthetic simulation-credibility evidence in JSON-LD for ASME
V&V 40 analysis. Packages are used to test a weakener-detection system.

Requirements:
1. Structurally complete. All required fields populated.
2. Passes SHACL validation against the vv40 pack.
3. Contains exactly the targeted weakness described below.
4. Plausible on a quick read. The flaw must be subtle, not trivial.

Output ONLY the JSON-LD package as a single valid JSON object. No commentary.
No markdown fences. No trailing text. Close every brace.
"""

USER_PROMPT_TEMPLATE = """\
Target weakener: {weakener} ({weakener_description})
Defeater type: D3 — undercutting (inference method mismatch)
Subtlety level: {subtlety}

Base COU skeleton (preserve the identity block verbatim in the output):
{base_cou_identity_json}

Context of Use (copy verbatim as hasContextOfUse):
{context_of_use_json}

Factor scaffolding — for each stub, fill requiredLevel, achievedLevel,
factorStatus, acceptanceCriteria, rationale (leave factorType and
factorStandard unchanged):
{factor_scaffold_json}

Task: generate a UnitOfAssurance package for this COU where the Validation
factor contains a comparator that is technically present and well-documented,
but whose experimental conditions do not match the declared Context of Use.
Specifically:

{subtlety_guidance}

W-AR-05 TRIGGER (CRITICAL — do not skip):
Emit at least one hasValidationResult as an INLINE OBJECT that does NOT have
a `comparedAgainst` key. This is the rule-detection surface. Other validation
results MAY include `comparedAgainst`; at least one MUST NOT.

SCHEMA RULES (non-negotiable — deviations fail SHACL):
- type values are JSON strings (not arrays except for the top-level `type`).
- `requiredLevel` and `achievedLevel` are INTEGERS 1..5. Never strings like
  "Gradation 2". Emit `"requiredLevel": 2`, not `"requiredLevel": "Gradation 2"`.
- `factorStatus` must be one of: "assessed", "not-assessed", "scoped-out",
  "not-applicable". Never "Met", "Complete", "Passed", etc.
- `factorStandard` stays as "ASME-VV40-2018".
- `hasContextOfUse`, `hasDecisionRecord`: inline objects with `id` field.
- `hasValidationResult`: array of inline objects, each with `id` and `type`.
- `bindsRequirement`, `bindsModel`: IRI strings.
- `bindsDataset`: array of IRI strings.
- `hasWeakener`: empty array [].
- `generatedAtTime`: ISO-8601 string, e.g. "2026-04-19T00:00:00Z".
- `hash`: "sha256:" followed by exactly 64 lowercase hex chars.
- `signature`: "ed25519:" followed by lowercase hex chars.

Required top-level fields (emit EXACTLY these values):
  "@context": "{context_url}"
  "synthetic": true
  "type": ["UnitOfAssurance", "uofa:SyntheticAdversarialSample"]
  "conformsToProfile": "https://uofa.net/vocab#ProfileMinimal"

Required decision outcome: {decision}

Minimal skeleton to follow (fill in content, do NOT copy verbatim):
{{
  "@context": "{context_url}",
  "id": "https://uofa.net/synth/<unique-id>",
  "type": ["UnitOfAssurance", "uofa:SyntheticAdversarialSample"],
  "synthetic": true,
  "conformsToProfile": "https://uofa.net/vocab#ProfileMinimal",
  "name": "...",
  "description": "...",
  "bindsRequirement": "https://uofa.net/synth/req/...",
  "bindsClaim": "https://uofa.net/synth/claim/...",
  "bindsModel": "https://uofa.net/synth/model/...",
  "bindsDataset": ["https://uofa.net/synth/data/..."],
  "hasContextOfUse": {{ /* the object above, verbatim */ }},
  "hasValidationResult": [
    {{
      "id": "https://uofa.net/synth/validation/no-comparator",
      "type": "ValidationResult",
      "name": "...",
      "description": "Discusses a comparator by name but omits the link."
    }}
  ],
  "wasDerivedFrom": "https://doi.org/...",
  "wasAttributedTo": "https://uofa.net/synth/org/...",
  "generatedAtTime": "2026-04-19T00:00:00Z",
  "hash": "sha256:0000000000000000000000000000000000000000000000000000000000000000",
  "signature": "ed25519:0000000000000000000000000000000000000000000000000000000000000000",
  "hasCredibilityFactor": [ /* from scaffolding above, fill fields */ ],
  "hasWeakener": [],
  "hasDecisionRecord": {{
    "id": "https://uofa.net/synth/decision/...",
    "type": "DecisionRecord",
    "actor": "https://uofa.net/synth/actor/...",
    "role": "Credibility assessment team",
    "outcome": "{decision}",
    "rationale": "...",
    "decidedAt": "2026-04-19T00:00:00Z"
  }}
}}
"""

SUBTLETY_GUIDANCE = {
    "low": (
        "Make the comparator-COU mismatch obvious. For example, validate on a "
        "steady-state flow regime when the COU requires pulsatile flow, and "
        "state this mismatch explicitly in the validation narrative."
    ),
    "medium": (
        "Make the mismatch present but not highlighted. The comparator should "
        "be from a related but not identical operating condition. The "
        "validation narrative should not flag the difference."
    ),
    "high": (
        "Make the mismatch present but plausibly deniable. The comparator "
        "should be from a condition that overlaps with the COU on most "
        "parameters but differs on one parameter that matters for the "
        "question of interest. The validation narrative should discuss the "
        "comparator in positive terms without examining its applicability to "
        "this specific COU."
    ),
}

WEAKENER_DESCRIPTIONS = {
    "W-AR-05": (
        "comparator absence or mismatch — a validation result lacks a "
        "comparedAgainst link, or the comparator is inappropriate for the "
        "declared COU"
    ),
}


def _render_w_ar_05(spec, context: dict) -> tuple[str, str]:
    """Phase 1 W-AR-05 renderer (preserves snapshot byte-identity)."""
    identity = context.get("identity", {})
    context_of_use = context.get("context_of_use")
    factor_scaffold = context.get("factor_scaffold", [])
    context_url = context.get("context_url", "")

    user = USER_PROMPT_TEMPLATE.format(
        weakener=spec.target_weakener,
        weakener_description=WEAKENER_DESCRIPTIONS[spec.target_weakener],
        subtlety=spec.subtlety,
        base_cou_identity_json=json.dumps(identity, indent=2, sort_keys=True),
        context_of_use_json=json.dumps(context_of_use, indent=2, sort_keys=True)
        if context_of_use is not None
        else "null",
        factor_scaffold_json=json.dumps(factor_scaffold, indent=2, sort_keys=True),
        subtlety_guidance=SUBTLETY_GUIDANCE[spec.subtlety],
        decision=spec.decision,
        context_url=context_url,
    )
    return SYSTEM_PROMPT, user


# ----- Phase 2 W-AR-03 (inference method mismatch) -----

W_AR_03_DESCRIPTION = (
    "inference method mismatch — a Requirement specifies a particular "
    "verification method, but the supporting activity used a different "
    "activityType, breaking the inference link"
)

W_AR_03_TASK = (
    "generate a UnitOfAssurance package where a Requirement declares "
    "`requiredVerificationMethod: \"<method-A>\"` but at least one "
    "ValidationResult is generated by an Activity whose `activityType` "
    "is `\"<method-B>\"`. The package narrative should make the methods "
    "look complementary, but the structured fields disagree."
)

W_AR_03_TRIGGER = (
    "Emit a Requirement IRI on `bindsRequirement` whose Requirement node "
    "carries `requiredVerificationMethod`. Emit at least one ValidationResult "
    "with a `wasGeneratedBy` link to an Activity whose `activityType` is "
    "different from the requirement's required method (e.g., requirement "
    "wants 'experimental-validation', activity is 'simulation-only')."
)

W_AR_03_SUBTLETY_GUIDANCE = {
    "low": (
        "Make the method mismatch obvious. Required method is "
        "'experimental-validation'; activityType is 'literature-review'. "
        "The narrative does not even reference the required method."
    ),
    "medium": (
        "Required method is 'experimental-validation' and activityType is "
        "'numerical-simulation'. The narrative argues the simulation 'is "
        "as good as' an experiment without formally substituting it."
    ),
    "high": (
        "Required method is 'controlled-experiment' and activityType is "
        "'observational-study'. The narrative cites the activity at length "
        "and assumes the reader will not check whether 'observational' "
        "satisfies a 'controlled-experiment' requirement."
    ),
}

validate_subtlety_examples(W_AR_03_SUBTLETY_GUIDANCE)

W_AR_03_EXTRA_SCHEMA_RULES = (
    "- `bindsRequirement`: IRI of a Requirement node that carries\n"
    "  `requiredVerificationMethod: \"...\"`.\n"
    "- `wasGeneratedBy` on a ValidationResult: IRI of an Activity inline\n"
    "  object that carries `activityType: \"...\"`."
)


def _render_w_ar_03(spec, context: dict) -> tuple[str, str]:
    user = build_user_prompt(
        weakener=spec.target_weakener,
        weakener_description=W_AR_03_DESCRIPTION,
        defeater_type="D3 — undercutting (inference method mismatch)",
        subtlety=spec.subtlety,
        subtlety_guidance=W_AR_03_SUBTLETY_GUIDANCE[spec.subtlety],
        base_cou_identity=context.get("identity"),
        context_of_use=context.get("context_of_use"),
        factor_scaffold=context.get("factor_scaffold", []),
        context_url=context.get("context_url", ""),
        decision=spec.decision,
        task=W_AR_03_TASK,
        trigger_block=W_AR_03_TRIGGER,
        extra_schema_rules=W_AR_03_EXTRA_SCHEMA_RULES,
    )
    return BASE_SYSTEM_PROMPT, user


_RENDERERS = {
    "W-AR-03": _render_w_ar_03,
    "W-AR-05": _render_w_ar_05,
}


def render(spec, context: dict) -> tuple[str, str]:
    """Dispatch by ``spec.target_weakener``. Module hosts W-AR-03 + W-AR-05."""
    fn = _RENDERERS.get(spec.target_weakener)
    if fn is None:
        raise NotImplementedError(
            f"d3_undercutting_inference does not handle {spec.target_weakener!r}"
        )
    return fn(spec, context)

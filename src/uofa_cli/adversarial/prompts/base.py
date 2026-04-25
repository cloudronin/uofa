"""Shared scaffolding for Phase 2 adversarial prompt templates.

Phase 1 ships one module-level template (``d3_undercutting_inference.py`` —
W-AR-05). Phase 2 adds 22 confirm_existing + 23 gap_probe + 10 negative_control
+ 6 interaction templates following the same module-level pattern. This module
provides the shared utilities they reuse:

- ``RESERVED_PROPERTY_PREAMBLE`` — the v0.5 reserved-property guard required by
  Phase 2 Spec v1.7 §8.2. Every new template's system prompt MUST begin with
  this preamble (or include the constraint inline).
- ``apply_reserved_property_constraint(system_prompt)`` — convenience helper
  that prepends the preamble to a template's existing system prompt.
- ``validate_subtlety_examples(examples)`` — sanity check that a template's
  ``SUBTLETY_GUIDANCE`` / ``subtlety_examples`` mapping has exactly the three
  required keys.
- ``BASE_SYSTEM_PROMPT`` / ``SCHEMA_RULES`` / ``JSON_LD_SKELETON`` /
  ``build_user_prompt()`` — shared per-prompt scaffolding so each new
  template module only needs to provide the weakener-specific trigger
  paragraph + subtlety guidance + descriptions.

The original W-AR-05 module is intentionally left at its legacy form for
backwards-compatibility with existing snapshots; new templates in Phase 2
should use these utilities from the start.
"""

from __future__ import annotations

import json
from typing import Mapping

REQUIRED_SUBTLETY_KEYS: frozenset[str] = frozenset({"low", "medium", "high"})

#: Phase 2 Spec v1.7 §8.2 — generators MUST NOT emit these v0.6-reserved
#: properties in synthetic packages.
RESERVED_PROPERTY_PREAMBLE = """\
Do NOT include `uofa:residualRiskJustification`, `uofa:consideredAlternative`,
or `uofa:knownLimitation` in the generated package. These are reserved for
v0.6 rules and should not appear in v0.5-era test data.

"""


def apply_reserved_property_constraint(system_prompt: str) -> str:
    """Prepend the v0.5 reserved-property preamble to *system_prompt*.

    Idempotent: if the preamble is already present, returns the prompt unchanged.
    """
    if "uofa:residualRiskJustification" in system_prompt:
        return system_prompt
    return RESERVED_PROPERTY_PREAMBLE + system_prompt


def validate_subtlety_examples(examples: Mapping[str, str]) -> None:
    """Raise :class:`ValueError` if *examples* is missing any of the three
    required subtlety levels.
    """
    keys = set(examples.keys())
    if keys != REQUIRED_SUBTLETY_KEYS:
        missing = REQUIRED_SUBTLETY_KEYS - keys
        extra = keys - REQUIRED_SUBTLETY_KEYS
        msg = []
        if missing:
            msg.append(f"missing subtlety keys: {sorted(missing)}")
        if extra:
            msg.append(f"unexpected subtlety keys: {sorted(extra)}")
        raise ValueError("; ".join(msg))


# ----- Shared prompt scaffolding (Phase 2 §8.1) -----

#: Base system prompt body shared by all Phase 2 templates. Includes the
#: reserved-property preamble. Each template can append a one-line
#: weakener-specific orientation if needed but the body is identical.
BASE_SYSTEM_PROMPT = RESERVED_PROPERTY_PREAMBLE + """\
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

#: SHACL-derived schema rules shared by all confirm_existing templates.
#: New templates should NOT redefine these — append weakener-specific overrides
#: in the trigger section instead.
SCHEMA_RULES = """\
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
- `signature`: "ed25519:" followed by lowercase hex chars."""

#: Top-level field requirements shared by all templates.
REQUIRED_TOP_LEVEL_FIELDS = """\
Required top-level fields (emit EXACTLY these values):
  "@context": "{context_url}"
  "synthetic": true
  "type": ["UnitOfAssurance", "uofa:SyntheticAdversarialSample"]
  "conformsToProfile": "https://uofa.net/vocab#ProfileMinimal"

Required decision outcome: {decision}"""

#: Minimal JSON-LD skeleton emitted in every confirm_existing user prompt.
#: Templates can vary the validation-result inline objects to drive different
#: weakener triggers but the rest of the skeleton is shared.
JSON_LD_SKELETON = """\
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
      "id": "https://uofa.net/synth/validation/<id>",
      "type": "ValidationResult",
      "name": "..."
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


def build_user_prompt(
    *,
    weakener: str,
    weakener_description: str,
    defeater_type: str,
    subtlety: str,
    subtlety_guidance: str,
    base_cou_identity: dict | None,
    context_of_use: dict | None,
    factor_scaffold: list,
    context_url: str,
    decision: str,
    task: str,
    trigger_block: str,
    extra_schema_rules: str = "",
) -> str:
    """Assemble the full user prompt for a Phase 2 confirm_existing template.

    Per-template parts: ``weakener``, ``weakener_description``, ``task``,
    ``trigger_block``, ``subtlety_guidance``, optional ``extra_schema_rules``.
    Shared parts come from module-level constants.
    """
    schema_block = SCHEMA_RULES
    if extra_schema_rules:
        schema_block = schema_block + "\n" + extra_schema_rules

    return f"""Target weakener: {weakener} ({weakener_description})
Defeater type: {defeater_type}
Subtlety level: {subtlety}

Base COU skeleton (preserve the identity block verbatim in the output):
{json.dumps(base_cou_identity or {{}}, indent=2, sort_keys=True)}

Context of Use (copy verbatim as hasContextOfUse):
{json.dumps(context_of_use, indent=2, sort_keys=True) if context_of_use is not None else "null"}

Factor scaffolding — for each stub, fill requiredLevel, achievedLevel,
factorStatus, acceptanceCriteria, rationale (leave factorType and
factorStandard unchanged):
{json.dumps(factor_scaffold, indent=2, sort_keys=True)}

Task: {task}

{subtlety_guidance}

{weakener} TRIGGER (CRITICAL — do not skip):
{trigger_block}

SCHEMA RULES (non-negotiable — deviations fail SHACL):
{schema_block}

{REQUIRED_TOP_LEVEL_FIELDS.format(context_url=context_url, decision=decision)}

{JSON_LD_SKELETON.format(context_url=context_url, decision=decision)}"""

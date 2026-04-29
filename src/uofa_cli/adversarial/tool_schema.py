"""Anthropic tool-use schema for UofA package generation (Phase 2 v3 v0.5.15).

Replaces the free-form JSON-LD skeleton + schema-rules text in the prompt
with a structured tool definition. The LLM submits its package by calling
the ``submit_uofa_package`` tool with input matching this schema.

Benefits over free-form generation:

* Anthropic's API parses the tool ``input`` field and returns it as a
  Python dict — eliminates malformed JSON failures (~5% pre-v0.5.15).
* Schema constraints (enum values, integer ranges, required fields,
  pattern matches) are enforced at the SDK boundary.
* The LLM cannot omit required fields; the call would fail before
  reaching our code.

What this schema does NOT enforce (still SHACL-validated post-tool-call):

* Profile dispatch (Minimal vs Complete required-field sets)
* Cross-field consistency (e.g., decision outcome matches factor levels)
* IRI uniqueness / referential integrity
* Substantive content quality (placeholder vs real content)

Those remain the SHACL retry loop's job.
"""

from __future__ import annotations


# Mirrors v0.5.13 SCHEMA_RULES and JSON_LD_SKELETON in
# src/uofa_cli/adversarial/prompts/base.py. When updating one, update
# both — the skeleton text in base.py is for free-form fallback and
# documentation; this schema is the structural contract.
# Note: ``@context`` is intentionally OMITTED from this schema. Anthropic's
# tool-input-schema validator rejects property keys that don't match the
# regex ^[a-zA-Z0-9_.-]{1,64}$, which excludes @-prefixed JSON-LD keys.
# The system prompt + REQUIRED_TOP_LEVEL_FIELDS still instructs the LLM
# to emit ``@context``; if the LLM omits it, the generator's
# ``_inject_provenance`` step adds it from the spec's context_url. The
# resulting JSON-LD package is structurally identical to the free-form
# generation path.
UOFA_PACKAGE_SCHEMA: dict = {
    "type": "object",
    "additionalProperties": True,  # allow archetype-specific extras + JSON-LD @-prefixed keys
    "required": [
        "id",
        "type",
        "synthetic",
        "conformsToProfile",
        "bindsRequirement",
        "bindsClaim",
        "bindsModel",
        "bindsDataset",
        "hasContextOfUse",
        "hasValidationResult",
        "wasDerivedFrom",
        "wasAttributedTo",
        "generatedAtTime",
        "hash",
        "signature",
        "hasCredibilityFactor",
        "hasWeakener",
        "hasDecisionRecord",
    ],
    "properties": {
        "id": {
            "type": "string",
            "description": "Unique IRI for this UofA package, e.g. https://uofa.net/synth/<id>.",
        },
        "type": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Must include 'UnitOfAssurance' and 'uofa:SyntheticAdversarialSample'.",
            "minItems": 2,
        },
        "synthetic": {
            "type": "boolean",
            "const": True,
            "description": "Marks the package as a synthetic adversarial sample.",
        },
        "conformsToProfile": {
            "type": "string",
            "enum": [
                "https://uofa.net/vocab#ProfileMinimal",
                "https://uofa.net/vocab#ProfileComplete",
                "uofa:ProfileMinimal",
                "uofa:ProfileComplete",
            ],
            "description": "Profile dispatch — Minimal or Complete (full IRI or curie).",
        },
        "name": {"type": "string"},
        "description": {"type": "string"},
        "couName": {"type": "string"},
        "deviceClass": {"type": "string"},
        "modelRiskLevel": {"type": "integer", "minimum": 1, "maximum": 5},
        "assuranceLevel": {"type": "string", "enum": ["Low", "Medium", "High"]},
        "decision": {"type": "string"},
        "bindsRequirement": {
            "type": "string",
            "description": "IRI of the requirement.",
        },
        "bindsClaim": {
            "type": "string",
            "description": "IRI of the claim.",
        },
        "bindsModel": {
            "type": "string",
            "description": "IRI of the model.",
        },
        "bindsDataset": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Array of IRI strings (datasets).",
        },
        "hasContextOfUse": {
            "type": "object",
            "required": ["id", "type"],
            "additionalProperties": True,
            "properties": {
                "id": {"type": "string"},
                "type": {"type": "string", "const": "ContextOfUse"},
                "name": {"type": "string"},
                "description": {"type": "string"},
                "deviceClass": {"type": "string"},
                "modelInfluence": {"type": "string"},
                "decisionConsequence": {"type": "string"},
                "hasApplicabilityConstraint": {
                    "type": "object",
                    "additionalProperties": True,
                    "properties": {
                        "id": {"type": "string"},
                        "type": {"type": "string", "const": "ApplicabilityConstraint"},
                        "name": {"type": "string"},
                        "description": {"type": "string"},
                    },
                },
                "hasOperatingEnvelope": {
                    "type": "object",
                    "additionalProperties": True,
                    "properties": {
                        "id": {"type": "string"},
                        "type": {"type": "string", "const": "OperatingEnvelope"},
                        "name": {"type": "string"},
                        "description": {"type": "string"},
                    },
                },
            },
        },
        "hasValidationResult": {
            "type": "array",
            "minItems": 0,
            "items": {
                "type": "object",
                "required": ["id", "type"],
                "additionalProperties": True,
                "properties": {
                    "id": {"type": "string"},
                    "type": {"type": "string", "const": "ValidationResult"},
                    "name": {"type": "string"},
                },
            },
        },
        "hasSensitivityAnalysis": {
            "type": "boolean",
            "description": (
                "Boolean flag indicating that a documented sensitivity "
                "analysis is part of the assurance package (xsd:boolean "
                "per v0.5 schema, mirrors hasUncertaintyQuantification)."
            ),
        },
        "wasDerivedFrom": {"type": "string"},
        "wasAttributedTo": {"type": "string"},
        "generatedAtTime": {
            "type": "string",
            "description": "ISO-8601 timestamp, e.g. 2026-04-19T00:00:00Z.",
        },
        "hash": {
            "type": "string",
            "pattern": "^sha256:[0-9a-f]{64}$",
            "description": "sha256: prefix + 64 lowercase hex chars.",
        },
        "signature": {
            "type": "string",
            "pattern": "^ed25519:[0-9a-f]+$",
            "description": "ed25519: prefix + lowercase hex chars.",
        },
        "hasCredibilityFactor": {
            "type": "array",
            "minItems": 0,
            "items": {
                "type": "object",
                "required": ["type", "factorType"],
                "additionalProperties": True,
                "properties": {
                    "id": {"type": "string"},
                    "type": {"type": "string", "const": "CredibilityFactor"},
                    "factorType": {"type": "string"},
                    "factorStandard": {"type": "string"},
                    "factorStatus": {
                        "type": "string",
                        "enum": ["assessed", "not-assessed", "scoped-out", "not-applicable"],
                    },
                    "requiredLevel": {"type": "integer", "minimum": 1, "maximum": 5},
                    "achievedLevel": {"type": "integer", "minimum": 1, "maximum": 5},
                    "acceptanceCriteria": {
                        "oneOf": [
                            {"type": "string"},  # IRI form
                            {  # inline AcceptanceCriteria object
                                "type": "object",
                                "additionalProperties": True,
                                "properties": {
                                    "id": {"type": "string"},
                                    "type": {"type": "string", "const": "AcceptanceCriteria"},
                                    "name": {"type": "string"},
                                    "description": {"type": "string"},
                                },
                            },
                        ]
                    },
                    "rationale": {"type": "string"},
                },
            },
        },
        "hasWeakener": {
            "type": "array",
            "description": "Empty array for synthetic samples; weakeners are derived by Jena rules.",
        },
        "hasDecisionRecord": {
            "type": "object",
            "required": ["id", "type", "outcome"],
            "additionalProperties": True,
            "properties": {
                "id": {"type": "string"},
                "type": {"type": "string", "const": "DecisionRecord"},
                "actor": {"type": "string"},
                "role": {"type": "string"},
                "outcome": {"type": "string"},
                "rationale": {"type": "string"},
                "decidedAt": {"type": "string"},
                "hasOffsetRationale": {
                    "oneOf": [
                        {"type": "object", "additionalProperties": True},
                        {"type": "array", "items": {"type": "object"}},
                    ]
                },
            },
        },
    },
}


_TOOL_DESCRIPTION = (
    "Submit a generated UofA (Unit of Assurance) JSON-LD package. "
    "The package must conform to the UofA v0.5 schema with all "
    "required fields populated. Synthetic adversarial samples carry "
    "the 'synthetic: true' flag and 'uofa:SyntheticAdversarialSample' "
    "type. Hash and signature are LLM-generated placeholders for "
    "synthetic samples (real packages are signed post-generation by "
    "the catalog tooling)."
)


# OpenAI-style tool definition (litellm normalizes to Anthropic's format
# when calling claude-* models). Pass as `tools=[UOFA_TOOL]`.
UOFA_TOOL: dict = {
    "type": "function",
    "function": {
        "name": "submit_uofa_package",
        "description": _TOOL_DESCRIPTION,
        "parameters": UOFA_PACKAGE_SCHEMA,
    },
}


# OpenAI-style tool_choice that forces the model to call our tool.
# Pass as `tool_choice=UOFA_TOOL_CHOICE`.
UOFA_TOOL_CHOICE: dict = {
    "type": "function",
    "function": {"name": "submit_uofa_package"},
}


# Anthropic-native tool definition (alternative form for direct
# Anthropic SDK use; not used by litellm).
UOFA_TOOL_ANTHROPIC: dict = {
    "name": "submit_uofa_package",
    "description": _TOOL_DESCRIPTION,
    "input_schema": UOFA_PACKAGE_SCHEMA,
}

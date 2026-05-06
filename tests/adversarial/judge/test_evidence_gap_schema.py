"""Tests for productive-OOS evidence_gap schema enforcement (Phase 3 v1.6 Delta 1+2).

Validates that:
- judge_output_schema.json requires evidence_gap when verdict==OUT-OF-SCOPE (if/then)
- judge_output_schema.json accepts evidence_gap=null for non-OOS verdicts
- judge_e_output_schema.json carries the same conditional + arbitration_basis
- The Anthropic schema-strip helper correctly drops `if/then/else` so the
  call payload is Anthropic-strict-mode compatible (R12)
"""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

from uofa_cli.adversarial.judge.providers.capabilities import (
    strip_schema_for_provider,
)


def _repo_root() -> Path:
    # Walk up from this file to find the repo root.
    return Path(__file__).resolve().parents[3]


def _load(name: str) -> dict:
    return json.loads((_repo_root() / "specs" / name).read_text())


def _base_oos_payload(**overrides) -> dict:
    """A minimal OOS judgment that satisfies the schema except evidence_gap."""
    payload = {
        "case_id": "cal-021-_-stub",  # anonymized
        "verdict": "OUT-OF-SCOPE",
        "confidence": 0.78,
        "reasoning_steps": {
            "source_taxonomy_identified": "oos/clinical-judgment-arbitration",
            "target_rule_identified": "(none)",
            "rule_firings_inspected": "baseline rules fired",
            "instantiation_check": "package is structurally complete; OOS rationale documented",
            "verdict_commitment": "OUT-OF-SCOPE",
        },
        "reasoning": "x" * 80,
        "section_6_7_candidate": None,
        "alternative_rule_analysis": None,
        "prompt_template_version": "v1.1.0",
        "judge_model": "claude-sonnet-4-6",
        "judge_thinking_enabled": True,
        "judge_model_params": {"temperature": 0.0, "seed": 42},
        "generator_provenance": {
            "generator_model": "anthropic/claude-sonnet-4-6",
            "temperature": None,
            "seed": None,
        },
        "evidence_gap": {
            "missing_evidence_type": "structured comparison studies for model-form selection",
            "would_support_defeater_evaluation": "model-form adequacy evaluation",
        },
    }
    payload.update(overrides)
    return payload


# ── Delta 1: judge_output_schema OOS conditional-required ──────────────


class TestProductionSchemaConditional:
    def test_oos_with_evidence_gap_validates(self) -> None:
        schema = _load("judge_output_schema.json")
        payload = _base_oos_payload()
        jsonschema.validate(payload, schema)  # no exception

    def test_oos_with_null_evidence_gap_rejected(self) -> None:
        schema = _load("judge_output_schema.json")
        payload = _base_oos_payload(evidence_gap=None)
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(payload, schema)

    def test_non_oos_with_null_evidence_gap_validates(self) -> None:
        schema = _load("judge_output_schema.json")
        payload = _base_oos_payload(
            verdict="CORRECT-DETECTION",
            reasoning_steps={
                "source_taxonomy_identified": "test/taxonomy/sub-type",
                "target_rule_identified": "W-AR-01",
                "rule_firings_inspected": "W-AR-01 fired as expected",
                "instantiation_check": "package legitimately instantiates the target",
                "verdict_commitment": "CORRECT-DETECTION",
            },
            evidence_gap=None,
        )
        jsonschema.validate(payload, schema)  # no exception

    def test_evidence_gap_missing_required_subfield_rejected(self) -> None:
        schema = _load("judge_output_schema.json")
        payload = _base_oos_payload(
            evidence_gap={"missing_evidence_type": "x" * 30},  # missing the second subfield
        )
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(payload, schema)


# ── Delta 2: judge_e_output_schema (arbitration extends Delta 1) ───────


class TestArbitrationSchemaConditional:
    def _base_arbitration_payload(self, **overrides) -> dict:
        payload = _base_oos_payload()
        payload.update({
            "judge_model": "mistral-large-2",
            "arbitration_basis": "package_content",
            "production_judge_evaluation": {
                "judge_a_reasoning_assessment": "sound",
                "judge_b_reasoning_assessment": "weak",
                "judge_c_reasoning_assessment": "weak",
            },
            "judge_role": "arbiter",
        })
        payload.update(overrides)
        return payload

    def test_arbiter_oos_with_evidence_gap_validates(self) -> None:
        schema = _load("judge_e_output_schema.json")
        payload = self._base_arbitration_payload()
        jsonschema.validate(payload, schema)

    def test_arbiter_oos_without_evidence_gap_rejected(self) -> None:
        schema = _load("judge_e_output_schema.json")
        payload = self._base_arbitration_payload(evidence_gap=None)
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(payload, schema)

    def test_arbiter_judge_role_must_be_arbiter(self) -> None:
        schema = _load("judge_e_output_schema.json")
        payload = self._base_arbitration_payload(judge_role="production")
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(payload, schema)

    def test_arbitration_basis_enum_enforced(self) -> None:
        schema = _load("judge_e_output_schema.json")
        payload = self._base_arbitration_payload(arbitration_basis="vibes")
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(payload, schema)


# ── R12: Anthropic strict-mode rejects if/then; strip helper handles it ─


class TestAnthropicSchemaStrip:
    def test_anthropic_strip_drops_if_then_else(self) -> None:
        schema = _load("judge_output_schema.json")
        # Schema has top-level if/then for the OOS conditional.
        assert "if" in schema and "then" in schema
        stripped = strip_schema_for_provider(schema, "anthropic")
        # Anthropic strict-mode rejects these — strip ensures they're gone.
        assert "if" not in stripped
        assert "then" not in stripped

    def test_runtime_validation_uses_full_schema_not_stripped(self) -> None:
        """The post-call parser MUST validate against the full schema.

        Otherwise OOS verdicts would slip through without evidence_gap.
        Smoke check: ensure the strip function doesn't mutate the input
        (i.e., the original schema retains if/then for runtime use).
        """
        schema = _load("judge_output_schema.json")
        _ = strip_schema_for_provider(schema, "anthropic")
        # Original schema should still have if/then.
        assert "if" in schema
        assert "then" in schema

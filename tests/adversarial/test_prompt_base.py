"""Tests for the shared prompt-template scaffolding (Phase 2 §8.1)."""

from __future__ import annotations

import pytest

from uofa_cli.adversarial.prompts.base import (
    REQUIRED_SUBTLETY_KEYS,
    RESERVED_PROPERTY_PREAMBLE,
    apply_reserved_property_constraint,
    validate_subtlety_examples,
)


def test_required_subtlety_keys_exact():
    assert REQUIRED_SUBTLETY_KEYS == frozenset({"low", "medium", "high"})


def test_reserved_property_preamble_mentions_all_three_properties():
    """The v0.5 reserved-property preamble must list all three reserved IRIs
    so the LLM cannot mis-trigger v0.6 rule placeholders.
    """
    assert "uofa:residualRiskJustification" in RESERVED_PROPERTY_PREAMBLE
    assert "uofa:consideredAlternative" in RESERVED_PROPERTY_PREAMBLE
    assert "uofa:knownLimitation" in RESERVED_PROPERTY_PREAMBLE


def test_apply_reserved_property_constraint_prepends_preamble():
    base_prompt = "You generate synthetic packages.\n"
    out = apply_reserved_property_constraint(base_prompt)
    assert out.startswith(RESERVED_PROPERTY_PREAMBLE)
    assert out.endswith(base_prompt)


def test_apply_reserved_property_constraint_is_idempotent():
    base_prompt = "You generate synthetic packages.\n"
    once = apply_reserved_property_constraint(base_prompt)
    twice = apply_reserved_property_constraint(once)
    assert once == twice


def test_validate_subtlety_examples_accepts_correct_keys():
    validate_subtlety_examples({"low": "...", "medium": "...", "high": "..."})


def test_validate_subtlety_examples_rejects_missing_key():
    with pytest.raises(ValueError, match="missing subtlety keys"):
        validate_subtlety_examples({"low": "...", "medium": "..."})


def test_validate_subtlety_examples_rejects_extra_key():
    with pytest.raises(ValueError, match="unexpected subtlety keys"):
        validate_subtlety_examples(
            {"low": "...", "medium": "...", "high": "...", "extreme": "..."}
        )

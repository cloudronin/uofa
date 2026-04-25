"""Spec loader tests — §11.1 of the adversarial spec.

Phase 2 additions: source_taxonomy field validation per Phase 2 Spec v1.7 §5.2.
"""

from __future__ import annotations

import pytest

from uofa_cli.adversarial.spec_loader import (
    AdversarialSpec,
    SourceTaxonomyError,
    SpecValidationError,
    default_taxonomy_for_pattern,
    load_spec,
    resolve_taxonomy_path,
)


def test_valid_spec_parses(valid_spec_path):
    spec = load_spec(valid_spec_path)
    assert isinstance(spec, AdversarialSpec)
    assert spec.spec_id == "adv-test-w-ar-05"
    assert spec.target_weakener == "W-AR-05"
    assert spec.defeater_type == "D3"
    assert spec.coverage_intent == "confirm_existing"
    assert spec.pack == "vv40"
    assert spec.mode == "skeleton"
    assert spec.base_cou is not None
    assert spec.base_cou.exists()
    assert spec.n_variants == 3
    assert spec.subtlety == "high"
    # CamelCase/sentence-case factors should normalize to the VV40 canonical list.
    assert "Model form" in spec.factors


def test_missing_spec_id_rejected(tmp_path, valid_spec_path):
    bad = tmp_path / "no_spec_id.yaml"
    text = valid_spec_path.read_text().replace("spec_id: adv-test-w-ar-05\n", "")
    bad.write_text(text)
    with pytest.raises(SpecValidationError, match="spec_id"):
        load_spec(bad)


def test_invalid_spec_id_rejected(tmp_path, valid_spec_path):
    bad = tmp_path / "bad_spec_id.yaml"
    text = valid_spec_path.read_text().replace(
        "spec_id: adv-test-w-ar-05", "spec_id: INVALID_UPPERCASE"
    )
    bad.write_text(text)
    with pytest.raises(SpecValidationError, match="spec_id"):
        load_spec(bad)


def test_invalid_defeater_type_rejected(tmp_path, valid_spec_path):
    bad = tmp_path / "bad_defeater.yaml"
    text = valid_spec_path.read_text().replace("defeater_type: D3", "defeater_type: D9")
    bad.write_text(text)
    with pytest.raises(SpecValidationError, match="defeater_type"):
        load_spec(bad)


def test_unknown_weakener_rejected(bad_weakener_spec_path):
    with pytest.raises(SpecValidationError, match="W-XX-99"):
        load_spec(bad_weakener_spec_path)


def test_unknown_factor_for_pack_rejected(bad_factor_spec_path):
    with pytest.raises(SpecValidationError, match="ThisFactorDoesNotExist"):
        load_spec(bad_factor_spec_path)


def test_skeleton_mode_requires_base_cou(bad_mode_spec_path):
    with pytest.raises(SpecValidationError, match="base_cou"):
        load_spec(bad_mode_spec_path)


def test_spec_hash_deterministic(valid_spec_path):
    a = load_spec(valid_spec_path)
    b = load_spec(valid_spec_path)
    assert a.spec_hash == b.spec_hash
    assert len(a.spec_hash) == 64  # SHA-256 hex


def test_factor_names_normalize_camelcase(tmp_path, valid_spec_path):
    text = valid_spec_path.read_text()
    text = text.replace("- Model form", "- ModelForm")
    out = tmp_path / "camel.yaml"
    out.write_text(text)
    spec = load_spec(out)
    assert "Model form" in spec.factors


# ---- Phase 2: source_taxonomy validation (spec §5.2) ---- #


def test_confirm_existing_default_taxonomy_populated(valid_spec_path):
    """When source_taxonomy is omitted on confirm_existing, default attribution applies."""
    spec = load_spec(valid_spec_path)
    assert spec.coverage_intent == "confirm_existing"
    assert spec.source_taxonomy == (
        "jarzebowicz-wardzinski/argument_defeaters/D5-undercutting-comparator"
    )


def test_confirm_existing_explicit_taxonomy_preserved(
    confirm_existing_explicit_taxonomy_spec_path,
):
    spec = load_spec(confirm_existing_explicit_taxonomy_spec_path)
    assert spec.source_taxonomy == (
        "jarzebowicz-wardzinski/argument_defeaters/D3-undercutting"
    )


def test_gap_probe_valid_taxonomy_loads(gap_probe_valid_spec_path):
    spec = load_spec(gap_probe_valid_spec_path)
    assert spec.coverage_intent == "gap_probe"
    assert spec.source_taxonomy == "gohar/evidence_validity/data-drift"


def test_gap_probe_missing_taxonomy_rejected(gap_probe_missing_taxonomy_spec_path):
    with pytest.raises(SourceTaxonomyError, match="required for coverage_intent=gap_probe"):
        load_spec(gap_probe_missing_taxonomy_spec_path)


def test_gap_probe_unresolved_taxonomy_rejected(gap_probe_unresolved_taxonomy_spec_path):
    with pytest.raises(SourceTaxonomyError, match="does not resolve"):
        load_spec(gap_probe_unresolved_taxonomy_spec_path)


def test_negative_control_valid_sentinel(negative_control_valid_spec_path):
    spec = load_spec(negative_control_valid_spec_path)
    assert spec.coverage_intent == "negative_control"
    assert spec.source_taxonomy == "control/none"


def test_negative_control_non_sentinel_rejected(negative_control_bad_taxonomy_spec_path):
    with pytest.raises(SourceTaxonomyError, match="control/none"):
        load_spec(negative_control_bad_taxonomy_spec_path)


def test_source_taxonomy_error_inherits_from_spec_validation_error():
    """SourceTaxonomyError must be a SpecValidationError subclass so generic
    spec-validation handlers continue to catch it.
    """
    assert issubclass(SourceTaxonomyError, SpecValidationError)


def test_resolve_taxonomy_path_three_levels():
    """Path resolver handles three-level identifiers (taxonomy/category/subtype)."""
    assert resolve_taxonomy_path("gohar/requirements/missing")
    assert not resolve_taxonomy_path("gohar/requirements/this-does-not-exist")
    assert not resolve_taxonomy_path("nonexistent-taxonomy/foo/bar")


def test_resolve_taxonomy_path_four_levels():
    """Path resolver handles nested logical_fallacies sub-categories."""
    assert resolve_taxonomy_path("gohar/logical_fallacies/relevance/red-herring")
    assert not resolve_taxonomy_path("gohar/logical_fallacies/relevance/no-such-fallacy")


def test_default_attribution_lookup():
    """Default attribution table provides a source_taxonomy for every shipped pattern."""
    assert default_taxonomy_for_pattern("W-AR-05") == (
        "jarzebowicz-wardzinski/argument_defeaters/D5-undercutting-comparator"
    )
    assert default_taxonomy_for_pattern("W-NONEXISTENT-99") is None

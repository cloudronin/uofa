"""Spec loader tests — §11.1 of the adversarial spec."""

from __future__ import annotations

import pytest

from uofa_cli.adversarial.spec_loader import (
    AdversarialSpec,
    SpecValidationError,
    load_spec,
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

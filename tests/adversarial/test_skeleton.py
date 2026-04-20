"""Skeleton-loader tests — §14 Q4 resolution."""

from __future__ import annotations

from pathlib import Path

import pytest

from uofa_cli.adversarial.skeleton import (
    IDENTITY_KEYS,
    PROVENANCE_KEYS,
    SkeletonLoadError,
    load_base_cou_skeleton,
)


MORRISON_COU1 = (
    Path(__file__).parent.parent.parent
    / "packs"
    / "vv40"
    / "examples"
    / "morrison"
    / "cou1"
)


def test_identity_block_extracted():
    sk = load_base_cou_skeleton(MORRISON_COU1, pack="vv40")
    identity = sk["identity"]
    # Morrison COU1 identity fields.
    assert identity.get("couName") == "CPB use"
    assert identity.get("deviceClass") == "Class II"
    assert identity.get("modelRiskLevel") == 2
    assert identity.get("decision") == "Accepted"
    assert "Morrison" in identity.get("name", "")
    # All keys in the identity block are valid identity keys.
    for k in identity:
        assert k in IDENTITY_KEYS


def test_factor_scaffold_populated():
    sk = load_base_cou_skeleton(MORRISON_COU1, pack="vv40")
    scaffold = sk["factor_scaffold"]
    assert isinstance(scaffold, list)
    assert len(scaffold) >= 7  # Morrison has 13 factors
    for f in scaffold:
        assert f["type"] == "CredibilityFactor"
        assert f["factorType"]
        assert f["factorStandard"] == "ASME-VV40-2018"
        # Scaffold stubs must NOT leak assessed levels.
        assert "requiredLevel" not in f
        assert "achievedLevel" not in f


def test_top_level_stamps_preserved():
    sk = load_base_cou_skeleton(MORRISON_COU1, pack="vv40")
    stamps = sk["top_level_stamps"]
    # Morrison has bindsRequirement, bindsModel, bindsDataset, etc.
    assert "bindsRequirement" in stamps
    for k in stamps:
        assert k in PROVENANCE_KEYS


def test_missing_file_raises():
    with pytest.raises(SkeletonLoadError):
        load_base_cou_skeleton(Path("/nonexistent/path/missing.jsonld"))


def test_dir_resolves_to_jsonld_file():
    sk = load_base_cou_skeleton(MORRISON_COU1, pack="vv40")
    # source_path should be the actual .jsonld file, not the directory.
    assert sk["source_path"].endswith(".jsonld")

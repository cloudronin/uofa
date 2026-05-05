"""Sanity checks for the 5-case mock bundle generator.

Ensures the fixture is well-formed (manifest matches, files present,
class distribution sums correctly) before downstream tests rely on it.
"""

from __future__ import annotations

import json
import tarfile
from pathlib import Path

from tests.adversarial.judge.fixtures.mock_bundle import (
    MOCK_CASES,
    MOCK_PACKAGE_COUNT,
    write_mock_bundle,
)


def test_write_mock_bundle_creates_tgz(tmp_path: Path) -> None:
    out = tmp_path / "out.tgz"
    written = write_mock_bundle(out)
    assert written == out
    assert out.exists()
    assert out.stat().st_size > 0


def test_mock_bundle_has_expected_members(tmp_path: Path) -> None:
    out = write_mock_bundle(tmp_path / "b.tgz")
    with tarfile.open(out, "r:gz") as tf:
        names = set(tf.getnames())

    assert "judge_ready_bundle/manifest.json" in names
    assert "judge_ready_bundle/coverage/matrix.csv" in names
    assert "judge_ready_bundle/coverage/summary.csv" in names
    for case in MOCK_CASES:
        assert f"judge_ready_bundle/packages/{case.case_id}.jsonld" in names
        assert f"judge_ready_bundle/packages/{case.case_id}.outcome.json" in names


def test_manifest_matches_case_count(tmp_path: Path) -> None:
    out = write_mock_bundle(tmp_path / "b.tgz")
    with tarfile.open(out, "r:gz") as tf:
        f = tf.extractfile("judge_ready_bundle/manifest.json")
        assert f is not None
        manifest = json.loads(f.read())

    assert manifest["package_count"] == MOCK_PACKAGE_COUNT
    # Distribution sums to total.
    assert sum(manifest["coverage_class_distribution"].values()) == MOCK_PACKAGE_COUNT


def test_outcome_jsons_carry_normalized_and_raw_class(tmp_path: Path) -> None:
    out = write_mock_bundle(tmp_path / "b.tgz")
    case = MOCK_CASES[0]
    with tarfile.open(out, "r:gz") as tf:
        f = tf.extractfile(f"judge_ready_bundle/packages/{case.case_id}.outcome.json")
        assert f is not None
        outcome = json.loads(f.read())
    assert outcome["coverage_class"] == case.coverage_class  # normalized
    assert outcome["phase2_outcome_class_raw"] == case.coverage_class_raw  # raw


def test_idempotent_overwrite(tmp_path: Path) -> None:
    p = tmp_path / "b.tgz"
    write_mock_bundle(p)
    first_size = p.stat().st_size
    write_mock_bundle(p)
    # Should be identical (deterministic content).
    assert p.stat().st_size == first_size

"""Tests for the bundle reader (open_bundle, iter_entries, manifest validation)."""

from __future__ import annotations

import json
import tarfile
from io import BytesIO
from pathlib import Path

import pytest

from uofa_cli.adversarial.judge.bundle import (
    Bundle,
    BundleEntry,
    BundleError,
    UnsafeBundleError,
    open_bundle,
)
from tests.adversarial.judge.fixtures.mock_bundle import (
    MOCK_CASES,
    MOCK_PACKAGE_COUNT,
    write_mock_bundle,
)


# ── happy-path open + iter ──────────────────────────────────────────────


class TestOpenBundle:
    def test_open_returns_bundle(self, mock_bundle_path: Path) -> None:
        with open_bundle(mock_bundle_path) as bundle:
            assert isinstance(bundle, Bundle)

    def test_manifest_loaded_and_validated(self, mock_bundle_path: Path) -> None:
        with open_bundle(mock_bundle_path) as bundle:
            assert bundle.manifest["package_count"] == MOCK_PACKAGE_COUNT
            assert "generator_provenance" in bundle.manifest

    def test_missing_path_raises(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            open_bundle(tmp_path / "nonexistent.tgz")


class TestIterEntries:
    def test_yields_one_entry_per_case(self, mock_bundle_path: Path) -> None:
        with open_bundle(mock_bundle_path) as bundle:
            entries = list(bundle.iter_entries())
        assert len(entries) == MOCK_PACKAGE_COUNT

    def test_entries_carry_case_id_package_outcome(self, mock_bundle_path: Path) -> None:
        with open_bundle(mock_bundle_path) as bundle:
            entries = list(bundle.iter_entries())
        case_ids = {e.case_id for e in entries}
        expected = {c.case_id for c in MOCK_CASES}
        assert case_ids == expected
        for e in entries:
            assert isinstance(e, BundleEntry)
            assert "@type" in e.package
            assert e.outcome["case_id"] == e.case_id

    def test_normalized_class_present_in_outcome(self, mock_bundle_path: Path) -> None:
        with open_bundle(mock_bundle_path) as bundle:
            entries = list(bundle.iter_entries())
        for e in entries:
            assert e.outcome["coverage_class"] in (
                "COV-HIT", "COV-MISS", "COV-WRONG", "GEN-INVALID"
            )
            assert "phase2_outcome_class_raw" in e.outcome


# ── failure modes ───────────────────────────────────────────────────────


def _write_tarball(path: Path, members: dict[str, str]) -> Path:
    """Write a custom tarball for failure-mode tests."""
    with tarfile.open(path, "w:gz") as tf:
        for name, payload in members.items():
            data = payload.encode("utf-8")
            info = tarfile.TarInfo(name=name)
            info.size = len(data)
            tf.addfile(info, BytesIO(data))
    return path


class TestFailureModes:
    def test_missing_manifest_raises_bundle_error(self, tmp_path: Path) -> None:
        p = _write_tarball(tmp_path / "no_manifest.tgz", {
            "judge_ready_bundle/packages/foo.jsonld": "{}",
        })
        with pytest.raises(BundleError, match="missing manifest"):
            open_bundle(p)

    def test_invalid_manifest_json_raises(self, tmp_path: Path) -> None:
        p = _write_tarball(tmp_path / "bad_json.tgz", {
            "judge_ready_bundle/manifest.json": "not valid json",
        })
        with pytest.raises(BundleError, match="not valid JSON"):
            open_bundle(p)

    def test_manifest_missing_required_field_fails_validation(self, tmp_path: Path) -> None:
        p = _write_tarball(tmp_path / "bad_schema.tgz", {
            # `package_count` and others missing.
            "judge_ready_bundle/manifest.json": json.dumps({
                "phase2_spec_version": "1.3",
            }),
        })
        with pytest.raises(Exception):  # jsonschema.ValidationError or BundleError
            open_bundle(p)

    def test_path_traversal_member_rejected(self, tmp_path: Path) -> None:
        # Manifest is valid, but a malicious member tries to escape the
        # extraction dir. The reader should refuse to open the bundle.
        p = _write_tarball(tmp_path / "evil.tgz", {
            "judge_ready_bundle/manifest.json": json.dumps({
                "phase2_spec_version": "1.3",
                "generated_at": "2026-05-04T00:00:00Z",
                "generator_provenance": {"generator_model": "test"},
                "package_count": 0,
                "coverage_class_distribution": {},
            }),
            "../escaped.txt": "evil",
        })
        with pytest.raises(UnsafeBundleError):
            open_bundle(p)

    def test_orphaned_jsonld_without_outcome_raises(self, tmp_path: Path) -> None:
        # Manifest valid; one package present, no matching outcome.
        p = _write_tarball(tmp_path / "orphan.tgz", {
            "judge_ready_bundle/manifest.json": json.dumps({
                "phase2_spec_version": "1.3",
                "generated_at": "2026-05-04T00:00:00Z",
                "generator_provenance": {"generator_model": "test"},
                "package_count": 1,
                "coverage_class_distribution": {"COV-HIT": 1},
            }),
            "judge_ready_bundle/packages/foo.jsonld": json.dumps({"@type": "X"}),
            # No foo.outcome.json.
        })
        with open_bundle(p) as bundle:
            with pytest.raises(BundleError, match="orphaned"):
                list(bundle.iter_entries())

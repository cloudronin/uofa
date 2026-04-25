"""Tests for ``uofa adversarial run`` batch orchestration — Phase 2 §9."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from uofa_cli.adversarial.runner import _discover_specs, run_batch


REPO_ROOT = Path(__file__).parent.parent.parent
CONFIRM_DIR = REPO_ROOT / "specs" / "confirm_existing"
GAP_DIR = REPO_ROOT / "specs" / "gap_probe"


def _build_args(out_dir: Path, batch: list[Path], **overrides) -> argparse.Namespace:
    base = dict(
        batch=batch,
        out=out_dir,
        model="mock",
        max_cost=None,
        parallel=1,
        resume=False,
        strict_circularity=False,
        allow_circular_model=False,
        max_retries=3,
        dry_run=False,
    )
    base.update(overrides)
    return argparse.Namespace(**base)


def test_discover_specs_finds_yaml_files(tmp_path):
    d = tmp_path / "batch1"
    d.mkdir()
    (d / "a.yaml").write_text("")
    (d / "b.yaml").write_text("")
    (d / "ignored.txt").write_text("")
    out = _discover_specs([d])
    assert len(out) == 2
    assert all(p.suffix == ".yaml" for _, p in out)


def test_discover_specs_handles_missing_dir(tmp_path):
    nonexistent = tmp_path / "no-such-dir"
    out = _discover_specs([nonexistent])
    assert out == []


@pytest.mark.parametrize("spec_filename", ["w-ar-01.yaml", "w-ep-01.yaml"])
def test_run_batch_produces_batch_manifest(tmp_path, spec_filename):
    """Mock-LLM batch on a single spec produces batch_manifest with the spec's results."""
    pytest.importorskip("yaml")
    if not (CONFIRM_DIR / spec_filename).exists():
        pytest.skip(f"spec {spec_filename} not present")

    # Prepare a one-spec batch dir
    batch_dir = tmp_path / "batch"
    batch_dir.mkdir()
    src = CONFIRM_DIR / spec_filename
    target = batch_dir / spec_filename
    target.write_text(src.read_text())

    out_dir = tmp_path / "out"
    args = _build_args(out_dir, [batch_dir])
    rc = run_batch(args)
    assert rc == 0, "batch should succeed under mock LLM"

    manifest_path = out_dir / "batch_manifest.json"
    assert manifest_path.exists()
    manifest = json.loads(manifest_path.read_text())
    assert manifest["specsLoaded"] == 1
    assert manifest["specsSucceeded"] == 1
    assert manifest["totalPackages"] >= 1
    # Per-spec entry present
    assert len(manifest["perSpecResults"]) == 1
    entry = manifest["perSpecResults"][0]
    assert entry["succeeded"] is True
    assert entry["coverage_intent"] == "confirm_existing"


def test_run_batch_resume_skips_existing_manifest(tmp_path):
    """When --resume is set and the per-spec manifest matches the spec hash,
    the runner should skip generation."""
    pytest.importorskip("yaml")
    spec_filename = "w-ar-01.yaml"
    if not (CONFIRM_DIR / spec_filename).exists():
        pytest.skip(f"spec {spec_filename} not present")

    batch_dir = tmp_path / "batch"
    batch_dir.mkdir()
    target = batch_dir / spec_filename
    target.write_text((CONFIRM_DIR / spec_filename).read_text())

    out_dir = tmp_path / "out"

    # First run
    args1 = _build_args(out_dir, [batch_dir])
    assert run_batch(args1) == 0
    first_manifest = json.loads((out_dir / "batch_manifest.json").read_text())
    first_count = first_manifest["totalPackages"]

    # Second run with --resume should not re-generate
    args2 = _build_args(out_dir, [batch_dir], resume=True)
    assert run_batch(args2) == 0
    second_manifest = json.loads((out_dir / "batch_manifest.json").read_text())
    # specsSucceeded still 1; totalPackages >= first since the resume path
    # reads the prior manifest's generated count.
    assert second_manifest["specsSucceeded"] == 1
    assert second_manifest["totalPackages"] == first_count


def test_run_batch_handles_multiple_batch_dirs(tmp_path):
    """Multiple --batch dirs should aggregate into a single batch manifest."""
    pytest.importorskip("yaml")
    if not (CONFIRM_DIR / "w-ar-01.yaml").exists():
        pytest.skip("w-ar-01 spec not present")
    if not (GAP_DIR / "gohar_ev_data_drift.yaml").exists():
        pytest.skip("gap_probe spec not present")

    b1 = tmp_path / "b1"
    b2 = tmp_path / "b2"
    b1.mkdir()
    b2.mkdir()
    (b1 / "w-ar-01.yaml").write_text((CONFIRM_DIR / "w-ar-01.yaml").read_text())
    (b2 / "data-drift.yaml").write_text(
        (GAP_DIR / "gohar_ev_data_drift.yaml").read_text()
    )

    out_dir = tmp_path / "out"
    args = _build_args(out_dir, [b1, b2])
    assert run_batch(args) == 0
    manifest = json.loads((out_dir / "batch_manifest.json").read_text())
    assert manifest["specsLoaded"] == 2
    assert manifest["specsSucceeded"] == 2

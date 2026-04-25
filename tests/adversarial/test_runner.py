"""Tests for ``uofa adversarial run`` batch orchestration — Phase 2 §9."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from uofa_cli.adversarial.runner import (
    _cou_short,
    _discover_specs,
    _expand_specs,
    _parse_csv_flag,
    run_batch,
)


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
        subtlety_override=None,
        base_cou_override=None,
        cost_preview=False,
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


# ───────────────────── P1: fan-out helpers (v1.8 §3) ─────────────────────


def test_parse_csv_flag_handles_whitespace_and_blanks():
    assert _parse_csv_flag(None) == []
    assert _parse_csv_flag("") == []
    assert _parse_csv_flag("low,medium,high") == ["low", "medium", "high"]
    assert _parse_csv_flag(" low , ,  medium ,") == ["low", "medium"]


def test_cou_short_uses_last_two_segments():
    assert _cou_short("packs/vv40/examples/morrison/cou1") == "morrison-cou1"
    assert _cou_short("packs/vv40/examples/nagaraja/cou1") == "nagaraja-cou1"
    # File path: parent name + stem (extension dropped)
    assert (
        _cou_short("packs/nasa-7009b/examples/aerospace/uofa-aero-cou1-nasa7009b.jsonld")
        == "aerospace-uofa-aero-cou1-nasa7009b"
    )


def test_expand_specs_no_overrides_yields_one_cell_per_spec(tmp_path):
    """When neither override is set, expansion is identity (1:1)."""
    spec1 = tmp_path / "a.yaml"
    spec1.write_text("target:\n  coverage_intent: confirm_existing\n")
    spec2 = tmp_path / "b.yaml"
    spec2.write_text("target:\n  coverage_intent: gap_probe\n")
    cells = _expand_specs(
        [("c1", spec1), ("c2", spec2)],
        subtlety_overrides=[],
        base_cou_overrides=[],
    )
    assert len(cells) == 2
    assert all(c.subtlety_override is None for c in cells)
    assert all(c.base_cou_override is None for c in cells)
    assert all(c.out_dir_suffix == "" for c in cells)


def test_expand_specs_subtlety_fanout_3x(tmp_path):
    """--subtlety-override low,medium,high produces 3 cells per spec."""
    spec = tmp_path / "a.yaml"
    spec.write_text("target:\n  coverage_intent: confirm_existing\n")
    cells = _expand_specs(
        [("c", spec)],
        subtlety_overrides=["low", "medium", "high"],
        base_cou_overrides=[],
    )
    assert len(cells) == 3
    assert sorted(c.subtlety_override for c in cells) == ["high", "low", "medium"]
    suffixes = sorted(c.out_dir_suffix for c in cells)
    assert suffixes == ["_high", "_low", "_medium"]


def test_expand_specs_base_cou_fanout_skips_gap_probe(tmp_path):
    """confirm_existing fans across base_cou; gap_probe does NOT — per §7
    convention, gap_probe specs pin a single base_cou by design."""
    confirm_spec = tmp_path / "ce.yaml"
    confirm_spec.write_text("target:\n  coverage_intent: confirm_existing\n")
    gap_spec = tmp_path / "gp.yaml"
    gap_spec.write_text("target:\n  coverage_intent: gap_probe\n")
    cells = _expand_specs(
        [("ce", confirm_spec), ("gp", gap_spec)],
        subtlety_overrides=[],
        base_cou_overrides=[
            "packs/vv40/examples/morrison/cou1",
            "packs/vv40/examples/morrison/cou2",
            "packs/vv40/examples/nagaraja/cou1",
        ],
    )
    # confirm_existing: 3 cells. gap_probe: 1 cell (override ignored).
    assert len(cells) == 4
    confirm_cells = [c for c in cells if c.category == "ce"]
    gap_cells = [c for c in cells if c.category == "gp"]
    assert len(confirm_cells) == 3
    assert len(gap_cells) == 1
    # gap_probe cell has no base_cou override applied
    assert gap_cells[0].base_cou_override is None
    assert gap_cells[0].out_dir_suffix == ""
    # confirm cells carry suffix derived from cou path
    assert {c.out_dir_suffix for c in confirm_cells} == {
        "_morrison-cou1", "_morrison-cou2", "_nagaraja-cou1"
    }


def test_expand_specs_combined_fanout_is_cartesian(tmp_path):
    """3 subtlety × 3 base_cou = 9 cells per confirm_existing spec."""
    spec = tmp_path / "ce.yaml"
    spec.write_text("target:\n  coverage_intent: confirm_existing\n")
    cells = _expand_specs(
        [("ce", spec)],
        subtlety_overrides=["low", "medium", "high"],
        base_cou_overrides=[
            "packs/vv40/examples/morrison/cou1",
            "packs/vv40/examples/morrison/cou2",
            "packs/vv40/examples/nagaraja/cou1",
        ],
    )
    assert len(cells) == 9
    # Each cell has both override values + a 2-part suffix
    for c in cells:
        assert c.subtlety_override in {"low", "medium", "high"}
        assert c.base_cou_override is not None
        # Suffix shape: _<sub>_<vendor>-<cou>
        assert c.out_dir_suffix.count("_") == 2


def test_expand_specs_negative_control_fans_base_cou(tmp_path):
    """negative_control specs are also eligible for base_cou fan-out."""
    spec = tmp_path / "nc.yaml"
    spec.write_text("target:\n  coverage_intent: negative_control\n")
    cells = _expand_specs(
        [("nc", spec)],
        subtlety_overrides=[],
        base_cou_overrides=[
            "packs/vv40/examples/morrison/cou1",
            "packs/vv40/examples/morrison/cou2",
        ],
    )
    assert len(cells) == 2


def test_expand_specs_interaction_pins_base_cou(tmp_path):
    """interaction specs pin a single base_cou per §7."""
    spec = tmp_path / "ix.yaml"
    spec.write_text("target:\n  coverage_intent: interaction\n")
    cells = _expand_specs(
        [("ix", spec)],
        subtlety_overrides=[],
        base_cou_overrides=[
            "packs/vv40/examples/morrison/cou1",
            "packs/vv40/examples/morrison/cou2",
        ],
    )
    assert len(cells) == 1
    assert cells[0].base_cou_override is None


# ───────────────────── P1: --cost-preview path ─────────────────────


def test_run_batch_cost_preview_skips_llm_and_writes_no_manifest(tmp_path):
    """--cost-preview discovers specs, prints a roll-up, exits 0, and does
    NOT create the batch_manifest.json or any output dirs."""
    pytest.importorskip("yaml")
    spec_filename = "w-ar-01.yaml"
    if not (CONFIRM_DIR / spec_filename).exists():
        pytest.skip(f"spec {spec_filename} not present")

    batch_dir = tmp_path / "batch"
    batch_dir.mkdir()
    (batch_dir / spec_filename).write_text(
        (CONFIRM_DIR / spec_filename).read_text()
    )

    out_dir = tmp_path / "out"  # intentionally not created up front
    args = _build_args(out_dir, [batch_dir], cost_preview=True)
    assert run_batch(args) == 0
    # No manifest, no per-category subdirs
    assert not (out_dir / "batch_manifest.json").exists()


def test_run_batch_invalid_subtlety_override_returns_2(tmp_path):
    """--subtlety-override with a value not in {low,medium,high} returns 2."""
    pytest.importorskip("yaml")
    spec_filename = "w-ar-01.yaml"
    if not (CONFIRM_DIR / spec_filename).exists():
        pytest.skip(f"spec {spec_filename} not present")

    batch_dir = tmp_path / "batch"
    batch_dir.mkdir()
    (batch_dir / spec_filename).write_text(
        (CONFIRM_DIR / spec_filename).read_text()
    )

    out_dir = tmp_path / "out"
    args = _build_args(
        out_dir, [batch_dir], subtlety_override="low,bogus"
    )
    assert run_batch(args) == 2


def test_run_batch_subtlety_override_creates_suffixed_output_dirs(tmp_path):
    """Mock-LLM batch with --subtlety-override low,high produces 2 cells
    in the perSpecResults array, each with a distinct output dir suffix."""
    pytest.importorskip("yaml")
    spec_filename = "w-ar-01.yaml"
    if not (CONFIRM_DIR / spec_filename).exists():
        pytest.skip(f"spec {spec_filename} not present")

    batch_dir = tmp_path / "batch"
    batch_dir.mkdir()
    (batch_dir / spec_filename).write_text(
        (CONFIRM_DIR / spec_filename).read_text()
    )

    out_dir = tmp_path / "out"
    args = _build_args(out_dir, [batch_dir], subtlety_override="low,high")
    rc = run_batch(args)
    assert rc == 0
    manifest = json.loads((out_dir / "batch_manifest.json").read_text())
    # 1 spec × 2 subtlety = 2 cells
    assert manifest["specsLoaded"] == 2
    cell_ids = sorted(r["spec_id"] for r in manifest["perSpecResults"])
    assert any(s.endswith("_low") for s in cell_ids)
    assert any(s.endswith("_high") for s in cell_ids)
    # Manifest captures the override values
    assert manifest["subtletyOverride"] == ["low", "high"]

"""Prompt-template tests — §11.1."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from uofa_cli.adversarial.prompts import (
    TemplateNotFoundError,
    _REGISTRY,
    get_template,
    mock_response,
)
from uofa_cli.adversarial.prompts import d3_undercutting_inference as d3
from uofa_cli.adversarial.skeleton import load_base_cou_skeleton
from uofa_cli.adversarial.spec_loader import load_spec


FIXTURES = Path(__file__).parent / "fixtures"


def _render(spec_path: Path, subtlety: str) -> tuple[str, str]:
    spec = load_spec(spec_path)
    spec.subtlety = subtlety
    skeleton = load_base_cou_skeleton(spec.base_cou, pack=spec.pack)
    template = get_template(spec.target_weakener)
    return template.render(spec, skeleton)


@pytest.mark.parametrize("subtlety", ["low", "medium", "high"])
def test_d3_w_ar_05_renders_all_subtlety_levels(valid_spec_path, subtlety):
    system, user = _render(valid_spec_path, subtlety)
    assert system
    assert user
    assert "W-AR-05" in user
    assert "JSON-LD" in system
    assert d3.SUBTLETY_GUIDANCE[subtlety][:30] in user


def test_d3_w_ar_05_prompt_includes_context_snippet(valid_spec_path):
    _, user = _render(valid_spec_path, "high")
    # Morrison COU1 identity lands in the prompt.
    assert "Morrison" in user or "hemolysis" in user.lower()
    # ProfileMinimal marker is enforced.
    assert "ProfileMinimal" in user


def test_d3_w_ar_05_prompt_includes_factor_list(valid_spec_path):
    _, user = _render(valid_spec_path, "medium")
    assert "factor_scaffold" in user or "factorType" in user


def test_prompt_version_exposed():
    assert isinstance(d3.PROMPT_VERSION, str)
    assert d3.PROMPT_VERSION.startswith("v")


@pytest.mark.parametrize("subtlety", ["low", "medium", "high"])
def test_snapshot_prompt(valid_spec_path, subtlety):
    _, user = _render(valid_spec_path, subtlety)
    system, _ = _render(valid_spec_path, subtlety)
    snapshot = FIXTURES / f"snapshot_d3_w_ar_05_{subtlety}.txt"
    expected = snapshot.read_text()
    rendered = f"── SYSTEM ──\n{system}\n── USER ──\n{user}"
    if os.environ.get("UOFA_UPDATE_SNAPSHOTS") == "1":
        snapshot.write_text(rendered)
        pytest.skip(f"snapshot refreshed: {snapshot}")
    assert rendered == expected, (
        f"snapshot mismatch for {subtlety}. Re-run with UOFA_UPDATE_SNAPSHOTS=1 to refresh."
    )


def test_registry_rejects_unknown_weakener():
    with pytest.raises(TemplateNotFoundError):
        get_template("W-ZZ-99")


def test_registry_contains_w_ar_05():
    assert "W-AR-05" in _REGISTRY


def test_mock_response_returns_json():
    """mock_response should produce a string that parses as JSON."""
    import json

    raw = mock_response({})
    doc = json.loads(raw)
    assert doc.get("synthetic") is True
    types = doc.get("type")
    if isinstance(types, list):
        assert "uofa:SyntheticAdversarialSample" in types
    else:
        assert types == "uofa:SyntheticAdversarialSample"


# ----- Phase 2: snapshot all template specs -----

REPO_ROOT = Path(__file__).parent.parent.parent
PHASE2_SNAPSHOTS = FIXTURES / "snapshots"
PHASE2_SPECS = sorted(
    list((REPO_ROOT / "specs" / "confirm_existing").glob("*.yaml"))
    + list((REPO_ROOT / "specs" / "gap_probe").glob("*.yaml"))
    + list((REPO_ROOT / "specs" / "negative_controls").glob("*.yaml"))
    + list((REPO_ROOT / "specs" / "interaction").glob("*.yaml"))
)


def _snapshot_key(spec) -> str:
    """Stable per-spec snapshot identifier.

    confirm_existing: weakener id (lowercase, underscores) — one snapshot
        per unique weakener.
    gap_probe: full source_taxonomy with slashes/hyphens flattened — one
        snapshot per unique sub-type.
    interaction: spec_id flattened — multiple INT specs share the primary
        target_weakener so we key by spec_id to avoid file collision.
    negative_control: spec_id — each NC is a distinct archetype.
    """
    if spec.coverage_intent == "confirm_existing":
        return spec.target_weakener.replace("-", "_").lower()
    if spec.coverage_intent == "gap_probe":
        return (spec.source_taxonomy or "unknown").replace("/", "_").replace("-", "_")
    if spec.coverage_intent in ("interaction", "negative_control"):
        return spec.spec_id.replace("-", "_")
    return spec.spec_id


@pytest.mark.parametrize("spec_path", PHASE2_SPECS, ids=lambda p: p.stem)
@pytest.mark.parametrize("subtlety", ["low", "medium", "high"])
def test_confirm_existing_snapshot(spec_path, subtlety):
    """One snapshot per (template, subtlety). Refresh with UOFA_UPDATE_SNAPSHOTS=1.

    Spec §12.3: ~105 snapshots when full battery ships. Phase 2 covers
    confirm_existing (22 × 3 = 66), gap_probe (22 × 3 = 66), negative_control
    (10 × 3 = 30), interaction (6 × 3 = 18). The legacy W-AR-05 fixtures
    live in fixtures/ rather than fixtures/snapshots/ and are covered by
    ``test_snapshot_prompt`` above.
    """
    from uofa_cli.adversarial.skeleton import load_base_cou_skeleton
    from uofa_cli.adversarial.spec_loader import load_spec
    from uofa_cli.adversarial.prompts import get_template_for_spec

    if spec_path.stem == "w_ar_05":
        pytest.skip("W-AR-05 covered by legacy test_snapshot_prompt")

    spec = load_spec(spec_path)
    spec.subtlety = subtlety
    skeleton = load_base_cou_skeleton(spec.base_cou, pack=spec.pack)
    template = get_template_for_spec(spec)
    system, user = template.render(spec, skeleton)

    module_short = spec._template_module()
    snapshot_file = (
        PHASE2_SNAPSHOTS
        / f"snapshot_{module_short}_{_snapshot_key(spec)}_{subtlety}.txt"
    )
    rendered = f"── SYSTEM ──\n{system}\n── USER ──\n{user}"

    if os.environ.get("UOFA_UPDATE_SNAPSHOTS") == "1":
        snapshot_file.parent.mkdir(parents=True, exist_ok=True)
        snapshot_file.write_text(rendered)
        pytest.skip(f"snapshot refreshed: {snapshot_file.name}")

    assert snapshot_file.exists(), (
        f"missing snapshot {snapshot_file.name}. Run with "
        f"UOFA_UPDATE_SNAPSHOTS=1 to generate."
    )
    expected = snapshot_file.read_text()
    assert rendered == expected, (
        f"snapshot mismatch for {spec.spec_id} ({subtlety}). "
        f"Re-run with UOFA_UPDATE_SNAPSHOTS=1 to refresh."
    )

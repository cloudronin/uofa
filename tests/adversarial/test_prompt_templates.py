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

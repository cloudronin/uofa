"""Phase 2 v1.8 §7.6 paraphrasing infrastructure tests."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from uofa_cli.adversarial.prompts import (
    _ParaphrasedTemplate,
    get_template_for_spec,
)
from uofa_cli.adversarial.prompts.paraphrase import (
    apply_paraphrase,
    is_paraphrased,
)
from uofa_cli.adversarial.spec_loader import (
    SpecValidationError,
    VALID_PROMPT_VARIANTS,
    load_spec,
)

REPO_ROOT = Path(__file__).parent.parent.parent
PARAPHRASE_DIR = REPO_ROOT / "specs" / "paraphrasing"
CONFIRM_DIR = REPO_ROOT / "specs" / "confirm_existing"


# ───────────────────── apply_paraphrase substitutions ─────────────────────


def test_apply_paraphrase_p0_is_identity():
    """p0 is the canonical path; no substitutions should occur."""
    sys, user = "Hello", "World"
    out_sys, out_user = apply_paraphrase("p0", sys, user)
    assert (out_sys, out_user) == ("Hello", "World")


def test_apply_paraphrase_p1_substitutes_descriptive_headers():
    """p1 swaps section headers; structural directives are untouched."""
    sys = "You generate synthetic simulation-credibility evidence."
    user = "Target weakener: W-AR-05\nSubtlety level: high"
    out_sys, out_user = apply_paraphrase("p1", sys, user)
    assert "produce synthetic simulation-credibility artifacts" in out_sys
    assert "Targeted defeater pattern:" in out_user
    assert "Plausibility tier:" in out_user
    # Structural fields preserved
    assert "W-AR-05" in out_user
    assert "high" in out_user


def test_apply_paraphrase_p2_uses_terse_register():
    """p2 compresses prose. Schema directives (field names) survive."""
    sys = "Requirements:"
    user = "Target weakener: W-AR-05\nSubtlety level: high"
    out_sys, out_user = apply_paraphrase("p2", sys, user)
    assert "Constraints:" in out_sys
    assert "Weakener: W-AR-05" in out_user
    assert "Subtlety: high" in out_user


def test_is_paraphrased_only_p1_p2():
    assert is_paraphrased("p0") is False
    assert is_paraphrased("p1") is True
    assert is_paraphrased("p2") is True
    assert is_paraphrased("unknown") is False


def test_apply_paraphrase_unknown_variant_is_noop():
    """Unknown variants behave like p0 (defensive default)."""
    out_sys, out_user = apply_paraphrase("p99", "S", "U")
    assert (out_sys, out_user) == ("S", "U")


# ───────────────────── spec_loader prompt_variant ─────────────────────


def test_spec_loader_default_prompt_variant_is_p0():
    """Existing specs without an explicit prompt_variant default to p0."""
    if not (CONFIRM_DIR / "w-ar-01.yaml").exists():
        pytest.skip("baseline spec missing")
    spec = load_spec(CONFIRM_DIR / "w-ar-01.yaml")
    assert spec.prompt_variant == "p0"


def test_spec_loader_rejects_invalid_prompt_variant(tmp_path):
    """generation.prompt_variant outside {p0,p1,p2} raises SpecValidationError."""
    spec_yaml = tmp_path / "bad.yaml"
    spec_yaml.write_text("""
spec_id: adv-test-bad-pv
description: bad
target:
  weakener: W-AR-05
  defeater_type: D3
  uncertainty_category: argument
  coverage_intent: confirm_existing
pack: vv40
package_context:
  base_cou: packs/vv40/examples/morrison/cou1
  mode: skeleton
  factors: [Model form]
  decision: Accepted
generation:
  model: claude-sonnet-4-6
  n_variants: 1
  subtlety: high
  prompt_variant: p99
""".lstrip())
    with pytest.raises(SpecValidationError, match="prompt_variant"):
        load_spec(spec_yaml)


def test_valid_prompt_variants_constant():
    assert VALID_PROMPT_VARIANTS == {"p0", "p1", "p2"}


# ───────────────────── _ParaphrasedTemplate dispatch ─────────────────────


def test_get_template_for_spec_p0_returns_module():
    """p0 dispatch returns the canonical module unchanged."""
    if not (CONFIRM_DIR / "w-ar-01.yaml").exists():
        pytest.skip("baseline spec missing")
    spec = load_spec(CONFIRM_DIR / "w-ar-01.yaml")
    tmpl = get_template_for_spec(spec)
    # Plain module — not the wrapper
    assert not isinstance(tmpl, _ParaphrasedTemplate)
    assert hasattr(tmpl, "render")
    assert hasattr(tmpl, "PROMPT_VERSION")


def test_get_template_for_spec_p1_returns_wrapper():
    """p1 dispatch returns the _ParaphrasedTemplate wrapper with bumped
    PROMPT_VERSION."""
    if not (CONFIRM_DIR / "w-ar-01.yaml").exists():
        pytest.skip("baseline spec missing")
    spec = load_spec(CONFIRM_DIR / "w-ar-01.yaml")
    spec.prompt_variant = "p1"  # mutate post-load to bypass YAML
    tmpl = get_template_for_spec(spec)
    assert isinstance(tmpl, _ParaphrasedTemplate)
    assert tmpl.PROMPT_VERSION.endswith("+p1")
    # render() composes parent + paraphrase
    assert callable(tmpl.render)


def test_get_template_for_spec_p2_returns_wrapper():
    if not (CONFIRM_DIR / "w-ar-01.yaml").exists():
        pytest.skip("baseline spec missing")
    spec = load_spec(CONFIRM_DIR / "w-ar-01.yaml")
    spec.prompt_variant = "p2"
    tmpl = get_template_for_spec(spec)
    assert isinstance(tmpl, _ParaphrasedTemplate)
    assert tmpl.PROMPT_VERSION.endswith("+p2")


# ───────────────────── paraphrasing battery presence ─────────────────────


def test_paraphrasing_battery_has_30_specs():
    if not PARAPHRASE_DIR.exists():
        pytest.skip("paraphrasing specs not present")
    yamls = sorted(PARAPHRASE_DIR.glob("*.yaml"))
    assert len(yamls) == 30, (
        f"expected 10 base × 3 variants = 30 paraphrasing specs, got {len(yamls)}"
    )
    # Distribution: 10 of each variant
    by_variant: dict[str, int] = {"p0": 0, "p1": 0, "p2": 0}
    for p in yamls:
        spec = load_spec(p)
        by_variant[spec.prompt_variant] += 1
    assert by_variant == {"p0": 10, "p1": 10, "p2": 10}


def test_paraphrasing_battery_runs_under_mock_llm(tmp_path):
    """End-to-end mock-LLM run produces 30 specs × 3 variants = 90 packages."""
    pytest.importorskip("yaml")
    if not PARAPHRASE_DIR.exists():
        pytest.skip("paraphrasing specs not present")

    from uofa_cli.adversarial.runner import run_batch

    out_dir = tmp_path / "out"
    args = argparse.Namespace(
        batch=[PARAPHRASE_DIR], out=out_dir, model="mock",
        max_cost=None, parallel=1, resume=False,
        strict_circularity=False, allow_circular_model=False,
        max_retries=3, dry_run=False,
        subtlety_override=None, base_cou_override=None, cost_preview=False,
    )
    rc = run_batch(args)
    assert rc == 0
    manifest = json.loads((out_dir / "batch_manifest.json").read_text())
    assert manifest["specsLoaded"] == 30
    assert manifest["specsSucceeded"] == 30
    assert manifest["totalPackages"] == 90  # §3: 10 × 3 paraphrases × 3 variants

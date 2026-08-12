"""The labeling sheet and the extraction prompt render from one source.

Written after the two documents were found to define three of four Group-B
properties differently (`CONSTRUCT-DRIFT.md`, 2026-08-11). The drift produced a
100% false-fire rate on P7 across three model families, and was invisible
because each document read correctly on its own.

The guard is not review discipline. It is that the definition exists once and
both artifacts are generated from it, so a hand-edit to either fails here.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO / "src"))

from uofa_cli import properties  # noqa: E402


def test_both_artifacts_match_the_property_source():
    """The whole point. Hand-edit either document and this goes red.

    Fix by editing `packs/model-credibility/properties/P*.json` and running
    `python -m uofa_cli.properties --write`, never by editing the rendered
    region -- an edit there survives exactly until the next render.
    """
    stale = properties.check()
    assert not stale, (
        f"rendered regions differ from the property source: {stale}. "
        "Edit the JSON and re-render; do not edit the artifact.")


def test_every_property_defines_both_directions():
    """A definition with no `absent` clause is half a definition, and the half
    it omits is where every over-generous label came from."""
    for p in properties.load():
        assert p["present"], f"{p['id']}: no present examples"
        assert p["absent"] or p["id"] == "P1_score", f"{p['id']}: no absent examples"


def test_the_adjudicated_negatives_survive_into_both_artifacts():
    """The three worked negatives are the 2026-08-11 label review's output.

    They are the reason the sheet and the prompt were reconciled at all, so a
    render that silently dropped them would restore the exact ambiguity the
    review resolved. Checked by content, not by counting.
    """
    sheet = properties.current(_REPO / properties.SHEET, properties.SHEET_MARKERS)
    prompt = properties.current(_REPO / properties.PROMPT, properties.PROMPT_MARKERS)

    for phrase in (
        "Research use only",              # P6: model-level disclaimer is not a COU
        "MEMBERSHIP in an ablation",      # P7: an arm is not a control
        "PROMPT REGIME",                  # P4: n-shot alone is not a run policy
    ):
        assert phrase in sheet, f"sheet lost the worked negative: {phrase!r}"
        assert phrase in prompt, f"prompt lost the worked negative: {phrase!r}"


def test_prompt_asks_for_every_form_the_sheet_counts():
    """The drift, as a direct assertion.

    P7 is the case that motivated all of this: the sheet counted "ablations
    offered as controls" and the prompt named neither ablations nor limitation
    statements, so the extractor was never asked for the form most labeled
    positives took.
    """
    prompt = properties.current(_REPO / properties.PROMPT, properties.PROMPT_MARKERS)
    for p in properties.load():
        if p["field"] == "metric_value":
            continue
        for example in p["present"]:
            head = example.split("(")[0].split(";")[0].strip().rstrip(".")
            assert head[:40] in prompt, (
                f"{p['id']}: the sheet counts {head[:40]!r} but the prompt "
                "does not ask for it -- this is the drift class recurring")


def test_field_names_match_the_extractor_contract():
    """Rendering must not rename a field out from under `card_prose.parse`."""
    from uofa_cli.furnishers import card_prose  # noqa: E402

    src = Path(card_prose.__file__).read_text(encoding="utf-8")
    for p in properties.load():
        if p["field"] == "metric_value":
            continue
        assert f'"{p["field"]}"' in src, (
            f"{p['id']}: prompt emits `{p['field']}` but card_prose never reads it")

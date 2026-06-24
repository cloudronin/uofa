"""Each frozen invariant fails loudly on a constructed violation, and both
Morrison fixtures pass. assert_reviewer_invariants is the guard that converts a
contradictory render from "catch it by eye on a PDF" into "cannot be emitted"."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from space.gloss import load_gloss
from space.reviewer import render_reviewer_html
from space.reviewer_state import (
    Concern,
    FactorState,
    ReviewerInvariantError,
    ReviewerState,
    Status,
    assert_reviewer_invariants,
    build_reviewer_state,
)

_FIX = Path(__file__).with_name("fixtures")
GLOSS = load_gloss()


def _factor(name, status=Status.NOT_STATED, required=True, targeting=()):
    return FactorState(name=name, plain_name=name, what_it_means="", status=status,
                       required=required, targeting_weakeners=tuple(targeting))


def _state(**over):
    base = dict(
        cou_name="C", cou_description="", standard="ASME V&V 40", risk_level=5,
        device_class=None, factors=(_factor("Model form", Status.EVIDENCED),),
        n_evidenced=1, n_expected=13, n_required=1, completeness_pct=8,
        required_all_accounted=False, open_high_count=0, missing=(),
        concerns=(), severity_counts={}, gates={"passed": 1, "total": 2},
        authenticity={},
    )
    base.update(over)
    return ReviewerState(**base)


def _raises(state, number):
    with pytest.raises(ReviewerInvariantError) as ei:
        assert_reviewer_invariants(state)
    assert ei.value.number == number


# ── each invariant fires on a constructed violation ──

def test_invariant_1_evidenced_factor_targeted_by_high_weakener():
    s = _state(
        factors=(_factor("Model form", Status.EVIDENCED),),
        concerns=(Concern("W-X", "High", "High", "d", ("Model form",), 1),),
        severity_counts={"High": 1},
    )
    _raises(s, 1)


def test_invariant_2_all_accounted_with_open_high():
    s = _state(required_all_accounted=True, open_high_count=1,
               concerns=(Concern("W-X", "High", "High", "d", (), 1),),
               severity_counts={"High": 1})
    _raises(s, 2)


def test_invariant_3_evidenced_count_mismatch():
    s = _state(factors=(_factor("Model form", Status.EVIDENCED),), n_evidenced=5)
    _raises(s, 3)


def test_invariant_4_severity_word_mismatch():
    # glance word would be "Critical", concern line word is "High".
    s = _state(
        factors=(_factor("Model form", Status.NOT_STATED),), n_evidenced=0,
        concerns=(Concern("W-X", "High", "High", "d", (), 1),),
        severity_counts={"Critical": 1},
    )
    _raises(s, 4)


def test_invariant_5_all_accounted_with_unevidenced_required():
    s = _state(
        factors=(_factor("Model form", Status.NOT_STATED, required=True),),
        n_evidenced=0, required_all_accounted=True, open_high_count=0,
    )
    _raises(s, 5)


def test_invariant_6_concern_count_mismatch():
    s = _state(
        factors=(_factor("Model form", Status.NOT_STATED),), n_evidenced=0,
        concerns=(Concern("W-X", "High", "High", "d", (), 1),),
        severity_counts={"High": 2},   # words match, totals do not
    )
    _raises(s, 6)


# ── both fixtures pass ──

@pytest.mark.parametrize("cou", ["cou1", "cou2"])
def test_morrison_fixtures_satisfy_all_invariants(cou):
    payload = json.loads((_FIX / f"morrison_{cou}_state.json").read_text())
    assert_reviewer_invariants(build_reviewer_state(payload, GLOSS))  # does not raise


# ── negative: a bad state never reaches HTML ──

def test_evidenced_weakener_target_blocks_render():
    # If a future builder produced an EVIDENCED factor that a High weakener
    # targets, the render must raise (invariant 1) rather than emit a page.
    bad = {
        "pack": "vv40",
        "completeness": {"assessed": ["Model form"], "missing": [], "excluded": [],
                         "n_assessed": 1, "n_expected": 13, "denom": 13},
        "weakeners": [{"patternId": "W-X", "severity": "High",
                       "factors": ["Model form"], "hits": 1, "description": "d"}],
        "structural": {"conforms": True, "violations": [], "n": 0},
        "context": {"model_risk_level": 5, "authenticity": {}},
    }
    # build_reviewer_state demotes it, so the normal path is safe...
    assert render_reviewer_html(bad, GLOSS)  # does not raise (demoted to Not stated)
    # ...but a hand-built EVIDENCED+targeted state is rejected.
    state = build_reviewer_state(bad, GLOSS)
    f = next(f for f in state.factors if f.name == "Model form")
    forced = replace(state, factors=tuple(
        replace(x, status=Status.EVIDENCED) if x.name == "Model form" else x
        for x in state.factors), n_evidenced=state.n_evidenced + 1)
    with pytest.raises(ReviewerInvariantError) as ei:
        assert_reviewer_invariants(forced)
    assert ei.value.number == 1
    assert f.status is Status.NOT_STATED

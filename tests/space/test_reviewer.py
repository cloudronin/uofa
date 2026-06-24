"""Reviewer render: reads only from ReviewerState, golden snapshots for both
Morrison COUs, and the contradictions the protocol now makes impossible.

Fixtures are source-grounded (firings/COU text/conformance from the real
JSON-LD; see fixtures/_generate.py). Regenerate with that script - never
hand-edit a golden."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from space.gloss import load_gloss
from space.reviewer import render_reviewer_html
from space.summary import expected_factors

_FIX = Path(__file__).with_name("fixtures")
GLOSS = load_gloss()


def _payload(cou):
    return json.loads((_FIX / f"morrison_{cou}_state.json").read_text(encoding="utf-8"))


def _html(cou):
    return render_reviewer_html(_payload(cou), GLOSS)


# ── structure ──

@pytest.mark.parametrize("cou", ["cou1", "cou2"])
def test_all_six_sections_render_in_order(cou):
    html = _html(cou)
    headings = [
        "<h2>What this model was used for</h2>",
        "<h2>At a glance</h2>",
        "<h2>Credibility factors</h2>",
        "<h2>Concerns found</h2>",
        "<h2>What is still missing</h2>",
        "<h2>Authenticity</h2>",
    ]
    pos = [html.find(h) for h in headings]
    assert all(p != -1 for p in pos), pos
    assert pos == sorted(pos)


@pytest.mark.parametrize("cou", ["cou1", "cou2"])
def test_reviewer_host_is_the_print_target(cou):
    assert 'id="ri-reviewer-host"' in _html(cou)


@pytest.mark.parametrize("cou", ["cou1", "cou2"])
def test_plain_language_not_raw_ids(cou):
    html = _html(cou)
    assert "Is the model built right for this use" in html   # gloss for "Model form"
    assert "ASME V&amp;V 40" in html
    for name in expected_factors("vv40"):
        assert GLOSS[name]["plain_name"] in html


@pytest.mark.parametrize("cou", ["cou1", "cou2"])
def test_no_holistic_verdict(cou):
    html = _html(cou)
    assert "Indicative summary, not a formal acceptance decision." in html
    assert "trustworthy" not in html.lower()
    assert ">Accepted</" not in html and ">Not accepted</" not in html


# ── the contradictions the protocol makes impossible ──

@pytest.mark.parametrize("cou", ["cou1", "cou2"])
def test_severity_word_single_source(cou):
    # at-a-glance count word == concern-line word; raw "Medium" never surfaces.
    html = _html(cou)
    assert "Moderate" in html
    assert "Medium" not in html


@pytest.mark.parametrize("cou", ["cou1", "cou2"])
def test_no_evidenced_factor_is_an_open_high_weakener_target(cou):
    # Invariant 1, observed at the render level: a factor disputed by a High/
    # Moderate concern never reads "Evidenced".
    payload = _payload(cou)
    from space.reviewer_state import build_reviewer_state, Status, _DEMOTING
    state = build_reviewer_state(payload, GLOSS)
    targeted = {f for c in state.concerns if c.severity in _DEMOTING for f in c.factors}
    for f in state.factors:
        if f.name in targeted:
            assert f.status is not Status.EVIDENCED


@pytest.mark.parametrize("cou", ["cou1", "cou2"])
def test_completeness_100_cannot_coexist_with_all_accounted_and_high(cou):
    # Invariant 2: the page never claims "all required accounted for" while a
    # High concern is open. (build + assert already enforce this; assert here.)
    from space.reviewer_state import build_reviewer_state
    state = build_reviewer_state(_payload(cou), GLOSS)
    if state.has_high_weakener:
        assert state.required_all_accounted is False


def test_cou2_no_longer_self_contradicts():
    # The Build B case: must NOT show 100%/all-evidenced next to High concerns.
    html = _html("cou2")
    assert "<dt>Completeness</dt><dd>100%</dd>" not in html
    assert "<dt>Completeness</dt><dd>38%</dd>" in html
    assert "38% of all factors evidenced" in html
    assert "8 factors required at Level 5 still need evidence" in html
    assert "Not stated" in html                       # W-EP-04 unassessed + provenance/COU demotions


def test_cou1_high_completeness_reframed_not_all_clear():
    # The reframing path: high factor-completeness, but concerns keep it from
    # reading "all accounted for".
    html = _html("cou1")
    assert "69% of all factors evidenced" in html
    assert "high-severity concerns remain open before this is review-ready" in html
    assert "all factors required at Level 2 are accounted for" not in html
    assert "Not applicable" in html                   # the scoped-out factors


def test_validation_scoped_concern_demotes_its_semantic_factor():
    # The engine-layer fix: a validation/COU-scoped concern that targets no
    # factor IRI still demotes the factor it implicates, via summary's
    # _PATTERN_FACTOR_FOCUS. W-PROV-01 (provenance) -> "Output comparison".
    from space.reviewer_state import Status, build_reviewer_state
    state = build_reviewer_state(_payload("cou2"), GLOSS)
    oc = next(f for f in state.factors if f.name == "Output comparison")
    assert oc.status is Status.NOT_STATED
    assert "W-PROV-01" in oc.targeting_weakeners
    assert "Relates to: Output comparison" in _html("cou2")


@pytest.mark.parametrize("cou", ["cou1", "cou2"])
def test_authenticity_is_honest_about_unsigned_demo(cou):
    html = _html(cou)
    assert "Unverified (demo)" in html
    assert "uofa check" in html


# ── golden snapshots (regenerate via fixtures/_generate.py) ──

@pytest.mark.parametrize("cou", ["cou1", "cou2"])
def test_golden_snapshot_matches(cou):
    golden = (_FIX / f"morrison_{cou}_reviewer.html").read_text(encoding="utf-8")
    assert _html(cou) == golden

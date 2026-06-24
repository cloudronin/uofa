"""Reviewer-view render tests against the deterministic Morrison fixture."""

from __future__ import annotations

import json
from pathlib import Path

from space.gloss import load_gloss
from space.reviewer import render_reviewer_html

_FIXTURE = Path(__file__).with_name("fixtures") / "morrison_analysis.json"


def _analysis() -> dict:
    return json.loads(_FIXTURE.read_text(encoding="utf-8"))


def test_all_six_sections_render_in_order():
    html = render_reviewer_html(_analysis(), load_gloss())
    headings = [
        "<h2>What this model was used for</h2>",
        "<h2>At a glance</h2>",
        "<h2>Credibility factors</h2>",
        "<h2>Concerns found</h2>",
        "<h2>What is still missing</h2>",
        "<h2>Authenticity</h2>",
    ]
    positions = [html.find(h) for h in headings]
    assert all(p != -1 for p in positions), positions
    assert positions == sorted(positions)  # in order


def test_plain_language_not_raw_ids():
    html = render_reviewer_html(_analysis(), load_gloss())
    # The gloss plain_name appears; the COU lead carries no jargon code.
    assert "Is the model built right for this use" in html      # gloss for "Model form"
    assert "Cardiopulmonary bypass support" in html             # COU in plain words
    assert "ASME V&amp;V 40" in html                            # standard shown (HTML-escaped &)


def test_at_a_glance_five_values():
    html = render_reviewer_html(_analysis(), load_gloss())
    assert "Completeness" in html and "85%" in html            # 11/13 in-scope -> 85%
    assert "11 of 13" in html                                   # factors evidenced
    assert "1 High" in html and "1 Medium" in html              # weakeners by severity
    assert "Authenticity verified" in html and "No (unsigned demo)" in html
    assert "Gate checks passed" in html


def test_no_holistic_verdict_but_keeps_indicative_line():
    html = render_reviewer_html(_analysis(), load_gloss())
    assert "Indicative summary, not a formal acceptance decision." in html
    # No accept/reject stamp.
    assert "Accepted" not in html and "Not accepted" not in html
    assert "trustworthy" not in html.lower()


def test_missing_and_concerns_populated():
    html = render_reviewer_html(_analysis(), load_gloss())
    # "Use error" is missing -> its gloss plain_name shows in the missing list.
    assert "Was the tool used correctly" in html
    # The High weakener's plain "why" line shows.
    assert "limited relevance to the stated context of use" in html


def test_authenticity_is_honest_about_unsigned_demo():
    html = render_reviewer_html(_analysis(), load_gloss())
    assert "Unverified (demo)" in html
    assert "uofa check" in html  # how a real package is re-verified


def test_factors_table_lists_every_expected_factor():
    from space.summary import expected_factors

    html = render_reviewer_html(_analysis(), load_gloss())
    gloss = load_gloss()
    for name in expected_factors("vv40"):
        assert gloss[name]["plain_name"] in html


def test_print_button_present_for_pdf():
    html = render_reviewer_html(_analysis(), load_gloss())
    assert 'onclick="window.print()"' in html
    assert 'id="ri-reviewer-host"' in html  # the @media print isolation target

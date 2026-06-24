"""Reviewer-view render tests against the deterministic Morrison COU2 fixture."""

from __future__ import annotations

import json
from pathlib import Path

from space.gloss import load_gloss
from space.reviewer import render_reviewer_html

_FIXTURES = Path(__file__).with_name("fixtures")
_FIXTURE = _FIXTURES / "morrison_analysis.json"
_GOLDEN = _FIXTURES / "morrison_reviewer.html"


def _analysis() -> dict:
    return json.loads(_FIXTURE.read_text(encoding="utf-8"))


def _html() -> str:
    return render_reviewer_html(_analysis(), load_gloss())


def test_all_six_sections_render_in_order():
    html = _html()
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
    html = _html()
    assert "Is the model built right for this use" in html      # gloss for "Model form"
    assert "Ventricular assist device support" in html          # COU2 in plain words
    assert "ASME V&amp;V 40" in html                            # standard shown (HTML-escaped &)


def test_at_a_glance_five_values():
    html = _html()
    assert "Completeness" in html and "55%" in html             # 6/11 in-scope -> 55%
    assert "6 of 13" in html                                     # factors evidenced (of all)
    assert "1 Critical, 1 High, 1 Moderate" in html             # weakeners by severity
    assert "Authenticity verified" in html and "No (unsigned demo)" in html
    assert "Gate checks passed" in html and "2 of 2" in html     # structural + completeness pass


def test_completeness_and_missing_no_longer_contradict():
    # Fix 1: the % is over all factors; the reconcile clause ties it to the same
    # "required" data the missing-line uses, so they read as one story.
    html = _html()
    assert "55% of all factors evidenced" in html
    assert "all factors required at Level 5 are accounted for" in html
    assert "Nothing required is missing" in html  # missing-line, same source (missing == [])


def test_scoped_out_renders_not_applicable_not_omission():
    # Fix 2: scoped-out factors are a decision, not an omission.
    html = _html()
    assert "Not applicable" in html              # the new label for excluded factors
    assert "Scoped out / N/A" not in html        # old label gone
    # Genuinely-unaddressed (absent) factors still read "Not stated".
    assert "Not stated" in html


def test_severity_word_single_source():
    # Fix 3: at-a-glance count and concern lines use ONE word for medium severity.
    html = _html()
    assert "1 Moderate" in html        # at-a-glance count
    assert "Moderate concern" in html  # concern line
    assert "Medium" not in html        # never the raw key


def test_no_holistic_verdict_but_keeps_indicative_line():
    html = _html()
    assert "Indicative summary, not a formal acceptance decision." in html
    assert "Accepted" not in html and "Not accepted" not in html
    assert "trustworthy" not in html.lower()


def test_concern_why_line_present():
    html = _html()
    assert "limited relevance to the long-duration context of use" in html


def test_authenticity_is_honest_about_unsigned_demo():
    html = _html()
    assert "Unverified (demo)" in html
    assert "uofa check" in html


def test_factors_table_lists_every_expected_factor():
    from space.summary import expected_factors

    html = _html()
    gloss = load_gloss()
    for name in expected_factors("vv40"):
        assert gloss[name]["plain_name"] in html


def test_reviewer_host_is_the_print_target():
    assert 'id="ri-reviewer-host"' in _html()


def test_golden_snapshot_matches():
    # Regenerate with: render the fixture and write tests/space/fixtures/morrison_reviewer.html
    assert _html().strip() == _GOLDEN.read_text(encoding="utf-8").strip()

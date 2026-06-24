"""P1 UX-polish tests — copy/structure guards that don't need a browser."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("gradio")

from space import app

_SPACE_DIR = Path(__file__).resolve().parents[2] / "space"
_APP_SRC = (_SPACE_DIR / "app.py").read_text()


def test_no_em_dash_anywhere_in_space_package():
    # Scan every module (not just app.py) — the router/pipeline produce
    # user-facing strings too, and that's where an em dash slipped through once.
    offenders = [p.name for p in _SPACE_DIR.glob("*.py") if "—" in p.read_text()]
    assert not offenders, f"em dash present in: {offenders}"


def test_step_tag_format():
    assert "Step 2 of 4 · Confirm standard" in app._step_tag(2, "Confirm standard")


def test_factor_label_shows_levels_only_when_below_required():
    equal = app._factor_label({"factor_type": "Model form", "status": "assessed",
                               "required_level": 3, "achieved_level": 3})
    assert "needs L" not in equal           # no noise when achieved == required
    assert "assessed" in equal

    gap = app._factor_label({"factor_type": "Use error", "status": "assessed",
                             "required_level": 3, "achieved_level": 1})
    assert "needs L3, has L1" in gap          # surfaced only when it's a shortfall


def test_issue_phrase_pluralizes():
    assert app._issue_phrase(1) == "1 issue found"
    assert app._issue_phrase(2) == "2 issues found"
    assert app._issue_phrase(0) == "0 issues found"


def test_headline_wrap_css_present():
    # Long gaps-led headline must wrap, not clip, at narrow widths.
    assert "overflow-wrap: anywhere" in app.CSS


def test_footer_hidden_and_theme_transparent():
    assert "footer { display: none" in app.CSS
    assert app.THEME is not None
    # The API page is closed via queue(api_open=False) in Gradio 6.
    assert "api_open=False" in _APP_SRC


def test_upload_copy_is_plural():
    assert "several files" in _APP_SRC
    assert 'file_count="multiple"' in _APP_SRC


def test_capture_panel_echoes_privacy():
    assert "Your evidence is not stored" in _APP_SRC

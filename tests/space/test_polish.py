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


# ── disclosure: the copy must match the backend actually in use ──
#
# Added when inference moved to a hosted provider. The Space's pre-upload note
# is the last thing a user reads before handing over documents, and there are
# three copies of the same promise (app.py, pipeline.py, the site page) that
# have to move together.


def test_local_note_claims_privacy_and_remote_note_does_not(monkeypatch):
    from space import app, llm_env
    from uofa_cli.llm.config import LLMConfig

    monkeypatch.setattr(app, "_LLM_CONFIG", None)
    local = app._cold_start_note()
    assert "privately inside this Space" in local
    assert "not sent to a third party" in local or "nothing is sent" in local.lower()

    remote = LLMConfig(backend="openai-compatible", model="m",
                       base_url="https://api.example.com/v1", api_key_env="K")
    monkeypatch.setattr(app, "_LLM_CONFIG", remote)
    note = app._cold_start_note()
    assert "privately" not in note.lower(), "claims privacy while sending text off-box"
    assert "api.example.com" in note, "must name where the documents go"
    assert "do not upload it here" in note.lower(), "must give the confidential-evidence answer"
    assert "stores nothing" in note.lower(), "the true storage claim should survive"


def test_in_flight_message_tracks_the_backend():
    from space import pipeline
    from uofa_cli.llm.config import LLMConfig

    assert "privately" in pipeline._reading_message(None)
    remote = LLMConfig(backend="openai-compatible", model="m",
                       base_url="https://api.example.com/v1", api_key_env="K")
    msg = pipeline._reading_message(remote)
    assert "privately" not in msg.lower()
    assert "api.example.com" in msg


def test_extraction_label_names_the_provider():
    """Rendered as "How assessed:" and carried in the payload, so the disclosure
    survives into the artifact rather than living only on the upload page."""
    from space import pipeline
    from uofa_cli.llm.config import LLMConfig

    assert "local" in pipeline.extraction_label(None)
    remote = LLMConfig(backend="openai-compatible", model="llama-x",
                       base_url="https://api.example.com/v1", api_key_env="K")
    label = pipeline.extraction_label(remote)
    assert "llama-x" in label and "api.example.com" in label


def test_demo_page_and_readme_disclose_transmission():
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    for rel in ("space/README.md", "site/src/content/docs/demo/index.mdx"):
        body = (root / rel).read_text(encoding="utf-8")
        assert "leave" in body.lower(), f"{rel} does not say documents leave"
        assert "confidential" in body.lower(), f"{rel} lacks the confidential-evidence steer"
        assert "no third-party" not in body.lower(), f"{rel} still claims no third party"

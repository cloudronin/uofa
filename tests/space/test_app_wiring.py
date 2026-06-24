"""S2 app-wiring tests — handler output arity must match each `outputs` list.

A Gradio handler that returns the wrong number of values silently misaligns
component updates at runtime (not at build). These tests pin the arities and
drive the handlers with the mock model so the wiring is exercised end to end
without launching a browser.
"""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("gradio")

from space import app, wizard

# Declared outputs arity for each handler (kept in lockstep with build()).
N_PREPARE = 12
N_EXTRACT = 8
N_FINALIZE = 11      # +reviewer_html, +view_toggle/author_panel/reviewer_panel (this handler owns the view)
N_START_OVER = 25    # groups + read/extract progress + cleared content surfaces + states + view


@pytest.fixture(autouse=True)
def _mock_model(monkeypatch):
    monkeypatch.setattr(app, "_MODEL", "mock")


def _src(tmp_path: Path, text="ASME V&V 40 context of use, model risk.") -> Path:
    d = tmp_path / "src"
    d.mkdir(exist_ok=True)
    (d / "evidence.txt").write_text(text, encoding="utf-8")
    return d


def test_detect_empty_yields_prepare_arity():
    outs = list(app._detect_from_upload([]))
    assert outs and all(len(o) == N_PREPARE for o in outs)


def test_stream_prepare_arity_and_reveals_route(tmp_path):
    outs = list(app._stream_prepare([_src(tmp_path)], "upload"))
    assert all(len(o) == N_PREPARE for o in outs)
    # Final tuple reveals the route group (index 2 visible=True).
    final = outs[-1]
    assert final[2]["visible"] is True


def test_run_extract_arity_and_reveals_confirm(tmp_path):
    prep = wizard.prepare([_src(tmp_path)])
    corpus = prep.payload["corpus"]
    outs = list(app._run_extract(corpus, "vv40"))
    assert all(len(o) == N_EXTRACT for o in outs)
    final = outs[-1]
    assert final[2]["visible"] is True  # confirm_group shown
    assert isinstance(final[6], dict) and final[6]  # status_state seeded


def test_finalize_arity_success_and_failure(tmp_path):
    prep = wizard.prepare([_src(tmp_path)])
    ext = wizard.extract(prep.payload["corpus"], "vv40", model="mock")
    result = ext.payload["result"]

    ok = app._finalize(result, "vv40", {"Use error": "not-assessed"}, [], "upload")
    assert len(ok) == N_FINALIZE
    assert ok[1]["visible"] is True  # summary_group shown
    # Author panels unchanged (engine/author regression): completeness in the tail
    # panel, weakeners/not-assessed before it.
    assert "12 of 13" in ok[5]["value"]
    assert isinstance(ok[6], dict) and ok[6]["completeness"]["n_assessed"] == 12  # summary_state
    assert ok[6]["context"]["authenticity"]["signed"] is False  # context attached, unsigned demo
    assert "Weakeners" in ok[4]["value"] or "Not assessed" in ok[4]["value"]
    assert "Completeness" in ok[5]["value"]
    # New reviewer view rendered off the same payload (index 7).
    assert "ri-reviewer" in ok[7]["value"] and "At a glance" in ok[7]["value"]

    # None result -> finalize fails gracefully, still correct arity.
    bad = app._finalize(None, "vv40", {}, [], "upload")
    assert len(bad) == N_FINALIZE
    assert bad[2]["visible"] is True  # error_md shown
    assert bad[6] is None  # no summary on failure


def test_pdf_print_js_targets_reviewer_host():
    # Save-as-PDF clones #ri-reviewer-host into a standalone white print window.
    assert "ri-reviewer-host" in app._PRINT_JS
    assert "window.open(" in app._PRINT_JS
    assert "color:#111" in app._PRINT_JS  # ink-friendly


def test_switch_view_flips_visibility_only():
    # Reviewer default: author hidden, reviewer shown. No pipeline work.
    author, reviewer = app._switch_view("Reviewer")
    assert author["visible"] is False and reviewer["visible"] is True
    author, reviewer = app._switch_view("Author (Gap-Finder)")
    assert author["visible"] is True and reviewer["visible"] is False


def test_capture_glue(monkeypatch):
    from space.leadcapture import CaptureResult

    monkeypatch.setattr(app.leadcapture, "capture_lead",
                        lambda *a, **k: CaptureResult(False, "invalid", "bad"))
    assert "valid" in app._capture("nope", "vv40", None)["value"].lower()

    monkeypatch.setattr(app.leadcapture, "capture_lead",
                        lambda *a, **k: CaptureResult(True, "dataset", "stored"))
    good = app._capture("user@org.com", "vv40", {"completeness": {}})
    assert good["visible"] is True
    assert "not stored" in good["value"].lower()  # evidence-privacy reassurance


def test_start_over_arity():
    assert len(app._start_over()) == N_START_OVER


def test_start_over_blanks_content_not_just_groups():
    # Start over must clear the result surfaces (reviewer HTML, author markdowns,
    # picked file), not only hide the step groups — otherwise a stale report
    # shows through. Asserts every gr.update among the returns that carries a
    # value sets it to empty/None (no leftover text).
    outs = app._start_over()
    cleared = [o for o in outs if isinstance(o, dict) and "value" in o and o.get("value")]
    # The only non-empty value Start over sets is the view toggle default.
    assert all(o.get("value") == "Reviewer" for o in cleared), cleared

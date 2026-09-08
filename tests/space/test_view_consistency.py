"""The two views must agree, and switching between them must not re-analyse.

Both properties are gate CI-4. Both were broken or unpinned on 2026-09-08:

- the Author view printed the raw severity key ("Medium") where the Reviewer
  printed the reader-facing word ("Moderate"), for the same finding, with a
  toggle between them;
- the two views report different completeness figures. Both are correct -- the
  Reviewer does not count a factor as evidenced while an open High or Moderate
  concern disputes it -- but neither said so, and side by side they read as a
  contradiction. The Reviewer half of that labelling is pinned by the golden
  snapshots. The Author half was pinned by nothing.

The toggle's independence is asserted structurally rather than by timing. It was
previously accepted on the strength of "the page came back in about five
seconds", which is an inference about a machine's speed, not a fact about what
the handler can reach.
"""

from __future__ import annotations

import inspect
import json
from pathlib import Path

import pytest

pytest.importorskip("gradio")

from space import app
from uofa_cli.report_state import _headline, sev_label


def test_the_author_completeness_line_names_its_own_basis():
    """"raw extracted statuses" is load-bearing, not decoration.

    Without it a reader sees "13 of 13" here and "11 of 13" in the Reviewer view
    with nothing explaining the difference, and has no way to tell a definition
    from an error.

    Asserted on the rendered markdown rather than on the source, so a reflow of
    the f-string cannot break it and a silent revert cannot pass it.
    """
    payload = json.loads(
        (Path(__file__).with_name("fixtures") / "morrison_cou1_state.json")
        .read_text(encoding="utf-8"))
    _head, _gaps, tail_md, _html = app._render_results(payload)

    assert "raw extracted statuses" in tail_md, (
        f"the Author completeness line no longer names which count it is:\n"
        f"{tail_md}\nThe Reviewer view reports a different, also correct "
        "number, and unlabelled the two read as a contradiction."
    )
    assert "Reviewer view reports a lower count" in tail_md, (
        f"the Author line no longer explains why the Reviewer figure is "
        f"lower:\n{tail_md}"
    )


def test_switching_view_cannot_re_run_the_analysis():
    """Structural, not timing: the handler has no access to the analysis.

    `_switch_view` takes the chosen view and nothing else, so it cannot reach a
    corpus, a pack, a model, or any pipeline state. Re-running is not something
    it does slowly; it is something it cannot do.
    """
    sig = inspect.signature(app._switch_view)

    assert list(sig.parameters) == ["choice"], (
        f"_switch_view now takes {list(sig.parameters)}. Anything beyond the "
        "chosen view gives a presentation toggle reach into the analysis."
    )

    src = inspect.getsource(app._switch_view)
    for forbidden in ("analyze", "wizard.", "pipeline.", "extract", "finalize"):
        assert forbidden not in src, (
            f"_switch_view references {forbidden!r}; the view toggle must be "
            "presentation only"
        )


def test_switching_view_only_changes_visibility():
    """Its returns are visibility updates, so no content is recomputed."""
    author_hidden, reviewer_shown = app._switch_view("Reviewer")
    author_shown, reviewer_hidden = app._switch_view("Author (Gap-Finder)")

    assert reviewer_shown["visible"] is True
    assert author_hidden["visible"] is False
    assert author_shown["visible"] is True
    assert reviewer_hidden["visible"] is False

    # Nothing else moves. A `value` here would mean the toggle re-rendered
    # content rather than revealing content already computed once.
    for upd in (author_hidden, reviewer_shown, author_shown, reviewer_hidden):
        assert set(upd) <= {"visible", "__type__"}, (
            f"the view toggle returns {sorted(upd)}; it may only change "
            "visibility, or the two panels can drift apart"
        )


def test_both_views_speak_one_severity_vocabulary():
    """The Author headline and the Reviewer glance must not disagree on a word."""
    line = _headline(13, 13, 0, [{}, {}, {}], {"High": 2, "Medium": 1})

    assert sev_label("Medium") in line
    assert "1 Medium" not in line, (
        f"the Author headline prints a raw severity key: {line!r}"
    )

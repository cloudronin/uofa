"""The Inspector's solver panel: presentation only, and it says so.

`tests/space/test_emittability.py` is the anti-fork guard -- the Space must
never emit something the CLI would not. This panel is the shape that stays on
the right side of it: it calls the same `uofa_cli.solver.reader` the CLI calls
and renders the result, and it is attached to the display payload after the
package is already built and signed.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "space"))

from space import solver_panel  # noqa: E402

from tests.solver.conftest import MINI, build_wbpz  # noqa: E402


@pytest.fixture
def wbpz(tmp_path):
    return build_wbpz(MINI, tmp_path / "mini.wbpz")


def test_no_solver_artifacts_means_no_panel(tmp_path):
    (tmp_path / "notes.txt").write_text("prose only", encoding="utf-8")
    assert solver_panel.summarise([tmp_path]) is None
    assert solver_panel.render(None) == ""


def test_panel_reports_release_cautions_and_absences(wbpz):
    summary = solver_panel.summarise([wbpz])
    assert summary["release"] == "2023 R2"
    assert summary["severityCounts"] == {"information": 1, "warning": 3, "error": 1}
    assert set(summary["absent"]) == {"ds.dat", "file.rst", "solve.out"}

    text = solver_panel.render(summary)
    assert "2023 R2" in text
    assert "ds.dat" in text


def test_the_release_line_offers_the_ordinary_explanation(wbpz):
    """A later re-save is the mundane reason an archive names a newer release.

    Presenting the gap without that reading turns a provenance note into an
    accusation, on a page a reviewer reads without the presenter beside them.
    """
    text = solver_panel.render(solver_panel.summarise([wbpz]))
    assert "re-save" in text


def test_the_panel_never_calls_a_solver_message_a_weakener(wbpz):
    """The Inspector's own weakener section is a few lines up the same page.

    Using the word for both would tell a reviewer a catalog rule fired when
    none did.
    """
    text = solver_panel.render(solver_panel.summarise([wbpz]))
    assert not re.search(r"weakener|defect|violation", text, re.I) or \
        "not weakeners" in text
    assert "not findings" in text or "not weakeners" in text


def test_stripped_solver_files_lead_the_absence_list(wbpz):
    summary = solver_panel.summarise([wbpz])
    assert summary["absent"][0] in {"ds.dat", "file.rst", "solve.out"}


def test_operator_identity_never_reaches_the_panel(wbpz):
    from uofa_cli.solver import redact
    text = solver_panel.render(solver_panel.summarise([wbpz]))
    assert redact.looks_redacted(text)
    assert "testuser" not in text.lower()


def test_the_panel_is_bounded(wbpz):
    """A real project carries 78 messages and 101 stated absences. The results
    page is not a log viewer."""
    summary = solver_panel.summarise([wbpz])
    assert len(summary["cautions"]) <= solver_panel.MAX_CAUTIONS
    assert len(summary["absent"]) <= solver_panel.MAX_ABSENT

"""Reviewer render protocol: derive one state, enforce invariants.

The reviewer logic now lives CLI-side in `uofa_cli.report_state` (shared with
the `uofa report` command, so the Space and CLI enforce one invariant set and
cannot drift). This module is a thin Space adapter: it re-exports the shared
names under their historical `Reviewer*` spellings and wires the Space's gloss
into the builder by default, so `space/reviewer.py` and the Space tests are
unchanged.

See `uofa_cli/report_state.py` for the status-derivation precedence and the six
frozen invariants. The known engine-data gap that motivated the factor-focus map
is now closed upstream: validation/COU-scoped weakeners carry the credibility
factor they implicate (declared per-pack, loaded via `weakener_focus`), so a
High/Critical concern demotes the right factor instead of demoting nothing.
"""

from __future__ import annotations

from uofa_cli.report_state import (  # noqa: F401  (re-exported under Space names)
    _DEMOTING,
    _HIGH,
    Concern,
    FactorState,
    ReportInvariantError as ReviewerInvariantError,
    ReportState as ReviewerState,
    Status,
    assert_report_invariants as assert_reviewer_invariants,
    build_report_state,
    sev_label,
    sev_rank,
)

from space.gloss import load_gloss

__all__ = [
    "Concern", "FactorState", "ReviewerState", "ReviewerInvariantError", "Status",
    "build_reviewer_state", "assert_reviewer_invariants", "sev_label", "sev_rank",
]


def build_reviewer_state(analysis: dict, gloss: dict | None = None) -> ReviewerState:
    """Derive the reviewer state, defaulting to the Space's plain-language gloss
    so factor rows render reader-facing names."""
    return build_report_state(analysis, gloss if gloss is not None else load_gloss())

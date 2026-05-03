"""Tests for the animated CLI spinner in `uofa_cli.output`."""

from __future__ import annotations

import io
import sys
import time

import pytest

from uofa_cli.output import noop_spinner, spinner


class _FakeTTY(io.StringIO):
    """StringIO that reports as a TTY so the spinner actually animates."""

    def isatty(self) -> bool:
        return True


def test_spinner_no_op_on_non_tty(monkeypatch):
    """Pipe-redirected stderr (the common CI / log case) should silently
    no-op so the spinner doesn't pollute logs with carriage-return junk."""
    buf = io.StringIO()  # plain StringIO; isatty() returns False
    monkeypatch.setattr(sys, "stderr", buf)
    with spinner("anything"):
        time.sleep(0.05)
    assert buf.getvalue() == ""


def test_spinner_animates_on_tty(monkeypatch):
    """In TTY mode, the spinner thread should write SOMETHING with the
    label before the body completes."""
    buf = _FakeTTY()
    monkeypatch.setattr(sys, "stderr", buf)
    with spinner("loading thing"):
        # Sleep long enough for at least 2 frames to be drawn.
        time.sleep(0.25)
    output = buf.getvalue()
    assert "loading thing" in output
    # \r is the per-frame overwrite marker
    assert "\r" in output
    # cleanup should have written the cursor-restore sequence
    assert "\033[?25h" in output


def test_spinner_cleans_up_on_exception(monkeypatch):
    """An exception in the with-body should still clear the line + restore
    the cursor (otherwise terminals end up stuck with a hidden cursor)."""
    buf = _FakeTTY()
    monkeypatch.setattr(sys, "stderr", buf)
    with pytest.raises(RuntimeError, match="boom"):
        with spinner("about to die"):
            time.sleep(0.1)
            raise RuntimeError("boom")
    output = buf.getvalue()
    assert "\033[?25h" in output  # cursor restored
    # The cleanup writes a clearing sequence (spaces) — line should not end
    # with the spinner label still visible without overwrite.
    assert output.rstrip().endswith("\033[?25h")


def test_noop_spinner_produces_no_output(monkeypatch):
    """noop_spinner is the dataclass default — must be silent regardless of TTY."""
    buf = _FakeTTY()
    monkeypatch.setattr(sys, "stderr", buf)
    with noop_spinner("loud label"):
        pass
    assert buf.getvalue() == ""


def test_spinner_thread_joins_within_timeout(monkeypatch):
    """The animator thread is daemon=True but we still join() to make sure
    cleanup completes before the with-block returns. Verify by checking
    that no further frames are written after exit."""
    buf = _FakeTTY()
    monkeypatch.setattr(sys, "stderr", buf)
    with spinner("brief"):
        time.sleep(0.15)
    snapshot = buf.getvalue()
    # Sleep beyond a frame interval; if the thread is still running it
    # would write more.
    time.sleep(0.25)
    assert buf.getvalue() == snapshot

"""ANSI color helpers and formatted output for the UofA CLI."""

from __future__ import annotations

import os
import sys
import threading
import time
from contextlib import contextmanager
from typing import Iterator

# ── Color support detection ──────────────────────────────────

def _color_enabled():
    if os.environ.get("NO_COLOR"):
        return False
    if not hasattr(sys.stdout, "isatty"):
        return False
    return sys.stdout.isatty()

_USE_COLOR = _color_enabled()


def set_color(enabled: bool):
    """Override color detection (e.g., from --no-color flag)."""
    global _USE_COLOR
    _USE_COLOR = enabled


# ── ANSI codes ───────────────────────────────────────────────

_CODES = {
    "reset":    "\033[0m",
    "bold":     "\033[1m",
    "red":      "\033[1;31m",
    "green":    "\033[32m",
    "yellow":   "\033[33m",
    "cyan":     "\033[36m",
    "dim":      "\033[37m",
    "header":   "\033[1;37m",
}

_SEVERITY_COLORS = {
    "Critical": "red",
    "High":     "yellow",
    "Medium":   "cyan",
    "Low":      "dim",
}


def color(text: str, name: str) -> str:
    if not _USE_COLOR:
        return text
    code = _CODES.get(name, "")
    reset = _CODES["reset"]
    return f"{code}{text}{reset}"


def severity_badge(sev: str) -> str:
    color_name = _SEVERITY_COLORS.get(sev, "dim")
    return color(f"[{sev}]", color_name)


# ── Structured output ────────────────────────────────────────

def header(text: str):
    line = "═" * 56
    print(color(f"\n{line}", "header"))
    print(color(f"  {text}", "header"))
    print(color(line, "header"))


def step_header(text: str):
    print(color(f"\n══ {text} ══", "header"))


def result_line(label: str, ok: bool, detail: str = ""):
    mark = color("✓", "green") if ok else color("✗", "red")
    suffix = f"  {detail}" if detail else ""
    print(f"  {mark} {label}{suffix}")


def error(msg: str):
    print(color(f"Error: {msg}", "red"), file=sys.stderr)


def warn(msg: str):
    print(color(f"Warning: {msg}", "yellow"), file=sys.stderr)


def info(msg: str):
    print(f"  {msg}")


def muted(text: str) -> str:
    return color(text, "dim")


def diamond() -> str:
    return color("◆", "yellow")


# ── Table output ────────────────────────────────────────────

def table_separator(widths: list[int]):
    parts = ["─" * w for w in widths]
    print(f"  ├─{'─┼─'.join(parts)}─┤")


def table_header(columns: list[str], widths: list[int]):
    cells = [c.center(w) for c, w in zip(columns, widths)]
    border = "─" * sum(w + 3 for w in widths)
    print(f"  ┌{border}─┐")
    print(f"  │ {' │ '.join(cells)} │")
    table_separator(widths)


def table_row(cells: list[str], widths: list[int], highlight: bool = False):
    padded = []
    for cell, w in zip(cells, widths):
        # Strip ANSI to compute visible length for padding
        visible = _strip_ansi(cell)
        pad = w - len(visible)
        padded.append(cell + " " * max(pad, 0))
    line = f"  │ {' │ '.join(padded)} │"
    if highlight:
        print(color(line, "yellow"))
    else:
        print(line)


def table_footer(widths: list[int]):
    parts = ["─" * w for w in widths]
    print(f"  └─{'─┴─'.join(parts)}─┘")


def _strip_ansi(text: str) -> str:
    import re
    return re.sub(r'\033\[[0-9;]*m', '', text)


# ── Spinner (for blocking operations like LLM calls) ────────


_SPINNER_FRAMES = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
_SPINNER_INTERVAL_S = 0.08


@contextmanager
def spinner(label: str = "") -> Iterator[None]:
    """Animated braille spinner during a blocking operation.

    Writes to stderr with carriage-return overwrites; cleans up the line
    on exit (including on exception). No-op when stderr is not a TTY so
    piped/redirected output stays clean.

    Sequential use only — concurrent spinners would interleave \\r writes.
    """
    if not (hasattr(sys.stderr, "isatty") and sys.stderr.isatty()):
        yield
        return

    stop = threading.Event()

    def animate() -> None:
        sys.stderr.write("\033[?25l")  # hide cursor
        try:
            i = 0
            while not stop.is_set():
                frame = _SPINNER_FRAMES[i % len(_SPINNER_FRAMES)]
                sys.stderr.write(f"\r  {frame} {label}")
                sys.stderr.flush()
                i += 1
                time.sleep(_SPINNER_INTERVAL_S)
        finally:
            # Clear the line and restore the cursor regardless of how we exit.
            clear = "\r" + " " * (len(label) + 4) + "\r"
            sys.stderr.write(clear + "\033[?25h")
            sys.stderr.flush()

    t = threading.Thread(target=animate, daemon=True)
    t.start()
    try:
        yield
    finally:
        stop.set()
        t.join(timeout=0.5)


@contextmanager
def noop_spinner(label: str = "") -> Iterator[None]:  # noqa: ARG001
    """No-op stand-in for `spinner` — used as the pipeline's default."""
    yield

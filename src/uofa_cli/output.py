"""ANSI color helpers and formatted output for the UofA CLI."""

import os
import sys

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

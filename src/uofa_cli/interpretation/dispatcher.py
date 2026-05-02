"""Function applicability dispatcher (spec v0.4 §4.2).

Each interpretation function declares which command outputs it applies to via
`@applies_to_commands(...)`. The dispatcher consults that declaration to skip
inapplicable functions silently — the matrix in spec §2.6 is the source of
truth, encoded right next to each function so a future addition is
self-documenting.

Functions are also keyed by their canonical short name (`explain`, `group`,
`contextualize`, `cross`, `narrative`) so `--explain-functions explain,group`
on the command line can pick a subset.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

# Spec §2.6 enumerates exactly five function names.
KNOWN_FUNCTIONS = ("explain", "group", "contextualize", "cross", "narrative")
KNOWN_COMMANDS = ("rules", "check", "diff", "shacl")


@dataclass
class _RegisteredFunction:
    name: str
    applies_to: tuple[str, ...]
    fn: Callable


# Module-level registry. Population happens at import time of the
# `functions/` modules; the dispatcher reads from it.
_REGISTRY: dict[str, _RegisteredFunction] = {}


def applies_to_commands(*commands: str) -> Callable:
    """Decorator: tag an interpretation function with the commands it serves.

    Usage:
        @applies_to_commands("rules", "check")
        def cross_pattern_recognition(structured_output, package, options):
            ...

    The function's `__name__` becomes the canonical short name (must be one
    of `KNOWN_FUNCTIONS`). Registration happens at import time — if the
    function module isn't imported, dispatch ignores it.

    Raises:
        ValueError: if any command isn't in `KNOWN_COMMANDS` (typo guard).
    """
    invalid = set(commands) - set(KNOWN_COMMANDS)
    if invalid:
        raise ValueError(
            f"applies_to_commands: unknown commands {sorted(invalid)}. "
            f"Allowed: {KNOWN_COMMANDS}"
        )

    def _wrap(fn: Callable) -> Callable:
        name = _short_name_from_function(fn)
        _REGISTRY[name] = _RegisteredFunction(
            name=name,
            applies_to=tuple(commands),
            fn=fn,
        )
        return fn

    return _wrap


def _short_name_from_function(fn: Callable) -> str:
    """Map a function name like `cross_pattern_recognition` to its canonical
    short form. Each KNOWN_FUNCTIONS entry must be a substring of exactly
    one registered function — gives implementations human-readable names
    while keeping the CLI surface compact."""
    fname = fn.__name__
    matches = [n for n in KNOWN_FUNCTIONS if n in fname]
    if len(matches) != 1:
        raise ValueError(
            f"Function {fname!r} must contain exactly one of "
            f"{KNOWN_FUNCTIONS} in its name; got matches={matches}."
        )
    return matches[0]


def applicable_functions(command: str, requested: list[str] | None = None) -> list[_RegisteredFunction]:
    """Return registered functions that apply to *command*, optionally
    filtered to the names in *requested*.

    *requested* may be None or `["all"]` to mean "everything applicable".
    Unknown names in *requested* raise ValueError so a typo on the CLI
    doesn't silently drop a function.
    """
    if command not in KNOWN_COMMANDS:
        raise ValueError(f"Unknown command: {command!r}. Allowed: {KNOWN_COMMANDS}")

    selected: set[str] | None = None
    if requested is not None and requested != ["all"] and "all" not in requested:
        unknown = set(requested) - set(KNOWN_FUNCTIONS)
        if unknown:
            raise ValueError(
                f"Unknown interpretation functions: {sorted(unknown)}. "
                f"Allowed: {KNOWN_FUNCTIONS}"
            )
        selected = set(requested)

    out: list[_RegisteredFunction] = []
    for name in KNOWN_FUNCTIONS:  # iterate in canonical order, not registry order
        rf = _REGISTRY.get(name)
        if rf is None:
            continue
        if command not in rf.applies_to:
            continue
        if selected is not None and name not in selected:
            continue
        out.append(rf)
    return out


def reset_registry() -> None:
    """Clear the registry. Test-only — production code never calls this."""
    _REGISTRY.clear()


def registered_function_names() -> list[str]:
    """Return all currently-registered function short names. For diagnostics."""
    return sorted(_REGISTRY)

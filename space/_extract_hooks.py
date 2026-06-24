"""Test-only `extract_fn` stand-ins for exercising pipeline failure paths.

These live in a real importable module (not a test file) so they survive the
multiprocessing "spawn" pickling that `analyze`'s subprocess extraction uses -
spawn re-imports the target by module path in the child interpreter.
"""

from __future__ import annotations

import time


def slow_extract(*_args, **_kwargs):
    """Outlive any sane test timeout, to trigger the extract-timeout path."""
    time.sleep(3600)


def failing_extract(*_args, **_kwargs):
    """Raise inside the child, to trigger the extract-error path."""
    raise RuntimeError("simulated extraction failure")


def empty_extract(*_args, **_kwargs):
    """Return an ExtractionResult with no factors, to trigger empty_factors."""
    from uofa_cli.llm_extractor import ExtractionResult

    return ExtractionResult()

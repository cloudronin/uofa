"""Test-suite-wide fixtures.

Currently provides:
- `_isolate_explain_cache` (autouse): redirects the interpretation cache
  to a per-test tmp dir so cached LLM-result rows from one test never
  leak into another. Without this, tests that run identical mock prompts
  see cache hits and skip backend calls — surfacing as `len(calls) == 0`
  failures.

The fixture is opt-out by yielding without monkeypatching when the
cache module isn't importable (graceful — pre-Phase-N tests still work).
"""

from __future__ import annotations

import pathlib

import pytest


@pytest.fixture(autouse=True)
def _isolate_explain_cache(monkeypatch, tmp_path):
    """Redirect the interpretation cache to a per-test sqlite file.

    Autouse + scope=function (default) so every test gets a fresh DB.
    The override is on `default_db_path()`, so any code that constructs
    `ExplanationCache()` with no args picks up the tmp path.
    """
    try:
        # Use string-based monkeypatch so this still works if the module
        # is rewritten — and so we don't import-fail when the cache module
        # is absent (e.g. pre-Phase-N codepaths or smaller-test runs).
        monkeypatch.setattr(
            "uofa_cli.interpretation.cache.default_db_path",
            lambda: tmp_path / "explain.db",
        )
    except (AttributeError, ModuleNotFoundError):
        pass
    yield


# ── the extracted corpus the pinning tests read ──────────────

_EXTRACTED_JSON = pathlib.Path(__file__).parent / "fixtures" / "extract_corpus" / "extracted_rows.json"


# Moved to `tests/extracted_corpus.py`. `from conftest import ...` is ambiguous
# -- `tests/space/conftest.py` registers under the same bare name -- and in a
# full run the wrong one won, so two tests that passed in isolation failed in CI
# with an ImportError. Re-exported here so nothing that reaches for them breaks.
from extracted_corpus import (  # noqa: E402,F401
    extracted_corpus_by_bundle,
    extracted_corpus_rows,
)
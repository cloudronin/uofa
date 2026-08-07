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


def extracted_corpus_rows() -> list[dict]:
    """Every scored factor row from the extraction run, flattened.

    Read from a committed JSON rather than from `extracted.xlsx`, which is
    gitignored -- correctly, since those are 1.2 MB of binary tied to one paid
    run. But two tests pin exact figures over them (rows == 800,
    claims_grounded == 859), so the coupling to that run already existed in the
    assertions; only the data was missing. In CI the files are absent, every
    loop body was skipped, the totals came out zero, and both tests failed on an
    assertion that said nothing about why.

    Regenerate with dev/tools/scripts/dump_corpus_rows.py where the xlsx exist.
    """
    import json
    if not _EXTRACTED_JSON.exists():
        return []
    data = json.loads(_EXTRACTED_JSON.read_text())
    return [r for bundle in sorted(data) for r in data[bundle]]


def extracted_corpus_by_bundle() -> dict[str, list[dict]]:
    """Same rows, keyed by bundle path, for tests that need the source text."""
    import json
    if not _EXTRACTED_JSON.exists():
        return {}
    return json.loads(_EXTRACTED_JSON.read_text())

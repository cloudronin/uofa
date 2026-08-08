"""The frozen extractor output, in a module with an unambiguous name.

These two helpers lived in `tests/conftest.py` and were reached by
`from conftest import ...`. That import is ambiguous: `tests/space/conftest.py`
also registers under the bare name `conftest`, and when both are collected --
which is every full run, and every CI run -- whichever imports first wins. The
result was `ImportError: cannot import name 'extracted_corpus_by_bundle' from
'conftest' (tests/space/conftest.py)`, in two tests that pass in isolation.

Isolation is what made it survive: `pytest tests/test_groundedness.py` never
collects `tests/space`, so the collision cannot happen, and that is how the test
was run every time it was checked by hand.

The rows are read from a committed JSON rather than from `extracted.xlsx`, which
is gitignored -- correctly, since those are 1.2 MB of binary tied to one paid
run. Two tests pin exact figures over them (rows == 800, claims_grounded == 859),
so the coupling to that run already existed in the assertions; only the data was
missing. Regenerate with `dev/tools/scripts/dump_corpus_rows.py` where the xlsx
exist.
"""
from __future__ import annotations

import json
import pathlib

_EXTRACTED_JSON = (pathlib.Path(__file__).parent / "fixtures" / "extract_corpus"
                   / "extracted_rows.json")


def extracted_corpus_rows() -> list[dict]:
    """Every extracted row, flattened across bundles."""
    if not _EXTRACTED_JSON.exists():
        return []
    data = json.loads(_EXTRACTED_JSON.read_text())
    return [r for bundle in sorted(data) for r in data[bundle]]


def extracted_corpus_by_bundle() -> dict[str, list[dict]]:
    """Same rows, keyed by bundle path, for tests that need the source text."""
    if not _EXTRACTED_JSON.exists():
        return {}
    return json.loads(_EXTRACTED_JSON.read_text())

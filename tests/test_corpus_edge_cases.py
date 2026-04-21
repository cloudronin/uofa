"""Pre-Tester QA Corpus v2 — edge-case reader robustness.

Per UofA_Pre_Tester_QA_Corpus_v2.md §"Edge case handling": every file under
corpus/edge-cases/ must be readable (or gracefully refused) without a
stack trace. User-facing errors must name the file and be actionable.

Prerequisite: build the corpus first via `make corpus` (optional deps
[corpus] must be installed). These tests importorskip when the optional
dependency chain is missing so CI without the deps sees them skip cleanly
rather than error.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
EDGE_DIR = REPO_ROOT / "corpus" / "edge-cases"

# Optional deps guard — exercised reader paths depend on these.
pytest.importorskip("openpyxl")

# The document_reader imports pdfplumber lazily; without it the PDF cases
# skip. CSV / XLSX / TXT cases don't need it.
_HAS_PDFPLUMBER = False
try:
    import pdfplumber  # noqa: F401
    _HAS_PDFPLUMBER = True
except ImportError:
    pass


# (filename, kind) — "kind" selects the expected-behavior shape.
# "chunks"  → reader returns text chunks, 0 warnings.
# "warn"    → reader returns chunks==0 and surfaces an actionable warning.
# "graceful" → reader returns any mix, must not crash.
EDGE_CASES = [
    ("tiny-note.txt", "chunks"),
    ("csv-with-semicolons.csv", "chunks"),
    ("non-english-headers.xlsx", "chunks"),
    ("merged-cells.xlsx", "chunks"),
    ("multi-sheet-workbook.xlsx", "chunks"),
    ("mixed-encoding.txt", "graceful"),          # chardet fallback may mojibake; must not crash
    ("password-protected.xlsx", "warn"),         # openpyxl refuses; readable warning required
    ("corrupted-file.pdf", "warn"),              # pdfplumber refuses; readable warning required
    ("huge-appendix.pdf", "chunks"),
    ("scanned-report.pdf", "chunks"),            # image-only sentinel chunk still counts
]

PDF_CASES = {"corrupted-file.pdf", "huge-appendix.pdf", "scanned-report.pdf"}


def _skip_reason(filename: str) -> str | None:
    if filename in PDF_CASES and not _HAS_PDFPLUMBER:
        return "pdfplumber not installed — install '.[llm]' or '.[corpus]' to cover PDFs"
    if not (EDGE_DIR / filename).exists():
        return f"{filename} missing — run `make corpus` first"
    return None


@pytest.mark.parametrize("filename,kind", EDGE_CASES)
def test_reader_does_not_crash(filename, kind):
    """read_corpus must return a structured result with 0 stack traces.

    Per spec acceptance: "Zero stack traces. Every error produces a
    user-friendly message naming the file and the issue."
    """
    skip = _skip_reason(filename)
    if skip:
        pytest.skip(skip)

    from uofa_cli.document_reader import read_corpus

    path = EDGE_DIR / filename
    # The call itself must not raise; that is the spec's primary criterion.
    corpus = read_corpus([path])

    if kind == "chunks":
        assert len(corpus.chunks) > 0, (
            f"{filename}: expected at least one chunk, got 0 with "
            f"warnings={corpus.warnings}"
        )
    elif kind == "warn":
        assert len(corpus.chunks) == 0, (
            f"{filename}: expected 0 chunks and a surfaced warning, "
            f"got {len(corpus.chunks)} chunks"
        )
        assert len(corpus.warnings) >= 1, f"{filename}: no warning surfaced"
        # Actionability: the warning must name the file, so a user running
        # a directory-wide extract knows which input triggered it.
        assert any(filename in w for w in corpus.warnings), (
            f"{filename}: warning does not name the file: {corpus.warnings}"
        )
    elif kind == "graceful":
        # Either outcome is acceptable; absence of crash is already asserted
        # by the read_corpus call above completing.
        pass


def test_extract_end_to_end_has_no_traceback(tmp_path):
    """End-to-end: run `uofa extract` on a tmp copy of the edge-cases
    directory and assert no Python traceback reaches stderr.

    This is the test the spec's acceptance section describes verbatim:
    a single command over the whole corpus producing zero stack traces.
    Skip when the corpus hasn't been built or pdfplumber is missing.
    """
    if not EDGE_DIR.exists() or not any(EDGE_DIR.iterdir()):
        pytest.skip("corpus/edge-cases/ not built — run `make corpus`")
    if not _HAS_PDFPLUMBER:
        pytest.skip("pdfplumber not installed; extract exercises PDF paths")

    # `uofa extract <dir>` runs three phases: discover → read → LLM.
    # No LLM backend is configured in CI, so extract will fail at the
    # LLM step. That's fine — the spec's acceptance is "zero stack
    # traces", which targets the reader phase preceding the LLM call.
    # Both the reader phase and the LLM failure path must produce
    # clean error messages, not Python tracebacks.
    result = subprocess.run(
        [sys.executable, "-m", "uofa_cli", "extract",
         str(EDGE_DIR), "--pack", "vv40"],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )
    assert "Traceback" not in result.stderr, (
        f"uofa extract produced a Python traceback:\n{result.stderr}"
    )
    assert "Traceback" not in result.stdout, (
        f"uofa extract produced a Python traceback on stdout:\n{result.stdout}"
    )

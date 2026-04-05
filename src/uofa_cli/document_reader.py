"""Document reader dispatcher — discovers files, reads them, builds an extraction corpus."""

from __future__ import annotations

import importlib
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class DocumentChunk:
    """A piece of extracted text with source attribution."""
    text: str
    source_file: str          # Filename only (e.g. "report.pdf")
    source_path: str          # Relative path for debugging
    page_number: int | None = None
    section_heading: str | None = None
    sheet_name: str | None = None
    format: str = "txt"       # "pdf", "docx", "xlsx", "csv", "txt"
    token_estimate: int = 0

    def __post_init__(self):
        if not self.token_estimate:
            self.token_estimate = len(self.text) // 4


@dataclass
class ExtractionCorpus:
    """All chunks from all files, ready for LLM extraction."""
    chunks: list[DocumentChunk] = field(default_factory=list)
    total_tokens: int = 0
    file_manifest: list[dict] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


# Suffix → (module_path, function_name) — lazy-imported on first use
_READERS: dict[str, tuple[str, str]] = {
    ".pdf":  ("uofa_cli.readers.pdf_reader",  "read_pdf"),
    ".docx": ("uofa_cli.readers.docx_reader", "read_docx"),
    ".xlsx": ("uofa_cli.readers.xlsx_reader", "read_xlsx"),
    ".csv":  ("uofa_cli.readers.csv_reader",  "read_csv"),
    ".tsv":  ("uofa_cli.readers.csv_reader",  "read_csv"),
    ".txt":  ("uofa_cli.readers.text_reader",  "read_text"),
    ".log":  ("uofa_cli.readers.text_reader",  "read_text"),
    ".f06":  ("uofa_cli.readers.text_reader",  "read_text"),
    ".dat":  ("uofa_cli.readers.text_reader",  "read_text"),
}

_DEFERRED_SUFFIXES = {".doc", ".xls", ".pptx", ".ppt"}

_SKIP_FILENAMES = {"EVIDENCE_MANIFEST.txt", "evidence_manifest.txt"}

# Sort priority: lower number = earlier in the sorted list
_FORMAT_PRIORITY = {
    ".pdf": 0, ".docx": 1, ".xlsx": 2, ".csv": 3, ".tsv": 3,
    ".txt": 4, ".log": 4, ".f06": 4, ".dat": 4,
}


def discover_files(
    sources: list[Path],
    glob_pattern: str | None = None,
    max_depth: int = 3,
) -> tuple[list[Path], list[str]]:
    """Walk sources and return (sorted file list, warnings).

    Files are sorted: PDFs first, then DOCX, XLSX/CSV, TXT; alpha within groups.
    Deferred formats (.doc, .xls, .pptx) are skipped with a warning.
    Hidden files and EVIDENCE_MANIFEST.txt are skipped silently.
    """
    warnings: list[str] = []
    found: set[Path] = set()

    glob_suffixes: set[str] | None = None
    if glob_pattern:
        # Parse glob pattern like "*.pdf" or "*.pdf,*.docx"
        parts = [p.strip() for p in glob_pattern.split(",")]
        glob_suffixes = set()
        for p in parts:
            if p.startswith("*."):
                glob_suffixes.add(p[1:])  # ".pdf"
            elif p.startswith("."):
                glob_suffixes.add(p)

    for source in sources:
        source = source.resolve()
        if source.is_file():
            found.add(source)
        elif source.is_dir():
            _walk_dir(source, source, 0, max_depth, found, warnings)
        else:
            warnings.append(f"Source not found: {source}")

    # Filter and sort
    result: list[Path] = []
    for path in found:
        name = path.name
        suffix = path.suffix.lower()

        # Skip hidden files
        if name.startswith("."):
            continue

        # Skip manifest files
        if name in _SKIP_FILENAMES:
            continue

        # Skip deferred formats
        if suffix in _DEFERRED_SUFFIXES:
            warnings.append(
                f"Unsupported format — save as "
                f"{'.docx' if suffix == '.doc' else '.xlsx' if suffix == '.xls' else '.docx/.xlsx'}. "
                f"Skipping {name}."
            )
            continue

        # Apply glob filter
        if glob_suffixes and suffix not in glob_suffixes:
            continue

        # Must be a supported format
        if suffix not in _READERS:
            continue

        result.append(path)

    # Deduplicate by resolved path
    seen: set[Path] = set()
    deduped: list[Path] = []
    for p in result:
        rp = p.resolve()
        if rp not in seen:
            seen.add(rp)
            deduped.append(p)

    # Sort by format priority, then alphabetically
    deduped.sort(key=lambda p: (_FORMAT_PRIORITY.get(p.suffix.lower(), 99), p.name.lower()))
    return deduped, warnings


def _walk_dir(
    root: Path, current: Path, depth: int, max_depth: int,
    found: set[Path], warnings: list[str],
) -> None:
    """Recursively walk a directory up to max_depth."""
    if depth > max_depth:
        return
    try:
        entries = sorted(current.iterdir(), key=lambda p: p.name.lower())
    except PermissionError:
        warnings.append(f"Permission denied: {current}")
        return

    for entry in entries:
        if entry.name.startswith(".") or entry.name == "__pycache__":
            continue
        if entry.is_file():
            found.add(entry)
        elif entry.is_dir():
            _walk_dir(root, entry, depth + 1, max_depth, found, warnings)


def read_corpus(paths: list[Path], row_budget: int = 50) -> ExtractionCorpus:
    """Read all files and assemble an ExtractionCorpus."""
    corpus = ExtractionCorpus()

    for path in paths:
        suffix = path.suffix.lower()
        reader_info = _READERS.get(suffix)
        if not reader_info:
            corpus.warnings.append(f"No reader for {path.name}")
            continue

        mod_path, func_name = reader_info
        try:
            mod = importlib.import_module(mod_path)
            reader_func = getattr(mod, func_name)
        except ImportError as exc:
            corpus.warnings.append(
                f"Cannot read {path.name}: missing dependency ({exc}). "
                f"Install with: pip install uofa-cli[llm]"
            )
            continue

        try:
            # Pass row_budget to readers that accept it
            if suffix in (".xlsx", ".csv", ".tsv"):
                chunks = reader_func(path, row_budget=row_budget)
            else:
                chunks = reader_func(path)
        except Exception as exc:
            corpus.warnings.append(f"Error reading {path.name}: {exc}")
            continue

        file_tokens = sum(c.token_estimate for c in chunks)
        corpus.chunks.extend(chunks)
        corpus.file_manifest.append({
            "path": str(path),
            "name": path.name,
            "format": suffix.lstrip("."),
            "chunks": len(chunks),
            "tokens": file_tokens,
        })

    corpus.total_tokens = sum(c.token_estimate for c in corpus.chunks)
    return corpus

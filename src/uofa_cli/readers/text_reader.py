"""Plain text / log file reader with encoding detection."""

from __future__ import annotations

from pathlib import Path

from uofa_cli.document_reader import DocumentChunk


def read_text(path: Path) -> list[DocumentChunk]:
    """Read a plain text or log file, returning a single chunk."""
    text = _read_with_encoding(path)

    fmt = "txt"
    suffix = path.suffix.lower()
    if suffix in (".log", ".f06", ".dat"):
        fmt = suffix.lstrip(".")

    return [DocumentChunk(
        text=text,
        source_file=path.name,
        source_path=str(path),
        format=fmt,
    )]


def _read_with_encoding(path: Path) -> str:
    """Read file with UTF-8, falling back to chardet detection."""
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        pass

    try:
        import chardet
        raw = path.read_bytes()
        detected = chardet.detect(raw)
        encoding = detected.get("encoding", "utf-8") or "utf-8"
        return raw.decode(encoding, errors="replace")
    except ImportError:
        return path.read_text(encoding="utf-8", errors="replace")

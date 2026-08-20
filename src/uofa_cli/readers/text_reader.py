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
    """Read a file, honouring a BOM before trying UTF-8.

    The BOM check is not a nicety. A UTF-16LE file does not raise under a UTF-8
    read -- it decodes to interleaved replacement characters, so the failure is
    silent and the mojibake goes on to an extractor as though it were text.
    Real solver evidence contains such files: `user_files/optiSLang_protocol.log`
    in the Nagaraja archives is UTF-16LE with a BOM.

    A file that is not text at all comes back as a stated placeholder rather
    than as replacement characters, for the same reason.
    """
    from uofa_cli.solver.detect import HEAD_BYTES, decode_head

    head = path.open("rb").read(HEAD_BYTES)
    _, encoding = decode_head(head)
    if encoding is None:
        return f"(binary file — no text could be read from {path.name})"
    if encoding != "utf-8":
        return path.read_bytes().decode(encoding, errors="replace")

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

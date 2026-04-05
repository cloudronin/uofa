"""CSV/TSV reader — converts delimited files to markdown tables."""

from __future__ import annotations

import csv
from pathlib import Path

from uofa_cli.document_reader import DocumentChunk


def read_csv(path: Path, row_budget: int = 50) -> list[DocumentChunk]:
    """Read a CSV/TSV and return a single chunk as a markdown table."""
    text_content = _read_with_encoding(path)

    # Auto-detect delimiter
    try:
        dialect = csv.Sniffer().sniff(text_content[:4096], delimiters=",\t;|")
        delimiter = dialect.delimiter
    except csv.Error:
        delimiter = "," if path.suffix.lower() == ".csv" else "\t"

    reader = csv.reader(text_content.splitlines(), delimiter=delimiter)
    rows = list(reader)

    if not rows:
        return [DocumentChunk(
            text="(empty CSV file)",
            source_file=path.name,
            source_path=str(path),
            format="csv",
        )]

    header = rows[0]
    data_rows = rows[1:]
    total_rows = len(data_rows)
    truncated = total_rows > row_budget
    display_rows = data_rows[:row_budget]

    n_cols = len(header)
    md_lines = [
        f"| {' | '.join(header)} |",
        f"| {' | '.join(['---'] * n_cols)} |",
    ]
    for row in display_rows:
        cells = row[:n_cols]
        while len(cells) < n_cols:
            cells.append("")
        md_lines.append(f"| {' | '.join(cells)} |")

    if truncated:
        md_lines.append(f"(showing {row_budget} of {total_rows} rows — full data in source file)")

    text = f"({total_rows} rows x {n_cols} cols)\n"
    text += "\n".join(md_lines)

    return [DocumentChunk(
        text=text,
        source_file=path.name,
        source_path=str(path),
        format="csv",
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

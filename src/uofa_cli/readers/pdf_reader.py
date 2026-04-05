"""PDF reader — extracts text per page via pdfplumber."""

from __future__ import annotations

from pathlib import Path

from uofa_cli.document_reader import DocumentChunk


def read_pdf(path: Path) -> list[DocumentChunk]:
    """Read a PDF and return one chunk per page with page numbers."""
    import pdfplumber

    chunks: list[DocumentChunk] = []
    with pdfplumber.open(path) as pdf:
        if not pdf.pages:
            return [DocumentChunk(
                text="(empty PDF)",
                source_file=path.name,
                source_path=str(path),
                format="pdf",
            )]

        has_text = False
        for i, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            if text.strip():
                has_text = True
            chunks.append(DocumentChunk(
                text=text,
                source_file=path.name,
                source_path=str(path),
                page_number=i,
                format="pdf",
            ))

        if not has_text:
            # Image-only PDF warning — return empty chunk
            return [DocumentChunk(
                text="(image-only PDF — no extractable text)",
                source_file=path.name,
                source_path=str(path),
                format="pdf",
            )]

    return chunks

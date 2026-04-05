"""Tests for document_reader — file discovery, readers, corpus assembly."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from uofa_cli.document_reader import (
    DocumentChunk, ExtractionCorpus, discover_files, read_corpus,
)


# ── DocumentChunk ────────────────────────────────────────────


class TestDocumentChunk:
    def test_token_estimate_auto(self):
        chunk = DocumentChunk(text="a" * 400, source_file="f.txt", source_path="f.txt")
        assert chunk.token_estimate == 100

    def test_token_estimate_override(self):
        chunk = DocumentChunk(text="hello", source_file="f.txt", source_path="f.txt", token_estimate=42)
        assert chunk.token_estimate == 42


# ── discover_files ───────────────────────────────────────────


class TestDiscoverFiles:
    def test_single_file(self, tmp_path):
        f = tmp_path / "report.pdf"
        f.write_bytes(b"%PDF-1.4 fake pdf")
        files, warnings = discover_files([f])
        assert len(files) == 1
        assert files[0].name == "report.pdf"

    def test_folder_walk(self, tmp_path):
        (tmp_path / "a.txt").write_text("text a")
        (tmp_path / "b.csv").write_text("col1,col2\n1,2")
        files, warnings = discover_files([tmp_path])
        assert len(files) == 2

    def test_sort_order(self, tmp_path):
        """PDFs before DOCX before CSV before TXT."""
        for name in ["z.txt", "a.csv", "b.docx", "c.pdf"]:
            (tmp_path / name).write_text("content")
        files, _ = discover_files([tmp_path])
        suffixes = [f.suffix for f in files]
        assert suffixes == [".pdf", ".docx", ".csv", ".txt"]

    def test_hidden_files_skipped(self, tmp_path):
        (tmp_path / ".hidden.txt").write_text("secret")
        (tmp_path / "visible.txt").write_text("public")
        files, _ = discover_files([tmp_path])
        assert len(files) == 1
        assert files[0].name == "visible.txt"

    def test_deferred_formats_warning(self, tmp_path):
        (tmp_path / "old.doc").write_text("old format")
        (tmp_path / "slides.pptx").write_text("slides")
        (tmp_path / "good.txt").write_text("text")
        files, warnings = discover_files([tmp_path])
        assert len(files) == 1
        assert len(warnings) == 2
        assert any("old.doc" in w for w in warnings)
        assert any("slides.pptx" in w for w in warnings)

    def test_manifest_skipped(self, tmp_path):
        (tmp_path / "EVIDENCE_MANIFEST.txt").write_text("manifest")
        (tmp_path / "data.csv").write_text("a,b\n1,2")
        files, _ = discover_files([tmp_path])
        assert len(files) == 1
        assert files[0].name == "data.csv"

    def test_glob_filter(self, tmp_path):
        (tmp_path / "a.pdf").write_text("pdf")
        (tmp_path / "b.txt").write_text("text")
        (tmp_path / "c.csv").write_text("data")
        files, _ = discover_files([tmp_path], glob_pattern="*.pdf")
        assert len(files) == 1
        assert files[0].name == "a.pdf"

    def test_max_depth(self, tmp_path):
        # Create nested dirs beyond max depth
        deep = tmp_path / "a" / "b" / "c" / "d"
        deep.mkdir(parents=True)
        (deep / "deep.txt").write_text("deep")
        (tmp_path / "shallow.txt").write_text("shallow")

        files_shallow, _ = discover_files([tmp_path], max_depth=2)
        assert all(f.name != "deep.txt" for f in files_shallow)

        files_deep, _ = discover_files([tmp_path], max_depth=5)
        assert any(f.name == "deep.txt" for f in files_deep)

    def test_dedup(self, tmp_path):
        f = tmp_path / "same.txt"
        f.write_text("content")
        files, _ = discover_files([f, f, tmp_path])
        assert len(files) == 1

    def test_nonexistent_source(self, tmp_path):
        files, warnings = discover_files([tmp_path / "nope"])
        assert len(files) == 0
        assert any("not found" in w for w in warnings)

    def test_empty_folder(self, tmp_path):
        files, warnings = discover_files([tmp_path])
        assert len(files) == 0


# ── read_corpus ──────────────────────────────────────────────


class TestReadCorpus:
    def test_text_files(self, tmp_path):
        (tmp_path / "a.txt").write_text("Hello world")
        (tmp_path / "b.txt").write_text("Goodbye world")
        files, _ = discover_files([tmp_path])
        corpus = read_corpus(files)
        assert len(corpus.chunks) == 2
        assert corpus.total_tokens > 0
        assert len(corpus.file_manifest) == 2

    def test_csv_file(self, tmp_path):
        (tmp_path / "data.csv").write_text("x,y,z\n1,2,3\n4,5,6\n")
        files, _ = discover_files([tmp_path])
        corpus = read_corpus(files)
        assert len(corpus.chunks) == 1
        assert "x" in corpus.chunks[0].text
        assert "|" in corpus.chunks[0].text  # markdown table

    def test_csv_row_budget(self, tmp_path):
        lines = ["col1,col2"] + [f"{i},{i*2}" for i in range(100)]
        (tmp_path / "big.csv").write_text("\n".join(lines))
        files, _ = discover_files([tmp_path])
        corpus = read_corpus(files, row_budget=10)
        assert "showing 10 of 100 rows" in corpus.chunks[0].text

    def test_unsupported_reader_warning(self, tmp_path):
        (tmp_path / "weird.xyz").write_text("unknown")
        # .xyz is not in _READERS, so discover_files won't include it
        files, _ = discover_files([tmp_path])
        assert len(files) == 0


# ── Reader-specific tests ────────────────────────────────────


class TestTextReader:
    def test_read_text(self, tmp_path):
        f = tmp_path / "log.txt"
        f.write_text("line 1\nline 2\n")
        from uofa_cli.readers.text_reader import read_text
        chunks = read_text(f)
        assert len(chunks) == 1
        assert "line 1" in chunks[0].text
        assert chunks[0].format == "txt"

    def test_read_log_format(self, tmp_path):
        f = tmp_path / "solver.log"
        f.write_text("iteration 1: residual = 1e-3\n")
        from uofa_cli.readers.text_reader import read_text
        chunks = read_text(f)
        assert chunks[0].format == "log"


class TestCsvReader:
    def test_comma_delimited(self, tmp_path):
        f = tmp_path / "data.csv"
        f.write_text("a,b,c\n1,2,3\n4,5,6\n")
        from uofa_cli.readers.csv_reader import read_csv
        chunks = read_csv(f)
        assert len(chunks) == 1
        assert "| a | b | c |" in chunks[0].text

    def test_tsv_delimited(self, tmp_path):
        f = tmp_path / "data.tsv"
        f.write_text("a\tb\tc\n1\t2\t3\n")
        from uofa_cli.readers.csv_reader import read_csv
        chunks = read_csv(f)
        assert "| a | b | c |" in chunks[0].text

    def test_empty_csv(self, tmp_path):
        f = tmp_path / "empty.csv"
        f.write_text("")
        from uofa_cli.readers.csv_reader import read_csv
        chunks = read_csv(f)
        assert len(chunks) == 1
        assert "empty" in chunks[0].text.lower()


# ── Morrison evidence integration ────────────────────────────


MORRISON_DIR = Path(__file__).parent / "fixtures" / "extract" / "morrison-evidence"


@pytest.mark.skipif(not MORRISON_DIR.exists(), reason="Morrison evidence not available")
class TestMorrisonDiscovery:
    def test_discover_morrison_files(self):
        files, warnings = discover_files([MORRISON_DIR])
        # Should find 11 files (12 minus EVIDENCE_MANIFEST.txt)
        assert len(files) == 11
        # Manifest should be skipped
        assert all("EVIDENCE_MANIFEST" not in f.name for f in files)

    def test_discover_pdfs_first(self):
        files, _ = discover_files([MORRISON_DIR])
        # PDFs should come first
        pdf_indices = [i for i, f in enumerate(files) if f.suffix == ".pdf"]
        non_pdf_indices = [i for i, f in enumerate(files) if f.suffix != ".pdf"]
        if pdf_indices and non_pdf_indices:
            assert max(pdf_indices) < min(non_pdf_indices)

    def test_glob_pdfs_only(self):
        files, _ = discover_files([MORRISON_DIR], glob_pattern="*.pdf")
        assert all(f.suffix == ".pdf" for f in files)
        assert len(files) == 3

    def test_read_morrison_text_files(self):
        """Read only txt/csv files (no pdfplumber/python-docx needed)."""
        files, _ = discover_files([MORRISON_DIR], glob_pattern="*.txt,*.csv")
        corpus = read_corpus(files)
        assert corpus.total_tokens > 0
        assert len(corpus.chunks) >= 6  # 4 csv + 2 txt
        # Check CSV has markdown tables
        csv_chunks = [c for c in corpus.chunks if c.format == "csv"]
        assert all("|" in c.text for c in csv_chunks)

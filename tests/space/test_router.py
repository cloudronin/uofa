"""S1 router tests — deterministic pack pick, NASA detection, confidence floor."""

from __future__ import annotations

from pathlib import Path

from space.router import MIN_SIGNAL, route
from uofa_cli.document_reader import DocumentChunk, ExtractionCorpus, discover_files, read_corpus

_REPO_ROOT = Path(__file__).resolve().parents[2]
_MORRISON = _REPO_ROOT / "packs" / "vv40" / "examples" / "morrison" / "source"


def _corpus(text: str, filename: str = "evidence.txt") -> ExtractionCorpus:
    c = ExtractionCorpus()
    c.chunks = [DocumentChunk(text=text, source_file=filename, source_path=filename)]
    c.file_manifest = [{"name": filename}]
    return c


def test_router_picks_vv40_on_vv40_cues():
    d = route(_corpus("This assessment defines the Context of Use and model risk under ASME V&V 40."))
    assert d.primary == "vv40"
    assert not d.low_confidence
    assert "V&V 40" in d.why


def test_router_picks_nasa_on_nasa_cues():
    d = route(_corpus(
        "Per NASA-STD-7009B the credibility assessment scale covers results robustness "
        "and use history for this aerospace model.",
        filename="nasa_7009b_cas_report.txt",
    ))
    assert d.primary == "nasa-7009b"
    assert not d.low_confidence


def test_router_low_confidence_on_generic_bundle():
    d = route(_corpus("The quarterly report summarizes revenue and headcount."))
    assert d.low_confidence
    assert d.primary == "vv40"  # best guess, but flagged for explicit confirmation
    assert d.confidence == 0.0
    assert "confirm" in d.why.lower()


def test_router_tie_breaks_to_vv40():
    # One vv40 cue and one nasa cue of equal weight -> vv40 wins ties.
    d = route(_corpus("asme review of the aerospace program"))  # asme=2 vs aerospace=2
    assert d.scores["vv40"] == d.scores["nasa-7009b"]
    assert d.primary == "vv40"


def test_router_morrison_sample_routes_vv40():
    """Done-gate: the real Morrison evidence routes to vv40, confidently."""
    file_paths, _ = discover_files([_MORRISON])
    assert file_paths, "Morrison sample not found"
    corpus = read_corpus(file_paths)
    d = route(corpus)
    assert d.primary == "vv40"
    assert not d.low_confidence
    assert d.scores["vv40"] >= MIN_SIGNAL

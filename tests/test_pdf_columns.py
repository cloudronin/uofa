"""Two-column PDFs must yield sentences, not spliced half-sentences.

`page.extract_text()` reads in raster order, so on a two-column page it joins the
left column's line to the right column's line. Token recall stays ~1.00 and every
sentence is destroyed. The synthetic corpus is markdown, so this was invisible
there and only ever affected real documents -- which is precisely where the
pipeline's transfer claims are made.

Measured against 13 hand-annotated evidence spans on the OpenSim credibility
paper (the spans a reviewer would cite for each NASA-STD-7009A factor):

    extract_text()             1/13 contiguous  ( 8%)
    extract_text(layout=True)  1/13 contiguous  ( 8%)
    per-column extraction     12/13 contiguous  (92%)
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

from uofa_cli.readers.pdf_reader import _find_gutter, read_pdf  # noqa: E402

pdfplumber = pytest.importorskip("pdfplumber")

_REAL = _ROOT / "tests" / "fixtures" / "extract_corpus_real"
_TWO_COL = (_REAL / "bundle_real_opensim_knee" / "source"
            / "Modeling_and_Simulation_Credibility_Assessments.pdf")
_ONE_COL = (_REAL / "bundle_real_opensim_knee" / "source"
            / "MS_Model_Credibility_Manuscript_Supplemental.pdf")
_ONE_COL_LONG = (_REAL / "bundle_real_elemance_thoracic" / "source"
                 / "20230017197_Manuscript.pdf")

# Hand-annotated by reading the paper, before any extractor was run against it.
# Each is the sentence a reviewer would cite as the evidence for that factor.
SPANS = [
    "The assessment score for code verification is 0",
    "The conceptual validation assessment score is 0 since studies need to be "
    "conducted representative of an EVA injury",
    "There is no evidence that results uncertainty or robustness (sensitivity) "
    "analyses were performed for the other models",
    "The ligament injury data pedigree score is 1 since the knee ligaments are "
    "modeled as a combination of ligament and muscle features with properties "
    "obtained from PMHS data",
    "The hand muscle strain injury data pedigree score is 1 since musculotendon "
    "properties were obtained from PMHS data",
]


def _norm(s: str) -> str:
    return " ".join(s.split()).lower()


def _text(path: Path) -> str:
    return _norm("\n".join(c.text for c in read_pdf(path)))


@pytest.mark.skipif(not _TWO_COL.exists(), reason="real corpus not present")
def test_two_column_spans_survive_as_contiguous_text():
    text = _text(_TWO_COL)
    missing = [s for s in SPANS if _norm(s) not in text]
    assert not missing, (
        f"{len(missing)}/{len(SPANS)} evidence spans are not contiguous in the "
        f"extracted text. Every sentence-level method -- extractive quoting, "
        f"sentence classification, attribution scoring -- needs the span, not "
        f"the words. First missing: {missing[0][:70]!r}"
    )


@pytest.mark.skipif(not _TWO_COL.exists(), reason="real corpus not present")
def test_raster_order_is_what_broke_them():
    """Pin the bug this fixes, so a regression is attributable rather than vague."""
    with pdfplumber.open(_TWO_COL) as pdf:
        raster = _norm("\n".join(p.extract_text() or "" for p in pdf.pages))
    survived = sum(_norm(s) in raster for s in SPANS)
    assert survived <= 1, (
        "raster-order extraction is no longer destroying these spans -- if "
        "pdfplumber gained layout awareness, the column split may be redundant"
    )


@pytest.mark.skipif(not _ONE_COL.exists(), reason="real corpus not present")
@pytest.mark.parametrize("path", [_ONE_COL, _ONE_COL_LONG],
                         ids=["opensim-supplemental", "elemance-manuscript"])
def test_single_column_prose_is_never_split(path):
    """A false positive cuts every line in half, so this is the dangerous side.

    Both of these are single-column prose documents that the pipeline already
    read correctly; splitting them would corrupt documents that were fine.
    """
    if not path.exists():
        pytest.skip("fixture not present")
    with pdfplumber.open(path) as pdf:
        split = []
        for i, page in enumerate(pdf.pages, start=1):
            x0, _, x1, _ = page.bbox
            if _find_gutter(page.extract_words(), x0, x1) is not None:
                split.append(i)
    assert not split, f"single-column pages wrongly detected as two-column: {split}"


@pytest.mark.skipif(not _TWO_COL.exists(), reason="real corpus not present")
def test_two_column_pages_are_detected():
    with pdfplumber.open(_TWO_COL) as pdf:
        detected = sum(
            _find_gutter(p.extract_words(), p.bbox[0], p.bbox[2]) is not None
            for p in pdf.pages
        )
    assert detected >= len(pdf.pages) - 1, (
        f"only {detected} of {len(pdf.pages)} pages of a two-column journal "
        f"article were detected as two-column"
    )


def test_gutter_needs_enough_words():
    """A handful of words is a figure or a title page, not evidence of columns."""
    assert _find_gutter([{"x0": 0, "x1": 5, "top": 0}] * 3, 0.0, 600.0) is None

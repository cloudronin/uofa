"""`wasDerivedFrom` comes from the files read, not from the model.

It is one of the nine properties `ProfileComplete` requires. The extraction
prompt asked the model for it -- "filename, DOI or report number of the document
this was derived from" -- and across 54 extracted workbooks the model answered
`None` every time. The property was then satisfied downstream by the skeleton
template's own example URI, which JSON-LD coerces to a `file://` IRI and which
therefore passes `sh:nodeKind sh:IRI`.

So a required provenance field was met by the instructions for meeting it, and
both the coverage report and SHACL validation read it as satisfied.

The pipeline opened the files. A model guessing at their names can only be
wrong, and on a provenance field the plausible wrong answer is a fabricated DOI
-- the exact failure this project exists to detect.
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

from uofa_cli.document_reader import DocumentChunk  # noqa: E402
from uofa_cli.llm_extractor import (  # noqa: E402
    ExtractionCorpus,
    ExtractionResult,
    FieldExtraction,
    _stamp_source_documents,
)


def _corpus(*names: str) -> ExtractionCorpus:
    return ExtractionCorpus(chunks=[
        DocumentChunk(text="x", source_file=n, source_path=f"/tmp/{n}", format="pdf")
        for n in names
    ])


def test_it_is_stamped_from_the_files_read():
    r = ExtractionResult()
    _stamp_source_documents(r, _corpus("report.pdf"))
    assert r.assessment_summary["source_document"].value == "report.pdf"


def test_every_file_is_named_once_and_in_order():
    """A bundle is often several files, and one page each is not one document."""
    r = ExtractionResult()
    _stamp_source_documents(r, _corpus("a.pdf", "b.pdf", "a.pdf", "c.pdf"))
    assert r.assessment_summary["source_document"].value == "a.pdf; b.pdf; c.pdf"


def test_it_overrides_whatever_the_model_said():
    """The model cannot know the filenames, so its answer is never preferred.

    On a provenance field the plausible wrong answer is a fabricated DOI, which
    is worse than an empty one: an absent field is visibly absent, an invented
    one is indistinguishable from a real one.
    """
    r = ExtractionResult()
    r.assessment_summary["source_document"] = FieldExtraction(
        value="doi:10.1000/invented", confidence=0.9)
    _stamp_source_documents(r, _corpus("real.pdf"))
    assert r.assessment_summary["source_document"].value == "real.pdf"


def test_confidence_is_certain_and_unattributed():
    """It is a fact about the run, not a reading of the document.

    Confidence 1.0 because the pipeline knows it; source_file None because
    pointing at a page would claim it was read there.
    """
    r = ExtractionResult()
    _stamp_source_documents(r, _corpus("report.pdf"))
    f = r.assessment_summary["source_document"]
    assert f.confidence == 1.0
    assert f.source_file is None and f.source_page is None


def test_nothing_is_stamped_when_no_file_is_known():
    """Better an absent field than a fabricated one."""
    r = ExtractionResult()
    _stamp_source_documents(r, ExtractionCorpus(chunks=[]))
    assert "source_document" not in r.assessment_summary


def test_the_template_placeholder_is_still_detected():
    """The placeholder check must keep working; this fix does not replace it.

    A package can still arrive with the skeleton's example URI -- from a
    hand-filled workbook rather than from extraction -- and that must keep being
    reported as satisfied-by-help-text.
    """
    sys.path.insert(0, str(_ROOT / "dev" / "tools" / "scripts"))
    from schema_coverage import placeholder_satisfied

    assert "wasDerivedFrom" in placeholder_satisfied(
        '{"wasDerivedFrom": "DOI, report number, or URI"}')
    assert placeholder_satisfied('{"wasDerivedFrom": "report.pdf"}') == []

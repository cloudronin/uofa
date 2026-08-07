"""A factor row the extractor left blank is not a detection.

The workbook template pre-fills the factor name and category for every factor in
the pack. `score_factors` matched on `factor_type`, so a row the extractor never
touched counted as FOUND, and `_compute_f1` put it in the predicted set.

Measured on the 54-bundle dev corpus: six NASA-only factors (Data pedigree,
Development process and product management, Development technical review,
Results uncertainty, Results robustness, Use history) had **162 entirely empty
rows** -- no level, no status, no criteria, no rationale -- and the report gave
all six a detection rate of 1.00.

    mean overall F1        all     nasa     vv40
    blank rows credited   0.920    0.928    0.912
    blank rows excluded   0.853    0.793    0.912

NASA read as *better* than V&V 40 while the extractor was filling 13 of its 19
factors. V&V 40 is unchanged because it has no blank rows, which is the control
for this fix.

This is the checklist-constant problem inside the extractor's own score: naming a
factor is free, so any metric that rewards the name rewards a null model.
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "dev" / "tools" / "scripts"))
sys.path.insert(0, str(_ROOT / "src"))

from score_extraction import _factor_has_content, score_factors  # noqa: E402

GT = [
    {"factor_type": "Model form", "expected_level": 3, "expected_status": "assessed"},
    {"factor_type": "Data pedigree", "expected_level": 4, "expected_status": "assessed"},
]

FILLED = {"factor_type": "Model form", "achieved_level": 3, "status": "assessed",
          "rationale": "Governing equations justified against the COU."}
# Exactly what the template leaves behind: a name, a category, nothing else.
TEMPLATE_ROW = {"factor_type": "Data pedigree", "category": "NASA — Capability",
                "achieved_level": None, "required_level": None, "status": None,
                "acceptance_criteria": None, "rationale": None,
                "linked_evidence": None}


def test_template_row_has_no_content():
    assert not _factor_has_content(TEMPLATE_ROW)
    assert _factor_has_content(FILLED)


def test_whitespace_only_is_not_content():
    assert not _factor_has_content({"factor_type": "X", "rationale": "   ",
                                    "status": ""})


def test_any_single_field_counts_as_content():
    # A status alone is a claim about the document, so it is an extraction.
    assert _factor_has_content({"factor_type": "X", "status": "not_applicable"})
    # A level of 0 is a real assessment, not an absence -- must not be falsy-dropped.
    assert _factor_has_content({"factor_type": "X", "achieved_level": 0})


def test_a_dropped_blank_row_scores_as_a_miss():
    """Filtering happens in the parser, so the scorer simply never sees the row.

    That is the honest reading: a blank template row means the extractor did
    not produce that factor.
    """
    r = score_factors([FILLED], GT)
    assert r["factors_found"] == 1
    assert r["per_factor"]["Data pedigree"]["status"] == "MISS"


def test_scoring_path_is_identical_for_controls_and_candidates():
    """The reason the filter lives in the parser and not in score_factors.

    `control_constant_list` emits factor_type alone -- deliberately, so it wins
    detection and nothing else. A content rule applied inside the scorer would
    class the null model itself as blank and drop it from F1 0.960 to 0.000,
    manufacturing headroom for every candidate instead of measuring any. The
    control and the candidate must go through one function with one setting.
    """
    control = [{"factor_type": g["factor_type"]} for g in GT]
    r = score_factors(control, GT)
    assert r["factors_found"] == len(GT), (
        "the checklist control lost its detections -- the blank-row rule leaked "
        "into the scoring path"
    )

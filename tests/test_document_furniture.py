"""The furniture filter: remove labels and rubrics, keep every finding.

Two properties, and the second is the one that took five attempts:

  * no furniture survives  -- otherwise the router keeps ranking table rows
  * no finding is removed  -- otherwise the filter destroys the evidence it
    exists to expose

Measured on `bundle_real_opensim_knee` against the 13 hand-annotated spans:
539 sentences -> 243 kept, 9/9 annotated evidence sentences retained, 0 furniture
left in the pool.

Every false positive below is a real sentence the filter wrongly removed at some
point, kept as a regression case. They share a shape: a *finding about scores*
looks like a *score row*, and a *finding about two factors* looks like a *table
header*. Wording never separated them; predication did. That is why `_VERB`
guards both rules.
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "dev" / "tools" / "scripts"))
sys.path.insert(0, str(_ROOT / "src"))
sys.path.insert(0, str(_ROOT / "tests" / "fixtures" / "extract_corpus_real"))

import pytest  # noqa: E402

from document_furniture import (  # noqa: E402
    classify,
    running_heads,
    strip_furniture,
)

FACTORS = ("data pedigree", "input pedigree", "code/solution verification",
           "conceptual validation", "referent validation",
           "results uncertainty", "results robustness",
           "numerical code verification", "discretization error")

# Real findings the filter must keep. Each one was wrongly removed by an earlier
# version, and each is the best evidence in the document for its factor.
FINDINGS = [
    "The hand muscle strain injury data pedigree score is 1 since musculotendon "
    "properties were obtained from PMHS data.",
    "There is no evidence that results uncertainty or robustness (sensitivity) "
    "analyses were performed for the other models, and thus a score of 0 was given.",
    "The assessment score for code verification is 0 and 1 for the solution "
    "verification, conceptual validation, and referent validation scores for a "
    "muscle strain injury for both models.",
    "The conceptual validation assessment score is 0 since studies need to be "
    "conducted representative of an EVA injury and 1 for referent validation "
    "since ligament parameters were validated against PMHS data sources.",
    "The input pedigree assessment of the models is based on the input required "
    "by OPENSIM which consist of files containing motion capture coordinates.",
]

# Furniture the filter must remove.
FURNITURE = [
    ("Code/solution verification", "fragment"),
    ("Referent validation", "fragment"),
    ("OPENSIM MUSCULOSKELETAL MODELING", "heading"),
    ("4 All data known and All input data known Reliable practices applied", "rubric"),
    ("2 Some data known and Some input data Documented practices applied", "rubric"),
]


@pytest.mark.parametrize("text", FINDINGS, ids=lambda t: t[:38])
def test_findings_are_never_removed(text):
    """A filter that deletes evidence is worse than no filter.

    The router can recover from noise left in the pool; it cannot recover from a
    sentence that is no longer there.
    """
    assert classify(text, FACTORS) is None, (
        f"removed a finding as {classify(text, FACTORS)!r}"
    )


@pytest.mark.parametrize("text,expected", FURNITURE, ids=lambda v: str(v)[:34])
def test_furniture_is_removed_with_the_right_reason(text, expected):
    assert classify(text, FACTORS) == expected


def test_a_score_row_without_a_verb_is_still_removed():
    """The verb guard must not let genuine table rows through.

    `_looks_tabular` and the factor-enumeration rule are both gated on absence
    of a verb, so this pins that the gate did not disable them entirely.
    """
    assert classify("Data Pedigree 1 Input Pedigree 0 Code/Solution Verification 0",
                    FACTORS) is not None


def test_a_bare_factor_enumeration_is_removed():
    assert classify("Level Data pedigree Input pedigree Results uncertainty",
                    FACTORS) == "factor-enumeration"


def test_running_heads_need_repetition_not_a_pattern():
    """Identified by recurring across pages, so no publisher-specific rule."""
    sents = ["Journal of Engineering and Science"] * 4 + ["A real finding about the model."]
    assert "journal of engineering and science" in running_heads(sents)
    assert len(running_heads(sents)) == 1


def test_indices_map_back_to_the_unfiltered_document():
    """A router's picks are scored against positions in the original text.

    Losing the mapping would shift every span silently, which is the failure
    mode that makes a filter look like a scoring regression.
    """
    sents = ["Referent validation", FINDINGS[0], "OPENSIM MODELING SECTION", FINDINGS[1]]
    kept, idx, _ = strip_furniture(sents, FACTORS)
    assert kept == [FINDINGS[0], FINDINGS[1]]
    assert idx == [1, 3]
    assert all(sents[i] == k for i, k in zip(idx, kept))


def test_reasons_are_reported_not_silent():
    """A filter that drops half a document must say what it dropped."""
    _, _, reasons = strip_furniture([t for t, _ in FURNITURE] + FINDINGS, FACTORS)
    assert sum(reasons.values()) == len(FURNITURE)
    assert set(reasons) <= {"fragment", "heading", "rubric", "table-row",
                            "factor-enumeration", "reference", "affiliation",
                            "no-verb", "running-head", "empty"}

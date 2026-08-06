"""The generator's pre-write validation, and the defects it exists to block.

Every rule checked here corresponds to a defect that reached the shipped corpus
and cost a paid generation run to discover. The validation runs before a bundle
is written and before the next one is billed, so a regression fails on bundle 1
rather than on bundle 50.

The corpus these guard against reported `mean overall F1 0.964 — PASS` while
82% of its packages failed the project's own SHACL and it carried ground truth
for one of the thirteen properties ProfileComplete requires.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "dev" / "tools" / "scripts"))

from generate_extract_corpus import _validate_full_schema  # noqa: E402


def _gt(**over):
    base = {
        "expected_factors": [
            {"factor_type": "Model form", "expected_status": "assessed",
             "expected_level": 3, "expected_required_level": 4},
        ],
        "expected_entities": {"models": 1, "datasets": 2, "requirements": 1},
        "expected_validation_results": [
            {"name_keywords": ["head rise"], "has_uq": "Yes", "pass_fail": "Pass"}],
        "expected_decision": {
            "outcome": "Accepted",
            "outcome_source": "the review board accepted with conditions",
            "rationale_keywords": ["GCI", "within tolerance"],
            "decided_by_keywords": ["review board"]},
        "_provenance": "hydra-7-report.md",
    }
    base.update(over)
    return base


def test_a_complete_ground_truth_passes():
    _validate_full_schema(_gt())


@pytest.mark.parametrize("section", [
    "expected_entities",
    "expected_validation_results",
    "expected_decision",
    "_provenance",
])
def test_each_missing_section_is_rejected(section):
    """The four sections the shipped corpus omitted entirely.

    Their absence is *why* the eval scored one property: with no ground truth
    for entities, validation results or the decision, there was nothing to
    score them against, and the gap was invisible in the F1.
    """
    gt = _gt()
    del gt[section]
    with pytest.raises(ValueError, match="missing required sections"):
        _validate_full_schema(gt)


def test_conditional_decision_is_rejected():
    """26 of 50 shipped packages failed SHACL for emitting this.

    The extract prompts instructed "conditionally accepted" and the shape
    allowed only Accepted / Not accepted. Ground truth must not reintroduce the
    value the prompt was fixed to stop producing.
    """
    with pytest.raises(ValueError, match="shape allows only"):
        _validate_full_schema(_gt(expected_decision={
            "outcome": "Conditional", "outcome_source": "x",
            "rationale_keywords": [], "decided_by_keywords": []}))


def test_not_applicable_rows_must_carry_a_null_level():
    """The 60-row defect that made the level metric uninterpretable.

    Writing 1 put rows with no level to assign into the level statistic,
    mixing "did you assign the right rigour" with "did you notice this does
    not apply".
    """
    with pytest.raises(ValueError, match="not_applicable rows must carry"):
        _validate_full_schema(_gt(expected_factors=[
            {"factor_type": "Use error", "expected_status": "not_applicable",
             "expected_level": 1, "expected_required_level": 2}]))

    _validate_full_schema(_gt(expected_factors=[
        {"factor_type": "Use error", "expected_status": "not_applicable",
         "expected_level": None, "expected_required_level": 2}]))


@pytest.mark.parametrize("level", [0, 6, "3", None])
def test_assessed_rows_need_a_level_in_range(level):
    with pytest.raises(ValueError, match="expected_level"):
        _validate_full_schema(_gt(expected_factors=[
            {"factor_type": "Model form", "expected_status": "assessed",
             "expected_level": level, "expected_required_level": 3}]))


def test_level_5_is_now_reachable():
    """Across 800 rows of the shipped corpus, not one reached 4 or 5.

    The old prompt instructed the generator to downgrade whenever more than
    2-3 factors reached level 4, which is why predicting the constant 2 scored
    1.000 inside the tolerance. If this rejects a 5, the cap is back.
    """
    _validate_full_schema(_gt(expected_factors=[
        {"factor_type": "Model form", "expected_status": "assessed",
         "expected_level": 5, "expected_required_level": 5}]))


def test_required_level_is_mandatory_and_ranged():
    with pytest.raises(ValueError, match="expected_required_level"):
        _validate_full_schema(_gt(expected_factors=[
            {"factor_type": "Model form", "expected_status": "assessed",
             "expected_level": 3}]))


def test_required_level_may_differ_from_achieved_in_both_directions():
    """The gap is the point.

    A shortfall says the evidence has not reached the rigour the risk demands;
    a surplus says it exceeded it. A generator that copied expected_level into
    expected_required_level would make the gap identically zero and delete the
    most useful number a reviewer reads.
    """
    for achieved, required in ((2, 4), (4, 2), (3, 3)):
        _validate_full_schema(_gt(expected_factors=[
            {"factor_type": "Model form", "expected_status": "assessed",
             "expected_level": achieved, "expected_required_level": required}]))

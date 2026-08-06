"""Schema coverage is saturated by constants, exactly as detection F1 was.

Adding seven properties to the eval fixed the problem that it described one.
It did not fix the deeper one. Measured against the shipped corpus:

    property             LLM     a constant
    bindsDataset          80%        100%
    bindsModel            82%        100%
    bindsRequirement      54%        100%
    hasContextOfUse      100%        100%
    hasDecisionRecord    100%        100%
    modelRiskLevel       100%        100%

**A zero-parameter function beats the extractor on three of them and ties on
three more.** `control_constant_entity` emits one model called "the model", one
dataset, one requirement, reads nothing, and satisfies `minCount >= 1` on all
three binding properties.

So "the extractor populates 8 of 9 required properties" is the same class of
claim as "the extractor scores F1 0.964": true, and not evidence of extraction.

What separates them is **accuracy**, which needs ground truth the shipped corpus
never carried. The v2 corpus adds `expected_entities` (counts of distinct
models, datasets and requirements), `expected_validation_results` and
`expected_decision` — against those, the constant's answer of "1, always" is
wrong by four on a document naming five models.

These tests exist so the coverage numbers are never read alone.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "dev" / "tools" / "scripts"))

from schema_controls import (  # noqa: E402
    CONTROLS,
    control_constant_entity,
    control_first_sentence,
)
from schema_coverage import required_properties, score_schema_coverage  # noqa: E402


def test_a_constant_satisfies_every_binding_property():
    """The finding. `bindsRequirement` is the sharpest: 54% against 100%."""
    cov = score_schema_coverage(control_constant_entity().as_parsed(), "vv40")
    for prop in ("bindsModel", "bindsDataset", "bindsRequirement"):
        assert cov[prop] is True, (
            f"{prop}: the constant stopped satisfying it — if the detector got "
            f"stricter that is good, but the coverage baselines are now stale")


def test_no_required_property_resists_every_control():
    """Read together, the controls cover the whole schema.

    Each control is narrow; the union is not. If a property here ever fails to
    be reachable by some constant, that property is genuinely measuring
    extraction and is worth reporting on its own — right now none is.
    """
    reachable = set()
    for make in CONTROLS.values():
        for prop, ok in score_schema_coverage(make().as_parsed(), "vv40").items():
            if ok:
                reachable.add(prop)
    # hasCredibilityFactor is reached by control_constant_list, which lives in
    # score_extraction.py and is already pinned there.
    from score_extraction import control_predictions
    if control_predictions("control_constant_list", "vv40"):
        reachable.add("hasCredibilityFactor")

    required = set(required_properties("vv40")) - {"wasDerivedFrom"}
    unreachable = required - reachable
    assert unreachable <= {"hasValidationResult"}, (
        f"unexpected properties no control reaches: {unreachable}. Either a "
        f"control regressed or a genuinely discriminating property appeared.")


def test_coverage_alone_would_rank_a_constant_above_the_extractor():
    """Stated as an executable claim, because it is the reason for the caveat.

    On the three binding properties, coverage ranks the constant first. Any
    report showing entity coverage without this beside it is saying a constant
    extracts better than a model.
    """
    llm_coverage = {"bindsModel": 0.82, "bindsDataset": 0.80, "bindsRequirement": 0.54}
    cov = score_schema_coverage(control_constant_entity().as_parsed(), "vv40")
    for prop, llm in llm_coverage.items():
        assert cov[prop] is True and llm < 1.0, prop


def test_the_first_sentence_control_floors_groundedness():
    """Groundedness had no null model until this.

    An extractive method cannot fabricate: every figure it quotes is in the
    source by construction, so it scores groundedness 1.000 — better than the
    LLM's 0.994. That is the honest ceiling for extractive approaches and the
    reason groundedness must be read beside claim density, which this control
    fails by saying the same thing on every factor.
    """
    source = ("The grid convergence index for head rise is 0.72% on the fine "
              "mesh. Residuals fell below 1e-5 throughout.")
    pkg = control_first_sentence(source, ["Model form", "Discretization error"])
    rationales = [f["rationale"] for f in pkg.credibility_factors]

    assert all(r for r in rationales), "coverage 1.0 — the cheat works on coverage"
    assert len(set(rationales)) == 1, (
        "and distinctness is what exposes it: one sentence, every factor")

    from groundedness import score_factor_rationales
    res = score_factor_rationales(pkg.credibility_factors, source)
    assert res.groundedness == 1.0, (
        "an extractive control cannot fabricate, so it must score 1.000; if it "
        "does not, the tokeniser is mis-reading its own quoted text")
    assert res.coverage == 1.0


def test_controls_do_not_read_the_source():
    """A control that reads the document is not a null model.

    `control_first_sentence` is the deliberate exception and takes the text as
    an argument; the rest take none, which is enforced by them being callable
    with no document at all.
    """
    for name, make in CONTROLS.items():
        pkg = make()          # no source available to it, by construction
        assert pkg.as_parsed(), name

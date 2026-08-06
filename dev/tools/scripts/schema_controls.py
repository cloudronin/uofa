#!/usr/bin/env python3
"""Null models for the newly scored schema properties.

Scoring `hasCredibilityFactor` alone hid that a zero-parameter function reached
F1 0.960. Adding seven more properties without adding their controls would
repeat that exactly: `bindsModel` populated in 82% of packages sounds like
extraction until you ask what *"always emit one model, called 'the model'"*
scores. It scores **100%**, passes `minCount >= 1`, and beats the extractor.

So every property scored gets a control before any candidate is compared
against it. The rule this file exists to enforce:

    coverage is necessary and never sufficient

A property where the constant matches the candidate is not measuring
extraction, and its number must not be reported alone.

## What each control is allowed to know

Nothing about the document. A control may know the pack's fixed vocabulary --
that is what makes it a *fair* null model rather than a broken one -- but it may
not read `source/`. `control_first_sentence` is the single exception and is
marked as such: it reads the first sentence and nothing else, which is the
cheapest possible thing that is not input-blind, and it exists to put a floor
under rationale groundedness.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# A sentence ends at .!? followed by whitespace and a capital or a quote.
# Splitting on a bare "." instead breaks "0.72%" at the decimal point and
# truncates the sentence to "...is 0." -- which destroys precisely the numeric
# claims that make an extractive method worth having. The first version of
# `control_first_sentence` did exactly that and scored groundedness 0.000
# instead of 1.000, which is how the test caught it.
_SENTENCE_END = re.compile(r'(?<=[.!?])\s+(?=[A-Z"\u201c(])')


@dataclass
class ControlPackage:
    """What a null model would put in a workbook, in parse_extracted_xlsx shape."""
    assessment_summary: dict
    entities: list
    validation_results: list
    decision: dict
    credibility_factors: list

    def as_parsed(self) -> dict:
        return {
            "assessment_summary": self.assessment_summary,
            "entities": self.entities,
            "validation_results": self.validation_results,
            "decision": self.decision,
            "credibility_factors": self.credibility_factors,
        }


def control_constant_entity(factors: list | None = None) -> ControlPackage:
    """One model, one dataset, one requirement, named nothing in particular.

    Scores 100% coverage on `bindsModel`, `bindsDataset` and `bindsRequirement`
    and satisfies `minCount >= 1` on all three, having read nothing. The
    extractor manages 82% / 80% / 54%.

    So on coverage alone this control **beats the LLM on all three properties**.
    Anything reporting entity coverage without this number beside it is
    reporting that a constant is better at extraction than a model.

    What separates them is `expected_entities`, which the v2 corpus carries and
    the shipped one did not: the constant always says 1, and a document naming
    five models is then wrong by four.
    """
    return ControlPackage(
        assessment_summary={},
        entities=[
            {"type": "model", "name": "the model"},
            {"type": "dataset", "name": "the dataset"},
            {"type": "requirement", "name": "the requirement"},
        ],
        validation_results=[],
        decision={},
        credibility_factors=list(factors or []),
    )


def control_constant_decision(factors: list | None = None) -> ControlPackage:
    """Always "Accepted".

    Ground truth is overwhelmingly Accepted -- a package that was rejected
    rarely gets written up -- so this is the `control_majority_status` problem
    in a new place. Outcome accuracy must be reported against it, never alone.
    """
    return ControlPackage(
        assessment_summary={},
        entities=[],
        validation_results=[],
        decision={"outcome": "Accepted", "rationale": "", "decided_by": ""},
        credibility_factors=list(factors or []),
    )


def control_constant_summary(factors: list | None = None) -> ControlPackage:
    """The modal assessment summary: MRL 2, a COU name copied from nothing.

    Satisfies `modelRiskLevel` and `hasContextOfUse` at 100% coverage. Both
    read 100% for the extractor too, which is exactly the point -- on coverage
    those two properties cannot distinguish anything, and only value accuracy
    can.
    """
    return ControlPackage(
        assessment_summary={"model_risk_level": "MRL 2", "cou_name": "Context of use",
                            "profile": "Complete"},
        entities=[],
        validation_results=[],
        decision={},
        credibility_factors=list(factors or []),
    )


def control_first_sentence(source_text: str, factor_names: list[str]) -> ControlPackage:
    """Rationale = the document's first sentence, on every factor.

    The only control here that reads the input, and it reads the least possible
    amount. It exists to floor **groundedness**, which is otherwise the one
    metric with no null model: any figure in that sentence is by construction
    present in the source, so this control scores groundedness 1.000.

    That is the honest ceiling for extractive methods and the reason
    groundedness must be read beside claim density. This control gets coverage
    1.0 and groundedness 1.0 while saying the same thing thirteen times -- only
    per-factor distinctness separates it from real work.
    """
    first = ""
    for chunk in _SENTENCE_END.split(source_text.strip()):
        chunk = chunk.strip()
        if len(chunk) > 40:
            first = chunk
            break
    return ControlPackage(
        assessment_summary={},
        entities=[],
        validation_results=[],
        decision={},
        credibility_factors=[
            {"factor_type": name, "rationale": first,
             "required_level": None, "achieved_level": None,
             "acceptance_criteria": None, "status": "assessed"}
            for name in factor_names
        ],
    )


CONTROLS = {
    "control_constant_entity": control_constant_entity,
    "control_constant_decision": control_constant_decision,
    "control_constant_summary": control_constant_summary,
}

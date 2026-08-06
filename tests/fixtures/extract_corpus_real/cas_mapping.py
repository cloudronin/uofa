#!/usr/bin/env python3
"""Published NASA credibility factors -> the repo's 19-factor nasa-7009b pack.

Real reports do not publish the pack's factor list. They publish one of three
different vocabularies, and which one depends on the year and the authors:

  rollup_7009a       8 factors. Verification and Validation are single scores.
                     Used by the Digital Astronaut Project posters (ARED,
                     20140011878) and the IMM assessment report (20150021308).

  decomposed_7009a   6 factors. Verification and Validation are split by kind
                     -- code/solution, conceptual/referent -- and data and input
                     pedigree are separated. Used by the 2023-24 EVA
                     finite-element and musculoskeletal papers.

  capability_results_7009b  11 factors across two assessments (Appendix E of
                     NASA-STD-7009B, March 2024). No report in the sample uses
                     it yet; included because the pack is named for 7009B and a
                     2025+ report will.

The repo pack is none of these: it is V&V 40's 13 factors plus 6 NASA ones, so
it decomposes Verification and Validation further than any published table does.

## Why this file exists rather than a wider ground truth

Ground truth is transcribed at **published granularity** -- exactly the rows and
scores the document prints. This module is the only place the two vocabularies
meet, and it is deliberately separate so that the judgment lives here, in code
that can be read and argued with, instead of being baked into a ground_truth.json
where it would look like something the document said.

A pack prediction is rolled UP to the published factor before comparison. It is
never the case that a published score is pushed DOWN onto several pack factors:
that would invent per-factor ground truth the document does not contain, and the
whole point of Tier 1 is that the labels are the authors', not ours.

## The rollup rule

`min` -- credibility is limited by its weakest constituent. A model whose code
verification is sound but whose solver convergence is unevidenced has not earned
the higher score. This matches how NASA-STD-7009 states its own level criteria,
where reaching a level requires *all* of that level's conditions.

`min` is a choice, not a fact, and it is the one number in this corpus that is
ours rather than the authors'. Report it as such.
"""

from __future__ import annotations

# ── rollup_7009a: 8 published factors ────────────────────────
# Verification absorbs four pack factors and Validation eight, which is why a
# report using this vocabulary is a weaker test of per-factor extraction than
# one using the decomposed vocabulary below.
ROLLUP_7009A: dict[str, list[str]] = {
    "Verification": [
        "Software quality assurance",
        "Numerical code verification",
        "Discretization error",
        "Numerical solver error",
    ],
    "Validation": [
        "Model form",
        "Test samples",
        "Test conditions",
        "Equivalency of input parameters",
        "Output comparison",
        "Relevance of the quantities of interest",
        "Relevance of the validation activities to the COU",
    ],
    "Input Pedigree": ["Model inputs", "Data pedigree"],
    "Results Uncertainty": ["Results uncertainty"],
    "Results Robustness": ["Results robustness"],
    "Use History": ["Use history"],
    "M&S Management": ["Development process and product management"],
    # No pack factor covers the qualifications of the people who ran the model.
    # Left empty on purpose: scoring it would require inventing a prediction.
    "People Qualifications": [],
}

# ── decomposed_7009a ─────────────────────────────────────────
# Much closer to 1:1, which makes these the better Tier 1 sources despite being
# the newer papers.
#
# The same paper family prints these at two granularities -- "Code verification"
# and "Solution verification" as separate rows in one table, "Code/solution
# verification" as one row in another -- so both spellings are keys here. That is
# not redundancy to tidy up: a bundle transcribes the rows its table printed, and
# collapsing the two forms would mean transcribing a row the document did not
# contain.
DECOMPOSED_7009A: dict[str, list[str]] = {
    "Data pedigree": ["Data pedigree"],
    "Input pedigree": ["Model inputs"],

    "Code verification": ["Numerical code verification"],
    "Solution verification": ["Discretization error", "Numerical solver error"],
    "Code/solution verification": [
        "Numerical code verification",
        "Discretization error",
        "Numerical solver error",
    ],

    "Conceptual validation": ["Model form"],
    "Referent validation": [
        "Output comparison",
        "Relevance of the validation activities to the COU",
    ],
    "Conceptual/referent validation": [
        "Model form",
        "Output comparison",
        "Relevance of the validation activities to the COU",
    ],

    "Results uncertainty": ["Results uncertainty"],
    "Results robustness": ["Results robustness"],
}

# ── capability_results_7009b: 11 published factors ───────────
CAPABILITY_RESULTS_7009B: dict[str, list[str]] = {
    # M&S Capability Assessment (NASA-STD-7009B E.3)
    "Data Pedigree": ["Data pedigree"],
    "Verification": [
        "Software quality assurance",
        "Numerical code verification",
        "Discretization error",
        "Numerical solver error",
    ],
    "Validation": [
        "Model form",
        "Test samples",
        "Test conditions",
        "Equivalency of input parameters",
        "Output comparison",
        "Relevance of the quantities of interest",
        "Relevance of the validation activities to the COU",
    ],
    "Development Technical Review": ["Development technical review"],
    "Development Process/Product Management": [
        "Development process and product management"],
    # M&S Results Assessment (E.4)
    "Use Assessment": ["Use history"],
    "Input Pedigree": ["Model inputs"],
    "Uncertainty Characterization": ["Results uncertainty"],
    "Results Robustness": ["Results robustness"],
    "Use/Analysis Technical Review": ["Development technical review"],
    "Use Process/Product Management": ["Development process and product management"],
}

VARIANTS: dict[str, dict[str, list[str]]] = {
    "rollup_7009a": ROLLUP_7009A,
    "decomposed_7009a": DECOMPOSED_7009A,
    "capability_results_7009b": CAPABILITY_RESULTS_7009B,
}


def canonical(published_factor: str, variant: str) -> str:
    """Resolve a printed factor name to its key in `variant`, ignoring case.

    The two decomposed-vocabulary papers disagree on capitalisation -- one
    prints "Data Pedigree", the other "Data pedigree" -- and bundles keep
    whatever their own table printed, because that is what transcription means.
    Capitalisation is not semantic, so lookup normalises it rather than forcing
    one paper's house style onto the other's ground truth.
    """
    table = VARIANTS[variant]
    if published_factor in table:
        return published_factor
    lowered = {k.lower(): k for k in table}
    if published_factor.lower() in lowered:
        return lowered[published_factor.lower()]
    raise KeyError(f"{published_factor!r} is not a factor of {variant!r}")


def roll_up(pack_levels: dict[str, float | None], variant: str) -> dict[str, float | None]:
    """Pack factor levels -> published factor levels, by the `min` rule.

    `pack_levels` maps the pack's factor names to extracted levels; missing or
    None entries are treated as not extracted and skipped. A published factor
    whose constituents were all missed returns None rather than 0 -- "did not
    extract" and "extracted, scored zero" are different failures and collapsing
    them is how the level metric became uninterpretable in the first place.
    """
    if variant not in VARIANTS:
        raise KeyError(f"unknown CAS variant {variant!r}; have {sorted(VARIANTS)}")
    out: dict[str, float | None] = {}
    for published, constituents in VARIANTS[variant].items():
        vals = [pack_levels.get(c) for c in constituents]
        vals = [v for v in vals if isinstance(v, (int, float))]
        out[published] = min(vals) if vals else None
    return out


def unmapped_factors(variant: str) -> list[str]:
    """Published factors no pack factor can answer.

    Only `People Qualifications` today. Scored as unanswerable rather than
    wrong: the pack has nothing to say about who ran the model, and counting
    that as a miss would penalise the extractor for a gap in the schema.
    """
    return [k for k, v in VARIANTS[variant].items() if not v]

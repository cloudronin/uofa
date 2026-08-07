#!/usr/bin/env python3
"""Drop the parts of a document that are not claims — headings, table rows, rubrics.

Sits between the segmenter and the router: `sentences()` produces units, this
decides which of them could carry evidence, and only those are offered to a
detector or extractor.

## Why it exists

K6 was run against a real document for the first time and scored 0.000
attribution, tying both null models. Every one of its six picks was document
furniture rather than prose:

    Code/solution verification  -> 'Code/solution verification'      table row label
    Referent validation         -> 'Referent validation'             table row label
    Data pedigree               -> '4 All data known and All input…' rubric row
    Conceptual validation       -> 'OPENSIM MUSCULOSKELETAL MODELING' heading
    Results robustness          -> 'Within the NASA'                 fragment
    Results uncertainty         -> 'uncertainties.'                  fragment

The cause is structural, not a weak classifier. In a real credibility report the
densest occurrence of a factor's name is the report's own scoring table and its
level rubric -- both of which name every factor and assess none. The findings are
in prose that names the factor once, obliquely, hundreds of sentences away.

The synthetic corpus cannot exhibit this: its generator is instructed never to
use canonical factor terminology, so no furniture containing factor names exists
to be attracted to. That is why the failure was invisible until a real document
was read, and it is the same shape as the two PDF-reader bugs -- a property of
real evidence that markdown fixtures do not have.

## Scope: rationale and routing only, never level extraction

The CAS table is noise *here* and gold *elsewhere*. It is where the published
per-factor scores live, so level extraction must keep reading it. Applying this
filter globally would delete the most valuable table in the document. Callers on
the level path should not use it.

## The signal

A claim has a finite verb. A heading, a row label and a column header do not:
"Referent validation" and "Data Pedigree 1 Input Pedigree 0" assert nothing on
their own. That single test does most of the work and needs no per-document
tuning, which matters because every hand-tuned threshold in this project has
eventually been found to be fitting one corpus.

The remaining rules cover things that do contain verbs but still are not the
document's own claims: running heads repeated on every page, reference entries,
and rubric rows, which are the standard's level definitions rather than findings
about this model.
"""

from __future__ import annotations

import re
from collections import Counter

# Auxiliaries and common report verbs. Presence of a finite verb is the main
# test for "this sentence asserts something".
# Inflected verb forms only. An earlier version used stems -- `valid\w+`,
# `verif\w+`, `assess\w+` -- which match the NOUNS "validation", "verification"
# and "assessment". Those are the words every factor name is made of, so the
# guard was satisfied by the exact strings it exists to see past:
# "Data Pedigree 1 Input Pedigree 0 Code/Solution Verification 0" counted as
# predicating something and survived as a claim.
_VERB = re.compile(
    r"\b(is|are|was|were|be|been|being|am|"
    r"has|have|had|do|does|did|"
    r"shall|should|will|would|can|could|may|might|must|"
    r"assign(?:s|ed)|perform(?:s|ed)|show(?:s|ed|n)|"
    r"demonstrat(?:e|es|ed)|achiev(?:e|es|ed)|provid(?:e|es|ed)|"
    r"includ(?:e|es|ed)|us(?:e|es|ed)|conduct(?:s|ed)|report(?:s|ed)|"
    r"evaluat(?:e|es|ed)|assess(?:es|ed)|indicat(?:e|es|ed)|"
    r"requir(?:e|es|ed)|obtain(?:s|ed)|compar(?:e|es|ed)|"
    r"determin(?:e|es|ed)|calculat(?:e|es|ed)|predict(?:s|ed)|"
    r"validat(?:e|es|ed)|verif(?:y|ies|ied)|scor(?:e|es|ed)|"
    r"model(?:s|ed|led)|simulat(?:e|es|ed)|represent(?:s|ed)|"
    r"correlat(?:e|es|ed)|exceed(?:s|ed)|need(?:s|ed))\b",
    re.I)

# Rubric rows: the standard's level-definition table. Detected structurally,
# by the leading bare digit that is the row's level column:
#
#     4 All data known and All input data known Reliable practices applied…
#     3 All data known and All input data known Formal practices applied…
#     2 Some data known and Some input data Documented practices applied…
#
# The first version of this matched on phrases instead -- "no evidence",
# "score of N" -- and removed three of the nine annotated gold sentences,
# because those phrases are exactly how a *finding* is worded too ("There is no
# evidence that results uncertainty or robustness analyses were performed").
# Wording does not separate a rubric from a finding; position in a table does.
_RUBRIC_ROW = re.compile(r"^\s*[0-5]\s+[A-Z]")

# Phrases that only ever appear in a rubric, never in a finding about a model.
_RUBRIC_PHRASE = re.compile(
    r"\b(all (?:input )?data known|some (?:input )?data known|"
    r"reliable practices applied|formal practices applied|"
    r"documented practices applied|informal practices applied)\b", re.I)

# Reference entries: a year in parentheses plus a page range or a DOI.
_REFERENCE = re.compile(
    r"(doi\.org/|https?://|\bpp\.\s*\d+|\b\d{4}[a-z]?\)\s*[""\"]|"
    r"\b\d+\s*\(\d+\)\s*:\s*\d+)", re.I)

# Author affiliation blocks.
_AFFILIATION = re.compile(
    r"([\w.+-]+@[\w-]+\.[\w.]+|\buniversity\b|\bnasa\s+\w+\s+(?:research\s+)?center\b|"
    r"\bcorresponding author\b)", re.I)

_MIN_WORDS = 6

# A bare gradation letter left behind by the segmenter. V&V 40 papers reproduce
# the standard's gradation table as "a. A single sample was used. b. Multiple
# samples were used..."; `sentences()` treats "a." as a sentence end, so the
# letter becomes its own fragment and the DEFINITION becomes a clean standalone
# sentence that survives every per-sentence test:
#
#   [fragment] 'b.'
#   [KEPT    ] 'Multiple samples were used, but not enough to be statistically relevant.'
#
# The definition is indistinguishable from a finding in isolation -- it has a
# verb and asserts something -- so the signal has to be positional. Only
# `strip_furniture` can see it, because only it has the surrounding list.
#
# NASA rubrics are digit-led and are caught per-sentence by `_RUBRIC_ROW`;
# V&V 40 rubrics are letter-led and are caught here. Same content, two
# standards, two shapes.
_GRADATION_LETTER = re.compile(r"^\s*[a-e][.)]\s*$")


def _looks_tabular(s: str) -> bool:
    """A row of a scoring table: mostly labels and digits, few connecting words.

    The verb test is load-bearing, not belt-and-braces. Digit density alone
    removed "The assessment score for code verification is 0 and 1 for the
    solution verification" -- a finding that quotes two scores, and one of the
    annotated gold sentences. A findings sentence about scores looks exactly like
    a score row by digit density; what separates them is that the finding
    predicates something.
    """
    toks = s.split()
    if len(toks) < 3:
        return False
    if _VERB.search(s):
        return False
    digits = sum(bool(re.fullmatch(r"\d+(?:\.\d+)?", t)) for t in toks)
    return digits >= 2 and digits / len(toks) >= 0.20


def _names_many_factors(s: str, factor_names: tuple[str, ...]) -> bool:
    """A row or header listing several factors at once.

    A finding is about one factor; a table header or a score row enumerates
    them. `Level Data pedigree Input pedigree Verification code and solution`
    outranked the real evidence for two different factors, because it contains
    every name the router is looking for.

    Uses the pack's compile-time factor list, which is the same information
    `control_constant_list` is allowed. It is NOT `evidence_keywords` -- those
    are verbatim source spans from ground truth and may never reach a matcher.
    """
    # A compound FINDING also names several factors -- "The conceptual
    # validation assessment score is 0 since studies need to be conducted ...
    # and 1 for referent validation since ligament parameters ... were
    # validated" covers two, and is the best evidence in the document for both.
    # Naming count alone removed it. What separates a header from a compound
    # finding is the same thing that separates a row label from a claim: the
    # finding predicates something.
    if _VERB.search(s):
        return False

    low = " ".join(s.split()).lower()
    # DISTINCT names, longest-first with the matched span consumed. Two traps,
    # both of which fired: callers pass the pack list concatenated with the
    # published list, so "data pedigree" occurs twice and a plain count reached
    # 2 on a sentence naming ONE factor; and shorter names are substrings of
    # longer ones, which double-counts the same words.
    hits, seen = 0, low
    for n in sorted(set(factor_names), key=len, reverse=True):
        if n and n in seen:
            hits += 1
            seen = seen.replace(n, " ")
    return hits >= 2


def classify(sentence: str, factor_names: tuple[str, ...] = ()) -> str | None:
    """Why this unit cannot be evidence, or None if it can.

    Returning the reason rather than a bool so a caller can report what was
    removed. A filter that silently drops 40% of a document is indistinguishable
    from one that is broken.
    """
    s = " ".join(sentence.split())
    if not s:
        return "empty"
    words = s.split()

    # Headings are frequently set in caps and rarely assert anything. Checked
    # before length so a short heading is reported as one rather than as a
    # generic fragment -- the reason is what a caller reviews.
    letters = [c for c in s if c.isalpha()]
    if letters and sum(c.isupper() for c in letters) / len(letters) > 0.7:
        return "heading"
    if len(words) < _MIN_WORDS:
        return "fragment"
    if _RUBRIC_ROW.match(s) or _RUBRIC_PHRASE.search(s):
        return "rubric"
    if _looks_tabular(s):
        return "table-row"
    if factor_names and _names_many_factors(s, factor_names):
        return "factor-enumeration"
    if _REFERENCE.search(s):
        return "reference"
    if _AFFILIATION.search(s):
        return "affiliation"
    # The main test, applied last so the more specific reasons are reported.
    if not _VERB.search(s):
        return "no-verb"
    return None


def running_heads(sentences: list[str], min_repeats: int = 3) -> set[str]:
    """Lines repeated across the document: journal name, page furniture.

    Repetition is what identifies these, not their content, so no pattern has to
    be written for each publisher.
    """
    counts = Counter(" ".join(s.split()).lower() for s in sentences)
    return {t for t, n in counts.items() if n >= min_repeats and len(t.split()) <= 14}


def strip_furniture(sentences: list[str], factor_names: tuple[str, ...] = (),
                    ) -> tuple[list[str], list[int], Counter]:
    """(kept sentences, their original indices, why the rest went).

    Indices are returned because a router's output is scored against sentence
    positions in the unfiltered document; losing the mapping would silently
    shift every span.
    """
    heads = running_heads(sentences)
    kept, idx, reasons = [], [], Counter()
    for i, s in enumerate(sentences):
        norm = " ".join(s.split()).lower()
        prev = sentences[i - 1] if i else ""
        if _GRADATION_LETTER.match(prev):
            reason = "rubric-definition"
        else:
            reason = "running-head" if norm in heads else classify(s, factor_names)
        if reason is None:
            kept.append(s)
            idx.append(i)
        else:
            reasons[reason] += 1
    return kept, idx, reasons

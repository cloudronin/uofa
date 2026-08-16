#!/usr/bin/env python3
"""Do the extractor's rationales cite things the source documents actually say?

Every other metric in this harness is reachable by a function that reads no
input. Emitting the pack's fixed checklist scores detection F1 0.960; predicting
the constant 2 saturates the level tolerance; `assessed` for everything scores
0.928. Groundedness is the first one a constant cannot touch, because producing
a citable claim requires having read the document.

It also needs no ground truth. The reference is the source text itself, so this
runs on the corpus as it stands rather than waiting on a regenerated one.

## Three numbers, never one

    coverage       fraction of factors given a rationale at all
    claim_density  fraction of rationales carrying >= 1 checkable claim
    groundedness   fraction of checkable claims traceable to the source

Coverage and groundedness alone are gameable, and the strategy is specific: a
backend emitting "evidence was reviewed and found adequate" for every factor
scores coverage 1.0 and contributes *zero rows* to the groundedness denominator,
because there is nothing in it to check. Contentless prose would be the optimal
play against a two-number metric. `claim_density` is what closes that -- the
contentless generator scores 0 while the LLM scores 0.565.

Read together: coverage 0 means the method wrote nothing. High coverage with low
density means it wrote filler. High density with low groundedness means it wrote
confident fiction, which for a credibility tool is worse than silence.

## The tokeniser is the metric

Measured on the 50-bundle corpus: coverage 0.974, claim density 0.565,
groundedness **0.9942** -- 859 of 864 claims, and **zero fabrications**. The five
ungrounded claims are three derived quantities, one out-of-bundle constant
(101.325 kPa, standard atmosphere), and nothing else.

That number is only worth as much as the number parsing under it, and the first
version of this file was not close. Its first pass reported 42 ungrounded rows,
of which **28 were artefacts of its own tokeniser** -- 67% against a 20% stopping
rule. Reading a range hyphen as a minus sign alone accounted for 21. A later fix
read the K in "+/-33K" as a kilo-suffix and turned 33 into 33000, inventing
twelve fresh accusations while repairing four.

The rules cut both ways, and the second direction is the quieter one. An early
`_IDENTIFIER` was case-insensitive and allowed any word between the keyword and
the number, so "table shows 88% agreement" masked the 88 -- deleting a real claim
rather than inventing a false one. Nothing downstream would have reported that;
the metric would simply have measured less than it claimed to.

So every rule here traces to a row where this metric called a correct rationale a
fabrication, or to one where it quietly declined to check a real claim, and each
is pinned in `test_groundedness.py` with that provenance. None was added to make
the number look better: the headline moved 0.959 -> 0.994 while the claim pool
*shrank* 1181 -> 864, because the artefacts were being counted in both the
numerator and the denominator.

## What this does NOT measure

**Correctness of attribution.** A rationale citing the GCI figure under
`Numerical solver error` is fully grounded and entirely wrong: the number is
real, traceable, and attached to the wrong factor. This metric measures
**fabrication** -- whether a cited quantity exists in the document -- because
that is objectively checkable without a reference answer. Whether the right
quantity was cited for the right factor is a different question and is not
scored here. Saying so is the point: the reason this harness needed repairing is
that its numbers meant less than they appeared to.

## Contamination

Claims are checked against the **source documents**. Never against
`evidence_keywords`, which are verbatim source spans lifted by the corpus
generator -- an extractor echoing the source would score 1.000 by construction,
and `score_factors` does not read them, so nothing downstream would catch it.
`assert_grounds_against_source` enforces this.
"""

from __future__ import annotations

import random
import re
import statistics
from dataclasses import dataclass, field
from pathlib import Path

# Superscript digits and minus, so "10⁻⁵" survives into a parseable exponent.
_SUPERSCRIPT = str.maketrans("⁻⁺⁰¹²³⁴⁵⁶⁷⁸⁹", "-+0123456789")

# U+2212 MINUS SIGN is what a typeset document writes; the extractor writes
# ASCII. Without this the source's "−11.2%" parses as +11.2 while the rationale's
# "-11.2%" parses as -11.2, and the row is reported as fabricated -- four rows of
# the third triage, all of them correct extractions.
_MINUS = str.maketrans("−‒", "--")

# Sources spell small counts out: "Forty-two thin-film RTD sensors", "nine speed
# lines". The extractor digitises them, correctly, and then cannot be matched.
_ONES = {"zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
         "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11,
         "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
         "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19}
_TENS = {"twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60,
         "seventy": 70, "eighty": 80, "ninety": 90}
_WORD_NUM = re.compile(
    r"\b(?:(" + "|".join(_TENS) + r")(?:[- ](" + "|".join(_ONES) + r"))?"
    r"|(" + "|".join(_ONES) + r"))\b", re.I)


def _word_to_digits(text: str) -> str:
    def sub(m: re.Match) -> str:
        tens, ones, bare = m.group(1), m.group(2), m.group(3)
        if bare:
            return str(_ONES[bare.lower()])
        return str(_TENS[tens.lower()] + (_ONES[ones.lower()] if ones else 0))
    return _WORD_NUM.sub(sub, text)

# "1 × 10⁻⁵", "1 x 10^-5", "1·10-5" all mean 1e-5. The source writes the first,
# the extractor writes "1e-5", and a naive string match calls that a fabrication
# -- verified on bundle_nasa_cfd_001, where the source reads
# "driven below 1 × 10⁻⁵ (scaled residuals)".
_SCI = re.compile(r"(\d+(?:\.\d+)?)\s*[x*]\s*10\s*\^?\s*([-+]?\d+)", re.I)

# Superscript exponents on 10, rewritten to a caret so the bare form below can
# require one. Done before the general superscript translation, which would turn
# "10⁻⁵" into the range-looking "10-5".
_SCI_SUP = re.compile(r"10\s*([⁻⁺]?[⁰¹²³⁴⁵⁶⁷⁸⁹]+)")

# "residuals < 10^-5" with no mantissa. _SCI requires one, so this parsed as the
# two numbers 10 and -5, and the -5 was reported as a fabrication -- six rows of
# the second triage. Requires the caret, so a range like "10-5" is untouched.
_SCI_BARE = re.compile(r"(?<![\d.])10\s*\^\s*([-+]?\d+)")

# A sign is only a sign at a token boundary. Without the lookbehind, "Ns 800-1200"
# yields -1200 and the row is reported as a fabrication -- the single largest
# artefact class in the first triage (21 of 42 rows).
_NUMBER = re.compile(r"(?<![\w.])[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?")

# A hyphen or dash between two digits is a range, not an operator. Applied after
# identifier masking, so "CC-2024-017" is already gone by the time this runs.
_RANGE = re.compile(r"(?<=\d)\s*[-–—]\s*(?=\d)")

# "65k" means 65,000 where the source writes it out. Lowercase only, and that is
# load-bearing: an earlier version accepted [kK] and rewrote "±33K", ">1100K" and
# "1.8K convergence" into 33000, 1100000 and 1800 -- twelve rows of fresh
# fabrication reports, more than the four it fixed. K is kelvin; k is thousands.
# The lookahead keeps the unit prefix in "28.1 kPa" out for the same reason.
_MAGNITUDE = re.compile(r"(\d+(?:\.\d+)?)k(?![A-Za-z])")

# Numbers that name a document, standard or part rather than measuring anything.
# "ISO 17025" and "CC-2024-017/018" are citations; scoring them as quantitative
# claims asks whether the *source* happens to cite the same standard, which is a
# different question from whether the extractor fabricated a figure.
#
# Case-sensitive, and the intervening token may only be uppercase. Both are
# load-bearing. An earlier version was case-insensitive and let any word sit
# between the keyword and the number, so "table shows 88% agreement" masked the
# 88 and "reference 7 locations" masked the 7 -- silently dropping real claims,
# which is the same class of defect as inventing false ones. No row in this
# corpus hit that path, so nothing would have caught it downstream.
_IDENTIFIER = re.compile(
    r"""(?:
          # ISO 9906:2012, ISO 17025, ASTM F136, NASA-STD-7009B, ASME V&V 20
          \b(?:ISO|IEC|ASME|ASTM|NASA|AIAA|ANSI|NIST|DIN|MIL|STD|SAE|API|EN|REV)
          [\s.:-]*[A-Z&]*[-\s]?\d[\w.:/-]*
          # Section 4, Rev-14c, Fig. 7 -- keyword straight onto the number
        | \b(?:Section|Rev|Ref|Doc|No|Part|Table|Figure|Fig|Eq)[\s.:-]*\d[\w.:/-]*
          # CC-2024-017/018, LX-5, TF-9
        | \b[A-Za-z]{1,4}-\d[\w./-]*
        )""",
    re.X,
)

# Values that carry no evidential weight: they appear in almost any document, so
# "grounding" them says nothing about whether the extractor read this one.
_TRIVIAL = frozenset({0.0, 1.0, 2.0, 3.0, 4.0, 5.0})


def normalise_numbers(text: str) -> set[float]:
    """Numeric *values* in a string, tolerant of how they were written.

    Compares by value rather than surface form, so 1e-5, 1E-05 and 1 × 10⁻⁵ are
    one number rather than three, and "65k" and "65,000" are one number rather
    than two.

    Identifier-like tokens are dropped rather than parsed. Every rule here was
    added because the first triage caught it accusing a correct rationale of
    fabrication; none was added to make a number look better.
    """
    if not text:
        return set()
    t = _SCI_SUP.sub(lambda m: "10^" + m.group(1).translate(_SUPERSCRIPT), text)
    t = t.translate(_SUPERSCRIPT).translate(_MINUS).replace("×", "x").replace("·", "x")
    t = _word_to_digits(t)
    t = _IDENTIFIER.sub(" ", t)
    t = _SCI.sub(r"\1e\2", t)
    t = _SCI_BARE.sub(r"1e\1", t)
    t = re.sub(r"(?<=\d),(?=\d{3}\b)", "", t)   # thousands separators only
    t = _MAGNITUDE.sub(lambda m: repr(float(m.group(1)) * 1000), t)
    t = _RANGE.sub(" to ", t)
    out: set[float] = set()
    for m in _NUMBER.finditer(t):
        try:
            out.add(float(m.group(0)))
        except ValueError:
            pass
    return out


def _decimals(value: float) -> int:
    s = repr(value)
    return len(s.split(".")[1]) if "." in s and "e" not in s else 0


def grounds(claim: float, source_values: set[float]) -> bool:
    """Is this claim traceable to something the source says?

    Exact match, or -- for a claim written with decimals -- a source value that
    rounds to it at the claim's own precision, so a rationale reporting 28.6
    against a source reading 28.61 is grounded.

    The tolerance is deliberately precision-derived rather than a fixed epsilon:
    it admits rounding and nothing else. An integer claim must match exactly,
    because rounding 65 to zero places would ground it against anything in
    [64.5, 65.5) and that is a licence, not a tolerance.
    """
    if claim in source_values:
        return True
    # Documents state a magnitude and put the direction in words -- "a correction
    # to predicted efficiency of up to 1.2 percentage points" -- and the
    # extractor writes "-1.2%". The number came from the document, so this is not
    # fabrication, which is the only thing this metric claims to measure.
    #
    # Deliberately one-directional: a negative claim may match a positive source
    # value, never the reverse. And it is a real weakening -- "-9.99%" grounds
    # against a source reading "9.99%" -- recorded here rather than in a note,
    # because the sign is not checked and no caller should assume it is.
    if claim < 0 and -claim in source_values:
        return True
    d = _decimals(claim)
    return d > 0 and any(round(v, d) == claim for v in source_values)


def checkable_claims(rationale: str) -> set[float]:
    """The claims in a rationale that can be checked against a document.

    Bare small integers are excluded: "3 meshes" grounds against any document
    containing a 3, which is nearly all of them, and counting it would inflate
    both density and groundedness without evidence.
    """
    return {v for v in normalise_numbers(rationale) if v not in _TRIVIAL}


# Two rationales count as the same span when they share this much of their
# vocabulary. Exact repetition scores 1.0; the threshold also catches a method
# that quotes overlapping windows of one paragraph for every factor.
_OVERLAP_THRESHOLD = 0.60


@dataclass
class GroundednessResult:
    factors_total: int = 0
    factors_with_rationale: int = 0
    rationales_with_claims: int = 0
    claims_total: int = 0
    claims_grounded: int = 0
    factors_distinct: int = 0
    ungrounded: list[dict] = field(default_factory=list)

    @property
    def coverage(self) -> float:
        return self.factors_with_rationale / self.factors_total if self.factors_total else 0.0

    @property
    def claim_density(self) -> float:
        n = self.factors_with_rationale
        return self.rationales_with_claims / n if n else 0.0

    @property
    def distinctness(self) -> float:
        """Fraction of rationales that do not restate another in the same bundle.

        The fourth number, and it is not implied by the other three. Measured:
        a control quoting one sentence of the source for all thirteen factors
        scores coverage 1.000, claim density 1.000 AND groundedness 1.000 --
        every figure it cites is real, and every rationale carries one. Reading
        the three together does not catch it, because density counts rationales
        that carry a claim, never whether they carry the *same* claim.

        Distinctness is what separates "found thirteen pieces of evidence" from
        "found one and pasted it thirteen times", and for an extractive method
        that is the whole question.
        """
        n = self.factors_with_rationale
        return self.factors_distinct / n if n else 0.0

    @property
    def groundedness(self) -> float:
        """Undefined without claims -- deliberately 0.0, not 1.0.

        A method that makes no checkable claim has not demonstrated grounding;
        returning 1.0 would reward saying nothing, which is the failure mode
        `claim_density` exists to expose.
        """
        return self.claims_grounded / self.claims_total if self.claims_total else 0.0

    def as_dict(self) -> dict:
        return {
            "coverage": self.coverage,
            "claim_density": self.claim_density,
            "groundedness": self.groundedness,
            "factors_total": self.factors_total,
            "factors_with_rationale": self.factors_with_rationale,
            "rationales_with_claims": self.rationales_with_claims,
            "claims_total": self.claims_total,
            "claims_grounded": self.claims_grounded,
            "distinctness": self.distinctness,
            "factors_distinct": self.factors_distinct,
        }


def assert_grounds_against_source(source_text: str, ground_truth: dict | None) -> None:
    """Fail loudly if the reference looks like ground truth rather than sources.

    Guards the property that makes the number a measurement: an extractor is
    scored against what the *document* says, never against spans the corpus
    generator lifted out of it.
    """
    if not ground_truth:
        return
    keywords = [kw for f in ground_truth.get("expected_factors", [])
                for kw in f.get("evidence_keywords", [])]
    if not keywords:
        return
    present = sum(1 for kw in keywords if kw and kw in source_text)
    # Source text legitimately contains its own spans; what must never happen is
    # the reference *being* the keyword list rather than the documents.
    if len(source_text) < sum(len(k) for k in keywords) * 2:
        raise SystemExit(
            "CONTAMINATION: the grounding reference is too small to be the source "
            f"documents ({len(source_text)} chars against {len(keywords)} evidence "
            "keywords). Ground against bundle_*/source/, not evidence_keywords."
        )
    del present


def _tokens(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9.%-]+", text.lower()) if len(w) > 2}


def _restates(a: set[str], b: set[str]) -> bool:
    """Do two rationales say substantially the same thing?

    Containment rather than symmetric Jaccard: a method that quotes a long
    paragraph for one factor and a sentence of that same paragraph for another
    has restated it, and Jaccard would score that pair as different because the
    lengths differ.
    """
    if not a or not b:
        return False
    return len(a & b) / min(len(a), len(b)) >= _OVERLAP_THRESHOLD


def score_factor_rationales(factors: list[dict], source_text: str,
                            ground_truth: dict | None = None) -> GroundednessResult:
    """Score one bundle's extracted factors against its source documents.

    `factors` are the dicts `score_extraction.parse_extracted_xlsx` produces,
    which already carry `rationale` -- the field the scorer parsed and discarded
    before this existed.
    """
    assert_grounds_against_source(source_text, ground_truth)
    source_values = normalise_numbers(source_text)

    res = GroundednessResult()
    for f in factors:
        res.factors_total += 1
        rationale = f.get("rationale")
        if not isinstance(rationale, str) or not rationale.strip():
            continue
        res.factors_with_rationale += 1

        claims = checkable_claims(rationale)
        if not claims:
            continue
        res.rationales_with_claims += 1

        missing = sorted(c for c in claims if not grounds(c, source_values))
        res.claims_total += len(claims)
        res.claims_grounded += len(claims) - len(missing)
        if missing:
            res.ungrounded.append({
                "factor_type": f.get("factor_type"),
                "missing": missing,
                "rationale": rationale,
            })

    # Distinctness, computed over the bundle rather than per row: a rationale is
    # distinct when no *other* rationale in the same bundle restates it.
    texts = [f.get("rationale") for f in factors
             if isinstance(f.get("rationale"), str) and f.get("rationale").strip()]
    toks = [_tokens(x) for x in texts]
    for i, ti in enumerate(toks):
        if not any(_restates(ti, tj) for j, tj in enumerate(toks) if i != j):
            res.factors_distinct += 1
    return res


@dataclass
class AttributionResult:
    """What attribution scoring returns, in the shape GroundednessResult set.

    `(right, scored)` was a two-integer return, and every question anyone
    actually asked of it needed a third number that had been thrown away:

    - **abstention is invisible.** A factor with no reference keywords is
      skipped, so it leaves the denominator entirely. On the shipped corpus the
      reported rate is 0.638 and `rate_over_gold` -- the same numerator over
      every gold-scorable factor -- is 0.537. Abstaining inflates the headline
      by ten points, and the two-integer return could not show it.
    - **loose and verbatim were merged.** The rule counts a paraphrase, which is
      right (98% of sonnet's rationales are written rather than quoted, so a
      verbatim-only rule scored it 0.422 against K6's 0.645 and would have read
      as "a TF-IDF classifier attributes better than sonnet"). But the two
      numbers say different things and only one was ever reported: 0.638 loose
      against 0.364 verbatim.
    - **the two failure kinds were summed.** Misfiled and unmatched call for
      opposite responses; see `attribution_confusion`.
    - **length was not recorded**, and length is the metric's known defect: a
      20-sentence shotgun scores 0.9284 against the extractor's 0.6383. A run
      that does not record its own rationale lengths cannot be compared to the
      null battery afterwards.

    `rate` stays the historical number so nothing silently re-baselines. Report
    it beside `rate_over_gold`, never alone.
    """

    scored: int = 0                 # rationales with a usable reference
    right: int = 0                  # ... that matched, loose rule
    right_verbatim: int = 0         # ... that quoted the reference outright
    gold_scorable: int = 0          # factors the gold could have scored
    abstained: int = 0              # gold-scorable factors not scored
    misfiled: int = 0
    unmatched: int = 0
    extra_factor_rows: int = 0      # emitted factors absent from the gold
    rationale_tokens: list[int] = field(default_factory=list)
    permutation_null: float | None = None

    @property
    def rate(self) -> float:
        """The historical figure: matched over scored. Never report alone."""
        return self.right / self.scored if self.scored else 0.0

    @property
    def rate_verbatim(self) -> float:
        return self.right_verbatim / self.scored if self.scored else 0.0

    @property
    def rate_over_gold(self) -> float:
        """Matched over every factor the gold could have scored.

        Abstention counted wrong rather than counted nowhere. This is the number
        that does not improve when the extractor declines to answer.
        """
        return self.right / self.gold_scorable if self.gold_scorable else 0.0

    @property
    def tokens_median(self) -> float:
        return statistics.median(self.rationale_tokens) if self.rationale_tokens else 0.0

    @property
    def tokens_p90(self) -> float:
        if not self.rationale_tokens:
            return 0.0
        ordered = sorted(self.rationale_tokens)
        return float(ordered[min(len(ordered) - 1, int(0.9 * len(ordered)))])

    def as_dict(self) -> dict:
        return {
            "rate": self.rate,
            "rate_verbatim": self.rate_verbatim,
            "rate_over_gold": self.rate_over_gold,
            "correct": self.right,
            "correct_verbatim": self.right_verbatim,
            "scored": self.scored,
            "gold_scorable": self.gold_scorable,
            "abstained": self.abstained,
            "misfiled": self.misfiled,
            "unmatched": self.unmatched,
            "extra_factor_rows": self.extra_factor_rows,
            "rationale_tokens_median": self.tokens_median,
            "rationale_tokens_p90": self.tokens_p90,
            # The raw lengths, not just their summary. A median of medians is
            # not a median, and the whole point of recording length is to place
            # the candidate on the shotgun sweep -- which needs the real
            # distribution once bundles are pooled.
            "rationale_tokens": list(self.rationale_tokens),
            "permutation_null": self.permutation_null,
        }


def assert_attribution_available(result: AttributionResult) -> None:
    """An unmeasured attribution may not render as a passed one.

    `score_attribution` returns zeros when the ground truth carries no
    `evidence_keywords`, and zeros render as an omitted row -- indistinguishable
    from "not run". That is the vacuous-pass class AGENTS.md 13 already names:
    *if a thing was not measured, say so where the result is read.*

    Callers that intend to report attribution call this first, so a corpus with
    no reference fails loudly instead of quietly reporting nothing.
    """
    if result.scored == 0:
        raise SystemExit(
            "ATTRIBUTION NOT MEASURED: no factor carried a usable reference "
            f"(gold_scorable={result.gold_scorable}, "
            f"extra_factor_rows={result.extra_factor_rows}). This renders as an "
            "omitted row, which reads as a pass. Score against a corpus whose "
            "ground truth carries evidence_keywords, or state that attribution "
            "was not measured where the result is read."
        )


def score_attribution_full(factors: list[dict], ground_truth: dict) -> AttributionResult:
    """`score_attribution`, keeping everything it used to discard.

    Same rule, same numbers -- `res.right, res.scored` is exactly what
    `score_attribution` returns, and a test pins that on the live corpus.
    """
    res = AttributionResult()
    if not ground_truth:
        return res
    want = _keyword_table(ground_truth)
    res.gold_scorable = sum(1 for kws in want.values() if kws)

    seen: set[str] = set()
    for f in factors:
        name = f.get("factor_type")
        rationale = f.get("rationale")
        if name not in want:
            res.extra_factor_rows += 1
            continue
        seen.add(name)
        kws = want.get(name) or []
        if not isinstance(rationale, str) or not rationale.strip() or not kws:
            continue
        res.scored += 1
        res.rationale_tokens.append(len(_tokens(rationale)))
        if _matches(rationale, kws):
            res.right += 1
            if any(k in " ".join(rationale.split()).lower() for k in kws):
                res.right_verbatim += 1
            continue
        others = [o for o, oks in want.items()
                  if o != name and oks and _matches(rationale, oks)]
        if others:
            res.misfiled += 1
        else:
            res.unmatched += 1

    res.abstained = res.gold_scorable - res.scored
    return res


def score_attribution(factors: list[dict], ground_truth: dict) -> tuple[int, int]:
    """Is each rationale about the factor it was filed under?

    The fifth number, and the only one that sees *which* factor a piece of
    evidence was assigned to. This module's own docstring disclaims it --
    "a real figure cited under the wrong factor scores as grounded" -- and for
    a long time that was the right call, because there was no reference to
    check attribution against without a gold rationale.

    There is one: `evidence_keywords` are verbatim source spans, and a
    rationale filed under factor F is correctly attributed when it contains one
    of F's keywords.

    Measured in the keyless pipeline, this is the difference between a detector
    and no detector. A constant router that walks the document in order scores
    coverage 1.000, density 0.586, groundedness 1.000 and distinctness 1.000 --
    and attribution **0.058**. The other four cannot tell it apart from a real
    router; this one separates it by 11x.

    ## Paraphrase must count, or the metric only measures quoting

    An exact-substring test is biased toward extractive methods by
    construction. Measured: **98% of sonnet's rationales are written rather
    than quoted**, so a verbatim check scored it 0.422 against K6's 0.645 --
    and reading that as "a TF-IDF classifier attributes better than sonnet"
    would have been wrong. It says the classifier quotes and the model
    paraphrases.

    So a rationale counts as attributed when it either contains a keyword
    outright or shares at least half that keyword's content tokens. The
    threshold is deliberately loose: the question is which *factor* the
    evidence belongs to, not how closely it was reworded.

    ## The rule that makes it legitimate

    Using `evidence_keywords` as an evaluation reference is sound. Using them
    to *seed a matcher* is not, and neither is scoring a method on bundles it
    was trained on. Both would be measuring the answer against itself. Callers
    that train anything must pass held-out bundles only.
    """
    if not ground_truth:
        return 0, 0
    want = _keyword_table(ground_truth)
    right = scored = 0
    for f in factors:
        rationale = f.get("rationale")
        kws = want.get(f.get("factor_type")) or []
        if not isinstance(rationale, str) or not rationale.strip() or not kws:
            continue
        scored += 1
        if _matches(rationale, kws):
            right += 1
    return right, scored


def _keyword_table(ground_truth: dict) -> dict[str, list[str]]:
    """factor -> its usable reference keywords. Shared so nothing can diverge."""
    return {f.get("factor_type"): [k for k in
                                   (" ".join(str(k).split()).lower()
                                    for k in (f.get("evidence_keywords") or []))
                                   if len(k) >= 4]
            for f in ground_truth.get("expected_factors", [])}


def _matches(rationale: str, keywords: list[str]) -> bool:
    """The attribution rule itself, in one place.

    Quoted outright, or at least half the keyword's content tokens present.
    Extracted from score_attribution so attribution_confusion below asks the
    identical question of every other factor -- a confusion table computed by a
    slightly different rule than the score it explains is worse than no table.
    """
    low = " ".join(rationale.split()).lower()
    toks = set(re.findall(r"[a-z0-9.%-]{3,}", low))
    for k in keywords:
        if k in low:                                      # quoted outright
            return True
        ktok = set(re.findall(r"[a-z0-9.%-]{3,}", k))
        if ktok and len(ktok & toks) / len(ktok) >= 0.5:  # paraphrased
            return True
    return False


def attribution_confusion(factors: list[dict], ground_truth: dict) -> list[dict]:
    """For each attribution failure, which factor's evidence did it match instead?

    `score_attribution` returns a count. A count of 142 failures is 142
    anonymous events; the same failures resolved into pairs are a short ranked
    list of confusable factors, and that list is actionable where the count is
    not.

    Two failure kinds, kept separate and never summed in prose:

      misfiled   the rationale matches some OTHER factor's keywords. The
                 evidence is in the document and filed under the wrong heading.
      unmatched  it matches nothing. Either the rationale cites evidence the
                 annotation does not cover, or it cites nothing checkable.

    They call for opposite responses -- misfiling is a routing problem, and
    unmatched is a coverage or a substance problem -- so a combined "attribution
    failures: 142" tells you which action to take exactly never.

    A rationale can match several other factors; all are recorded. This reads
    the same `evidence_keywords` as the score, under the same rule, so a row
    here always corresponds to a miss there.
    """
    if not ground_truth:
        return []
    want = _keyword_table(ground_truth)
    out: list[dict] = []
    for f in factors:
        filed = f.get("factor_type")
        rationale = f.get("rationale")
        kws = want.get(filed) or []
        if not isinstance(rationale, str) or not rationale.strip() or not kws:
            continue
        if _matches(rationale, kws):
            continue
        others = sorted(other for other, oks in want.items()
                        if other != filed and oks and _matches(rationale, oks))
        out.append({"filed_under": filed,
                    "matches": others,
                    "kind": "misfiled" if others else "unmatched"})
    return out


# Wording a document uses to state a verdict. Absence of all of it means the
# document does not record a decision, whatever the extractor wrote down.
_VERDICT_WORDS = re.compile(
    r"\b(?:accepted|approved|rejected|declined|denied|not accepted|not approved|"
    r"adequate for|sufficient for|fit for (?:the )?purpose|cleared for|"
    r"authoris?ed for|endorsed|unfit|withheld|do(?:es)? not (?:meet|satisfy))\b",
    re.I)


def field_is_supported(value: str, source_text: str, field: str) -> bool:
    """Could this value have been read out of the document at all?

    Separate from whether it is *correct*. A decision outcome is supported when
    the source contains verdict wording somewhere; a free-text value is
    supported when it appears in the source.

    ## Why this exists

    `expected_decision.outcome` is in ground truth for every bundle, and the
    source states no verdict in **78%** of them -- the ground truth outcome is
    the corpus generator's inference. Scored against it, sonnet invents an
    outcome in 77% of bundles and scores **0.914**, against a constant's 0.878.

    Two models inferring the same base rate agree with each other, and the
    scorer records that agreement as extraction. It is not: nothing was read.
    """
    if not isinstance(value, str) or not value.strip():
        return False
    if field == "decision_outcome":
        return bool(_VERDICT_WORDS.search(source_text))
    return " ".join(value.split()).lower() in " ".join(source_text.split()).lower()


def score_field(value: str, expected: str, source_text: str,
                field: str) -> str:
    """One of four outcomes, never collapsed into "correct".

        grounded_correct     read it, got it right      -- extraction
        grounded_wrong       read it, got it wrong      -- misreading
        unsupported_correct  guessed, got it right      -- LUCK
        unsupported_wrong    guessed, got it wrong      -- fabrication

    Reporting only accuracy merges the first and third, which is how a field
    invented in 77% of bundles came to read as 0.914. The pair a credibility
    tool must not confuse is `grounded_correct` and `unsupported_correct`:
    identical in the output, opposite in what they say about the method.

    An extractor that abstains where the document is silent should be scored
    ABOVE one that guesses correctly, because a recorded decision nobody made
    is worse than a blank -- an absent field is visibly absent, an invented one
    is indistinguishable from a real one.
    """
    supported = field_is_supported(value, source_text, field)
    correct = (str(value).strip().lower() == str(expected).strip().lower())
    return f"{'grounded' if supported else 'unsupported'}_" \
           f"{'correct' if correct else 'wrong'}"


def field_score(verdicts: dict[str, int]) -> dict[str, float]:
    """Accuracy and groundedness combined the way F1 combines P and R.

    Takes the four-way counts from `score_field` and returns three numbers:

        accuracy      got it right, however it got there
        groundedness  could have read it, right or not
        harmonic      2AG/(A+G) -- high only when BOTH are

    ## Why harmonic, and why not over the four categories

    The four verdicts partition the total, so a harmonic mean *of them* is
    minimised by the ideal outcome: all `grounded_correct` puts three zeros in
    the denominator and scores 0. Combining two independent rates is the form
    that works, and it is the same argument F1 makes about precision and
    recall -- a method may not be excused one by excelling at the other.

    What it buys, measured:

        variant                     acc    grnd   harmonic
        pure guesser at 91% base   0.914   0.000     0.000
        old corpus                 0.910   0.230     0.367
        new corpus                 1.000   1.000     1.000

    A function that ignores the document and answers "Accepted" scores 0.914
    on accuracy and **zero** here, which is what a credibility tool should say
    about it. The old corpus drops from a flattering 0.910 to 0.367 -- right
    most of the time, for the wrong reason.
    """
    n = sum(verdicts.values())
    if not n:
        return {"accuracy": 0.0, "groundedness": 0.0, "harmonic": 0.0}
    acc = (verdicts.get("grounded_correct", 0)
           + verdicts.get("unsupported_correct", 0)) / n
    grd = (verdicts.get("grounded_correct", 0)
           + verdicts.get("grounded_wrong", 0)) / n
    h = 0.0 if (acc + grd) == 0 else 2 * acc * grd / (acc + grd)
    return {"accuracy": acc, "groundedness": grd, "harmonic": h}


def read_source_text(bundle_dir: Path) -> str:
    """Concatenate a bundle's source documents. This is the grounding reference.

    PDFs go through the reader. They used to go through `read_text(errors=
    "ignore")`, which on a PDF returns its raw object syntax -- 1.5 MB of
    `/Rect [ 161.802002 134.589005 ... ]`, font tables and object ids for one
    paper. Every coordinate in that is a number, so a rationale's figures could
    ground against typesetting geometry that no reader would call evidence.

    Found 2026-08-15 when a triage printed the "source" a claim had matched and
    it was a PDF link rectangle.

    **The bias is PESSIMISTIC, and an earlier version of this docstring had the
    direction backwards.** The intuition -- raw bytes carry more numbers, so
    claims ground too easily -- is wrong, because PDF text lives in compressed
    streams. `read_text` surfaces structure and metadata, not sentences. Measured
    on bologna: the raw reading carries 761 spurious decimals AND is missing 15
    of the 39 decimals that appear in the prose, so **38% of genuine figures were
    unfindable** and honest claims failed to ground.

    Confirmed by the re-score: the frontier arm's groundedness went 0.621 ->
    1.000 when the noise was removed. Removing junk RAISED the score, which is
    only possible if the junk was suppressing real matches.

    The withdrawal of those figures was still correct. The stated reason for it
    was not, and it was asserted with more confidence than an unmeasured
    direction deserved.

    Only bundles with PDFs were affected -- the synthetic corpus is markdown,
    where `read_text` is correct and this change is a no-op.
    """
    src = Path(bundle_dir) / "source"
    if not src.is_dir():
        raise SystemExit(f"{bundle_dir} has no source/ directory to ground against")

    parts: list[str] = []
    for p in sorted(src.glob("*")):
        if not p.is_file():
            continue
        if p.suffix.lower() == ".pdf":
            from uofa_cli.readers.pdf_reader import read_pdf  # noqa: WPS433
            parts.append("\n".join(c.text for c in read_pdf(p)))
        else:
            parts.append(p.read_text(errors="ignore"))
    return "\n".join(parts)


def print_groundedness(res: GroundednessResult) -> None:
    print(f"\n  RATIONALE GROUNDEDNESS")
    print(f"  {'─' * 50}")
    print(f"  Coverage:      {res.coverage:.0%} ({res.factors_with_rationale}/{res.factors_total} factors)")
    print(f"  Claim density: {res.claim_density:.0%} ({res.rationales_with_claims}/{res.factors_with_rationale} carry a checkable claim)")
    print(f"  Groundedness:  {res.groundedness:.3f} ({res.claims_grounded}/{res.claims_total} claims trace to source)")
    if res.ungrounded:
        print(f"  Ungrounded rationales: {len(res.ungrounded)}")
    print(f"  {'─' * 50}")
    print("  Measures fabrication, not attribution: a real number cited under the")
    print("  wrong factor scores as grounded.")


# ── the null battery ─────────────────────────────────────────
#
# Every other metric in this harness is reported against a null that reads no
# input, because that is what makes a scalar interpretable. Attribution shipped
# without one for months, and when the nulls were finally built they
# disqualified it: a "shotgun" rationale of k random source sentences, filed
# identically under EVERY factor and carrying no attribution judgment at all,
# beats the real extractor once k is large enough.
#
#     the real extractor   0.6383
#     shotgun k=5          0.5884
#     shotgun k=12         0.7740
#     shotgun k=20         0.9284
#
# That is the same failure as detection F1, one metric to the right, and it is
# why Phase 3 replaces the rule rather than tuning its threshold.
#
# There IS signal underneath. A label-shuffle permutation null -- the extractor's
# own rationales, reassigned to factors at random -- scores 0.0955 +/- 0.0145, so
# 0.638 sits about 37 standard deviations above chance. The metric is
# unnormalised, not meaningless. Both facts have to be reported together: the
# permutation null alone reads as "far above chance, therefore good", and the
# length sweep alone reads as "meaningless".


def _rationale_pool(factors: list[dict]) -> list[str]:
    return [f["rationale"] for f in factors
            if isinstance(f.get("rationale"), str) and f["rationale"].strip()]


def null_document_order(factor_names: list[str], sentences_: list[str]) -> list[dict]:
    """Walk the document in order, one sentence per factor. Reads no labels.

    The constant router. Measured at 0.058 in the keyless pipeline against a
    real router's 0.62, which is the one place attribution has behaved like a
    discriminating metric.
    """
    return [{"factor_type": n, "rationale": sentences_[i % len(sentences_)]}
            for i, n in enumerate(factor_names)] if sentences_ else []


def null_first_sentence(factor_names: list[str], sentences_: list[str]) -> list[dict]:
    """One sentence of the document, pasted under every factor."""
    return [{"factor_type": n, "rationale": sentences_[0]}
            for n in factor_names] if sentences_ else []


def null_shotgun(factor_names: list[str], sentences_: list[str], k: int,
                 seed: int = 0) -> list[dict]:
    """k random source sentences, the SAME blob under every factor.

    Carries zero attribution judgment by construction: every factor gets an
    identical rationale, so nothing about it can be about which factor it was
    filed under. Whatever it scores is what length alone buys.
    """
    if not sentences_:
        return []
    rng = random.Random(seed)
    blob = " ".join(rng.sample(sentences_, min(k, len(sentences_))))
    return [{"factor_type": n, "rationale": blob} for n in factor_names]


def permutation_null(factors: list[dict], ground_truth: dict,
                     iterations: int = 200, seed: int = 0) -> dict:
    """Chance level for THIS run: its own rationales, labels shuffled.

    Computed on the run's own rationales rather than on synthetic text, so it
    inherits their length and vocabulary. That is the point -- a null written
    independently would differ from the candidate in length as well as in
    attribution, and length is the confound under investigation.

    Milliseconds for 200 iterations; there is no reason to report attribution
    without it.
    """
    pool = _rationale_pool(factors)
    names = [f.get("factor_type") for f in factors]
    if len(pool) < 2:
        return {"mean": 0.0, "sd": 0.0, "iterations": 0}

    rng = random.Random(seed)
    rates = []
    for _ in range(iterations):
        shuffled = pool[:]
        rng.shuffle(shuffled)
        permuted = [{"factor_type": n, "rationale": r}
                    for n, r in zip(names, shuffled)]
        right, scored = score_attribution(permuted, ground_truth)
        if scored:
            rates.append(right / scored)
    if not rates:
        return {"mean": 0.0, "sd": 0.0, "iterations": 0}
    return {"mean": statistics.mean(rates),
            "sd": statistics.pstdev(rates) if len(rates) > 1 else 0.0,
            "iterations": len(rates)}


def null_battery(factors: list[dict], ground_truth: dict, sentences_: list[str],
                 seed: int = 0) -> dict:
    """Every null, plus the length sweep, in one call.

    Returns {name: rate}. A candidate that any of these reaches has not
    demonstrated attribution, and the shotgun row that reaches it tells you at
    what rationale length it stopped meaning anything.
    """
    names = [f.get("factor_type") for f in factors if f.get("factor_type")]
    if not names:
        return {}

    def rate(rows: list[dict]) -> float | None:
        right, scored = score_attribution(rows, ground_truth)
        return right / scored if scored else None

    out = {
        "document_order": rate(null_document_order(names, sentences_)),
        "first_sentence": rate(null_first_sentence(names, sentences_)),
    }
    for k in (1, 5, 12, 20):
        out[f"shotgun_k{k}"] = rate(null_shotgun(names, sentences_, k, seed))
    out["permutation"] = permutation_null(factors, ground_truth, seed=seed)["mean"]
    return out


# ── Phase 3: attribution that length cannot buy ──────────────


def _sentence_offsets(text: str, sents: list[str]) -> list[tuple[int, int]]:
    """Character span of each sentence in the normalised text.

    Lifted from v1_real_attribution rather than rewritten. Matching a reference
    *inside* one sentence fails: references are what a reviewer would cite, and
    those run across the segmenter's boundaries. Map by character offset and
    accept every sentence the reference touches.
    """
    flat = _norm_ws(text)
    offs, cur = [], 0
    for s in sents:
        n = _norm_ws(s)
        i = flat.find(n, cur)
        if i < 0:
            i = cur
        offs.append((i, i + len(n)))
        cur = i + len(n)
    return offs


def _norm_ws(s: str) -> str:
    return " ".join(str(s).split()).lower()


def _is_furniture(s: str) -> bool:
    """Heading, table row, bullet or rule -- document structure, not evidence.

    Measured on the shipped corpus: 783 of the raw gold sentences are furniture,
    because an `evidence_keywords` fragment lands in a markdown heading or a
    table row often enough to matter. That records a location no reviewer would
    cite and no extractor should be asked to hit, and it penalises a rule that
    correctly finds the prose sentence carrying the same evidence.

    Adjudicating the rows where the old and new rules disagreed, 91 of 176 -- at
    least 52%, and the true figure is higher because the auto-triage was
    conservative -- were this, not a rule error.

    A defect in the reference is not a defect in what is scored against it.
    """
    t = s.lstrip()
    return t.startswith(("#", "|", "*", "---", "===")) or (
        t.startswith("-") and not t[1:2].isdigit())


def gold_sentence_sets(ground_truth: dict, text: str, sents: list[str],
                       drop_furniture: bool = True) -> dict[str, set[int]]:
    """factor -> the sentence indices its reference keywords land in.

    `drop_furniture=False` reproduces the raw sets, so both numbers can be
    reported and the filter's effect on the nulls can be checked. A filter that
    lifts the nulls is removing difficulty rather than noise.
    """
    flat = _norm_ws(text)
    offs = _sentence_offsets(text, sents)
    gold: dict[str, set[int]] = {}
    for f in ground_truth.get("expected_factors", []):
        name = f.get("factor_type")
        for kw in f.get("evidence_keywords") or []:
            n = _norm_ws(kw)
            if len(n) < 4:
                continue
            start = flat.find(n)
            if start < 0:
                continue
            end = start + len(n)
            for i, (lo, hi) in enumerate(offs):
                if lo < end and start < hi:
                    if drop_furniture and _is_furniture(sents[i]):
                        continue
                    gold.setdefault(name, set()).add(i)
    return gold


def _token_f1(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    inter = len(a & b)
    if not inter:
        return 0.0
    p, r = inter / len(b), inter / len(a)
    return 2 * p * r / (p + r)


def locate_sentence(text: str, sents: list[str],
                    sent_tokens: list[set[str]] | None = None) -> int | None:
    """Which source sentence is this text about? argmax token-F1.

    F1 rather than raw overlap is what makes the rule length-invariant. Overlap
    grows monotonically as the candidate text gets longer -- which is precisely
    the defect being repaired -- while F1 penalises a candidate that matches a
    sentence by simply containing everything.
    """
    tt = _tokens(text)
    if not tt:
        return None
    toks = sent_tokens if sent_tokens is not None else [_tokens(s) for s in sents]
    best, best_score = None, 0.0
    for i, st in enumerate(toks):
        score = _token_f1(st, tt)
        if score > best_score:
            best, best_score = i, score
    return best


def score_attribution_by_sentence(factors: list[dict], ground_truth: dict,
                                  text: str, sents: list[str],
                                  field: str = "rationale",
                                  drop_furniture: bool = True) -> AttributionResult:
    """Attribution scored in sentence indices, not keyword overlap.

    The unit `attribution_agreement.py` and `d1_annotator_agreement.py` already
    score in, which is what finally makes the 91.3% same-sentence agreement
    figure commensurable with the metric.

    A rationale is correctly attributed when the sentence it is most about is
    one of the sentences its factor's evidence lives in. Length buys nothing: a
    longer text does not become *more about* any particular sentence, because
    token-F1 penalises the extra tokens that match nothing.

    Honest cost, measured: the headline falls from 0.638 to roughly 0.418. That
    is the price of a number a verbose null cannot reach.

    `field` selects the text scored. The pre-registered primary is `rationale`;
    `evidence_span` is reported beside it, per studies/evidence-span/.
    """
    res = AttributionResult()
    gold = gold_sentence_sets(ground_truth, text, sents, drop_furniture)
    res.gold_scorable = sum(1 for v in gold.values() if v)
    if not gold:
        return res

    sent_tokens = [_tokens(s) for s in sents]
    for f in factors:
        name = f.get("factor_type")
        value = f.get(field)
        if name not in gold or not gold[name]:
            if name not in gold:
                res.extra_factor_rows += 1
            continue
        if not isinstance(value, str) or not value.strip():
            continue
        res.scored += 1
        res.rationale_tokens.append(len(_tokens(value)))
        predicted = locate_sentence(value, sents, sent_tokens)
        if predicted is not None and predicted in gold[name]:
            res.right += 1
            if _norm_ws(value) in _norm_ws(text):
                res.right_verbatim += 1
        elif predicted is not None and any(predicted in g for g in gold.values()):
            res.misfiled += 1        # localised, but to another factor's evidence
        else:
            res.unmatched += 1       # localised nowhere any factor's evidence lives

    res.abstained = res.gold_scorable - res.scored
    return res

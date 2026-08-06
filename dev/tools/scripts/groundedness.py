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

import re
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


@dataclass
class GroundednessResult:
    factors_total: int = 0
    factors_with_rationale: int = 0
    rationales_with_claims: int = 0
    claims_total: int = 0
    claims_grounded: int = 0
    ungrounded: list[dict] = field(default_factory=list)

    @property
    def coverage(self) -> float:
        return self.factors_with_rationale / self.factors_total if self.factors_total else 0.0

    @property
    def claim_density(self) -> float:
        n = self.factors_with_rationale
        return self.rationales_with_claims / n if n else 0.0

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
    return res


def read_source_text(bundle_dir: Path) -> str:
    """Concatenate a bundle's source documents. This is the grounding reference."""
    src = Path(bundle_dir) / "source"
    if not src.is_dir():
        raise SystemExit(f"{bundle_dir} has no source/ directory to ground against")
    return "\n".join(p.read_text(errors="ignore") for p in sorted(src.glob("*")))


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

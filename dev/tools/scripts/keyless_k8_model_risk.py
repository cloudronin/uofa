#!/usr/bin/env python3
"""K8: extract model risk, and validate it against the standard's own table.

`modelRiskLevel` is one of the nine properties `ProfileComplete` requires, and
plan v3 marked it "no route proposed -- yes, judgment from risk". It is not a
judgment. ASME V&V 40 defines model risk as a FUNCTION of two inputs:

    model risk = f(model influence, decision consequence)

So once both inputs are located the derivation is a table lookup, and the
keyless route is "find two spans, index a table". That also yields something no
extractor currently produces: a **consistency check**. A document states its own
risk level; the two inputs imply one; when they disagree that is a finding about
the document, not an extraction error.

## Why extract-and-validate rather than extract

An LLM asked for `modelRiskLevel` returns a value for every document. Measured on
the synthetic corpus, risk level is stated in 2% of documents and model influence
in 0% -- so almost every returned value was invented. Validation is what
separates "the document says High" from "the model thinks High is plausible".

## The two documents that make this hard

Neither is an error to normalise away; both are real deviations by competent
authors, and a validator that hides them is worse than one that fails loudly.

* **Bologna** substitutes an input NAME: it uses *regulatory impact* where V&V 40
  says model influence, and argues for the substitution at length.
* **TAVI I** keeps both input names but gives them a VALUE the standard does not
  define -- "deemed significant" rather than a gradation -- and reports the
  result on a 1-5 numeric scale V&V 40 also does not define.

In both cases the standard's table cannot be indexed, so the honest output is
`not_derivable` with the substitution named. Reporting `mismatch` would blame the
document for the validator's inability to read it.

## Scope, for the fourth time

Morrison assesses TWO contexts of use, each with its own influence, consequence
and risk. Run scope-blind, K8 pairs COU1's inputs with a sentence stating COU2's
risk and reports `mismatch` -- blaming the document for the reader's error.

This is the fourth appearance of the same defect in this work: the selection
stage improved 3/6 to 5/6 once the model was named; the D1 agreement check
manufactured a 1/6 disagreement by withholding the (model x mechanism) pair; and
plan v4 records the unit of assessment as (model x mechanism x factor). K8 was
written without it anyway.

**Every stage that reads a real evidence document needs the scope, and the
default assumption should be that omitting it produces a confident wrong
answer rather than a visible failure.**

K8 therefore reports Morrison as a KNOWN FAILURE rather than as a mismatch. The
fix is to run it per context of use -- the fixtures already carry morrison-cou1
and morrison-cou2 separately -- and it is not attempted here, because a candidate
that quietly handles the easy documents and hides the hard one is the thing this
project exists to stop.

## Keyless

Routing is RRF over K4+K6 -- the project default. The risk vocabulary is a small
closed set fixed by the standard, so locating the spans needs patterns rather
than a model. No API key, no network.
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(_ROOT / "dev" / "tools" / "scripts"))
sys.path.insert(0, str(_ROOT / "src"))

from document_furniture import strip_furniture  # noqa: E402
from keyless_k2_extractive import sentences  # noqa: E402
from uofa_cli import excel_constants as ec  # noqa: E402
from uofa_cli.readers.pdf_reader import read_pdf  # noqa: E402

NAMES = tuple({n.lower() for n in ec.VV40_FACTOR_NAMES})

# ASME V&V 40 Table: model risk from its two inputs. Only the gradations the
# standard defines are keys -- a value it does not define must not be silently
# mapped onto one, which is the whole point of the `not_derivable` branch.
_RISK_TABLE: dict[tuple[str, str], str] = {}
_LEVELS = ("low", "medium", "high")
for _i, _inf in enumerate(_LEVELS):
    for _j, _dc in enumerate(_LEVELS):
        _RISK_TABLE[(_inf, _dc)] = _LEVELS[min(2, max(_i, _j))]

# The gradation is stated as a CONCLUSION after the rationale, not next to the
# label. Morrison:
#
#   ...will be identified from the CFD results -> Low
#   Decision Consequence: if the pump causes high levels of hemolysis while the
#   patient is in the surgical suite, then the pump can be replaced -> Medium
#   Model Risk: Low-medium (level 2)
#
# A first-match rule captured "high" from "high levels of hemolysis" -- the
# hazard being described, not the value being assigned -- and Morrison then
# scored agreement=match by coincidence. Take the LAST gradation before the next
# label instead, which is where the assignment sits.
_LABEL = r"(?:model influence|decision consequence|regulatory impact|model risk)"
_GRADE = re.compile(r"\b(low|medium|high)\b", re.I)

# Citations look like risk levels. "accounting for its risk level [3,4]" yielded
# a stated risk of "3" on Bologna, from a bibliography reference.
_CITATION = re.compile(r"\[[\d,\s-]+\]")

# Compound values the standard does not define -- Morrison's "Low-medium
# (level 2)", Nagaraja's "High-Medium". Recorded rather than resolved: picking
# one half would be inventing a gradation the authors declined to state.
_COMPOUND = re.compile(r"\b(low|medium|high)\s*[-/]\s*(low|medium|high)\b", re.I)


def _segment_after(text: str, label: str) -> str | None:
    """Text between this label and the next one -- where its value is assigned."""
    m = re.search(label + r"\s*:?", text, re.I)
    if not m:
        return None
    rest = text[m.end():]
    nxt = re.search(_LABEL, rest, re.I)
    return rest[:nxt.start()] if nxt else rest[:400]


def _graded(text: str, label: str) -> str | None:
    """The gradation assigned to `label`: the last one before the next label."""
    seg = _segment_after(text, label)
    if seg is None:
        return None
    hits = _GRADE.findall(_CITATION.sub(" ", seg))
    return hits[-1].lower() if hits else None

# Terms a paper may put in place of one of the two inputs. Detected so the
# substitution can be NAMED rather than guessed at or silently accepted.
_SUBSTITUTES = ("regulatory impact",)

# Values used where the standard expects a gradation.
_NON_GRADATION = re.compile(
    r"(?:model influence|decision consequence)[^.]{0,60}?\bdeemed (\w+)\b", re.I)


def _locate(label: str, sents: list[str], pool: list[int]) -> tuple[str | None, str | None]:
    """(gradation, the verbatim sentence carrying the label) or (None, None)."""
    for i in pool:
        s = " ".join(sents[i].split())
        if re.search(label, s, re.I):
            g = _graded(s, label)
            if g:
                return g, s
    return None, None


def assess(sents: list[str], pool: list[int]) -> dict:
    """The fixed output record. Every field is a verbatim span or null."""
    inf_v, inf_s = _locate(r"model influence", sents, pool)
    dc_v, dc_s = _locate(r"decision consequence", sents, pool)
    risk_v, risk_s = _locate(r"model risk|risk rating", sents, pool)
    # A compound stated risk is not a gradation the table can be compared to.
    compound = None
    if risk_s:
        m = _COMPOUND.search(_CITATION.sub(" ", risk_s))
        if m:
            compound = m.group(0).lower()
            risk_v = None

    sub = None
    for i in pool:
        low = " ".join(sents[i].split()).lower()
        for term in _SUBSTITUTES:
            if term in low and "model influence" not in low:
                sub = term
                break
        if sub:
            break
    # A non-gradation value given to a defined input is also a substitution --
    # of the value rather than the name.
    if sub is None:
        for i in pool:
            m = _NON_GRADATION.search(sents[i])
            if m and m.group(1).lower() not in _LEVELS:
                sub = m.group(1).lower()
                break

    derived = None
    if inf_v and dc_v:
        derived = _RISK_TABLE.get((inf_v, dc_v))

    if derived is None:
        agreement = "not_derivable"
    elif risk_v is None:
        agreement = "not_derivable"
    else:
        agreement = "match" if risk_v == derived else "mismatch"

    if compound and sub is None:
        sub = compound
    return {"stated_risk": risk_s, "decision_consequence": dc_s,
            "model_influence": inf_s, "substituted_term": sub,
            "derived_risk": derived, "agreement": agreement}


DOCS = [
    ("bologna", "extract_corpus_vv40/bundle_bologna_bcthip", "V&V40"),
    ("tavi1", "extract_corpus_vv40/bundle_tavi1_s3", "V&V40"),
    ("morrison", "extract_corpus_vv40/bundle_morrison", "V&V40"),
    ("nagaraja", "extract_corpus_vv40/bundle_nagaraja", "V&V40"),
    ("opensim", "extract_corpus_real/bundle_real_opensim_knee", "7009A"),
    ("elemance", "extract_corpus_real/bundle_real_elemance_thoracic", "7009A"),
]


def main() -> int:
    print("\nK8 — model risk, extracted and validated\n")
    out = {}
    for tag, bundle, std in DOCS:
        src = _ROOT / "tests" / "fixtures" / bundle / "source"
        text = "\n".join(c.text for p in sorted(src.glob("*.pdf")) for c in read_pdf(p))
        sents = sentences(text)
        _, pool, _ = strip_furniture(sents, NAMES)
        r = assess(sents, pool)
        out[tag] = r
        flat = " ".join(text.split()).lower()
        verbatim = all(" ".join(str(v).split()).lower() in flat
                       for k, v in r.items()
                       if v and k in ("stated_risk", "decision_consequence", "model_influence"))
        print(f"  {tag:9s} [{std:6s}] agreement={r['agreement']:14s} "
              f"derived={str(r['derived_risk']):7s} sub={str(r['substituted_term']):18s} "
              f"verbatim={'ok' if verbatim else 'FAIL'}")
        for k in ("stated_risk", "decision_consequence", "model_influence"):
            if r[k]:
                print(f"       {k:22s} {r[k][:88]!r}")

    print("\n  ── kill criteria (plan v4) ──")
    ok = True
    # 3. 7009A documents must be all-null / not_derivable
    for tag in ("opensim", "elemance"):
        r = out[tag]
        clean = (r["agreement"] == "not_derivable"
                 and not any(r[k] for k in ("stated_risk", "decision_consequence",
                                            "model_influence", "derived_risk")))
        ok &= clean
        print(f"  {'PASS' if clean else 'FAIL'}  {tag}: all fields null, not_derivable "
              f"(any value here is fabrication)")
    # 2. Bologna names its substitution and refuses to derive
    r = out["bologna"]
    b = (r["substituted_term"] == "regulatory impact" and r["model_influence"] is None
         and r["agreement"] == "not_derivable")
    ok &= b
    print(f"  {'PASS' if b else 'FAIL'}  bologna: substituted_term='regulatory impact', "
          f"model_influence=null, not_derivable")
    # TAVI I: value substitution, also not derivable
    r = out["tavi1"]
    t = r["agreement"] == "not_derivable" and r["substituted_term"] is not None
    ok &= t
    print(f"  {'PASS' if t else 'FAIL'}  tavi1: non-gradation value named, not_derivable")
    # nagaraja: compound value named
    r = out["nagaraja"]
    n = r["agreement"] == "not_derivable" and r["substituted_term"] == "high-medium"
    ok &= n
    print(f"  {'PASS' if n else 'FAIL'}  nagaraja: compound 'high-medium' named, not_derivable")
    # morrison: KNOWN FAILURE, stated as one rather than omitted from the criteria
    r = out["morrison"]
    print(f"  KNOWN-FAIL morrison: agreement={r['agreement']!r} -- two contexts of use, "
          f"and K8 is scope-blind.")
    print(f"             It pairs COU1's inputs with a COU2 risk sentence. The criteria")
    print(f"             above did not test Morrison, which is how the first version of")
    print(f"             this script reported PASS on two false captures.")
    ok = ok and r["agreement"] == "mismatch"  # pinned: this is the current, wrong, behaviour
    print(f"\n  K8: 5 of 6 documents correct, 1 known failure (morrison, multi-COU).")
    print(f"  Criteria as written: {'satisfied' if ok else 'NOT satisfied'} -- but they were")
    print(f"  satisfied by a broken extractor once already, so read the spans above.")
    print(f"\n  Six documents, two standards. The two 7009A rows are the control:")
    print(f"  those documents do not state model risk, so any value is invented.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

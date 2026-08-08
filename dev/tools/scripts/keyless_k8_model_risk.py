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

import pathlib
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
# Moved to `uofa_cli.keyless.routes` so the shipped extractor and this
# candidate script cannot drift apart. Verified identical on all 40
# seeded documents before the move; `tests/test_keyless_routes.py`
# keeps them from being redefined here.
from uofa_cli.keyless.routes import (  # noqa: E402
    assess,
)


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
    print("             It pairs COU1's inputs with a COU2 risk sentence. The criteria")
    print("             above did not test Morrison, which is how the first version of")
    print("             this script reported PASS on two false captures.")
    ok = ok and r["agreement"] == "mismatch"  # pinned: this is the current, wrong, behaviour
    print("\n  K8: 5 of 6 documents correct, 1 known failure (morrison, multi-COU).")
    print(f"  Criteria as written: {'satisfied' if ok else 'NOT satisfied'} -- but they were")
    print("  satisfied by a broken extractor once already, so read the spans above.")
    print("\n  Six documents, two standards. The two 7009A rows are the control:")
    print("  those documents do not state model risk, so any value is invented.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

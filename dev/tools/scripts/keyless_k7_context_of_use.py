#!/usr/bin/env python3
"""K7: find the context of use, and refuse to invent one.

`hasContextOfUse` is one of the nine properties `ProfileComplete` requires. The
deliverable records it as **not evaluable** -- n=4 against a coin-flip control
demands 4/4 to say anything -- so this is written to be measured at the seeded
corpus's n, not to be believed at n=4.

## The property exists in only one of the two standards

ASME V&V 40 requires a context of use. NASA-STD-7009A has no such concept.
Measured across the five real papers: 0 and 1 mentions in the two 7009A
documents against 39, 33 and 50 in the three V&V 40 ones.

That asymmetry looked like the strongest test available -- K8 uses the same one
and it works there -- and **measuring it shows it does not transfer**.

K8's control holds because the risk VOCABULARY is absent from 7009A papers:
those documents never write "model influence" or "decision consequence", so an
extractor that finds one has invented it. K7 has no such luck. OpenSim, a 7009A
paper, states plainly:

    "The OPENSIM Full Body Model was used to assess a muscle strain injury
     occurring in the muscles of the pelvis, legs..."

That is a model-purpose statement in exactly the shape a context of use takes.
The two standards differ in whether they give that statement a formal ROLE, not
in whether the sentence exists. So requiring None on 7009A tests whether the
extractor was told the standard, which it is, and not whether it read anything.

**Recorded rather than engineered around:** the 7009A row is reported and is not
a discriminating control for this property. K8's analogous row is; the difference
is vocabulary, and assuming it generalised was wrong.

## Why the route is a shape, not the term

The sentences containing the phrase "context of use" are ABOUT the context of
use, not the statement of it. In Bologna all four say things like "starting from
BBCT proposed context of use the whole credibility plan is presented". The
statement itself -- the model provides an absolute risk of hip fracture employed
as a surrogate endpoint -- never uses the phrase.

This is R7 in the wild: the evidence sits away from the term that names it. So
the route matches the SHAPE of a context-of-use claim,

    the model + is used/employed/proposed + for a decision or a quantity

which is a pattern, not a semantic judgement, and needs no model.

## The real corpus cannot settle this, for a third reason

Bologna's context of use is stated in sentence 166, which the two-column reader
delivers as

    "Right: a graphical repre hip provides an absolute risk of hip fracture,
     which shall be employed as a surroga ost"

-- a figure caption interleaved with body text across the gutter. The one
sentence carrying the answer is the one the extraction pathology destroyed, so on
this document K7 is being scored against evidence that no longer exists in the
text it reads.

Of the five real papers: two are 7009A and carry no such property, one has gold
that is a paraphrase sitting in a damaged sentence, and two have no transcribed
context of use at all. **n=1, and that one is unreadable.** This is the row the
seeded corpus was built for.

## Scoring differs by corpus, deliberately

The real corpus's transcribed gold is a **paraphrase**: Bologna's is not verbatim
anywhere in the document, and the best-overlapping sentence carries 73% of its
content words while being damaged by two-column reading. An exact-match score
there would measure the transcriber's phrasing.

So real papers are scored on content-word overlap and seeded papers on the
verbatim span their gold records. The seeded corpus is the one that can carry a
strict score, which is a reason it exists.

## Keyless

Patterns and section structure only. No API key, no network.
"""
from __future__ import annotations

import argparse
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

# The subject: this paper's model, however it refers to it.
_MODEL = re.compile(
    r"\b(the\s+)?(computational\s+|in\s+silico\s+|finite\s+element\s+|CFD\s+|FE\s+)?"
    r"(model|simulation|framework|tool|analysis)\b", re.I)

# The claim: what it is used FOR.
_USED_FOR = re.compile(
    r"\b(is|was|are|were|shall be|will be|to be)\s+(used|employed|applied|"
    r"intended|proposed|deployed|leveraged)\b|"
    r"\b(supports?|informs?|replaces?|substitutes? for|stands? in for)\b", re.I)

# The object: a decision, an endpoint, a regulatory purpose.
_PURPOSE = re.compile(
    r"\b(decision|decide|assess\w*|evaluat\w*|predict\w*|estimat\w*|"
    r"surrogate|biomarker|endpoint|claim|submission|clearance|approval|"
    r"regulatory|labell?ing|in place of|instead of|rather than)\b", re.I)

# Sentences ABOUT the context of use rather than statements of it. Bologna's
# four mentions are all of this kind, and quoting one would score the term.
_ABOUT = re.compile(
    r"\b(context of use|COU)\b.{0,60}\b(is (presented|described|defined|given)|"
    r"section|table|figure|following|below|above|proposed context)\b|"
    r"^\s*(starting from|based on|according to)\b", re.I)


def find_context_of_use(sents: list[str], pool: list[int]) -> list[int]:
    """Sentence indices stating a context of use, best-first by parts matched."""
    scored: list[tuple[int, int]] = []
    for i in pool:
        s = " ".join(sents[i].split())
        if _ABOUT.search(s):
            continue
        parts = (bool(_MODEL.search(s)) + bool(_USED_FOR.search(s))
                 + bool(_PURPOSE.search(s)))
        if parts == 3:
            scored.append((parts, i))
    scored.sort(key=lambda t: (-t[0], t[1]))
    return [i for _, i in scored]


def control_names_the_term(sents: list[str], pool: list[int]) -> list[int]:
    """Null model: the first sentence containing "context of use".

    Not free -- it reads the document, and on a V&V 40 paper it will always find
    something, which is exactly why it is the control worth beating. It is also
    what a keyword extractor would do.
    """
    return [i for i in pool if re.search(r"context of use|\bCOU\b", sents[i], re.I)]


def _overlap(a: str, b: str) -> float:
    """Content-word overlap, for gold that is a paraphrase rather than a span."""
    w = lambda x: {t for t in re.findall(r"[a-z]{4,}", x.lower())}  # noqa: E731
    ga = w(a)
    return len(ga & w(b)) / len(ga) if ga else 0.0


REAL = [("bologna", "extract_corpus_vv40/bundle_bologna_bcthip", "V&V40"),
        ("nagaraja", "extract_corpus_vv40/bundle_nagaraja", "V&V40"),
        ("morrison", "extract_corpus_vv40/bundle_morrison", "V&V40"),
        ("opensim", "extract_corpus_real/bundle_real_opensim_knee", "7009A"),
        ("elemance", "extract_corpus_real/bundle_real_elemance_thoracic", "7009A")]
_HIT = 0.50   # content-word overlap counting as a hit against paraphrased gold


def _read(src: pathlib.Path) -> tuple[list[str], list[int]]:
    text = "\n".join(c.text for p in sorted(src.glob("*.pdf")) for c in read_pdf(p))
    sents = sentences(text)
    _, pool, _ = strip_furniture(sents, NAMES)
    return sents, pool


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--corpus", type=pathlib.Path, default=None,
                    help="seeded corpus root; omit to run the five real papers")
    ap.add_argument("--k", type=int, default=3)
    args = ap.parse_args()

    print("\nK7 — context of use, by shape\n")
    rows: list[tuple[str, str, bool | None, bool | None]] = []

    if args.corpus:
        bundles = [b for b in sorted(args.corpus.rglob("bundle_*"))
                   if (b / "ground_truth.json").exists()]
        for b in bundles:
            gt = json.loads((b / "ground_truth.json").read_text())
            sents, pool = _read(b / "source")
            got = find_context_of_use(sents, pool)[:args.k]
            gold = gt.get("expected_context_of_use")
            std = gt.get("standard")
            if std != "V&V40":
                # The control. Any value here is fabrication.
                rows.append((b.name[14:], std, not got, None))
            else:
                hit = any(_overlap(gold, sents[i]) >= _HIT for i in got) if gold else None
                base = control_names_the_term(sents, pool)[:args.k]
                bhit = any(_overlap(gold, sents[i]) >= _HIT for i in base) if gold else None
                rows.append((b.name[14:], std, hit, bhit))
    else:
        for tag, bundle, std in REAL:
            gt = json.loads((_ROOT / "tests" / "fixtures" / bundle
                             / "ground_truth.json").read_text())
            gold = (gt.get("_provenance") or {}).get("context_of_use")
            sents, pool = _read(_ROOT / "tests" / "fixtures" / bundle / "source")
            got = find_context_of_use(sents, pool)[:args.k]
            if std != "V&V40":
                rows.append((tag, std, not got, None))
            elif gold:
                hit = any(_overlap(gold, sents[i]) >= _HIT for i in got)
                base = control_names_the_term(sents, pool)[:args.k]
                rows.append((tag, std, hit, any(_overlap(gold, sents[i]) >= _HIT
                                                for i in base)))
            else:
                rows.append((tag, std, None, None))   # no gold to score against

    print(f"  {'document':22s}{'std':8s}{'K7':>8s}{'control':>10s}")
    for tag, std, hit, base in rows:
        f = lambda v: "-" if v is None else ("hit" if v else "miss")  # noqa: E731
        print(f"  {tag[:22]:22s}{std:8s}{f(hit):>8s}{f(base):>10s}")

    ctrl = [r for r in rows if r[1] != "V&V40"]
    vv = [r for r in rows if r[1] == "V&V40" and r[2] is not None]
    print(f"\n  ── the 7009A control: silence is the correct answer ──")
    clean = sum(1 for r in ctrl if r[2])
    print(f"  {clean}/{len(ctrl)} returned nothing, as the standard requires.")
    if len(ctrl) and clean < len(ctrl):
        print("  A value on a 7009A document is invented; this is the row that")
        print("  separates an extractor from a text generator.")
    if vv:
        k7 = sum(1 for r in vv if r[2])
        cb = sum(1 for r in vv if r[3])
        print(f"\n  ── V&V 40 retrieval, n={len(vv)} ──")
        print(f"  K7 {k7}/{len(vv)}   control (name the term) {cb}/{len(vv)}")
        if len(vv) < 8:
            print(f"\n  n={len(vv)} is too small to separate these. Recorded, not believed.")
    else:
        print("\n  No V&V 40 document carried gold to score against.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

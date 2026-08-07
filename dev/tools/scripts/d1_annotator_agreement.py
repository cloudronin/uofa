#!/usr/bin/env python3
"""D1: is the real-document annotation a measurement or one reader's opinion?

Everything now rests on 39 hand-annotated factor-document pairs across five real
documents, annotated once, by me. The only reliability figure this project has
is 89.3% inter-annotator agreement -- measured on the *synthetic* corpus, which
subsequently turned out to invert method rankings. Checking the reliability of
the data you are no longer using is not a check.

## Why a different model family and not a second pass

A second pass by the same annotator measures consistency, not reliability. The
established pattern here is `attribution_agreement.py`, which cross-checked
gpt-5's synthetic labels against claude-sonnet. The real-document annotations
are mine, so the independent annotator is **gpt-5**.

That is weaker than a human SME and is not claimed to be otherwise. What it can
establish is whether the spans are determined by the document or by the reader:
if two unrelated systems, given the same text and the same factor list, land on
the same sentences, the annotation is tracking something. If they do not, 39
pairs are 39 opinions and every number resting on them needs restating.

## The comparison is span-level, not string-level

Two annotators will phrase a span differently while pointing at the same
sentence. So the unit is: for factor F, which SENTENCE did each annotator's
spans land in? Comparing strings would measure paraphrase -- the mistake the
attribution metric itself made once and had to be corrected for.

Reported three ways, because they answer different questions:

    factor selection   did both annotators mark this factor at all
    STRICT             same sentence
    LOOSE              >=50% token overlap, the rule score_attribution uses

## Documents

Bologna and Nagaraja, which carry 21 of the 39 pairs (54%). They are also the
two whose annotation was hardest -- both state per-factor findings in tables
that reproduce the standard's own gradation text, which is exactly where a
reader is most likely to be substituting judgement for evidence.

## The annotators must be given the same scope

These papers assess several models across several injury mechanisms and score
every factor separately for each. A bundle is one (model x mechanism) pair. The
first version of this script gave gpt-5 the document and the factor list but not
the pair, and on elemance it duly quoted THUMS femur/tibia evidence for an
Elemance/thoracic bundle -- scoring 1/6 against an annotation that was correct.

That failure mode was already known: naming the model took the selection stage
from 3/6 to 5/6. Withholding it here manufactured disagreement and would have
been read as unreliable annotation.

## Result: 15% same-sentence, and the cause is not disagreement

    factor selection            20/26   76.9%
    STRICT same sentence         3/20   15.0%
    LOOSE  >=50% token overlap   8/20   40.0%

Against 89.3% on the synthetic corpus. But reading the disagreements shows the
15% is not two readers disputing what the evidence is. It is two readers
answering from **different parts of the document**:

    factor                 mine                          gpt-5
    Discretization error   "conservation equation         "negligibly small (< 0.5%)
                            balances are checked"          for N = 106"
    SQA                    "SQA procedures from the       "detailed audit reports from a
                            vendors are referenced"        third-party testing body, TUV"
    Test samples           "statistically relevant        "a dataset of 101 calibrated CT
                            number of samples used"        scans collected at Rizzoli"

Positionally, in a 989-sentence document:

    mine    12 spans, sentences 501-525, median gap 1   -- a contiguous block
    gpt-5   19 spans, sentences 221-579, median gap 5   -- dispersed

**Sentences 501-525 are Table 1.** I annotated the summary table; gpt-5
annotated the body prose that the table summarises. Both are defensible as
"evidence for this factor", and the document genuinely contains both. On
`Relevance of the validation activities` the two even say the same thing --
"there was partial overlap between the ranges of the validation points and the
CoU" (table) against "As a whole, partial overlap can be identified between the
ranges of the validation points" (prose).

So D1's finding is sharper than "the annotation is unreliable":

1. **The annotation has an undeclared systematic bias.** Choosing the table over
   the prose was a choice, made silently, and it is the choice that produced
   nearly every disagreement.
2. **gpt-5's spans are the better evidence.** They carry the figures -- 0.5%,
   N = 106, 101 CT scans, TUV -- where the table cells carry the standard's own
   summary vocabulary. A credibility artefact wants the former.
3. **Routing numbers measured against my gold answer a different question than
   intended.** They measure whether a router can find the summary table, not
   whether it can find the findings. Bologna scored 0/10 same-sentence, and
   Bologna is 11 of the 39 pairs.

The 15% figure should not be quoted as an agreement rate without this. It is
mostly one methodological choice, not twenty independent disagreements.
"""
from __future__ import annotations

import json
import os
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

# All five, not the original two. Clustering analysis showed opensim and
# elemance are as tightly clustered as Bologna was (2% of the document, median
# gap 2), and Bologna's cluster turned out to be a summary table. Their clusters
# look like findings sections instead, but that was assumed once already and was
# wrong, so it is checked.
DOCS = [("bologna", "extract_corpus_vv40/bundle_bologna_bcthip", "annot_bologna.json"),
        ("nagaraja", "extract_corpus_vv40/bundle_nagaraja", "annot_nagaraja.json"),
        ("morrison", "extract_corpus_vv40/bundle_morrison", "annot_morrison.json"),
        ("opensim", "extract_corpus_real/bundle_real_opensim_knee", "annot_opensim.json"),
        ("elemance", "extract_corpus_real/bundle_real_elemance_thoracic",
         "annot_elemance_thoracic.json")]
NAMES = tuple({n.lower() for n in ec.VV40_FACTOR_NAMES})

PROMPT = """\
You are annotating an engineering credibility-assessment document written under
ASME V&V 40.

{scope}
For each credibility factor listed below that the document ACTUALLY reports a
finding about, quote 1-3 short phrases that appear LITERALLY in the source and
that a reviewer would cite as the evidence for that factor. Copy unbroken spans
exactly as written -- no ellipses, no stitching distant phrases together.

Two things to avoid, both of which are present in this document:

* These papers reproduce the V&V 40 gradation table, which DEFINES each factor's
  levels ("a. A single sample was used. b. Multiple samples were used..."). Those
  are definitions from the standard, not findings about this model. Do not quote
  them.
* Section headings and table row labels name a factor without assessing it. Do
  not quote them either.

A finding says what THIS study did, found, or scored, and why. Omit any factor
the document does not report a finding about. Do not invent phrases.

Where the paper assesses SEVERAL models or several injury mechanisms, quote only
evidence for the one named above. A sentence scoring a different model or a
different mechanism is the wrong answer however well it matches the factor.

Return JSON only, no prose, no fences:
{{"factors": [{{"factor_type": "<exact name from the list>",
               "evidence": ["<span>", "<span>"]}}]}}

## Canonical factors
{factor_list}

## Source document
{source}
"""


def norm(s: str) -> str:
    return " ".join(str(s).split()).lower()


def spans_for(spans, sents) -> set[int]:
    """Which sentence indices do these spans land in?"""
    low = [norm(s) for s in sents]
    hits = set()
    for sp in spans:
        k = norm(sp)
        if len(k) < 8:
            continue
        for i, s in enumerate(low):
            if k in s:
                hits.add(i)
                break
    return hits


def toks(s: str) -> set[str]:
    return set(re.findall(r"[a-z0-9.%-]{3,}", norm(s)))


def main() -> int:
    from uofa_cli.llm.backend import GenerationOptions
    from uofa_cli.llm.litellm_backend import LiteLLMBackend

    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise SystemExit("OPENAI_API_KEY not set")
    backend = LiteLLMBackend(backend_name="openai", model_name="gpt-5",
                             api_key=key, default_timeout_seconds=300)

    failed: list[str] = []
    tot_f = both_f = mine_only = theirs_only = 0
    tot_s = agree_s = 0
    tot_l = agree_l = 0
    per_doc = {}

    for tag, bundle, annot in DOCS:
        src = _ROOT / "tests" / "fixtures" / bundle / "source"
        text = "\n".join(c.text for p in sorted(src.glob("*.pdf")) for c in read_pdf(p))
        sents = sentences(text)
        kept, pool, _ = strip_furniture(sents, NAMES)

        mine = {a["factor_type"]: a["evidence"]
                for a in json.loads((_ROOT / "docs" / "v1" / annot).read_text())["annotations"]}

        # No temperature: gpt-5 rejects a non-default value and the backend
        # already strips it. Budget is generous because reasoning tokens are
        # drawn from the same allowance as the answer, so a budget that is fine
        # for a short prompt returns empty on a long one.
        body = "\n".join(kept)[:80000]
        # Offer each annotator the vocabulary its own document uses: the 7009A
        # papers are annotated with published decomposed_7009a names, the V&V 40
        # papers with pack names. Offering the wrong list guarantees disagreement
        # on factor selection for reasons that have nothing to do with reading.
        prov = json.loads((_ROOT / "tests" / "fixtures" / bundle
                           / "ground_truth.json").read_text()).get("_provenance", {})
        bits = [f"{k.replace('_', ' ')}: {prov[k]}"
                for k in ("model", "injury_mechanism", "scenario") if prov.get(k)]
        scope = ("This assessment is specifically of -- " + "; ".join(bits) + ".\n"
                 if bits else "")
        mine_names = sorted(mine)
        vocab = mine_names if tag in ("opensim", "elemance") else list(ec.VV40_FACTOR_NAMES)
        raw = backend.generate(
            PROMPT.format(factor_list="\n".join(f"- {f}" for f in vocab),
                          source=body, scope=scope),
            GenerationOptions(max_tokens=16000))
        m = re.search(r"\{.*\}", raw or "", re.S)
        if not m:
            # Never silently continue: an unparsed response must not read as
            # disagreement. That is exactly how a failed API call becomes a
            # finding about the data.
            print(f"  {tag}: NO JSON. prompt {len(body):,} chars, "
                  f"response {len(raw or '')} chars: {(raw or '')[:200]!r}")
            failed.append(tag)
            continue
        try:
            theirs = {f["factor_type"]: f.get("evidence") or []
                      for f in json.loads(m.group(0)).get("factors", [])
                      if f.get("evidence")}
        except json.JSONDecodeError:
            print(f"  {tag}: unparseable response")
            continue

        d_both = d_s = d_sn = 0
        for f in set(mine) | set(theirs):
            tot_f += 1
            in_m, in_t = f in mine, f in theirs
            if in_m and in_t:
                both_f += 1
                d_both += 1
                ms, ts = spans_for(mine[f], sents), spans_for(theirs[f], sents)
                if ms and ts:
                    tot_s += 1
                    d_sn += 1
                    if ms & ts:
                        agree_s += 1
                        d_s += 1
                tot_l += 1
                tt = set().union(*(toks(x) for x in theirs[f])) if theirs[f] else set()
                if any(t and len(t & tt) / len(t) >= 0.5
                       for t in (toks(x) for x in mine[f])):
                    agree_l += 1
            elif in_m:
                mine_only += 1
            else:
                theirs_only += 1
        per_doc[tag] = (d_both, d_s, d_sn)
        print(f"  {tag}: mine {len(mine)} factors, gpt-5 {len(theirs)}, both {d_both}"
              f"  (same sentence {d_s}/{d_sn})")

    if failed or tot_s == 0:
        print(f"\n  ── D1 DID NOT RUN ──")
        print(f"  documents with no usable response: {failed or 'none'}; "
              f"comparable factors: {tot_s}")
        print(f"  No verdict is printed. An API failure is not evidence about")
        print(f"  the annotation, and an earlier version of this script reported")
        print(f"  '< 0.60: largely one reader's judgement' from zero data.")
        return 1

    print(f"\n  ── D1: annotator agreement on real documents ──")
    print(f"  factor selection: both marked {both_f}/{tot_f} ({both_f/max(tot_f,1):.1%})")
    print(f"    mine only {mine_only}      gpt-5 only {theirs_only}")
    print(f"  where both marked the factor:")
    print(f"    STRICT same sentence       {agree_s}/{tot_s} ({agree_s/max(tot_s,1):.1%})")
    print(f"    LOOSE  >=50% token overlap {agree_l}/{tot_l} ({agree_l/max(tot_l,1):.1%})")
    r = agree_s / max(tot_s, 1)
    print()
    if r >= 0.80:
        print(f"  >= 0.80: the spans are determined by the document. 39 pairs are")
        print(f"  measurements, and the routing numbers stand as reported.")
    elif r >= 0.60:
        print(f"  0.60-0.80: substantial but not decisive. Usable with the caveat")
        print(f"  stated on every figure that rests on the annotation.")
    else:
        print(f"  < 0.60: the spans are largely one reader's judgement. Every")
        print(f"  routing number resting on them measures agreement with me, not")
        print(f"  routing, and must be restated.")
    print(f"\n  gpt-5 is not a human SME. This bounds reader-dependence; it does")
    print(f"  not establish correctness.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

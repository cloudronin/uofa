#!/usr/bin/env python3
"""Do two model families agree on which sentence evidences which factor?

Attribution is scored against `evidence_keywords`, which gpt-5 wrote. That makes
it a measurement of agreement with one annotator, and the size of that caveat
depends entirely on whether a different family would have marked the same spans.

    high agreement   the labels track something in the document, and
                     attribution measures attribution
    low agreement    the labels are one model's taste, and every number
                     built on them inherits it

This is the cheap decisive experiment: re-annotate a sample with Claude from the
same sources, and compare.

## What is and is not at risk

Sonnet's extraction already scores 0.946 against gpt-5's labels, and that is
**cross-family** -- an Anthropic model matching an OpenAI model's view of which
evidence belongs where. So the labels are not obviously idiosyncratic.

K6 is the number genuinely at risk: it is *trained* on gpt-5's labels and
*tested* against gpt-5's labels, so part of its 0.615 could be learning this
annotator's habits rather than the task. If agreement is low, K6's figure needs
restating.

## The comparison is span-level, not keyword-level

Two annotators will phrase a keyword differently while pointing at the same
sentence. So the unit is: for factor F, which SENTENCE did each annotator's
keywords land in? Agreement means both landed in the same sentence. Comparing
keyword strings would measure paraphrase, which is the mistake the attribution
metric itself already made once and had to be corrected for.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(_ROOT / "dev" / "tools" / "scripts"))
sys.path.insert(0, str(_ROOT / "src"))

from keyless_k2_extractive import sentences  # noqa: E402

PROMPT = """\
You are annotating an engineering credibility-assessment document.

For each credibility factor listed below that the document ACTUALLY discusses,
quote 2-4 short phrases that appear LITERALLY in the source and that a reviewer
would use to locate the evidence for that factor. Copy unbroken spans exactly as
written -- no ellipses, no stitching two distant phrases together.

Omit any factor the document does not substantively address. Do not invent
phrases.

Return JSON only, no prose, no fences:
{{"factors": [{{"factor_type": "<exact name from the list>",
               "evidence_keywords": ["<span>", "<span>"]}}]}}

## Canonical factors
{factor_list}

## Source documents
{source}
"""


def spans_for(keywords: list[str], sents: list[str]) -> set[int]:
    """Which sentence indices do this factor's keywords land in?"""
    norm = [" ".join(s.split()).lower() for s in sents]
    hits = set()
    for kw in keywords:
        k = " ".join(str(kw).split()).lower()
        if len(k) < 4:
            continue
        for i, s in enumerate(norm):
            if k in s:
                hits.add(i)
                break
    return hits


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--corpus", type=Path,
                    default=_ROOT / "tests" / "fixtures" / "extract_corpus_v2" / "dev")
    ap.add_argument("--n", type=int, default=10)
    ap.add_argument("--model", default="claude-sonnet-4-6")
    args = ap.parse_args()

    from uofa_cli.llm.backend import GenerationOptions
    from uofa_cli.llm.litellm_backend import LiteLLMBackend

    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise SystemExit("ANTHROPIC_API_KEY not set")
    backend = LiteLLMBackend(backend_name="anthropic", model_name=args.model,
                             api_key=key, default_timeout_seconds=180)

    bundles = [b for b in sorted(args.corpus.glob("bundle_*"))
               if (b / "ground_truth.json").exists() and (b / "source").is_dir()][:args.n]

    tot_f = agree_f = 0          # factors both annotators marked
    tot_s = agree_s = 0          # sentence-level overlap (STRICT)
    tot_l = agree_l = 0          # token-overlap (LOOSE, the attribution rule)
    only_gpt = only_claude = 0

    for b in bundles:
        gt = json.loads((b / "ground_truth.json").read_text())
        src = "\n".join(p.read_text(errors="ignore")
                        for p in sorted((b / "source").glob("*")))
        sents = sentences(src)
        factors = [f["factor_type"] for f in gt["expected_factors"]]

        raw = backend.generate(
            PROMPT.format(factor_list="\n".join(f"- {f}" for f in factors),
                          source=src[:60000]),
            GenerationOptions(temperature=0.0, max_tokens=4000))
        m = re.search(r"\{.*\}", raw, re.S)
        if not m:
            print(f"  {b.name}: no JSON returned, skipping")
            continue
        try:
            claude = {f["factor_type"]: f.get("evidence_keywords") or []
                      for f in json.loads(m.group(0)).get("factors", [])}
        except json.JSONDecodeError:
            print(f"  {b.name}: unparseable, skipping")
            continue

        gpt = {f["factor_type"]: (f.get("evidence_keywords") or [])
               for f in gt["expected_factors"]
               if f.get("expected_status") == "assessed" and f.get("evidence_keywords")}

        for f in set(gpt) | set(claude):
            in_g, in_c = f in gpt, f in claude and claude[f]
            if in_g and in_c:
                tot_f += 1
                agree_f += 1
                gs, cs = spans_for(gpt[f], sents), spans_for(claude[f], sents)
                if gs and cs:
                    tot_s += 1
                    if gs & cs:
                        agree_s += 1
                # Same pair, scored by the rule the attribution metric uses,
                # so the two numbers sit on one scale and can be compared.
                tot_l += 1
                ctok = set()
                for k in claude[f]:
                    ctok |= set(re.findall(r"[a-z0-9.%-]{3,}", str(k).lower()))
                for k in gpt[f]:
                    ktok = set(re.findall(r"[a-z0-9.%-]{3,}", str(k).lower()))
                    if ktok and len(ktok & ctok) / len(ktok) >= 0.5:
                        agree_l += 1
                        break
            elif in_g:
                only_gpt += 1; tot_f += 1
            elif in_c:
                only_claude += 1; tot_f += 1
        print(f"  {b.name}: gpt {len(gpt)} factors, claude {len(claude)}")

    print(f"\n  ── inter-annotator agreement, {len(bundles)} bundles ──")
    print(f"  factor selection: both marked {agree_f}/{tot_f} ({agree_f/max(tot_f,1):.1%})")
    print(f"    gpt-5 only  {only_gpt}      claude only {only_claude}")
    print(f"  where both marked the factor:")
    print(f"    STRICT same sentence      {agree_s}/{tot_s} ({agree_s/max(tot_s,1):.1%})")
    print(f"    LOOSE  >=50% token overlap {agree_l}/{tot_l} ({agree_l/max(tot_l,1):.1%})")
    print(f"    (LOOSE is the rule score_attribution uses, so it is the one")
    print(f"     comparable with sonnet's 0.946)")
    print()
    r = agree_s / max(tot_s, 1)
    if r >= 0.80:
        print(f"  >= 0.80: the labels track the document, not the annotator.")
        print(f"  Attribution measures attribution; K6's 0.615 stands as reported.")
    elif r >= 0.60:
        print(f"  0.60-0.80: substantial but not decisive. Attribution is usable")
        print(f"  with the caveat stated, and K6's figure carries that caveat too.")
    else:
        print(f"  < 0.60: the labels are largely one model's taste. Every number")
        print(f"  built on them -- including K6's 0.615 -- measures agreement with")
        print(f"  gpt-5 rather than extraction, and must be restated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

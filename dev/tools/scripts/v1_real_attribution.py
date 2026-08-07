#!/usr/bin/env python3
"""V1's actual number: keyless attribution on a real document, after the fix.

The kill criterion in plan v3 was "annotate 3 real bundles; if pipeline
attribution is < 0.30, stop the keyless line". That number was never produced,
because until the two-column PDF fix the sentences it needed did not survive
extraction (1/13 spans contiguous). This produces it.

Scored against a hand annotation written before any extractor ran, on the one
real document that is both extractable prose and carries a per-factor
assessment. One document, one annotator: falsifying, not confirming.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(_ROOT / "dev" / "tools" / "scripts"))
sys.path.insert(0, str(_ROOT / "src"))

from keyless_k2_extractive import sentences  # noqa: E402
from uofa_cli.readers.pdf_reader import read_pdf  # noqa: E402

ann = json.loads((_ROOT / "docs" / "v1" / "annot_opensim.json").read_text())
src = _ROOT / "tests/fixtures/extract_corpus_real/bundle_real_opensim_knee/source"
text = "\n".join(c.text for p in sorted(src.glob("*.pdf")) for c in read_pdf(p))
sents = sentences(text)


def norm(s: str) -> str:
    return " ".join(str(s).split()).lower()


# Which sentence(s) does each annotated span overlap? Matching a span *inside*
# one sentence fails: the annotations are what a reviewer would cite, and those
# run across the segmenter's boundaries. Map by character offset instead, and
# accept every sentence the span touches.
flat = norm(text)
offs, cur = [], 0
for s_ in sents:
    n_ = norm(s_)
    i_ = flat.find(n_, cur)
    if i_ < 0:
        i_ = cur
    offs.append((i_, i_ + len(n_)))
    cur = i_ + len(n_)

gold: dict[str, set[int]] = {}
for a in ann["annotations"]:
    hits = set()
    for e in a["evidence"]:
        n = norm(e)
        start = flat.find(n)
        if start < 0:
            continue
        end = start + len(n)
        for i, (lo, hi) in enumerate(offs):
            if lo < end and start < hi:
                hits.add(i)
    if hits:
        gold[a["factor_type"]] = hits

print(f"document sentences: {len(sents)}")
print(f"factors with a locatable annotated span: {len(gold)}/{len(ann['annotations'])}\n")

FACTORS = [a["factor_type"] for a in ann["annotations"]]

# --- the null model: walk the document in order, one span per factor ---
const = {f: {i} for i, f in enumerate(FACTORS)}

# --- keyword routing: the honest keyless detector available without training ---
# K6 is trained on the synthetic corpus and has never seen a real document; the
# lexical router is what a keyless pipeline can do with no corpus at all.
def route_lexical(factor: str) -> set[int]:
    import re
    key = [w for w in re.findall(r"[a-z]{4,}", factor.lower())
           if w not in {"the", "and", "for", "of", "to", "with"}]
    best, score = None, 0
    for i, s in enumerate(sents):
        low = norm(s)
        n = sum(w in low for w in key)
        if n > score:
            best, score = i, n
    return {best} if best is not None else set()


lex = {f: route_lexical(f) for f in FACTORS}

for label, pred in (("control: document order", const),
                    ("keyless lexical routing", lex)):
    right = scored = 0
    for f, want in gold.items():
        got = pred.get(f) or set()
        if not got:
            continue
        scored += 1
        right += bool(got & want)
    acc = right / scored if scored else 0.0
    print(f"  {label:26s} attribution {acc:.3f}  ({right}/{scored})")

print("\n  Kill criterion (plan v3): < 0.30 stops the keyless line.")
print("  One document, one annotator -- falsifying, not confirming.")

#!/usr/bin/env python3
"""K10: given a shortlist, pick the sentence that is the evidence.

Routing is not going away. Every keyless route this project has that works --
K7, K8, and the RRF fusion behind `hasCredibilityFactor` -- narrows a document
before anything reads it. So the honest unit of remaining work is not "extract
from a document" but **"choose from k candidates"**, and that stage has never
been measured keyless.

## Why this is the stage worth attacking, and why accuracy is not the point

The router is the bottleneck: RRF recall@5 is 0.180 on seeded-train and 0.357 on
the real papers, so most findings never reach a selector at all. Improving
selection cannot recover them.

What selection CAN do is remove the model. The deliverable measures a MODEL
selector at **1.000** given a shortlist containing the answer, and that model
call is the last thing standing between `hasCredibilityFactor` and a keyless
pipeline. K10 does not need to beat 1.000; it needs to come close enough that the
pipeline runs unaided.

## Scored conditionally, so the router's failures do not contaminate it

Precision@1 **given the answer is in the shortlist**. A selector cannot be blamed
for evidence the router never surfaced, and mixing the two is how a composed
number stops telling you which stage to fix -- which happened here already: an
earlier script reported router recall as though it were a composed pipeline.

## The null is what makes this worth running

`control_rank_1` takes the router's top hit. The deliverable measures that at
**0.000 end to end**, so any real selection signal shows immediately. If nothing
keyless beats rank-1, that is a clean negative and the question of a fully
keyless pipeline is closed rather than open.

## The four signals, and why each is not the factor's name

R7 built the corpus so evidence is phrased WITHOUT the standard's vocabulary --
that is the whole reason a labelled-evidence corpus measures nothing. So a
selector keying on the factor name is measuring the corpus's failure to hide it.
These key on what a finding looks like instead:

* **a figure** -- findings report values; topic sentences do not
* **a comparison** -- "compared to", "within", "against"
* **past-tense reporting** -- what this study DID, not what one should do
* **not a rubric rung** -- the standard's own level definitions look like
  findings and outrank them, which is the fifth extraction pathology
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
from keyless_k6_classifier import label_sentences, load_split  # noqa: E402
from uofa_cli import excel_constants as ec  # noqa: E402
from uofa_cli.readers.pdf_reader import read_pdf  # noqa: E402
from v1_router_comparison import factor_queries  # noqa: E402

NAMES = tuple({n.lower() for n in ec.VV40_FACTOR_NAMES})
ENCODER = "all-MiniLM-L6-v2"
RRF_K = 60

_FIGURE = re.compile(r"\d+(?:\.\d+)?\s*(?:%|mm|MPa|N\b|kPa|Hz|s\b|degrees?|"
                     r"percent|micro\w*)|\b\d+(?:\.\d+)?\b")
_COMPARISON = re.compile(
    r"\b(compared|comparison|versus|against|relative to|within|exceed\w*|"
    r"agree\w*|differ\w*|deviat\w*|match\w*|correlat\w*)\b", re.I)
_REPORTED = re.compile(
    r"\b(was|were|had|showed|demonstrated|achieved|yielded|produced|"
    r"remained|reached|measured|observed|performed|confirmed)\b", re.I)
# The standard's own gradation rungs. They read like findings and are not.
_RUBRIC = re.compile(
    r"^\s*(a|b|c|d|e)[.)]|^\s*(no|a single|multiple|comprehensive)\b.{0,50}"
    r"\b(was|were)\b|^\s*in addition to\b", re.I)


def score_sentence(s: str) -> float:
    """How much this reads like a reported finding. Deliberately not the name."""
    t = " ".join(s.split())
    if _RUBRIC.search(t):
        return -1.0
    return (2.0 * bool(_FIGURE.search(t))
            + 1.5 * bool(_COMPARISON.search(t))
            + 1.0 * bool(_REPORTED.search(t))
            - 0.5 * (len(t) < 60))          # a fragment is rarely the evidence


def select(shortlist: list[str]) -> int:
    """Index of the sentence K10 picks. Ties break toward the router's order."""
    best, best_i = None, 0
    for i, s in enumerate(shortlist):
        sc = score_sentence(s)
        if best is None or sc > best:
            best, best_i = sc, i
    return best_i


def control_rank_1(_shortlist: list[str]) -> int:
    """Null: trust the router's top hit. The deliverable measures this at 0.000."""
    return 0


def main() -> int:
    from sentence_transformers import SentenceTransformer
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_union

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--corpus", type=pathlib.Path, required=True)
    ap.add_argument("--k", type=int, default=5)
    args = ap.parse_args()

    bundles = [b for b in sorted(args.corpus.rglob("bundle_*"))
               if (b / "ground_truth.json").exists()]
    train = load_split(_ROOT / "tests" / "fixtures" / "extract_corpus_v2" / "dev")
    X, y = [], []
    for b in train:
        for s, lab in label_sentences(b):
            X.append(s)
            y.append(lab)
    feats = make_union(
        TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True,
                        strip_accents="unicode"),
        TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=3,
                        sublinear_tf=True))
    clf = LogisticRegression(max_iter=2000, class_weight="balanced", C=4.0)
    clf.fit(feats.fit_transform(X), y)
    cls = {c: i for i, c in enumerate(clf.classes_)}
    enc = SentenceTransformer(ENCODER)
    queries = factor_queries()

    n_short = k10 = ctrl = 0
    routed_total = 0
    print(f"\nK10 — selection from a shortlist of {args.k}\n")
    for b in bundles:
        gt = json.loads((b / "ground_truth.json").read_text())
        sents = sentences("\n".join(c.text for c in read_pdf(b / "source" / "paper.pdf")))
        _, pool, _ = strip_furniture(sents, NAMES)
        if not pool:
            continue
        texts = [sents[i] for i in pool]
        P = clf.predict_proba(feats.transform(texts))
        cvec = enc.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        low = [" ".join(t.split()).lower() for t in texts]

        gold: dict[tuple, list[str]] = {}
        for f in gt.get("findings", []):
            if f.get("status") == "ambiguous":
                continue
            gold.setdefault((f["factor"], f.get("model", ""), f.get("mechanism", "")),
                            []).extend(f.get("spans") or [f["span"]])

        for (factor, _m, _x), spans in gold.items():
            col, q = cls.get(factor), queries.get(factor)
            if col is None and q is None:
                continue
            routed_total += 1
            r6 = (sorted(range(len(pool)), key=lambda k: -P[k][col])
                  if col is not None else list(range(len(pool))))
            if q is not None:
                qv = enc.encode([q], normalize_embeddings=True, show_progress_bar=False)
                sims = (qv @ cvec.T).max(axis=0)
                r4 = sorted(range(len(pool)), key=lambda k: -sims[k])
            else:
                r4 = list(range(len(pool)))
            p6 = {s: i for i, s in enumerate(r6)}
            p4 = {s: i for i, s in enumerate(r4)}
            order = sorted(range(len(pool)),
                           key=lambda s: -(1.0 / (RRF_K + p6.get(s, len(pool)))
                                           + 1.0 / (RRF_K + p4.get(s, len(pool)))))
            shortlist = order[:args.k]
            gl = [" ".join(s.split()).lower() for s in spans
                  if len(" ".join(s.split())) > 12]
            correct = {j for j, idx in enumerate(shortlist)
                       if any(g in low[idx] for g in gl)}
            if not correct:
                continue                      # the router missed; not K10's to answer
            n_short += 1
            k10 += select([texts[i] for i in shortlist]) in correct
            ctrl += control_rank_1([texts[i] for i in shortlist]) in correct

    print(f"  {'(factor x scope) pairs routed':38s}{routed_total:>8d}")
    print(f"  {'...where the answer reached the shortlist':38s}{n_short:>8d}"
          f"   ({n_short/max(routed_total,1):.3f} — the router's ceiling)\n")
    print(f"  {'selector':38s}{'precision@1':>12s}")
    print(f"  {'K10 — finding-shaped':38s}{k10/max(n_short,1):>12.3f}   {k10}/{n_short}")
    print(f"  {'control — take rank 1':38s}{ctrl/max(n_short,1):>12.3f}   {ctrl}/{n_short}")
    print(f"  {'a MODEL selector (deliverable, k=5)':38s}{1.000:>12.3f}")

    from math import comb
    c = ctrl / max(n_short, 1)
    if n_short and 0 < c < 1:
        pv = sum(comb(n_short, i) * c**i * (1 - c)**(n_short - i)
                 for i in range(k10, n_short + 1))
    else:
        pv = float("nan")
    print(f"\n  P(K10 >= {k10}/{n_short} | rank-1's rate) = {pv:.4f}")
    beats = k10 > ctrl and pv < 0.05
    print("  KILL CRITERION: beat rank-1 on precision@1")
    print(f"  -> {'PASSES' if beats else 'FAILS'}")
    print("\n  Conditional on the router succeeding, so this is selection alone.")
    print(f"  End-to-end keyless would be {n_short/max(routed_total,1):.3f} x "
          f"{k10/max(n_short,1):.3f} = "
          f"{n_short/max(routed_total,1) * k10/max(n_short,1):.3f}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

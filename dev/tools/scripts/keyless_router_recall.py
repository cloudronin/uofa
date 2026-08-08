#!/usr/bin/env python3
"""Router recall at k, against position. NOT a composed pipeline.

Every figure this project reports for a keyless stage was measured on that stage
ALONE. Routing recall@5 = 0.357 was the router by itself; K2's groundedness of
1.000 is true by construction, because it quotes. Neither says what the pair
does, and a router at 0.357 feeding an extractor at X does not give 0.357X --
errors correlate, and the sign of the correlation is not predictable from the
parts.

**What this measures, precisely.** Whether any of the k routed sentences CONTAINS
one of the finding's reference spans. That is router recall@k. It does NOT select
a span, and no extractor runs: an earlier version of this docstring claimed
"RRF@5 -> K2 end to end" while `quote_for` was never called, and the number was
reported as a composed pipeline result. It is not. Selection is measured by K10.

## What is being compared

    RRF@5   -> K2      against      control_constant_list -> K2

Same extractor on both sides. The only thing that varies is whether a routing
signal exists. That framing is the whole point of the exercise, because
`control_constant_list` scores 1.000 on DETECTION -- it announces every factor,
having read nothing -- and yet carries no routing signal at all, so the extractor
downstream of it must fall back on position.

If routing is worth anything, this is where it shows.

## No leakage

K6 trains on `extract_corpus_v2/dev`, the OLD synthetic corpus, and is measured
on the seeded corpus it has never seen. Training it on seeded-train and testing
on seeded-holdout would be defensible too, but the plan defers retraining -- the
seeded papers are paraphrases of three of the five real documents, and the only
clean read on a retrained K6 is elemance and morrison at n=2.

## Scoring

A factor is HIT when any of the k routed sentences contains any of that
finding's reference spans. Gold is multi-reference: a paper often states a
finding twice, and a router that finds either has found it.

Scored per (factor x model x mechanism), which is the unit of assessment this
project settled on after the same scope defect appeared five times.
"""
from __future__ import annotations

import argparse
import json
import pathlib
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


def _norm(s: str) -> str:
    return " ".join(str(s).split()).lower()


def control_constant_list(pool: list[int], k: int) -> list[int]:
    """The null: announce every factor, and route to the first k sentences.

    This is `control_constant_list` made to do the extractor's job. It scores
    1.000 on detection and cannot rank, so the only thing it can hand an
    extractor is position -- which is exactly the argument that detection is not
    a metric. Not free: reading the first k sentences of a credibility paper is
    a real strategy, since papers front-load their summary.
    """
    return pool[:k]


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
    if not bundles:
        raise SystemExit(f"no bundles under {args.corpus}")

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

    print(f"\nKeyless hybrid, end to end — RRF@{args.k} -> K2\n")
    print(f"  {len(bundles)} papers; K6 trained on {len(train)} OLD-synthetic "
          f"bundles, never on these\n")

    hit = ctrl = tot = 0
    no_query = 0
    per_doc = []
    for b in bundles:
        gt = json.loads((b / "ground_truth.json").read_text())
        sents = sentences("\n".join(c.text for c in read_pdf(b / "source" / "paper.pdf")))
        _, pool, _ = strip_furniture(sents, NAMES)
        if not pool:
            continue
        texts = [sents[i] for i in pool]
        P = clf.predict_proba(feats.transform(texts))
        cvec = enc.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        low = [_norm(t) for t in texts]

        # gold, keyed by the unit of assessment
        gold: dict[tuple[str, str, str], list[str]] = {}
        for f in gt.get("findings", []):
            if f.get("status") == "ambiguous":
                continue
            key = (f["factor"], f.get("model", ""), f.get("mechanism", ""))
            gold.setdefault(key, []).extend(f.get("spans") or [f["span"]])

        d_hit = d_tot = 0
        for (factor, _m, _mech), spans in gold.items():
            col = cls.get(factor)
            q = queries.get(factor)
            if col is None and q is None:
                no_query += 1
                continue
            tot += 1
            d_tot += 1
            # K6 order
            r6 = (sorted(range(len(pool)), key=lambda k: -P[k][col])
                  if col is not None else list(range(len(pool))))
            # K4 order
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
            routed = order[:args.k]
            base = list(range(min(args.k, len(pool))))     # the constant's fallback
            gl = [_norm(s) for s in spans if len(_norm(s)) > 12]
            if not gl:
                tot -= 1
                d_tot -= 1
                continue
            hit += any(g in low[i] for i in routed for g in gl)
            d_hit += any(g in low[i] for i in routed for g in gl)
            ctrl += any(g in low[i] for i in base for g in gl)
        per_doc.append((b.name[14:], d_hit, d_tot))

    print(f"  {'document':22s}{'hit':>6s}{'of':>6s}")
    for name, h, n in per_doc:
        print(f"  {name[:22]:22s}{h:>6d}{n:>6d}")

    r, c = hit / max(tot, 1), ctrl / max(tot, 1)
    print(f"\n  {'':22s}{'RRF recall@%d' % args.k:>16s}{'first-%d sentences' % args.k:>18s}")
    print(f"  {'recall':22s}{r:>16.3f}{c:>18.3f}")
    print(f"  {'':22s}{hit}/{tot:<15d}{ctrl}/{tot}")
    if no_query:
        print(f"\n  {no_query} (factor x scope) pairs had no K6 class and no K4 query")
        print("  -- factors outside the router's vocabulary, skipped and counted.")

    # A control that scores exactly 0 makes the binomial nan, and `nan < 0.05`
    # is False -- so the first version printed "not demonstrated" for 216 hits
    # against 0, the most decisive result the comparison can produce. Handled
    # explicitly rather than left to a float comparison that fails silently in
    # the direction of understating the finding.
    from math import comb
    if hit == 0:
        pv, verdict = 1.0, "is not demonstrated"
    elif c <= 0:
        pv, verdict = 0.0, "HELPS (the control found nothing at all)"
    elif c >= 1:
        pv, verdict = 1.0, "cannot be separated -- the control is perfect"
    else:
        pv = sum(comb(tot, i) * c**i * (1 - c)**(tot - i) for i in range(hit, tot + 1))
        verdict = "HELPS" if pv < 0.05 else "is not demonstrated"
    print(f"\n  P(RRF >= {hit}/{tot} | the constant's rate) = {pv:.4f}")
    print(f"  VERDICT: routing {verdict} at k={args.k}")
    print("\n  Both sides are scored the same way. The only difference is whether a")
    print("  routing signal exists, which is what detection F1 cannot measure.")
    print("  Neither side SELECTS a span -- that is K10.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

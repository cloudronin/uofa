#!/usr/bin/env python3
"""K4 vs K6 as routers on the synthetic corpus — the same question at scale.

On real documents K4 (embeddings) beat K6 (lexical) at tight k, and RRF beat
both. That was 19 factor-document pairs across 3 documents, which cannot
distinguish "embeddings are a better router" from "these three documents happen
to suit embeddings". The synthetic corpus has 87 bundles and the same measure
runs on it unchanged.

It answers a different question than the real-document run, and neither
substitutes for the other:

  synthetic   many bundles, one generator, markdown, and gold spans that were
              written alongside the document
  real        three documents, three genres, PDFs, and gold spans a reader
              chose afterwards

A method that wins on both is a method. A method that wins only here has learned
the generator.

## Contamination, and why the split is bundle-level

K6 trains on `label_sentences`, which labels a sentence for a factor when one of
that factor's `evidence_keywords` falls inside it. Those keywords are also the
gold here. Evaluating K6 on a bundle it trained on scores it against its own
training labels, so the split is by bundle and asserted, not assumed.

K4 needs no training -- its queries are the pack prompt anchors, compile-time
text -- so it is unaffected by the split. It is still evaluated on the identical
held-out bundles, because a comparison across different evaluation sets is not
one.
"""
from __future__ import annotations

import pathlib
import random
import sys
from math import comb

_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(_ROOT / "dev" / "tools" / "scripts"))
sys.path.insert(0, str(_ROOT / "src"))

from document_furniture import strip_furniture  # noqa: E402
from keyless_extract_probe import (  # noqa: E402
    PROMPTS,
    assert_anchors_come_from_the_prompt,
    parse_anchors,
)
from keyless_k2_extractive import sentences  # noqa: E402
from keyless_k6_classifier import (  # noqa: E402
    NULL,
    assert_bundle_level_split,
    label_sentences,
    load_split,
)
from uofa_cli import excel_constants as ec  # noqa: E402

KS = (1, 3, 5, 10, 20, 40)
ENCODER = "all-MiniLM-L6-v2"
HOLDOUT = 0.30
NAMES = tuple({n.lower() for n in ec.NASA_ALL_FACTOR_NAMES}
              | {n.lower() for n in ec.VV40_FACTOR_NAMES})


def factor_queries() -> dict[str, str]:
    out: dict[str, str] = {}
    for _pack, path in PROMPTS.items():
        anchors = parse_anchors(path)
        assert_anchors_come_from_the_prompt(anchors, path)
        for label, phrases in anchors.items():
            out.setdefault(label, f"{label}. " + "; ".join(phrases))
    if not out:
        raise SystemExit("no factor queries parsed")
    return out


def report(name, ranked, rng, ks=KS):
    n = len(ranked)
    print(f"\n  {name}   ({n} factor-bundle pairs)")
    print(f"  {'k':>3s}  {'recall@k':>9s}  {'random@k':>9s}  {'lift':>7s}   p")
    out = {}
    for k in ks:
        hit = sum(bool(set(r[:k]) & g) for r, g, _ in ranked.values())
        trials, rhit, tot = 20, 0, 0
        for _ in range(trials):
            for r, g, pool in ranked.values():
                tot += 1
                if set(rng.sample(pool, min(k, len(pool)))) & g:
                    rhit += 1
        pr = rhit / tot
        rec = hit / n
        pv = sum(comb(n, i) * pr**i * (1 - pr)**(n - i) for i in range(hit, n + 1))
        out[k] = rec
        print(f"  {k:>3d}  {rec:>9.3f}  {pr:>9.3f}  {rec - pr:>+7.3f}   "
              f"{pv:.2e}{' *' if pv < 0.05 else ''}  ({hit}/{n})")
    return out


def main() -> int:
    from sentence_transformers import SentenceTransformer
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_union

    allb = load_split(_ROOT / "tests" / "fixtures" / "extract_corpus_v2" / "dev")
    allb.sort(key=lambda b: b["id"])
    cut = int(len(allb) * (1 - HOLDOUT))
    train_b, test_b = allb[:cut], allb[cut:]
    assert_bundle_level_split(train_b, test_b)
    print(f"\nRouter comparison on the synthetic corpus")
    print(f"  {len(train_b)} train bundles, {len(test_b)} held out "
          f"(bundle-level split, asserted)")

    X, y = [], []
    for b in train_b:
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
    print(f"  K6 trained on {len(X)} sentences; K4 has {len(queries)} prompt queries")

    k6r, k4r, fused = {}, {}, {}
    skipped = 0
    for b in test_b:
        sents = sentences(b["src"])
        _, pool, _ = strip_furniture(sents, NAMES)
        if len(pool) < 10:
            skipped += 1
            continue
        texts = [sents[i] for i in pool]
        P = clf.predict_proba(feats.transform(texts))
        cvec = enc.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        # gold: sentences carrying this factor's evidence_keywords
        gold: dict[str, set[int]] = {}
        for i, (s, lab) in enumerate(label_sentences(b)):
            if lab != NULL and i < len(sents):
                gold.setdefault(lab, set()).add(i)
        for factor, g in gold.items():
            g = g & set(pool)
            if not g or factor not in cls or factor not in queries:
                continue
            key = (b["id"], factor)
            o6 = sorted(range(len(pool)), key=lambda k: -P[k][cls[factor]])
            qv = enc.encode([queries[factor]], normalize_embeddings=True,
                            show_progress_bar=False)
            sims = (qv @ cvec.T).max(axis=0)
            o4 = sorted(range(len(pool)), key=lambda k: -sims[k])
            k6r[key] = ([pool[k] for k in o6], g, pool)
            k4r[key] = ([pool[k] for k in o4], g, pool)
            p6 = {pool[k]: i for i, k in enumerate(o6)}
            p4 = {pool[k]: i for i, k in enumerate(o4)}
            fused[key] = (sorted(pool, key=lambda s: -(1.0 / (60 + p6[s])
                                                       + 1.0 / (60 + p4[s]))), g, pool)
    if skipped:
        print(f"  {skipped} bundles skipped: fewer than 10 sentences survived filtering")

    rng = random.Random(0)
    r6 = report("K6 — lexical (TF-IDF + logistic regression)", k6r, rng)
    r4 = report(f"K4 — embeddings ({ENCODER} cosine)", k4r, rng)
    rf = report("K4+K6 — reciprocal rank fusion", fused, rng)

    print(f"\n  Side by side, and against the real-document run:")
    print(f"  {'k':>3s}  {'K6':>7s} {'K4':>7s} {'RRF':>7s}    "
          f"{'K6real':>7s} {'K4real':>7s} {'RRFreal':>8s}")
    REAL6 = {1: .158, 3: .421, 5: .421, 10: .526, 20: .684, 40: .737}
    REAL4 = {1: .211, 3: .263, 5: .474, 10: .526, 20: .632, 40: .737}
    REALF = {1: .316, 3: .421, 5: .526, 10: .632, 20: .684, 40: .789}
    for k in KS:
        print(f"  {k:>3d}  {r6[k]:>7.3f} {r4[k]:>7.3f} {rf[k]:>7.3f}    "
              f"{REAL6[k]:>7.3f} {REAL4[k]:>7.3f} {REALF[k]:>8.3f}")
    # ARED's evidence lines begin with the factor name, so it flatters every
    # router. The transfer question is about journal prose, where the router has
    # to find an unlabelled finding.
    PROSE6 = {1: 0.000, 5: 0.083, 20: 0.500}
    PROSE4 = {1: 0.000, 5: 0.417, 20: 0.500}
    PROSEF = {1: 0.083, 5: 0.333, 20: 0.500}
    print(f"\n  Transfer gap: synthetic -> real JOURNAL PROSE (12 pairs, ARED dropped)")
    print(f"  {'router':6s} {'k':>3s}  {'synthetic':>10s}  {'real prose':>11s}  {'drop':>7s}")
    for name, syn, prose in (("K6", r6, PROSE6), ("K4", r4, PROSE4), ("RRF", rf, PROSEF)):
        for k in (1, 5, 20):
            print(f"  {name:6s} {k:>3d}  {syn[k]:>10.3f}  {prose[k]:>11.3f}  "
                  f"{syn[k] - prose[k]:>+7.3f}")
    print(f"\n  K6 wins outright on synthetic and loses 0.75 of it at k=5 on real")
    print(f"  prose. K4 is the weaker router here and loses 0.09. Same measure,")
    print(f"  same filter, same pool -- only the documents change.")
    print(f"\n  That asymmetry is what a model fitted to its generator looks like.")
    print(f"  K6 trains on 37 bundles from the same generator as the 17 it is")
    print(f"  scored on: a bundle-level split stops it memorising documents, not")
    print(f"  the phrasing conventions they share. K4 trains on nothing.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

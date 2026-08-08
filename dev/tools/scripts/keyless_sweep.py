#!/usr/bin/env python3
"""Register every keyless component and sweep the combinations.

Each router and selector this project has built is wrapped as a component under
the registry's contract, and every combination is scored on the same documents
with the same gold. The point is to stop comparing numbers that were measured
differently -- which has happened repeatedly here, most recently when router
recall was reported as an end-to-end result.

Run with `--corpus tests/fixtures/extract_corpus_seeded/train`. Controls are
marked `*` and are swept alongside the candidates, never omitted.
"""
from __future__ import annotations

import argparse
import pathlib
import sys

_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(_ROOT / "dev" / "tools" / "scripts"))
sys.path.insert(0, str(_ROOT / "src"))

import keyless_k10_selector as K10  # noqa: E402
from keyless_pipeline_registry import (  # noqa: E402
    REGISTRY, Doc, Pipeline, component, read, score,
)

RRF_K = 60


class Ctx:
    """Everything expensive, built once: the classifier, the encoder, queries."""

    def __init__(self) -> None:
        from sentence_transformers import SentenceTransformer
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression
        from sklearn.pipeline import make_union

        from keyless_k6_classifier import label_sentences, load_split
        from v1_router_comparison import factor_queries

        train = load_split(_ROOT / "tests" / "fixtures" / "extract_corpus_v2" / "dev")
        X, y = [], []
        for b in train:
            for s, lab in label_sentences(b):
                X.append(s)
                y.append(lab)
        self.feats = make_union(
            TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True,
                            strip_accents="unicode"),
            TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=3,
                            sublinear_tf=True))
        self.clf = LogisticRegression(max_iter=2000, class_weight="balanced", C=4.0)
        self.clf.fit(self.feats.fit_transform(X), y)
        self.cls = {c: i for i, c in enumerate(self.clf.classes_)}
        self.enc = SentenceTransformer("all-MiniLM-L6-v2")
        self.queries = factor_queries()
        self.n_train = len(train)
        self._cache: dict = {}

    def per_doc(self, doc: Doc):
        """Probabilities and embeddings, computed once per document."""
        key = str(doc.bundle)
        if key not in self._cache:
            texts = doc.texts
            self._cache[key] = (
                self.clf.predict_proba(self.feats.transform(texts)),
                self.enc.encode(texts, normalize_embeddings=True,
                                show_progress_bar=False))
        return self._cache[key]


# ── routers ───────────────────────────────────────────────────────────

@component("route", "k6")
def route_k6(doc: Doc, factor: str, ctx: Ctx) -> list[int]:
    """Lexical: TF-IDF word + char n-grams into logistic regression."""
    col = ctx.cls.get(factor)
    if col is None:
        return []
    P, _ = ctx.per_doc(doc)
    return sorted(range(len(doc.pool)), key=lambda k: -P[k][col])


@component("route", "k4")
def route_k4(doc: Doc, factor: str, ctx: Ctx) -> list[int]:
    """Embeddings: cosine against a query written from the pack prompt."""
    q = ctx.queries.get(factor)
    if q is None:
        return []
    _, cvec = ctx.per_doc(doc)
    qv = ctx.enc.encode([q], normalize_embeddings=True, show_progress_bar=False)
    sims = (qv @ cvec.T).max(axis=0)
    return sorted(range(len(doc.pool)), key=lambda k: -sims[k])


@component("route", "rrf")
def route_rrf(doc: Doc, factor: str, ctx: Ctx) -> list[int]:
    """Reciprocal rank fusion of K4 and K6.

    Fusion rather than choosing, because the two disagree per factor and neither
    dominates. RRF needs no score calibration between a cosine and a class
    probability, which are not on the same scale.
    """
    r6, r4 = route_k6(doc, factor, ctx), route_k4(doc, factor, ctx)
    if not r6:
        return r4
    if not r4:
        return r6
    p6 = {s: i for i, s in enumerate(r6)}
    p4 = {s: i for i, s in enumerate(r4)}
    n = len(doc.pool)
    return sorted(range(n), key=lambda s: -(1.0 / (RRF_K + p6.get(s, n))
                                            + 1.0 / (RRF_K + p4.get(s, n))))


@component("route", "position", control=True)
def route_position(doc: Doc, _factor: str, _ctx: Ctx) -> list[int]:
    """Null: document order.

    What `control_constant_list` can offer an extractor. It scores 1.000 on
    detection while carrying no routing signal, which is the finding that
    detection is not a metric in this domain.
    """
    return list(range(len(doc.pool)))


# ── selectors ─────────────────────────────────────────────────────────

@component("select", "k10")
def select_k10(doc: Doc, shortlist: list[int], _ctx: Ctx) -> int:
    """Finding-shaped: a figure, a comparison, past-tense reporting, not a rung."""
    return K10.select([doc.texts[i] for i in shortlist])


@component("select", "k2")
def select_k2(doc: Doc, shortlist: list[int], _ctx: Ctx) -> int:
    """K2's preference: the span carrying a digit, nearest 160 characters.

    Written to quote a rationale rather than to choose between candidates, so
    this asks what it would pick if forced to.
    """
    import re
    best, best_i = None, 0
    for j, idx in enumerate(shortlist):
        s = doc.texts[idx]
        sc = (bool(re.search(r"\\d", s)), -abs(len(s) - 160))
        if best is None or sc > best:
            best, best_i = sc, j
    return best_i


@component("select", "rank1", control=True)
def select_rank1(_doc: Doc, _shortlist: list[int], _ctx: Ctx) -> int:
    """Null: trust the router. Measured at 0.000 end to end in the deliverable."""
    return 0


@component("select", "longest", control=True)
def select_longest(doc: Doc, shortlist: list[int], _ctx: Ctx) -> int:
    """Second null: the longest sentence, which needs no reading at all."""
    return max(range(len(shortlist)), key=lambda j: len(doc.texts[shortlist[j]]))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--corpus", type=pathlib.Path, required=True)
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()

    bundles = [b for b in sorted(args.corpus.rglob("bundle_*"))
               if (b / "ground_truth.json").exists()]
    if args.limit:
        bundles = bundles[:args.limit]
    docs = [read(b) for b in bundles]
    ctx = Ctx()

    print(f"\nKeyless component sweep — {len(docs)} documents, k={args.k}")
    print(f"  K6 trained on {ctx.n_train} OLD-synthetic bundles, never on these")
    print(f"  routers  : {sorted(REGISTRY['route'])}")
    print(f"  selectors: {sorted(REGISTRY['select'])}      (* = control)\n")

    rows = []
    for r in sorted(REGISTRY["route"]):
        for s in sorted(REGISTRY["select"]):
            pipe = Pipeline(route=r, select=s)
            rows.append((pipe, score(pipe, docs, ctx, args.k)))

    print(f"  {'combination':34s}{'router':>9s}{'select|R':>10s}{'end-to-end':>12s}")
    for pipe, m in sorted(rows, key=lambda t: -t[1]["end_to_end"]):
        print(f"  {pipe.describe():34s}{m['router_recall']:>9.3f}"
              f"{m['select_given_reached']:>10.3f}{m['end_to_end']:>12.3f}")

    best = max(rows, key=lambda t: t[1]["end_to_end"])
    ctrl_only = [t for t in rows if t[0].is_all_control]
    floor = max((t[1]["end_to_end"] for t in ctrl_only), default=0.0)
    print(f"\n  best        : {best[0].describe()}  end-to-end {best[1]['end_to_end']:.3f}")
    print(f"  all-control : {floor:.3f}")
    print(f"  pairs       : {best[1]['pairs']}, of which {best[1]['reached']} reached "
          f"a shortlist")
    print("\n  'select|R' is precision@1 GIVEN the router reached the answer, so a")
    print("  selector is not charged for evidence it never saw. end-to-end is the")
    print("  product, and is the only number that describes the pipeline.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

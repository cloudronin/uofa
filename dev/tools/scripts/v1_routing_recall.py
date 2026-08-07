#!/usr/bin/env python3
"""Does K6 ROUTE well on a real document, even though it PICKS badly?

Attribution has been scored top-1: the router's single best sentence must be one
the annotation marked. That measures a picker. A detector's job in this pipeline
is routing -- handing the extractor a shortlist to read -- so the matching
question is whether a gold sentence is anywhere in the top k.

The two can differ sharply. A router that puts the right sentence at rank 3 out
of 213 every time is doing almost all the work and scores 0.000 top-1.

## Baselines, at the same k

Recall@k rises with k for any method, including a useless one, so a random
selector is reported at every k. Its expectation is k/N, which is the number
K6 has to beat -- not zero.

`control_constant_list` has no analogue here: it emits factor names, not
sentence positions, so it cannot route at all. That is the point made in plan
v3 -- routing is exactly what a constant cannot do -- and it is why this measure
is worth having.
"""
from __future__ import annotations

import json
import pathlib
import random
import sys

_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(_ROOT / "dev" / "tools" / "scripts"))
sys.path.insert(0, str(_ROOT / "src"))
sys.path.insert(0, str(_ROOT / "tests" / "fixtures" / "extract_corpus_real"))

from cas_mapping import DECOMPOSED_7009A  # noqa: E402
from document_furniture import strip_furniture  # noqa: E402
from keyless_k2_extractive import sentences  # noqa: E402
from keyless_k6_classifier import label_sentences, load_split  # noqa: E402
from uofa_cli import excel_constants as ec  # noqa: E402
from uofa_cli.readers.pdf_reader import read_pdf  # noqa: E402

BUNDLE = "bundle_real_opensim_knee"
KS = (1, 3, 5, 10, 20)
NAMES = tuple({n.lower() for n in ec.NASA_ALL_FACTOR_NAMES}
              | {k.lower() for k in DECOMPOSED_7009A})
ANNOT_TO_PUBLISHED = {
    "Code verification": "Code/solution verification",
    "Solution verification": "Code/solution verification",
    "Conceptual validation": "Conceptual validation",
    "Referent validation": "Referent validation",
    "Results uncertainty": "Results uncertainty",
    "Results robustness (sensitivity)": "Results robustness",
    "Data pedigree": "Data pedigree",
    "Input pedigree": "Input pedigree",
}


def norm(s: str) -> str:
    return " ".join(str(s).split()).lower()


def main() -> int:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_union

    src = _ROOT / "tests" / "fixtures" / "extract_corpus_real" / BUNDLE / "source"
    text = "\n".join(c.text for p in sorted(src.glob("*.pdf")) for c in read_pdf(p))
    sents = sentences(text)
    flat = norm(text)
    offs, cur = [], 0
    for s in sents:
        n = norm(s)
        i = flat.find(n, cur)
        i = i if i >= 0 else cur
        offs.append((i, i + len(n)))
        cur = i + len(n)

    ann = json.loads((_ROOT / "docs" / "v1" / "annot_opensim.json").read_text())
    gold: dict[str, set[int]] = {}
    for a in ann["annotations"]:
        pub = ANNOT_TO_PUBLISHED.get(a["factor_type"])
        if pub is None:
            continue
        for e in a["evidence"]:
            n = norm(e)
            st = flat.find(n)
            if st < 0:
                continue
            for i, (lo, hi) in enumerate(offs):
                if lo < st + len(n) and st < hi:
                    gold.setdefault(pub, set()).add(i)

    kept, idx, _ = strip_furniture(sents, NAMES)
    pool = idx
    print(f"\nRouting recall on a real document — {BUNDLE}")
    print(f"  {len(sents)} sentences, {len(pool)} after the furniture filter, "
          f"{len(gold)} factors annotated\n")

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

    P = clf.predict_proba(feats.transform([sents[i] for i in pool]))
    ranked: dict[str, list[int]] = {}
    for pub, cons in DECOMPOSED_7009A.items():
        cols = [cls[c] for c in cons if c in cls]
        if not cols or pub not in gold:
            continue
        order = sorted(range(len(pool)),
                       key=lambda k: -max(P[k][c] for c in cols))
        ranked[pub] = [pool[k] for k in order]

    rng = random.Random(0)
    print(f"  {'k':>3s}  {'K6 recall@k':>12s}  {'random@k':>10s}  {'lift':>6s}")
    for k in KS:
        hit = sum(bool(set(r[:k]) & gold[f]) for f, r in ranked.items())
        # random shortlist of the same size from the same pool, averaged
        trials = 200
        rhit = 0
        for _ in range(trials):
            for f in ranked:
                if set(rng.sample(pool, min(k, len(pool)))) & gold[f]:
                    rhit += 1
        rrec = rhit / (trials * len(ranked))
        rec = hit / len(ranked)
        print(f"  {k:>3d}  {rec:>12.3f}  {rrec:>10.3f}  {rec - rrec:>+6.3f}"
              f"   ({hit}/{len(ranked)})")

    print("\n  Rank of the best gold sentence, per factor:")
    for f, r in sorted(ranked.items()):
        best = min((r.index(g) + 1 for g in gold[f] if g in r), default=None)
        print(f"    {f:30s} {best if best else '-':>5}  of {len(r)}")

    print("\n  One document, one annotator. A shortlist that contains the answer")
    print("  is a router doing its job; whether the extractor can then use it is")
    print("  a separate question this does not answer.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

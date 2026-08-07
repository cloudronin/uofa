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

DOCS = [("opensim", "bundle_real_opensim_knee", "annot_opensim.json"),
        ("elemance", "bundle_real_elemance_thoracic", "annot_elemance_thoracic.json")]
KS = (1, 3, 5, 10, 20)
NAMES = tuple({n.lower() for n in ec.NASA_ALL_FACTOR_NAMES}
              | {k.lower() for k in DECOMPOSED_7009A})
# Annotation names -> keys of DECOMPOSED_7009A. The two papers capitalise
# differently and the OpenSim prose splits code from solution verification,
# which the published vocabulary does not; `canonical` handles case, this
# handles the split.
ANNOT_TO_PUBLISHED = {
    "code verification": "Code/solution verification",
    "solution verification": "Code/solution verification",
    "code/solution verification": "Code/solution verification",
    "conceptual validation": "Conceptual validation",
    "referent validation": "Referent validation",
    "results uncertainty": "Results uncertainty",
    "results robustness": "Results robustness",
    "results robustness (sensitivity)": "Results robustness",
    "data pedigree": "Data pedigree",
    "input pedigree": "Input pedigree",
}


def norm(s: str) -> str:
    return " ".join(str(s).split()).lower()


def main() -> int:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_union

    # one classifier, trained once, applied to every real document
    train = load_split(_ROOT / "tests" / "fixtures" / "extract_corpus_v2" / "dev")
    X, y = [], []
    for b in train:
        for s, lab in label_sentences(b):
            X.append(s); y.append(lab)
    feats = make_union(
        TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True,
                        strip_accents="unicode"),
        TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=3,
                        sublinear_tf=True))
    clf = LogisticRegression(max_iter=2000, class_weight="balanced", C=4.0)
    clf.fit(feats.fit_transform(X), y)
    cls = {c: i for i, c in enumerate(clf.classes_)}
    print(f"\nRouting recall on real documents "
          f"(K6 trained on {len(train)} synthetic bundles)\n")

    rng = random.Random(0)
    all_ranked = {}
    for tag, bundle, annot in DOCS:
        src = _ROOT / "tests" / "fixtures" / "extract_corpus_real" / bundle / "source"
        text = "\n".join(c.text for p in sorted(src.glob("*.pdf")) for c in read_pdf(p))
        sents = sentences(text)
        flat = norm(text)
        offs, cur = [], 0
        for s in sents:
            n = norm(s); i = flat.find(n, cur); i = i if i >= 0 else cur
            offs.append((i, i + len(n))); cur = i + len(n)

        ann = json.loads((_ROOT / "docs" / "v1" / annot).read_text())
        gold = {}
        for a in ann["annotations"]:
            pub = ANNOT_TO_PUBLISHED.get(a["factor_type"].strip().lower())
            if pub is None:
                continue
            for e in a["evidence"]:
                n = norm(e); st = flat.find(n)
                if st < 0:
                    continue
                for i, (lo, hi) in enumerate(offs):
                    if lo < st + len(n) and st < hi:
                        gold.setdefault(pub, set()).add(i)

        kept, pool, _ = strip_furniture(sents, NAMES)
        P = clf.predict_proba(feats.transform([sents[i] for i in pool]))
        print(f"  {tag}: {len(sents)} sentences, {len(pool)} after filtering, "
              f"{len(gold)} factors annotated")
        for pub, cons in DECOMPOSED_7009A.items():
            cols = [cls[c] for c in cons if c in cls]
            if not cols or pub not in gold:
                continue
            order = sorted(range(len(pool)), key=lambda k: -max(P[k][c] for c in cols))
            all_ranked[(tag, pub)] = ([pool[k] for k in order], gold[pub], pool)

    n = len(all_ranked)
    print(f"\n  {n} factor-document pairs across {len(DOCS)} documents\n")
    print(f"  {'k':>3s}  {'K6 recall@k':>12s}  {'random@k':>10s}  {'lift':>7s}")
    from math import comb
    for k in KS:
        hit = sum(bool(set(r[:k]) & g) for r, g, _ in all_ranked.values())
        trials, rhit, tot = 200, 0, 0
        for _ in range(trials):
            for r, g, pool in all_ranked.values():
                tot += 1
                if set(rng.sample(pool, min(k, len(pool)))) & g:
                    rhit += 1
        pr = rhit / tot
        rec = hit / n
        pv = sum(comb(n, i) * pr**i * (1 - pr)**(n - i) for i in range(hit, n + 1))
        print(f"  {k:>3d}  {rec:>12.3f}  {pr:>10.3f}  {rec - pr:>+7.3f}"
              f"   ({hit}/{n})  p={pv:.4f}{'  *' if pv < 0.05 else ''}")

    print(f"\n  Rank of the best gold sentence:")
    for (tag, pub), (r, g, pool) in sorted(all_ranked.items()):
        best = min((r.index(x) + 1 for x in g if x in r), default=None)
        print(f"    {tag:9s} {pub:30s} {best if best else '-':>5}  of {len(r)}")

    print("\n  Two documents, one annotator. random@k is the bar, not zero:")
    print("  recall@k rises with k for any method, useless ones included.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

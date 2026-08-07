#!/usr/bin/env python3
"""K6 against a real document — the transfer measurement, finally runnable.

K6's 0.615 attribution is the headline keyless figure and it has only ever been
measured on documents gpt-5 wrote. Two things blocked the real-document version
and both are now fixed:

* the PDF reader spliced two-column pages together, so 12 of 13 evidence spans
  did not exist as contiguous text (`readers/pdf_reader.py`);
* K6 predicts *pack* factors while a real paper prints *7009A* ones, so the
  prediction has to be rolled up before it can be compared — `cas_mapping.py`
  already does this, mapping each published factor to its pack constituents.

The reference is a hand annotation of `bundle_real_opensim_knee`, written before
any extractor was run against the document. One document, one annotator: this
can falsify the transfer claim, and cannot confirm it.

## What is being scored

For each published factor, which sentence does the method point at? Correct when
it lands in a sentence the annotation marked for that factor. Same question the
synthetic attribution metric asks, so the numbers sit on one scale.

The pack has no constituent for `Input pedigree` beyond `Model inputs`, and the
annotation's "Code verification" and "Solution verification" both roll into
`Code/solution verification` — the published vocabulary is coarser than either
the pack or the paper's prose, which is the honest situation and not a defect.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(_ROOT / "dev" / "tools" / "scripts"))
sys.path.insert(0, str(_ROOT / "src"))
sys.path.insert(0, str(_ROOT / "tests" / "fixtures" / "extract_corpus_real"))

from cas_mapping import DECOMPOSED_7009A  # noqa: E402
from keyless_k2_extractive import sentences  # noqa: E402
from keyless_k6_classifier import NULL, label_sentences, load_split  # noqa: E402
from uofa_cli.readers.pdf_reader import read_pdf  # noqa: E402

BUNDLE = "bundle_real_opensim_knee"
VARIANT = "decomposed_7009a"

# The annotation names the paper's own prose factors; the published table is
# coarser. Written out so the collapse is visible rather than inferred.
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
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression
        from sklearn.pipeline import make_union
    except ImportError:
        raise SystemExit("pip install scikit-learn")

    # ---- the real document, read through the repaired reader ----
    src = _ROOT / "tests" / "fixtures" / "extract_corpus_real" / BUNDLE / "source"
    text = "\n".join(c.text for p in sorted(src.glob("*.pdf")) for c in read_pdf(p))
    sents = sentences(text)
    flat = norm(text)

    # sentence char offsets, so a span crossing a boundary maps to every
    # sentence it touches rather than none
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

    print(f"\nK6 on a real document — {BUNDLE} ({VARIANT})\n")
    print(f"  {len(sents)} sentences, {len(gold)} published factors annotated")

    # ---- train K6 on the synthetic corpus, exactly as it is normally trained ----
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
                        sublinear_tf=True),
    )
    clf = LogisticRegression(max_iter=2000, class_weight="balanced", C=4.0)
    clf.fit(feats.fit_transform(X), y)
    print(f"  trained on {len(train)} synthetic bundles, {len(X)} sentences, "
          f"{len(set(y)) - 1} pack factors\n")

    # ---- predict, then roll pack factors up to the published vocabulary ----
    proba = clf.predict_proba(feats.transform(sents))
    classes = list(clf.classes_)
    idx = {c: i for i, c in enumerate(classes)}

    k6: dict[str, set[int]] = {}
    for pub, constituents in DECOMPOSED_7009A.items():
        cols = [idx[c] for c in constituents if c in idx]
        if not cols:
            continue
        # score(sentence, published) = max over its pack constituents
        best, top = None, -1.0
        for i in range(len(sents)):
            v = max(proba[i][c] for c in cols)
            if v > top:
                best, top = i, v
        if best is not None:
            k6[pub] = {best}

    # ---- controls, on the identical question ----
    published = list(DECOMPOSED_7009A)
    const = {f: {i} for i, f in enumerate(published)}

    import re
    def lexical(f: str) -> set[int]:
        key = [w for w in re.findall(r"[a-z]{4,}", f.lower())
               if w not in {"the", "and", "for", "of", "to", "with"}]
        best, score = None, 0
        for i, s in enumerate(sents):
            n = sum(w in norm(s) for w in key)
            if n > score:
                best, score = i, n
        return {best} if best is not None else set()
    lex = {f: lexical(f) for f in published}

    print(f"  {'method':28s} {'attribution':>12s}   detail")
    for label, pred in (("control: document order", const),
                        ("keyless lexical routing", lex),
                        ("K6 rolled up", k6)):
        right = scored = 0
        misses = []
        for f, want in gold.items():
            got = pred.get(f) or set()
            if not got:
                continue
            scored += 1
            if got & want:
                right += 1
            else:
                misses.append(f)
        acc = right / scored if scored else 0.0
        print(f"  {label:28s} {acc:>12.3f}   ({right}/{scored})")

    print("\n  Where K6 pointed, per published factor:")
    for f in sorted(gold):
        got = k6.get(f) or set()
        i = next(iter(got), None)
        mark = "hit " if got & gold[f] else "MISS"
        print(f"    {mark} {f:30s} -> s{i}: {sents[i][:64] if i is not None else '-'!r}")
        g = sorted(gold[f])[0]
        print(f"         {'':30s}    gold s{g}: {sents[g][:64]!r}")

    print("\n  One document, one annotator, synthetic-trained. Falsifying, not")
    print("  confirming: a low score here is informative, a high one is not proof.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

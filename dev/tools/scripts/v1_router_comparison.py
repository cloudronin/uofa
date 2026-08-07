#!/usr/bin/env python3
"""K4 (embeddings) vs K6 (lexical) as ROUTERS on real documents.

K4 was killed for failing detection F1 against `control_constant_list`. Plan v3
then established that detection F1 is the wrong metric permanently -- a constant
scores 0.960 synthetic and 1.000 on the real corpus -- and K6, killed by the
same criterion, was rescued once it was scored as a router instead.

K4 has never been scored as a router. It is retired on a discredited metric.

That matters here specifically, because routing recall is now the pipeline's
bottleneck (0.500, against a selector at 0.833), and K4 was built for exactly
the gap that caps a lexical router:

    the anchors are written at the abstraction level of the standard
    ("QoI directly measures the safety concern") while the documents are
    written at the level of the physics ("head rise prediction", "SST k-omega")

TF-IDF cannot cross that gap by construction -- no shared token, no score. An
embedding can or cannot, and on real documents written by strangers the gap
should be wider than on synthetic text, so this is where the difference shows if
there is one.

## Same protocol as K6

Same two documents, same 12 factor-document pairs, same hand annotation, same
furniture filter, same recall@k, same random baseline at each k. The only thing
that changes is how candidates are ranked.

K4 ranks by cosine between a factor query and each sentence. The query is the
factor name plus the pack prompt's own anchors -- the same text K1 matched on,
so this measures what the encoder adds over substring matching against identical
input.

## Contamination

`evidence_keywords` are verbatim source spans and are never embedded: that would
score the answer against itself. Factor queries come from the pack prompt files,
which are compile-time text.
"""
from __future__ import annotations

import json
import pathlib
import random
import re
import sys
from math import comb

_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(_ROOT / "dev" / "tools" / "scripts"))
sys.path.insert(0, str(_ROOT / "src"))
sys.path.insert(0, str(_ROOT / "tests" / "fixtures" / "extract_corpus_real"))

from cas_mapping import DECOMPOSED_7009A, VARIANTS, unmapped_factors  # noqa: E402
from document_furniture import strip_furniture  # noqa: E402
from keyless_extract_probe import (  # noqa: E402
    PROMPTS,
    assert_anchors_come_from_the_prompt,
    parse_anchors,
)
from keyless_k2_extractive import sentences  # noqa: E402
from keyless_k6_classifier import label_sentences, load_split  # noqa: E402
from uofa_cli import excel_constants as ec  # noqa: E402
from uofa_cli.readers.pdf_reader import read_pdf  # noqa: E402

DOCS = [("opensim", "bundle_real_opensim_knee", "annot_opensim.json"),
        ("elemance", "bundle_real_elemance_thoracic", "annot_elemance_thoracic.json"),
        # rollup_7009a, and a poster rather than a journal article -- if routing
        # only works on decomposed-vocabulary prose, this is where it shows.
        ("ared", "bundle_real_ared_dap", "annot_ared_dap.json"),
        # ASME V&V 40, not NASA 7009A. Maps onto the vv40 pack by identity, so
        # no rollup -- the only document in the set where published and pack
        # vocabulary are the same, which is why it lives in its own corpus dir.
        ("bologna", "extract_corpus_vv40/bundle_bologna_bcthip", "annot_bologna.json"),
        ("nagaraja", "extract_corpus_vv40/bundle_nagaraja", "annot_nagaraja.json"),
        ("morrison", "extract_corpus_vv40/bundle_morrison", "annot_morrison.json")]
KS = (1, 3, 5, 10, 20, 40)
ENCODER = "all-MiniLM-L6-v2"
NAMES = tuple({n.lower() for n in ec.NASA_ALL_FACTOR_NAMES}
              | {k.lower() for k in DECOMPOSED_7009A})
# Published factor names vary in case between papers; `canonical` resolves that.
# This table only handles the cases where the annotation is FINER than the
# published vocabulary (the OpenSim prose splits code from solution
# verification, which decomposed_7009a does not).
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


def factor_queries() -> dict[str, str]:
    """Factor name plus the pack prompt's own anchors, per pack factor.

    Uses the canonical PROMPTS mapping and parse_anchors rather than a private
    glob -- an earlier version globbed for *.md, the prompts are .txt, and it
    silently produced zero queries. `assert_anchors_come_from_the_prompt` is the
    contamination guard: the query text must come from compile-time prompt
    files, never from `evidence_keywords`, which are verbatim source spans and
    would score the answer against itself.
    """
    out: dict[str, str] = {}
    for pack, path in PROMPTS.items():
        anchors = parse_anchors(path)
        assert_anchors_come_from_the_prompt(anchors, path)
        for label, phrases in anchors.items():
            out.setdefault(label, f"{label}. " + "; ".join(phrases))
    if not out:
        raise SystemExit("no factor queries parsed -- the comparison would be empty")
    return out


def load_case(tag, bundle, annot):
    base = (_ROOT / "tests" / "fixtures" / bundle if "/" in bundle
            else _ROOT / "tests" / "fixtures" / "extract_corpus_real" / bundle)
    gt = json.loads((base / "ground_truth.json").read_text())
    # V&V 40 documents have no cas_variant: their published vocabulary IS the
    # pack's, so the "mapping" is identity and `VARIANTS` does not apply.
    variant = gt.get("cas_variant")
    src = base / "source"
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
    ann = json.loads((_ROOT / "docs" / "v1" / annot).read_text())
    if variant is None:
        table = {f: [f] for f in ec.VV40_FACTOR_NAMES}
    else:
        table = VARIANTS[variant]
    lowered = {k.lower(): k for k in table}
    # A published factor with no pack constituent cannot be routed at all --
    # People Qualifications, where the pack has nothing to say about who ran the
    # model. Excluded rather than scored as a miss, which would penalise the
    # router for a gap in the schema.
    unmapped = set(unmapped_factors(variant)) if variant else set()
    gold: dict[str, set[int]] = {}
    for a in ann["annotations"]:
        raw = a["factor_type"].strip()
        pub = lowered.get(raw.lower()) or ANNOT_TO_PUBLISHED.get(raw.lower())
        if pub is None or pub in unmapped:
            continue
        for e in a["evidence"]:
            n = norm(e)
            st = flat.find(n)
            if st < 0:
                continue
            for i, (lo, hi) in enumerate(offs):
                if lo < st + len(n) and st < hi:
                    gold.setdefault(pub, set()).add(i)
    _, pool, _ = strip_furniture(sents, NAMES)
    return sents, pool, gold, variant


def report(name, ranked, rng):
    n = len(ranked)
    print(f"\n  {name}")
    print(f"  {'k':>3s}  {'recall@k':>9s}  {'random@k':>9s}  {'lift':>7s}   p")
    for k in KS:
        hit = sum(bool(set(r[:k]) & g) for r, g, _ in ranked.values())
        trials, rhit, tot = 120, 0, 0
        for _ in range(trials):
            for r, g, pool in ranked.values():
                tot += 1
                if set(rng.sample(pool, min(k, len(pool)))) & g:
                    rhit += 1
        pr = rhit / tot
        rec = hit / n
        pv = sum(comb(n, i) * pr**i * (1 - pr)**(n - i) for i in range(hit, n + 1))
        print(f"  {k:>3d}  {rec:>9.3f}  {pr:>9.3f}  {rec - pr:>+7.3f}   "
              f"{pv:.4f}{' *' if pv < 0.05 else ''}  ({hit}/{n})")


def main() -> int:
    from sentence_transformers import SentenceTransformer
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_union

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
    print(f"\nRouter comparison on real documents")
    print(f"  K6: TF-IDF word(1,2) + char_wb(3,5) -> logistic regression, "
          f"{len(train)} synthetic bundles")
    print(f"  K4: {ENCODER} cosine, {len(queries)} factor queries from pack prompts")

    k6r, k4r = {}, {}
    for tag, bundle, annot in DOCS:
        sents, pool, gold, variant = load_case(tag, bundle, annot)
        texts = [sents[i] for i in pool]
        P = clf.predict_proba(feats.transform(texts))
        cvec = enc.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        table = ({f: [f] for f in ec.VV40_FACTOR_NAMES} if variant is None
                 else VARIANTS[variant])
        for pub, cons in table.items():
            if pub not in gold:
                continue
            cols = [cls[c] for c in cons if c in cls]
            if cols:
                order = sorted(range(len(pool)),
                               key=lambda k: -max(P[k][c] for c in cols))
                k6r[(tag, pub)] = ([pool[k] for k in order], gold[pub], pool)
            qs = [queries[c] for c in cons if c in queries]
            if qs:
                qv = enc.encode(qs, normalize_embeddings=True, show_progress_bar=False)
                sims = (qv @ cvec.T).max(axis=0)
                order = sorted(range(len(pool)), key=lambda k: -sims[k])
                k4r[(tag, pub)] = ([pool[k] for k in order], gold[pub], pool)

    # Reciprocal rank fusion. The two routers disagree per factor -- K4 wins
    # results uncertainty (363 -> 21) and robustness (60 -> 3), K6 wins referent
    # validation (81 -> 12) -- which is the case for combining them rather than
    # choosing. RRF is used because it needs no score calibration between a
    # cosine and a class probability, which are not on the same scale.
    RRF_K = 60
    fused = {}
    for key in set(k6r) & set(k4r):
        r6, gold, pool = k6r[key]
        r4, _, _ = k4r[key]
        p6 = {s: i for i, s in enumerate(r6)}
        p4 = {s: i for i, s in enumerate(r4)}
        order = sorted(pool, key=lambda s: -(1.0 / (RRF_K + p6.get(s, len(pool)))
                                             + 1.0 / (RRF_K + p4.get(s, len(pool)))))
        fused[key] = (order, gold, pool)

    rng = random.Random(0)
    report("K6 — lexical (TF-IDF + logistic regression)", k6r, rng)
    report(f"K4 — embeddings ({ENCODER} cosine)", k4r, rng)
    report("K4+K6 — reciprocal rank fusion", fused, rng)

    print(f"\n  Best gold rank, per pair:")
    print(f"    {'document':9s} {'factor':30s} {'K6':>6s} {'K4':>6s} {'RRF':>6s}  of")
    for key in sorted(set(k6r) | set(k4r)):
        tag, pub = key
        def best(d):
            if key not in d:
                return None
            r, g, _ = d[key]
            return min((r.index(x) + 1 for x in g if x in r), default=None)
        b6, b4, bf = best(k6r), best(k4r), best(fused)
        pool_n = len(k6r.get(key, k4r[key])[2])
        print(f"    {tag:9s} {pub:30s} {b6 if b6 else '-':>6} {b4 if b4 else '-':>6} "
              f"{bf if bf else '-':>6}  {pool_n}")

    print(f"\n  Same documents, annotation, filter and baseline as the K6 run;")
    print(f"  only the ranking changes. K4 was retired on detection F1, which")
    print(f"  plan v3 established is the wrong metric permanently.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

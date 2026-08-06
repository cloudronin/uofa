#!/usr/bin/env python3
"""Detector and extractor are different jobs. Score the pair, not the parts.

Every candidate so far was scored in isolation against `control_constant_list`,
and all three detectors lost:

    K1 substring    R 0.235   delta F1 -0.593
    K4 embeddings   R 0.993   delta F1 -0.002   (flags everything)
    K6 classifier   R 0.870   delta F1 -0.140

That framing is wrong, and the wrongness is structural rather than a tuning
problem. The corpus is ~94% `assessed`, so a function announcing every factor
scores F1 0.967 having read nothing. No detector can beat it, and the number
says nothing about whether a detector is useful.

## What a detector is actually for

Not to be right on its own -- to **route**. It tells the extractor which
sentences to read. And that is exactly what the constant cannot do: "all
nineteen factors are present" carries no routing signal at all, so an extractor
downstream of it has nothing to go on and must fall back on position.

So the constant's perfect detection score is worthless the moment anything
depends on it, and the comparison that matters is:

    (detector -> extractor)   versus   (constant -> the same extractor)

Same extractor on both sides. The only thing that varies is whether the routing
signal exists.

## The two roles, and that they need not be one model

  DETECTOR   sentence -> which factor (or none)
             K1 substring, K4 embeddings, K6 classifier, constant
  EXTRACTOR  routed sentences -> the value to record
             K2 quote-the-span, and later K3 entities, K5 decision

Nothing requires these to be the same model, and the evidence says they should
not be: K6 recalls 0.870 as a router while K1 recalls 0.235, but K1's precision
0.973 makes it the better *value* selector where it does fire.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(_ROOT / "dev" / "tools" / "scripts"))
sys.path.insert(0, str(_ROOT / "src"))

from groundedness import GroundednessResult, score_factor_rationales  # noqa: E402
from keyless_extract_probe import PROMPTS, parse_anchors  # noqa: E402
from keyless_k2_extractive import quote_for, sentences  # noqa: E402
from keyless_k6_classifier import NULL, label_sentences, load_split  # noqa: E402


def attribution(rationales: list[dict], gt: dict) -> tuple[int, int]:
    """Is the quoted span actually about the factor it was filed under?

    The metric the other four cannot supply. Groundedness says the figure is
    real; distinctness says the spans differ; neither asks whether the span
    belongs to THIS factor -- and that is precisely and only what the detector
    decides. Measured in the pipeline run, coverage/density/groundedness/
    distinctness all read ~1.000 for a constant router that simply walks the
    document in order, so without attribution the pipeline cannot tell a
    detector from no detector.

    A quote is correctly attributed when it contains one of that factor's
    `evidence_keywords`. Those are verbatim source spans, usable here as
    ground truth for evaluation on HELD-OUT bundles -- never as a matcher seed,
    and never on bundles the router was trained on.
    """
    want = {f["factor_type"]: [" ".join(str(k).split()).lower()
                               for k in (f.get("evidence_keywords") or [])]
            for f in gt["expected_factors"]}
    right = scored = 0
    for r in rationales:
        q = r.get("rationale")
        kws = want.get(r["factor_type"]) or []
        if not q or not kws:
            continue
        scored += 1
        low = " ".join(q.split()).lower()
        if any(k in low for k in kws if len(k) >= 4):
            right += 1
    return right, scored


def extract_k2(spans: list[str], routing: dict[str, list[int]],
               factors: list[str]) -> list[dict]:
    """K2 as an EXTRACTOR: quote the best routed span, never reusing one.

    `routing` maps factor -> candidate span indices, ranked best first. The
    extractor's only job is to pick one and quote it; which spans are on offer
    is the detector's job. Splitting the roles this way is what lets the same
    extractor sit downstream of every detector.
    """
    taken: set[int] = set()
    out = []
    for f in factors:
        pick = None
        for i in routing.get(f, []):
            if i not in taken and 40 <= len(spans[i]) <= 400:
                pick = i
                break
        if pick is not None:
            taken.add(pick)
            out.append({"factor_type": f, "rationale": spans[pick]})
        else:
            out.append({"factor_type": f, "rationale": None})
    return out


def route_constant(spans: list[str], factors: list[str], **_) -> dict[str, list[int]]:
    """The null detector: every factor is present, and no idea where.

    It announces all of them and offers the document in reading order, because
    that is genuinely all it knows. This is the honest downstream consequence of
    a detector that scores F1 0.967 by reading nothing.
    """
    order = list(range(len(spans)))
    return {f: order for f in factors}


def route_anchors(spans: list[str], factors: list[str], anchors=None, **_):
    out = {}
    low = [s.lower() for s in spans]
    for f in factors:
        phrases = anchors.get(f, [])
        hits = [i for i, s in enumerate(low) if any(p in s for p in phrases)]
        hits.sort(key=lambda i: (not any(c.isdigit() for c in spans[i]),))
        out[f] = hits
    return out


def route_classifier(spans: list[str], factors: list[str], clf=None, feats=None,
                     classes=None, **_):
    if not spans:
        return {f: [] for f in factors}
    prob = clf.predict_proba(feats.transform(spans))
    out: dict[str, list[int]] = {f: [] for f in factors}
    idx = {c: j for j, c in enumerate(classes)}
    for f in factors:
        if f not in idx:
            continue
        col = prob[:, idx[f]]
        out[f] = [i for i in col.argsort()[::-1] if col[i] > 0.05]
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    root = _ROOT / "tests" / "fixtures" / "extract_corpus_v2"
    ap.add_argument("--corpus", type=Path, default=root / "dev")
    ap.add_argument("--holdout", type=float, default=0.30)
    args = ap.parse_args()

    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_union

    allb = sorted(load_split(args.corpus), key=lambda b: b["id"])
    cut = int(len(allb) * (1 - args.holdout))
    train_b, test_b = allb[:cut], allb[cut:]

    Xtr, ytr = [], []
    for b in train_b:
        for s, y in label_sentences(b):
            Xtr.append(s); ytr.append(y)
    feats = make_union(
        TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True),
        TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=3,
                        sublinear_tf=True))
    clf = LogisticRegression(max_iter=2000, class_weight="balanced", C=4.0)
    clf.fit(feats.fit_transform(Xtr), ytr)
    anchors = {p: parse_anchors(path) for p, path in PROMPTS.items()}

    detectors = {
        "constant  -> K2": (route_constant, {}),
        "K1 anchors-> K2": (route_anchors, {}),
        "K6 classif-> K2": (route_classifier,
                            {"clf": clf, "feats": feats, "classes": list(clf.classes_)}),
    }

    print(f"\nPipeline: detector -> K2 extractor   "
          f"({len(test_b)} held-out bundles)\n")
    print(f"  {'pipeline':18s} {'cov':>6s} {'den':>6s} {'gnd':>6s} {'distinct':>9s} {'ATTRIB':>8s}")

    for label, (router, kw) in detectors.items():
        agg = GroundednessResult()
        a_right = a_scored = 0
        for b in test_b:
            spans = sentences(b["src"])
            factors = [f["factor_type"] for f in b["gt"]["expected_factors"]]
            routing = router(spans, factors, anchors=anchors.get(b["pack"], {}), **kw)
            rats = extract_k2(spans, routing, factors)
            ar, asc = attribution(rats, b["gt"])
            a_right += ar; a_scored += asc
            res = score_factor_rationales(rats, b["src"])
            for k in ("factors_total", "factors_with_rationale", "rationales_with_claims",
                      "claims_total", "claims_grounded", "factors_distinct"):
                setattr(agg, k, getattr(agg, k) + getattr(res, k))
        att = a_right / a_scored if a_scored else 0.0
        print(f"  {label:18s} {agg.coverage:>6.3f} {agg.claim_density:>6.3f} "
              f"{agg.groundedness:>6.3f} {agg.distinctness:>9.3f} {att:>8.3f}")

    print(f"\n  Same extractor throughout; the only variable is the routing signal.")
    print(f"  ATTRIB is the column that sees the detector. Coverage, density,")
    print(f"  groundedness and distinctness all read ~1.000 for a constant router")
    print(f"  that walks the document in order, because a verbatim quote is always")
    print(f"  grounded and the extractor enforces distinctness itself. Only")
    print(f"  attribution asks whether the span belongs to the factor it was filed")
    print(f"  under, which is the one thing a detector decides.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

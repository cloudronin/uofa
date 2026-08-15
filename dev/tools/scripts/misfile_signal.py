#!/usr/bin/env python3
"""Phase 4: a second opinion that can disagree with the filing.

The naive version is dead and the reason is measured. The extractor writes each
rationale in its FILED factor's vocabulary regardless of what evidence it
quotes, so a second reader given the rationale as written names the filed factor
0.70 of the time and the correct factor for a genuine misfile 4 times in 68.
**Any post-hoc re-attribution that reads the rationale as written confirms the
misfiling 94% of the time.**

So the mechanism has to be denied the label vocabulary, exactly as
`keyless_k10_selector.score_sentence` was deliberately denied the factor name:
"How much this reads like a reported finding. Deliberately not the name."

## What is compared

    base rate         flag everything. Precision = the misfile rate itself.
    prompt anchors    score the rationale against the pack's `Look for:` terms.
                      Already refused three times (routing 0.367 vs a 0.960
                      control; re-attribution 0.059; author rationales 0.522
                      against a 0.522 name-only null). Included so the refusal
                      is measured here too rather than asserted.
    K6 unmasked       trained classifier, factor names left in the text.
    K6 masked         trained classifier, factor names and their content words
                      struck from the rationale before it is read.

Bundle-level splits throughout, via `assert_bundle_level_split`. A sentence-level
split leaks: two spans from one paragraph, one each side, make the score a
memorisation check.

## The labels may train and may score and may never seed a matcher

Ground truth is `attribution_confusion` under the Phase 3 sentence-index rule:
a row is a misfile when its rationale localises to a sentence carrying another
factor's evidence. `evidence_keywords` are verbatim source spans, so a matcher
seeded with them scores near 1.00 by construction.

Usage:

    PYTHONPATH=src python dev/tools/scripts/misfile_signal.py
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(_ROOT / "dev" / "tools" / "scripts"))
sys.path.insert(0, str(_ROOT / "src"))

from groundedness import (  # noqa: E402
    _tokens,
    gold_sentence_sets,
    locate_sentence,
    read_source_text,
)
from keyless_extract_probe import PROMPTS, parse_anchors  # noqa: E402
from score_extraction import parse_extracted_xlsx  # noqa: E402
from uofa_cli.segmentation import sentences  # noqa: E402

# Minimum precision gain that justifies keeping the extra feature block, declared
# before it is measured.
FEATURE_GAIN_FLOOR = 0.05

# Precision on real documents below which the signal stays a confidence
# demotion and does not become a `Concern` in the readout.
CONCERN_FLOOR = 0.85


def available() -> tuple[bool, str]:
    """(usable, precise reason). Never degrade silently to a worse method.

    Follows keyless_trained.available: a route that cannot run says so and
    reports itself unavailable, rather than quietly falling back to something
    that scores differently under the same name.
    """
    try:
        import sklearn  # noqa: F401
    except ImportError:
        return False, ("scikit-learn is not installed; the misfile signal needs "
                       "it for the trained second opinion. Install it, or run "
                       "without the signal -- it is optional by design.")
    return True, "ok"


def mask_factor_vocabulary(text: str, factor_names: list[str]) -> str:
    """Strike every factor's name words from the text.

    The rationale is written in its filed factor's vocabulary, so leaving the
    names in lets the classifier read the label off the prose and agree with it.
    That is the 94%-confirmation failure, and masking is the whole mechanism.
    """
    vocab = set()
    for name in factor_names:
        vocab |= {w for w in re.findall(r"[a-z]{4,}", name.lower())}
    out = []
    for w in re.findall(r"\w+|\W+", text):
        out.append("" if w.lower() in vocab else w)
    return "".join(out)


def load_rows(corpus_glob: str) -> list[dict]:
    """One row per scored factor, with its misfile label from the Phase 3 rule."""
    rows: list[dict] = []
    for bd in sorted(glob.glob(corpus_glob)):
        gtp = os.path.join(bd, "ground_truth.json")
        xl = Path(bd) / "extracted.xlsx"
        if not (os.path.exists(gtp) and xl.exists()):
            continue
        gt = json.loads(Path(gtp).read_text())
        names = [f["factor_type"] for f in gt["expected_factors"]]
        facs = parse_extracted_xlsx(xl, names).get("credibility_factors", [])
        text = read_source_text(Path(bd))
        sents = sentences(text)
        gold = gold_sentence_sets(gt, text, sents)
        stoks = [_tokens(s) for s in sents]
        for f in facs:
            n = f.get("factor_type")
            r = f.get("rationale")
            if not isinstance(r, str) or not r.strip():
                continue
            g = gold.get(n) or set()
            if not g:
                continue
            pred = locate_sentence(r, sents, stoks)
            if pred is None:
                continue
            correct = pred in g
            elsewhere = any(pred in gg for k, gg in gold.items() if k != n)
            rows.append({
                "bundle": Path(bd).name, "pack": gt["pack"], "factor": n,
                "rationale": r, "misfiled": bool(not correct and elsewhere),
                "names": names,
            })
    return rows


def _folds(rows: list[dict]) -> list[tuple[list[dict], list[dict]]]:
    """Bundle-level 2-fold. Never split a document across the two sides."""
    bundles = sorted({r["bundle"] for r in rows})
    a = set(bundles[::2])
    fold_a = [r for r in rows if r["bundle"] in a]
    fold_b = [r for r in rows if r["bundle"] not in a]
    overlap = {r["bundle"] for r in fold_a} & {r["bundle"] for r in fold_b}
    if overlap:
        raise SystemExit(f"CONTAMINATION: {sorted(overlap)[:5]} on both sides")
    return [(fold_a, fold_b), (fold_b, fold_a)]


def _pr(flags: list[bool], truth: list[bool]) -> tuple[float, float, int]:
    tp = sum(1 for f, t in zip(flags, truth) if f and t)
    fired = sum(flags)
    real = sum(truth)
    return (tp / fired if fired else 0.0,
            tp / real if real else 0.0,
            fired)


def run_base_rate(rows: list[dict]) -> tuple[float, float, int]:
    return _pr([True] * len(rows), [r["misfiled"] for r in rows])


def run_anchors(rows: list[dict]) -> tuple[float, float, int]:
    """Flag when the rationale scores higher against ANOTHER factor's anchors."""
    anchors = {}
    for pack, path in PROMPTS.items():
        anchors[pack] = parse_anchors(path)
    flags = []
    for r in rows:
        table = anchors.get(r["pack"], {})
        rt = _tokens(r["rationale"])
        best, best_s = None, 0.0
        for factor, phrases in table.items():
            s = max((len(_tokens(p) & rt) / max(1, len(_tokens(p)))
                     for p in phrases), default=0.0)
            if s > best_s:
                best, best_s = factor, s
        flags.append(best is not None and best != r["factor"])
    return _pr(flags, [r["misfiled"] for r in rows])


def run_trained(rows: list[dict], masked: bool,
                positional: bool = False) -> tuple[float, float, int]:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_union

    flags = [False] * len(rows)
    index = {id(r): i for i, r in enumerate(rows)}
    for train, test in _folds(rows):
        if not train or not test:
            continue

        def feats(rs):
            return [mask_factor_vocabulary(r["rationale"], r["names"]) if masked
                    else r["rationale"] for r in rs]

        vec = make_union(
            TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True,
                            strip_accents="unicode"),
            TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=3,
                            sublinear_tf=True))
        X = vec.fit_transform(feats(train))
        y = [r["misfiled"] for r in train]
        if len(set(y)) < 2:
            continue
        if positional:
            import numpy as np
            from scipy.sparse import csr_matrix, hstack

            def extra(rs):
                return csr_matrix(np.array(
                    [[len(r["rationale"]), len(r["rationale"].split()),
                      float(bool(re.search(r"\d", r["rationale"]))),
                      float(r["rationale"].strip().endswith("."))]
                     for r in rs], dtype=float))
            X = hstack([X, extra(train)]).tocsr()
        clf = LogisticRegression(max_iter=2000, class_weight="balanced", C=4.0)
        clf.fit(X, y)
        Xt = vec.transform(feats(test))
        if positional:
            from scipy.sparse import hstack as h2
            Xt = h2([Xt, extra(test)]).tocsr()
        for r, p in zip(test, clf.predict(Xt)):
            flags[index[id(r)]] = bool(p)
    return _pr(flags, [r["misfiled"] for r in rows])


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--corpus",
                    default=str(_ROOT / "tests/fixtures/extract_corpus/*/bundle_*"))
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()

    ok, why = available()
    if not ok:
        raise SystemExit(f"MISFILE SIGNAL UNAVAILABLE: {why}")

    rows = load_rows(args.corpus)
    if not rows:
        raise SystemExit("no scored rows; nothing to measure")
    base = sum(r["misfiled"] for r in rows) / len(rows)
    print(f"rows {len(rows)}   bundles {len({r['bundle'] for r in rows})}   "
          f"misfile base rate {base:.3f}\n")

    results = {}
    print(f"{'second opinion':<28s} {'precision':>10s} {'recall':>8s} {'fired':>7s}")
    for label, fn in (
        ("base rate (fire always)", lambda: run_base_rate(rows)),
        ("prompt anchors", lambda: run_anchors(rows)),
        ("K6 trained, unmasked", lambda: run_trained(rows, masked=False)),
        ("K6 trained, masked", lambda: run_trained(rows, masked=True)),
        ("K6 masked + extra feats", lambda: run_trained(rows, True, True)),
    ):
        p, r, fired = fn()
        results[label] = {"precision": p, "recall": r, "fired": fired}
        print(f"{label:<28s} {p:>10.3f} {r:>8.3f} {fired:>7d}")

    masked_p = results["K6 trained, masked"]["precision"]
    extra_p = results["K6 masked + extra feats"]["precision"]
    gain = extra_p - masked_p
    print(f"\n  extra features moved precision {gain:+.3f} "
          f"(floor {FEATURE_GAIN_FLOOR}) -> "
          f"{'KEEP' if gain >= FEATURE_GAIN_FLOOR else 'DROP, declared before measuring'}")
    print(f"  masked over base: {masked_p - base:+.3f} "
          f"({masked_p / base:.2f}x)" if base else "")
    print(f"\n  Ships as a CONFIDENCE DEMOTION, not a warning banner: at this "
          f"\n  precision the signal is wrong {1 - masked_p:.0%} of the time, and a red "
          f"\n  'MISFILED' label at that rate is the mirror of the failure this "
          f"\n  project already paid for. Promotion to a `Concern` needs "
          f"{CONCERN_FLOOR:.2f}"
          f"\n  precision on REAL documents, which is not measured here.")

    if args.out:
        args.out.write_text(json.dumps(
            {"rows": len(rows), "base_rate": base, "results": results,
             "feature_gain": gain}, indent=1) + "\n")
        print(f"\n  wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""EXPLORATORY: an embedding-based second opinion, after the LLM.

## Status: a look, not a finding

**No kill criteria were declared before this ran.** It is exploration, and its
output may not be cited as a measured result, promoted into a study conclusion,
or compared to a gated figure as though it were one. If any number here looks
worth having, the way to have it is to declare criteria and run it again.

Marked this loudly because the project's whole month has been about the
difference, and an exploratory number in a repo full of gated ones is exactly
the kind of thing that gets quoted six months later without its caveat.

## What is new here

Embeddings have been tried extensively and always as a *replacement* for the
LLM -- K4 alone, and RRF fusion of K4+K6 as a keyless router (recall@5 0.357,
@20 0.607). They have never been tried as a stage *alongside* the LLM.

Of the two hybrid directions:

- **before the LLM** (retrieve a shortlist, LLM reads only that) is rejected on
  a ceiling argument that does not need running: router recall 0.357 against the
  LLM's 0.62 can only cap performance, and a longer shortlist is worse --
  selection quality 1.000 -> 0.833 -> 0.250 as k goes 5 -> 20 -> 40.
- **after the LLM** (LLM extracts, encoder checks) is untried. Phase 4 did this
  shape with TF-IDF (K6) and reached 0.247 precision against a 0.175 base rate.

This is that second direction with an encoder instead of TF-IDF.

## Why it is worth a look despite Phase 4 failing

Phase 4's most informative negative was that **masking the factor vocabulary
made no difference at all** -- 0.247 both ways, with a mask that verifiably
strips 99% of factor tokens. If lexical features carried the signal, masking
should have hurt them. That they did not move is weak evidence that TF-IDF is
the wrong representation for this question, which is the same argument K4 was
built on for routing.

## Three variants, all post-LLM

    A. encoder + logistic regression, on the rationale
    B. as A, with the factor vocabulary masked
    C. no classifier at all -- cosine between the rationale and the factor's
       own prompt definition, flag when another factor scores higher

C is the interesting one: it needs no training, so it cannot overfit the
labels, and it is the direct embedding analogue of the anchor dictionary that
has now failed four times on lexical matching.

Usage:

    PYTHONPATH=src python dev/tools/scripts/misfile_signal_embeddings.py
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(_ROOT / "dev" / "tools" / "scripts"))
sys.path.insert(0, str(_ROOT / "src"))

from keyless_extract_probe import PROMPTS, parse_anchors  # noqa: E402
from misfile_signal import _folds, _pr, load_rows, mask_factor_vocabulary  # noqa: E402

ENCODER = "all-MiniLM-L6-v2"


def available() -> tuple[bool, str]:
    try:
        import sentence_transformers  # noqa: F401
    except ImportError:
        return False, (f"sentence-transformers is not installed; this needs "
                       f"{ENCODER}. Dev-only by design -- the shipped CLI must "
                       f"not acquire a torch stack for an exploratory check.")
    return True, "ok"


def _encoder():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(ENCODER)


def run_trained(rows: list[dict], enc, masked: bool) -> tuple[float, float, int]:
    """Encoder embeddings into logistic regression. Bundle-level 2-fold."""
    import numpy as np
    from sklearn.linear_model import LogisticRegression

    def texts(rs):
        return [mask_factor_vocabulary(r["rationale"], r["names"]) if masked
                else r["rationale"] for r in rs]

    flags = [False] * len(rows)
    index = {id(r): i for i, r in enumerate(rows)}
    for train, test in _folds(rows):
        if not train or not test:
            continue
        y = [r["misfiled"] for r in train]
        if len(set(y)) < 2:
            continue
        X = enc.encode(texts(train), normalize_embeddings=True,
                       show_progress_bar=False)
        clf = LogisticRegression(max_iter=2000, class_weight="balanced", C=4.0)
        clf.fit(np.asarray(X), y)
        Xt = enc.encode(texts(test), normalize_embeddings=True,
                        show_progress_bar=False)
        for r, p in zip(test, clf.predict(np.asarray(Xt))):
            flags[index[id(r)]] = bool(p)
    return _pr(flags, [r["misfiled"] for r in rows])


def run_untrained(rows: list[dict], enc) -> tuple[float, float, int]:
    """No training: cosine between the rationale and each factor's definition.

    Flag when some other factor's definition is closer than the filed one. The
    embedding analogue of the anchor dictionary, which has failed four times on
    lexical matching -- routing 0.367 against a 0.960 control, re-attribution
    0.059, author-rationale recovery 0.522 against a 0.522 name-only null, and
    misfile flagging 0.194 against a 0.175 base.
    """
    import numpy as np

    defs: dict[str, dict[str, str]] = {}
    for pack, path in PROMPTS.items():
        anchors = parse_anchors(path)
        defs[pack] = {f: f + ". " + " ".join(ph) for f, ph in anchors.items()}

    flags = []
    cache: dict[str, dict] = {}
    for pack in defs:
        names = sorted(defs[pack])
        vecs = enc.encode([defs[pack][n] for n in names],
                          normalize_embeddings=True, show_progress_bar=False)
        cache[pack] = {"names": names, "vecs": np.asarray(vecs)}

    for pack in {r["pack"] for r in rows}:
        subset = [r for r in rows if r["pack"] == pack]
        if pack not in cache or not subset:
            continue
        rv = np.asarray(enc.encode([r["rationale"] for r in subset],
                                   normalize_embeddings=True,
                                   show_progress_bar=False))
        sims = rv @ cache[pack]["vecs"].T
        names = cache[pack]["names"]
        for r, row in zip(subset, sims):
            best = names[int(row.argmax())]
            r["_flag"] = best != r["factor"]

    flags = [r.get("_flag", False) for r in rows]
    return _pr(flags, [r["misfiled"] for r in rows])


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()

    ok, why = available()
    if not ok:
        raise SystemExit(f"UNAVAILABLE: {why}")

    rows = load_rows(str(_ROOT / "tests/fixtures/extract_corpus/*/bundle_*"))
    base = sum(r["misfiled"] for r in rows) / len(rows)
    print("EXPLORATORY -- no criteria declared before this run. Not a finding.\n")
    print(f"rows {len(rows)}   bundles {len({r['bundle'] for r in rows})}   "
          f"misfile base rate {base:.3f}\n")

    enc = _encoder()
    results = {}
    print(f"{'second opinion':<34s} {'precision':>10s} {'recall':>8s} {'fired':>7s}")
    print(f"{'base rate (fire always)':<34s} {base:>10.3f} {1.0:>8.3f} {len(rows):>7d}")
    for label, fn in (
        ("MiniLM + logreg, unmasked", lambda: run_trained(rows, enc, False)),
        ("MiniLM + logreg, masked", lambda: run_trained(rows, enc, True)),
        ("MiniLM cosine to definitions", lambda: run_untrained(rows, enc)),
    ):
        p, r, fired = fn()
        results[label] = {"precision": p, "recall": r, "fired": fired}
        print(f"{label:<34s} {p:>10.3f} {r:>8.3f} {fired:>7d}")

    print("\n  for reference, Phase 4's TF-IDF figures on the same rows:")
    print("    K6 trained, masked             0.247   (recall 0.200)")
    print("    prompt anchors                 0.194   (recall 0.533)")
    print("\n  Exploratory. No number here may be cited as a result, promoted "
          "\n  into a study conclusion, or compared to a gated figure as though "
          "\n  it were one. To have any of it, declare criteria and re-run.")

    if args.out:
        args.out.write_text(json.dumps(
            {"exploratory": True, "criteria_declared": False,
             "rows": len(rows), "base_rate": base, "encoder": ENCODER,
             "results": results}, indent=1) + "\n")
        print(f"\n  wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

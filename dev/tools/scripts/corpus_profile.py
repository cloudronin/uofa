#!/usr/bin/env python3
"""The acceptance gate: does a generated corpus look like the real one?

A corpus is not usable until its profile matches the five real papers. This
consolidates checks that were scattered across throwaway scripts and gives them
one exit code.

Two things make this gate different from "is the prose realistic":

## It fails corpora that are too CLEAN, not just too fake

The previous synthetic corpus inverted the ranking between two methods, and it
did so by being tidy -- one model per bundle, thirteen clean findings, no tables,
no PDF layout. Prose realism was never the problem. So the bands below are
two-sided: annotator agreement ABOVE its band fails, because papers everyone
agrees about are papers that are not testing the hard judgement.

## It checks the papers differ from each other

Every other measure asks whether a paper resembles a real one. Forty identical
papers pass all of them and give an effective sample of one. The diversity floor
is calibrated on the five real papers rather than chosen:

    mean pairwise TF-IDF cosine   0.258
    max pair                      0.404   (opensim/elemance -- same group,
                                           same EVA injury scenario)

An earlier draft of the plan proposed failing above 0.60 mean / 0.85 max. That
would have passed a corpus more than twice as homogeneous as reality, which is
the exact failure the floor exists to catch. Measure the target, do not pick it.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(_ROOT / "dev" / "tools" / "scripts"))
sys.path.insert(0, str(_ROOT / "src"))

from document_furniture import strip_furniture  # noqa: E402
from keyless_k2_extractive import sentences  # noqa: E402
from uofa_cli import excel_constants as ec  # noqa: E402
from uofa_cli.readers.pdf_reader import _find_gutter, read_pdf  # noqa: E402

NAMES = tuple({n.lower() for n in ec.VV40_FACTOR_NAMES})

# A paper this close to another is not a second sample. Fixed, not scaled: the
# threshold asks "is this the same paper reworded", which does not depend on how
# many papers were drawn. Margin is wide -- the closest genuine pair anywhere in
# this project is 0.404 (opensim/elemance, same group and scenario) and the
# closest old-synthetic pair is 0.391 across 87 template-generated papers.
_TWIN = 0.60

REAL = {
    "bologna": "extract_corpus_vv40/bundle_bologna_bcthip",
    "nagaraja": "extract_corpus_vv40/bundle_nagaraja",
    "morrison": "extract_corpus_vv40/bundle_morrison",
    "opensim": "extract_corpus_real/bundle_real_opensim_knee",
    "elemance": "extract_corpus_real/bundle_real_elemance_thoracic",
}

# Every target is a measurement of the five real papers, not a choice.
# (low, high) -- None means unbounded on that side.
BANDS: dict[str, tuple[float | None, float | None, str]] = {
    "sentence_like":      (0.36, 0.56, "real 0.46"),
    "furniture_kept":     (0.25, 0.45, "real 0.35"),
    "run_together":       (None, 0.005, "real ~0.0005; >0.005 means a reader bug"),
    "two_col_pages":      (0.60, None, "real 0.75-1.00 for 2-col papers"),
    "hyphen_lines":       (0.02, None, "real 0.007-0.083"),
    # Two-sided, and the high side is the point: agreement above the band means
    # the papers are too clean. The seeded pilot scored 1.000 on selection.
    "agree_selection":    (0.85, 0.95, "real 0.920"),
    "agree_same_sentence": (0.60, 0.85, "real 0.714"),
    "na_rate":            (0.0, 0.0, "real exactly 0 -- the checklist constant "
                                     "must stay unbeatable; that is correct"),
    # Capped at _DIVERSITY_CAP words, and the two size-sensitive rows are scaled
    # by _DRIFT before comparison. Bases are the n=5 real measurements plus ~12%.
    #
    # The mean is the size-stable gate but it is BLIND TO DUPLICATION: hiding
    # three exact twins among thirty papers moved it 0.162 -> 0.166, while the
    # nearest-neighbour mean moved 0.278 -> 0.421 and max pair pinned to 1.000.
    # A corpus of three papers repeated thirteen times scores mean-NN 1.000. That
    # is the "forty samples or three repeated" question the checkpoint exists to
    # answer, and only the last two rows can answer it.
    "diversity_mean":     (None, 0.18, "real 0.141 -- size-stable, blind to twins"),
    "diversity_max":      (None, 0.29, "real 0.261 at n=5, scaled by n"),
    "diversity_nn":       (None, 0.24, "real 0.213 at n=5, scaled by n"),
    # The one gate that is neither dilutable nor size-dependent.
    "twins":              (0.0, 0.0, f"papers with a neighbour >= {_TWIN}; "
                                     "must be 0 -- a twin is not a sample"),
    # Length and vocabulary breadth. These reject the old corpus on their own and
    # cost nothing: it ran 1,341 words and 513 distinct types per document
    # against the real 10,998 and 1,702. A short paper cannot carry R7's
    # requirement that evidence sit >=100 sentences from where its factor is
    # named, so this is a precondition for the corpus, not a cosmetic match.
    "words":              (5000, None, "real 6,479-16,297; old synth 1,341"),
    "vocab_types":        (1200, None, "real median 1,702; old synth 513"),
}

HYPH = re.compile(r"[A-Za-z]{2,}-\s*$")

# Diversity is measured on the first N words of each document, not the whole of
# it, because full-text TF-IDF cosine reads LENGTH as much as sameness. Measured
# on the two corpora that matter:
#
#     sample            five real papers    old synthetic (known bad)
#     full text              0.258                 0.216   <- old looks BETTER
#     first 3000 words       0.195                 0.216
#     first 1500 words       0.141                 0.202   <- correct ordering
#
# Uncapped, the gate passed the corpus that inverted the K6/K4 ranking and rated
# forty template-generated papers as more varied than five different devices
# under two standards. Longer documents share more terms, so the real papers were
# penalised for being 8x longer (median 10,998 words against 1,341). At a fixed
# sample the old corpus is 43% more self-similar, which is the true relation.
_DIVERSITY_CAP = 1500

# Two of the three diversity measures grow with corpus size on their own. Drawing
# repeatedly from ONE generator (87 old-synthetic papers, 200 subsamples each):
#
#     n       mean pair   max pair   mean NN
#     5         0.137       0.229      0.192
#     10        0.138       0.276      0.222
#     40        0.138       0.365      0.268
#     87        0.138       0.391      0.289
#
# The generator never changed, so every movement is sample size. `mean pair` is
# flat and can be gated on a fixed number; `max pair` gains 59% and `mean NN` 40%
# between n=5 and n=40. A ceiling calibrated on the five real papers would
# therefore have FAILED a 40-paper corpus exactly as diverse as they are -- a
# spurious failure that would have been read as the generator collapsing.
#
# So those two thresholds scale by the measured drift, relative to the n=5 point
# where the real-paper calibration was taken.
_DRIFT = {5: (1.000, 1.000), 10: (1.205, 1.156), 20: (1.393, 1.292),
          40: (1.594, 1.396), 87: (1.707, 1.505)}



def _drift(n: int, which: int) -> float:
    """Size adjustment for max-pair (which=0) or mean-NN (which=1), log-interpolated."""
    import math
    ks = sorted(_DRIFT)
    if n <= ks[0]:
        return _DRIFT[ks[0]][which]
    if n >= ks[-1]:
        return _DRIFT[ks[-1]][which]
    hi = next(k for k in ks if k >= n)
    lo = max(k for k in ks if k <= n)
    if lo == hi:
        return _DRIFT[lo][which]
    f = (math.log(n) - math.log(lo)) / (math.log(hi) - math.log(lo))
    return _DRIFT[lo][which] + f * (_DRIFT[hi][which] - _DRIFT[lo][which])


def _docs(corpus: pathlib.Path) -> dict[str, pathlib.Path]:
    # rglob, not glob: the old corpus nests bundles under dev/ and test/.
    return {b.name: b / "source" for b in sorted(corpus.rglob("bundle_*"))
            if (b / "source").is_dir()}


def _text(src: pathlib.Path) -> str:
    """Document text. Falls back to markdown so the OLD corpus can be measured.

    The corpus that inverted the K6/K4 ranking is markdown -- `source/report.md`,
    no PDF at all. Reading it here is deliberate: a gate that crashes on the
    known-bad input has not rejected it. With no PDF the layout rows measure 0
    and fail, which is the correct verdict rather than an error.
    """
    pdfs = sorted(src.glob("*.pdf"))
    if pdfs:
        return "\n".join(c.text for p in pdfs for c in read_pdf(p))
    return "\n".join(f.read_text(errors="replace")
                     for f in sorted(src.iterdir())
                     if f.suffix.lower() in (".md", ".txt"))


def measure(docs: dict[str, pathlib.Path]) -> dict:
    """Every per-document measure the gate needs, plus corpus-level diversity."""
    import pdfplumber

    per, texts = {}, []
    for name, src in docs.items():
        t = _text(src)
        texts.append(t)
        ss = sentences(t)
        kept, _, reasons = strip_furniture(ss, NAMES)
        toks = re.findall(r"[A-Za-z-]+", t)
        pages = split = lines = hy = 0
        for f in sorted(src.glob("*.pdf")):
            with pdfplumber.open(f) as pdf:
                for pg in pdf.pages:
                    pages += 1
                    try:
                        if _find_gutter(pg.extract_words(), pg.bbox[0], pg.bbox[2]) is not None:
                            split += 1
                    except Exception:  # noqa: BLE001 -- malformed page
                        pass
                    ls = [x for x in (pg.extract_text(x_tolerance=1.2) or "").split("\n")
                          if x.strip()]
                    lines += len(ls)
                    hy += sum(1 for x in ls if HYPH.search(x))
        if not pages:  # markdown: count its real lines rather than reporting 0/1
            ls = [x for x in t.split("\n") if x.strip()]
            lines, hy = len(ls), sum(1 for x in ls if HYPH.search(x))
        per[name] = {
            "sentence_like": sum(1 for x in ss if len(x.split()) >= 6 and x[:1].isupper())
                             / max(len(ss), 1),
            "furniture_kept": len(kept) / max(len(ss), 1),
            "run_together": sum(1 for w in toks if len(w) > 20) / max(len(toks), 1),
            "two_col_pages": split / max(pages, 1),
            "hyphen_lines": hy / max(lines, 1),
            "rubric_sents": reasons.get("rubric-definition", 0) + reasons.get("rubric", 0),
            "sentences": len(ss),
            "words": len(t.split()),
            "vocab_types": len(set(re.findall(r"[a-z]{3,}", t.lower()))),
        }

    out = {"per_document": per}
    if len(texts) >= 2:
        out.update(diversity(texts, list(docs)))
    return out


def diversity(texts: list[str], names: list[str] | None = None) -> dict:
    """Mean pairwise, max pairwise, and mean nearest-neighbour TF-IDF cosine.

    Three numbers because no one of them is sufficient. The mean is the only one
    that does not move with corpus size, and it cannot see duplication; the
    nearest-neighbour mean sees duplication and does move with size. Both are
    reported, and the two size-sensitive ones are compared against a scaled
    threshold -- see _DRIFT.
    """
    from sklearn.feature_extraction.text import TfidfVectorizer

    names = names or [str(i) for i in range(len(texts))]
    capped = [" ".join(t.split()[:_DIVERSITY_CAP]) for t in texts]
    X = TfidfVectorizer(stop_words="english", max_features=20000,
                        sublinear_tf=True).fit_transform(capped)
    S = (X @ X.T).toarray()
    for i in range(len(texts)):
        S[i][i] = -1.0
    pairs = [(i, j) for i in range(len(texts)) for j in range(i + 1, len(texts))]
    off = [S[i][j] for i, j in pairs]
    i, j = max(pairs, key=lambda p: S[p[0]][p[1]])
    nn = [max(row) for row in S]
    return {"diversity_mean": sum(off) / len(off),
            "diversity_max": max(off),
            "diversity_nn": sum(nn) / len(texts),
            # The duplication gate. A COUNT, not a mean, because a mean dilutes:
            # three twins hidden among thirty papers lifted the nearest-neighbour
            # mean by less than its own threshold and passed. Six papers out of
            # thirty being duplicates is not a small deviation in an average, it
            # is six papers that are not samples -- so count them.
            "twins": sum(1 for v in nn if v >= _TWIN),
            "twin_names": [names[k] for k, v in enumerate(nn) if v >= _TWIN][:8],
            "closest_pair": (names[i], names[j], float(S[i][j]))}


_SCALED = {"diversity_max": 0, "diversity_nn": 1}


def _verdict(key: str, value: float, n: int = 5) -> tuple[bool, str]:
    lo, hi, note = BANDS[key]
    if key in _SCALED and hi is not None:
        r = _drift(n, _SCALED[key])
        hi *= r
        note = f"{note} [x{r:.2f} @ n={n}]"
    ok = (lo is None or value >= lo - 1e-9) and (hi is None or value <= hi + 1e-9)
    band = f"[{'' if lo is None else f'{lo:.3f}'}, {'' if hi is None else f'{hi:.3f}'}]"
    return ok, f"{band:18s} {note}"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--corpus", type=pathlib.Path,
                    help="generated corpus root (contains bundle_*/source/*.pdf)")
    ap.add_argument("--corpus-real", action="store_true",
                    help="profile the five real papers instead, to calibrate")
    ap.add_argument("--diversity-only", action="store_true")
    ap.add_argument("--json", type=pathlib.Path, default=None)
    args = ap.parse_args()

    if args.corpus_real:
        docs = {k: _ROOT / "tests" / "fixtures" / v / "source" for k, v in REAL.items()}
        label = "five real papers"
    elif args.corpus:
        docs = _docs(args.corpus)
        label = str(args.corpus)
    else:
        raise SystemExit("give --corpus or --corpus-real")
    if not docs:
        raise SystemExit(f"no bundles with a source/ directory under {label}")

    m = measure(docs)
    print(f"\ncorpus profile — {label}  ({len(docs)} documents)\n")

    if not args.diversity_only:
        ratios = ("sentence_like", "furniture_kept", "run_together",
                  "two_col_pages", "hyphen_lines")
        counts = ("words", "vocab_types")
        head = "".join(f"{k[:12]:>14s}" for k in ratios) + f"{'rubric':>8s}"
        print(f"  {'document':22s}{head}" + "".join(f"{k[:11]:>13s}" for k in counts))
        for name, d in m["per_document"].items():
            print(f"  {name[:22]:22s}" + "".join(f"{d[k]:>14.3f}" for k in ratios)
                  + f"{d['rubric_sents']:>8d}"
                  + "".join(f"{d[k]:>13,d}" for k in counts))
        print()
        fails = []
        for k in ratios + counts:
            vals = [d[k] for d in m["per_document"].values()]
            mean = sum(vals) / len(vals)
            ok, note = _verdict(k, mean)
            fails += [] if ok else [k]
            shown = f"{mean:6.3f}" if k in ratios else f"{mean:6,.0f}"
            print(f"  {'PASS' if ok else 'FAIL'}  {k:20s} mean {shown}   {note}")
    else:
        fails = []

    if "diversity_mean" in m:
        print()
        for k in ("diversity_mean", "diversity_max", "diversity_nn", "twins"):
            ok, note = _verdict(k, m[k], len(docs))
            fails += [] if ok else [k]
            shown = f"{m[k]:6.3f}" if k != "twins" else f"{m[k]:6d}"
            print(f"  {'PASS' if ok else 'FAIL'}  {k:20s}      {shown}   {note}")
        a, b, s = m["closest_pair"]
        print(f"        closest pair: {a} / {b} = {s:.3f}")
        if m["twins"]:
            print(f"        twinned: {', '.join(m['twin_names'])}")
    else:
        print("\n  diversity not computed: needs >= 2 documents")

    print("\n  Not measured here (needs API calls, see d1_annotator_agreement.py):")
    print("    agree_selection      band [0.85, 0.95]  real 0.920 -- ABOVE the band")
    print("                         means the papers are too clean")
    print("    agree_same_sentence  band [0.60, 0.85]  real 0.714")
    print("    na_rate              must be exactly 0")
    print("  A corpus is not accepted until those three are run cross-family.")

    if args.json:
        args.json.write_text(json.dumps(m, indent=2, default=float) + "\n")
    if fails:
        print(f"\n  OUT OF TOLERANCE: {fails}")
        return 1
    print("\n  All measured rows within tolerance.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

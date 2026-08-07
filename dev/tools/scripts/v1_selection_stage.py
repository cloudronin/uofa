#!/usr/bin/env python3
"""The hybrid: keyless routes to 20 sentences, a model picks one.

K6 on real documents routes at recall@20 = 0.500 against random 0.123
(p=0.0017, 12 factor-document pairs) and picks at 0.000. It knows the
neighbourhood and cannot pick the house. This tests whether a model can pick,
given only the neighbourhood.

That is the whole economic claim of the hybrid. Reading 20 sentences instead of
539 (opensim) or 1326 (elemance) is a 27-66x reduction in what the paid stage
sees, and if selection accuracy is high the pipeline costs almost nothing per
document while remaining a model-quality extractor.

## What the ceiling is, and why it is reported

The model cannot find a sentence the router did not hand it. So selection is
scored twice:

  * **of those reachable** -- the 6 of 12 pairs where a gold sentence is
    actually in the top 20. This measures the selector alone.
  * **end to end** -- all 12 pairs, which is what the pipeline would deliver
    and is capped at the router's recall@20 of 0.500.

Reporting only the first would be the same error as scoring a detector without
its null model: it flatters the stage by hiding the constraint it operates
under.

## Controls

A model given 20 sentences and asked to choose one has a 1-in-20 floor, but the
real floor is higher because the shortlist is ranked -- always answering "the
first one" is a free strategy. Both are reported.
"""
from __future__ import annotations

import json
import os
import pathlib
import random
import re
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
K = 20
NAMES = tuple({n.lower() for n in ec.NASA_ALL_FACTOR_NAMES}
              | {k.lower() for k in DECOMPOSED_7009A})
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

PROMPT = """\
You are reading an engineering credibility assessment report.

{scope}Below are {n} numbered candidate sentences taken from it, in no meaningful
order. Exactly one question: which single sentence is the best evidence a
reviewer would cite for the credibility factor "{factor}"?

The best evidence STATES A FINDING about the model and scenario named above --
what was done, what was found, or what score was assigned and why. It is not a
heading, not a row of a scoring table, and not the standard's definition of the
factor.

These reports assess SEVERAL models across SEVERAL injury mechanisms, and the
same factor is scored separately for each. A sentence giving a score for a
different model or a different mechanism is the wrong answer, however well it
matches the factor name.

If none of them is evidence for that factor, answer 0.

Answer with the number alone, nothing else.

{candidates}
"""


def norm(s: str) -> str:
    return " ".join(str(s).split()).lower()


def main() -> int:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_union

    from uofa_cli.llm.backend import GenerationOptions
    from uofa_cli.llm.litellm_backend import LiteLLMBackend

    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise SystemExit("ANTHROPIC_API_KEY not set")
    backend = LiteLLMBackend(backend_name="anthropic",
                             model_name="claude-sonnet-4-6",
                             api_key=key, default_timeout_seconds=120)

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

    cases = []
    for tag, bundle, annot in DOCS:
        src = _ROOT / "tests" / "fixtures" / "extract_corpus_real" / bundle / "source"
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
        prov = json.loads((_ROOT / "tests" / "fixtures" / "extract_corpus_real"
                           / bundle / "ground_truth.json").read_text()).get("_provenance", {})
        bits = [f"model: {prov[k]}" for k in ("model",) if prov.get(k)]
        bits += [f"injury mechanism: {prov[k]}" for k in ("injury_mechanism",) if prov.get(k)]
        bits += [f"scenario: {prov[k]}" for k in ("scenario",) if prov.get(k)]
        scope = ("This assessment is specifically of -- " + "; ".join(bits) + ".\n\n") if bits else ""

        ann = json.loads((_ROOT / "docs" / "v1" / annot).read_text())
        gold: dict[str, set[int]] = {}
        for a in ann["annotations"]:
            pub = ANNOT_TO_PUBLISHED.get(a["factor_type"].strip().lower())
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
        _, pool, _ = strip_furniture(sents, NAMES)
        P = clf.predict_proba(feats.transform([sents[i] for i in pool]))
        for pub, cons in DECOMPOSED_7009A.items():
            cols = [cls[c] for c in cons if c in cls]
            if not cols or pub not in gold:
                continue
            order = sorted(range(len(pool)), key=lambda k: -max(P[k][c] for c in cols))
            shortlist = [pool[k] for k in order[:K]]
            cases.append({"doc": tag, "factor": pub, "shortlist": shortlist,
                          "gold": gold[pub], "sents": sents, "scope": scope})

    print(f"\nSelection stage — sonnet choosing 1 of {K} routed sentences\n")
    print(f"  {len(cases)} factor-document pairs\n")

    rng = random.Random(0)
    reachable = sum(bool(set(c["shortlist"]) & c["gold"]) for c in cases)
    sel_ok = sel_ok_reachable = 0
    first_ok = first_ok_reachable = 0

    for c in cases:
        cand = "\n".join(f"{i + 1}. {c['sents'][s]}"
                         for i, s in enumerate(c["shortlist"]))
        raw = backend.generate(
            PROMPT.format(n=len(c["shortlist"]), factor=c["factor"],
                          candidates=cand, scope=c["scope"]),
            GenerationOptions(temperature=0.0, max_tokens=16))
        m = re.search(r"\d+", raw or "")
        pick = int(m.group(0)) if m else 0
        chosen = c["shortlist"][pick - 1] if 1 <= pick <= len(c["shortlist"]) else None
        hit = chosen in c["gold"]
        can = bool(set(c["shortlist"]) & c["gold"])
        sel_ok += hit
        sel_ok_reachable += hit and can
        # "always take rank 1" -- free, and the baseline a ranked list creates
        firsth = c["shortlist"][0] in c["gold"]
        first_ok += firsth
        first_ok_reachable += firsth and can
        print(f"  {'HIT ' if hit else 'miss'} {c['doc']:9s} {c['factor']:30s} "
              f"picked {pick:>2}{'  (gold in list)' if can else '  (gold NOT in list)'}")

    n = len(cases)
    print(f"\n  {'measure':38s} {'score':>7s}")
    print(f"  {'router recall@20 (the ceiling)':38s} {reachable / n:>7.3f}  ({reachable}/{n})")
    print(f"  {'sonnet selection, end to end':38s} {sel_ok / n:>7.3f}  ({sel_ok}/{n})")
    if reachable:
        print(f"  {'sonnet selection, of those reachable':38s} "
              f"{sel_ok_reachable / reachable:>7.3f}  ({sel_ok_reachable}/{reachable})")
    print(f"  {'control: always take rank 1':38s} {first_ok / n:>7.3f}  ({first_ok}/{n})")
    print(f"  {'control: uniform 1-of-20':38s} "
          f"{sum(rng.randrange(K) == 0 for _ in range(2000)) / 2000 * (reachable / n):>7.3f}")
    print(f"\n  Two documents, one annotator. End to end is the number the")
    print(f"  pipeline delivers; 'of those reachable' measures the selector alone.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

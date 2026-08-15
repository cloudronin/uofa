#!/usr/bin/env python3
"""The real-document re-score the H2 replacement gate is declared against.

Thresholds were committed first, in
`docs/decisions/2026-08-14-h2-replacement-thresholds.md`. This runs against
them; it does not set them.

## The first version of this script was circular, and the declared gate caught it

It scored the annotation's own evidence text against gold sentence sets derived
from that same annotation text -- "does this text localise to the sentence
containing this text". It returned **0.8545**, with three of six papers at
exactly 1.000.

That is above the 0.714 real-document inter-annotator agreement ceiling, which
is condition 3 of the declared gate, and condition 3 exists precisely because a
figure above the ceiling is unreachable by a perfect extractor and therefore
evidence of a broken measurement rather than a good result. **It fired on the
first run, on its first real use.**

The candidate must be an **extraction**, not the annotation. This version runs
the shipped extractor over each paper's source PDFs and scores its rationales
against the human annotation's sentence sets. The reference and the candidate
then come from different processes, which is the whole point.

Usage:

    PYTHONPATH=src python dev/tools/scripts/real_document_rescore.py
"""
from __future__ import annotations

import argparse
import json
import random
import statistics
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(_ROOT / "dev" / "tools" / "scripts"))
sys.path.insert(0, str(_ROOT / "src"))

sys.path.insert(0, str(_ROOT / "tests" / "fixtures" / "extract_corpus_real"))

from cas_mapping import VARIANTS  # noqa: E402
from groundedness import _tokens, locate_sentence  # noqa: E402
from uofa_cli import excel_constants as ec  # noqa: E402
from v1_router_comparison import DOCS, load_case  # noqa: E402

# Declared in docs/decisions/2026-08-14-h2-replacement-thresholds.md
MARGIN_FLOOR = 0.25
SD_FLOOR = 3.0
AGREEMENT_CEILING = 0.714          # REAL documents. Not the synthetic 0.913.


def _shotgun(sents: list[str], k: int, seed: int = 0) -> str:
    rng = random.Random(seed)
    return " ".join(rng.sample(sents, min(k, len(sents))))


CONFIG = None       # built lazily so --help works without a key


def _config():
    from uofa_cli.llm.config import LLMConfig
    return LLMConfig(backend="openai-compatible",
                     model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
                     base_url="https://api.together.xyz/v1",
                     api_key_env="UOFA_OPENAI_COMPATIBLE_API_KEY")


def _extract_rationales(bundle: str, pack: str) -> dict[str, str]:
    """Run the shipped extractor over the paper. factor -> rationale."""
    from uofa_cli.document_reader import read_corpus
    from uofa_cli.llm_extractor import extract

    base = (_ROOT / "tests" / "fixtures" / bundle if "/" in bundle
            else _ROOT / "tests" / "fixtures" / "extract_corpus_real" / bundle)
    src = base / "source"
    paths = sorted(p for p in src.iterdir() if p.is_file() and not p.name.startswith("."))
    result = extract(read_corpus(paths), "unused", pack, llm_config=_config())
    out = {}
    for f in result.credibility_factors:
        name = getattr(f.get("factor_type"), "value", None)
        rat = getattr(f.get("rationale"), "value", None)
        if name and isinstance(rat, str) and rat.strip():
            out[name] = rat
    return out


def score_case(tag: str, bundle: str, annot: str) -> dict:
    """The extractor's rationales against the human annotation's sentences.

    Candidate and reference come from different processes. That is what the
    circular first version lacked.

    ## The published-to-pack mapping, and why it is a repair not a change

    Three of the six papers carry a `cas_variant`, and `load_case` keys their
    gold by the **published** factor vocabulary -- `Code/solution verification`,
    `Input pedigree`, `Referent validation`. The extractor emits **pack** factor
    names. Without the mapping no extraction can match those keys and all three
    papers score n=0, which is what the first extraction-based run did.

    `cas_mapping.VARIANTS` maps published -> pack constituents, and
    `v1_router_comparison` already applies it for exactly this reason. Wiring it
    here is defined entirely by pre-existing gold structure.

    A published factor counts as hit when **any** of its pack constituents'
    rationales localises into that factor's gold sentences. `Verification` has
    four constituents, so a rolled-up factor gets four attempts where a
    one-to-one factor gets one. Recorded rather than corrected: it is how
    `v1_router_comparison` scores the same structure, and changing it here would
    make the two incomparable.
    """
    sents, pool, gold, variant = load_case(tag, bundle, annot)
    stoks = [_tokens(s) for s in sents]

    # Variant papers are 7009A/7009B-flavoured and their gold includes NASA-only
    # factors (Data pedigree, Results robustness, Results uncertainty) that a
    # V&V 40 extraction cannot produce at all.
    pack = "vv40" if variant is None else "nasa-7009b"
    table = ({f: [f] for f in ec.VV40_FACTOR_NAMES} if variant is None
             else VARIANTS[variant])

    rationales = _extract_rationales(bundle, pack)

    right = scored = 0
    for pub, idxs in gold.items():
        cons = table.get(pub, [pub])
        texts = [rationales[c] for c in cons if c in rationales]
        if not texts:
            continue
        scored += 1
        if any((lambda pr: pr is not None and pr in idxs)(
                locate_sentence(t_, sents, stoks)) for t_ in texts):
            right += 1

    nulls = {}
    names = sorted(gold)
    for label, maker in (
        ("first_sentence", lambda: [sents[0]] * len(names) if sents else []),
        ("document_order", lambda: [sents[i % len(sents)] for i in range(len(names))]),
        ("shotgun_k5", lambda: [_shotgun(sents, 5)] * len(names)),
        ("shotgun_k12", lambda: [_shotgun(sents, 12)] * len(names)),
        ("shotgun_k20", lambda: [_shotgun(sents, 20)] * len(names)),
    ):
        rows = maker()
        if not rows:
            continue
        r = n = 0
        for name, txt in zip(names, rows):
            n += 1
            pred = locate_sentence(txt, sents, stoks)
            if pred is not None and pred in gold[name]:
                r += 1
        nulls[label] = r / n if n else 0.0

    # Permutation null: the EXTRACTOR's rationales, reassigned at random.
    perm = []
    scorable = [pub for pub in sorted(gold)
                if any(c in rationales for c in table.get(pub, [pub]))]
    texts_pool = [next(rationales[c] for c in table.get(pub, [pub]) if c in rationales)
                  for pub in scorable]
    if len(texts_pool) >= 2:
        rng = random.Random(0)
        for _ in range(200):
            sh = texts_pool[:]
            rng.shuffle(sh)
            r = n = 0
            for pub, txt in zip(scorable, sh):
                n += 1
                pred = locate_sentence(txt, sents, stoks)
                if pred is not None and pred in gold[pub]:
                    r += 1
            if n:
                perm.append(r / n)

    return {"tag": tag, "variant": variant, "pack": pack, "sentences": len(sents),
            "right": right, "scored": scored,
            "extracted_factors": len(rationales),
            "rate": right / scored if scored else 0.0,
            "nulls": nulls,
            "perm_mean": statistics.mean(perm) if perm else 0.0,
            "perm_sd": statistics.pstdev(perm) if len(perm) > 1 else 0.0}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()

    rows = [score_case(*d) for d in DOCS]
    tot_r = sum(r["right"] for r in rows)
    tot_s = sum(r["scored"] for r in rows)
    rate = tot_r / tot_s if tot_s else 0.0

    print(f"{'case':<12s} {'sents':>6s} {'rate':>8s} {'n':>4s}  "
          f"{'perm':>7s} {'k20':>7s}")
    for r in rows:
        print(f"{r['tag']:<12s} {r['sentences']:>6d} {r['rate']:>8.3f} "
              f"{r['scored']:>4d}  {r['perm_mean']:>7.3f} "
              f"{r['nulls'].get('shotgun_k20', 0):>7.3f}")

    perm_mean = statistics.mean([r["perm_mean"] for r in rows])
    perm_sd = statistics.mean([r["perm_sd"] for r in rows if r["perm_sd"]] or [0])
    worst = max((max(r["nulls"].values()) for r in rows if r["nulls"]), default=0.0)
    margin = rate - perm_mean
    sd_above = margin / perm_sd if perm_sd else float("inf")

    print(f"\n  REAL-DOCUMENT CANDIDATE   {rate:.4f}   ({tot_r}/{tot_s})")
    print(f"  permutation null          {perm_mean:.4f}  (sd {perm_sd:.4f})")
    print(f"  worst null, any length    {worst:.4f}")
    print(f"  agreement ceiling         {AGREEMENT_CEILING:.3f}  (REAL, not the "
          f"synthetic 0.913)")

    print(f"\n  {'condition':<44s} {'result':>10s}")
    c1 = margin >= MARGIN_FLOOR and sd_above >= SD_FLOOR
    print(f"  {'1. margin >= 0.25 and >= 3 sd':<44s} "
          f"{f'{margin:+.3f} / {sd_above:.1f}sd':>10s}  {'PASS' if c1 else 'FAIL'}")
    c2 = worst < rate
    print(f"  {'2. no null reaches the candidate':<44s} "
          f"{worst:>10.3f}  {'PASS' if c2 else 'FAIL'}")
    c3 = rate <= AGREEMENT_CEILING
    print(f"  {'3. stated against the 0.714 ceiling':<44s} "
          f"{rate:>10.3f}  {'below ceiling' if c3 else 'ABOVE CEILING -- suspect'}")
    print(f"  {'4. measured on the real corpus':<44s} {'yes':>10s}  PASS")

    if args.out:
        args.out.write_text(json.dumps(
            {"rate": rate, "right": tot_r, "scored": tot_s,
             "perm_mean": perm_mean, "perm_sd": perm_sd, "worst_null": worst,
             "per_case": rows}, indent=1) + "\n")
        print(f"\n  wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

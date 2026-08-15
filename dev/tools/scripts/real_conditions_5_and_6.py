#!/usr/bin/env python3
"""Conditions 5 and 6 of the H2 replacement gate, on the real corpus.

`real_document_rescore.py` measured conditions 1-4. Two were left unmeasured on
real documents and satisfied only on synthetic:

    5. FP/FN rates from the disagreement adjudication, published beside it
    6. groundedness as the triple, never a lone number

Condition 1 already failed, so the conjunction is settled either way. These are
run because a conjunction reported as "failed on one condition" while two others
were never measured is not the same claim as one measured throughout, and the
difference is exactly the kind a reader is entitled to.

Extractions are computed once and reused for both, so this costs one pass over
the six papers rather than two.

Usage:

    UOFA_OPENAI_COMPATIBLE_API_KEY=... PYTHONPATH=src \\
      python dev/tools/scripts/real_conditions_5_and_6.py
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(_ROOT / "dev" / "tools" / "scripts"))
sys.path.insert(0, str(_ROOT / "src"))
sys.path.insert(0, str(_ROOT / "tests" / "fixtures" / "extract_corpus_real"))

from cas_mapping import VARIANTS  # noqa: E402
from groundedness import (  # noqa: E402
    GroundednessResult,
    _matches,
    _tokens,
    locate_sentence,
    score_factor_rationales,
)
from real_document_rescore import _extract_rationales  # noqa: E402
from uofa_cli import excel_constants as ec  # noqa: E402
from uofa_cli.readers.pdf_reader import read_pdf  # noqa: E402
from v1_router_comparison import DOCS, load_case  # noqa: E402


def _source_text(bundle: str) -> str:
    base = (_ROOT / "tests" / "fixtures" / bundle if "/" in bundle
            else _ROOT / "tests" / "fixtures" / "extract_corpus_real" / bundle)
    return "\n".join(c.text for p in sorted((base / "source").glob("*.pdf"))
                     for c in read_pdf(p))


def run(tag: str, bundle: str, annot: str) -> dict:
    sents, _pool, gold, variant = load_case(tag, bundle, annot)
    stoks = [_tokens(s) for s in sents]
    pack = "vv40" if variant is None else "nasa-7009b"
    table = ({f: [f] for f in ec.VV40_FACTOR_NAMES} if variant is None
             else VARIANTS[variant])

    rationales = _extract_rationales(bundle, pack)

    # ── condition 6: the groundedness triple ─────────────────
    factors = [{"factor_type": k, "rationale": v} for k, v in rationales.items()]
    g = score_factor_rationales(factors, _source_text(bundle))

    # ── condition 5: old rule vs new rule, adjudicated ───────
    # The old rule needs keyword references. The annotated sentences ARE the
    # reference, same construction real_attribution_reference.py uses.
    rows = []
    for pub, idxs in gold.items():
        cons = table.get(pub, [pub])
        texts = [(c, rationales[c]) for c in cons if c in rationales]
        if not texts:
            continue
        refs = [sents[i] for i in sorted(idxs)]
        old_ok = any(_matches(t, refs) for _c, t in texts)
        new_ok = any((lambda p: p is not None and p in idxs)(
            locate_sentence(t, sents, stoks)) for _c, t in texts)
        if old_ok != new_ok:
            # Adjudicate: does the sentence the new rule picked carry this
            # factor's reference text? If so the new rule found real evidence
            # and the old rule's keyword test missed it.
            picked = []
            for _c, t in texts:
                p = locate_sentence(t, sents, stoks)
                if p is not None:
                    picked.append(sents[p])
            new_found_real = any(_matches(pk, refs) for pk in picked)
            rows.append({"factor": pub, "old": old_ok, "new": new_ok,
                         "new_picked_real_evidence": new_found_real})
    return {"tag": tag, "pack": pack, "groundedness": g, "disagreements": rows,
            "n_factors": len(rationales)}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()

    results = [run(*d) for d in DOCS]

    # ── condition 6 ──────────────────────────────────────────
    agg = GroundednessResult()
    for r in results:
        for k in ("factors_total", "factors_with_rationale", "rationales_with_claims",
                  "claims_total", "claims_grounded", "factors_distinct"):
            setattr(agg, k, getattr(agg, k) + getattr(r["groundedness"], k))
        agg.ungrounded += r["groundedness"].ungrounded

    print("CONDITION 6 -- the groundedness triple, real corpus")
    print(f"  coverage       {agg.coverage:.3f}   "
          f"{agg.factors_with_rationale}/{agg.factors_total}")
    print(f"  claim_density  {agg.claim_density:.3f}   "
          f"{agg.rationales_with_claims}/{agg.factors_with_rationale}")
    print(f"  groundedness   {agg.groundedness:.3f}   "
          f"{agg.claims_grounded}/{agg.claims_total}")
    print(f"  distinctness   {agg.distinctness:.3f}")
    print(f"  ungrounded     {len(agg.ungrounded)}")
    print("\n  per paper:")
    for r in results:
        gg = r["groundedness"]
        print(f"    {r['tag']:<10s} cov {gg.coverage:.3f}  den {gg.claim_density:.3f}  "
              f"grd {gg.groundedness:.3f}  ({gg.claims_grounded}/{gg.claims_total} claims)")

    # ── condition 5 ──────────────────────────────────────────
    dis = [d for r in results for d in r["disagreements"]]
    old_only = [d for d in dis if d["old"] and not d["new"]]
    new_only = [d for d in dis if d["new"] and not d["old"]]
    gold_err = [d for d in old_only if d["new_picked_real_evidence"]]

    print("\nCONDITION 5 -- disagreement adjudication, real corpus")
    print(f"  disagreement rows          {len(dis)}")
    print(f"    old right / new wrong    {len(old_only)}")
    print(f"    old wrong / new right    {len(new_only)}")
    if old_only:
        print("  of the old-right/new-wrong rows:")
        print(f"    new rule DID find real evidence (gold-set gap)  "
              f"{len(gold_err)} ({len(gold_err)/len(old_only):.1%})")
        print(f"    localiser error                                 "
              f"{len(old_only) - len(gold_err)}")
    print(f"\n  FP rate (new rule fires where old does not): "
          f"{len(new_only)}/{len(dis) or 1} of disagreements")
    print(f"  FN rate (new rule misses where old does not): "
          f"{len(old_only)}/{len(dis) or 1} of disagreements")

    if args.out:
        args.out.write_text(json.dumps({
            "condition_6": agg.as_dict(),
            "condition_5": {"disagreements": len(dis), "old_only": len(old_only),
                            "new_only": len(new_only), "gold_set_gap": len(gold_err),
                            "rows": dis},
        }, indent=1) + "\n")
        print(f"\n  wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

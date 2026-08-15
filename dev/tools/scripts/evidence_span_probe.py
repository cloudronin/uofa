#!/usr/bin/env python3
"""Phase 2: does the `evidence_span` prompt field actually work?

The prompt now asks for one unbroken sentence, copied verbatim from the corpus,
separate from the rationale. This measures whether the model does it, against
kill criteria declared before the run.

## Why this reads the extraction and not the workbook

The Credibility Factors sheet has eight fixed columns and every reader indexes
them positionally. Adding a ninth is a schema change that touches the writer,
`parse_extracted_xlsx`, the import path and the goldens -- and it would be
wasted work, plus churned goldens, if the field turns out not to survive its
kill criteria.

So the field goes to the workbook only if it passes. Until then it is measured
where it already exists: `ExtractionResult.credibility_factors`, straight out of
`extract()`.

## Kill criteria, declared before running

    KILL if evidence_span is filled on < 70% of factor rows
    KILL if > 30% of filled spans are not verbatim substrings of the corpus
    KILL if mean_overall_f1 moves more than 0.004

The third is measured by the normal batch scorer with the new prompts, not here
-- F1 does not need the span. 0.004 is what the absence-rule change moved it,
so it is the noise floor this corpus has already demonstrated.

The second criterion is the one that matters most. A blank span says "no single
sentence covers this factor", which is honest and useful. An invented span says
a document contains words it does not contain, which is worse than the
unseparated rationale it was meant to replace.

Usage:

    UOFA_OPENAI_COMPATIBLE_API_KEY=... PYTHONPATH=src \\
      python dev/tools/scripts/evidence_span_probe.py --n 8
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(_ROOT / "dev" / "tools" / "scripts"))
sys.path.insert(0, str(_ROOT / "src"))

from uofa_cli.document_reader import read_corpus  # noqa: E402
from uofa_cli.llm.config import LLMConfig  # noqa: E402
from uofa_cli.llm_extractor import assemble_corpus_text, extract  # noqa: E402
from uofa_cli.segmentation import sentences  # noqa: E402

FILLED_FLOOR = 0.70
VERBATIM_FLOOR = 0.70          # i.e. at most 30% non-verbatim

CONFIG = LLMConfig(
    backend="openai-compatible",
    model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
    base_url="https://api.together.xyz/v1",
    api_key_env="UOFA_OPENAI_COMPATIBLE_API_KEY",
)


def _norm(s: str) -> str:
    """Whitespace and case only. Nothing that would let a paraphrase through."""
    return " ".join(str(s).split()).lower()


def _v(fe) -> str:
    val = getattr(fe, "value", fe)
    return "" if val is None else str(val)


def _tokens(s: str) -> set[str]:
    return set(re.findall(r"[a-z0-9.%-]{3,}", _norm(s)))


def _localises(span: str, sents: list[str], floor: float = 0.60) -> bool:
    """Does the span map to a source sentence by token overlap?

    The measurement Phase 3 actually needs, and it is not the same question as
    the verbatim check. A span with a parenthetical elided is not findable by
    exact search -- which is the product failure -- but still overlaps its
    source sentence almost completely, so sentence-index attribution would
    localise it correctly.

    Reported, not gating. It is a new measurement, and giving it a threshold
    after seeing arm 1 would be exactly the retroactive thresholding this
    project has been burned by. 0.60 is the reporting cut, not a criterion.
    """
    st = _tokens(span)
    if not st:
        return False
    return any(len(st & _tokens(s)) / len(st) >= floor for s in sents)


def probe(bundle: Path) -> dict:
    gt = json.loads((bundle / "ground_truth.json").read_text())
    paths = sorted(p for p in (bundle / "source").iterdir()
                   if p.is_file() and not p.name.startswith("."))
    corpus = read_corpus(paths)
    text = assemble_corpus_text(corpus)
    flat = _norm(text)
    sents = sentences(text)

    result = extract(corpus, "unused", gt["pack"], llm_config=CONFIG)

    rows = 0
    filled = 0
    verbatim = 0
    localised = 0
    invented: list[str] = []
    multi_sentence = 0
    for f in result.credibility_factors:
        rows += 1
        span = _v(f.get("evidence_span")).strip()
        if not span:
            continue
        filled += 1
        if _norm(span) in flat:
            verbatim += 1
        else:
            invented.append(span)
        if _localises(span, sents):
            localised += 1
        # "One unbroken sentence" -- a span with an interior sentence boundary
        # is stitched, which the prompt forbids for a reason: a stitched span
        # cannot be checked by reading one line of the document.
        if re.search(r"[.!?]\s+[A-Z]", span):
            multi_sentence += 1

    return {"bundle": bundle.name, "pack": gt["pack"], "rows": rows,
            "filled": filled, "verbatim": verbatim, "localised": localised,
            "multi_sentence": multi_sentence, "invented": invented}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--corpus", type=Path,
                    default=_ROOT / "tests" / "fixtures" / "extract_corpus" / "dev")
    ap.add_argument("--n", type=int, default=8)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()

    bundles = [b for b in sorted(args.corpus.glob("bundle_*"))
               if (b / "ground_truth.json").exists()][:args.n]

    rows = []
    for b in bundles:
        try:
            r = probe(b)
        except Exception as exc:                       # noqa: BLE001
            print(f"  {b.name}: FAILED {type(exc).__name__}: {exc}")
            continue
        rows.append(r)
        print(f"  {r['bundle']:<28s} {r['filled']:>3d}/{r['rows']:<3d} filled  "
              f"{r['verbatim']:>3d} verbatim  {r['localised']:>3d} localised  "
              f"{r['multi_sentence']:>2d} stitched")

    if not rows:
        raise SystemExit("no bundle produced a result; nothing to report")

    tot_rows = sum(r["rows"] for r in rows)
    tot_filled = sum(r["filled"] for r in rows)
    tot_verbatim = sum(r["verbatim"] for r in rows)
    tot_stitched = sum(r["multi_sentence"] for r in rows)
    tot_localised = sum(r["localised"] for r in rows)

    fill_rate = tot_filled / tot_rows if tot_rows else 0.0
    verb_rate = tot_verbatim / tot_filled if tot_filled else 0.0

    print(f"\n  bundles {len(rows)}   factor rows {tot_rows}")
    print(f"  filled          {tot_filled}/{tot_rows} = {fill_rate:.3f}   "
          f"{'PASS' if fill_rate >= FILLED_FLOOR else 'KILL'} (floor {FILLED_FLOOR})")
    print(f"  verbatim        {tot_verbatim}/{tot_filled} = {verb_rate:.3f}   "
          f"{'PASS' if verb_rate >= VERBATIM_FLOOR else 'KILL'} (floor {VERBATIM_FLOOR})")
    print(f"  stitched        {tot_stitched}/{tot_filled} "
          f"(spans containing an interior sentence boundary)")
    loc_rate = tot_localised / tot_filled if tot_filled else 0.0
    print(f"  localised       {tot_localised}/{tot_filled} = {loc_rate:.3f}   "
          f"REPORTED, NOT GATING -- the question Phase 3 needs answered")

    bad = [s for r in rows for s in r["invented"]][:5]
    if bad:
        print("\n  spans that are NOT verbatim in their corpus:")
        for s in bad:
            print(f"    {s[:110]!r}")

    print("\n  F1 movement is the third criterion and is not measured here -- it "
          "\n  comes from the batch scorer with the new prompts. Kill if it moves "
          "\n  more than 0.004.")

    if args.out:
        args.out.write_text(json.dumps(
            {"fill_rate": fill_rate, "verbatim_rate": verb_rate,
             "localised_rate": loc_rate, "rows": tot_rows, "filled": tot_filled,
             "verbatim": tot_verbatim, "localised": tot_localised,
             "stitched": tot_stitched, "per_bundle": rows}, indent=1) + "\n")
        print(f"\n  wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

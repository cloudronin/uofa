#!/usr/bin/env python3
"""Model or temperature? Four arms, identical prompts.

Runs against `studies/specificity-discriminator/DECLARATION.md`, which was
committed before this script existed. It does not set thresholds; it reports
against them.

The C3 migration changed the extraction model and the sampling temperature at
once, and they have never been separated. Prompt has been refuted twice
independently -- the pack split killed `"or implied"` (both packs collapsed,
only one carried the clause), and a prompt change aimed directly at claim
density halved it. What remains is model or temperature.

## Checkpointing

Results are appended per bundle to the output file, so a run that is killed
part-way is not wasted and can be read for whatever arms completed. Long by
design: qwen3.5:4b runs ~161 s/bundle locally, so the two qwen arms are ~2.7
hours for 30 bundles.

Usage:

    UOFA_OPENAI_COMPATIBLE_API_KEY=... PYTHONPATH=src \\
      python dev/tools/scripts/specificity_discriminator.py --out results.jsonl
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(_ROOT / "dev" / "tools" / "scripts"))
sys.path.insert(0, str(_ROOT / "src"))

from groundedness import (  # noqa: E402
    GroundednessResult,
    read_source_text,
    score_factor_rationales,
)
from uofa_cli import excel_constants as ec  # noqa: E402
from uofa_cli.document_reader import read_corpus  # noqa: E402
from uofa_cli.llm.config import LLMConfig  # noqa: E402
from uofa_cli.llm_extractor import extract  # noqa: E402

# Declared threshold: half the observed collapse. See DECLARATION.md.
SEPARATION = 0.20
CLOSE = 0.10

SHARED = set(ec.VV40_FACTOR_NAMES)   # the 13 factors both packs score


def _llama():
    return LLMConfig(backend="openai-compatible",
                     model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
                     base_url="https://api.together.xyz/v1",
                     api_key_env="UOFA_OPENAI_COMPATIBLE_API_KEY")


# (arm, model string, llm_config factory, temperature)
ARMS = [
    ("A qwen default", "ollama/qwen3.5:4b", None, None),
    ("B qwen temp0", "ollama/qwen3.5:4b", None, 0.0),
    ("C llama default", None, _llama, None),
    ("D llama temp0", None, _llama, 0.0),
]


def _v(fe):
    return getattr(fe, "value", fe)


def run_arm(label, model, cfg_factory, temp, bundles, out) -> dict:
    cfg = cfg_factory() if cfg_factory else None
    crit, agg = [], GroundednessResult()
    t0 = time.perf_counter()
    for i, bd in enumerate(bundles, 1):
        gt = json.loads((bd / "ground_truth.json").read_text())
        paths = sorted(p for p in (bd / "source").iterdir()
                       if p.is_file() and not p.name.startswith("."))
        try:
            r = extract(read_corpus(paths), model or "unused", gt["pack"],
                        llm_config=cfg, temperature=temp)
        except Exception as exc:                            # noqa: BLE001
            print(f"    [{i}/{len(bundles)}] {bd.name}: FAILED {exc}", flush=True)
            continue

        for f in r.credibility_factors:
            name = _v(f.get("factor_type"))
            if name not in SHARED:          # 13 shared factors only, per the declaration
                continue
            c = _v(f.get("acceptance_criteria"))
            if isinstance(c, str) and c.strip():
                crit.append(" ".join(c.split()).lower())

        facs = [{"factor_type": _v(f.get("factor_type")),
                 "rationale": _v(f.get("rationale"))} for f in r.credibility_factors]
        g = score_factor_rationales(facs, read_source_text(bd))
        for k in ("factors_total", "factors_with_rationale", "rationales_with_claims",
                  "claims_total", "claims_grounded", "factors_distinct"):
            setattr(agg, k, getattr(agg, k) + getattr(g, k))
        agg.ungrounded += g.ungrounded

        d = len(set(crit)) / len(crit) if crit else 0.0
        print(f"    [{i}/{len(bundles)}] {bd.name}: running distinct/filled {d:.3f}",
              flush=True)
        with out.open("a") as fh:
            fh.write(json.dumps({"arm": label, "bundle": bd.name, "n": i,
                                 "distinct_over_filled": d}) + "\n")

    rate = len(set(crit)) / len(crit) if crit else 0.0
    res = {"arm": label, "distinct_over_filled": rate,
           "filled": len(crit), "distinct": len(set(crit)),
           "groundedness": agg.as_dict(), "seconds": round(time.perf_counter() - t0, 1)}
    with out.open("a") as fh:
        fh.write(json.dumps({"ARM_RESULT": res}) + "\n")
    return res


def verdict(r: dict[str, float]) -> str:
    a, b, c, d = (r.get(k) for k in
                  ("A qwen default", "B qwen temp0",
                   "C llama default", "D llama temp0"))
    if None in (a, b, c, d):
        return "INCOMPLETE -- not all arms ran"
    model_gap = abs(a - c)
    temp_gaps = (abs(a - b), abs(c - d))
    if model_gap >= SEPARATION and all(t < CLOSE for t in temp_gaps):
        return "MODEL-ATTRIBUTED"
    if max(temp_gaps) >= SEPARATION and model_gap < CLOSE:
        return "TEMPERATURE-ATTRIBUTED"
    pairs = [abs(x - y) for i, x in enumerate([a, b, c, d])
             for y in [a, b, c, d][i + 1:]]
    if max(pairs) >= SEPARATION:
        return ("INTERACTION -- named in advance so it cannot be reported as one "
                "of the clean two")
    return "UNSEPARATED -- neither model nor temperature as operationalised here"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--n", type=int, default=30)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--arms", default="ABCD", help="subset, e.g. CD")
    args = ap.parse_args()

    bundles = [Path(b) for b in sorted(
        (_ROOT / "tests/fixtures/extract_corpus/dev").glob("bundle_*"))
        if (Path(b) / "ground_truth.json").exists()][:args.n]
    print(f"{len(bundles)} dev bundles, identical committed prompts\n")

    rates = {}
    for label, model, cfg, temp in ARMS:
        if label[0] not in args.arms:
            continue
        print(f"  {label}  (temperature={temp if temp is not None else 'backend default'})",
              flush=True)
        res = run_arm(label, model, cfg, temp, bundles, args.out)
        rates[label] = res["distinct_over_filled"]
        g = res["groundedness"]
        print(f"    -> distinct/filled {res['distinct_over_filled']:.4f} "
              f"({res['distinct']}/{res['filled']})  "
              f"triple {g['coverage']:.3f}/{g['claim_density']:.3f}/{g['groundedness']:.3f}  "
              f"{res['seconds']:.0f}s\n", flush=True)

    print(f"\n  {'arm':<20s} {'distinct/filled':>16s}")
    for k, v in rates.items():
        print(f"  {k:<20s} {v:>16.4f}")
    print(f"\n  VERDICT: {verdict(rates)}")
    print("  (thresholds from DECLARATION.md: separation >= 0.20, close < 0.10)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

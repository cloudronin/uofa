#!/usr/bin/env python3
"""The extraction-model scorecard. Runs against a declaration it does not set.

`studies/model-selection/DECLARATION.md` fixes the candidates, the bar and the
verdict logic, and was committed before this file existed.

## The bar, as declared

A candidate passes only by clearing ALL of:

    Q2 conjunction   claim density >= 0.40 AND groundedness >= 0.98
                     AND ungrounded triage set <= 4
    detection        F1 within 0.004 of the incumbent
    coverage         >= 0.95

on BOTH corpora, with the real six papers deciding.

## What is pinned, per row

Model identifier, prompt hash, temperature, max_tokens, and cost per document.
A qualification row whose configuration cannot be reconstructed is not a
qualification row -- and a frontier extractor clearing the bar at 100x the 4B's
cost is itself a tradeoff finding, so the cost column sits next to the pin
rather than in a footnote.

Checkpoints per bundle. Long runs get reaped; partial arms are still readable.

Usage:

    PYTHONPATH=src python dev/tools/scripts/model_selection.py \\
        --arms incumbent,family-72b,frontier --corpus synthetic --out rows.jsonl
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(_ROOT / "dev" / "tools" / "scripts"))
sys.path.insert(0, str(_ROOT / "src"))
sys.path.insert(0, str(_ROOT / "tests" / "fixtures" / "extract_corpus_real"))

from groundedness import (  # noqa: E402
    GroundednessResult,
    read_source_text,
    score_factor_rationales,
)
from uofa_cli import paths  # noqa: E402
from uofa_cli.document_reader import read_corpus  # noqa: E402
from uofa_cli.llm.config import LLMConfig  # noqa: E402
from uofa_cli.llm_extractor import extract  # noqa: E402

# Declared in studies/model-selection/DECLARATION.md. Not set here.
DENSITY_FLOOR = 0.40
GROUNDEDNESS_FLOOR = 0.98
TRIAGE_CEILING = 4
COVERAGE_FLOOR = 0.95
F1_TOLERANCE = 0.004

# Rough per-million-token prices for the cost column. Stated as estimates
# because they are list prices, not invoices -- the point is the order of
# magnitude between arms, which is what the tradeoff turns on.
_PRICE_PER_MTOK = {
    "local-4b": 0.0,                    # local, electricity only
    "incumbent": 0.88,
    "family-72b": 0.36,   # HF Router / deepinfra list price
    "frontier": 3.00,
}

ARMS = {
    "local-4b": dict(model="ollama/qwen3.5:4b", cfg=None),
    "incumbent": dict(model=None, cfg=lambda: LLMConfig(
        backend="openai-compatible",
        model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
        base_url="https://api.together.xyz/v1",
        api_key_env="UOFA_OPENAI_COMPATIBLE_API_KEY")),
    # Served through the HF Router rather than Together: no qwen-family model
    # is serverless on the Together account, and all five probed there return
    # "Unable to access non-serverless model". Same model, different serving
    # path -- which costs the declaration's "same hosted path as arm 2"
    # control. Recorded in DECLARATION.md rather than absorbed silently.
    "family-72b": dict(model=None, cfg=lambda: LLMConfig(
        backend="openai-compatible",
        model="Qwen/Qwen2.5-72B-Instruct",
        base_url="https://router.huggingface.co/v1",
        api_key_env="HF_TOKEN")),
    # The declared id claude-sonnet-5-2026 returns 404; claude-sonnet-5 is the
    # same model correctly spelled. See task #21 -- docs/llm-config.md carries
    # the broken string.
    "frontier": dict(model=None, cfg=lambda: LLMConfig(
        backend="anthropic", model="claude-sonnet-5",
        api_key_env="ANTHROPIC_API_KEY")),
}


def _prompt_hash() -> str:
    """One hash over both scored packs' prompts, so a row pins what it saw."""
    h = hashlib.sha256()
    for pack in ("vv40", "nasa-7009b"):
        h.update(paths.extract_prompt(pack).read_bytes())
    return h.hexdigest()[:16]


def _v(fe):
    return getattr(fe, "value", fe)


def _synthetic_bundles(n: int) -> list[tuple[Path, str]]:
    base = _ROOT / "tests/fixtures/extract_corpus/dev"
    out = []
    for bd in sorted(base.glob("bundle_*"))[:n]:
        gt = bd / "ground_truth.json"
        if gt.exists():
            out.append((bd, json.loads(gt.read_text())["pack"]))
    return out


def _real_bundles() -> list[tuple[Path, str]]:
    from v1_router_comparison import DOCS
    out = []
    for _tag, bundle, _annot in DOCS:
        base = (_ROOT / "tests" / "fixtures" / bundle if "/" in bundle
                else _ROOT / "tests" / "fixtures" / "extract_corpus_real" / bundle)
        pack = "vv40" if bundle.startswith("extract_corpus_vv40") else "nasa-7009b"
        out.append((base, pack))
    return out


def run_arm(name: str, bundles, out: Path, corpus: str) -> dict:
    spec = ARMS[name]
    cfg = spec["cfg"]() if spec["cfg"] else None
    agg = GroundednessResult()
    tokens = 0
    t0 = time.perf_counter()
    ok = 0

    for i, (bd, pack) in enumerate(bundles, 1):
        src = bd / "source"
        files = sorted(p for p in src.iterdir()
                       if p.is_file() and not p.name.startswith("."))
        try:
            corpus_obj = read_corpus(files)
            r = extract(corpus_obj, spec["model"] or "unused", pack, llm_config=cfg)
        except Exception as exc:                             # noqa: BLE001
            print(f"    [{i}/{len(bundles)}] {bd.name}: FAILED "
                  f"{type(exc).__name__}: {str(exc)[:90]}", flush=True)
            continue
        ok += 1
        tokens += getattr(corpus_obj, "total_tokens", 0)

        facs = [{"factor_type": _v(f.get("factor_type")),
                 "rationale": _v(f.get("rationale"))} for f in r.credibility_factors]
        g = score_factor_rationales(facs, read_source_text(bd))
        for k in ("factors_total", "factors_with_rationale", "rationales_with_claims",
                  "claims_total", "claims_grounded", "factors_distinct"):
            setattr(agg, k, getattr(agg, k) + getattr(g, k))
        agg.ungrounded += g.ungrounded

        print(f"    [{i}/{len(bundles)}] {bd.name}: "
              f"den {agg.claim_density:.3f} grd {agg.groundedness:.3f}", flush=True)
        with out.open("a") as fh:
            fh.write(json.dumps({"arm": name, "corpus": corpus, "bundle": bd.name,
                                 "n": i, "running": agg.as_dict()}) + "\n")

    secs = time.perf_counter() - t0
    row = {
        "ARM_RESULT": {
            "arm": name, "corpus": corpus,
            "bundles_ok": ok, "bundles_total": len(bundles),
            "triple": agg.as_dict(),
            "ungrounded": len(agg.ungrounded),
            # the pin
            "model": (spec["cfg"]().model if spec["cfg"] else spec["model"]),
            "prompt_sha": _prompt_hash(),
            "temperature": "backend default",
            "max_tokens": 16384,
            # the cost column, next to the pin
            "corpus_tokens": tokens,
            "seconds": round(secs, 1),
            "est_usd_per_doc": round(
                (tokens / 1e6) * _PRICE_PER_MTOK.get(name, 0.0) / max(ok, 1), 5),
        }
    }
    with out.open("a") as fh:
        fh.write(json.dumps(row) + "\n")
    return row["ARM_RESULT"]


def _spread(vals):
    return (min(vals), max(vals)) if vals else (0.0, 0.0)


def scorecard_repeated(by_arm: dict[str, list[dict]]) -> None:
    """Per-clause spread beside the point value, per the repeat policy.

    An arm whose spread straddles a threshold is UNSTABLE AT THE BAR -- neither
    passed nor failed. Reporting whichever run landed on the convenient side of
    a threshold is what W-EV-DET-03 exists to stop, and the study earned that
    weakener against itself before this policy existed.
    """
    print(f"\n  {'arm':<12s} {'runs':>5s} {'coverage':>18s} {'density':>18s} "
          f"{'groundedness':>18s}  verdict")
    for arm, runs in by_arm.items():
        cov = [r["triple"]["coverage"] for r in runs]
        den = [r["triple"]["claim_density"] for r in runs]
        grd = [r["triple"]["groundedness"] for r in runs]
        tri = [r["ungrounded"] for r in runs]

        def cell(vals):
            lo, hi = _spread(vals)
            mean = sum(vals) / len(vals)
            return f"{mean:.3f} [{lo:.3f}-{hi:.3f}]"

        # straddle = the spread crosses the threshold, so the run decides
        straddles = []
        if min(den) < DENSITY_FLOOR <= max(den):
            straddles.append("density")
        if min(grd) < GROUNDEDNESS_FLOOR <= max(grd):
            straddles.append("groundedness")
        if min(cov) < COVERAGE_FLOOR <= max(cov):
            straddles.append("coverage")
        if min(tri) <= TRIAGE_CEILING < max(tri):
            straddles.append("triage")

        if straddles:
            verdict = "UNSTABLE AT THE BAR: " + ",".join(straddles)
        else:
            fails = []
            if max(den) < DENSITY_FLOOR:
                fails.append("density")
            if max(grd) < GROUNDEDNESS_FLOOR:
                fails.append("grounding")
            if min(tri) > TRIAGE_CEILING:
                fails.append("triage")
            if max(cov) < COVERAGE_FLOOR:
                fails.append("coverage")
            verdict = "CLEARS" if not fails else "fails: " + ",".join(fails)

        print(f"  {arm:<12s} {len(runs):>5d} {cell(cov):>18s} {cell(den):>18s} "
              f"{cell(grd):>18s}  {verdict}")
    print("\n  Point value is the mean; brackets are min-max across runs.")
    print("  A spread straddling a threshold is UNSTABLE AT THE BAR, not a pass")
    print("  or a fail on whichever run happened. Policy: DECLARATION.md.")


def scorecard(rows: list[dict]) -> None:
    print(f"\n  {'arm':<12s} {'corpus':<10s} {'cov':>6s} {'density':>8s} "
          f"{'grnd':>6s} {'triage':>7s} {'$/doc':>8s}  conjunction")
    for r in rows:
        t = r["triple"]
        passes = (t["claim_density"] >= DENSITY_FLOOR
                  and t["groundedness"] >= GROUNDEDNESS_FLOOR
                  and r["ungrounded"] <= TRIAGE_CEILING
                  and t["coverage"] >= COVERAGE_FLOOR)
        # which clause failed -- never report a lone clause as the verdict
        why = []
        if t["claim_density"] < DENSITY_FLOOR:
            why.append("density")
        if t["groundedness"] < GROUNDEDNESS_FLOOR:
            why.append("grounding")
        if r["ungrounded"] > TRIAGE_CEILING:
            why.append("triage")
        if t["coverage"] < COVERAGE_FLOOR:
            why.append("coverage")
        verdict = "CLEARS" if passes else "fails: " + ",".join(why)
        print(f"  {r['arm']:<12s} {r['corpus']:<10s} {t['coverage']:>6.3f} "
              f"{t['claim_density']:>8.3f} {t['groundedness']:>6.3f} "
              f"{r['ungrounded']:>7d} {r['est_usd_per_doc']:>8.4f}  {verdict}")
    print("\n  The bar is a CONJUNCTION. One clause is not a pass -- see the")
    print("  correction in studies/specificity-discriminator/FINDINGS.md.")
    print("  Detection F1 within 0.004 of the incumbent is the fourth clause and")
    print("  is scored by score_extraction_batch, not here.")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--arms", default="incumbent",
                    help="comma-separated: " + ",".join(ARMS))
    ap.add_argument("--corpus", choices=("synthetic", "real"), default="synthetic")
    ap.add_argument("--n", type=int, default=30)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--repeats", type=int, default=3,
                    help="hosted arms need >= 3 per the declaration's repeat policy")
    args = ap.parse_args()

    bundles = (_synthetic_bundles(args.n) if args.corpus == "synthetic"
               else _real_bundles())
    print(f"{len(bundles)} {args.corpus} bundles   prompt {_prompt_hash()}\n")

    rows: list[dict] = []
    by_arm: dict[str, list[dict]] = {}
    for name in [a.strip() for a in args.arms.split(",") if a.strip()]:
        if name not in ARMS:
            raise SystemExit(f"unknown arm {name!r}. Known: {list(ARMS)}")
        spec = ARMS[name]
        if spec["cfg"]:
            # `api_key_env` is the env var's NAME, never its value -- the
            # invariant is stated in src/uofa_cli/llm/config.py:17 and enforced
            # by config validation, which rejects an inline key outright. The
            # branch below is reached only when that name is UNSET, so there is
            # no value in the process to disclose.
            # CodeQL flags the print below as py/clear-text-logging-sensitive-data
            # (high). It is a false positive on the name, not the data, and it is
            # NOT suppressed here: inline `# codeql[...]` comments are ignored by
            # this repo's default-setup scanning, and leaving one would read as
            # handled while the alert still stands -- the vacuous pass in §13.
            # The alert is open and awaiting a dismiss-or-restructure decision.
            key_var_name = spec["cfg"]().api_key_env
            if key_var_name and not os.environ.get(key_var_name):
                print(f"  {name}: SKIPPED -- {key_var_name} not set. Recorded "
                      f"as not run; no substitution.\n", flush=True)
                continue
        # The local arm cites determinism rather than repeating: fixed weights
        # on fixed hardware, so a repeat measures the harness, not the model.
        n = 1 if name == "local-4b" else args.repeats
        runs = []
        for k in range(1, n + 1):
            print(f"  {name}  run {k}/{n}", flush=True)
            runs.append(run_arm(name, bundles, args.out, args.corpus))
        by_arm[name] = runs
        rows.extend(runs)

    if by_arm:
        scorecard_repeated(by_arm)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

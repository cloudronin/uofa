"""Ablation — how much lift does the weakener catalog/rule give the model?

Same model, same cells, same posture-grounded scorer; vary ONLY what the prompt
reveals (run_p0.build_prompt conditions):

  full            fired pattern + catalog DEFINITION + measures + context  (baseline)
  fired_flag      "a weakener fired" (ID only, definition withheld) + measures + context
  definition_only the catalog definition as a CANDIDATE concern (not asserted) + measures + context
  catalog_ablated measures + context only          (NO weakener, NO meaning)
  measures_only   measures only                    (NO weakener, NO meaning, NO context)

Lift = the metric change vs `full`. The headline is **dangerous-error**: the
catalog's job is to catch the conflicting-signal gaps a model misses from raw
measures, so removing it should RAISE false-OK on the fire cells. Reuse a recorded
`full` run with --full-from to avoid re-running the baseline.

  python -m harness.bakeoff.ablation --model qwen2.5:7b \
      --conditions catalog_ablated,measures_only \
      --full-from harness/bakeoff/results/gate-2026-05-31-qwen2.5-7b.json \
      --output /tmp/ablation_7b.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

_COLS = ["dangerous_error_rate", "posture_accuracy", "escalation_rate",
         "selective_coverage_at_alpha", "ece"]


def _print_table(results: dict) -> None:
    print("\ncondition          danger  posture  escal  cov@a   ece   (hard-core)")
    print("  " + "-" * 64)
    for cond, r in results.items():
        hc = r["hard_core"]
        print(f"  {cond:16} {hc['dangerous_error_rate']:.2f}    {hc['posture_accuracy']:.2f}    "
              f"{hc['escalation_rate']:.2f}   {hc['selective_coverage_at_alpha']:.2f}   {hc['ece']:.2f}")
    if "full" not in results:
        return
    f = results["full"]["hard_core"]
    print("\nLIFT FROM THE CATALOG (full vs ablated, hard-core):")
    print("  a +danger means removing the catalog INTRODUCES dangerous false-OK errors the catalog caught")
    for cond, r in results.items():
        if cond == "full":
            continue
        hc = r["hard_core"]
        print(f"  full → {cond:16}  danger {hc['dangerous_error_rate'] - f['dangerous_error_rate']:+.2f}"
              f"   posture {f['posture_accuracy'] - hc['posture_accuracy']:+.2f}"
              f"   coverage {f['selective_coverage_at_alpha'] - hc['selective_coverage_at_alpha']:+.2f}"
              f"   escalation {hc['escalation_rate'] - f['escalation_rate']:+.2f}")


def run(argv: list[str] | None = None) -> int:
    from harness.bakeoff import run_p0, score

    p = argparse.ArgumentParser(description="Catalog-lift ablation on the bakeoff corpus.")
    p.add_argument("--corpus", type=Path, default=Path("harness/bakeoff/corpus"))
    p.add_argument("--model", help="override [llm] model (e.g. qwen2.5:7b)")
    p.add_argument("--backend", help="override [llm] backend (e.g. ollama)")
    p.add_argument("--conditions", default="full,catalog_ablated,measures_only",
                   help="comma-separated subset of " + ",".join(run_p0.CONDITIONS))
    p.add_argument("--alpha", type=float, default=0.02)
    p.add_argument("--measures", choices=["named", "raw"], default="named",
                   help="measures rendering: 'named' (conclusion-bearing fields) or 'raw' "
                        "(de-named signals — the fair detection test). NOTE: a 'named' --full-from "
                        "is not comparable to a 'raw' run; re-run full under the same --measures.")
    p.add_argument("--full-from", type=Path,
                   help="reuse a recorded full-condition result (its hard_core) instead of re-running 'full'")
    p.add_argument("--output", type=Path)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--temperature", type=float, default=0.0,
                   help="sampling temperature (default 0.0 = greedy/deterministic; the seed is "
                        "inert at 0.0). Set > 0 for a genuine multi-seed sampling-robustness run.")
    args = p.parse_args(argv)

    rows = run_p0.load_corpus(args.corpus)
    if not rows:
        print(f"no corpus rows under {args.corpus}")
        return 2

    backend = None
    if args.model or args.backend:
        from uofa_cli.llm import get_backend
        overrides = {k: v for k, v in (("model", args.model), ("backend", args.backend)) if v}
        backend = get_backend(cli_overrides=overrides)

    conditions = [c.strip() for c in args.conditions.split(",") if c.strip()]
    bad = [c for c in conditions if c not in run_p0.CONDITIONS]
    if bad:
        print(f"unknown condition(s): {bad}; choose from {run_p0.CONDITIONS}")
        return 2

    results: dict[str, dict] = {}
    for cond in conditions:
        if cond == "full" and args.full_from:
            rec = json.loads(Path(args.full_from).read_text())
            results["full"] = {"hard_core": rec["hard_core"], "reused_from": str(args.full_from)}
            print(f"=== full: reused from {args.full_from} ===", flush=True)
            continue
        print(f"\n=== condition: {cond} | measures={args.measures} seed={args.seed} "
              f"T={args.temperature} ({len(rows)} cells) ===", flush=True)
        answers = run_p0.run_corpus(rows, backend, condition=cond,
                                    measures_variant=args.measures, seed=args.seed,
                                    temperature=args.temperature)
        card = score.scorecard(rows, answers, alpha=args.alpha)
        results[cond] = {"hard_core": card["hard_core"], "answers": answers}

    # Ensure the baseline is present for the lift table even if 'full' wasn't in --conditions.
    if "full" not in results and args.full_from:
        rec = json.loads(Path(args.full_from).read_text())
        results = {"full": {"hard_core": rec["hard_core"], "reused_from": str(args.full_from)}, **results}

    print(f"\nmeasures rendering: {args.measures}")
    _print_table(results)
    if args.output:
        args.output.write_text(json.dumps(results, indent=2), encoding="utf-8")
        print(f"\nwrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())

"""Paired cell-bootstrap of the gap between two ablation conditions.

The recorded runs are temp-0 (greedy/deterministic), so the right robustness question
is not "does it survive resampling the model" (it can't vary) but "is the gap real or
driven by a few of the 60 cells." This pairs the two conditions per cell, bootstraps the
mean paired difference over cells, and reports a 95% CI. A CI that excludes 0 means the
gap survives cell resampling.

    python -m harness.bakeoff.bootstrap_gap \
        --output harness/bakeoff/results/ablation-raw-n60-2026-05-31-qwen2.5-7b.json \
        --a full --b catalog_ablated
"""
from __future__ import annotations

import argparse
import glob
import json
import random
from pathlib import Path

from harness.bakeoff import score

METRICS = ("posture", "committed_correct", "harmful")


def _per_cell(answers: list[dict], rows: dict[str, dict]) -> dict[str, dict]:
    out = {}
    for a in answers:
        r = rows.get(a.get("row_id"))
        if not r:
            continue
        s = score.score_row(r, a)
        out[a["row_id"]] = {
            "posture": int(s.posture_match),
            "harmful": int(s.action_bucket == "harmful"),
            "committed_correct": int((not a.get("escalate")) and s.posture_match),
        }
    return out


def bootstrap_gap(output_path: Path, corpus_dir: Path, cond_a: str, cond_b: str,
                  *, n_boot: int = 5000, rng_seed: int = 12345) -> dict:
    rng = random.Random(rng_seed)
    results = json.loads(Path(output_path).read_text())
    rows = {json.loads(Path(f).read_text())["row_id"]: json.loads(Path(f).read_text())
            for f in glob.glob(str(corpus_dir / "*.json"))}
    a = _per_cell(results[cond_a]["answers"], rows)
    b = _per_cell(results[cond_b]["answers"], rows)
    ids = [i for i in a if i in b]
    out: dict = {"a": cond_a, "b": cond_b, "n_cells": len(ids), "metrics": {}}
    for m in METRICS:
        diffs = [a[i][m] - b[i][m] for i in ids]
        k = len(diffs)
        means = sorted(sum(diffs[rng.randrange(k)] for _ in range(k)) / k for _ in range(n_boot))
        lo, hi = means[int(0.025 * n_boot)], means[int(0.975 * n_boot)]
        out["metrics"][m] = {"point": round(sum(diffs) / k, 4), "ci_lo": round(lo, 4),
                             "ci_hi": round(hi, 4), "robust": bool(lo > 0 or hi < 0)}
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Paired cell-bootstrap of an ablation gap (a − b).")
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--corpus", type=Path, default=Path("harness/bakeoff/corpus"))
    ap.add_argument("--a", default="full")
    ap.add_argument("--b", default="catalog_ablated")
    args = ap.parse_args()
    rd = bootstrap_gap(args.output, args.corpus, args.a, args.b)
    print(f"paired cell-bootstrap  {rd['a']} − {rd['b']}  (n_cells={rd['n_cells']})")
    for m, v in rd["metrics"].items():
        flag = "ROBUST" if v["robust"] else "includes 0 (noise)"
        print(f"  {m:18} {v['point']:+.3f}   95% CI [{v['ci_lo']:+.3f}, {v['ci_hi']:+.3f}]   {flag}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python
"""Measure HF `model-index` coverage before building the A3 eval-evidence detector.

Addendum v0.1 A3 carries an investigation item: the HF `model-index` metadata
block is structured and free, so check its coverage before investing in a
markdown-pattern tier -- the regex path may be a fallback rather than the
primary. This measures that rather than assuming it.

    python studies/a3-model-index-2026-08/measure_model_index.py [--limit 100]
"""

from __future__ import annotations

import argparse
import collections
import json
import urllib.request
from pathlib import Path

API = ("https://huggingface.co/api/models?sort=downloads&direction=-1"
       "&limit={limit}&filter=text-generation&expand[]=cardData&expand[]=downloads")


def measure(limit: int) -> dict:
    with urllib.request.urlopen(API.format(limit=limit), timeout=60) as r:
        models = json.load(r)

    with_index, with_results, metrics = [], [], collections.Counter()
    for m in models:
        index = (m.get("cardData") or {}).get("model-index")
        if not index:
            continue
        with_index.append(m["id"])
        if not any(e.get("results") for e in (index or [])):
            continue
        with_results.append(m["id"])
        for entry in index:
            for result in (entry.get("results") or []):
                for metric in (result.get("metrics") or []):
                    metrics[metric.get("type") or metric.get("name")] += 1

    n = len(models)
    return {
        "study": "a3-model-index-2026-08",
        "measured": "2026-08-10",
        "population": "most-downloaded text-generation models on the HF hub",
        "n_sampled": n,
        "n_with_model_index": len(with_index),
        "n_with_results": len(with_results),
        "pct_with_model_index": round(100 * len(with_index) / n, 1) if n else None,
        "models_with_model_index": sorted(with_index),
        "distinct_metric_types": len(metrics),
        "metric_types": dict(metrics.most_common()),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--limit", type=int, default=100)
    ap.add_argument("--out", default=str(Path(__file__).parent / "results.json"))
    args = ap.parse_args()
    result = measure(args.limit)
    Path(args.out).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(f"{result['n_sampled']} models sampled")
    print(f"  model-index present: {result['n_with_model_index']} "
          f"({result['pct_with_model_index']}%)")
    print(f"  with results[]     : {result['n_with_results']}")
    print(f"  distinct metrics   : {result['distinct_metric_types']}")
    print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

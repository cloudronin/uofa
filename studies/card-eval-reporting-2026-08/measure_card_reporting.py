#!/usr/bin/env python
"""What do model cards actually report, and does it overlap what a furnisher measures?

Measured before designing the Phase-4 prose path and W-EV-DIV-07, because both
rest on assumptions about card content that are cheaper to check than to debug:

  1. Is there enough structured benchmark reporting in cards to extract at all?
  2. Do the benchmarks cards report OVERLAP the constituents raidex furnishes?
     W-EV-DIV-07 compares a reported score against a furnished one for the SAME
     constituent. With no shared constituent there is nothing to compare, and the
     rule cannot fire regardless of whether the scores would agree.

    python studies/card-eval-reporting-2026-08/measure_card_reporting.py [--limit 50]
"""

from __future__ import annotations

import argparse
import collections
import json
import sys
import urllib.request
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO / "src"))

from uofa_cli.hf_card import fetch_card  # noqa: E402

API = ("https://huggingface.co/api/models?sort=downloads&direction=-1"
       "&limit={limit}&filter=text-generation")

# raidex constituent ids and how they plausibly appear in card prose. Generous on
# purpose: an alias list that is too narrow would understate overlap and bias the
# design decision toward "do not build DIV-07".
ALIASES = {
    "bbq": ["bbq"],
    "wmdp": ["wmdp"],
    "simpleqa": ["simpleqa", "simple qa", "simple-qa"],
    "strongreject": ["strongreject", "strong reject", "strong-reject"],
    "ethics": ["hendrycks ethics", "ethics benchmark"],
    "xstest": ["xstest", "xs-test"],
    "advglue": ["advglue", "adv-glue", "adversarial glue"],
    "confaide": ["confaide"],
    "sycophancy": ["sycophancy"],
}


def measure(limit: int) -> dict:
    with urllib.request.urlopen(API.format(limit=limit), timeout=60) as r:
        models = json.load(r)

    rows, per_constituent = [], collections.Counter()
    n_table = n_any = 0

    for m in models:
        mid = m["id"]
        try:
            fetched = fetch_card(mid, None)
        except Exception as exc:                      # network/hub hiccup, not a finding
            rows.append({"model": mid, "status": f"error:{type(exc).__name__}"})
            continue
        if fetched.status != "ok" or not fetched.text:
            rows.append({"model": mid, "status": fetched.status})
            continue

        low = fetched.text.lower()
        has_table = "\n|" in fetched.text and "---" in fetched.text
        hits = sorted(k for k, v in ALIASES.items() if any(a in low for a in v))
        n_table += bool(has_table)
        n_any += bool(hits)
        for h in hits:
            per_constituent[h] += 1
        rows.append({"model": mid, "status": "ok", "words": len(fetched.text.split()),
                     "has_markdown_table": has_table, "raidex_constituents_named": hits})

    ok = [r for r in rows if r.get("status") == "ok"]
    n = len(ok)
    return {
        "study": "card-eval-reporting-2026-08",
        "measured": "2026-08-11",
        "population": "most-downloaded text-generation models on the HF hub",
        "n_requested": limit,
        "n_with_readable_card": n,
        "n_with_markdown_table": n_table,
        "pct_with_markdown_table": round(100 * n_table / n, 1) if n else None,
        "n_naming_any_raidex_constituent": n_any,
        "pct_naming_any_raidex_constituent": round(100 * n_any / n, 1) if n else None,
        "per_constituent": dict(per_constituent),
        "aliases_searched": ALIASES,
        "per_model": rows,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--limit", type=int, default=50)
    ap.add_argument("--out", default=str(Path(__file__).parent / "results.json"))
    args = ap.parse_args()
    r = measure(args.limit)
    Path(args.out).write_text(json.dumps(r, indent=2, sort_keys=True) + "\n")
    n = r["n_with_readable_card"]
    print(f"{n} readable cards of {r['n_requested']} requested")
    print(f"  with a markdown table          : {r['n_with_markdown_table']} ({r['pct_with_markdown_table']}%)")
    print(f"  naming any raidex constituent  : {r['n_naming_any_raidex_constituent']} ({r['pct_naming_any_raidex_constituent']}%)")
    print(f"  per constituent                : {r['per_constituent'] or 'none'}")
    print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

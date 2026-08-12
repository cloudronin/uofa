#!/usr/bin/env python
"""Run the prose extractor over the committed specificity cases.

    python studies/taxonomy-validation/enrichment/run_specificity.py \
        [--model ollama/qwen3.5:4b] [--limit N]

Writes `specificity/<slug>.json` — one result file per extractor configuration.

**A specificity number is meaningless without the configuration that produced
it.** So every result pins the backend, the model, the generation parameters, the
prompt file's hash, and the cases file's hash. Two runs that disagree must be
attributable to a change in one of those, and without them you cannot tell
whether the extractor got better or the prompt moved under you.

## What the two directions mean

    expected=absent, field POPULATED   -> FALSE CLEAR
        Extraction invented a property the card does not state, which silences a
        warranted weakener. The card looks better than its record supports.

    expected=present, field BLANK      -> FALSE FIRE
        Extraction missed a property the card DOES state, so the weakener fires
        and accuses a published card of an omission it did not commit. This is
        the reputation-damaging direction and the reason the enrichment stratum
        exists -- the gold set cannot test it, having no positives.

An extraction ERROR is neither. Counting a timeout as a blank would score a
crash as a correct absence on the `absent` cases and as a false fire on the
`present` ones, so errors are tallied separately and excluded from both rates.

## Scope

Internal instrumentation for the A16 validation study. This does NOT touch the
public card surfaces (A6/A12), which stay gated behind catalog closure per A16.9.

Labels are **machine-drafted** and stay that way (A16.3/A16.7 amended
2026-08-11). These rates measure agreement between two machine readings of the
same text -- informative about extraction behaviour, and NOT a settle criterion.
A16.4 finding validity, adjudicated on fired findings, is the settle authority.
The output says so in `label_status`.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO / "src"))

from uofa_cli.furnishers import card_prose  # noqa: E402

CASES = _REPO / "tests/fixtures/specificity/cases.json"

# property -> the ValidationResult field card_prose.parse populates for it
FIELD_OF = {
    "P2_uncertainty": "hasUncertaintyQuantification",
    "P5_null_baseline": "nullBaselineStatement",
    "P6_claimed_cou": "claimedCOU",
    "P7_confound_control": "confoundControlStatement",
}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def _populated(evidence, field: str) -> bool:
    """Did extraction populate this property on ANY reported node?

    Any, not all: the claim under test is "the card states this", and one node
    carrying it is the card stating it. Requiring every node to carry it would
    score a card reporting five benchmarks with uncertainty on one as an absence.

    Booleans are handled explicitly. `hasUncertaintyQuantification` is emitted as
    `True` (card_prose moves the stated text to `uqMethod`), and the naive
    `str(value).strip()` test would read a hypothetical `False` as the non-empty
    string "False" and score it populated. Today parse() only ever omits the key
    or sets True, so the naive form happens to be right -- by accident of the
    emission, not by construction. Anything relied on by accident is a latent
    wrong number.
    """
    for node in getattr(evidence, "nodes", []) or []:
        if field not in node:
            continue
        value = node[field]
        if isinstance(value, bool):
            if value:
                return True
            continue
        if str(value or "").strip():
            return True
    return False


def run(model: str, limit: int | None, out_dir: Path) -> dict:
    # Hash AT READ TIME, not when the result is written. Hashing at the end
    # pins whatever the file became during the run, so a cases file edited
    # mid-run yields a result that pins a state it never scored -- an internally
    # inconsistent provenance block that still looks well-formed. Caught exactly
    # that way: a mid-run relabel left the hash current and the status stale.
    cases_sha = _sha(CASES)
    payload = json.loads(CASES.read_text(encoding="utf-8"))
    cases = payload["cases"][:limit] if limit else payload["cases"]

    results, errors = [], 0
    started = time.time()
    for i, case in enumerate(cases, 1):
        prop = case["property"]
        field = FIELD_OF[prop]
        row = {"card_id": case["card_id"], "row_hash": case["row_hash"],
               "property": prop, "expected": case["expected"],
               "hard_assert": case["hard_assert"], "reason": case["reason"]}
        try:
            evidence = card_prose.extract(
                case["excerpt"], f"https://uofa.net/spec/{case['row_hash']}",
                model=model, source_url=case["card_id"])
            got = _populated(evidence, field)
            row["populated"] = got
            row["n_nodes"] = len(getattr(evidence, "nodes", []) or [])
            if case["expected"] == "absent":
                row["outcome"] = "false-clear" if got else "correct"
            else:
                row["outcome"] = "correct" if got else "false-fire"
        except Exception as exc:                      # never silently a blank
            errors += 1
            row["outcome"] = "error"
            row["error"] = f"{type(exc).__name__}: {exc}"[:200]
        results.append(row)
        if i % 10 == 0 or i == len(cases):
            done = sum(1 for r in results if r["outcome"] != "error")
            print(f"  {i}/{len(cases)}  scored={done} errors={errors} "
                  f"({time.time()-started:.0f}s)", flush=True)

    # Rates per property, errors excluded from both denominators.
    rates = {}
    for prop in FIELD_OF:
        rows = [r for r in results if r["property"] == prop
                and r["outcome"] != "error"]
        absent = [r for r in rows if r["expected"] == "absent"]
        present = [r for r in rows if r["expected"] == "present"]
        fc = sum(r["outcome"] == "false-clear" for r in absent)
        ff = sum(r["outcome"] == "false-fire" for r in present)
        rates[prop] = {
            "n_absent": len(absent), "false_clears": fc,
            "false_clear_rate": round(fc / len(absent), 3) if absent else None,
            "n_present": len(present), "false_fires": ff,
            "false_fire_rate": round(ff / len(present), 3) if present else None,
        }

    hard = [r for r in results if r["hard_assert"] and r["outcome"] != "error"]
    out = {
        "study": "taxonomy-validation/enrichment/specificity",
        "scope": ("internal instrumentation for A16 validation; does NOT touch "
                  "the public card surfaces, which stay gated per A16.9"),
        # Without this block the numbers below mean nothing.
        "extractor": {
            "model": model,
            "prompt_file": str(card_prose.prompt_path().relative_to(_REPO)),
            "prompt_sha256": _sha(card_prose.prompt_path()),
            "temperature": 0.0, "seed": 20260811,
        },
        "cases_file": str(CASES.relative_to(_REPO)),
        "cases_sha256": cases_sha,
        "label_status": payload["label_status"],
        "n_cases": len(results), "n_errors": errors,
        "elapsed_seconds": round(time.time() - started),
        "rates": rates,
        "hard_assert": {
            "n": len(hard),
            "failures": [r for r in hard if r["outcome"] != "correct"],
        },
        "results": results,
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    slug = model.replace("/", "__").replace(":", "-")
    path = out_dir / f"{slug}.json"
    path.write_text(json.dumps(out, indent=2) + "\n")
    return {"path": path, **out}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model", default="ollama/qwen3.5:4b",
                    help="extractor config; pinned into the result")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--out", type=Path,
                    default=Path(__file__).parent / "specificity")
    args = ap.parse_args()

    if not CASES.exists():
        raise SystemExit("run make_cases.py first")

    res = run(args.model, args.limit, args.out)
    print(f"\nextractor: {res['extractor']['model']}  "
          f"prompt {res['extractor']['prompt_sha256']}")
    print(f"cases {res['n_cases']}  errors {res['n_errors']}\n")
    print(f"  {'property':22s} {'false-clear':>18s} {'false-fire':>18s}")
    for prop, r in res["rates"].items():
        fc = ("--" if r["false_clear_rate"] is None
              else f"{r['false_clears']}/{r['n_absent']} ({r['false_clear_rate']:.0%})")
        ff = ("--" if r["false_fire_rate"] is None
              else f"{r['false_fires']}/{r['n_present']} ({r['false_fire_rate']:.0%})")
        print(f"  {prop:22s} {fc:>18s} {ff:>18s}")
    hf = res["hard_assert"]["failures"]
    print(f"\n  hard_assert: {res['hard_assert']['n']} scored, {len(hf)} failed")
    for r in hf[:8]:
        print(f"    {r['card_id'][:38]:38s} {r['property'].split('_')[0]} "
              f"{r['outcome']}")
    print(f"\n  -> {res['path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

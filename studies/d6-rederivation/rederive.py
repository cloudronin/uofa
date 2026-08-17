#!/usr/bin/env python
"""Re-derive D6's 384/427 and test the equality claim in BOTH directions.

Decision Record ruling 10: measure, do not reword. The manuscript's §4.x sentence
says core's W-AL-01 fires on 384 of 427 raidex validation results and clears
"exactly the results carrying real uncertainty". Two things needed checking:

  (1) 384/427 is prose arithmetic in the README; re-derive it from the pinned
      artifact.
  (2) the equality claim was verified in one direction only. "Clears => carries
      uncertainty" is true by construction and proves little. The load-bearing
      converse -- "carries uncertainty => clears" -- was never tested.

    python studies/d6-rederivation/rederive.py            # offline, pinned cache
    python studies/d6-rederivation/rederive.py --out results.json

Why the converse is not circular here. Asking the furnisher whether it set
`hasUncertaintyQuantification` and then asking whether W-AL-01 cleared is one
question asked twice: the rule is `noValue` on that property, so the answers
cannot disagree. This script therefore defines "carries a stated uncertainty"
WITHOUT consulting the furnisher's predicate: it scans each result's raw block
for stderr-shaped keys and classifies every value it finds, including the ones
`_as_number` discards. A result holding a stderr a reader would call stated, but
which the furnisher declined, is a converse failure and this script names it.

The specific risk that motivated the scan: `_as_number` accepts int/float only
and returns None for every string, numeric ones included. A cohort publishing
`"acc_stderr": "0.023"` would state uncertainty and still be fired on.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO / "src"))

from uofa_cli.furnishers import raidex  # noqa: E402

DATASET = "cloudronin/raidex-results"
REVISION = "d459f536b506dc5f82355891db19f599f374a92c"

# The manuscript's claim, stated here so a mismatch is loud rather than silent.
CLAIMED_FIRES = 384
CLAIMED_TOTAL = 427
CLAIMED_CLEARS = 43

_MISSING = {"n/a", "na", "none", "null", "nan", "-", "", "not reported",
            "not available", "unavailable"}


def _snapshot_dir() -> Path:
    """The pinned revision in the local HF cache. Offline by construction."""
    base = (Path.home() / ".cache/huggingface/hub"
            / f"datasets--{DATASET.replace('/', '--')}" / "snapshots" / REVISION)
    if not base.is_dir():
        raise SystemExit(
            f"pinned revision not in cache: {base}\n"
            f"fetch it first, or pass --local-dir. Re-deriving against a "
            f"different revision would not be a re-derivation."
        )
    return base


def classify(value):
    """How a reader would read a stderr-shaped value, independent of the furnisher.

    Returns one of: 'number' (a real int/float), 'numeric-string' (a string that
    parses as a number -- stated uncertainty the furnisher discards), 'sentinel'
    (an explicit statement that uncertainty is unavailable), or 'other'.
    """
    if isinstance(value, bool):
        return "other"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, str):
        s = value.strip().lower()
        if s in _MISSING:
            return "sentinel"
        try:
            float(s)
            return "numeric-string"
        except ValueError:
            return "other"
    return "other"


def scan_stderr_values(raw):
    """Every stderr-shaped key in a raw block, with its reader-classification."""
    out = []

    def walk(node, path=""):
        if isinstance(node, dict):
            for k, v in node.items():
                walk(v, f"{path}.{k}" if path else str(k))
        elif "stderr" in path.lower():
            out.append((path, node, classify(node)))

    walk(raw or {})
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--local-dir", type=Path, default=None)
    ap.add_argument("--out", type=Path,
                    default=Path(__file__).parent / "results.json")
    args = ap.parse_args()

    src = args.local_dir or _snapshot_dir()
    files = sorted(src.glob("*.json"))
    if not files:
        raise SystemExit(f"no records under {src}")

    total = clears = fires = 0
    n_models = 0
    # Converse evidence, collected without consulting the furnisher's predicate.
    stated_but_fired = []      # the converse failures, if any
    cleared_without_stderr = []  # direction-1 failures, if any
    value_kinds = Counter()
    fired_shape = Counter()
    per_model = []

    for path in files:
        fetched = raidex.fetch_record("", local_path=path)
        if not fetched.ok:
            continue
        n_models += 1
        ev = raidex.furnish(fetched.record, "https://example.org/m", path.name)

        # `results` is a dict keyed by constituent name, plus a `composite`
        # sibling; the furnisher's node ids end in that same key, so each result
        # pairs with the record it was furnished from.
        raws = {}
        for key, entry in (fetched.record.get("results") or {}).items():
            if isinstance(entry, dict):
                raws[str(key)] = entry.get("raw")
        comp = fetched.record.get("composite")
        if isinstance(comp, dict):
            raws["composite"] = comp.get("raw")

        m_clears = 0
        for node in ev.nodes:
            total += 1
            key = node["id"].rsplit("-", 1)[-1]
            cleared = "hasUncertaintyQuantification" in node
            if cleared:
                clears += 1
                m_clears += 1
            else:
                fires += 1

            found = scan_stderr_values(raws.get(key))
            for _p, _v, kind in found:
                value_kinds[kind] += 1

            # How a fired-on result declines to report uncertainty: explicitly
            # (a sentinel under a stderr-shaped key) or silently (no such key at
            # all). The manuscript's phrasing depends on which dominates.
            if not cleared:
                if any(k == "sentinel" for _p, _v, k in found):
                    fired_shape["explicit-na"] += 1
                elif found:
                    fired_shape["stderr-key-other-value"] += 1
                else:
                    fired_shape["silent-no-stderr-key"] += 1

            reader_states_uncertainty = any(
                k in ("number", "numeric-string") for _p, _v, k in found)

            # Direction 2 (the converse): stated, yet fired on.
            if reader_states_uncertainty and not cleared:
                stated_but_fired.append({
                    "model": path.name, "result": key,
                    "values": [{"path": p, "value": v, "kind": k}
                               for p, v, k in found
                               if k in ("number", "numeric-string")],
                })
            # Direction 1: cleared, yet nothing a reader would call uncertainty.
            if cleared and not reader_states_uncertainty:
                cleared_without_stderr.append({
                    "model": path.name, "result": key,
                    "values": [{"path": p, "value": v, "kind": k}
                               for p, v, k in found],
                })

        per_model.append({"file": path.name, "results": len(ev.nodes),
                          "cleared": m_clears})

    d1_holds = not cleared_without_stderr
    d2_holds = not stated_but_fired
    arithmetic_holds = (fires == CLAIMED_FIRES and total == CLAIMED_TOTAL
                        and clears == CLAIMED_CLEARS)

    out = {
        "study": "d6-rederivation",
        "dataset": DATASET,
        "dataset_revision": REVISION,
        "n_models": n_models,
        "n_validation_results": total,
        "w_al_01_fires": fires,
        "w_al_01_clears": clears,
        "claimed": {"fires": CLAIMED_FIRES, "total": CLAIMED_TOTAL,
                    "clears": CLAIMED_CLEARS},
        "arithmetic_reproduces": arithmetic_holds,
        "equality_direction_1_cleared_implies_stated": {
            "holds": d1_holds, "counterexamples": cleared_without_stderr},
        "equality_direction_2_stated_implies_cleared": {
            "holds": d2_holds, "counterexamples": stated_but_fired},
        "stderr_shaped_value_kinds": dict(value_kinds),
        "fired_on_result_shape": dict(fired_shape),
        "per_model": per_model,
    }
    args.out.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")

    print(f"models {n_models}  results {total}")
    print(f"W-AL-01 fires {fires} / clears {clears}"
          f"   (claimed {CLAIMED_FIRES} / {CLAIMED_CLEARS})")
    print(f"arithmetic reproduces: {arithmetic_holds}")
    print(f"stderr-shaped values by reader-classification: {dict(value_kinds)}")
    print(f"how the {fires} fired-on results decline uncertainty: {dict(fired_shape)}")
    print(f"direction 1  cleared => stated uncertainty : "
          f"{'HOLDS' if d1_holds else f'FAILS ({len(cleared_without_stderr)})'}")
    print(f"direction 2  stated uncertainty => cleared : "
          f"{'HOLDS' if d2_holds else f'FAILS ({len(stated_but_fired)})'}")
    if stated_but_fired:
        print("\nconverse counterexamples (stated, yet fired on):")
        for c in stated_but_fired[:10]:
            print(f"  {c['model']} :: {c['result']} :: {c['values'][:2]}")
    print(f"\nwrote {args.out}")
    return 0 if (arithmetic_holds and d1_holds and d2_holds) else 1


if __name__ == "__main__":
    raise SystemExit(main())

"""Independent post-hoc loosening-sentinel verification.

The metrics module already counts ``loosening_sentinel_fires`` as part of
``compute_metrics``. This tool runs the same check independently — useful
as a 5-minute spot-check after a rule locks, and as documentation of the
sentinel pool for the audit trail.

For *rule_id*, prints:

* the size and intent breakdown of the sentinel pool;
* whether sentinels were properly disjoint from
  ``AFFECTED_RULES[rule_id]`` in the M5 baseline;
* whether any sentinel newly fires *rule_id* in *post_outcomes*;
* per-key listing of any newly-firing sentinel (if loosening detected).

Exit code 0 iff sentinels are clean post-fix.

CLI: ``python -m dev.tools.phase2_5.verify_sentinels --rule W-EP-01 \\
        --post-outcomes dev/build/phase2_5/.../milestones/after_w_ep_01.csv``
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

from dev.tools.phase2_5.refinement_loop.metrics import AFFECTED_RULES


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--rule", required=True)
    p.add_argument(
        "--split-path", type=Path, default=None,
        help="splits/{rule}_split.json (derived from --rule)",
    )
    p.add_argument(
        "--baseline-outcomes", type=Path,
        default=Path("dev/build/adversarial/phase2/2026-04-26/coverage/outcomes.csv"),
    )
    p.add_argument(
        "--post-outcomes", type=Path, required=True,
        help="post-modification outcomes.csv to check for newly-firing sentinels",
    )
    args = p.parse_args(argv)

    if args.split_path is None:
        rule_slug = args.rule.lower().replace("-", "_")
        args.split_path = Path(
            f"dev/build/phase2_5/shared/splits/{rule_slug}_split.json"
        )

    sentinels = json.loads(args.split_path.read_text())["loosening_sentinels"]
    affected = AFFECTED_RULES.get(args.rule, frozenset({args.rule}))

    # Build {key: row} for both baseline and post outcomes
    def index(path: Path) -> dict[str, dict]:
        out: dict[str, dict] = {}
        with open(path) as f:
            for r in csv.DictReader(f):
                out[f"{r['spec_id']}|{r['variant_num']}"] = r
        return out

    base = index(args.baseline_outcomes)
    post = index(args.post_outcomes)

    intents = Counter()
    base_disjoint = 0
    base_violators: list[str] = []
    for k in sentinels:
        r = base.get(k)
        if r is None:
            base_violators.append(f"{k} missing from baseline")
            continue
        intents[r.get("coverage_intent", "?")] += 1
        fired = {p.strip() for p in (r.get("rules_fired") or "").split(",") if p.strip()}
        if affected.isdisjoint(fired):
            base_disjoint += 1
        else:
            base_violators.append(f"{k} fired {affected & fired} in baseline")

    print(f"Rule: {args.rule}")
    print(f"Affected rules (splice set): {sorted(affected)}")
    print(f"Sentinel pool size: {len(sentinels)}")
    print(f"Sentinel intent breakdown: {dict(intents)}")
    print(f"Sentinels disjoint from affected rules in baseline: {base_disjoint}/{len(sentinels)}")
    if base_violators:
        print("BASELINE INTEGRITY VIOLATIONS:")
        for v in base_violators:
            print(f"  {v}")

    post_fires: list[tuple[str, set[str]]] = []
    for k in sentinels:
        r = post.get(k)
        if r is None:
            continue
        fired = {p.strip() for p in (r.get("rules_fired") or "").split(",") if p.strip()}
        if args.rule in fired:
            post_fires.append((k, fired))

    print(f"Sentinels firing {args.rule} post-modification: {len(post_fires)}/{len(sentinels)}")
    if post_fires:
        print("LOOSENING DETECTED — predicate fires on previously-clean packages:")
        for k, f in post_fires:
            print(f"  {k}: {sorted(f)}")
        return 1
    print("CLEAN: no loosening detected.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

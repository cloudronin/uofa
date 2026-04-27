"""Log a refinement-loop decision without re-running analyze.

Three use cases:

1. **lock-no-edit**: an upstream atomic rule's lock has already
   improved the metrics for a downstream compound rule (or a
   chained rule). The compound rule itself doesn't need an edit;
   we lock it at the current state with the upstream-rule's
   outcomes.csv as the reference.

2. **stuck**: structural analysis (or a series of reverts) has
   established that no narrow rule fix can improve the metric gate.
   Mark the rule stuck with rationale.

3. **rejected-baseline**: the post-upstream-lock re-baseline shows
   the rule is below a hard floor (e.g., recall < 0.80), so any
   iteration starts already-failed. Document and mark stuck.

Usage:

    python -m tools.phase2_5.log_decision \\
        --rule COMPOUND-01 --iteration 1 \\
        --decision rejected-baseline \\
        --baseline-outcomes out/.../milestones/after_w_ep_01.csv \\
        --rationale "post-W-EP-01 re-baseline: train recall=0.57, below floor"
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from tools.phase2_5.log import (
    IterationRecord,
    RefinementLog,
    current_git_sha,
    extract_rule_body,
    now_iso,
    predicate_sha,
    write_predicate_diff,
)
from tools.phase2_5.metrics import compute_metrics
from tools.phase2_5.refine_loop import RULE_NAME_MAP


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--rule", required=True)
    p.add_argument("--iteration", type=int, required=True)
    p.add_argument(
        "--decision", required=True,
        choices=["lock-no-edit", "stuck", "rejected-baseline"],
    )
    p.add_argument("--rationale", required=True)
    p.add_argument(
        "--baseline-outcomes", type=Path, required=True,
        help="outcomes.csv to compute metrics from (typically milestones/after_<rule>.csv)",
    )
    p.add_argument(
        "--rules-file", type=Path,
        default=Path("packs/core/rules/uofa_weakener.rules"),
    )
    p.add_argument(
        "--split-path", type=Path, default=None,
        help="splits/{rule}_split.json (derived from --rule)",
    )
    p.add_argument(
        "--log-path", type=Path,
        default=Path("out/phase2_5/2026-04-27/refinement_log.jsonl"),
    )
    p.add_argument(
        "--diff-dir", type=Path,
        default=Path("out/phase2_5/2026-04-27/predicate_diffs"),
    )
    p.add_argument(
        "--lock-dir", type=Path,
        default=Path("out/phase2_5/2026-04-27/holdout_used"),
    )
    args = p.parse_args(argv)

    if args.split_path is None:
        rule_slug = args.rule.lower().replace("-", "_")
        args.split_path = Path(f"out/phase2_5/2026-04-27/splits/{rule_slug}_split.json")

    rule_name = RULE_NAME_MAP[args.rule]

    # Compute metrics on baseline (no rules edit)
    train = compute_metrics(
        rule_id=args.rule, split_name="train",
        split_path=args.split_path, outcomes_csv=args.baseline_outcomes,
        batch_dir=args.baseline_outcomes.parent.parent,
        rules_file_override=None, holdout_lock_dir=args.lock_dir,
    )
    dev = compute_metrics(
        rule_id=args.rule, split_name="dev",
        split_path=args.split_path, outcomes_csv=args.baseline_outcomes,
        batch_dir=args.baseline_outcomes.parent.parent,
        rules_file_override=None, holdout_lock_dir=args.lock_dir,
    )

    # Predicate SHA of current state (no edit)
    current_body = extract_rule_body(args.rules_file, rule_name)
    sha = predicate_sha(current_body)

    # Empty diff for "no edit"
    diff_text = "(no predicate edit; lock at current state)\n"
    diff_path = write_predicate_diff(diff_text, args.diff_dir, args.rule, args.iteration)

    # Map decision → review_decision label
    review_decision = {
        "lock-no-edit": "accepted-no-edit",
        "stuck": "stuck",
        "rejected-baseline": "rejected-baseline",
    }[args.decision]

    log = RefinementLog(args.log_path)
    log.append(IterationRecord(
        rule_id=args.rule, iteration=args.iteration, timestamp=now_iso(),
        proposed_by="claude_code", review_decision=review_decision,
        predicate_before_sha=sha, predicate_after_sha=sha,
        predicate_diff_path=str(diff_path),
        rationale=args.rationale,
        train_metrics=train.to_dict(), dev_metrics=dev.to_dict(),
        decision=f"{review_decision}: {args.rationale[:200]}",
        git_sha=current_git_sha(),
        notes=f"baseline_outcomes={args.baseline_outcomes}",
    ))
    print(json.dumps({
        "rule_id": args.rule,
        "iteration": args.iteration,
        "decision": review_decision,
        "rationale": args.rationale,
        "train": train.to_dict(),
        "dev": dev.to_dict(),
        "diff_path": str(diff_path),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

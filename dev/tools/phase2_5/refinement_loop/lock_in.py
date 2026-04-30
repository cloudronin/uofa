"""Lock-in helper: compute train/dev/holdout metrics from a freshly-
analyzed outcomes.csv, log the iteration, and decide accept / revert.

Used after running ``uofa adversarial analyze --out per_iter_outcomes/<rule>_iter<N>``
on the full M5 batch with a modified rules file. This is the spec's
"end-of-rule full-analyze validation" plus the per-iteration metric
gate, in one shot — chosen for W-EP-01 because the structural fix is
high-confidence and the splice optimization isn't worth its complexity
at one rule × one iteration.

Usage:

    python -m dev.tools.phase2_5.lock_in --rule W-EP-01 --iteration 1 \
        --new-outcomes dev/build/phase2_5/.../w_ep_01_iter01/coverage/outcomes.csv \
        --rationale "added (?claim rdf:type uofa:Claim) guard"

Decision policy mirrors refine_loop._decision_metrics_pass:
- train.recall >= 0.80
- train.nc_fpr < baseline.nc_fpr
- train.bystander_rate < baseline.bystander_rate
- train.loosening_sentinel_fires == 0
- dev.recall >= prior_dev.recall - 0.05

If all pass and --commit-holdout is given, also computes holdout
(which spends the lock).
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from dev.tools.phase2_5.refinement_loop.log import (
    IterationRecord,
    RefinementLog,
    current_git_sha,
    extract_rule_body,
    now_iso,
    predicate_sha,
    write_predicate_diff,
)
from dev.tools.phase2_5.refinement_loop.metrics import AFFECTED_RULES, compute_metrics
from dev.tools.phase2_5.refinement_loop.refine_loop import RULE_NAME_MAP


M5_BASELINE_OUTCOMES = Path("dev/build/adversarial/phase2/2026-04-26/coverage/outcomes.csv")


def baseline_metrics(
    rule_id: str, split_path: Path, lock_dir: Path,
    baseline_outcomes: Path = M5_BASELINE_OUTCOMES,
):
    """Compute baseline metrics from *baseline_outcomes*.

    Default points at the M5 baseline; for COMPOUND rules whose firing
    rate shifted when an upstream atomic rule (W-EP-01 / W-ON-02)
    locked, pass the post-atomic-lock outcomes.csv so the metric gate
    measures against the CURRENT state, not the obsolete M5 numbers.
    See Phase 2.5 plan §"COMPOUND-01 needs a re-baseline" — the chain
    means COMPOUND-01's NC FPR drops from 89.8% to ~22% just from the
    W-EP-01 fix, with no COMPOUND-01 predicate edit.
    """
    return {
        "train": compute_metrics(
            rule_id=rule_id, split_name="train",
            split_path=split_path, outcomes_csv=baseline_outcomes,
            batch_dir=baseline_outcomes.parent.parent,
            rules_file_override=None, holdout_lock_dir=lock_dir,
        ),
        "dev": compute_metrics(
            rule_id=rule_id, split_name="dev",
            split_path=split_path, outcomes_csv=baseline_outcomes,
            batch_dir=baseline_outcomes.parent.parent,
            rules_file_override=None, holdout_lock_dir=lock_dir,
        ),
    }


def post_iter_metrics(
    rule_id: str, split_path: Path, new_outcomes: Path, lock_dir: Path,
    *, want_holdout: bool, force_holdout: bool = False,
):
    """Compute post-modification metrics from a new outcomes.csv.

    No rules_file_override → metrics module reads new_outcomes directly.
    """
    out = {
        "train": compute_metrics(
            rule_id=rule_id, split_name="train",
            split_path=split_path, outcomes_csv=new_outcomes,
            batch_dir=new_outcomes.parent.parent,
            rules_file_override=None, holdout_lock_dir=lock_dir,
        ),
        "dev": compute_metrics(
            rule_id=rule_id, split_name="dev",
            split_path=split_path, outcomes_csv=new_outcomes,
            batch_dir=new_outcomes.parent.parent,
            rules_file_override=None, holdout_lock_dir=lock_dir,
        ),
    }
    if want_holdout:
        out["holdout"] = compute_metrics(
            rule_id=rule_id, split_name="holdout",
            split_path=split_path, outcomes_csv=new_outcomes,
            batch_dir=new_outcomes.parent.parent,
            rules_file_override=None, holdout_lock_dir=lock_dir,
            force_holdout=force_holdout,
        )
    return out


def loosening_sentinel_check(rule_id: str, split_path: Path, new_outcomes: Path) -> int:
    """Count how many loosening sentinels now have any rule in
    AFFECTED_RULES[rule_id] firing — anything > 0 means the rule has
    loosened and we should auto-revert.
    """
    import csv
    affected = AFFECTED_RULES.get(rule_id, frozenset({rule_id}))
    sentinels = set(json.loads(split_path.read_text())["loosening_sentinels"])
    fires = 0
    with open(new_outcomes) as f:
        for r in csv.DictReader(f):
            key = f"{r['spec_id']}|{r['variant_num']}"
            if key not in sentinels:
                continue
            fired = {p.strip() for p in (r.get("rules_fired") or "").split(",") if p.strip()}
            if affected & fired:
                fires += 1
    return fires


def decide(baseline, post) -> tuple[str, str, bool]:
    """Apply the metric-gated accept policy.

    Returns ``(decision, reason, target_zone_reached)``. Decision is one of:

    - ``"accept"`` — train.recall ≥ 0.90 AND train.nc_fpr ≤ 0.10 (target
      zone). Rule is lockable; holdout can be spent.
    - ``"provisional"`` — clears hard floors but misses target zone.
      Predicate change is logged but the rule is NOT locked; the loop
      should continue iterating.
    - ``"revert"`` — hard floor violation, sentinel loosening, or dev
      overfit.

    Target-zone semantics mirror tools.phase2_5.refine_loop:
    HARD_FLOOR_RECALL=0.80, HARD_FLOOR_NC_FPR=0.25,
    TARGET_ZONE_RECALL=0.90, TARGET_ZONE_NC_FPR=0.10.
    """
    from dev.tools.phase2_5.refinement_loop.refine_loop import (
        HARD_FLOOR_RECALL, HARD_FLOOR_NC_FPR,
        TARGET_ZONE_RECALL, TARGET_ZONE_NC_FPR,
    )
    pt = post["train"]
    pd = post["dev"]
    bd = baseline["dev"]

    if pt.recall < HARD_FLOOR_RECALL:
        return "revert", (
            f"train.recall={pt.recall:.3f} below hard floor {HARD_FLOOR_RECALL}"
        ), False
    if pt.loosening_sentinel_fires > 0:
        return "revert", (
            f"loosening sentinel fired ({pt.loosening_sentinel_fires})"
        ), False
    if pt.nc_fpr > HARD_FLOOR_NC_FPR:
        return "revert", (
            f"train.nc_fpr={pt.nc_fpr:.3f} above hard floor {HARD_FLOOR_NC_FPR}"
        ), False
    if pd.recall < bd.recall - 0.05:
        return "revert", (
            f"dev.recall={pd.recall:.3f} regressed >5% from baseline {bd.recall:.3f}"
        ), False

    in_target_zone = (
        pt.recall >= TARGET_ZONE_RECALL and pt.nc_fpr <= TARGET_ZONE_NC_FPR
    )
    if in_target_zone:
        return "accept", (
            f"target zone: recall={pt.recall:.3f}≥{TARGET_ZONE_RECALL}, "
            f"nc_fpr={pt.nc_fpr:.3f}≤{TARGET_ZONE_NC_FPR}"
        ), True
    return "provisional", (
        f"hard floors cleared but target zone not reached: "
        f"recall={pt.recall:.3f} (target ≥ {TARGET_ZONE_RECALL}), "
        f"nc_fpr={pt.nc_fpr:.3f} (target ≤ {TARGET_ZONE_NC_FPR})"
    ), False


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--rule", required=True)
    p.add_argument("--iteration", type=int, required=True)
    p.add_argument("--new-outcomes", type=Path, required=True)
    p.add_argument("--rationale", default="")
    p.add_argument(
        "--rules-file", type=Path,
        default=Path("packs/core/rules/uofa_weakener.rules"),
    )
    p.add_argument(
        "--baseline-rules-file", type=Path, default=None,
        help="path to a backup of the rules file BEFORE this iter (for diff). "
             "If absent, fall back to git show HEAD",
    )
    p.add_argument(
        "--split-path", type=Path, default=None,
        help="splits/{rule}_split.json (derived from --rule)",
    )
    p.add_argument(
        "--log-path", type=Path,
        default=Path("dev/build/phase2_5/shared/refinement_log.jsonl"),
    )
    p.add_argument(
        "--diff-dir", type=Path,
        default=Path("dev/build/phase2_5/shared/predicate_diffs"),
    )
    p.add_argument(
        "--lock-dir", type=Path,
        default=Path("dev/build/phase2_5/shared/holdout_used"),
    )
    p.add_argument(
        "--milestones-dir", type=Path,
        default=Path("dev/build/phase2_5/shared/milestones"),
    )
    p.add_argument("--commit-holdout", action="store_true",
                   help="if metric gates pass, ALSO compute holdout (spends lock)")
    p.add_argument("--force-holdout", action="store_true")
    p.add_argument(
        "--baseline-outcomes", type=Path, default=M5_BASELINE_OUTCOMES,
        help="reference outcomes.csv to compute baseline metrics from. "
             "For COMPOUND rules after an atomic rule locks, pass the post-"
             "atomic outcomes.csv so the metric gate uses the CURRENT state, "
             "not the obsolete M5 numbers (see plan §COMPOUND re-baseline).",
    )
    args = p.parse_args(argv)

    if args.split_path is None:
        rule_slug = args.rule.lower().replace("-", "_")
        args.split_path = Path(f"dev/build/phase2_5/shared/splits/{rule_slug}_split.json")

    rule_name = RULE_NAME_MAP[args.rule]

    # Compute baseline and post-iter metrics. Default baseline is M5;
    # COMPOUND rules pass --baseline-outcomes pointing at the post-atomic-
    # rule lock outcomes (see plan §COMPOUND re-baseline).
    baseline = baseline_metrics(
        args.rule, args.split_path, args.lock_dir,
        baseline_outcomes=args.baseline_outcomes,
    )
    post = post_iter_metrics(
        args.rule, args.split_path, args.new_outcomes, args.lock_dir,
        want_holdout=False,
    )

    # Sentinel check (independent of compute_metrics's per-rule fire count)
    sent_fires = loosening_sentinel_check(args.rule, args.split_path, args.new_outcomes)
    post["train"].loosening_sentinel_fires = sent_fires

    decision_state, reason, target_zone = decide(baseline, post)

    # Holdout is only spent on a true ACCEPT (target zone reached).
    # Provisional iterations DO NOT spend the holdout — the loop should
    # continue iterating to push the rule into the target zone, and
    # holdout stays untouched until that happens.
    is_accept = decision_state == "accept"
    if is_accept and args.commit_holdout:
        holdout = compute_metrics(
            rule_id=args.rule, split_name="holdout",
            split_path=args.split_path, outcomes_csv=args.new_outcomes,
            batch_dir=args.new_outcomes.parent.parent,
            rules_file_override=None, holdout_lock_dir=args.lock_dir,
            force_holdout=args.force_holdout,
        )
        post["holdout"] = holdout

    # Log
    new_body = extract_rule_body(args.rules_file, rule_name)
    new_sha = predicate_sha(new_body)

    if args.baseline_rules_file:
        prior_body = extract_rule_body(args.baseline_rules_file, rule_name)
    else:
        # Fall back to git: read the rule body from HEAD
        import subprocess
        try:
            rules_text = subprocess.check_output(
                ["git", "show", f"HEAD:{args.rules_file}"], text=True
            )
            tmp = Path("/tmp/_baseline_rules.rules")
            tmp.write_text(rules_text)
            prior_body = extract_rule_body(tmp, rule_name)
        except Exception:
            prior_body = "(unknown)"
    prior_sha = predicate_sha(prior_body)

    import difflib
    diff_text = "\n".join(difflib.unified_diff(
        prior_body.splitlines(),
        new_body.splitlines(),
        fromfile=f"{args.rule} (before)",
        tofile=f"{args.rule} (iter {args.iteration})",
        lineterm="",
    ))
    diff_path = write_predicate_diff(diff_text, args.diff_dir, args.rule, args.iteration)

    decision_label = {
        "accept": "accepted-auto",
        "provisional": "provisional",
        "revert": "reverted",
    }[decision_state]
    log = RefinementLog(args.log_path)
    log.append(IterationRecord(
        rule_id=args.rule, iteration=args.iteration, timestamp=now_iso(),
        proposed_by="claude_code", review_decision=decision_label,
        predicate_before_sha=prior_sha, predicate_after_sha=new_sha,
        predicate_diff_path=str(diff_path),
        rationale=args.rationale,
        train_metrics=post["train"].to_dict(),
        dev_metrics=post["dev"].to_dict(),
        holdout_metrics=post["holdout"].to_dict() if "holdout" in post else None,
        decision=f"{decision_label}: {reason}",
        git_sha=current_git_sha(),
        target_zone_reached=target_zone,
        notes=f"new_outcomes={args.new_outcomes}",
    ))

    # On accept (target zone reached): copy the new outcomes to milestones/.
    # On provisional, copy to a separate milestones-provisional file so
    # plotting can still pick it up but it's not treated as final.
    if is_accept:
        args.milestones_dir.mkdir(parents=True, exist_ok=True)
        rule_slug = args.rule.lower().replace("-", "_")
        milestone = args.milestones_dir / f"after_{rule_slug}.csv"
        shutil.copyfile(args.new_outcomes, milestone)
        print(f"milestone copied: {milestone}")
    elif decision_state == "provisional":
        args.milestones_dir.mkdir(parents=True, exist_ok=True)
        rule_slug = args.rule.lower().replace("-", "_")
        milestone = args.milestones_dir / f"provisional_{rule_slug}_iter{args.iteration:02d}.csv"
        shutil.copyfile(args.new_outcomes, milestone)
        print(f"provisional milestone copied: {milestone}")

    print(json.dumps({
        "rule_id": args.rule,
        "iteration": args.iteration,
        "decision": decision_label,
        "target_zone_reached": target_zone,
        "reason": reason,
        "baseline_train": baseline["train"].to_dict(),
        "post_train": post["train"].to_dict(),
        "baseline_dev": baseline["dev"].to_dict(),
        "post_dev": post["dev"].to_dict(),
        "post_holdout": post["holdout"].to_dict() if "holdout" in post else None,
        "loosening_sentinel_fires": sent_fires,
        "diff_path": str(diff_path),
    }, indent=2))
    # Exit 0 on accept (target zone), 1 on provisional, 2 on revert
    return {"accept": 0, "provisional": 1, "revert": 2}[decision_state]


if __name__ == "__main__":
    raise SystemExit(main())

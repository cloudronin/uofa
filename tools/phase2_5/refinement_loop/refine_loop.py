"""Auto-mode metric-gated refinement orchestrator.

Per spec §4 (with adaptation #1: auto-mode). One CLI call drives a
single rule from baseline to either ``locked`` or
``refinement-stuck``. Every iteration is logged to
``refinement_log.jsonl`` regardless of outcome.

State machine per iteration:

    1. Inspect misfires (5 NC + 5 BYSTANDER from train split).
    2. Propose predicate revision (LLM call).
    3. Apply revision to a *scratch* rules file (does NOT touch
       packs/core/rules until the iteration accepts).
    4. Compute train metrics on the scratch rules file.
    5. Evaluate gates:
         - train.recall < 0.80                       → REVERT (hard floor)
         - train.loosening_sentinel_fires > 0        → REVERT (loosened)
         - train.nc_fpr ≥ baseline.nc_fpr            → REVERT (no improvement)
         - train.bystander_rate ≥ baseline.bystander → REVERT (no improvement)
       Otherwise compute dev metrics:
         - dev.recall < prior_dev.recall − 0.05      → REVERT (overfit)
         - else                                      → ACCEPT
    6. On ACCEPT: copy scratch rules → packs/core/rules; bump
       baseline.nc_fpr / baseline.bystander_rate / prior_dev.recall.
       Log iteration as accepted-auto.
    7. On REVERT: log iteration as reverted (no rules file change);
       increment consecutive-revert counter. 3 in a row → mark stuck.

CLI: ``python -m tools.phase2_5.refine_loop --rule W-EP-01``

Mocking knobs for tests:
    --dry-run                     don't touch the real rules file
    --max-iterations N            cap (default 5; spec target 3-5)
    --propose-fn dotted.path      override the propose function
    --metrics-fn dotted.path      override compute_metrics
"""

from __future__ import annotations

import argparse
import importlib
import json
import shutil
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from tools.phase2_5.refinement_loop.log import (
    IterationRecord,
    RefinementLog,
    current_git_sha,
    extract_rule_body,
    now_iso,
    predicate_sha,
    write_predicate_diff,
)
from tools.phase2_5.refinement_loop.metrics import (
    AFFECTED_RULES,
    Metrics,
    compute_metrics,
)


# Map rule_id (catalog ID) → Jena rule name (lowercase, underscored)
# Verified against packs/core/rules/uofa_weakener.rules.
# Note: W-CON-04 is implemented across multiple rule arms in the file
# (w_con04_no_sa, ...). For lock-in / stuck logging we use the primary
# arm; the predicate diff captures the relevant body.
RULE_NAME_MAP: dict[str, str] = {
    "W-EP-01":     "w_ep01",
    "W-ON-02":     "w_on02",
    "W-AL-02":     "w_al02",
    "COMPOUND-01": "compound_escalation",
    "COMPOUND-03": "compound_assurance_override",
    "W-AR-01":     "w_ar01",
    "W-AR-02":     "w_ar02",
    "W-CON-01":    "w_con01",
    "W-CON-04":    "w_con04_no_sa",
}


@dataclass
class LoopState:
    """Carry-over between iterations within a single rule's loop.

    Tracks consecutive reverts for the stuck signal AND the best
    provisional state (cleared hard floors but missed target zone) so
    the loop can fall back to it if the cap is hit before any iteration
    reaches the target zone.
    """
    baseline: Metrics
    prior_dev: Metrics
    consecutive_reverts: int = 0
    accepted_iters: list[int] = field(default_factory=list)
    last_accepted_body: str = ""
    best_provisional_body: str | None = None
    best_provisional_metrics: Metrics | None = None

    @property
    def stuck(self) -> bool:
        return self.consecutive_reverts >= 3


def _replace_rule_body(rules_text: str, rule_name: str, new_body: str) -> str:
    """Replace ``[rule_name: ... ]`` in ``rules_text`` with ``new_body``."""
    marker = f"[{rule_name}:"
    start = rules_text.find(marker)
    if start == -1:
        raise ValueError(f"rule {rule_name!r} not found")
    depth = 0
    for i in range(start, len(rules_text)):
        ch = rules_text[i]
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0:
                return rules_text[:start] + new_body + rules_text[i + 1 :]
    raise ValueError(f"no closing bracket for rule {rule_name!r}")


def _resolve_dotted(path: str):
    """Resolve a dotted import path to a callable (for test injection)."""
    mod_name, _, attr = path.rpartition(".")
    return getattr(importlib.import_module(mod_name), attr)


# Metric-gate thresholds. Tightened beyond the original "clear hard floors"
# policy: clearing the floors is necessary but no longer sufficient — a
# rule must land in the *target zone* before the iteration ACCEPTs and
# the rule LOCKs. See plan §"Auto-mode metric-gated accept policy".
HARD_FLOOR_RECALL = 0.80          # below → REVERT (cannot use this rule)
HARD_FLOOR_NC_FPR = 0.25          # above → REVERT (still mostly noise)
TARGET_ZONE_RECALL = 0.90         # at or above is in the target zone
TARGET_ZONE_NC_FPR = 0.10         # at or below is in the target zone


def _decision_metrics_pass(
    state: LoopState,
    train: Metrics,
    dev: Metrics,
) -> tuple[str, str, bool]:
    """Return (decision, reason, target_zone_reached).

    Decision is one of:

    - ``"accept"`` — train recall ≥ 0.90 AND train nc_fpr ≤ 0.10 AND no
      sentinel/dev regression. Target zone reached, rule is lockable.
    - ``"provisional"`` — clears hard floors but misses the target zone.
      Apply the new predicate, log as PROVISIONAL, but DO NOT lock —
      the loop continues so a later iteration can reach the target zone.
    - ``"revert"`` — hard floor violation, sentinel loosening, or dev
      overfit. Predicate change is discarded.

    Target-zone semantics: "the rule is now both adequately recall-y
    and adequately precise on NC." Iterations that are merely "less
    bad than baseline" no longer auto-lock; the loop must keep trying.
    """
    if train.recall < HARD_FLOOR_RECALL:
        return "revert", (
            f"train.recall={train.recall:.3f} below hard floor "
            f"{HARD_FLOOR_RECALL}"
        ), False
    if train.loosening_sentinel_fires > 0:
        return "revert", (
            f"loosening sentinel fired ({train.loosening_sentinel_fires} fires) — "
            "predicate has loosened"
        ), False
    if train.nc_fpr > HARD_FLOOR_NC_FPR:
        return "revert", (
            f"train.nc_fpr={train.nc_fpr:.3f} above hard floor "
            f"{HARD_FLOOR_NC_FPR}"
        ), False
    if dev.recall < state.prior_dev.recall - 0.05:
        return "revert", (
            f"dev.recall={dev.recall:.3f} regressed >5% from prior "
            f"{state.prior_dev.recall:.3f} (overfit signal)"
        ), False

    in_target_zone = (
        train.recall >= TARGET_ZONE_RECALL
        and train.nc_fpr <= TARGET_ZONE_NC_FPR
    )
    if in_target_zone:
        return "accept", (
            f"target zone: recall={train.recall:.3f}≥{TARGET_ZONE_RECALL}, "
            f"nc_fpr={train.nc_fpr:.3f}≤{TARGET_ZONE_NC_FPR}"
        ), True

    # Cleared hard floors but missed target zone — provisional acceptance.
    return "provisional", (
        f"hard floors cleared but target zone not reached: "
        f"recall={train.recall:.3f} (target ≥ {TARGET_ZONE_RECALL}), "
        f"nc_fpr={train.nc_fpr:.3f} (target ≤ {TARGET_ZONE_NC_FPR})"
    ), False


def run_loop(
    *,
    rule_id: str,
    rules_file: Path,
    split_path: Path,
    outcomes_csv: Path,
    batch_dir: Path,
    log_path: Path,
    diff_dir: Path,
    holdout_lock_dir: Path,
    max_iterations: int = 10,
    propose_fn=None,
    metrics_fn=None,
    inspect_fn=None,
    dry_run: bool = False,
    parallel: int = 5,
) -> dict:
    """Run the refinement loop on *rule_id*; return a summary dict.

    *propose_fn* / *metrics_fn* / *inspect_fn* are dependency-injected
    for tests; defaults are the real production functions.
    """
    if propose_fn is None:
        from tools.phase2_5.refinement_loop.propose_revision import make_proposal as propose_fn
    if metrics_fn is None:
        metrics_fn = compute_metrics
    if inspect_fn is None:
        from tools.phase2_5.analysis.inspect_misfires import sample_misfires as inspect_fn

    rule_name = RULE_NAME_MAP[rule_id]
    log = RefinementLog(log_path)

    # Baseline metrics on train + dev (no rules_file_override).
    baseline_train: Metrics = metrics_fn(
        rule_id=rule_id, split_name="train",
        split_path=split_path, outcomes_csv=outcomes_csv,
        batch_dir=batch_dir, rules_file_override=None,
        holdout_lock_dir=holdout_lock_dir, parallel=parallel,
    )
    baseline_dev: Metrics = metrics_fn(
        rule_id=rule_id, split_name="dev",
        split_path=split_path, outcomes_csv=outcomes_csv,
        batch_dir=batch_dir, rules_file_override=None,
        holdout_lock_dir=holdout_lock_dir, parallel=parallel,
    )
    initial_body = extract_rule_body(rules_file, rule_name)

    state = LoopState(
        baseline=baseline_train,
        prior_dev=baseline_dev,
        last_accepted_body=initial_body,
    )

    summary = {
        "rule_id": rule_id,
        "baseline_train": baseline_train.to_dict(),
        "baseline_dev": baseline_dev.to_dict(),
        "iterations": [],
        "final_state": "in-progress",
    }

    for iteration in range(1, max_iterations + 1):
        if state.stuck:
            summary["final_state"] = "refinement-stuck"
            break

        # 1. Inspect misfires
        misfires = inspect_fn(
            rule_id=rule_id, outcomes_csv=outcomes_csv, batch_dir=batch_dir,
        )

        # 2. Propose
        proposal = propose_fn(rule_id, state.last_accepted_body, misfires)

        # If proposal is a no-op, log and count as revert (but don't write).
        prior_sha = predicate_sha(state.last_accepted_body)
        new_sha = predicate_sha(proposal.new_body)
        if proposal.new_body == state.last_accepted_body or not proposal.diff_text:
            diff_path = write_predicate_diff(
                proposal.diff_text or "(no-op)\n", diff_dir, rule_id, iteration
            )
            log.append(IterationRecord(
                rule_id=rule_id, iteration=iteration, timestamp=now_iso(),
                proposed_by="claude_code", review_decision="rejected-noop",
                predicate_before_sha=prior_sha, predicate_after_sha=new_sha,
                predicate_diff_path=str(diff_path),
                rationale=proposal.rationale or "no-op",
                train_metrics={}, dev_metrics={},
                decision="rejected-noop", git_sha=current_git_sha(),
                target_zone_reached=False,
            ))
            state.consecutive_reverts += 1
            summary["iterations"].append({
                "iteration": iteration, "decision": "rejected-noop",
                "rationale": proposal.rationale,
            })
            continue

        # 3. Apply to scratch rules file
        scratch = Path(tempfile.mkstemp(suffix=".rules", prefix=f"{rule_name}_iter{iteration}_")[1])
        rules_text = rules_file.read_text()
        modified_text = _replace_rule_body(rules_text, rule_name, proposal.new_body)
        scratch.write_text(modified_text)

        # 4. Train metrics on the scratch rules file
        train_m: Metrics = metrics_fn(
            rule_id=rule_id, split_name="train",
            split_path=split_path, outcomes_csv=outcomes_csv,
            batch_dir=batch_dir, rules_file_override=scratch,
            holdout_lock_dir=holdout_lock_dir, parallel=parallel,
        )

        # 5. First-pass decision: only need TRAIN metrics for hard-floor /
        # target-zone screening. If train clearly fails the hard floors,
        # don't burn wall-clock on dev metrics.
        decision_first, reason_first, target_zone_first = _decision_metrics_pass(
            state, train_m, state.prior_dev,
        )
        dev_m: Metrics
        if decision_first == "revert":
            dev_m = Metrics(
                recall=0.0, nc_fpr=0.0, bystander_rate=0.0,
                precision=0.0, specificity=0.0,
                n_target=0, n_bystander=0, n_negative=0,
                notes="skipped-train-failed",
            )
            decision_state, reason, target_zone = decision_first, reason_first, False
        else:
            dev_m = metrics_fn(
                rule_id=rule_id, split_name="dev",
                split_path=split_path, outcomes_csv=outcomes_csv,
                batch_dir=batch_dir, rules_file_override=scratch,
                holdout_lock_dir=holdout_lock_dir, parallel=parallel,
            )
            decision_state, reason, target_zone = _decision_metrics_pass(
                state, train_m, dev_m,
            )

        diff_path = write_predicate_diff(proposal.diff_text, diff_dir, rule_id, iteration)
        # Map internal state → log decision label
        decision_label = {
            "accept": "accepted-auto",
            "provisional": "provisional",
            "revert": "reverted",
        }[decision_state]

        log.append(IterationRecord(
            rule_id=rule_id, iteration=iteration, timestamp=now_iso(),
            proposed_by="claude_code", review_decision=decision_label,
            predicate_before_sha=prior_sha, predicate_after_sha=new_sha,
            predicate_diff_path=str(diff_path),
            rationale=proposal.rationale,
            train_metrics=train_m.to_dict(), dev_metrics=dev_m.to_dict(),
            decision=decision_label + ": " + reason,
            git_sha=current_git_sha(),
            target_zone_reached=target_zone,
            notes=f"guard_added={proposal.guard_added}",
        ))
        summary["iterations"].append({
            "iteration": iteration, "decision": decision_label,
            "target_zone_reached": target_zone, "reason": reason,
            "train": train_m.to_dict(), "dev": dev_m.to_dict(),
        })

        if decision_state == "accept":
            # Lock-eligible: rule reaches target zone. Apply the predicate
            # and stop iterating (loop exits with locked state).
            state.consecutive_reverts = 0
            state.accepted_iters.append(iteration)
            state.last_accepted_body = proposal.new_body
            state.best_provisional_body = None  # supersede any provisional
            state.best_provisional_metrics = None
            state.baseline = train_m
            state.prior_dev = dev_m
            if not dry_run:
                shutil.copyfile(scratch, rules_file)
            summary["final_state"] = "locked"
            try:
                scratch.unlink()
            except OSError:
                pass
            break
        elif decision_state == "provisional":
            # Apply the predicate (it's an improvement) but don't lock.
            # Track this as the best-so-far provisional state in case the
            # loop hits the iteration cap without reaching target zone.
            state.consecutive_reverts = 0  # progress, even if not target
            if (
                state.best_provisional_metrics is None
                or _provisional_score(train_m) >
                   _provisional_score(state.best_provisional_metrics)
            ):
                state.best_provisional_body = proposal.new_body
                state.best_provisional_metrics = train_m
            state.last_accepted_body = proposal.new_body
            state.baseline = train_m
            state.prior_dev = dev_m
            if not dry_run:
                shutil.copyfile(scratch, rules_file)
        else:
            state.consecutive_reverts += 1

        try:
            scratch.unlink()
        except OSError:
            pass

    if summary["final_state"] == "in-progress":
        if state.stuck:
            summary["final_state"] = "refinement-stuck"
        elif state.best_provisional_body is not None:
            summary["final_state"] = "target-zone-not-reached"
        else:
            summary["final_state"] = "max-iterations-no-accept"

    summary["accepted_iterations"] = state.accepted_iters
    summary["final_train"] = state.baseline.to_dict()
    summary["final_dev"] = state.prior_dev.to_dict()
    return summary


def _provisional_score(m: Metrics) -> float:
    """Score a provisional state for "best-so-far" tracking.

    We prefer iterations that get closer to the target zone — minimize
    distance from (recall=0.95, nc_fpr=0.05) in the worse direction.
    Higher is better.
    """
    return m.recall - 2 * m.nc_fpr  # recall good, nc_fpr bad (weighted)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--rule", required=True)
    p.add_argument(
        "--rules-file", type=Path,
        default=Path("packs/core/rules/uofa_weakener.rules"),
    )
    p.add_argument(
        "--split-path", type=Path, default=None,
        help="splits/{rule}_split.json (derived from --rule)",
    )
    p.add_argument(
        "--outcomes", type=Path,
        default=Path("dev/build/adversarial/phase2/2026-04-26/coverage/outcomes.csv"),
    )
    p.add_argument(
        "--batch-dir", type=Path,
        default=Path("dev/build/adversarial/phase2/2026-04-26"),
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
    p.add_argument("--max-iterations", type=int, default=5)
    p.add_argument("--parallel", type=int, default=5)
    p.add_argument("--dry-run", action="store_true",
                   help="run loop but don't write to packs/core/rules")
    p.add_argument("--propose-fn", default=None,
                   help="dotted path to override propose_fn (for tests)")
    p.add_argument("--metrics-fn", default=None,
                   help="dotted path to override metrics_fn (for tests)")
    p.add_argument("--inspect-fn", default=None,
                   help="dotted path to override inspect_fn (for tests)")
    args = p.parse_args(argv)

    if args.split_path is None:
        rule_slug = args.rule.lower().replace("-", "_")
        args.split_path = Path(f"dev/build/phase2_5/shared/splits/{rule_slug}_split.json")

    propose_fn = _resolve_dotted(args.propose_fn) if args.propose_fn else None
    metrics_fn = _resolve_dotted(args.metrics_fn) if args.metrics_fn else None
    inspect_fn = _resolve_dotted(args.inspect_fn) if args.inspect_fn else None

    summary = run_loop(
        rule_id=args.rule,
        rules_file=args.rules_file,
        split_path=args.split_path,
        outcomes_csv=args.outcomes,
        batch_dir=args.batch_dir,
        log_path=args.log_path,
        diff_dir=args.diff_dir,
        holdout_lock_dir=args.lock_dir,
        max_iterations=args.max_iterations,
        propose_fn=propose_fn,
        metrics_fn=metrics_fn,
        inspect_fn=inspect_fn,
        dry_run=args.dry_run,
        parallel=args.parallel,
    )
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

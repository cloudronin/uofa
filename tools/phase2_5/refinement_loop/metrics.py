"""Per-rule metrics with cached-baseline + delta re-evaluation.

Per the approved plan, computing metrics on every iteration of the
refinement loop must NOT take ~50 minutes (a full re-analyze). We
splice deltas onto the cached M5 baseline outcomes, re-classifying
only the affected packages.

Key data structures:

    AFFECTED_RULES        — when modifying R, which rules' firings shift
    LOOSENING_SENTINELS   — populated at split time; checked every iter

API:

    compute_metrics(rule_id, split_name, rules_file_override=None)
        Returns {recall, nc_fpr, bystander_rate, precision, specificity,
                 n_target, n_bystander, n_negative, loosening_sentinel_fires}

    compute_metrics_full(rules_file)  — for end-of-rule validation

Holdout enforcement: writes a sentinel file per rule on first holdout
call; subsequent calls raise HoldoutAlreadyComputed unless --force.
"""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

# When refining rule R, also re-evaluate the firings of any compound
# rule whose body chains on R's output. Inspection of
# packs/core/rules/uofa_weakener.rules:
#
# * compound_escalation (COMPOUND-01): chains on any (Critical, High)
#   weakener pair where neither is itself a COMPOUND rule. So any atomic
#   rule modification can shift it. For our four primaries, the firings
#   that COMPOUND-01 cares about are W-EP-01 (Critical) and W-ON-02
#   (High). Other atomic rules also feed it (W-AR-02, W-AL-01, etc.)
#   but we're not modifying those in primaries.
#
# * compound_assurance_override (COMPOUND-03): chains on any Critical
#   weakener (excluding COMPOUND-*). W-EP-01 is the only Critical-firing
#   rule in our primary scope; W-ON-02 is High so doesn't propagate
#   into COMPOUND-03.
#
# These are pessimistic / over-approximating — we'd rather re-evaluate
# slightly more rules than miss a chained dependency.
AFFECTED_RULES: dict[str, frozenset[str]] = {
    "W-EP-01":     frozenset({"W-EP-01", "COMPOUND-01", "COMPOUND-03"}),
    "W-ON-02":     frozenset({"W-ON-02", "COMPOUND-01"}),
    "COMPOUND-01": frozenset({"COMPOUND-01"}),
    "COMPOUND-03": frozenset({"COMPOUND-03"}),
    # Stretch rules — atomic; assume they propagate to COMPOUND-01 if
    # they fire Critical or High; verified at iter start.
    "W-AR-02":     frozenset({"W-AR-02", "COMPOUND-01", "COMPOUND-03"}),
    "W-CON-01":    frozenset({"W-CON-01", "COMPOUND-01"}),
    "W-CON-04":    frozenset({"W-CON-04", "COMPOUND-01"}),
}


class HoldoutAlreadyComputed(Exception):
    """Raised on second compute_metrics(..., split='holdout') call for a
    rule that has already had its holdout spent."""


@dataclass
class Metrics:
    recall: float
    nc_fpr: float
    bystander_rate: float
    precision: float
    specificity: float
    n_target: int
    n_bystander: int
    n_negative: int
    loosening_sentinel_fires: int = 0
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "recall": round(self.recall, 4),
            "nc_fpr": round(self.nc_fpr, 4),
            "bystander_rate": round(self.bystander_rate, 4),
            "precision": round(self.precision, 4),
            "specificity": round(self.specificity, 4),
            "n_target": self.n_target,
            "n_bystander": self.n_bystander,
            "n_negative": self.n_negative,
            "loosening_sentinel_fires": self.loosening_sentinel_fires,
            "notes": self.notes,
        }


def _load_baseline_rows(outcomes_csv: Path) -> dict[str, dict]:
    """Index baseline outcomes.csv by composite key (spec_id|variant_num)."""
    out: dict[str, dict] = {}
    with open(outcomes_csv) as f:
        for r in csv.DictReader(f):
            key = f"{r['spec_id']}|{r['variant_num']}"
            out[key] = r
    return out


def _split_keys(split_path: Path, split_name: str) -> dict[str, list[str]]:
    """Read a per-rule split JSON and return the
    target/bystander/negative key lists for *split_name*."""
    data = json.loads(Path(split_path).read_text())
    return data[split_name]  # {"target": [...], "bystander": [...], "negative": [...]}


def _split_loosening_sentinels(split_path: Path) -> list[str]:
    return json.loads(Path(split_path).read_text())["loosening_sentinels"]


def _holdout_lock_path(rule_id: str, lock_dir: Path) -> Path:
    rule_slug = rule_id.lower().replace("-", "_")
    return lock_dir / f"{rule_slug}.lock"


def _check_holdout_lock(
    rule_id: str, split_name: str, lock_dir: Path, force: bool
) -> None:
    """Raise if the holdout split has already been computed for *rule_id*.

    Writes the lock on first holdout call so subsequent calls fail.
    """
    if split_name != "holdout":
        return
    lock_dir.mkdir(parents=True, exist_ok=True)
    lock = _holdout_lock_path(rule_id, lock_dir)
    if lock.exists() and not force:
        raise HoldoutAlreadyComputed(
            f"holdout already computed for {rule_id} (lock: {lock}). "
            f"Re-running holdout violates spec §3 'compute exactly once'. "
            f"Use --force-holdout to override (intentional foot-gun)."
        )
    lock.write_text(f"computed at: $(date -u)\nrule: {rule_id}\n")


def _run_jena_on_package(package_path: Path, rules_file: Path, pack: str = "vv40") -> set[str]:
    """Invoke `uofa rules` with a specific rules file; return fired pattern IDs."""
    try:
        result = subprocess.run(
            ["python", "-m", "uofa_cli", "rules", "--pack", pack,
             "--rules", str(rules_file), str(package_path)],
            capture_output=True, text=True, timeout=120,
        )
    except (subprocess.TimeoutExpired, OSError):
        return set()

    # Parse stdout for "⚠ <PATTERN>" or "⚡ <PATTERN>" lines
    import re
    fired = set()
    pattern = re.compile(r"^\s*[⚠⚡]\s+(W-[A-Z]+-\d+|COMPOUND-\d+)\s+\[")
    for line in result.stdout.splitlines():
        m = pattern.search(line)
        if m:
            fired.add(m.group(1))
    return fired


def _resolve_package_path(row: dict, batch_dir: Path) -> Path | None:
    """Reconstruct package_path from outcomes.csv row.

    Path layout: <batch>/<category>/<spec_id>/<spec_id>-vNN.jsonld
    """
    spec_id = row["spec_id"]
    variant_num = int(row["variant_num"])
    intent = row.get("coverage_intent", "")
    # Map coverage_intent → category subdir name (matches the runner)
    category_map = {
        "confirm_existing": "confirm_existing",
        "gap_probe": "gap_probe",
        "negative_control": "negative_controls",
        "interaction": "interaction",
    }
    category = category_map.get(intent, intent)
    # Strip any cell-suffix from spec_id (the runner adds _<sub>_<cou>)
    # Actually the spec_id in outcomes.csv IS the full cell_id, so use as-is
    candidate = batch_dir / category / spec_id / f"{spec_id.split('_')[0]}-v{variant_num:02d}.jsonld"
    if candidate.exists():
        return candidate
    # Fallback: glob for the variant file in the spec dir
    cell_dir = batch_dir / category / spec_id
    if cell_dir.exists():
        candidates = list(cell_dir.glob(f"*-v{variant_num:02d}.jsonld"))
        if candidates:
            return candidates[0]
    return None


def _splice_firings(
    baseline_rows: dict[str, dict],
    affected_rules: frozenset[str],
    new_firings_per_key: dict[str, set[str]],
) -> dict[str, set[str]]:
    """For each row's spec_id|variant_num key, build a fresh fired-set:
    drop everything in *affected_rules* from the baseline, then union in
    *new_firings_per_key*'s contribution for the SAME affected_rules.

    Returns {key: full_fired_set} for ALL rows in the baseline.
    """
    out: dict[str, set[str]] = {}
    for key, row in baseline_rows.items():
        baseline_fired = {
            p.strip() for p in (row.get("rules_fired") or "").split(",") if p.strip()
        }
        # Baseline minus affected
        kept = baseline_fired - affected_rules
        # Plus the new firings for affected rules (only present for affected packages)
        new = new_firings_per_key.get(key, set()) & affected_rules
        out[key] = kept | new
    return out


def _compute_from_fired_sets(
    rule_id: str,
    split_keys: dict[str, list[str]],
    fired_sets: dict[str, set[str]],
    sentinels: list[str],
) -> Metrics:
    """Compute the per-rule metrics from a {key: fired_set} dict."""
    target_keys = split_keys.get("target", [])
    bystander_keys = split_keys.get("bystander", [])
    negative_keys = split_keys.get("negative", [])

    n_target = len(target_keys)
    n_bystander = len(bystander_keys)
    n_negative = len(negative_keys)

    # Recall: of the target packages, how many have rule_id firing?
    target_hits = sum(1 for k in target_keys if rule_id in fired_sets.get(k, set()))
    recall = target_hits / n_target if n_target else 0.0

    # NC FPR
    nc_fires = sum(1 for k in negative_keys if rule_id in fired_sets.get(k, set()))
    nc_fpr = nc_fires / n_negative if n_negative else 0.0
    specificity = 1.0 - nc_fpr

    # Bystander rate
    by_fires = sum(1 for k in bystander_keys if rule_id in fired_sets.get(k, set()))
    bystander_rate = by_fires / n_bystander if n_bystander else 0.0

    # Precision = TP / (TP + FP)
    fp = nc_fires + by_fires
    precision = target_hits / (target_hits + fp) if (target_hits + fp) else 0.0

    # Loosening sentinel fires (only meaningful for the rule itself, not affected set)
    sentinel_fires = sum(1 for k in sentinels if rule_id in fired_sets.get(k, set()))

    return Metrics(
        recall=recall, nc_fpr=nc_fpr, bystander_rate=bystander_rate,
        precision=precision, specificity=specificity,
        n_target=n_target, n_bystander=n_bystander, n_negative=n_negative,
        loosening_sentinel_fires=sentinel_fires,
    )


def compute_metrics(
    rule_id: str,
    split_name: str,
    *,
    split_path: Path,
    outcomes_csv: Path,
    batch_dir: Path,
    rules_file_override: Path | None = None,
    holdout_lock_dir: Path,
    force_holdout: bool = False,
    parallel: int = 5,
) -> Metrics:
    """Compute metrics for *rule_id* on *split_name* split.

    If *rules_file_override* is given, splices that file's firings for
    AFFECTED_RULES[rule_id] over the baseline outcomes, then computes.
    Otherwise reads baseline outcomes directly (for baseline metrics).

    Holdout enforcement: writes a lock on first call; subsequent calls
    raise HoldoutAlreadyComputed unless force_holdout=True.
    """
    _check_holdout_lock(rule_id, split_name, holdout_lock_dir, force_holdout)

    baseline_rows = _load_baseline_rows(outcomes_csv)
    split_keys = _split_keys(split_path, split_name)
    sentinels = _split_loosening_sentinels(split_path)

    if rules_file_override is None:
        # Use baseline firings directly
        fired_sets: dict[str, set[str]] = {
            k: {p.strip() for p in (r.get("rules_fired") or "").split(",") if p.strip()}
            for k, r in baseline_rows.items()
        }
    else:
        # Cached-baseline + delta strategy
        affected = AFFECTED_RULES.get(rule_id, frozenset({rule_id}))
        # Affected packages: all keys in split + sentinels
        affected_keys: set[str] = set()
        for pop_keys in split_keys.values():
            affected_keys.update(pop_keys)
        affected_keys.update(sentinels)

        # Run Jena on each affected package with the override rules file.
        # For each, capture firings and intersect with affected rules.
        new_firings_per_key: dict[str, set[str]] = {}
        from concurrent.futures import ThreadPoolExecutor, as_completed
        def _eval(key: str) -> tuple[str, set[str]]:
            row = baseline_rows.get(key)
            if not row:
                return key, set()
            pkg_path = _resolve_package_path(row, batch_dir)
            if pkg_path is None:
                return key, set()
            return key, _run_jena_on_package(pkg_path, rules_file_override)

        if parallel == 1:
            for key in affected_keys:
                k, fired = _eval(key)
                new_firings_per_key[k] = fired
        else:
            with ThreadPoolExecutor(max_workers=parallel) as pool:
                futs = [pool.submit(_eval, k) for k in affected_keys]
                for f in as_completed(futs):
                    k, fired = f.result()
                    new_firings_per_key[k] = fired

        # Splice and compute
        fired_sets = _splice_firings(baseline_rows, affected, new_firings_per_key)

    return _compute_from_fired_sets(rule_id, split_keys, fired_sets, sentinels)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--rule", required=True, help="rule ID (e.g., W-EP-01)")
    p.add_argument(
        "--split", required=True, choices=["train", "dev", "holdout"],
        help="which split to compute on",
    )
    p.add_argument(
        "--split-path", type=Path, default=None,
        help="splits/{rule}_split.json (default: derived from --rule)",
    )
    p.add_argument(
        "--outcomes", type=Path,
        default=Path("build/adversarial/phase2/2026-04-26/coverage/outcomes.csv"),
    )
    p.add_argument(
        "--batch-dir", type=Path,
        default=Path("build/adversarial/phase2/2026-04-26"),
    )
    p.add_argument(
        "--rules-file", type=Path, default=None,
        help="modified rules file for delta evaluation (omit for baseline)",
    )
    p.add_argument(
        "--lock-dir", type=Path,
        default=Path("build/phase2_5/shared/holdout_used"),
    )
    p.add_argument(
        "--force-holdout", action="store_true",
        help="bypass single-shot holdout enforcement (intentional foot-gun)",
    )
    p.add_argument("--parallel", type=int, default=5)
    args = p.parse_args(argv)

    if args.split_path is None:
        rule_slug = args.rule.lower().replace("-", "_")
        args.split_path = Path(f"build/phase2_5/shared/splits/{rule_slug}_split.json")

    m = compute_metrics(
        rule_id=args.rule,
        split_name=args.split,
        split_path=args.split_path,
        outcomes_csv=args.outcomes,
        batch_dir=args.batch_dir,
        rules_file_override=args.rules_file,
        holdout_lock_dir=args.lock_dir,
        force_holdout=args.force_holdout,
        parallel=args.parallel,
    )
    print(json.dumps(m.to_dict(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

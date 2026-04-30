"""Train / dev / holdout splitter per rule.

Per spec §3:
- For each in-scope rule R, partition the M5 outcomes into TARGET /
  BYSTANDER / NEGATIVE populations.
- Stratified by base_cou_key (morrison/cou1, morrison/cou2,
  nagaraja/cou1) and variant_num bucket (1-7, 8-14, 15-20).
- 70/15/15 train/dev/holdout, seed=20260427.
- LOOSENING_SENTINELS sample (50 per rule) drawn at split time and
  pinned in the JSON for reproducibility.

CLI: ``python -m tools.phase2_5.split --rule W-EP-01``
     ``python -m tools.phase2_5.split --all``
"""

from __future__ import annotations

import argparse
import csv
import json
import random
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path

# Fixed seed per spec §3
SPLIT_SEED = 20260427

# In-scope rules (per the approved plan)
PRIMARY_RULES = ("W-EP-01", "W-ON-02", "COMPOUND-01", "COMPOUND-03")
STRETCH_RULES = ("W-AR-02", "W-CON-01", "W-CON-04")
ALL_RULES = PRIMARY_RULES + STRETCH_RULES

# Loosening sentinel size per spec adaptation
LOOSENING_SENTINEL_SIZE = 50


@dataclass
class Split:
    """One split bucket for one rule.

    Each list contains spec_id|variant_num composite keys (str) so we
    can quickly look up rows in outcomes.csv.
    """
    rule_id: str
    train: dict[str, list[str]]      # population → [keys]
    dev: dict[str, list[str]]
    holdout: dict[str, list[str]]
    loosening_sentinels: list[str]   # 50 keys where rule didn't fire in baseline
    seed: int = SPLIT_SEED

    def to_json(self) -> dict:
        return asdict(self)


def _key(row: dict) -> str:
    """Deterministic composite key for a row in outcomes.csv."""
    return f"{row['spec_id']}|{row['variant_num']}"


def _bucket_variant(variant_num: int) -> str:
    if variant_num <= 7:
        return "v1-7"
    if variant_num <= 14:
        return "v8-14"
    return "v15-20"


def _populate(rule_id: str, rows: list[dict]) -> dict[str, list[dict]]:
    """Bucket rows into TARGET / BYSTANDER / NEGATIVE for *rule_id*.

    TARGET    — confirm_existing rows where target_weakener == rule_id
    BYSTANDER — confirm_existing rows where target_weakener != rule_id
    NEGATIVE  — negative_control rows (excluding GEN-INVALID)
    """
    target: list[dict] = []
    bystander: list[dict] = []
    negative: list[dict] = []

    for r in rows:
        intent = r.get("coverage_intent")
        outcome = r.get("outcome_class")
        target_weakener = r.get("target_weakener")

        if intent == "confirm_existing":
            if outcome == "GEN-INVALID":
                continue  # skip gen-invalid for splits
            if target_weakener == rule_id:
                target.append(r)
            else:
                bystander.append(r)
        elif intent == "negative_control" and outcome != "GEN-INVALID":
            negative.append(r)

    return {"target": target, "bystander": bystander, "negative": negative}


def _stratified_split(
    rows: list[dict], rng: random.Random, ratios: tuple[float, float, float] = (0.7, 0.15, 0.15)
) -> tuple[list[dict], list[dict], list[dict]]:
    """Split *rows* into train/dev/holdout, stratified by
    (base_cou_key, variant_num bucket).

    Each stratum is shuffled with the given rng (deterministic per seed)
    and assigned in 70/15/15 ratio. Strata smaller than 7 rows fall
    back to all-train (ratios still respected on the whole population).
    """
    strata: dict[tuple, list[dict]] = defaultdict(list)
    for r in rows:
        cou = r.get("base_cou_key") or "unknown_cou"
        bucket = _bucket_variant(int(r.get("variant_num", 0)))
        strata[(cou, bucket)].append(r)

    train, dev, holdout = [], [], []
    for stratum_rows in strata.values():
        rng.shuffle(stratum_rows)
        n = len(stratum_rows)
        n_train = int(round(n * ratios[0]))
        n_dev = int(round(n * ratios[1]))
        # holdout gets the remainder so totals always reconcile
        train.extend(stratum_rows[:n_train])
        dev.extend(stratum_rows[n_train : n_train + n_dev])
        holdout.extend(stratum_rows[n_train + n_dev :])

    return train, dev, holdout


def _draw_loosening_sentinels(
    rule_id: str,
    affected_rules: frozenset[str],
    all_rows: list[dict],
    rng: random.Random,
    n: int = LOOSENING_SENTINEL_SIZE,
) -> list[str]:
    """Pick ``n`` row keys where NONE of the affected rules fired.

    These are the canaries: if a refined predicate later loosens and
    starts firing on any sentinel, it triggers an auto-revert.
    """
    candidates: list[dict] = []
    for r in all_rows:
        fired = {
            p.strip() for p in (r.get("rules_fired") or "").split(",") if p.strip()
        }
        if affected_rules.isdisjoint(fired):
            candidates.append(r)

    rng.shuffle(candidates)
    return [_key(r) for r in candidates[:n]]


def build_split(
    rule_id: str,
    outcomes_csv: Path,
    affected_rules: frozenset[str],
    seed: int = SPLIT_SEED,
) -> Split:
    """Build the train/dev/holdout split for *rule_id*."""
    rows = list(csv.DictReader(open(outcomes_csv)))
    populations = _populate(rule_id, rows)

    rng = random.Random(seed)
    out: dict[str, dict[str, list[str]]] = {
        "train": {}, "dev": {}, "holdout": {},
    }
    for pop_name, pop_rows in populations.items():
        train, dev, holdout = _stratified_split(pop_rows, rng)
        out["train"][pop_name] = [_key(r) for r in train]
        out["dev"][pop_name] = [_key(r) for r in dev]
        out["holdout"][pop_name] = [_key(r) for r in holdout]

    sentinels = _draw_loosening_sentinels(rule_id, affected_rules, rows, rng)

    return Split(
        rule_id=rule_id,
        train=out["train"],
        dev=out["dev"],
        holdout=out["holdout"],
        loosening_sentinels=sentinels,
        seed=seed,
    )


def write_split(split: Split, splits_dir: Path) -> Path:
    splits_dir.mkdir(parents=True, exist_ok=True)
    rule_slug = split.rule_id.lower().replace("-", "_")
    out_path = splits_dir / f"{rule_slug}_split.json"
    out_path.write_text(json.dumps(split.to_json(), indent=2))
    return out_path


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--outcomes",
        type=Path,
        default=Path("dev/build/adversarial/phase2/2026-04-26/coverage/outcomes.csv"),
        help="path to M5 outcomes.csv (read-only)",
    )
    p.add_argument(
        "--out", type=Path, default=Path("dev/build/phase2_5/shared/splits"),
        help="output directory for split JSONs",
    )
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--rule", help="single rule ID (e.g., W-EP-01)")
    g.add_argument("--all", action="store_true", help="all primary + stretch rules")
    args = p.parse_args(argv)

    # Late import so the module can be imported standalone for testing
    from tools.phase2_5.refinement_loop.metrics import AFFECTED_RULES

    rules = list(ALL_RULES) if args.all else [args.rule]
    for rule_id in rules:
        affected = AFFECTED_RULES.get(rule_id, frozenset({rule_id}))
        split = build_split(rule_id, args.outcomes, affected)
        out_path = write_split(split, args.out)
        # Quick sanity print: cardinalities per population
        n_train = sum(len(v) for v in split.train.values())
        n_dev = sum(len(v) for v in split.dev.values())
        n_hold = sum(len(v) for v in split.holdout.values())
        print(
            f"{rule_id}: train={n_train}, dev={n_dev}, holdout={n_hold}, "
            f"sentinels={len(split.loosening_sentinels)} → {out_path}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Unit tests for tools.phase2_5.split."""

from __future__ import annotations

import csv
import json
import random
from pathlib import Path

from tools.phase2_5.refinement_loop.split import (
    SPLIT_SEED,
    _bucket_variant,
    _draw_loosening_sentinels,
    _populate,
    _stratified_split,
    build_split,
    write_split,
)


def _make_synthetic_outcomes(tmp_path: Path, n_per_pop: int = 30) -> Path:
    """Create a small fake outcomes.csv with confirm_existing + nc rows."""
    rows = []
    cous = ["morrison/cou1", "morrison/cou2", "nagaraja/cou1"]
    # confirm_existing rows targeting W-EP-01
    for i in range(n_per_pop):
        cou = cous[i % 3]
        v = (i % 20) + 1
        rows.append({
            "spec_id": f"spec_target_{i}",
            "variant_num": str(v),
            "coverage_intent": "confirm_existing",
            "target_weakener": "W-EP-01",
            "outcome_class": "WEAKENED",
            "rules_fired": "W-EP-01",
            "base_cou_key": cou,
        })
    # confirm_existing rows targeting something else (bystanders)
    for i in range(n_per_pop):
        cou = cous[i % 3]
        v = (i % 20) + 1
        rows.append({
            "spec_id": f"spec_bystander_{i}",
            "variant_num": str(v),
            "coverage_intent": "confirm_existing",
            "target_weakener": "W-XX-99",
            "outcome_class": "WEAKENED",
            "rules_fired": "W-XX-99,W-EP-01",
            "base_cou_key": cou,
        })
    # negative_control rows
    for i in range(n_per_pop):
        cou = cous[i % 3]
        v = (i % 20) + 1
        rows.append({
            "spec_id": f"spec_nc_{i}",
            "variant_num": str(v),
            "coverage_intent": "negative_control",
            "target_weakener": "",
            "outcome_class": "VALID",
            "rules_fired": "" if i % 2 == 0 else "W-EP-01",
            "base_cou_key": cou,
        })
    p = tmp_path / "outcomes.csv"
    fieldnames = list(rows[0].keys())
    with open(p, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    return p


def test_bucket_variant():
    assert _bucket_variant(1) == "v1-7"
    assert _bucket_variant(7) == "v1-7"
    assert _bucket_variant(8) == "v8-14"
    assert _bucket_variant(14) == "v8-14"
    assert _bucket_variant(15) == "v15-20"
    assert _bucket_variant(20) == "v15-20"


def test_populate_buckets_correctly(tmp_path: Path):
    rows = list(csv.DictReader(open(_make_synthetic_outcomes(tmp_path))))
    pops = _populate("W-EP-01", rows)
    # Each population should be ~30 (excluding GEN-INVALIDs, which we made none of)
    assert len(pops["target"]) == 30
    assert len(pops["bystander"]) == 30
    assert len(pops["negative"]) == 30


def test_stratified_split_ratios(tmp_path: Path):
    """Train/dev/holdout should be approximately 70/15/15."""
    rows = list(csv.DictReader(open(_make_synthetic_outcomes(tmp_path, n_per_pop=100))))
    pops = _populate("W-EP-01", rows)
    rng = random.Random(SPLIT_SEED)
    train, dev, holdout = _stratified_split(pops["target"], rng)
    total = len(train) + len(dev) + len(holdout)
    assert total == len(pops["target"])
    # Allow ±15% slack (small strata can wobble)
    assert 0.55 <= len(train) / total <= 0.85
    assert 0.05 <= len(dev) / total <= 0.25
    assert 0.05 <= len(holdout) / total <= 0.25


def test_split_is_deterministic(tmp_path: Path):
    """Two runs with same seed produce identical splits."""
    p = _make_synthetic_outcomes(tmp_path)
    s1 = build_split("W-EP-01", p, frozenset({"W-EP-01"}))
    s2 = build_split("W-EP-01", p, frozenset({"W-EP-01"}))
    assert s1.train == s2.train
    assert s1.dev == s2.dev
    assert s1.holdout == s2.holdout
    assert s1.loosening_sentinels == s2.loosening_sentinels


def test_loosening_sentinels_disjoint_from_affected(tmp_path: Path):
    p = _make_synthetic_outcomes(tmp_path)
    rows = list(csv.DictReader(open(p)))
    rng = random.Random(SPLIT_SEED)
    sents = _draw_loosening_sentinels(
        "W-EP-01", frozenset({"W-EP-01", "COMPOUND-01"}), rows, rng, n=20
    )
    # No sentinel row should have W-EP-01 or COMPOUND-01 in rules_fired.
    by_key = {f"{r['spec_id']}|{r['variant_num']}": r for r in rows}
    for k in sents:
        r = by_key[k]
        fired = {p.strip() for p in (r.get("rules_fired") or "").split(",") if p.strip()}
        assert "W-EP-01" not in fired
        assert "COMPOUND-01" not in fired


def test_write_split_filename(tmp_path: Path):
    p = _make_synthetic_outcomes(tmp_path)
    s = build_split("W-EP-01", p, frozenset({"W-EP-01"}))
    out_dir = tmp_path / "splits"
    out_path = write_split(s, out_dir)
    assert out_path.name == "w_ep_01_split.json"
    data = json.loads(out_path.read_text())
    assert data["rule_id"] == "W-EP-01"
    assert data["seed"] == SPLIT_SEED
    assert "train" in data and "dev" in data and "holdout" in data


def test_split_keys_are_disjoint_per_population(tmp_path: Path):
    """A given (key, population) should appear in exactly one of
    train/dev/holdout."""
    p = _make_synthetic_outcomes(tmp_path, n_per_pop=50)
    s = build_split("W-EP-01", p, frozenset({"W-EP-01"}))
    for pop in ("target", "bystander", "negative"):
        union = set(s.train[pop]) | set(s.dev[pop]) | set(s.holdout[pop])
        assert (
            len(s.train[pop]) + len(s.dev[pop]) + len(s.holdout[pop])
            == len(union)
        ), f"overlap detected in population {pop}"

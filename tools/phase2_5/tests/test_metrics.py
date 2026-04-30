"""Unit tests for tools.phase2_5.metrics."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from tools.phase2_5.refinement_loop.metrics import (
    AFFECTED_RULES,
    HoldoutAlreadyComputed,
    Metrics,
    _check_holdout_lock,
    _compute_from_fired_sets,
    _splice_firings,
    compute_metrics,
)


def test_affected_rules_w_ep_01():
    """W-EP-01 (Critical) should splice into COMPOUND-01 + COMPOUND-03."""
    a = AFFECTED_RULES["W-EP-01"]
    assert "W-EP-01" in a
    assert "COMPOUND-01" in a
    assert "COMPOUND-03" in a


def test_affected_rules_w_on_02():
    """W-ON-02 (High) should splice into COMPOUND-01 only (not COMPOUND-03)."""
    a = AFFECTED_RULES["W-ON-02"]
    assert "W-ON-02" in a
    assert "COMPOUND-01" in a
    assert "COMPOUND-03" not in a


def test_affected_rules_compound_self_only():
    """COMPOUND rules don't chain into other COMPOUND rules."""
    assert AFFECTED_RULES["COMPOUND-01"] == frozenset({"COMPOUND-01"})
    assert AFFECTED_RULES["COMPOUND-03"] == frozenset({"COMPOUND-03"})


def test_holdout_lock_raises_on_second_call(tmp_path: Path):
    _check_holdout_lock("W-EP-01", "holdout", tmp_path, force=False)
    with pytest.raises(HoldoutAlreadyComputed):
        _check_holdout_lock("W-EP-01", "holdout", tmp_path, force=False)


def test_holdout_lock_force_overrides(tmp_path: Path):
    _check_holdout_lock("W-EP-01", "holdout", tmp_path, force=False)
    # Force should silently allow re-run
    _check_holdout_lock("W-EP-01", "holdout", tmp_path, force=True)


def test_holdout_lock_per_rule(tmp_path: Path):
    _check_holdout_lock("W-EP-01", "holdout", tmp_path, force=False)
    # Different rule should not be locked
    _check_holdout_lock("W-ON-02", "holdout", tmp_path, force=False)


def test_holdout_lock_skips_train_dev(tmp_path: Path):
    """Only 'holdout' triggers the lock."""
    _check_holdout_lock("W-EP-01", "train", tmp_path, force=False)
    _check_holdout_lock("W-EP-01", "dev", tmp_path, force=False)
    _check_holdout_lock("W-EP-01", "train", tmp_path, force=False)


def test_splice_firings_replaces_only_affected(tmp_path: Path):
    """Splice should replace ONLY affected rules' contributions."""
    baseline_rows = {
        "k1": {"rules_fired": "W-EP-01,W-AL-01,COMPOUND-01"},
        "k2": {"rules_fired": "W-XX-99"},
        "k3": {"rules_fired": ""},
    }
    affected = frozenset({"W-EP-01", "COMPOUND-01"})
    new_firings = {
        "k1": {"W-AL-01"},  # W-EP-01 + COMPOUND-01 dropped from rebuilt
        "k2": {"W-EP-01"},   # adds new W-EP-01 firing on a previously-clean key
    }
    out = _splice_firings(baseline_rows, affected, new_firings)
    # k1: baseline minus affected = {W-AL-01}; new ∩ affected = ∅; result = {W-AL-01}
    assert out["k1"] == {"W-AL-01"}
    # k2: baseline minus affected = {W-XX-99}; new ∩ affected = {W-EP-01}; result = {W-XX-99, W-EP-01}
    assert out["k2"] == {"W-XX-99", "W-EP-01"}
    # k3: baseline empty → result empty
    assert out["k3"] == set()


def test_compute_from_fired_sets_recall_and_fpr():
    split_keys = {
        "target": ["t1", "t2", "t3", "t4"],     # 4 targets
        "bystander": ["b1", "b2"],               # 2 bystanders
        "negative": ["n1", "n2", "n3", "n4", "n5"],  # 5 NCs
    }
    fired_sets = {
        "t1": {"W-EP-01"}, "t2": {"W-EP-01"}, "t3": {"W-EP-01"}, "t4": set(),  # 3/4 hits
        "b1": {"W-EP-01"}, "b2": set(),                                          # 1/2 hits
        "n1": {"W-EP-01"}, "n2": {"W-EP-01"}, "n3": set(), "n4": set(), "n5": set(),  # 2/5 hits
    }
    m = _compute_from_fired_sets("W-EP-01", split_keys, fired_sets, sentinels=[])
    assert m.recall == 3 / 4
    assert m.bystander_rate == 1 / 2
    assert m.nc_fpr == 2 / 5
    assert m.specificity == pytest.approx(0.6)
    # precision = 3 / (3 + 1 + 2) = 3/6 = 0.5
    assert m.precision == pytest.approx(0.5)


def test_compute_from_fired_sets_loosening_sentinels():
    split_keys = {"target": [], "bystander": [], "negative": []}
    fired_sets = {
        "s1": {"W-EP-01"}, "s2": set(), "s3": {"W-EP-01"}, "s4": set(),
    }
    m = _compute_from_fired_sets(
        "W-EP-01", split_keys, fired_sets, sentinels=["s1", "s2", "s3", "s4"],
    )
    assert m.loosening_sentinel_fires == 2


def test_compute_from_fired_sets_handles_empty_populations():
    split_keys = {"target": [], "bystander": [], "negative": []}
    m = _compute_from_fired_sets("W-EP-01", split_keys, {}, sentinels=[])
    # No division-by-zero, no NaN
    assert m.recall == 0.0
    assert m.nc_fpr == 0.0
    assert m.bystander_rate == 0.0
    assert m.precision == 0.0


def test_metrics_to_dict_rounds_floats():
    m = Metrics(
        recall=0.123456789, nc_fpr=0.987654321, bystander_rate=0.5,
        precision=0.333333, specificity=0.012345,
        n_target=10, n_bystander=5, n_negative=20,
    )
    d = m.to_dict()
    assert d["recall"] == 0.1235
    assert d["nc_fpr"] == 0.9877


def test_compute_metrics_baseline_path(tmp_path: Path):
    """End-to-end: compute_metrics with no rules_file_override reads
    baseline outcomes.csv directly."""
    # Build a minimal outcomes.csv with two targets, one bystander, two NCs.
    rows = [
        {"spec_id": "s1", "variant_num": "1", "coverage_intent": "confirm_existing",
         "target_weakener": "W-EP-01", "outcome_class": "WEAKENED",
         "rules_fired": "W-EP-01", "base_cou_key": "morrison/cou1"},
        {"spec_id": "s2", "variant_num": "1", "coverage_intent": "confirm_existing",
         "target_weakener": "W-EP-01", "outcome_class": "WEAKENED",
         "rules_fired": "W-EP-01", "base_cou_key": "morrison/cou1"},
        {"spec_id": "s3", "variant_num": "1", "coverage_intent": "confirm_existing",
         "target_weakener": "W-XX-99", "outcome_class": "WEAKENED",
         "rules_fired": "W-EP-01", "base_cou_key": "morrison/cou1"},
        {"spec_id": "s4", "variant_num": "1", "coverage_intent": "negative_control",
         "target_weakener": "", "outcome_class": "VALID",
         "rules_fired": "W-EP-01", "base_cou_key": "morrison/cou1"},
        {"spec_id": "s5", "variant_num": "1", "coverage_intent": "negative_control",
         "target_weakener": "", "outcome_class": "VALID",
         "rules_fired": "", "base_cou_key": "morrison/cou1"},
    ]
    outcomes_csv = tmp_path / "outcomes.csv"
    with open(outcomes_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow(r)

    split = {
        "rule_id": "W-EP-01",
        "train": {"target": ["s1|1", "s2|1"], "bystander": ["s3|1"], "negative": ["s4|1", "s5|1"]},
        "dev": {"target": [], "bystander": [], "negative": []},
        "holdout": {"target": [], "bystander": [], "negative": []},
        "loosening_sentinels": [],
        "seed": 1,
    }
    split_path = tmp_path / "split.json"
    split_path.write_text(json.dumps(split))

    m = compute_metrics(
        rule_id="W-EP-01", split_name="train",
        split_path=split_path, outcomes_csv=outcomes_csv,
        batch_dir=tmp_path,  # unused on baseline path
        rules_file_override=None,
        holdout_lock_dir=tmp_path / "locks",
    )
    assert m.recall == 1.0  # both targets fired
    assert m.bystander_rate == 1.0  # the bystander fired
    assert m.nc_fpr == 0.5  # 1/2 NC fired
    assert m.n_target == 2
    assert m.n_bystander == 1
    assert m.n_negative == 2

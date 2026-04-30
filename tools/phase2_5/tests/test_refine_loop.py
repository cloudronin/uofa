"""Integration test for tools.phase2_5.refine_loop with mocked Jena.

Two scenarios per the plan §A8:
- "obvious-improvement" path: every iteration's mocked metrics improve
  on the baseline → loop accepts and reports ``locked``.
- "obvious-regression" path: every iteration's mocked metrics regress
  → 3 reverts → loop reports ``refinement-stuck``.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from tools.phase2_5.refinement_loop.metrics import Metrics
from tools.phase2_5.refinement_loop.refine_loop import _replace_rule_body, run_loop


# Minimal Jena rules file used by every test
SAMPLE_RULES = """\
@prefix uofa: <http://example.com/uofa#>.

[w_ep01: (?x rdf:type uofa:Foo) -> (?x uofa:fired "true") ]

[w_on02: (?x rdf:type uofa:Bar) -> (?x uofa:other "true") ]
"""


def _write_split_for_rule(tmp_path: Path, rule_id: str) -> Path:
    """Drop a stub split JSON for *rule_id*."""
    rule_slug = rule_id.lower().replace("-", "_")
    splits_dir = tmp_path / "splits"
    splits_dir.mkdir(exist_ok=True)
    split = {
        "rule_id": rule_id,
        "train": {"target": ["t1|1"], "bystander": ["b1|1"], "negative": ["n1|1"]},
        "dev": {"target": ["t2|1"], "bystander": [], "negative": ["n2|1"]},
        "holdout": {"target": ["t3|1"], "bystander": [], "negative": ["n3|1"]},
        "loosening_sentinels": [],
        "seed": 1,
    }
    p = splits_dir / f"{rule_slug}_split.json"
    p.write_text(json.dumps(split))
    return p


def _stub_outcomes(tmp_path: Path) -> Path:
    p = tmp_path / "outcomes.csv"
    p.write_text("spec_id,variant_num,coverage_intent,target_weakener,outcome_class,rules_fired,base_cou_key\n")
    return p


def test_replace_rule_body_simple():
    new = "[w_ep01: (?x rdf:type uofa:Bar) -> (?x uofa:fired2 \"true\") ]"
    out = _replace_rule_body(SAMPLE_RULES, "w_ep01", new)
    assert "uofa:Bar" in out
    assert "uofa:Foo" not in out
    # The other rule should be untouched
    assert "[w_on02:" in out


def test_replace_rule_body_missing_raises():
    import pytest
    with pytest.raises(ValueError):
        _replace_rule_body(SAMPLE_RULES, "does_not_exist", "[xxx: -> ]")


@dataclass
class _StubProposal:
    rule_id: str
    rationale: str
    guard_added: str
    new_body: str
    diff_text: str

    def to_dict(self):
        return self.__dict__


def test_loop_accepts_obvious_improvement(tmp_path: Path):
    """Mocked metrics that improve into the target zone → loop ACCEPTs.

    Target zone is recall≥0.90 AND nc_fpr≤0.10. The first iter clears
    hard floors (nc_fpr=0.20) but is provisional; the second iter
    enters the target zone (nc_fpr=0.05) and the loop locks.
    """
    rules_file = tmp_path / "uofa_weakener.rules"
    rules_file.write_text(SAMPLE_RULES)

    split_path = _write_split_for_rule(tmp_path, "W-EP-01")

    counter = {"n": 0}

    def stub_propose(rule_id, rule_body, misfires):
        counter["n"] += 1
        new = rule_body.replace("uofa:Foo", f"uofa:FooV{counter['n']}")
        return _StubProposal(
            rule_id=rule_id, rationale=f"narrow v{counter['n']}",
            guard_added="type-narrow",
            new_body=new,
            diff_text=f"--- old\n+++ new\n@@ -1 +1 @@\n-uofa:Foo\n+uofa:FooV{counter['n']}\n",
        )

    def stub_metrics(rule_id, split_name, *, rules_file_override=None, **kwargs):
        if rules_file_override is None:
            return Metrics(
                recall=0.95, nc_fpr=0.80, bystander_rate=0.50,
                precision=0.30, specificity=0.20,
                n_target=10, n_bystander=10, n_negative=10,
            )
        # iter 1: provisional (clears 0.25 floor but above 0.10 target)
        # iter 2: target zone reached
        n = counter["n"]
        nc_fpr_seq = [0.20, 0.05, 0.02]
        nc_fpr = nc_fpr_seq[min(n - 1, len(nc_fpr_seq) - 1)]
        return Metrics(
            recall=0.92, nc_fpr=nc_fpr,
            bystander_rate=0.05,
            precision=0.30 + 0.10 * n, specificity=1 - nc_fpr,
            n_target=10, n_bystander=10, n_negative=10,
        )

    def stub_inspect(rule_id, outcomes_csv, batch_dir, **kwargs):
        return {"rule_id": rule_id, "nc_misfires": [], "bystander_misfires": []}

    summary = run_loop(
        rule_id="W-EP-01",
        rules_file=rules_file,
        split_path=split_path,
        outcomes_csv=_stub_outcomes(tmp_path),
        batch_dir=tmp_path,
        log_path=tmp_path / "log.jsonl",
        diff_dir=tmp_path / "diffs",
        holdout_lock_dir=tmp_path / "locks",
        max_iterations=5,
        propose_fn=stub_propose,
        metrics_fn=stub_metrics,
        inspect_fn=stub_inspect,
    )
    assert summary["final_state"] == "locked"
    assert len(summary["accepted_iterations"]) >= 1
    # The rules file should have the latest accepted body's marker.
    assert "uofa:FooV" in rules_file.read_text()


def test_loop_provisional_caps_at_max_iter(tmp_path: Path):
    """Mocked metrics that clear hard floors but never reach target zone.

    Loop should run to max_iterations, applying each provisional change
    but never locking. Final state = target-zone-not-reached.
    """
    rules_file = tmp_path / "uofa_weakener.rules"
    rules_file.write_text(SAMPLE_RULES)
    split_path = _write_split_for_rule(tmp_path, "W-EP-01")

    counter = {"n": 0}

    def stub_propose(rule_id, rule_body, misfires):
        counter["n"] += 1
        new = rule_body.replace("uofa:Foo", f"uofa:FooV{counter['n']}")
        return _StubProposal(
            rule_id=rule_id, rationale=f"v{counter['n']}", guard_added="x",
            new_body=new,
            diff_text=f"@@ -1 +1 @@\n-uofa:Foo\n+uofa:FooV{counter['n']}\n",
        )

    def stub_metrics(rule_id, split_name, *, rules_file_override=None, **kwargs):
        if rules_file_override is None:
            return Metrics(recall=0.95, nc_fpr=0.80, bystander_rate=0.50,
                           precision=0.30, specificity=0.20,
                           n_target=10, n_bystander=10, n_negative=10)
        # All provisional: nc_fpr hangs at 0.18 (clears 0.25 floor, above 0.10 target)
        return Metrics(recall=0.92, nc_fpr=0.18, bystander_rate=0.05,
                       precision=0.50, specificity=0.82,
                       n_target=10, n_bystander=10, n_negative=10)

    def stub_inspect(rule_id, outcomes_csv, batch_dir, **kwargs):
        return {"rule_id": rule_id, "nc_misfires": [], "bystander_misfires": []}

    summary = run_loop(
        rule_id="W-EP-01",
        rules_file=rules_file,
        split_path=split_path,
        outcomes_csv=_stub_outcomes(tmp_path),
        batch_dir=tmp_path,
        log_path=tmp_path / "log.jsonl",
        diff_dir=tmp_path / "diffs",
        holdout_lock_dir=tmp_path / "locks",
        max_iterations=3,
        propose_fn=stub_propose,
        metrics_fn=stub_metrics,
        inspect_fn=stub_inspect,
    )
    assert summary["final_state"] == "target-zone-not-reached"
    # No iterations should be in accepted_iterations (provisional, not accepted)
    assert len(summary["accepted_iterations"]) == 0


def test_loop_marks_stuck_after_three_reverts(tmp_path: Path):
    """Mocked metrics that always regress → loop hits stuck after 3 reverts."""
    rules_file = tmp_path / "uofa_weakener.rules"
    rules_file.write_text(SAMPLE_RULES)
    original = rules_file.read_text()
    split_path = _write_split_for_rule(tmp_path, "W-EP-01")

    counter = {"n": 0}

    def stub_propose(rule_id, rule_body, misfires):
        counter["n"] += 1
        new = rule_body.replace("uofa:Foo", f"uofa:FooV{counter['n']}")
        return _StubProposal(
            rule_id=rule_id, rationale=f"v{counter['n']}",
            guard_added="bad", new_body=new,
            diff_text="--- old\n+++ new\n@@ -1 +1 @@\n-uofa:Foo\n+uofa:FooV%d\n" % counter["n"],
        )

    def stub_metrics(rule_id, split_name, *, rules_file_override=None, **kwargs):
        if rules_file_override is None:
            return Metrics(
                recall=0.95, nc_fpr=0.20, bystander_rate=0.10,
                precision=0.80, specificity=0.80,
                n_target=10, n_bystander=10, n_negative=10,
            )
        # All overrides regress NC FPR (worse than baseline 0.20)
        return Metrics(
            recall=0.95, nc_fpr=0.50, bystander_rate=0.10,
            precision=0.50, specificity=0.50,
            n_target=10, n_bystander=10, n_negative=10,
        )

    def stub_inspect(rule_id, outcomes_csv, batch_dir, **kwargs):
        return {"rule_id": rule_id, "nc_misfires": [], "bystander_misfires": []}

    summary = run_loop(
        rule_id="W-EP-01",
        rules_file=rules_file,
        split_path=split_path,
        outcomes_csv=_stub_outcomes(tmp_path),
        batch_dir=tmp_path,
        log_path=tmp_path / "log.jsonl",
        diff_dir=tmp_path / "diffs",
        holdout_lock_dir=tmp_path / "locks",
        max_iterations=5,
        propose_fn=stub_propose,
        metrics_fn=stub_metrics,
        inspect_fn=stub_inspect,
    )
    assert summary["final_state"] == "refinement-stuck"
    assert len(summary["accepted_iterations"]) == 0
    # Rules file should be UNCHANGED (loop never accepted)
    assert rules_file.read_text() == original


def test_loop_logs_each_iteration(tmp_path: Path):
    """Every iteration writes to refinement_log.jsonl regardless of outcome."""
    rules_file = tmp_path / "uofa_weakener.rules"
    rules_file.write_text(SAMPLE_RULES)
    split_path = _write_split_for_rule(tmp_path, "W-EP-01")
    log_path = tmp_path / "log.jsonl"

    counter = {"n": 0}

    def stub_propose(rule_id, rule_body, misfires):
        counter["n"] += 1
        new = rule_body.replace("uofa:Foo", f"uofa:V{counter['n']}")
        return _StubProposal(
            rule_id=rule_id, rationale=f"v{counter['n']}",
            guard_added="x", new_body=new,
            diff_text=f"@@ -1 +1 @@\n-uofa:Foo\n+uofa:V{counter['n']}\n",
        )

    def stub_metrics(rule_id, split_name, *, rules_file_override=None, **kwargs):
        return Metrics(recall=0.95, nc_fpr=0.50, bystander_rate=0.40,
                       precision=0.50, specificity=0.50,
                       n_target=10, n_bystander=10, n_negative=10)

    def stub_inspect(rule_id, outcomes_csv, batch_dir, **kwargs):
        return {"rule_id": rule_id, "nc_misfires": [], "bystander_misfires": []}

    run_loop(
        rule_id="W-EP-01",
        rules_file=rules_file,
        split_path=split_path,
        outcomes_csv=_stub_outcomes(tmp_path),
        batch_dir=tmp_path,
        log_path=log_path,
        diff_dir=tmp_path / "diffs",
        holdout_lock_dir=tmp_path / "locks",
        max_iterations=3,
        propose_fn=stub_propose,
        metrics_fn=stub_metrics,
        inspect_fn=stub_inspect,
    )
    # Should have at least 3 iterations logged
    lines = [ln for ln in log_path.read_text().splitlines() if ln.strip()]
    assert len(lines) >= 3
    # Every record should have the SHA fields
    for ln in lines:
        rec = json.loads(ln)
        assert rec["predicate_before_sha"].startswith("sha256:")
        assert rec["predicate_after_sha"].startswith("sha256:")

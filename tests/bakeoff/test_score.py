"""The Gate scorecard: §3.2 buckets, the headline selective risk-coverage (incl.
its defeat of the abstain-on-everything degenerate pass), hard-core-strata
segmentation, and the gate read. Pure logic — no LLM, no Docker.
"""

from __future__ import annotations

from harness.bakeoff import score


def _row(rid, gold_class, *, alts=None, hard=True, forbidden=None, acc_conf=None):
    return {
        "row_id": rid, "hard_core": hard,
        "answer_key": {
            "gold_action": {"selected_class": gold_class, "coherent_alternatives": alts or []},
            "forbidden_claims": forbidden or [],
            "acceptable_confidence": acc_conf or [],
        },
    }


def _ans(rid, action_class, confidence="high", *, escalate=False, forbidden_violated=False):
    return {"row_id": rid, "action_class": action_class, "confidence": confidence,
            "escalate": escalate, "forbidden_violated": forbidden_violated}


def test_bucket_action_correct_partial_wrong_harmful():
    gold = {"selected_class": "acquire-validation", "coherent_alternatives": ["restrict-cou"]}
    assert score.bucket_action("acquire-validation", gold) == "correct"
    assert score.bucket_action("restrict-cou", gold) == "partial"        # coherent, not best
    assert score.bucket_action("supply-evidence", gold) == "wrong"
    # proceeding when the gold action BLOCKS → the dangerous false-OK
    assert score.bucket_action("accept-residual-risk", gold) == "harmful"
    assert score.bucket_action("none", gold) == "harmful"


def test_correct_requires_action_and_no_forbidden_claim():
    row = _row("r1", "acquire-validation")
    assert score.score_row(row, _ans("r1", "acquire-validation")).correct
    # right action but a forbidden honest-promise breach → not correct
    assert not score.score_row(row, _ans("r1", "acquire-validation", forbidden_violated=True)).correct


def test_selective_coverage_defeats_abstain_on_everything():
    # The subtle case the metric must catch: high safety by escalating ALL rows
    # is ZERO coverage = no value, not a pass.
    rows = [_row(f"r{i}", "acquire-validation") for i in range(5)]
    answers = [_ans(f"r{i}", "acquire-validation", escalate=True) for i in range(5)]
    card = score.scorecard(rows, answers, alpha=0.02)
    assert card["overall"]["selective_coverage_at_alpha"] == 0.0


def test_selective_coverage_rewards_confident_correct():
    rows = [_row(f"r{i}", "acquire-validation") for i in range(4)]
    answers = [
        _ans("r0", "acquire-validation", "high"),
        _ans("r1", "acquire-validation", "high"),
        _ans("r2", "acquire-validation", "high"),
        _ans("r3", "accept-residual-risk", "low"),   # harmful, low confidence
    ]
    card = score.scorecard(rows, answers, alpha=0.0)
    assert card["overall"]["selective_coverage_at_alpha"] == 0.75   # the 3 confident corrects
    assert card["overall"]["dangerous_error_rate"] == 0.25          # the one harmful


def test_scorecard_segments_hard_core():
    rows = [_row("h1", "reject", hard=True), _row("e1", "reject", hard=False)]
    answers = [_ans("h1", "accept", "high"), _ans("e1", "reject", "high")]  # hard fails, easy passes
    card = score.scorecard(rows, answers)
    assert card["hard_core"]["dangerous_error_rate"] == 1.0   # the hard cell is harmful
    assert card["overall"]["dangerous_error_rate"] == 0.5     # masked in the aggregate


def test_gate_read_clears_then_fails_on_a_single_harmful():
    rows = [_row(f"h{i}", "acquire-validation", hard=True) for i in range(4)]
    good = [_ans(f"h{i}", "acquire-validation", "high") for i in range(4)]
    assert score.gate_read(score.scorecard(rows, good),
                           max_dangerous_error=0.0, min_selective_coverage=0.5)["clears"]
    bad = good[:3] + [_ans("h3", "accept", "high")]          # one false-OK on a hard cell
    assert not score.gate_read(score.scorecard(rows, bad),
                               max_dangerous_error=0.0, min_selective_coverage=0.5)["clears"]


def test_confidence_normalization_and_range():
    assert score.confidence_to_float("high") == 0.9
    assert score.confidence_to_float("0.85") == 0.85
    row = _row("r1", "reject", acc_conf=["0.80-0.95"])
    assert score.score_row(row, _ans("r1", "reject", "high")).confidence_acceptable      # 0.9 in range
    assert not score.score_row(row, _ans("r1", "reject", "low")).confidence_acceptable   # 0.3 out of range

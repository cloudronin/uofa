"""Tests for majority-of-3 triage bucketing (spec §10.1)."""

from __future__ import annotations

import pytest

from uofa_cli.adversarial.judge.providers.base import Judgment
from uofa_cli.adversarial.judge.triage import (
    DEFAULT_CONFIDENCE_FLOOR,
    TriageBucket,
    align_trios,
    triage_case,
    triage_corpus,
)


def _j(case_id: str, verdict: str, confidence: float = 0.85) -> Judgment:
    """Construct a minimal Judgment for triage tests."""
    return Judgment(
        case_id=case_id,
        verdict=verdict,
        confidence=confidence,
        reasoning_steps={
            "source_taxonomy_identified": "x" * 10,
            "target_rule_identified": "x" * 5,
            "rule_firings_inspected": "x" * 10,
            "instantiation_check": "x" * 20,
            "verdict_commitment": verdict,
        },
        reasoning="x" * 50,
        section_6_7_candidate=None,
        alternative_rule_analysis=None,
        prompt_template_version="v0.0.0-stub",
        judge_model="mock",
        judge_thinking_enabled=False,
        judge_model_params={"temperature": 0.0, "seed": 42},
        generator_provenance={"generator_model": "mock", "temperature": None, "seed": None},
    )


# ── triage_case (single trio) ──────────────────────────────────────────


class TestTriageCaseConvergent:
    def test_three_judges_agree_high_conf(self) -> None:
        a = _j("c1", "REAL-GAP", 0.9)
        b = _j("c1", "REAL-GAP", 0.85)
        c = _j("c1", "REAL-GAP", 0.8)
        e = triage_case(a, b, c)
        assert e.bucket == TriageBucket.CONVERGENT
        assert e.majority_verdict == "REAL-GAP"
        assert "convergent_3of3" in e.disagreement_type

    def test_two_judges_agree_high_conf(self) -> None:
        a = _j("c1", "REAL-GAP", 0.9)
        b = _j("c1", "REAL-GAP", 0.85)
        c = _j("c1", "GENERATOR-ARTIFACT", 0.7)
        e = triage_case(a, b, c)
        assert e.bucket == TriageBucket.CONVERGENT
        assert e.majority_verdict == "REAL-GAP"
        assert "convergent_2of3" in e.disagreement_type


class TestTriageCaseDivergent:
    def test_all_three_disagree(self) -> None:
        a = _j("c1", "REAL-GAP", 0.85)
        b = _j("c1", "GENERATOR-ARTIFACT", 0.85)
        c = _j("c1", "OUT-OF-SCOPE", 0.85)
        e = triage_case(a, b, c)
        assert e.bucket == TriageBucket.DIVERGENT
        assert e.majority_verdict is None
        assert e.disagreement_type == "all_three_disagree"

    def test_two_disagree_one_uncertain(self) -> None:
        a = _j("c1", "REAL-GAP", 0.85)
        b = _j("c1", "GENERATOR-ARTIFACT", 0.85)
        c = _j("c1", "UNCERTAIN", 0.85)
        e = triage_case(a, b, c)
        assert e.bucket == TriageBucket.DIVERGENT
        assert e.disagreement_type == "two_disagree_one_uncertain"

    def test_low_confidence_concurrence_routes_to_divergent(self) -> None:
        # Two agree on REAL-GAP but one is below confidence floor.
        a = _j("c1", "REAL-GAP", 0.9)
        b = _j("c1", "REAL-GAP", 0.4)  # below floor
        c = _j("c1", "GENERATOR-ARTIFACT", 0.85)
        e = triage_case(a, b, c)
        assert e.bucket == TriageBucket.DIVERGENT
        assert e.majority_verdict is None
        assert "low_conf_concurrence" in e.disagreement_type


class TestTriageCaseUncertain:
    def test_two_uncertain_majority(self) -> None:
        a = _j("c1", "REAL-GAP", 0.9)
        b = _j("c1", "UNCERTAIN", 0.85)
        c = _j("c1", "UNCERTAIN", 0.85)
        e = triage_case(a, b, c)
        assert e.bucket == TriageBucket.UNCERTAIN
        assert e.majority_verdict == "UNCERTAIN"
        assert "uncertain_majority_2of3" in e.disagreement_type

    def test_three_uncertain_majority(self) -> None:
        a = _j("c1", "UNCERTAIN", 0.9)
        b = _j("c1", "UNCERTAIN", 0.85)
        c = _j("c1", "UNCERTAIN", 0.85)
        e = triage_case(a, b, c)
        assert e.bucket == TriageBucket.UNCERTAIN
        assert "uncertain_majority_3of3" in e.disagreement_type


class TestTriageCaseEdges:
    def test_mismatched_case_ids_raises(self) -> None:
        a = _j("c1", "REAL-GAP")
        b = _j("c2", "REAL-GAP")
        c = _j("c1", "REAL-GAP")
        with pytest.raises(ValueError, match="mismatched case ids"):
            triage_case(a, b, c)

    def test_custom_confidence_floor(self) -> None:
        # Floor 0.5: a 0.4-confidence agreeing judge still triggers DIVERGENT.
        a = _j("c1", "REAL-GAP", 0.9)
        b = _j("c1", "REAL-GAP", 0.4)
        c = _j("c1", "GENERATOR-ARTIFACT", 0.9)
        e = triage_case(a, b, c, confidence_floor=0.5)
        assert e.bucket == TriageBucket.DIVERGENT
        # Floor 0.3: 0.4 ≥ 0.3 → CONVERGENT
        e2 = triage_case(a, b, c, confidence_floor=0.3)
        assert e2.bucket == TriageBucket.CONVERGENT


# ── triage_corpus ───────────────────────────────────────────────────────


class TestTriageCorpus:
    def test_bucket_counts_aggregate(self) -> None:
        trios = [
            (_j("c1", "REAL-GAP"), _j("c1", "REAL-GAP"), _j("c1", "REAL-GAP")),
            (_j("c2", "REAL-GAP"), _j("c2", "GEN-INVALID"), _j("c2", "OUT-OF-SCOPE"))
            if False else
            (_j("c2", "REAL-GAP"), _j("c2", "GENERATOR-ARTIFACT"), _j("c2", "OUT-OF-SCOPE")),
            (_j("c3", "UNCERTAIN"), _j("c3", "UNCERTAIN"), _j("c3", "REAL-GAP")),
        ]
        result = triage_corpus(trios)
        assert result.bucket_counts[TriageBucket.CONVERGENT] == 1
        assert result.bucket_counts[TriageBucket.DIVERGENT] == 1
        assert result.bucket_counts[TriageBucket.UNCERTAIN] == 1
        assert len(result.entries) == 3

    def test_default_confidence_floor_value(self) -> None:
        assert DEFAULT_CONFIDENCE_FLOOR == 0.6


# ── align_trios ─────────────────────────────────────────────────────────


class TestAlignTrios:
    def test_aligns_by_case_id(self) -> None:
        a = [_j("c1", "REAL-GAP"), _j("c2", "REAL-GAP")]
        b = [_j("c2", "REAL-GAP"), _j("c1", "REAL-GAP")]  # different order
        c = [_j("c1", "REAL-GAP"), _j("c2", "REAL-GAP")]
        trios = align_trios(a, b, c)
        assert len(trios) == 2
        # Output is sorted by case_id.
        assert trios[0][0].case_id == "c1"
        assert trios[1][0].case_id == "c2"

    def test_drops_cases_missing_from_any_judge(self) -> None:
        a = [_j("c1", "REAL-GAP"), _j("c2", "REAL-GAP"), _j("c3", "REAL-GAP")]
        b = [_j("c1", "REAL-GAP"), _j("c2", "REAL-GAP")]  # missing c3
        c = [_j("c1", "REAL-GAP"), _j("c2", "REAL-GAP"), _j("c3", "REAL-GAP")]
        trios = align_trios(a, b, c)
        # c3 is missing from B → dropped.
        case_ids = {t[0].case_id for t in trios}
        assert case_ids == {"c1", "c2"}

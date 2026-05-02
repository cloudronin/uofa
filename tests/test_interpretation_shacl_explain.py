"""Tests for the shacl `--explain` extension (P-K / v0.6.2).

Same explain function, third code path: when command='shacl' the
function operates on ViolationContext objects and renders the
shacl-specific template.
"""

from __future__ import annotations

import json

from uofa_cli.interpretation import (
    InterpretationOptions,
    interpret_shacl_output,
)
from uofa_cli.llm import MockBackend


def _shacl_canned() -> str:
    return json.dumps({
        "patternId": "ignored-by-normalization",
        "severity": "High",
        "affected_evidence_summary": "Shacl-mock evidence summary.",
        "gap_description": "Shacl-mock gap description.",
        "relevance_to_cou": "Shacl-mock relevance.",
    })


# ── Routing: shacl command goes through the violation path ────


class TestShaclRouting:
    def test_violations_produce_explanations(self):
        backend = MockBackend(default_response=_shacl_canned())
        violations = [
            {"path": "uofa:hasContextOfUse", "severity": "High",
             "focus_node": "ex:pkg1", "fix_suggestion": "Add a Context of Use."},
            {"path": "uofa:hasCredibilityFactor", "severity": "Medium",
             "focus_node": "ex:pkg1", "fix_suggestion": "Add at least one factor."},
        ]
        env = interpret_shacl_output(
            structured_output={"violations": violations},
            violations=violations,
            options=InterpretationOptions(backend=backend, pack_name="vv40"),
        )
        assert "explain" in env.interpretation.functions_run
        assert len(env.interpretation.explanations) == 2
        # patternId field carries the constraint path (authoritative)
        pids = [e["patternId"] for e in env.interpretation.explanations]
        assert "uofa:hasContextOfUse" in pids
        assert "uofa:hasCredibilityFactor" in pids

    def test_no_violations_produces_no_explanations(self):
        backend = MockBackend(default_response=_shacl_canned())
        env = interpret_shacl_output(
            structured_output={"violations": []},
            violations=[],
            options=InterpretationOptions(backend=backend, pack_name="vv40"),
        )
        assert env.interpretation.explanations == []
        assert backend.calls == []

    def test_constraint_path_used_as_pattern_id(self):
        """The model's `patternId` echo is discarded; we use the
        ViolationContext's constraint_path. Closes the same hallucination
        class as the rules path."""
        backend = MockBackend(default_response=json.dumps({
            "patternId": "BOGUS-MODEL-ECHO",
            "severity": "Bogus-too",
            "affected_evidence_summary": "x",
            "gap_description": "y",
            "relevance_to_cou": "z",
        }))
        violations = [{"path": "uofa:hash", "severity": "Critical",
                       "focus_node": "ex:pkg", "fix_suggestion": "sign it"}]
        env = interpret_shacl_output(
            structured_output={"violations": violations},
            violations=violations,
            options=InterpretationOptions(backend=backend, pack_name="vv40"),
        )
        e = env.interpretation.explanations[0]
        assert e["patternId"] == "uofa:hash"
        assert e["severity"] == "Critical"


# ── Spec §2.6 applicability for shacl ─────────────────────


class TestShaclApplicability:
    def test_explain_runs(self):
        backend = MockBackend(default_response=_shacl_canned())
        violations = [{"path": "uofa:hash", "severity": "Critical",
                       "focus_node": "ex:pkg"}]
        env = interpret_shacl_output(
            structured_output={"violations": violations},
            violations=violations,
            options=InterpretationOptions(backend=backend, pack_name="vv40"),
        )
        assert "explain" in env.interpretation.functions_run

    def test_group_and_contextualize_also_run(self):
        """Per spec §2.6, group + contextualize also apply to shacl. They
        ship templates in P-K alongside explain."""
        backend = MockBackend(default_response=json.dumps({
            "groupings": [],
            "contextual_severity": {},
            "patternId": "x", "severity": "x",
            "affected_evidence_summary": "x", "gap_description": "y", "relevance_to_cou": "z",
        }))
        violations = [{"path": "uofa:hash", "severity": "Critical",
                       "focus_node": "ex:pkg"}]
        env = interpret_shacl_output(
            structured_output={"violations": violations},
            violations=violations,
            options=InterpretationOptions(backend=backend, pack_name="vv40"),
        )
        # All three shacl functions should be in the run list
        for name in ("explain", "group", "contextualize"):
            assert name in env.interpretation.functions_run


# ── max_items truncation ──────────────────────────────────


class TestMaxItems:
    def test_max_items_truncates(self):
        backend = MockBackend(default_response=_shacl_canned())
        violations = [
            {"path": f"uofa:p{i}", "severity": "High", "focus_node": "ex:n"}
            for i in range(5)
        ]
        env = interpret_shacl_output(
            structured_output={"violations": violations},
            violations=violations,
            options=InterpretationOptions(
                backend=backend, max_items=2, pack_name="vv40", functions=["explain"],
            ),
        )
        assert len(env.interpretation.explanations) == 2

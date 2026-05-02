"""Tests for the diff `--explain` extension (P-J / v0.6.1).

Same explain function, different code path: when command='diff' the
function operates on DifferenceContext objects and renders the
diff-specific template.
"""

from __future__ import annotations

import json

import pytest

from uofa_cli.interpretation import (
    InterpretationOptions,
    interpret_diff_output,
    interpret_rules_output,
)
from uofa_cli.interpretation.context import (
    CouContext,
    DifferenceContext,
    PackContext,
)
from uofa_cli.llm import MockBackend


def _diff_canned() -> str:
    return json.dumps({
        "patternId": "MOCK",
        "severity": "High",
        "affected_evidence_summary": "Diff-mock evidence summary.",
        "gap_description": "Diff-mock gap description.",
        "relevance_to_cou": "Diff-mock relevance.",
    })


# ── Routing: diff command goes through the diff path ──────


class TestDiffRouting:
    def test_diff_runs_explain(self):
        backend = MockBackend(default_response=_diff_canned())
        env = interpret_diff_output(
            structured_output={},
            only_a=["W-AR-02"], only_b=[],
            weakeners_a=[{"patternId": "W-AR-02", "severity": "High",
                          "description": "Rebutting Defeater"}],
            weakeners_b=[],
            cou_identity_a={"cou_name": "COU1", "device_class": "Class II", "model_risk_level": "MRL 2"},
            cou_identity_b={"cou_name": "COU2", "device_class": "Class III", "model_risk_level": "MRL 5"},
            options=InterpretationOptions(backend=backend, pack_name="vv40"),
        )
        assert "explain" in env.interpretation.functions_run
        assert len(env.interpretation.explanations) == 1
        e = env.interpretation.explanations[0]
        assert e["patternId"] == "W-AR-02"
        assert e["severity"] == "High"
        assert e["affected_evidence_summary"] == "Diff-mock evidence summary."

    def test_diff_handles_only_b(self):
        """A pattern firing only in B should also produce an explanation."""
        backend = MockBackend(default_response=_diff_canned())
        env = interpret_diff_output(
            structured_output={},
            only_a=[], only_b=["W-EP-04"],
            weakeners_a=[],
            weakeners_b=[{"patternId": "W-EP-04", "severity": "High",
                          "description": "Unassessed Factor"}],
            cou_identity_a={"cou_name": "COU1"},
            cou_identity_b={"cou_name": "COU2"},
            options=InterpretationOptions(backend=backend, pack_name="vv40"),
        )
        assert len(env.interpretation.explanations) == 1
        assert env.interpretation.explanations[0]["patternId"] == "W-EP-04"

    def test_diff_with_no_divergence_skipped(self):
        """No divergent patterns → no contexts → no LLM calls."""
        backend = MockBackend(default_response=_diff_canned())
        env = interpret_diff_output(
            structured_output={},
            only_a=[], only_b=[],
            weakeners_a=[], weakeners_b=[],
            cou_identity_a={}, cou_identity_b={},
            options=InterpretationOptions(backend=backend, pack_name="vv40"),
        )
        assert env.interpretation.explanations == []
        assert backend.calls == []

    def test_diff_does_not_run_group_contextualize_or_cross(self):
        """Spec §2.6: only explain applies to diff."""
        backend = MockBackend(default_response=_diff_canned())
        env = interpret_diff_output(
            structured_output={},
            only_a=["W-X"], only_b=[],
            weakeners_a=[{"patternId": "W-X", "severity": "High"}],
            weakeners_b=[],
            cou_identity_a={"cou_name": "A"},
            cou_identity_b={"cou_name": "B"},
            options=InterpretationOptions(backend=backend, pack_name="vv40"),
        )
        assert env.interpretation.functions_run == ["explain"]


# ── Identifier hardening (mirrors rules path) ──────────────


class TestIdentifierHallucination:
    def test_diff_pattern_id_uses_ctx_not_model_echo(self):
        backend = MockBackend(default_response=json.dumps({
            "patternId": "TOTALLY-WRONG",
            "severity": "Bogus",
            "affected_evidence_summary": "x",
            "gap_description": "y",
            "relevance_to_cou": "z",
        }))
        env = interpret_diff_output(
            structured_output={},
            only_a=["W-AR-02"], only_b=[],
            weakeners_a=[{"patternId": "W-AR-02", "severity": "High"}],
            weakeners_b=[],
            cou_identity_a={"cou_name": "A"},
            cou_identity_b={"cou_name": "B"},
            options=InterpretationOptions(backend=backend, pack_name="vv40"),
        )
        e = env.interpretation.explanations[0]
        # Identifier comes from ctx (real patternId), not model echo
        assert e["patternId"] == "W-AR-02"
        assert e["severity"] == "High"
        # Prose comes from model
        assert e["affected_evidence_summary"] == "x"


# ── max_items truncation ──────────────────────────────────


class TestMaxItems:
    def test_diff_max_items_truncates_by_severity(self):
        backend = MockBackend(default_response=_diff_canned())
        env = interpret_diff_output(
            structured_output={},
            only_a=["W-CRIT", "W-HIGH-1", "W-HIGH-2", "W-LOW"],
            only_b=[],
            weakeners_a=[
                {"patternId": "W-CRIT", "severity": "Critical"},
                {"patternId": "W-HIGH-1", "severity": "High"},
                {"patternId": "W-HIGH-2", "severity": "High"},
                {"patternId": "W-LOW", "severity": "Low"},
            ],
            weakeners_b=[],
            cou_identity_a={}, cou_identity_b={},
            options=InterpretationOptions(backend=backend, max_items=2, pack_name="vv40"),
        )
        # 2 explanations (top by severity rank)
        assert len(env.interpretation.explanations) == 2
        pids = [e["patternId"] for e in env.interpretation.explanations]
        # Critical first, then a High (alphabetical tiebreak)
        assert "W-CRIT" in pids
        assert "W-HIGH-1" in pids


# ── Rules path still works (regression) ──────────────────


class TestRulesPathUnchanged:
    def test_rules_command_still_uses_firing_path(self):
        """Adding diff to the @applies_to_commands list must NOT change
        rules behavior. Sanity: firing context produces a normal
        explanation."""
        backend = MockBackend(default_response=json.dumps({
            "patternId": "W-EP-04", "severity": "High",
            "affected_evidence_summary": "rules path",
            "gap_description": "g", "relevance_to_cou": "r",
        }))
        firings = [{"patternId": "W-EP-04", "severity": "High", "hits": 1}]
        env = interpret_rules_output(
            structured_output={"firings": firings},
            package_doc={},
            firings=firings,
            options=InterpretationOptions(backend=backend, pack_name="vv40", functions=["explain"]),
        )
        assert env.interpretation.explanations[0]["affected_evidence_summary"] == "rules path"

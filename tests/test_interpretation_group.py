"""Tests for the grouping/clustering function (P-F, spec §2.2).

Mock-driven tests verify the function's wiring: prompt rendering picks
up firing labels, output normalization converts the model's list form
to the envelope's dict form, command-applicability filter behaves per
spec §2.6 matrix.
"""

from __future__ import annotations

import json

import pytest

from uofa_cli.interpretation import (
    InterpretationOptions,
    interpret_check_output,
    interpret_diff_output,
    interpret_rules_output,
    interpret_shacl_output,
)
from uofa_cli.interpretation.context import (
    CouContext,
    FiringContext,
    PackContext,
)
from uofa_cli.interpretation.functions.group import (
    _render_firings_block,
    _top_n,
)
from uofa_cli.llm import MockBackend


def _grouping_response(*groupings: dict) -> str:
    """Build a canned grouping response wrapping the model's output shape."""
    return json.dumps({"groupings": list(groupings)})


# ── Output shape: list → dict normalization ────────────────


class TestOutputNormalization:
    def test_list_form_converted_to_dict_keyed_by_name(self):
        backend = MockBackend(default_response=_grouping_response(
            {"name": "Provenance gaps", "kind": "conceptual",
             "members": ["W-PROV-01", "W-EP-02"], "rationale": "shared issue"},
            {"name": "Unassessed factors", "kind": "same-pattern",
             "members": ["W-EP-04"], "rationale": "same patternId, six hits"},
        ))
        firings = [
            {"patternId": "W-PROV-01", "severity": "Critical", "hits": 7},
            {"patternId": "W-EP-02", "severity": "High", "hits": 3},
            {"patternId": "W-EP-04", "severity": "High", "hits": 6},
        ]
        env = interpret_rules_output(
            structured_output={"firings": firings}, package_doc={},
            firings=firings,
            options=InterpretationOptions(backend=backend, pack_name="vv40", functions=["group"]),
        )
        groupings = env.interpretation.groupings
        assert isinstance(groupings, dict)
        assert "Provenance gaps" in groupings
        assert groupings["Provenance gaps"]["kind"] == "conceptual"
        assert groupings["Provenance gaps"]["members"] == ["W-PROV-01", "W-EP-02"]
        assert "shared" in groupings["Provenance gaps"]["rationale"]

    def test_empty_response_yields_empty_groupings(self):
        backend = MockBackend(default_response=_grouping_response())
        firings = [{"patternId": "W-X", "severity": "Low", "hits": 1}]
        env = interpret_rules_output(
            structured_output={"firings": firings}, package_doc={},
            firings=firings,
            options=InterpretationOptions(backend=backend, pack_name="vv40", functions=["group"]),
        )
        assert env.interpretation.groupings == {}

    def test_unnamed_group_skipped(self):
        """Defensive: model that returns a grouping without a name should
        be silently dropped (vs crashing the envelope construction)."""
        backend = MockBackend(default_response=json.dumps({
            "groupings": [
                {"name": "", "members": ["W-X"], "rationale": "no name"},
                {"name": "Real cluster", "members": ["W-Y"], "rationale": "ok"},
            ],
        }))
        firings = [{"patternId": "W-X", "severity": "High", "hits": 1}]
        env = interpret_rules_output(
            structured_output={"firings": firings}, package_doc={},
            firings=firings,
            options=InterpretationOptions(backend=backend, pack_name="vv40", functions=["group"]),
        )
        assert "Real cluster" in env.interpretation.groupings
        assert "" not in env.interpretation.groupings


# ── Single LLM call (not per-firing) ───────────────────────


class TestSingleCall:
    def test_one_call_regardless_of_firing_count(self):
        """Group function makes ONE LLM call per command, NOT one per
        firing. Six firings → one call. (explain is the per-firing one.)"""
        backend = MockBackend(default_response=_grouping_response())
        firings = [
            {"patternId": f"W-{i}", "severity": "High", "hits": 1}
            for i in range(6)
        ]
        interpret_rules_output(
            structured_output={"firings": firings}, package_doc={},
            firings=firings,
            options=InterpretationOptions(backend=backend, pack_name="vv40", functions=["group"]),
        )
        # Exactly one LLM call (not 6)
        non_streaming = [c for c in backend.calls if c[0] in ("generate", "generate_structured")]
        assert len(non_streaming) == 1


# ── Spec §2.6 applicability ────────────────────────────────


class TestApplicability:
    def test_runs_on_rules(self):
        backend = MockBackend(default_response=_grouping_response())
        firings = [{"patternId": "W-X", "severity": "High", "hits": 1}]
        env = interpret_rules_output(
            structured_output={"firings": firings}, package_doc={},
            firings=firings,
            options=InterpretationOptions(backend=backend, pack_name="vv40"),
        )
        assert "group" in env.interpretation.functions_run

    def test_runs_on_check(self):
        backend = MockBackend(default_response=_grouping_response())
        firings = [{"patternId": "W-X", "severity": "High", "hits": 1}]
        env = interpret_check_output(
            structured_output={"rules": firings}, package_doc={},
            rules_firings=firings,
            options=InterpretationOptions(backend=backend, pack_name="vv40"),
        )
        assert "group" in env.interpretation.functions_run

    def test_skips_on_diff(self):
        """Per spec §2.6: diff supports only explain, not group."""
        backend = MockBackend(default_response=_grouping_response())
        env = interpret_diff_output(
            structured_output={}, only_a=["W-X"], only_b=[],
            weakeners_a=[{"patternId": "W-X", "severity": "High"}], weakeners_b=[],
            cou_identity_a={}, cou_identity_b={},
            options=InterpretationOptions(backend=backend, pack_name="vv40"),
        )
        assert "group" not in env.interpretation.functions_run

    def test_runs_on_shacl_but_skips_without_template(self):
        """Per spec §2.6 group applies to shacl, but the shacl/group
        template doesn't ship until P-K. Until then the function should
        return empty rather than try to render rules/group.jinja2 against
        violations."""
        backend = MockBackend(default_response=_grouping_response())
        violations = [{"path": "uofa:hasContextOfUse", "severity": "High"}]
        env = interpret_shacl_output(
            structured_output={"violations": violations},
            violations=violations,
            options=InterpretationOptions(backend=backend, pack_name="vv40"),
        )
        # Function ran (registered for shacl) but returned empty
        assert "group" in env.interpretation.functions_run
        assert env.interpretation.groupings == {}


# ── Prompt rendering ──────────────────────────────────────


class TestRendering:
    def test_firings_block_includes_pattern_severity_hits(self):
        ctx = FiringContext(
            pattern_id="W-EP-04", severity="High", hits=6,
            description="Unassessed Factor at Elevated Risk",
            pack=PackContext(name="vv40"),
            cou=CouContext(name="COU2"),
        )
        block = _render_firings_block([ctx])
        assert "W-EP-04" in block
        assert "High" in block
        assert "6 hits" in block
        assert "Unassessed Factor" in block

    def test_firings_block_includes_affected_evidence_labels(self):
        ctx = FiringContext(
            pattern_id="W-EP-04", severity="High", hits=2,
            description="x", pack=None, cou=None,
            affected_evidence=(
                {"iri": "ex:1", "label": "Use error", "kind": "CredibilityFactor",
                 "status": "not-assessed", "required": "", "achieved": "",
                 "description": ""},
                {"iri": "ex:2", "label": "Test samples", "kind": "CredibilityFactor",
                 "status": "not-assessed", "required": "", "achieved": "",
                 "description": ""},
            ),
        )
        block = _render_firings_block([ctx])
        assert "Use error" in block
        assert "Test samples" in block

    def test_firings_block_includes_compound_constituents(self):
        ctx = FiringContext(
            pattern_id="COMPOUND-01", severity="Critical", hits=1,
            description="x", pack=None, cou=None,
            constituent_firings=(
                {"patternId": "W-AL-01", "severity": "High",
                 "description": "Missing UQ",
                 "affected": {"iri": "ex:1", "label": "use-error",
                              "kind": "CredibilityFactor", "status": "",
                              "required": "", "achieved": "", "description": ""}},
            ),
        )
        block = _render_firings_block([ctx])
        assert "W-AL-01" in block
        assert "Constituents" in block


# ── max_items truncation (consistent with explain) ─────────


class TestMaxItems:
    def test_top_n_orders_by_severity_then_hits(self):
        contexts = [
            FiringContext(pattern_id="W-LOW", severity="Low", hits=10),
            FiringContext(pattern_id="W-CRIT", severity="Critical", hits=1),
            FiringContext(pattern_id="W-HI-MORE", severity="High", hits=5),
            FiringContext(pattern_id="W-HI-FEW", severity="High", hits=2),
        ]
        top = _top_n(contexts, 3)
        assert [c.pattern_id for c in top] == ["W-CRIT", "W-HI-MORE", "W-HI-FEW"]

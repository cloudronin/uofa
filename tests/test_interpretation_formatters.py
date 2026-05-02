"""Tests for the four output formatters (spec v0.4 §4.6, P-M).

Each format is a pure function returning a string. Tests verify:
- The shape contract (json round-trips, markdown headings, html escaping)
- Optional sections are skipped when empty
- The dispatcher in render_envelope wires the right formatter
"""

from __future__ import annotations

import json

import pytest

from uofa_cli.interpretation.envelope import (
    INTERPRETATION_VERSION,
    Interpretation,
    InterpretationEnvelope,
    make_envelope,
)
from uofa_cli.interpretation.formatters import (
    render_envelope,
    render_html,
    render_json,
    render_markdown,
    render_text,
)


def _envelope(
    *,
    explanations=None, groupings=None, contextual_severity=None,
    cross_patterns=None, narratives=None,
) -> InterpretationEnvelope:
    return make_envelope(
        command="rules",
        command_version="0.6.0",
        structured_output={"firings": []},
        backend_name="ollama",
        model_name="qwen3.5:4b",
        functions_run=["explain"],
        explanations=explanations or [],
        groupings=groupings or {},
        contextual_severity=contextual_severity or {},
        cross_patterns=cross_patterns or [],
        narratives=narratives or [],
        timestamp="2026-12-15T22:30:00Z",
    )


def _sample_explanations():
    """v0.4.0 three-field schema fixtures."""
    return [
        {
            "patternId": "W-EP-04", "severity": "High",
            "affected_evidence_summary": "Six factors are unassessed (Use error, ...).",
            "gap_description": "Provenance broken.",
            "relevance_to_cou": "MRL 5 stakes are highest.",
        },
        {
            "patternId": "W-AL-01", "severity": "Medium",
            "affected_evidence_summary": "Three validation results lack UQ.",
            "gap_description": "UQ missing.",
            "relevance_to_cou": "Class III VAD requires UQ.",
        },
    ]


# ── JSON ───────────────────────────────────────────────────


class TestJsonFormat:
    def test_round_trip(self):
        env = _envelope(explanations=_sample_explanations())
        out = render_json(env)
        parsed = json.loads(out)
        assert parsed["command"] == "rules"
        assert parsed["interpretation"]["interpretation_version"] == INTERPRETATION_VERSION
        assert len(parsed["interpretation"]["explanations"]) == 2

    def test_envelope_with_null_interpretation(self):
        env = InterpretationEnvelope(
            command="rules", command_version="0.6.0",
            structured_output={}, interpretation=None,
        )
        parsed = json.loads(render_json(env))
        assert parsed["interpretation"] is None

    def test_dispatcher_routes_to_json(self):
        env = _envelope(explanations=_sample_explanations())
        out = render_envelope(env, format="json")
        assert json.loads(out)["command"] == "rules"


# ── Text ───────────────────────────────────────────────────


class TestTextFormat:
    def test_basic_structure(self, monkeypatch):
        monkeypatch.setenv("NO_COLOR", "1")  # strip ANSI for assertion clarity
        env = _envelope(explanations=_sample_explanations())
        out = render_text(env)
        assert "══ Interpretation ══" in out
        assert "Backend: ollama / qwen3.5:4b" in out
        assert "Functions run: explain" in out
        assert "W-EP-04" in out
        assert "Provenance broken." in out

    def test_empty_envelope_produces_empty_string(self):
        env = InterpretationEnvelope(
            command="rules", command_version="0.6.0",
            structured_output={}, interpretation=None,
        )
        assert render_text(env) == ""

    def test_skips_empty_sections(self, monkeypatch):
        monkeypatch.setenv("NO_COLOR", "1")
        env = _envelope(explanations=_sample_explanations())  # only explanations
        out = render_text(env)
        assert "Groupings" not in out
        assert "Contextual severity" not in out
        assert "Cross-item patterns" not in out
        assert "Surviving-set" not in out

    def test_renders_groupings_when_present(self, monkeypatch):
        monkeypatch.setenv("NO_COLOR", "1")
        env = _envelope(groupings={"theme1": ["W-A", "W-B"], "theme2": ["W-C"]})
        out = render_text(env)
        assert "Groupings (2):" in out
        assert "theme1" in out
        assert "W-A, W-B" in out

    def test_error_explanations_marked(self, monkeypatch):
        monkeypatch.setenv("NO_COLOR", "1")
        env = _envelope(explanations=[
            {"patternId": "X", "severity": "High",
             "affected_evidence_summary": "",
             "gap_description": "(unavailable)",
             "relevance_to_cou": "",
             "error": True},
        ])
        out = render_text(env)
        assert "[unavailable]" in out

    def test_dispatcher_routes_to_text_by_default(self, monkeypatch):
        monkeypatch.setenv("NO_COLOR", "1")
        env = _envelope(explanations=_sample_explanations())
        out = render_envelope(env)  # no format kwarg → text default
        assert "══ Interpretation ══" in out


# ── Markdown ───────────────────────────────────────────────


class TestMarkdownFormat:
    def test_has_h2_h3_h4(self):
        env = _envelope(explanations=_sample_explanations())
        out = render_markdown(env)
        assert "## Interpretation" in out
        assert "### Explanations" in out
        assert "#### `W-EP-04`" in out

    def test_uses_code_spans_for_pattern_ids(self):
        env = _envelope(explanations=_sample_explanations())
        out = render_markdown(env)
        assert "`W-EP-04`" in out

    def test_groupings_render_as_bullet_list(self):
        env = _envelope(groupings={"theme1": ["W-A", "W-B"]})
        out = render_markdown(env)
        assert "- **theme1**:" in out
        assert "`W-A`" in out

    def test_no_explanation_text_shows_placeholder(self):
        env = _envelope(explanations=[
            {"patternId": "X", "severity": "Low",
             "affected_evidence_summary": "", "gap_description": "",
             "relevance_to_cou": ""},
        ])
        out = render_markdown(env)
        assert "_No explanation produced._" in out


# ── HTML ───────────────────────────────────────────────────


class TestHtmlFormat:
    def test_basic_structure(self):
        env = _envelope(explanations=_sample_explanations())
        out = render_html(env)
        assert '<div class="uofa-explain">' in out
        assert "</div>" in out
        assert '<h2 class="uofa-explain-heading">Interpretation</h2>' in out
        assert '<article class="uofa-explain-firing">' in out

    def test_html_escapes_user_content(self):
        """Spec §6.4 / general security: any user-derived text must be escaped."""
        env = _envelope(explanations=[{
            "patternId": "<script>alert(1)</script>",
            "severity": "High",
            "affected_evidence_summary": "<img src=x onerror=alert(1)>",
            "gap_description": "</div><script>steal()</script>",
            "relevance_to_cou": "<a href='javascript:'>",
        }])
        out = render_html(env)
        # Original tags should NOT appear unescaped
        assert "<script>alert(1)</script>" not in out
        assert "</div><script>" not in out
        assert "<img src=x" not in out
        # Escaped form should be present
        assert "&lt;script&gt;alert(1)&lt;/script&gt;" in out
        assert "&lt;img src=x" in out

    def test_severity_class_lowercased(self):
        env = _envelope(explanations=[
            {"patternId": "X", "severity": "Critical",
             "affected_evidence_summary": "x", "gap_description": "y",
             "relevance_to_cou": "z"},
        ])
        out = render_html(env)
        assert 'sev-critical' in out

    def test_error_attribute_on_failed_explanations(self):
        env = _envelope(explanations=[
            {"patternId": "X", "severity": "High",
             "affected_evidence_summary": "", "gap_description": "(err)",
             "relevance_to_cou": "", "error": True},
        ])
        out = render_html(env)
        assert 'data-error="true"' in out

    def test_dispatcher_routes_to_html(self):
        env = _envelope(explanations=_sample_explanations())
        out = render_envelope(env, format="html")
        assert '<div class="uofa-explain">' in out


# ── Section gating across all formats ─────────────────────


class TestSectionGating:
    """Each formatter must render only the per-function sections that have
    content. A function that's run but produced nothing should not show
    a heading with no body."""

    @pytest.mark.parametrize("renderer", [render_text, render_markdown, render_html])
    def test_empty_envelope_no_section_headings(self, renderer, monkeypatch):
        monkeypatch.setenv("NO_COLOR", "1")
        env = _envelope()  # nothing in any slot
        out = renderer(env)
        # Headings for empty per-function sections should not appear
        assert "Explanations" not in out or "Functions run" in out  # the meta line may legitimately mention it
        assert "Groupings" not in out
        assert "Cross-item" not in out
        assert "Surviving-set" not in out

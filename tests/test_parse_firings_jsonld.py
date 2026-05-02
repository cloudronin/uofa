"""Tests for `rules.parse_firings_jsonld()` (P-B Round 1, Phase 2).

Covers:
- Basic shape: one dict per patternId, hits aggregated correctly
- affectedNode IRIs extracted (deduped, order-preserved)
- description carried from schema:description
- escalationSource extracted for compound patterns
- IRI extraction handles `@id`-dict, bare-string, list-of-one variants
- Malformed input doesn't raise
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from uofa_cli.commands.rules import parse_firings_jsonld

REPO_ROOT = Path(__file__).parent.parent
MORRISON_COU2 = REPO_ROOT / "packs/vv40/examples/morrison/cou2/uofa-morrison-cou2.jsonld"


# ── Helpers ────────────────────────────────────────────────


def _annotation(pid, severity, affected_iri, description="desc", escalation=None):
    out = {
        "@id": f"_:{pid.lower()}",
        "@type": "https://uofa.net/vocab#WeakenerAnnotation",
        "https://uofa.net/vocab#patternId": pid,
        "https://uofa.net/vocab#severity": severity,
        "https://uofa.net/vocab#affectedNode": {"@id": affected_iri},
        "https://schema.org/description": description,
    }
    if escalation is not None:
        out["https://uofa.net/vocab#escalationSource"] = escalation
    return out


# ── Basic shape ────────────────────────────────────────────


class TestBasicShape:
    def test_single_firing_returns_one_dict(self):
        graph = {"@graph": [_annotation("W-EP-04", "High", "https://ex/factor/use-error")]}
        out = parse_firings_jsonld(json.dumps(graph))
        assert len(out) == 1
        assert out[0]["patternId"] == "W-EP-04"
        assert out[0]["severity"] == "High"
        assert out[0]["hits"] == 1
        assert out[0]["affected_nodes"] == ["https://ex/factor/use-error"]
        assert out[0]["description"] == "desc"
        assert out[0]["escalation_sources"] == []

    def test_multiple_hits_same_pattern_aggregated(self):
        graph = {"@graph": [
            _annotation("W-EP-04", "High", "https://ex/factor/a"),
            _annotation("W-EP-04", "High", "https://ex/factor/b"),
            _annotation("W-EP-04", "High", "https://ex/factor/c"),
        ]}
        out = parse_firings_jsonld(json.dumps(graph))
        assert len(out) == 1
        assert out[0]["hits"] == 3
        assert out[0]["affected_nodes"] == [
            "https://ex/factor/a",
            "https://ex/factor/b",
            "https://ex/factor/c",
        ]

    def test_affected_nodes_deduped(self):
        """Same affected IRI appearing twice should be listed once."""
        graph = {"@graph": [
            _annotation("W-EP-04", "High", "https://ex/factor/a"),
            _annotation("W-EP-04", "High", "https://ex/factor/a"),  # dup
        ]}
        out = parse_firings_jsonld(json.dumps(graph))
        assert out[0]["hits"] == 2  # hits still counts both
        assert out[0]["affected_nodes"] == ["https://ex/factor/a"]  # but unique IRIs

    def test_multiple_patterns_in_first_occurrence_order(self):
        graph = {"@graph": [
            _annotation("W-AL-01", "High", "https://ex/n1"),
            _annotation("W-EP-04", "High", "https://ex/n2"),
            _annotation("W-AL-01", "High", "https://ex/n3"),
            _annotation("W-CON-04", "Medium", "https://ex/n4"),
        ]}
        out = parse_firings_jsonld(json.dumps(graph))
        pids = [f["patternId"] for f in out]
        assert pids == ["W-AL-01", "W-EP-04", "W-CON-04"]
        # W-AL-01 has 2 hits aggregated
        assert out[0]["hits"] == 2

    def test_description_preserved_from_first_annotation(self):
        graph = {"@graph": [
            _annotation("W-EP-04", "High", "https://ex/n1", description="desc1"),
            _annotation("W-EP-04", "High", "https://ex/n2", description="desc2"),
        ]}
        out = parse_firings_jsonld(json.dumps(graph))
        assert out[0]["description"] == "desc1"


# ── COMPOUND escalation_sources ────────────────────────────


class TestEscalationSources:
    def test_compound_with_single_escalation_source(self):
        graph = {"@graph": [_annotation(
            "COMPOUND-01", "Critical", "https://ex/uofa",
            escalation={"@id": "_:b1"},
        )]}
        out = parse_firings_jsonld(json.dumps(graph))
        assert out[0]["escalation_sources"] == ["_:b1"]

    def test_compound_with_list_of_sources(self):
        graph = {"@graph": [_annotation(
            "COMPOUND-01", "Critical", "https://ex/uofa",
            escalation=[{"@id": "_:b1"}, {"@id": "_:b2"}, {"@id": "_:b3"}],
        )]}
        out = parse_firings_jsonld(json.dumps(graph))
        assert out[0]["escalation_sources"] == ["_:b1", "_:b2", "_:b3"]

    def test_escalation_sources_deduped_across_hits(self):
        graph = {"@graph": [
            _annotation("COMPOUND-01", "Critical", "https://ex/uofa", escalation=[{"@id": "_:b1"}]),
            _annotation("COMPOUND-01", "Critical", "https://ex/uofa", escalation=[{"@id": "_:b1"}, {"@id": "_:b2"}]),
        ]}
        out = parse_firings_jsonld(json.dumps(graph))
        assert out[0]["escalation_sources"] == ["_:b1", "_:b2"]


# ── IRI extraction edge cases ──────────────────────────────


class TestIriExtraction:
    def test_bare_string_iri(self):
        graph = {"@graph": [{
            "@type": "https://uofa.net/vocab#WeakenerAnnotation",
            "https://uofa.net/vocab#patternId": "W-X",
            "https://uofa.net/vocab#severity": "High",
            "https://uofa.net/vocab#affectedNode": "https://ex/bare",  # not wrapped in {@id: ...}
        }]}
        out = parse_firings_jsonld(json.dumps(graph))
        assert out[0]["affected_nodes"] == ["https://ex/bare"]

    def test_list_of_one_iri(self):
        graph = {"@graph": [{
            "@type": "https://uofa.net/vocab#WeakenerAnnotation",
            "https://uofa.net/vocab#patternId": "W-X",
            "https://uofa.net/vocab#severity": "High",
            "https://uofa.net/vocab#affectedNode": [{"@id": "https://ex/listed"}],
        }]}
        out = parse_firings_jsonld(json.dumps(graph))
        assert out[0]["affected_nodes"] == ["https://ex/listed"]


# ── Robustness ─────────────────────────────────────────────


class TestRobustness:
    def test_invalid_json_returns_empty(self):
        assert parse_firings_jsonld("not json {") == []

    def test_missing_graph_returns_empty(self):
        assert parse_firings_jsonld(json.dumps({"foo": "bar"})) == []

    def test_graph_not_a_list_returns_empty(self):
        assert parse_firings_jsonld(json.dumps({"@graph": "scalar"})) == []

    def test_non_weakener_nodes_ignored(self):
        graph = {"@graph": [
            {"@id": "x", "@type": "SomeOtherType", "foo": "bar"},
            _annotation("W-X", "High", "https://ex/n1"),
        ]}
        out = parse_firings_jsonld(json.dumps(graph))
        assert len(out) == 1

    def test_annotation_missing_patternid_skipped(self):
        graph = {"@graph": [{
            "@type": "https://uofa.net/vocab#WeakenerAnnotation",
            "https://uofa.net/vocab#severity": "High",
        }]}
        out = parse_firings_jsonld(json.dumps(graph))
        assert out == []

    def test_annotation_missing_severity_defaults_to_medium(self):
        graph = {"@graph": [{
            "@type": "https://uofa.net/vocab#WeakenerAnnotation",
            "https://uofa.net/vocab#patternId": "W-X",
            "https://uofa.net/vocab#affectedNode": {"@id": "https://ex/n"},
        }]}
        out = parse_firings_jsonld(json.dumps(graph))
        assert out[0]["severity"] == "Medium"


# ── Integration with real Morrison COU2 engine output ─────


@pytest.mark.skipif(not MORRISON_COU2.exists(), reason="Morrison fixture not available")
class TestRealEngineOutput:
    """End-to-end against real engine output. Requires Java/JRE."""

    def _engine_output(self) -> str:
        """Run the Java rule engine in jsonld mode and return its raw stdout."""
        import argparse as ap
        from uofa_cli.commands import rules
        try:
            args = ap.Namespace(
                file=MORRISON_COU2, rules=None, context=None, build=False,
                raw=False, format="jsonld", output=None,
            )
            return rules.run_structured(args).raw_stdout
        except FileNotFoundError:
            pytest.skip("Java rule engine not available")

    def test_morrison_cou2_w_ep_04_has_six_unassessed_factors(self):
        """SME-flagged canonical case: W-EP-04 fires 6 times in COU2,
        once per unassessed credibility factor. The parser must surface
        all six factor IRIs so the explanation can name them."""
        out = parse_firings_jsonld(self._engine_output())
        w_ep_04 = next((f for f in out if f["patternId"] == "W-EP-04"), None)
        assert w_ep_04 is not None
        assert w_ep_04["hits"] == 6
        assert len(w_ep_04["affected_nodes"]) == 6
        # Spot-check: should include the use-error factor cited in the audit
        assert any("use-error" in iri for iri in w_ep_04["affected_nodes"])

    def test_morrison_cou2_compound_01_has_escalation_sources(self):
        """COMPOUND-01 fires when Critical+High coexist; the escalation
        sources point to the constituent annotations. Parser must capture
        them so the explanation can cite which weakeners compounded."""
        out = parse_firings_jsonld(self._engine_output())
        compound = next((f for f in out if f["patternId"] == "COMPOUND-01"), None)
        if compound is None:
            pytest.skip("COMPOUND-01 doesn't fire on this fixture")
        assert len(compound["escalation_sources"]) >= 2

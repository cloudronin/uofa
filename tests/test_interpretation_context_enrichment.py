"""Tests for Round 1 context-enrichment helpers (P-B Phase 3).

Covers:
- `_resolve_node_in_doc` — finds nodes by IRI in mixed `id`/`@id` docs,
  doesn't get stuck on cycles
- `_summarize_node` — extracts label/kind/status/levels with correct
  precedence across alias keys
- `_summarize_constituent` — resolves a compound's escalation source to
  a constituent firing summary
- `extract_firing_contexts` enriched path — given rich `jsonld_firings`
  + `individual_annotations`, populates `affected_evidence` and
  `constituent_firings` correctly
- `extract_firing_contexts` legacy path — without rich data, behaves
  exactly as Round 0 (unchanged contract for `uofa explain --from-file`
  on cached envelopes)
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from uofa_cli.interpretation.context import (
    FiringContext,
    extract_firing_contexts,
    _resolve_node_in_doc,
    _summarize_constituent,
    _summarize_node,
)

REPO_ROOT = Path(__file__).parent.parent
MORRISON_COU2 = REPO_ROOT / "packs/vv40/examples/morrison/cou2/uofa-morrison-cou2.jsonld"


# ── _resolve_node_in_doc ───────────────────────────────────


class TestResolveNodeInDoc:
    def test_finds_node_by_compact_id(self):
        doc = {"hasFactor": [{"id": "https://ex/factor/a", "type": "F", "label": "A"}]}
        result = _resolve_node_in_doc(doc, "https://ex/factor/a")
        assert result == {"id": "https://ex/factor/a", "type": "F", "label": "A"}

    def test_finds_node_by_expanded_at_id(self):
        doc = {"@graph": [{"@id": "https://ex/n1", "@type": "Thing"}]}
        result = _resolve_node_in_doc(doc, "https://ex/n1")
        assert result["@id"] == "https://ex/n1"

    def test_finds_deeply_nested_node(self):
        doc = {
            "level1": {"level2": {"level3": [
                {"id": "https://ex/deep", "label": "FOUND"}
            ]}}
        }
        result = _resolve_node_in_doc(doc, "https://ex/deep")
        assert result["label"] == "FOUND"

    def test_returns_none_when_iri_not_present(self):
        doc = {"foo": "bar"}
        assert _resolve_node_in_doc(doc, "https://nonexistent") is None

    def test_handles_empty_iri(self):
        doc = {"id": "x"}
        assert _resolve_node_in_doc(doc, "") is None

    def test_does_not_loop_on_cyclic_refs(self):
        """Object identity tracking prevents infinite recursion."""
        a: dict = {"id": "https://ex/a"}
        b: dict = {"id": "https://ex/b", "ref": a}
        a["ref"] = b  # cycle
        result = _resolve_node_in_doc(a, "https://ex/b")
        assert result is b

    def test_real_morrison_cou2_factor_lookup(self):
        if not MORRISON_COU2.exists():
            pytest.skip("Morrison fixture not available")
        doc = json.loads(MORRISON_COU2.read_text())
        result = _resolve_node_in_doc(doc, "https://uofa.net/morrison/cou2/factor/use-error")
        assert result is not None
        assert result.get("factorType") == "Use error"
        assert result.get("factorStatus") == "not-assessed"


# ── _summarize_node ────────────────────────────────────────


class TestSummarizeNode:
    def test_credibility_factor_summary(self):
        node = {
            "id": "https://ex/factor/use-error",
            "type": "CredibilityFactor",
            "factorType": "Use error",
            "factorStatus": "not-assessed",
            "requiredLevel": 4,
            "achievedLevel": 0,
        }
        s = _summarize_node(node)
        assert s["iri"] == "https://ex/factor/use-error"
        assert s["kind"] == "CredibilityFactor"
        assert s["label"] == "Use error"
        assert s["status"] == "not-assessed"
        assert s["required"] == "4"
        assert s["achieved"] == "0"

    def test_uses_name_when_factor_type_absent(self):
        node = {"id": "x", "name": "My Validation Result", "type": "ValidationResult"}
        s = _summarize_node(node)
        assert s["label"] == "My Validation Result"
        assert s["kind"] == "ValidationResult"

    def test_handles_at_id_form(self):
        node = {"@id": "https://ex/x", "@type": "Thing", "name": "Y"}
        s = _summarize_node(node)
        assert s["iri"] == "https://ex/x"
        assert s["kind"] == "Thing"

    def test_missing_fields_become_empty_strings(self):
        s = _summarize_node({"id": "x"})
        assert s["iri"] == "x"
        assert s["kind"] == ""
        assert s["label"] == ""
        assert s["status"] == ""

    def test_list_value_joined(self):
        node = {"id": "x", "type": ["Foo", "Bar"]}
        s = _summarize_node(node)
        assert s["kind"] == "Foo, Bar"

    def test_non_dict_input_returns_safe_dict(self):
        s = _summarize_node({})
        assert all(isinstance(v, str) for v in s.values())


# ── _summarize_constituent ────────────────────────────────


class TestSummarizeConstituent:
    def test_resolves_affected_node_to_label(self):
        annotation = {
            "id": "_:b1",
            "patternId": "W-AL-01",
            "severity": "High",
            "affected_node": "https://ex/factor/use-error",
            "description": "Missing UQ",
        }
        package_doc = {"hasFactor": [{
            "id": "https://ex/factor/use-error",
            "type": "CredibilityFactor",
            "factorType": "Use error",
        }]}
        out = _summarize_constituent(annotation, package_doc)
        assert out["patternId"] == "W-AL-01"
        assert out["severity"] == "High"
        assert out["description"] == "Missing UQ"
        assert out["affected"]["label"] == "Use error"
        assert out["affected"]["kind"] == "CredibilityFactor"

    def test_unresolvable_iri_yields_iri_only_summary(self):
        annotation = {
            "id": "_:b1", "patternId": "W-X", "severity": "High",
            "affected_node": "https://ex/orphan", "description": "",
        }
        out = _summarize_constituent(annotation, {})
        assert out["affected"]["iri"] == "https://ex/orphan"
        assert out["affected"]["label"] == ""


# ── extract_firing_contexts: legacy path ──────────────────


class TestExtractContextsLegacy:
    """Without rich jsonld_firings, behavior should match pre-Round-1
    (the standalone explain --from-file path passes None for these)."""

    def test_legacy_call_produces_empty_evidence_fields(self):
        firings = [{"patternId": "W-EP-04", "severity": "High", "hits": 6}]
        contexts = extract_firing_contexts(firings, package_doc={}, pack_name="vv40")
        assert len(contexts) == 1
        assert contexts[0].affected_evidence == ()
        assert contexts[0].constituent_firings == ()
        # And the legacy fields stay populated as before
        assert contexts[0].pattern_id == "W-EP-04"
        assert contexts[0].hits == 6


# ── extract_firing_contexts: enriched path ────────────────


class TestExtractContextsEnriched:
    def test_affected_evidence_populated_from_jsonld_firings(self):
        firings = [{"patternId": "W-EP-04", "severity": "High", "hits": 2}]
        jsonld_firings = [{
            "patternId": "W-EP-04",
            "severity": "High",
            "hits": 2,
            "description": "Unassessed Factor at Elevated Risk",
            "affected_nodes": [
                "https://ex/factor/use-error",
                "https://ex/factor/test-samples",
            ],
            "escalation_sources": [],
        }]
        package_doc = {"hasCredibilityFactor": [
            {"id": "https://ex/factor/use-error", "type": "CredibilityFactor",
             "factorType": "Use error", "factorStatus": "not-assessed"},
            {"id": "https://ex/factor/test-samples", "type": "CredibilityFactor",
             "factorType": "Test samples", "factorStatus": "not-assessed"},
        ]}
        contexts = extract_firing_contexts(
            firings, package_doc, "vv40",
            jsonld_firings=jsonld_firings,
        )
        ctx = contexts[0]
        assert len(ctx.affected_evidence) == 2
        labels = [e["label"] for e in ctx.affected_evidence]
        assert labels == ["Use error", "Test samples"]
        # affected_node (singular legacy field) carries the first IRI
        assert ctx.affected_node == "https://ex/factor/use-error"

    def test_unresolvable_iri_still_creates_summary(self):
        """If an affected_node IRI doesn't appear in the package, the
        summary should still exist (with iri only) so the prompt sees
        the count is right."""
        firings = [{"patternId": "W-X", "severity": "Low", "hits": 1}]
        jsonld_firings = [{
            "patternId": "W-X", "severity": "Low", "hits": 1,
            "description": "", "affected_nodes": ["https://ex/orphan"],
            "escalation_sources": [],
        }]
        contexts = extract_firing_contexts(
            firings, package_doc={}, pack_name="vv40",
            jsonld_firings=jsonld_firings,
        )
        assert len(contexts[0].affected_evidence) == 1
        assert contexts[0].affected_evidence[0]["iri"] == "https://ex/orphan"

    def test_compound_constituents_resolved(self):
        firings = [{"patternId": "COMPOUND-01", "severity": "Critical", "hits": 1}]
        jsonld_firings = [{
            "patternId": "COMPOUND-01",
            "severity": "Critical",
            "hits": 1,
            "description": "Risk Escalation — Critical + High coexist",
            "affected_nodes": ["https://ex/uofa/cou2"],
            "escalation_sources": ["_:b1", "_:b2"],
        }]
        individual_annotations = [
            {"id": "_:b1", "patternId": "W-AL-01", "severity": "High",
             "affected_node": "https://ex/factor/use-error",
             "description": "Missing UQ"},
            {"id": "_:b2", "patternId": "W-EP-04", "severity": "High",
             "affected_node": "https://ex/factor/test-samples",
             "description": "Unassessed Factor"},
        ]
        package_doc = {"items": [
            {"id": "https://ex/factor/use-error", "factorType": "Use error",
             "type": "CredibilityFactor"},
            {"id": "https://ex/factor/test-samples", "factorType": "Test samples",
             "type": "CredibilityFactor"},
        ]}
        contexts = extract_firing_contexts(
            firings, package_doc, "vv40",
            jsonld_firings=jsonld_firings,
            individual_annotations=individual_annotations,
        )
        ctx = contexts[0]
        assert len(ctx.constituent_firings) == 2
        cons_pids = [c["patternId"] for c in ctx.constituent_firings]
        assert cons_pids == ["W-AL-01", "W-EP-04"]
        # Each constituent carries a resolved affected-node label
        assert ctx.constituent_firings[0]["affected"]["label"] == "Use error"
        assert ctx.constituent_firings[1]["affected"]["label"] == "Test samples"

    def test_compound_without_individual_annotations_still_works(self):
        """If the caller forgot to pass individual_annotations, the COMPOUND
        firing context still exists (just without resolved constituents).
        Fail-soft so bugs don't crash the pipeline."""
        firings = [{"patternId": "COMPOUND-01", "severity": "Critical", "hits": 1}]
        jsonld_firings = [{
            "patternId": "COMPOUND-01", "severity": "Critical", "hits": 1,
            "description": "x", "affected_nodes": [],
            "escalation_sources": ["_:b1"],
        }]
        contexts = extract_firing_contexts(
            firings, package_doc={}, pack_name="vv40",
            jsonld_firings=jsonld_firings,
            # individual_annotations omitted
        )
        assert contexts[0].constituent_firings == ()


# ── End-to-end against real Morrison COU2 ─────────────────


@pytest.mark.skipif(not MORRISON_COU2.exists(), reason="Morrison fixture not available")
class TestRealMorrisonCou2:
    """The SME-canonical case: W-EP-04 in COU2 should now produce a
    FiringContext whose affected_evidence lists the six unassessed
    factors by their human-readable factorType labels."""

    def _setup(self):
        import argparse as ap
        from uofa_cli.commands import rules
        try:
            args = ap.Namespace(
                file=MORRISON_COU2, rules=None, context=None, build=False,
                raw=False, format="jsonld", output=None,
            )
            jsonld_text = rules.run_structured(args).raw_stdout
        except FileNotFoundError:
            pytest.skip("Java rule engine not available")
        return jsonld_text

    def test_w_ep_04_lists_six_factor_labels(self):
        from uofa_cli.commands.rules import (
            parse_firings, parse_firings_jsonld, parse_individual_annotations,
        )
        # Run summary mode for the legacy `firings` shape
        import argparse as ap
        from uofa_cli.commands import rules as rules_mod
        args = ap.Namespace(
            file=MORRISON_COU2, rules=None, context=None, build=False,
            raw=False, format="summary", output=None,
        )
        summary_firings = rules_mod.run_structured(args).firings

        jsonld_text = self._setup()
        jsonld_firings = parse_firings_jsonld(jsonld_text)
        annotations = parse_individual_annotations(jsonld_text)

        package_doc = json.loads(MORRISON_COU2.read_text())

        contexts = extract_firing_contexts(
            summary_firings, package_doc, "vv40",
            jsonld_firings=jsonld_firings,
            individual_annotations=annotations,
        )
        w_ep_04 = next(c for c in contexts if c.pattern_id == "W-EP-04")
        labels = [e["label"] for e in w_ep_04.affected_evidence]
        assert len(labels) == 6
        assert "Use error" in labels
        assert "Test samples" in labels
        # All labels populated (no empty strings)
        assert all(labels)

    def test_w_ep_04_template_vars_expose_the_evidence(self):
        """Round-trip check: the prompt template will iterate
        firing.affected_evidence — verify it's there and shaped right."""
        from uofa_cli.commands.rules import (
            parse_firings_jsonld, parse_individual_annotations,
        )
        import argparse as ap
        from uofa_cli.commands import rules as rules_mod
        args = ap.Namespace(
            file=MORRISON_COU2, rules=None, context=None, build=False,
            raw=False, format="summary", output=None,
        )
        summary_firings = rules_mod.run_structured(args).firings
        jsonld_text = self._setup()
        contexts = extract_firing_contexts(
            summary_firings, json.loads(MORRISON_COU2.read_text()), "vv40",
            jsonld_firings=parse_firings_jsonld(jsonld_text),
            individual_annotations=parse_individual_annotations(jsonld_text),
        )
        w_ep_04 = next(c for c in contexts if c.pattern_id == "W-EP-04")
        vars = w_ep_04.to_template_vars()
        assert "affected_evidence" in vars["firing"]
        assert len(vars["firing"]["affected_evidence"]) == 6
        # Each entry has the keys the template expects
        first = vars["firing"]["affected_evidence"][0]
        for k in ("iri", "kind", "label", "status"):
            assert k in first

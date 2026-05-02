"""Tests for the plain-language firing explanation function (P-B, spec §2.1).

Backend-driven tests use MockBackend with canned `structured_responses`
so they're deterministic. Real-Ollama sample generation is in the
companion script `dev/scripts/generate_explain_sample.py` (manual SME
review per spec §8.3 kill criterion).
"""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest

from uofa_cli.interpretation import (
    InterpretationOptions,
    interpret_rules_output,
)
# Cache isolation is provided by tests/conftest.py (autouse fixture).
from uofa_cli.interpretation.context import (
    CouContext,
    FiringContext,
    PackContext,
)
from uofa_cli.interpretation.functions.explain import (
    _top_n_by_severity,
)
from uofa_cli.llm import MockBackend


# ── Fixtures ────────────────────────────────────────────────


def _firing(pid="W-EP-04", severity="High", hits=3, description=""):
    return FiringContext(
        pattern_id=pid,
        severity=severity,
        hits=hits,
        description=description,
        pack=PackContext(name="vv40", standard="ASME-VV40-2018"),
        cou=CouContext(name="COU1", device_class="Class II"),
    )


def _explanation_response(pid, severity, text="Plain-language explanation here."):
    """Build a canned response shape matching the v0.4.0 three-field schema.

    `text` is split across the three prose fields with simple tags so each
    field is non-empty and recognizable in assertions. Tests that need
    fine-grained per-field control should construct their own dicts.
    """
    return {
        "patternId": pid,
        "severity": severity,
        "affected_evidence_summary": f"[evidence] {text}",
        "gap_description": f"[gap] {text}",
        "relevance_to_cou": f"[relevance] {text}",
    }


# ── Happy path ──────────────────────────────────────────────


class TestExplainHappyPath:
    def test_one_call_per_firing(self):
        """Spec §4.8 cost example: 14 firings → 14 LLM calls."""
        backend = MockBackend(
            default_response=json.dumps(_explanation_response("X", "Medium")),
        )
        firings = [
            {"patternId": "W-EP-04", "severity": "High", "hits": 3},
            {"patternId": "W-AR-05", "severity": "Critical", "hits": 1},
            {"patternId": "COMPOUND-01", "severity": "Critical", "hits": 1},
        ]
        env = interpret_rules_output(
            structured_output={"firings": firings},
            package_doc={},
            firings=firings,
            options=InterpretationOptions(backend=backend, pack_name="vv40", functions=["explain"]),
        )
        # generate_structured was called once per firing
        structured_calls = [c for c in backend.calls if c[0] == "generate_structured"]
        assert len(structured_calls) == 3
        assert len(env.interpretation.explanations) == 3

    def test_explanation_carries_pattern_metadata(self):
        backend = MockBackend(
            default_response=json.dumps(
                _explanation_response("W-EP-04", "High", "EP-04 explanation.")
            ),
        )
        firings = [{"patternId": "W-EP-04", "severity": "High", "hits": 3}]
        env = interpret_rules_output(
            structured_output={"firings": firings},
            package_doc={},
            firings=firings,
            options=InterpretationOptions(backend=backend, pack_name="vv40"),
        )
        e = env.interpretation.explanations[0]
        assert e["patternId"] == "W-EP-04"
        assert e["severity"] == "High"
        # v0.4.0 schema: three prose fields, no confidence
        assert "EP-04" in e["affected_evidence_summary"]
        assert "EP-04" in e["gap_description"]
        assert "EP-04" in e["relevance_to_cou"]
        assert "confidence" not in e

    def test_pattern_id_substituted_into_prompt(self):
        """The Jinja2 template must thread firing.patternId into the prompt
        so the LLM sees the specific pattern, not generic placeholder."""
        backend = MockBackend(
            structured_responses={
                "W-AR-02": _explanation_response("W-AR-02", "High"),
            },
            default_response=json.dumps(_explanation_response("default", "Low")),
        )
        firings = [{"patternId": "W-AR-02", "severity": "High", "hits": 1}]
        env = interpret_rules_output(
            structured_output={"firings": firings},
            package_doc={},
            firings=firings,
            options=InterpretationOptions(backend=backend, pack_name="vv40"),
        )
        # MockBackend's structured_responses dispatches on prompt substring;
        # if W-AR-02 appears in the rendered prompt we hit the canned response.
        assert env.interpretation.explanations[0]["patternId"] == "W-AR-02"

    def test_command_check_also_dispatches(self):
        """Spec §2.6 matrix: explain applies to rules AND check."""
        from uofa_cli.interpretation import interpret_check_output
        backend = MockBackend(
            default_response=json.dumps(_explanation_response("W-EP-04", "High")),
        )
        firings = [{"patternId": "W-EP-04", "severity": "High", "hits": 1}]
        env = interpret_check_output(
            structured_output={"rules": firings},
            package_doc={},
            rules_firings=firings,
            options=InterpretationOptions(backend=backend, pack_name="vv40"),
        )
        assert env.command == "check"
        assert "explain" in env.interpretation.functions_run
        assert len(env.interpretation.explanations) == 1


# ── max_items truncation (spec §3.2) ───────────────────────


class TestMaxItems:
    def test_top_n_by_severity_orders_correctly(self):
        firings = [
            _firing("W-LOW", "Low", hits=10),
            _firing("W-CRIT", "Critical", hits=1),
            _firing("W-HI-1", "High", hits=3),
            _firing("W-HI-2", "High", hits=5),
            _firing("W-MED", "Medium", hits=20),
        ]
        top3 = _top_n_by_severity(firings, 3)
        names = [f.pattern_id for f in top3]
        # Critical first, then High (sorted by hits desc), then Medium
        assert names == ["W-CRIT", "W-HI-2", "W-HI-1"]

    def test_max_items_truncates_pipeline_output(self):
        backend = MockBackend(
            default_response=json.dumps(_explanation_response("X", "Medium")),
        )
        firings = [
            {"patternId": f"W-{i:02}", "severity": "High", "hits": i}
            for i in range(10)
        ]
        env = interpret_rules_output(
            structured_output={"firings": firings},
            package_doc={},
            firings=firings,
            options=InterpretationOptions(
                backend=backend, max_items=3, pack_name="vv40", functions=["explain"],
            ),
        )
        # Only 3 LLM calls + 3 explanations
        structured_calls = [c for c in backend.calls if c[0] == "generate_structured"]
        assert len(structured_calls) == 3
        assert len(env.interpretation.explanations) == 3


# ── Error handling per firing ──────────────────────────────


class TestPerFiringErrors:
    def test_individual_failure_does_not_blow_up_batch(self):
        """Spec §4.8 cost-tracking pattern: per-firing calls. One backend
        failure on firing N must not lose explanations for firings 0..N-1
        and N+1..end."""
        from uofa_cli.llm.errors import LLMError

        # Build a backend that fails on the second call only
        call_count = {"n": 0}

        class FlakyBackend(MockBackend):
            def generate_structured(self, prompt, schema, options):
                call_count["n"] += 1
                if call_count["n"] == 2:
                    raise LLMError("transient", suggestion="retry")
                return _explanation_response("OK", "Medium")

        backend = FlakyBackend(default_response=json.dumps(_explanation_response("X", "Medium")))
        firings = [
            {"patternId": "W-A", "severity": "High", "hits": 1},
            {"patternId": "W-B", "severity": "High", "hits": 1},
            {"patternId": "W-C", "severity": "High", "hits": 1},
        ]
        env = interpret_rules_output(
            structured_output={"firings": firings},
            package_doc={},
            firings=firings,
            options=InterpretationOptions(backend=backend, pack_name="vv40"),
        )
        # All 3 explanations present; the failed one carries error=True
        assert len(env.interpretation.explanations) == 3
        assert env.interpretation.explanations[0]["error"] is False if "error" in env.interpretation.explanations[0] else True
        assert env.interpretation.explanations[1].get("error") is True
        # v0.4.0: failure surfaces as `error: True` + diagnostic in
        # gap_description; no separate confidence flag
        assert "unavailable" in env.interpretation.explanations[1]["gap_description"]


# ── Backend-without-structured-output fallback ────────────


class TestStructuredOutputFallback:
    def test_falls_back_to_generate_when_unsupported(self):
        """OpenAI-compatible backends sometimes lack structured output —
        the function must fall back to plain generate() + JSON parse."""

        class NoStructuredBackend(MockBackend):
            def supports_structured_output(self):
                return False

            def generate_structured(self, prompt, schema, options):
                raise NotImplementedError("not supported")

        # Plain `generate` returns text; the response includes a JSON object.
        canned = json.dumps(_explanation_response("W-EP-04", "High"))
        backend = NoStructuredBackend(default_response=canned)
        firings = [{"patternId": "W-EP-04", "severity": "High", "hits": 1}]
        env = interpret_rules_output(
            structured_output={"firings": firings},
            package_doc={},
            firings=firings,
            options=InterpretationOptions(backend=backend, pack_name="vv40"),
        )
        e = env.interpretation.explanations[0]
        assert e["patternId"] == "W-EP-04"
        # generate (not generate_structured) was called
        assert any(c[0] == "generate" for c in backend.calls)

    def test_strips_markdown_code_fences(self):
        """Some backends wrap JSON output in ```json ... ``` fences."""
        class NoStructuredBackend(MockBackend):
            def supports_structured_output(self):
                return False

            def generate_structured(self, prompt, schema, options):
                raise NotImplementedError

        fenced = "```json\n" + json.dumps(_explanation_response("W-EP-04", "High")) + "\n```"
        backend = NoStructuredBackend(default_response=fenced)
        firings = [{"patternId": "W-EP-04", "severity": "High", "hits": 1}]
        env = interpret_rules_output(
            structured_output={"firings": firings},
            package_doc={},
            firings=firings,
            options=InterpretationOptions(backend=backend, pack_name="vv40"),
        )
        # Round 1: at least one of the prose fields is populated
        e = env.interpretation.explanations[0]
        assert e["affected_evidence_summary"] or e["gap_description"]


# ── Identifier hallucination: model output is NOT trusted ──


class TestIdentifierHallucination:
    """Regression for the W-AL-01 → W-AL-AL-01 bug observed in P-B Round 1.

    The model can hallucinate `patternId` and `severity` in its JSON
    response (we saw it duplicate the prefix on one of 11 firings).
    `_explain_one` must use the authoritative ctx values for these
    fields and ignore the model's echo. The prose fields stay sourced
    from the model — that's the actual user-visible content.
    """

    def test_pattern_id_uses_ctx_not_model_echo(self):
        backend = MockBackend(default_response=json.dumps({
            "patternId": "TOTALLY-WRONG-XX-99",  # model lies
            "severity": "Bogus",                  # model lies
            "affected_evidence_summary": "a",
            "gap_description": "b",
            "relevance_to_cou": "c",
        }))
        firings = [{"patternId": "W-AL-01", "severity": "High", "hits": 3}]
        env = interpret_rules_output(
            structured_output={"firings": firings},
            package_doc={},
            firings=firings,
            options=InterpretationOptions(backend=backend, pack_name="vv40"),
        )
        e = env.interpretation.explanations[0]
        # Identifier fields come from ctx, not the model
        assert e["patternId"] == "W-AL-01"
        assert e["severity"] == "High"
        # Prose fields come from the model
        assert e["affected_evidence_summary"] == "a"
        assert e["gap_description"] == "b"

    def test_w_al_01_round_trips_intact(self):
        """Targeted regression for the exact W-AL-01 → W-AL-AL-01 bug."""
        backend = MockBackend(default_response=json.dumps({
            "patternId": "W-AL-AL-01",  # the actual hallucination we observed
            "severity": "High",
            "affected_evidence_summary": "Three validation results lack UQ.",
            "gap_description": "Missing aleatory uncertainty metrics.",
            "relevance_to_cou": "Class II MRL 2 stakes.",
        }))
        firings = [{"patternId": "W-AL-01", "severity": "High", "hits": 3}]
        env = interpret_rules_output(
            structured_output={"firings": firings},
            package_doc={},
            firings=firings,
            options=InterpretationOptions(backend=backend, pack_name="vv40"),
        )
        assert env.interpretation.explanations[0]["patternId"] == "W-AL-01"


# ── No-template-found graceful path ────────────────────────


class TestNoTemplate:
    def test_skips_silently_when_no_template_exists(self, monkeypatch):
        """If a pack overrides `--explain-functions` to include explain but
        ships no template AND there's no bundled default, the function
        emits an empty list — not an error. Lets pack ecosystems add
        functions incrementally without breaking on missing templates."""
        from uofa_cli.interpretation.functions import explain as explain_mod

        monkeypatch.setattr(explain_mod, "has_template", lambda *a, **kw: False)

        backend = MockBackend()
        firings = [{"patternId": "W-EP-04", "severity": "High", "hits": 1}]
        env = interpret_rules_output(
            structured_output={"firings": firings},
            package_doc={},
            firings=firings,
            # Restrict to explain so other functions (group, etc.) don't
            # also call the backend and break the "no calls" assertion.
            options=InterpretationOptions(backend=backend, pack_name="vv40", functions=["explain"]),
        )
        assert env.interpretation.explanations == []
        # No backend calls happened
        assert backend.calls == []

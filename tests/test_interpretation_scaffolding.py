"""Tests for the Phase 4 (P-A) interpretation scaffolding.

Covers `envelope`, `dispatcher`, `context`, `templates`, and `pipeline`.
The actual per-function implementations land in Phase 5+; this module
locks in the API contracts the rest of the system will consume.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from uofa_cli.interpretation import (
    INTERPRETATION_VERSION,
    KNOWN_COMMANDS,
    KNOWN_FUNCTIONS,
    CouContext,
    DifferenceContext,
    FiringContext,
    Interpretation,
    InterpretationEnvelope,
    InterpretationOptions,
    PackContext,
    ViolationContext,
    applicable_functions,
    applies_to_commands,
    extract_cou_context,
    extract_difference_contexts,
    extract_firing_contexts,
    extract_pack_context,
    extract_violation_contexts,
    has_template,
    interpret_check_output,
    interpret_diff_output,
    interpret_rules_output,
    interpret_shacl_output,
    make_envelope,
    registered_function_names,
)
from uofa_cli.interpretation.dispatcher import reset_registry
from uofa_cli.llm import MockBackend


REPO_ROOT = Path(__file__).parent.parent
MORRISON_COU1 = REPO_ROOT / "packs" / "vv40" / "examples" / "morrison" / "cou1" / "uofa-morrison-cou1.jsonld"


@pytest.fixture(autouse=True)
def isolated_registry():
    """Each test gets a clean dispatcher registry — registrations are
    process-global so tests would otherwise leak state. Teardown reloads
    every function module so its top-level `@applies_to_commands`
    decorator re-registers the production function for subsequent test
    modules. (`importlib.reload` of the package `__init__.py` alone is
    insufficient because Python caches the inner modules — only reloading
    the function modules re-runs their decorators.)

    Add new function modules to the reload list as they're added in
    P-G / P-H / P-I / P-J / P-K.
    """
    reset_registry()
    yield
    reset_registry()
    import importlib
    import uofa_cli.interpretation.functions.explain as explain_mod
    import uofa_cli.interpretation.functions.group as group_mod
    import uofa_cli.interpretation.functions.contextualize as contextualize_mod
    import uofa_cli.interpretation.functions.cross as cross_mod
    import uofa_cli.interpretation.functions.narrative as narrative_mod
    importlib.reload(explain_mod)
    importlib.reload(group_mod)
    importlib.reload(contextualize_mod)
    importlib.reload(cross_mod)
    importlib.reload(narrative_mod)


# ── Envelope ───────────────────────────────────────────────


class TestEnvelope:
    def test_make_envelope_shape_matches_spec(self):
        env = make_envelope(
            command="rules",
            command_version="0.6.0",
            structured_output={"firings": []},
            backend_name="ollama",
            model_name="qwen3.5:4b",
            functions_run=["explain"],
            timestamp="2026-12-15T22:30:00Z",
        )
        d = env.to_dict()
        # Spec §4.5 top-level keys
        assert set(d) == {"command", "command_version", "structured_output", "interpretation"}
        assert d["command"] == "rules"
        assert d["command_version"] == "0.6.0"
        # Interpretation keys
        i = d["interpretation"]
        assert i["interpretation_timestamp"] == "2026-12-15T22:30:00Z"
        assert i["interpretation_model"] == "qwen3.5:4b"
        assert i["interpretation_backend"] == "ollama"
        assert i["interpretation_version"] == INTERPRETATION_VERSION
        assert i["functions_run"] == ["explain"]

    def test_envelope_is_json_serializable(self):
        import json
        env = make_envelope(
            command="shacl",
            command_version="0.6.0",
            structured_output={"violations": [{"path": "p", "severity": "High"}]},
            backend_name="anthropic",
            model_name="claude-sonnet-5-2026",
            functions_run=[],
            explanations=[{"item": "x", "text": "y"}],
        )
        # Must round-trip through JSON cleanly
        roundtrip = json.loads(json.dumps(env.to_dict()))
        assert roundtrip["command"] == "shacl"
        assert roundtrip["interpretation"]["explanations"] == [{"item": "x", "text": "y"}]

    def test_interpretation_can_be_none(self):
        """Caller may set interpretation=None for graceful-degradation
        envelopes (matches degrade.to_explain_envelope shape)."""
        env = InterpretationEnvelope(
            command="rules",
            command_version="0.6.0",
            structured_output={},
            interpretation=None,
        )
        d = env.to_dict()
        assert d["interpretation"] is None


# ── Dispatcher ─────────────────────────────────────────────


class TestDispatcher:
    def test_applies_to_commands_registers_function(self):
        @applies_to_commands("rules")
        def explain(**kwargs):
            return None
        assert "explain" in registered_function_names()

    def test_unknown_command_in_decorator_raises(self):
        with pytest.raises(ValueError, match="unknown commands"):
            @applies_to_commands("rules", "bogus-command")  # noqa: F841
            def explain(**kwargs):
                return None

    def test_function_name_must_contain_known_short_name(self):
        with pytest.raises(ValueError, match="must contain exactly one"):
            @applies_to_commands("rules")
            def some_function_with_no_known_keyword(**kwargs):  # noqa: F841
                return None

    def test_applicable_functions_filters_by_command(self):
        @applies_to_commands("rules", "check")
        def explain(**kwargs):
            return None

        @applies_to_commands("rules")
        def cross_pattern_recognition(**kwargs):
            return None

        rules_fns = {rf.name for rf in applicable_functions("rules")}
        check_fns = {rf.name for rf in applicable_functions("check")}
        diff_fns = {rf.name for rf in applicable_functions("diff")}

        assert rules_fns == {"explain", "cross"}
        assert check_fns == {"explain"}
        assert diff_fns == set()

    def test_requested_filter_picks_subset(self):
        @applies_to_commands("rules")
        def explain(**kwargs):
            return None

        @applies_to_commands("rules")
        def grouping_function(**kwargs):
            return None

        names = [rf.name for rf in applicable_functions("rules", requested=["explain"])]
        assert names == ["explain"]

    def test_requested_all_runs_everything(self):
        @applies_to_commands("rules")
        def explain(**kwargs):
            return None

        @applies_to_commands("rules")
        def grouping_function(**kwargs):
            return None

        names = {rf.name for rf in applicable_functions("rules", requested=["all"])}
        assert names == {"explain", "group"}

    def test_unknown_requested_function_raises(self):
        with pytest.raises(ValueError, match="Unknown interpretation functions"):
            applicable_functions("rules", requested=["totally-made-up"])

    def test_unknown_command_raises(self):
        with pytest.raises(ValueError, match="Unknown command"):
            applicable_functions("not-a-command")

    def test_applicable_functions_returns_canonical_order(self):
        """Functions come back in KNOWN_FUNCTIONS order regardless of
        registration order — gives consumers stable iteration."""
        @applies_to_commands("rules")
        def cross_thing(**kwargs):
            return None

        @applies_to_commands("rules")
        def explain(**kwargs):
            return None

        names = [rf.name for rf in applicable_functions("rules")]
        # KNOWN_FUNCTIONS order: explain, group, contextualize, cross, narrative
        assert names == ["explain", "cross"]


# ── Context extractors ────────────────────────────────────


class TestContext:
    def test_pack_context_falls_back_when_manifest_missing(self):
        ctx = extract_pack_context("does-not-exist-pack")
        assert ctx.name == "does-not-exist-pack"
        assert ctx.standard is None

    def test_pack_context_pulls_standard_from_manifest(self):
        ctx = extract_pack_context("vv40")
        assert ctx.name == "vv40"
        assert ctx.standard == "ASME-VV40-2018"

    def test_cou_context_extracts_from_doc(self):
        doc = {
            "hasContextOfUse": {
                "name": "COU1: CFD Class II",
                "description": "Model Risk Level 2",
            }
        }
        ctx = extract_cou_context(doc)
        assert ctx.name == "COU1: CFD Class II"
        assert ctx.device_class == "Class II"
        assert ctx.model_risk_level == "MRL 2"

    def test_cou_context_handles_missing_cou(self):
        ctx = extract_cou_context({})
        assert ctx.name == ""

    def test_firing_contexts_built_from_rules_firings(self):
        firings = [
            {"patternId": "W-EP-04", "severity": "High", "hits": 6},
            {"patternId": "COMPOUND-01", "severity": "Critical", "hits": 1},
        ]
        contexts = extract_firing_contexts(firings, package_doc={}, pack_name="vv40")
        assert len(contexts) == 2
        assert contexts[0].pattern_id == "W-EP-04"
        assert contexts[0].severity == "High"
        assert contexts[0].hits == 6
        assert contexts[0].pack and contexts[0].pack.name == "vv40"

    def test_firing_context_to_template_vars_shape(self):
        ctx = FiringContext(
            pattern_id="W-EP-04",
            severity="High",
            hits=6,
            description="some description",
            pack=PackContext(name="vv40", standard="ASME-VV40-2018"),
            cou=CouContext(name="COU1"),
        )
        vars = ctx.to_template_vars()
        # Spec §6.3 namespace: firing, evidence, pack, cou
        assert set(vars) == {"firing", "evidence", "pack", "cou"}
        assert vars["firing"]["patternId"] == "W-EP-04"
        assert vars["firing"]["hits"] == 6
        assert vars["pack"]["name"] == "vv40"
        assert vars["cou"]["name"] == "COU1"

    def test_difference_contexts_label_only_in_correctly(self):
        contexts = extract_difference_contexts(
            only_a=["W-AR-02"],
            only_b=["W-EP-04", "W-CON-04"],
            weakeners_a=[{"patternId": "W-AR-02", "severity": "High"}],
            weakeners_b=[
                {"patternId": "W-EP-04", "severity": "Critical"},
                {"patternId": "W-CON-04", "severity": "Medium"},
            ],
            cou_identity_a={"cou_name": "A"},
            cou_identity_b={"cou_name": "B"},
            pack_name="vv40",
        )
        assert len(contexts) == 3
        assert contexts[0].pattern_id == "W-AR-02"
        assert contexts[0].only_in == "A"
        assert contexts[1].only_in == "B"
        assert contexts[2].only_in == "B"

    def test_violation_contexts_use_alias_keys(self):
        """ViolationContext extractor should pull from any of several alias
        keys since shacl_friendly's exact key naming has varied."""
        violations = [
            {
                "path": "uofa:hasContextOfUse",
                "severity": "High",
                "focus_node": "ex:package1",
                "fix_suggestion": "Add a Context of Use.",
            },
        ]
        contexts = extract_violation_contexts(violations, "vv40")
        assert len(contexts) == 1
        assert contexts[0].constraint_path == "uofa:hasContextOfUse"
        assert contexts[0].affected_node == "ex:package1"
        assert "Context of Use" in contexts[0].description


# ── Templates ──────────────────────────────────────────────


class TestTemplates:
    def test_template_path_returns_none_when_truly_missing(self):
        # As of v0.6.2 templates ship for every (command, function) pair
        # in the spec §2.6 matrix. Test against pairs that are genuinely
        # outside the matrix and will never have a template — group/cross/
        # narrative don't apply to diff per spec §2.6.
        assert has_template("diff", "group", "vv40") is False
        assert has_template("diff", "cross", "vv40") is False
        assert has_template("shacl", "cross", "vv40") is False
        assert has_template("shacl", "narrative", "vv40") is False

    def test_template_lookup_walks_pack_then_bundled(self, tmp_path, monkeypatch):
        """When a pack provides a template, it wins over the bundled default."""
        from uofa_cli.interpretation import templates as tmpl_module

        # Stub pack_dir to point at a temp tree
        pack_root = tmp_path / "fakepack"
        prompts_dir = pack_root / "prompts" / "rules"
        prompts_dir.mkdir(parents=True)
        (prompts_dir / "explain.jinja2").write_text("PACK TEMPLATE")

        monkeypatch.setattr("uofa_cli.paths.pack_dir", lambda name, root=None: pack_root if name == "fakepack" else None)

        path = tmpl_module.template_path("rules", "explain", "fakepack")
        assert path is not None
        assert path.read_text() == "PACK TEMPLATE"

    def test_render_uses_jinja2(self, tmp_path, monkeypatch):
        """Smoke test: render() actually invokes Jinja2 substitution."""
        from uofa_cli.interpretation import templates as tmpl_module

        pack_root = tmp_path / "fakepack"
        prompts_dir = pack_root / "prompts" / "rules"
        prompts_dir.mkdir(parents=True)
        (prompts_dir / "explain.jinja2").write_text("Pattern: {{ firing.patternId }}")

        monkeypatch.setattr("uofa_cli.paths.pack_dir", lambda name, root=None: pack_root if name == "fakepack" else None)
        # Reset the lru_cache so we don't pick up a stale template
        tmpl_module._compile_template.cache_clear()

        out = tmpl_module.render("rules", "explain", "fakepack",
                                 firing={"patternId": "W-EP-04"})
        assert out == "Pattern: W-EP-04"


# ── Pipeline ───────────────────────────────────────────────


class TestPipeline:
    def test_pipeline_returns_envelope_with_no_functions_registered(self):
        """Phase 4 contract: with nothing registered, pipeline still
        returns a well-formed envelope (functions_run=[], all per-function
        slots empty). Lets callers wire the API immediately."""
        backend = MockBackend()
        env = interpret_rules_output(
            structured_output={"firings": []},
            package_doc={},
            firings=[],
            options=InterpretationOptions(backend=backend),
        )
        assert isinstance(env, InterpretationEnvelope)
        assert env.command == "rules"
        assert env.interpretation.functions_run == []
        assert env.interpretation.explanations == []
        assert env.interpretation.interpretation_backend == "mock"

    def test_pipeline_runs_registered_function(self):
        captured = {}

        @applies_to_commands("rules")
        def explain(**kwargs):
            captured.update(kwargs)
            return {"explanations": [{"text": "hello"}]}

        backend = MockBackend()
        env = interpret_rules_output(
            structured_output={"firings": [{"patternId": "W-EP-04"}]},
            package_doc={},
            firings=[{"patternId": "W-EP-04", "severity": "High", "hits": 1}],
            options=InterpretationOptions(backend=backend),
        )
        # Function was invoked with the expected kwargs
        assert captured["command"] == "rules"
        assert captured["backend"] is backend
        assert len(captured["contexts"]) == 1
        # Result was merged into the envelope
        assert env.interpretation.functions_run == ["explain"]
        assert env.interpretation.explanations == [{"text": "hello"}]

    def test_pipeline_skips_functions_not_applicable_to_command(self):
        @applies_to_commands("rules")  # NOT diff
        def explain(**kwargs):
            return {"explanations": [{"text": "should not appear"}]}

        env = interpret_diff_output(
            structured_output={},
            options=InterpretationOptions(backend=MockBackend()),
        )
        assert env.interpretation.functions_run == []
        assert env.interpretation.explanations == []

    def test_pipeline_respects_requested_functions(self):
        @applies_to_commands("rules")
        def explain(**kwargs):
            return {"explanations": [{"id": "1"}]}

        @applies_to_commands("rules")
        def grouping_function(**kwargs):
            return {"groupings": {"k": "v"}}

        env = interpret_rules_output(
            structured_output={},
            package_doc={},
            firings=[],
            options=InterpretationOptions(
                backend=MockBackend(),
                functions=["explain"],  # exclude group
            ),
        )
        assert env.interpretation.functions_run == ["explain"]
        assert env.interpretation.groupings == {}

    def test_pipeline_merges_per_function_results(self):
        @applies_to_commands("rules")
        def explain(**kwargs):
            return {"explanations": [{"id": "e1"}, {"id": "e2"}]}

        @applies_to_commands("rules")
        def grouping_function(**kwargs):
            return {"groupings": {"theme1": ["e1", "e2"]}}

        env = interpret_rules_output(
            structured_output={},
            package_doc={},
            firings=[],
            options=InterpretationOptions(backend=MockBackend()),
        )
        assert env.interpretation.functions_run == ["explain", "group"]
        assert env.interpretation.explanations == [{"id": "e1"}, {"id": "e2"}]
        assert env.interpretation.groupings == {"theme1": ["e1", "e2"]}


# ── Spec invariants ────────────────────────────────────────


class TestSpecInvariants:
    def test_known_functions_match_spec_section_2_6(self):
        """Spec §2.6 enumerates exactly five: explain, group, contextualize, cross, narrative."""
        assert set(KNOWN_FUNCTIONS) == {"explain", "group", "contextualize", "cross", "narrative"}

    def test_known_commands_match_spec_section_3_1(self):
        """Spec §3.1: --explain applies to rules, check, diff, shacl."""
        assert set(KNOWN_COMMANDS) == {"rules", "check", "diff", "shacl"}

    def test_interpretation_version_is_set(self):
        # 0.4.0 — Round 1 follow-up: dropped `confidence` field after
        # bundled qwen3.5:4b returned 11/11 high regardless of explicit
        # criteria (model can't self-assess on this task). Three prose
        # fields remain. Cache invalidation is automatic via the
        # version-keyed cache key.
        assert INTERPRETATION_VERSION == "0.4.0"

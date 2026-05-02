"""Public interpretation pipeline (spec v0.4 §4.1).

One entry point per command — `interpret_<command>_output(...)`. Each:

1. Loads the appropriate context bundles from the structured output.
2. Asks the dispatcher which functions apply (filtered by user request).
3. Resolves an LLM backend (or accepts an injected one for tests).
4. Runs each applicable function, collecting per-function results.
5. Wraps everything in an InterpretationEnvelope.

In Phase 4 (P-A scaffolding), the function implementations are placeholders:
the dispatcher returns no functions until P-B onward register them. The
public API + envelope shape is locked in now so callers (per-command
`--explain` flag wiring in P-C extension, standalone `uofa explain` in P-L)
can be built against a stable surface.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from uofa_cli.interpretation.cache import ExplanationCache
from uofa_cli.interpretation.context import (
    extract_difference_contexts,
    extract_firing_contexts,
    extract_violation_contexts,
)
from uofa_cli.interpretation.dispatcher import applicable_functions
from uofa_cli.interpretation.envelope import (
    Command,
    InterpretationEnvelope,
    make_envelope,
)


@dataclass(frozen=True)
class InterpretationOptions:
    """Per-invocation knobs. Mirrors the spec §3.2 `--explain-*` flags.

    `backend` is an injected LLMBackend (test/programmatic use) — when None,
    `pipeline.run_pipeline` resolves one from the global config via
    `uofa_cli.llm.get_backend()`. `functions` is a list of canonical short
    names (`explain`, `group`, ...) or `["all"]` to run everything applicable.
    """

    functions: list[str] = field(default_factory=lambda: ["all"])
    max_items: int | None = None
    no_cache: bool = False
    backend: Any | None = None  # LLMBackend; typed as Any to avoid import cycle
    pack_name: str = "vv40"
    command_version: str = "0.6.0"


# ── Per-command entry points ────────────────────────────────


def interpret_rules_output(
    structured_output: dict | list,
    package_doc: dict,
    *,
    firings: list[dict] | None = None,
    jsonld_firings: list[dict] | None = None,
    individual_annotations: list[dict] | None = None,
    options: InterpretationOptions | None = None,
) -> InterpretationEnvelope:
    """Interpret a `rules` command's structured output.

    `structured_output` is the JSON shape that goes into the envelope's
    `structured_output` field — typically derived from `RulesResult` (e.g.
    `{"firings": result.firings, "stdout": result.raw_stdout}`). `firings`
    is the same list in canonical form, used to build per-firing contexts.

    Round 1 (P-B iteration) added two optional inputs that drive
    explanation grounding:

    - `jsonld_firings`: from `rules.parse_firings_jsonld()` — same firings
      but with `affected_nodes` (IRIs) + `escalation_sources` (for
      compounds). When provided, the FiringContexts get an
      `affected_evidence` list resolved against `package_doc`.
    - `individual_annotations`: from `rules.parse_individual_annotations()`
      — needed only when COMPOUND patterns are present so their
      `escalation_sources` blank-node refs can resolve to constituent
      firing summaries.

    Without the rich inputs, the function works in legacy mode (the
    standalone `uofa explain --from-file` path uses this when consuming
    a cached envelope that lacks rich data).
    """
    options = options or InterpretationOptions()
    contexts = extract_firing_contexts(
        firings or [], package_doc, options.pack_name,
        jsonld_firings=jsonld_firings,
        individual_annotations=individual_annotations,
    )
    return _run_pipeline(
        command="rules",
        structured_output=structured_output,
        contexts=contexts,
        options=options,
    )


def interpret_check_output(
    structured_output: dict,
    package_doc: dict,
    *,
    rules_firings: list[dict] | None = None,
    rules_jsonld_firings: list[dict] | None = None,
    rules_individual_annotations: list[dict] | None = None,
    shacl_violations: list[dict] | None = None,
    options: InterpretationOptions | None = None,
) -> InterpretationEnvelope:
    """Interpret a `check` command's composite output.

    Check has three sub-pipelines (shacl + integrity + rules) per spec §4.5;
    interpretation runs over the rules portion and the shacl portion (per
    matrix §2.6 — integrity has no interpretation). Round 1 adds the same
    `jsonld_firings` / `individual_annotations` enrichment inputs as
    `interpret_rules_output` (prefixed `rules_*` here for clarity).
    """
    options = options or InterpretationOptions()

    contexts: list = []
    if rules_firings:
        contexts.extend(
            extract_firing_contexts(
                rules_firings, package_doc, options.pack_name,
                jsonld_firings=rules_jsonld_firings,
                individual_annotations=rules_individual_annotations,
            )
        )
    if shacl_violations:
        contexts.extend(
            extract_violation_contexts(shacl_violations, options.pack_name)
        )
    return _run_pipeline(
        command="check",
        structured_output=structured_output,
        contexts=contexts,
        options=options,
    )


def interpret_diff_output(
    structured_output: dict,
    *,
    only_a: list[str] | None = None,
    only_b: list[str] | None = None,
    weakeners_a: list[dict] | None = None,
    weakeners_b: list[dict] | None = None,
    cou_identity_a: dict | None = None,
    cou_identity_b: dict | None = None,
    options: InterpretationOptions | None = None,
) -> InterpretationEnvelope:
    """Interpret a `diff` command's output (per-difference explanations).

    Spec §2.6: only the explain function applies to diff; group /
    contextualize / cross / narrative do not.
    """
    options = options or InterpretationOptions()
    contexts = extract_difference_contexts(
        only_a or [], only_b or [],
        weakeners_a or [], weakeners_b or [],
        cou_identity_a or {}, cou_identity_b or {},
        options.pack_name,
    )
    return _run_pipeline(
        command="diff",
        structured_output=structured_output,
        contexts=contexts,
        options=options,
    )


def interpret_shacl_output(
    structured_output: dict,
    *,
    violations: list[dict] | None = None,
    options: InterpretationOptions | None = None,
) -> InterpretationEnvelope:
    """Interpret a `shacl` command's output (per-violation explanations + grouping)."""
    options = options or InterpretationOptions()
    contexts = extract_violation_contexts(violations or [], options.pack_name)
    return _run_pipeline(
        command="shacl",
        structured_output=structured_output,
        contexts=contexts,
        options=options,
    )


# ── Internal: shared run loop ──────────────────────────────


def _run_pipeline(
    *,
    command: Command,
    structured_output: dict | list,
    contexts: list,
    options: InterpretationOptions,
) -> InterpretationEnvelope:
    """Run the dispatcher loop and assemble the envelope.

    In Phase 4 this is mostly skeleton — real function implementations
    register themselves in Phases 5-12 via `@applies_to_commands(...)`,
    and the dispatcher picks them up automatically. With nothing
    registered the envelope still comes back well-formed with empty
    per-function payloads and `functions_run=[]`.

    Cache lifecycle: opened once for the whole pipeline (so all functions
    in the same envelope share state), closed in finally. Functions
    receive it as a kwarg and decide whether to use it.
    """
    backend = _ensure_backend(options)
    functions = applicable_functions(command, requested=options.functions)

    explanations: list[dict] = []
    groupings: dict = {}
    contextual_severity: dict = {}
    cross_patterns: list[dict] = []
    narratives: list[dict] = []

    cache: ExplanationCache | None = None
    if not options.no_cache:
        try:
            cache = ExplanationCache().open()
        except Exception:  # noqa: BLE001 — cache failure should never break interpretation
            cache = None

    try:
        for rf in functions:
            result = rf.fn(
                command=command,
                contexts=contexts,
                structured_output=structured_output,
                backend=backend,
                options=options,
                cache=cache,
            )
            # Each function returns a dict shaped like {field_name: value}
            # where field_name is one of the per-function slots in
            # Interpretation (explanations, groupings, ...). Empty/None
            # returns mean "function ran but had nothing to add."
            if not result:
                continue
            explanations.extend(result.get("explanations", []))
            groupings.update(result.get("groupings", {}))
            contextual_severity.update(result.get("contextual_severity", {}))
            cross_patterns.extend(result.get("cross_patterns", []))
            narratives.extend(result.get("narratives", []))
    finally:
        if cache is not None:
            cache.close()

    return make_envelope(
        command=command,
        command_version=options.command_version,
        structured_output=structured_output,
        backend_name=backend.name() if backend else "none",
        model_name=backend.model() if backend else "none",
        functions_run=[rf.name for rf in functions],
        explanations=explanations,
        groupings=groupings,
        contextual_severity=contextual_severity,
        cross_patterns=cross_patterns,
        narratives=narratives,
    )


def _ensure_backend(options: InterpretationOptions):
    """Return the explicit backend from options, else resolve the default."""
    if options.backend is not None:
        return options.backend
    from uofa_cli.llm import get_backend  # noqa: PLC0415
    return get_backend()

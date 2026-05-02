"""LLM-driven interpretation pipeline (spec v0.4).

Public surface:
- `pipeline.interpret_<command>_output(...)` — the four entry points called
  from each command's `run()` when `--explain` is set, or from the
  standalone `uofa explain` command.
- `dispatcher.applies_to_commands(...)` — decorator used by per-function
  modules in `functions/` to register applicability.
- `envelope.InterpretationEnvelope` — the JSON wrapper returned by every
  entry point (spec §4.5).
- `degrade.make_degradation_notice(...)` — graceful-degradation notice
  formatter for spec §3.7 failure modes.

Phase 4 (P-A) ships the scaffolding; per-function implementations
(`functions/explain.py`, etc.) register themselves at import time and
land over Phases 5-12.
"""

from __future__ import annotations

from uofa_cli.interpretation.context import (
    CouContext,
    DifferenceContext,
    FiringContext,
    PackContext,
    ViolationContext,
    extract_cou_context,
    extract_difference_contexts,
    extract_firing_contexts,
    extract_pack_context,
    extract_violation_contexts,
)
from uofa_cli.interpretation.degrade import (
    DegradationNotice,
    Suggestion,
    make_degradation_notice,
)
from uofa_cli.interpretation.dispatcher import (
    KNOWN_COMMANDS,
    KNOWN_FUNCTIONS,
    applicable_functions,
    applies_to_commands,
    registered_function_names,
)
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
from uofa_cli.interpretation.pipeline import (
    InterpretationOptions,
    interpret_check_output,
    interpret_diff_output,
    interpret_rules_output,
    interpret_shacl_output,
)
from uofa_cli.interpretation.templates import (
    has_template,
    load_template,
    render,
    template_path,
)

# Side-effect import: every module under `functions/` is decorated with
# `@applies_to_commands(...)` at module-load time, which registers it with
# the dispatcher. Importing the package once at `interpretation` import is
# enough — the dispatcher then sees them all.
from uofa_cli.interpretation import functions  # noqa: F401, E402

__all__ = [
    # Pipeline
    "InterpretationOptions",
    "interpret_rules_output",
    "interpret_check_output",
    "interpret_diff_output",
    "interpret_shacl_output",
    # Envelope
    "InterpretationEnvelope",
    "Interpretation",
    "INTERPRETATION_VERSION",
    "make_envelope",
    # Dispatcher
    "applies_to_commands",
    "applicable_functions",
    "registered_function_names",
    "KNOWN_FUNCTIONS",
    "KNOWN_COMMANDS",
    # Context
    "FiringContext",
    "DifferenceContext",
    "ViolationContext",
    "PackContext",
    "CouContext",
    "extract_firing_contexts",
    "extract_difference_contexts",
    "extract_violation_contexts",
    "extract_pack_context",
    "extract_cou_context",
    # Templates
    "load_template",
    "render",
    "template_path",
    "has_template",
    # Formatters
    "render_envelope",
    "render_text",
    "render_json",
    "render_markdown",
    "render_html",
    # Degradation
    "DegradationNotice",
    "Suggestion",
    "make_degradation_notice",
]

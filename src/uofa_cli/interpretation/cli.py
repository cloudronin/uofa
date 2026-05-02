"""Shared `--explain*` CLI plumbing for the four target commands.

Spec v0.4 §3.2 enumerates the explain-specific options; rather than
duplicating the argparse setup in each command, this module provides:

- `add_explain_arguments(parser)` — registers the standard flag set
- `args_to_options(args, pack_name) -> InterpretationOptions`
- `print_envelope(env, format)` — renders to text/json/markdown
- `print_degradation(exc, mode, format)` — handles graceful degradation
  per spec §3.7

Each command's `run()` calls these after running its primary work.
"""

from __future__ import annotations

import json as _json
import sys
from typing import Literal

from uofa_cli.interpretation.degrade import make_degradation_notice
from uofa_cli.interpretation.envelope import InterpretationEnvelope
from uofa_cli.interpretation.formatters import render_envelope
from uofa_cli.interpretation.pipeline import InterpretationOptions
from uofa_cli.llm.errors import LLMError


def add_explain_arguments(parser) -> None:
    """Register the `--explain*` flag set on a command's argparse parser.

    Identical across rules/check/diff/shacl per spec §3.2 — duplicating
    the wiring per command would be a maintenance trap.
    """
    parser.add_argument(
        "--explain", action="store_true",
        help="run the interpretation pipeline after the primary analysis",
    )
    parser.add_argument(
        "--explain-functions", default=None,
        help="comma-separated list of interpretation functions to run "
             "(values: explain, group, contextualize, cross, narrative). "
             "Default: all applicable for the command.",
    )
    parser.add_argument(
        "--explain-format", default=None,
        choices=["text", "json", "markdown", "html"],
        help="output format for the interpretation block. Default: same as "
             "the command's primary --format, falling back to text.",
    )
    parser.add_argument(
        "--explain-backend", default=None,
        choices=["ollama", "anthropic", "openai", "openai-compatible", "bundled", "mock"],
        help="LLM backend for explain (overrides [llm] backend in uofa.toml)",
    )
    parser.add_argument(
        "--explain-model", default=None,
        help="model name on the chosen backend (overrides [llm] model)",
    )
    parser.add_argument(
        "--explain-base-url", default=None,
        help="base URL for openai-compatible backends",
    )
    parser.add_argument(
        "--explain-max-items", type=int, default=None,
        help="limit interpretation to top N items by severity",
    )
    parser.add_argument(
        "--explain-no-cache", action="store_true",
        help="bypass cached interpretation results",
    )


def args_to_options(args, *, pack_name: str = "vv40") -> InterpretationOptions:
    """Convert argparse-parsed args into InterpretationOptions.

    Resolves the backend from the `--explain-*` flags via the unified
    LLM config resolver (spec §3.6 precedence). Callers pass `pack_name`
    so the right pack templates are selected.
    """
    # Build cli_overrides for the LLM config resolver if the user passed
    # any --explain-backend / --explain-model / --explain-base-url flag.
    backend = None
    if any((args.explain_backend, args.explain_model, args.explain_base_url)):
        from uofa_cli.llm import resolve_llm_config, get_backend
        cli_overrides: dict = {}
        if args.explain_backend:
            cli_overrides["backend"] = args.explain_backend
        if args.explain_model:
            cli_overrides["model"] = args.explain_model
        if args.explain_base_url:
            cli_overrides["base_url"] = args.explain_base_url
        # Convention env var defaults (mirror extract_cmd's logic)
        if cli_overrides.get("backend") in ("anthropic", "openai"):
            cli_overrides.setdefault(
                "api_key_env",
                {"anthropic": "ANTHROPIC_API_KEY", "openai": "OPENAI_API_KEY"}[cli_overrides["backend"]],
            )
        config = resolve_llm_config(cli_overrides=cli_overrides)
        backend = get_backend(config)

    functions: list[str] = ["all"]
    if args.explain_functions:
        functions = [name.strip() for name in args.explain_functions.split(",") if name.strip()]

    return InterpretationOptions(
        functions=functions,
        max_items=args.explain_max_items,
        no_cache=args.explain_no_cache,
        backend=backend,
        pack_name=pack_name,
    )


# ── Rendering ──────────────────────────────────────────────


Format = Literal["text", "json", "markdown", "html"]


def print_envelope(env: InterpretationEnvelope, *, format: Format = "text") -> None:
    """Render `env` to the chosen format and print to stdout.

    Thin shell over `formatters.render_envelope`; tests / programmatic
    consumers wanting the rendered string call the formatter directly.
    """
    rendered = render_envelope(env, format=format)
    if rendered:
        # Strip trailing newline so print's own newline doesn't double-up
        # for formats that already terminate (text/markdown/html do; json
        # doesn't). Conditional dropping keeps things tidy in all cases.
        print(rendered, end="" if rendered.endswith("\n") else "\n")


def print_degradation(
    exc: LLMError,
    *,
    mode: Literal["explain", "extract"] = "explain",
    format: Format = "text",
    command: str | None = None,
    structured_output=None,
) -> None:
    """Print a graceful-degradation notice (spec §3.7) for an LLM error.

    Returns nothing; caller decides exit code (explain → 0, extract → 1).
    """
    notice = make_degradation_notice(exc, mode=mode)
    if format == "json":
        if mode == "extract":
            envelope = notice.to_extract_envelope()
        else:
            envelope = notice.to_explain_envelope(
                command=command or "unknown",
                structured_output=structured_output if structured_output is not None else {},
            )
        print(_json.dumps(envelope, indent=2))
        return
    # text / markdown fall through to the bracket-wrapped notice
    print()
    print(notice.to_text(), file=sys.stderr if mode == "extract" else sys.stdout)

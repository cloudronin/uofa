"""uofa explain — interpret pre-existing structured output (spec v0.4 §3.3).

Operates on JSON output captured from a previous `uofa rules/check/diff/shacl
--explain --explain-format json` invocation. Useful for re-rendering, format
conversion, or running interpretation on cached output without re-running
the underlying analysis.

Usage:
    uofa explain --from-file FILE [OPTIONS]
    uofa explain --from-stdin [OPTIONS]

Spec §3.3 enumerates the option set, mirroring `--explain-*` on the four
target commands but without the prefix (since this command IS explain). The
input source is mutually exclusive (file or stdin) and required.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from uofa_cli.output import error, info

HELP = "interpret pre-existing structured output from rules/check/diff/shacl"


def add_arguments(parser):
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--from-file", type=Path, dest="from_file",
                     help="read structured output from FILE")
    src.add_argument("--from-stdin", action="store_true", dest="from_stdin",
                     help="read structured output from stdin")
    parser.add_argument("--input-type", dest="input_type",
                        choices=["rules", "check", "diff", "shacl"],
                        help="override auto-detection of input type")
    parser.add_argument("--functions", default=None,
                        help="comma-separated list of interpretation functions to run")
    parser.add_argument("--format", default="text",
                        choices=["text", "json", "markdown"],
                        help="output format (default: text)")
    parser.add_argument("--max-items", type=int, default=None, dest="max_items",
                        help="limit interpretation to top N items by severity")
    parser.add_argument("--no-cache", action="store_true", dest="no_cache",
                        help="bypass cached interpretation results")
    parser.add_argument("--backend", default=None,
                        choices=["ollama", "anthropic", "openai", "openai-compatible", "bundled", "mock"],
                        help="LLM backend (overrides [llm] backend in uofa.toml)")
    parser.add_argument("--model", default=None,
                        help="model name on the chosen backend")
    parser.add_argument("--base-url", default=None, dest="base_url",
                        help="base URL for openai-compatible backends")
    # NOTE: --pack is a global flag inherited from the parent parser; we
    # read `args.pack` in run() rather than redefining the option here.


def run(args) -> int:
    # ── 1. Read input ────────────────────────────────────────
    try:
        if args.from_stdin:
            text = sys.stdin.read()
        else:
            text = args.from_file.read_text(encoding="utf-8")
    except OSError as exc:
        error(f"Could not read input: {exc}")
        return 1

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        error(f"Input is not valid JSON: {exc}")
        return 1

    # ── 2. Detect input type ─────────────────────────────────
    input_type = args.input_type or _detect_input_type(data)
    if input_type is None:
        error(
            "Could not detect input type from JSON shape. "
            "Pass --input-type rules|check|diff|shacl explicitly."
        )
        info(f"  Top-level keys seen: {sorted(data.keys()) if isinstance(data, dict) else type(data).__name__}")
        return 1

    # ── 3. Build interpretation options ──────────────────────
    options = _build_options(args)

    # ── 4. Route to the right interpret_*_output() ──────────
    from uofa_cli.interpretation.cli import print_degradation, print_envelope
    from uofa_cli.llm.errors import LLMError

    try:
        env = _route_and_interpret(input_type, data, options)
    except LLMError as exc:
        print_degradation(
            exc, mode="explain", format=args.format,
            command=input_type,
            structured_output=_unwrap_structured(data),
        )
        # Spec §3.7: explain graceful degradation → exit 0
        return 0

    # ── 5. Render the envelope ───────────────────────────────
    print_envelope(env, format=args.format)
    return 0


# ── Auto-detection ─────────────────────────────────────────


def _detect_input_type(data) -> str | None:
    """Inspect JSON shape and return the input type, or None if unclear.

    Detection order:
      1. Envelope: top-level `command` field with a known value (matches
         output from `--explain-format json` on any of the four commands).
      2. Shape distinguishers (most specific first):
         - `only_a` or `only_b` present → diff
         - `shacl` AND `rules` keys → check
         - `violations` AND `conforms` → shacl
         - `firings` → rules
    """
    if not isinstance(data, dict):
        return None

    cmd = data.get("command")
    if cmd in ("rules", "check", "diff", "shacl"):
        return cmd

    # Unwrap envelope if present so we can sniff the structured_output shape
    inner = data.get("structured_output", data) if isinstance(data, dict) else data
    if not isinstance(inner, dict):
        return None

    if "only_a" in inner or "only_b" in inner or "divergence_count" in inner:
        return "diff"
    if "shacl" in inner and "rules" in inner:
        return "check"
    if "violations" in inner and "conforms" in inner:
        return "shacl"
    if "firings" in inner:
        return "rules"
    return None


def _unwrap_structured(data):
    """Return the structured_output if `data` is a full envelope, else `data` itself."""
    if isinstance(data, dict) and "structured_output" in data:
        return data["structured_output"]
    return data


# ── Options builder (mirrors interpretation.cli.args_to_options but
#    with the standalone command's flag names) ────────────────


def _build_options(args):
    from uofa_cli.interpretation import InterpretationOptions

    backend = None
    if args.backend or args.model or args.base_url:
        from uofa_cli.llm import get_backend, resolve_llm_config
        cli_overrides: dict = {}
        if args.backend:
            cli_overrides["backend"] = args.backend
        if args.model:
            cli_overrides["model"] = args.model
        if args.base_url:
            cli_overrides["base_url"] = args.base_url
        if cli_overrides.get("backend") in ("anthropic", "openai"):
            cli_overrides.setdefault(
                "api_key_env",
                {"anthropic": "ANTHROPIC_API_KEY", "openai": "OPENAI_API_KEY"}[cli_overrides["backend"]],
            )
        backend = get_backend(resolve_llm_config(cli_overrides=cli_overrides))

    functions: list[str] = ["all"]
    if args.functions:
        functions = [n.strip() for n in args.functions.split(",") if n.strip()]

    pack_name = getattr(args, "pack", None) or "vv40"
    if isinstance(pack_name, list):
        # The parent parser stores --pack as a list (--pack can be repeated)
        pack_name = pack_name[0] if pack_name else "vv40"
    return InterpretationOptions(
        functions=functions,
        max_items=args.max_items,
        no_cache=args.no_cache,
        backend=backend,
        pack_name=pack_name,
    )


# ── Routing ────────────────────────────────────────────────


def _route_and_interpret(input_type: str, data, options):
    """Dispatch to the right `interpret_<command>_output()`.

    `data` may be a full envelope (with `structured_output` key) or just the
    structured payload. We extract the relevant fields per command and pass
    them through. `package_doc` is unavailable from cached output (the
    package itself isn't in the envelope), so context extraction loses the
    COU info — interpretation functions handle this gracefully by treating
    missing context as an empty CouContext.
    """
    from uofa_cli.interpretation import (
        interpret_check_output,
        interpret_diff_output,
        interpret_rules_output,
        interpret_shacl_output,
    )

    structured = _unwrap_structured(data)

    if input_type == "rules":
        firings = structured.get("firings", []) if isinstance(structured, dict) else []
        return interpret_rules_output(
            structured_output=structured,
            package_doc={},
            firings=firings,
            options=options,
        )
    if input_type == "shacl":
        violations = structured.get("violations", []) if isinstance(structured, dict) else []
        return interpret_shacl_output(
            structured_output=structured,
            violations=violations,
            options=options,
        )
    if input_type == "diff":
        return interpret_diff_output(
            structured_output=structured,
            only_a=structured.get("only_a", []) if isinstance(structured, dict) else [],
            only_b=structured.get("only_b", []) if isinstance(structured, dict) else [],
            weakeners_a=structured.get("weakeners_a", []) if isinstance(structured, dict) else [],
            weakeners_b=structured.get("weakeners_b", []) if isinstance(structured, dict) else [],
            cou_identity_a=structured.get("cou_identity_a", {}) if isinstance(structured, dict) else {},
            cou_identity_b=structured.get("cou_identity_b", {}) if isinstance(structured, dict) else {},
            options=options,
        )
    if input_type == "check":
        rules_data = structured.get("rules", {}) if isinstance(structured, dict) else {}
        shacl_data = structured.get("shacl", {}) if isinstance(structured, dict) else {}
        rules_firings = rules_data.get("firings", []) if isinstance(rules_data, dict) else []
        shacl_violations = shacl_data.get("violations", []) if isinstance(shacl_data, dict) else None
        return interpret_check_output(
            structured_output=structured,
            package_doc={},
            rules_firings=rules_firings,
            shacl_violations=shacl_violations,
            options=options,
        )
    raise ValueError(f"Unknown input_type: {input_type!r}")

"""uofa shacl — SHACL validation with friendly error messages.

Spec v0.4 §4.1 / §4.5: `run_structured(args)` returns a typed `ShaclResult`
the interpretation pipeline can consume. `run(args)` is a thin shell that
calls it and prints — preserved bit-for-bit so existing CLI behavior is
unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from uofa_cli.output import step_header
from uofa_cli.shacl_friendly import run_shacl_multi, print_results
from uofa_cli import paths

HELP = "validate against SHACL profiles (C2 completeness)"


@dataclass(frozen=True)
class ShaclResult:
    """Structured result of a SHACL validation pass.

    `violations` is the same list of dicts that shacl_friendly emits internally
    (each carrying `severity`, `path`, `message`, `focus_node`, etc.). Empty
    when `conforms` is True.

    `raw_text` is populated only in `--raw` mode; that mode bypasses the
    friendly formatter entirely and emits pyshacl's native text. Captured
    here so the interpretation pipeline can still operate on it if needed.
    """

    file: Path
    conforms: bool
    violations: list[dict] = field(default_factory=list)
    raw_text: str | None = None
    exit_code: int = 0


def add_arguments(parser):
    parser.add_argument("file", type=Path, help="UofA JSON-LD file to validate")
    parser.add_argument("--raw", action="store_true", help="show raw pyshacl output instead of friendly messages")
    from uofa_cli.interpretation.cli import add_explain_arguments
    add_explain_arguments(parser)


def run_structured(args) -> ShaclResult:
    """Run SHACL validation and return a typed result.

    Does NOT print — `run()` is the I/O shell. Useful for the interpretation
    pipeline (spec §2.6 maps shacl → explain/group/contextualize) and for
    tests that want to assert on structured data without parsing stdout.
    """
    if not args.file.exists():
        raise FileNotFoundError(f"File not found: {args.file}")

    shacl_paths = paths.all_shacl_schemas(active=paths.resolve_active_packs(args))

    if args.raw:
        from pyshacl import validate as shacl_validate
        from uofa_cli.shacl_friendly import (
            _load_data_graph, _collect_violations, format_drilled_violations_text,
        )
        shapes_graph = _load_combined_shapes(shacl_paths)
        # Load data via rdflib first to dodge the pyshacl JSON-LD path bug
        # and to give us the parsed Graph for the drill-in.
        data_graph = _load_data_graph(args.file)
        conforms, results_graph, results_text = shacl_validate(
            data_graph=data_graph,
            shacl_graph=shapes_graph,
        )

        # Even in --raw, run the drill-in when there's an OR-constraint
        # failure on the profile dispatcher (the user's complaint was that
        # --raw without drill-in is unusable). Append the drilled-in
        # detail AFTER the pyshacl text so tool-integration consumers can
        # still parse the raw report from the top.
        violations = [] if conforms else _collect_violations(
            data_graph, results_graph, shapes_graph,
        )
        drilled_text = format_drilled_violations_text(violations)
        combined_text = results_text + drilled_text if drilled_text else results_text

        return ShaclResult(
            file=args.file,
            conforms=bool(conforms),
            violations=violations,
            raw_text=combined_text,
            exit_code=0 if conforms else 1,
        )

    conforms, violations = run_shacl_multi(args.file, shacl_paths)
    return ShaclResult(
        file=args.file,
        conforms=bool(conforms),
        violations=list(violations),
        exit_code=0 if conforms else 1,
    )


def run(args) -> int:
    step_header("C2: SHACL profile validation")
    result = run_structured(args)
    if result.raw_text is not None:
        print(result.raw_text)
    else:
        print_results(result.conforms, result.violations)

    # ── --explain pipeline (spec §3.1) ────────────────────────
    # Per spec §2.6, shacl supports explain/group/contextualize. Skipped
    # when the package conforms (no violations to interpret).
    if getattr(args, "explain", False) and not result.conforms:
        _run_explain(args, result)

    return result.exit_code


def _run_explain(args, result: ShaclResult) -> None:
    """Invoke the interpretation pipeline for shacl violations."""
    from uofa_cli.interpretation import interpret_shacl_output
    from uofa_cli.interpretation.cli import (
        args_to_options, print_degradation, print_envelope,
    )
    from uofa_cli.llm.errors import LLMError

    pack_name = paths.resolve_active_packs(args)[0]
    try:
        env = interpret_shacl_output(
            structured_output={"violations": result.violations, "conforms": result.conforms},
            violations=result.violations,
            options=args_to_options(args, pack_name=pack_name),
        )
    except LLMError as exc:
        print_degradation(
            exc, mode="explain", format=args.explain_format or "text",
            command="shacl",
            structured_output={"violations": result.violations, "conforms": result.conforms},
        )
        return

    print_envelope(env, format=args.explain_format or "text")


def _load_combined_shapes(shacl_paths: list[Path]):
    """Load and combine multiple SHACL shape files into one rdflib Graph."""
    from rdflib import Graph
    combined = Graph()
    for p in shacl_paths:
        combined.parse(str(p), format="turtle")
    return combined

"""uofa validate — SHACL validation on all example UofA files."""

from pathlib import Path

from uofa_cli.output import step_header, result_line, color
from uofa_cli.shacl_friendly import run_shacl, print_violations
from uofa_cli import paths

HELP = "validate all examples against SHACL profiles"

_EXCLUDE_DIRS = {"templates"}


def add_arguments(parser):
    parser.add_argument("--dir", type=Path, help="directory to scan (default: examples/)")


def run(args) -> int:
    examples = args.dir or paths.examples_dir()
    if not examples.exists():
        raise FileNotFoundError(f"Examples directory not found: {examples}")

    step_header("SHACL validation: all examples")

    files = sorted(
        f for f in examples.rglob("*.jsonld")
        if not any(part in _EXCLUDE_DIRS for part in f.parts)
    )

    if not files:
        result_line("No .jsonld files found", False)
        return 1

    passed = 0
    failed = 0
    shacl = paths.shacl_schema()

    for f in files:
        conforms, violations = run_shacl(f, shacl)
        rel = f.relative_to(examples.parent) if examples.parent in f.parents else f
        result_line(str(rel), conforms)
        if conforms:
            passed += 1
        else:
            failed += 1
            print_violations(violations)

    print()
    total = passed + failed
    if failed == 0:
        result_line(f"All {total} example(s) conform", True)
    else:
        result_line(f"{failed}/{total} example(s) failed", False)

    return 0 if failed == 0 else 1

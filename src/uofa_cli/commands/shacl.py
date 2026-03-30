"""uofa shacl — SHACL validation with friendly error messages."""

from pathlib import Path

from uofa_cli.output import step_header
from uofa_cli.shacl_friendly import run_shacl, print_results
from uofa_cli import paths

HELP = "validate against SHACL profiles (C2 completeness)"


def add_arguments(parser):
    parser.add_argument("file", type=Path, help="UofA JSON-LD file to validate")
    parser.add_argument("--raw", action="store_true", help="show raw pyshacl output instead of friendly messages")


def run(args) -> int:
    if not args.file.exists():
        raise FileNotFoundError(f"File not found: {args.file}")

    step_header("C2: SHACL profile validation")

    if args.raw:
        from pyshacl import validate as shacl_validate
        conforms, _, results_text = shacl_validate(
            data_graph=str(args.file),
            shacl_graph=str(paths.shacl_schema()),
            data_graph_format="json-ld",
        )
        print(results_text)
        return 0 if conforms else 1

    conforms, violations = run_shacl(args.file, paths.shacl_schema())
    print_results(conforms, violations)
    return 0 if conforms else 1

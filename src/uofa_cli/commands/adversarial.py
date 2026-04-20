"""uofa adversarial — generate synthetic credibility evidence packages."""

from __future__ import annotations

from pathlib import Path

HELP = "generate synthetic credibility evidence packages for coverage experiments"


def add_arguments(parser):
    sub = parser.add_subparsers(
        dest="adversarial_command",
        title="adversarial commands",
        metavar="{generate}",
    )

    gen = sub.add_parser(
        "generate",
        help="generate a batch of synthetic packages from a spec YAML",
    )
    gen.add_argument("--spec", type=Path, required=True, help="path to adversarial spec YAML")
    gen.add_argument("--out", type=Path, required=True, help="output directory (created if missing)")
    gen.add_argument("--model", default=None, help="override generation model from spec")
    gen.add_argument(
        "--max-retries", type=int, default=3, help="SHACL retries per variant (default: 3)"
    )
    gen.add_argument(
        "--dry-run", action="store_true", help="render prompts to stdout without calling the LLM"
    )
    gen.add_argument(
        "--strict-circularity",
        action="store_true",
        help="exit 4 if generation model matches extract model (recommended for coverage experiments)",
    )
    gen.add_argument(
        "--allow-circular-model",
        action="store_true",
        help="explicit opt-in required when --model matches the extract model",
    )
    gen.add_argument(
        "--force",
        action="store_true",
        help="overwrite existing manifest with matching spec_id",
    )


def run(args) -> int:
    if getattr(args, "adversarial_command", None) == "generate":
        from uofa_cli.adversarial.generator import run_generate
        return run_generate(args)

    # No subcommand: print help-style usage.
    print("usage: uofa adversarial <subcommand>")
    print()
    print("subcommands:")
    print("  generate   generate a batch of synthetic packages from a spec")
    return 0

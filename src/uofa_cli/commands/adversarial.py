"""uofa adversarial — generate, run, and analyze synthetic credibility
evidence packages for Phase 2 coverage experiments."""

from __future__ import annotations

from pathlib import Path

HELP = "generate / orchestrate / classify synthetic credibility evidence packages"


def add_arguments(parser):
    sub = parser.add_subparsers(
        dest="adversarial_command",
        title="adversarial commands",
        metavar="{generate,run,analyze}",
    )

    # ----- generate (Phase 1 single-spec entry point) -----
    gen = sub.add_parser(
        "generate",
        help="generate a batch of synthetic packages from a single spec YAML",
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

    # ----- run (Phase 2 batch orchestration, spec §9) -----
    run_sub = sub.add_parser(
        "run",
        help="batch-orchestrate adversarial generation across one or more spec directories",
    )
    run_sub.add_argument(
        "--batch",
        type=Path,
        action="append",
        required=True,
        help="directory of spec YAMLs to process (may be repeated)",
    )
    run_sub.add_argument(
        "--out", type=Path, required=True, help="output root directory"
    )
    run_sub.add_argument(
        "--model", default=None, help="override generation model from each spec"
    )
    run_sub.add_argument(
        "--max-cost",
        type=float,
        default=None,
        help="halt the batch when accumulated estimated cost (USD) reaches this threshold",
    )
    run_sub.add_argument(
        "--parallel",
        type=int,
        default=1,
        help="number of concurrent spec generations (default: 1)",
    )
    run_sub.add_argument(
        "--resume",
        action="store_true",
        help="skip specs whose output already contains a valid manifest with matching spec_hash",
    )
    run_sub.add_argument(
        "--strict-circularity",
        action="store_true",
        help="exit 4 if generation model matches extract model",
    )
    run_sub.add_argument(
        "--allow-circular-model",
        action="store_true",
        help="explicit opt-in required when --model matches the extract model",
    )
    run_sub.add_argument(
        "--max-retries", type=int, default=3, help="SHACL retries per variant"
    )
    run_sub.add_argument(
        "--dry-run", action="store_true", help="dry-run mode (per-spec render, no LLM)"
    )

    # ----- analyze (Phase 2 outcome classifier, spec §10) -----
    an = sub.add_parser(
        "analyze",
        help="classify a batch's outcomes and write CSV + HTML coverage reports",
    )
    an.add_argument(
        "--in", dest="in_dir", type=Path, required=True,
        help="batch output directory (the --out from `uofa adversarial run`)",
    )
    an.add_argument(
        "--out", type=Path, required=True, help="report output directory (created if missing)"
    )
    an.add_argument(
        "--check-pack", default="vv40", help="pack to use for `uofa check` (default: vv40)"
    )


def run(args) -> int:
    cmd = getattr(args, "adversarial_command", None)
    if cmd == "generate":
        from uofa_cli.adversarial.generator import run_generate
        return run_generate(args)
    if cmd == "run":
        from uofa_cli.adversarial.runner import run_batch
        return run_batch(args)
    if cmd == "analyze":
        from uofa_cli.adversarial.classifier import run_analyze
        return run_analyze(args)

    print("usage: uofa adversarial <subcommand>")
    print()
    print("subcommands:")
    print("  generate   generate from a single spec (Phase 1)")
    print("  run        batch-orchestrate generation across spec directories (Phase 2)")
    print("  analyze    classify a batch's outcomes; emit CSV + HTML reports (Phase 2)")
    return 0

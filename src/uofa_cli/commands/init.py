"""uofa init — scaffold a new UofA project."""

import json
import re
from pathlib import Path

from uofa_cli.integrity import generate_keypair
from uofa_cli.output import step_header, result_line, info
from uofa_cli import paths

HELP = "scaffold a new UofA project (template + keys)"


def add_arguments(parser):
    parser.add_argument("name", help="project name (e.g., my-turbine-study)")
    parser.add_argument("--profile", choices=["minimal", "complete"], default="minimal",
                        help="starting profile (default: minimal)")
    parser.add_argument("--dir", type=Path, default=Path("."), help="parent directory (default: cwd)")


def run(args) -> int:
    project_dir = args.dir / args.name
    if project_dir.exists():
        raise FileExistsError(f"Directory already exists: {project_dir}")

    step_header(f"Initializing UofA project: {args.name}")

    # ── Create directory ──────────────────────────────────────
    project_dir.mkdir(parents=True)
    keys_dir = project_dir / "keys"
    keys_dir.mkdir()

    # ── Copy and customize template ───────────────────────────
    template_name = f"uofa-{'minimal' if args.profile == 'minimal' else 'complete'}-skeleton.jsonld"
    template = paths.templates_dir() / template_name

    if not template.exists():
        raise FileNotFoundError(f"Template not found: {template}")

    with open(template, "r") as f:
        content = f.read()

    # Substitute placeholders
    content = content.replace("example.org/my-project", f"example.org/{args.name}")
    content = content.replace("YOUR PROJECT NAME", args.name)
    # Ensure context is a distributable URL (not a local relative path)
    content = content.replace(
        '"../../spec/context/v0.4.jsonld"',
        '"https://raw.githubusercontent.com/cloudronin/uofa/main/spec/context/v0.4.jsonld"'
    )
    content = content.replace(
        '"../../../spec/context/v0.4.jsonld"',
        '"https://raw.githubusercontent.com/cloudronin/uofa/main/spec/context/v0.4.jsonld"'
    )

    output_file = project_dir / f"{args.name}-cou1.jsonld"
    with open(output_file, "w") as f:
        f.write(content)

    result_line(f"Template ({args.profile})", True, str(output_file))

    # ── Generate keypair ──────────────────────────────────────
    key_path = keys_dir / f"{args.name}.key"
    key_path, pub_path = generate_keypair(key_path)
    result_line("Keypair generated", True, str(key_path.name))

    # ── Create .gitignore ─────────────────────────────────────
    gitignore = project_dir / ".gitignore"
    gitignore.write_text("# Private keys — never commit\n*.key\n")
    result_line(".gitignore", True)

    # ── Next steps ────────────────────────────────────────────
    print()
    info("Next steps:")
    info(f"  1. Edit {output_file}")
    info(f"  2. Sign: uofa sign {output_file} --key {key_path}")
    info(f"  3. Validate: uofa check {output_file}")

    return 0

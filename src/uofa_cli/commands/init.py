"""uofa init — scaffold a new UofA project."""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

from uofa_cli.integrity import generate_keypair
from uofa_cli.output import step_header, result_line, info
from uofa_cli import paths

HELP = "scaffold a new UofA project (template + keys + uofa.toml)"


def add_arguments(parser):
    parser.add_argument("name", help="project name (e.g., my-turbine-study)")
    parser.add_argument("--profile", choices=["minimal", "complete"], default="complete",
                        help="starting profile (default: complete)")
    parser.add_argument("--dir", type=Path, default=Path("."), help="parent directory (default: cwd)")
    parser.add_argument("--provider", default="ollama",
                        help="LLM provider for uofa extract (default: ollama)")
    parser.add_argument("--model", default="llama3.2",
                        help="LLM model for uofa extract (default: llama3.2)")


def run(args) -> int:
    project_dir = args.dir / args.name
    if project_dir.exists():
        raise FileExistsError(f"Directory already exists: {project_dir}")

    step_header(f"Initializing UofA project: {args.name}")

    # ── Create directories ───────────────────────────────────
    project_dir.mkdir(parents=True)
    keys_dir = project_dir / "keys"
    keys_dir.mkdir()
    evidence_dir = project_dir / "evidence"
    evidence_dir.mkdir()
    (evidence_dir / ".gitkeep").touch()

    # ── Copy and customize JSON-LD template ───────────────────
    template_name = f"uofa-{'minimal' if args.profile == 'minimal' else 'complete'}-skeleton.jsonld"
    template = paths.templates_dir() / template_name

    if not template.exists():
        raise FileNotFoundError(f"Template not found: {template}")

    with open(template, "r") as f:
        content = f.read()

    content = content.replace("example.org/my-project", f"example.org/{args.name}")
    content = content.replace("YOUR PROJECT NAME", args.name)
    content = content.replace(
        '"../../spec/context/v0.5.jsonld"',
        '"https://raw.githubusercontent.com/cloudronin/uofa/main/spec/context/v0.5.jsonld"'
    )
    content = content.replace(
        '"../../../spec/context/v0.5.jsonld"',
        '"https://raw.githubusercontent.com/cloudronin/uofa/main/spec/context/v0.5.jsonld"'
    )

    output_file = project_dir / f"{args.name}-cou1.jsonld"
    with open(output_file, "w") as f:
        f.write(content)

    result_line(f"Template ({args.profile})", True, str(output_file))

    # ── Generate keypair ──────────────────────────────────────
    key_path = keys_dir / f"{args.name}.key"
    key_path, pub_path = generate_keypair(key_path)
    result_line("Keypair generated", True, str(key_path.name))

    # ── Copy Excel template from pack ─────────────────────────
    active_pack = paths.get_active_pack()
    pack_name = active_pack[0] if active_pack else "vv40"
    xlsx_template = _find_pack_template(pack_name)

    if pack_name == "vv40" or pack_name == "core":
        xlsx_dest_name = "uofa-template.xlsx"
    else:
        xlsx_dest_name = f"uofa-template-{pack_name}.xlsx"

    if xlsx_template and xlsx_template.exists():
        xlsx_dest = project_dir / xlsx_dest_name
        shutil.copy2(xlsx_template, xlsx_dest)
        result_line("Excel template", True, xlsx_dest_name)
    else:
        xlsx_dest_name = "uofa-template.xlsx"
        info("  (no Excel template found for this pack)")

    # ── Write uofa.toml ──────────────────────────────────────
    toml_content = _generate_toml(
        name=args.name,
        pack=pack_name,
        profile=args.profile,
        template=xlsx_dest_name,
        provider=args.provider,
        model=args.model,
    )
    toml_path = project_dir / "uofa.toml"
    toml_path.write_text(toml_content)
    result_line("uofa.toml", True)

    # ── Write README.md ───────────────────────────────────────
    readme_content = _generate_readme(
        project_name=args.name,
        pack_name=pack_name,
        template_filename=xlsx_dest_name,
    )
    (project_dir / "README.md").write_text(readme_content)
    result_line("README.md", True)

    # ── Create .gitignore ─────────────────────────────────────
    gitignore = project_dir / ".gitignore"
    gitignore.write_text(
        "# Private keys — never commit\n"
        "*.key\n"
    )
    result_line(".gitignore", True)

    # ── Next steps ────────────────────────────────────────────
    print()
    info("Next steps:")
    info(f"  1. Fill in {xlsx_dest_name}")
    info(f"  2. Import: cd {args.name} && uofa import")
    info(f"  3. Check:  uofa check {args.name}-cou1.jsonld")

    return 0


def _find_pack_template(pack_name: str) -> Path | None:
    """Find the Excel template for a given pack."""
    try:
        manifest = paths.pack_manifest(pack_name)
        template_rel = manifest.get("template")
        if template_rel:
            template_path = paths.pack_dir(pack_name) / template_rel
            if template_path.exists():
                return template_path
    except (FileNotFoundError, KeyError):
        pass
    # Fallback: core pack template
    try:
        manifest = paths.pack_manifest("core")
        template_rel = manifest.get("template")
        if template_rel:
            template_path = paths.pack_dir("core") / template_rel
            if template_path.exists():
                return template_path
    except (FileNotFoundError, KeyError):
        pass
    return None


def _generate_toml(name, pack, profile, template, provider, model):
    """Generate uofa.toml content."""
    return (
        "# UofA Project Configuration\n"
        f"# Generated by: uofa init {name}\n"
        "\n"
        "[project]\n"
        f'name = "{name}"\n'
        f'pack = "{pack}"\n'
        f'profile = "{profile}"\n'
        "\n"
        "[paths]\n"
        'output = "."\n'
        'evidence = "evidence"\n'
        f'template = "{template}"\n'
        "\n"
        "[extract]\n"
        f'provider = "{provider}"\n'
        f'model = "{model}"\n'
    )


_PACK_DISPLAY = {
    "vv40": "ASME V&V 40-2018",
    "nasa-7009b": "NASA-STD-7009B",
    "core": "Core (standards-agnostic)",
}


def _generate_readme(project_name, pack_name, template_filename):
    """Generate project README.md content."""
    pack_display = _PACK_DISPLAY.get(pack_name, pack_name)
    return (
        f"# {project_name} — UofA Project\n"
        "\n"
        "## Quick Start\n"
        "\n"
        "1. **Fill in the Excel template:**\n"
        f"   Open `{template_filename}` and fill in your assessment data.\n"
        "\n"
        "2. **Import to JSON-LD:**\n"
        "   ```bash\n"
        f"   uofa import {template_filename}\n"
        "   ```\n"
        "   (Pack and signing key are read from `uofa.toml` — no flags needed.)\n"
        "\n"
        "3. **Check your evidence package:**\n"
        "   ```bash\n"
        f"   uofa check {project_name}-cou1.jsonld\n"
        "   ```\n"
        "\n"
        "4. **Fix any weakeners**, re-import, and check again until clean.\n"
        "\n"
        "## Project Structure\n"
        "\n"
        "- `uofa.toml` — Project configuration (pack, profile, paths)\n"
        "- `evidence/` — Place your evidence files here\n"
        f"- `{template_filename}` — Excel template for your credibility assessment\n"
        "- `keys/` — Signing keys (keep `*.key` private, share `*.pub`)\n"
        "\n"
        "## Commands\n"
        "\n"
        "All commands auto-detect project settings from `uofa.toml`:\n"
        "\n"
        "```bash\n"
        f"uofa import {template_filename}          # Excel -> signed JSON-LD\n"
        f"uofa check {project_name}-cou1.jsonld    # Full C1+C2+C3 pipeline\n"
        f"uofa rules {project_name}-cou1.jsonld    # Weakener detection only\n"
        "uofa diff cou1.jsonld cou2.jsonld         # Compare two COUs\n"
        "```\n"
        "\n"
        f"## Pack: {pack_display}\n"
        "\n"
        f"This project uses the **{pack_display}** standards pack.\n"
    )

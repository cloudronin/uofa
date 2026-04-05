"""uofa import — import an Excel workbook into a UofA JSON-LD file."""

import json
from pathlib import Path

from uofa_cli.output import step_header, result_line, info, error, warn
from uofa_cli import paths

HELP = "import an Excel workbook into a UofA JSON-LD file"


def add_arguments(parser):
    parser.add_argument("file", nargs="?", type=Path,
                        help="Excel workbook (.xlsx). If omitted, reads template from uofa.toml")
    parser.add_argument("--output", "-o", type=Path,
                        help="output path (default: same directory, .jsonld extension)")
    parser.add_argument("--sign", action="store_true",
                        help="sign the output after generation")
    parser.add_argument("--key", "-k", type=Path,
                        help="path to ed25519 private key (required with --sign, or auto-detected from project)")
    parser.add_argument("--check", action="store_true",
                        help="run all quality gates on the output")
    parser.add_argument("--profile", choices=["minimal", "complete"],
                        help="override profile auto-detection")


def run(args) -> int:
    from uofa_cli.excel_reader import read_workbook, ImportError as ExcelImportError
    from uofa_cli.excel_mapper import map_to_jsonld

    # ── Project-aware defaults ───────────────────────────────
    project_root = paths.find_project_root()
    config = paths.load_project_config(project_root) if project_root else {}

    # Resolve input file: CLI > uofa.toml template > error
    xlsx = args.file
    if not xlsx and config.get("template"):
        template = config["template"]
        if template.exists():
            xlsx = template
    if not xlsx:
        error("No Excel file specified and no template found in uofa.toml")
        return 1

    if not xlsx.exists():
        error(f"File not found: {xlsx}")
        return 1

    if not xlsx.suffix.lower() == ".xlsx":
        error(f"Expected .xlsx file, got: {xlsx.suffix}")
        return 1

    # Resolve pack: CLI dispatcher already sets active pack from --pack flag.
    # If no --pack was given and we're in a project, override with toml pack.
    packs = paths.get_active_pack()
    if not getattr(args, "pack", None) and config.get("pack"):
        packs = [config["pack"]]
        paths.set_active_pack(packs)

    step_header(f"Importing {xlsx.name}")

    # ── Read and validate ────────────────────────────────────
    try:
        data = read_workbook(xlsx, packs)
    except ExcelImportError as exc:
        for e in exc.errors:
            error(e)
        return 1

    # Override profile if requested
    if args.profile:
        data["summary"]["profile"] = args.profile.capitalize()

    # ── Map to JSON-LD ───────────────────────────────────────
    doc = map_to_jsonld(data, packs, xlsx.resolve())

    # ── Write output ─────────────────────────────────────────
    output = args.output
    if not output and config.get("output"):
        output = config["output"] / f"{xlsx.stem}.jsonld"
    if not output:
        output = xlsx.with_suffix(".jsonld")

    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w") as f:
        json.dump(doc, f, indent=2, sort_keys=True, ensure_ascii=False)
        f.write("\n")

    # Summary counts
    n_req = sum(1 for e in data["entities"] if e["entity_type"] == "Requirement")
    n_model = sum(1 for e in data["entities"] if e["entity_type"] == "Model")
    n_data = sum(1 for e in data["entities"] if e["entity_type"] == "Dataset")
    n_vr = len(data["validation_results"])
    n_factors = len([f for f in data["factors"] if f["status"] == "assessed"])

    result_line("Imported", True, str(output))
    info(f"  {n_req} requirement(s), {n_model} model(s), {n_data} dataset(s)")
    info(f"  {n_vr} validation result(s), {n_factors} credibility factor(s)")
    info(f"  Profile: {data['summary']['profile']}, Pack: {', '.join(packs)}")

    # ── Optional: Sign ───────────────────────────────────────
    if args.sign:
        key = args.key
        # Auto-detect key from project if not specified
        if not key and project_root:
            key_candidates = list((project_root / "keys").glob("*.key"))
            if key_candidates:
                key = key_candidates[0]
        if not key:
            error("--sign requires --key <path> (or run inside a project with keys/)")
            return 1
        if not key.exists():
            error(f"Key file not found: {key}")
            return 1

        from uofa_cli.integrity import sign_file
        ctx = paths.context_file()
        sha256_hex, sig_hex = sign_file(output, key, ctx)
        result_line("Signed", True)
        info(f"  SHA-256: {sha256_hex[:16]}...")

    # ── Optional: Check ──────────────────────────────────────
    if args.check:
        from uofa_cli.commands import check
        import argparse
        check_args = argparse.Namespace(
            file=output,
            key=None,
            context=None,
            rules=None,
            skip_rules=False,
            no_color=getattr(args, "no_color", False),
            verbose=getattr(args, "verbose", False),
            repo_root=getattr(args, "repo_root", None),
            pack=packs,
            raw=False,
        )
        print()
        rc = check.run(check_args)
        if rc != 0:
            return rc

    return 0

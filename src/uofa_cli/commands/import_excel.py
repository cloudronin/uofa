"""uofa import — import an Excel workbook into a UofA JSON-LD file."""

from __future__ import annotations

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
    parser.add_argument("--sip-pubkey", type=Path,
                        help="SIP measurement public key for verifying a SIP-bundle input (default: keys/research.pub)")
    parser.add_argument("--decision-pubkey", type=Path,
                        help="engineer public key for verifying a SIP-bundle engineerDecision on import")


def run(args) -> int:
    # ── Project-aware defaults ───────────────────────────────
    project_root = paths.find_project_root()
    config = paths.load_project_config(project_root) if project_root else {}

    # ── v2 native SIP-bundle path (SIP §7.3 v2) ──────────────
    # A SIP evidence bundle (.json) maps directly to surrogate-pack JSON-LD via
    # the native reader, skipping the xlsx/LLM on-ramp for measured fields.
    if args.file and args.file.suffix.lower() == ".json" and _looks_like_sip_bundle(args.file):
        return _run_sip_import(args, args.file, project_root, config)

    from uofa_cli.excel_reader import read_workbook, ImportError as ExcelImportError
    from uofa_cli.excel_mapper import map_to_jsonld

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
    packs = paths.resolve_active_packs(args)
    if not getattr(args, "pack", None) and config.get("pack"):
        packs = [config["pack"]]
        args.active_packs = packs

    step_header(f"Importing {xlsx.name}")

    # ── Read and validate ────────────────────────────────────
    try:
        data = read_workbook(xlsx, packs)
    except ExcelImportError as exc:
        for e in exc.errors:
            error(e)
        return 1

    # Surface non-fatal normalizations from the reader (e.g. LLM-produced
    # evidence_type labels that were mapped onto the canonical enum).
    for w in data.pop("_warnings", []):
        warn(w)

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

    return _sign_and_check(args, output, packs, project_root)


def _looks_like_sip_bundle(path: Path) -> bool:
    try:
        doc = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    return isinstance(doc, dict) and str(doc.get("schemaVersion", "")).startswith("sip-evidence-bundle")


def _run_sip_import(args, bundle_path: Path, project_root, config) -> int:
    """v2 native SIP-bundle import: verify signatures, map to surrogate-pack JSON-LD."""
    from uofa_cli.readers.sip_bundle_reader import read_sip_bundle

    packs = ["surrogate"]
    args.active_packs = packs
    step_header(f"Importing SIP bundle {bundle_path.name}")

    measurement_pubkey = getattr(args, "sip_pubkey", None) or paths.default_pubkey()
    decision_pubkey = getattr(args, "decision_pubkey", None)
    try:
        doc = read_sip_bundle(bundle_path, measurement_pubkey=measurement_pubkey,
                              decision_pubkey=decision_pubkey)
    except (ValueError, FileNotFoundError) as exc:
        error(str(exc))
        return 1

    output = args.output
    if not output and config.get("output"):
        output = config["output"] / f"{bundle_path.stem}.jsonld"
    if not output:
        output = bundle_path.with_suffix(".jsonld")
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w") as f:
        json.dump(doc, f, indent=2, sort_keys=True, ensure_ascii=False)
        f.write("\n")

    result_line("Imported SIP bundle", True, str(output))
    info("  measurement signature verified")
    if "decision" in doc:
        info(f"  engineer decision: {doc['decision']} (signature verified)")
    else:
        info("  engineer decision: none verified → no inferred acceptance")
    return _sign_and_check(args, output, packs, project_root)


def _sign_and_check(args, output: Path, packs, project_root) -> int:
    # Implicitly sign when --key is provided alongside --check: the only reason
    # to pass --key to import + verify is to verify against that key, which
    # requires signing first.
    should_sign = args.sign or bool(args.check and args.key)
    signing_key: Path | None = None
    if should_sign:
        key = args.key
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
        signing_key = key

        from uofa_cli.integrity import sign_file
        ctx = paths.context_file()
        sha256_hex, sig_hex = sign_file(output, key, ctx)
        result_line("Signed", True)
        info(f"  SHA-256: {sha256_hex[:16]}...")

    if args.check:
        from uofa_cli.commands import check
        import argparse

        pubkey_for_check: Path | None = None
        if signing_key is not None:
            candidate = signing_key.with_suffix(".pub")
            if candidate.exists():
                pubkey_for_check = candidate

        check_args = argparse.Namespace(
            file=output,
            pubkey=pubkey_for_check,
            key=None,
            context=None,
            rules=None,
            skip_rules=False,
            build=False,
            no_color=getattr(args, "no_color", False),
            verbose=getattr(args, "verbose", False),
            repo_root=getattr(args, "repo_root", None),
            pack=packs,
            # Thread the active set explicitly (P2d-3): check.run_structured
            # resolves packs via paths.resolve_active_packs(args), which reads
            # args.active_packs — not args.pack — so the surrogate bundle is
            # validated against surrogate shapes, not the vv40 default.
            active_packs=packs,
            raw=False,
        )
        print()
        rc = check.run(check_args)
        if rc != 0:
            return rc

    return 0

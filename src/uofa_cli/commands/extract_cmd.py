"""uofa extract — extract assessment data from evidence documents into an Excel template."""

from __future__ import annotations

from pathlib import Path

from uofa_cli.output import step_header, result_line, info, error, warn
from uofa_cli import paths

HELP = "extract assessment data from evidence documents into an Excel template"


def add_arguments(parser):
    parser.add_argument("source", nargs="*", type=Path,
                        help="file or folder path(s) containing evidence documents")
    parser.add_argument("--model", default=None,
                        help="litellm model string (default: qwen3:4b or uofa.toml)")
    parser.add_argument("--output", "-o", type=Path,
                        help="output Excel path (default: {source}-extracted.xlsx)")
    parser.add_argument("--glob", default=None,
                        help="file filter pattern (e.g. '*.pdf' or '*.pdf,*.docx')")
    parser.add_argument("--thinking", action="store_true", default=False,
                        help="enable thinking/reasoning mode (slower, may improve accuracy)")
    parser.add_argument("--prompt-version", default=None,
                        help="tag for scoring log tracking (e.g. 'v2-detailed')")


def run(args) -> int:
    from uofa_cli.document_reader import discover_files, read_corpus
    from uofa_cli.llm_extractor import extract
    from uofa_cli.excel_writer import write_extraction

    # ── Project-aware defaults ───────────────────────────────
    project_root = paths.find_project_root()
    config = paths.load_project_config(project_root) if project_root else {}

    # Resolve pack: CLI dispatcher already sets active pack from --pack flag.
    # If no --pack was given and we're in a project, override with toml pack.
    packs = paths.get_active_pack()
    if not getattr(args, "pack", None) and config.get("pack"):
        packs = [config["pack"]]
        paths.set_active_pack(packs)
    pack_name = packs[0]

    # Resolve model: CLI > uofa.toml > default
    model = args.model
    if not model:
        model = config.get("model", "qwen3:4b")

    # Resolve sources: CLI > uofa.toml evidence dir > error
    sources = args.source
    if not sources and config.get("evidence"):
        evidence_dir = config["evidence"]
        if evidence_dir.is_dir():
            sources = [evidence_dir]
    if not sources:
        error("No source files or directories specified.")
        info("  Usage: uofa extract <file-or-folder> [...]")
        info("  Or run inside a project with uofa.toml (evidence dir)")
        return 1

    # ── Step 1: Discover files ───────────────────────────────
    step_header(f"Discovering files...")

    file_paths, discover_warnings = discover_files(sources, glob_pattern=args.glob)
    for w in discover_warnings:
        warn(w)

    if not file_paths:
        error("No supported files found.")
        if args.glob:
            info(f"  Glob filter: {args.glob}")
        info("  Supported: .pdf, .docx, .xlsx, .csv, .tsv, .txt, .log")
        return 1

    info(f"  Found {len(file_paths)} file(s):")
    for i, fp in enumerate(file_paths, 1):
        suffix = fp.suffix.lower().lstrip(".")
        info(f"    {i:>3}. {fp.name}  ({suffix.upper()})")

    # ── Step 2: Read corpus ──────────────────────────────────
    step_header("Reading files...")

    corpus = read_corpus(file_paths)
    for w in corpus.warnings:
        warn(w)

    if getattr(args, "verbose", False):
        for entry in corpus.file_manifest:
            info(f"  ✓ {entry['name']:<45} {entry['tokens']:>6} tokens")

    info(f"  Total corpus: {corpus.total_tokens:,} tokens")

    if not corpus.chunks:
        error("No text could be extracted from the source files.")
        return 1

    # ── Step 3: LLM extraction ───────────────────────────────
    step_header(f"Extracting with {model}...")

    pack_prompt_path = paths.extract_prompt()

    try:
        result = extract(
            corpus, model, pack_name, pack_prompt_path,
            thinking=getattr(args, "thinking", False),
        )
    except Exception as exc:
        error(f"Extraction failed: {exc}")
        if getattr(args, "verbose", False):
            raise
        return 1

    # Extraction summary
    n_summary = sum(1 for fe in result.assessment_summary.values() if fe.value is not None)
    n_entities = len(result.model_and_data)
    n_vr = len(result.validation_results)
    n_factors = len(result.credibility_factors)
    n_decision = sum(1 for fe in result.decision.values() if fe.value is not None)

    result_line("Assessment Summary", True, f"{n_summary} fields")
    result_line("Model & Data", True, f"{n_entities} entities")
    result_line("Validation Results", True, f"{n_vr} results")
    result_line("Credibility Factors", True, f"{n_factors} factors mapped")
    result_line("Decision", True, f"{n_decision} fields")

    # Confidence distribution
    all_confidences = []
    for fe in result.assessment_summary.values():
        if fe.value is not None:
            all_confidences.append(fe.confidence)
    for factor in result.credibility_factors:
        for fe in factor.values():
            if fe.value is not None:
                all_confidences.append(fe.confidence)
    for fe in result.decision.values():
        if fe.value is not None:
            all_confidences.append(fe.confidence)

    if all_confidences:
        high = sum(1 for c in all_confidences if c >= 0.85)
        medium = sum(1 for c in all_confidences if 0.50 <= c < 0.85)
        low = sum(1 for c in all_confidences if c < 0.50)
        if low > 0:
            warn(f"  {low} cell(s) low confidence (red)")

    # ── Step 4: Write Excel ──────────────────────────────────
    step_header("Writing Excel output...")

    # Resolve template
    template = _find_pack_template(pack_name)

    # Resolve output path
    output = args.output
    if not output:
        if config.get("output") and config["output"].is_dir():
            source_name = sources[0].stem if sources else "extract"
            output = config["output"] / f"{source_name}-extracted.xlsx"
        else:
            source_name = sources[0].stem if sources else "extract"
            output = Path(f"{source_name}-extracted.xlsx")

    output.parent.mkdir(parents=True, exist_ok=True)
    write_extraction(result, template, output, pack_name)

    # Count filled cells and confidence levels
    n_filled = len(all_confidences)
    result_line("Output", True, str(output))
    info(f"  {n_filled} cells pre-filled")
    if all_confidences:
        info(f"  {high} high confidence (green), {medium} review suggested (yellow)")

    print()
    info("Done. Review the spreadsheet, then run:")
    info(f"  uofa import {output} --sign --key <your-key> --check")

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

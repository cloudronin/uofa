"""uofa import — import an Excel workbook into a UofA JSON-LD file."""

from __future__ import annotations

import json
from pathlib import Path

from uofa_cli.furnishers import pins
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
    parser.add_argument("--protocol-check", action="store_true", default=False,
                        help="gate the import on the reference-encoding conformance "
                             "checks. Runs the workbook-side checks against the input "
                             "and the package-side checks against the artifacts beside "
                             "the output. Any failure exits non-zero.")
    parser.add_argument("--profile", choices=["minimal", "complete"],
                        help="override profile auto-detection")
    parser.add_argument("--base-uri",
                        help="namespace to mint identifiers under, e.g. https://acme.example/uofa. "
                             "Overrides [project] base_uri in uofa.toml. Defaults to a reserved "
                             "example.org placeholder; uofa.net is refused.")
    parser.add_argument("--evidence", type=Path,
                        help="evidence sidecar from `uofa evidence seal`; its "
                             "manifest, source pins and corroboration are folded "
                             "in BEFORE hashing, so the seal sits inside the "
                             "signature scope")
    parser.add_argument("--sip-pubkey", type=Path,
                        help="SIP measurement public key for verifying a SIP-bundle input (default: keys/research.pub)")
    parser.add_argument("--decision-pubkey", type=Path,
                        help="engineer public key for verifying a SIP-bundle hasDecisionRecord on import")


def _print_provenance_counts(output: Path) -> None:
    """Per-class field counts. See R5 in docs/valid-package-spec.md."""
    import collections
    import json

    try:
        blob = json.loads(output.read_text())
    except (OSError, ValueError):
        return
    node = blob if "fieldProvenance" in blob else next(
        (n for n in (blob.get("@graph") or []) if isinstance(n, dict)
         and "fieldProvenance" in n), None)
    if not node:
        return
    entries = node.get("fieldProvenance") or []
    counts = collections.Counter(e.split("=")[-1] for e in entries
                                 if isinstance(e, str) and "=" in e)
    if not counts:
        return
    parts = ", ".join(f"{n} {cls}" for cls, n in sorted(counts.items()))
    info(f"  field provenance: {parts}")
    if not counts.get("extracted"):
        info("  NOTHING in this package was read from the document — every "
             "field came from the run, a default, or a synthesis.")


def run(args) -> int:
    # ── Project-aware defaults ───────────────────────────────
    project_root = paths.find_project_root()
    config = paths.load_project_config(project_root) if project_root else {}

    # Validate the minting namespace before doing any work. Reading and
    # extracting a workbook is slow, and a rejected --base-uri should not cost
    # the user that wait before telling them the flag is wrong.
    from uofa_cli.excel_mapper import resolve_base_uri
    try:
        resolve_base_uri(getattr(args, "base_uri", None) or config.get("base_uri"))
    except ValueError as exc:
        error(str(exc))
        return 1

    # ── v2 native SIP-bundle path (SIP §7.3 v2) ──────────────
    # A SIP evidence bundle (.json) maps directly to surrogate-pack JSON-LD via
    # the native reader, skipping the xlsx/LLM on-ramp for measured fields.
    if args.file and args.file.suffix.lower() == ".json" and _looks_like_sip_bundle(args.file):
        return _run_sip_import(args, args.file, project_root, config)

    from uofa_cli.excel_reader import read_workbook, ImportError as ExcelImportError
    from uofa_cli.excel_mapper import map_to_jsonld
    from uofa_cli.excel_constants import DEFAULT_BASE_URI

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
    # Precedence: --base-uri > uofa.toml [project] base_uri > placeholder default.
    # The id lands inside the canonicalised content that the hash and signature
    # cover, so getting this wrong is unfixable once the package is signed.
    base_uri = args.base_uri or config.get("base_uri")
    doc = map_to_jsonld(data, packs, xlsx.resolve(), base_uri=base_uri)

    if getattr(args, "evidence", None):
        folded = _fold_evidence(doc, args.evidence)
        info(f"  Evidence sidecar folded in: {', '.join(folded)}")

    if not base_uri:
        warn(
            f"Identifiers minted under {DEFAULT_BASE_URI}, a placeholder domain. "
            f"Set [project] base_uri in uofa.toml, or pass --base-uri, to use a "
            f"namespace you control. The id is covered by the signature, so this "
            f"cannot be changed after signing."
        )

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


# What the sidecar contributes to the package. Undeclared terms on purpose:
# `@vocab` in the v0.5 context expands each to `uofa:<term>`, and that context
# is inlined into the hash preimage, so declaring them would invalidate every
# signed package in the repo (furnishers/pins.py:19-25).
_EVIDENCE_FIELDS = ("artifactManifest", "solverFact", "solverCaution",
                    "absentArtifact", "corroboration")


def _fold_evidence(doc: dict, sidecar: Path) -> list[str]:
    """Merge an evidence sidecar into the package before it is hashed.

    Order matters and is the whole point: this runs before `integrity.sign_file`,
    so the artifact digests and source pins are covered by the signature rather
    than shipped alongside it. A manifest beside a signed package proves
    nothing about the package.
    """
    if not sidecar.exists():
        raise FileNotFoundError(f"Evidence sidecar not found: {sidecar}")
    payload = json.loads(sidecar.read_text(encoding="utf-8"))
    schema = str(payload.get("schemaVersion", ""))
    if not schema.startswith("uofa-evidence-seal/"):
        raise ValueError(
            f"{sidecar} is not an evidence sidecar (schemaVersion {schema!r}); "
            f"generate one with `uofa evidence seal <folder>`")

    added = []
    for field in _EVIDENCE_FIELDS:
        value = payload.get(field)
        if value:
            doc[field] = value
            added.append(f"{len(value)} {field}")

    # Source pins go through pins.attach so the de-duplication rule stays in
    # one place rather than being re-implemented here.
    for pin in payload.get("sourcePin") or []:
        pins.attach(doc, pin)
    if payload.get("sourcePin"):
        added.append(f"{len(payload['sourcePin'])} sourcePin")
    return added or ["nothing (the sidecar was empty)"]


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

    measurement_pubkey = getattr(args, "sip_pubkey", None)
    if measurement_pubkey is None:
        _anchors = paths.shipped_anchors()
        measurement_pubkey = _anchors[0][0] if _anchors else None
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


def _run_protocol_check(args, output: Path) -> bool:
    """Reference-encoding conformance gate. True when nothing failed.

    Workbook-side checks are skipped for a non-xlsx input, because the SIP-bundle
    path never produces a workbook to check.
    """
    from uofa_cli import protocol_check
    from uofa_cli import paths as _paths

    results = []
    source = getattr(args, "file", None)
    if source is not None and Path(source).suffix.lower() == ".xlsx":
        try:
            template = _paths.template_path()
        except Exception:
            template = None
        results += protocol_check.check_workbook(Path(source), template)
    results += protocol_check.check_package(output)
    print()
    return protocol_check.render(results, output.name)


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
        # None: the package just written names its own context, and that is
        # what it must be hashed against.
        sha256_hex, sig_hex = sign_file(output, key, None)
        result_line("Signed", True)
        info(f"  SHA-256: {sha256_hex[:16]}...")

    # R5. Always, not under a verbose flag. A conforming package says nothing
    # today about how much of it was READ, and three separate failures on
    # 2026-08-08 looked exactly like a clean pass: one validated on an assessor
    # the model invented, one on the template's help text, one via a warned
    # auto-synthesis. This is the line that tells them apart.
    _print_provenance_counts(output)

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

    if getattr(args, "protocol_check", False) and not _run_protocol_check(args, output):
        return 1

    return 0

"""uofa evidence — inventory and seal a simulation evidence folder.

Runs before any extractor, and needs no language model, no network and no
vendor software. `inventory` says what is in the folder; `seal` records a
digest for every file and archive member and writes the sidecar that
`uofa import --evidence` folds into the package before it is signed.

The point of splitting these from `extract` is that integrity, provenance and
completeness are establishable without reading a single credibility factor.
Pointing this at three proprietary Workbench archives and getting a complete,
digest-backed account of them is the claim; the extraction is a separate one.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from uofa_cli import corroborate, paths
from uofa_cli.corroborate import Corroboration
from uofa_cli.output import (error, info, result_line, step_header, table_header,
                             table_row, table_separator, warn)
from uofa_cli.solver import detect, seal as sealmod
from uofa_cli.solver.facts import SolverEvidence
from uofa_cli.solver.reader import read_evidence

HELP = "inventory and seal a simulation evidence folder (no model, no network)"

_COLS = ["kind", "size", "read", "path"]
_WIDTHS = [22, 13, 6, 60]


def _add_common(sub_parser):
    """The flag block both subcommands share.

    Registered per subparser rather than on the parent: a parent-level
    positional competes with the subparser action for the first argument, and
    argparse resolves that by handing the path to the subcommand chooser (see
    the same care taken in commands/interrogate.py:36-37).
    """
    sub_parser.add_argument("source", type=Path,
                            help="evidence folder or single artifact")
    sub_parser.add_argument("--source-map", type=Path,
                            help="name→URL map (JSON object, or 'name<space>url' "
                                 "per line) used to attach re-derivable source pins")
    sub_parser.add_argument("--fetched-at",
                            help="RFC3339 time the content was fetched, for pins "
                                 "(default: now)")
    sub_parser.add_argument("--claims", type=Path,
                            help="JSON claim set to corroborate against the "
                                 "solver artifacts (quantities asserted in "
                                 "prose, e.g. a paper's model-parameter table)")


def add_arguments(parser):
    sub = parser.add_subparsers(dest="evidence_command")

    inv = sub.add_parser("inventory", help="list what is in the folder, with digests")
    _add_common(inv)
    inv.add_argument("--members", action="store_true",
                     help="list archive members, not just top-level files")

    seal_p = sub.add_parser("seal", help="write the evidence sidecar JSON")
    _add_common(seal_p)
    seal_p.add_argument("--output", "-o", type=Path,
                        help="sidecar path (default: <source>-evidence.json)")
    seal_p.add_argument("--members", action="store_true",
                        help="list archive members in the readout")

    parser.epilog = (
        "Examples:\n"
        "  uofa evidence inventory osf-n4pjz/\n"
        "  uofa evidence inventory osf-n4pjz/ --members       # every archive member\n"
        "  uofa evidence seal osf-n4pjz/ -o evidence.json\n"
        "  uofa evidence seal osf-n4pjz/ --source-map osf-urls.txt -o evidence.json\n"
        "  uofa import extracted.xlsx --evidence evidence.json --sign --key k.key\n"
    )


@dataclass(frozen=True)
class EvidenceResult:
    """Typed result for callers that must not go through the I/O shell."""
    seal: sealmod.EvidenceSeal
    sidecar: Path | None = None
    evidence: SolverEvidence | None = None
    corroboration: Corroboration | None = None

    @property
    def exit_code(self) -> int:
        # An unreadable artifact is a reported state, not a failure: the whole
        # point is that a sealed-but-unread `.mechdb` is a legitimate outcome.
        # Only a folder we could not read at all is an error.
        return 0 if self.seal.artifacts else 1


def run_structured(args) -> EvidenceResult:
    """Do the work, emit nothing. See tests/test_command_structured.py."""
    source = _source_of(args)
    source_map = (sealmod.load_source_map(args.source_map)
                  if getattr(args, "source_map", None) else None)
    seal = sealmod.seal_folder(
        source, source_map=source_map,
        fetched_at=getattr(args, "fetched_at", "") or "")

    solver_evidence = read_evidence(source)
    corroboration = None
    if getattr(args, "claims", None):
        identity = paths.detection_config(
            paths.pack_manifest(paths.resolve_active_packs(args)[0])
        ).get("quantityIdentity")
        corroboration = corroborate.corroborate(
            corroborate.load_claims(args.claims), solver_evidence, identity)

    sidecar = None
    if getattr(args, "evidence_command", None) == "seal":
        sidecar = args.output or source.parent / f"{source.name}-evidence.json"
        sealmod.write_sidecar(seal, sidecar, evidence=solver_evidence,
                              corroboration=corroboration)
    return EvidenceResult(seal=seal, sidecar=sidecar, evidence=solver_evidence,
                          corroboration=corroboration)


def run(args) -> int:
    if not getattr(args, "evidence_command", None):
        error("No subcommand given.")
        info("  Usage: uofa evidence inventory <folder-or-file> [--members]")
        info("         uofa evidence seal <folder-or-file> -o evidence.json")
        return 2
    source = _source_of(args)
    if not source.exists():
        raise FileNotFoundError(f"Not found: {source}")

    verb = "Sealing" if args.evidence_command == "seal" else "Inventorying"
    step_header(f"{verb} {source.name}...")
    result = run_structured(args)
    seal = result.seal

    for w in seal.warnings:
        warn(w)

    _render(seal, members=getattr(args, "members", False))

    for line in sealmod.summarise(seal):
        info(f"  {line}")

    if result.evidence is not None:
        step_header("What the solver artifacts say")
        for line in result.evidence.summarise():
            info(f"  {line}")

    if result.corroboration is not None:
        step_header("Prose claims against the artifacts")
        for line in result.corroboration.summarise():
            info(f"  {line}")
        info("  (Divergences are reported for a human to adjudicate. A "
             "materials library may hold unused, superseded or duplicate "
             "entries; the artifact does not say which one a published run "
             "used.)")

    if result.sidecar:
        result_line("Sidecar written", True, str(result.sidecar))
        info(f"  Next: uofa import <workbook>.xlsx --evidence {result.sidecar}")

    return result.exit_code


def _render(seal: sealmod.EvidenceSeal, *, members: bool) -> None:
    table_header(_COLS, _WIDTHS)
    for art in seal.artifacts:
        table_row([art.kind, f"{art.size:,}", "yes" if art.read else "no",
                   art.path], _WIDTHS)
        if not members:
            continue
        for m in art.members:
            table_row([f"  {m.kind}", f"{m.size:,}",
                       "yes" if m.read else "no", f"  {m.path}"], _WIDTHS)
    table_separator(_WIDTHS)

    # Unread kinds, once each with the reason -- the honest-blank readout.
    unread: dict[str, int] = {}
    for art in seal.artifacts:
        if not art.read:
            unread[art.kind] = unread.get(art.kind, 0) + 1
        for m in art.members:
            if not m.read:
                unread[m.kind] = unread.get(m.kind, 0) + 1
    for kind, n in sorted(unread.items()):
        info(f"  {n:>3} × {kind}: {detect.unreadable_reason(kind)}")

    empty = [d for a in seal.artifacts for d in a.empty_dirs]
    if empty:
        info(f"  {len(empty)} empty director(ies):")
        for d in empty[:12]:
            info(f"      {d}")
        if len(empty) > 12:
            info(f"      … and {len(empty) - 12} more")


def _source_of(args) -> Path | None:
    return getattr(args, "source", None)

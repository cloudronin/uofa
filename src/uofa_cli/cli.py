"""UofA CLI entry point — argparse dispatcher for all subcommands."""

from __future__ import annotations

import argparse
import sys

from uofa_cli import __version__
from uofa_cli.output import set_color, error
from uofa_cli.paths import find_repo_root, set_active_pack


def main():
    sys.exit(_run() or 0)


def _run():
    # Shared flags inherited by all subcommands
    parent = argparse.ArgumentParser(add_help=False)
    parent.add_argument("--no-color", action="store_true", help="disable colored output")
    parent.add_argument("--verbose", action="store_true", help="show full tracebacks on error")
    parent.add_argument("--repo-root", metavar="PATH", help="override repo root auto-detection")
    parent.add_argument("--pack", metavar="NAME", action="append",
                        help="pack(s) to use for shapes, rules, and templates (default: vv40). "
                             "May be repeated: --pack vv40 --pack nasa-7009b")

    parser = argparse.ArgumentParser(
        prog="uofa",
        description="Create, validate, and sign Unit of Assurance evidence packages.",
        parents=[parent],
    )
    parser.add_argument("--version", action="version", version=f"uofa {__version__}")

    sub = parser.add_subparsers(dest="command", title="commands")

    # ── Register subcommands ──────────────────────────────────
    from uofa_cli.commands import keygen, sign, verify, shacl, rules, check, validate, init, diff, schema, packs, migrate, import_excel, extract_cmd, adversarial

    modules = {
        "keygen":      keygen,
        "sign":        sign,
        "verify":      verify,
        "shacl":       shacl,
        "rules":       rules,
        "check":       check,
        "validate":    validate,
        "init":        init,
        "diff":        diff,
        "schema":      schema,
        "packs":       packs,
        "migrate":     migrate,
        "import":      import_excel,
        "extract":     extract_cmd,
        "adversarial": adversarial,
    }

    for name, mod in modules.items():
        sp = sub.add_parser(name, help=mod.HELP, parents=[parent])
        mod.add_arguments(sp)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    if args.no_color:
        set_color(False)

    # Set active pack(s) before resolving repo root
    set_active_pack(args.pack or ["vv40"])

    # Resolve repo root early so commands can use paths.*
    try:
        find_repo_root(args.repo_root)
    except FileNotFoundError as exc:
        error(str(exc))
        return 1

    # Dispatch
    mod = modules[args.command]
    try:
        return mod.run(args)
    except FileNotFoundError as exc:
        error(str(exc))
        if args.verbose:
            raise
        return 1
    except Exception as exc:
        error(str(exc))
        if args.verbose:
            raise
        return 1


if __name__ == "__main__":
    main()

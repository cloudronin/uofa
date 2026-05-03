"""UofA CLI entry point — argparse dispatcher for all subcommands."""

from __future__ import annotations

import argparse
import sys

from uofa_cli import __version__
from uofa_cli.output import set_color, error
from uofa_cli.paths import find_repo_root, set_active_pack


def _force_utf8_streams() -> None:
    """Reconfigure stdout/stderr to UTF-8 with replacement.

    The CLI emits Unicode characters (`══`, `✓`, `✗`, status emoji) in
    its progress output. Windows consoles default to cp1252
    ("charmap"), which can't encode those bytes and raises
    ``UnicodeEncodeError``, crashing the CLI mid-run. Python 3.7+
    exposes ``reconfigure`` on text streams; we set encoding=utf-8 +
    errors='replace' so any truly-unencodable byte falls back to
    ``?`` rather than crashing.

    No-op on streams that don't support reconfigure (PIPEs without
    text wrapping, redirected file handles in some environments).
    """
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        if stream is None:
            continue
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8", errors="replace")
        except (OSError, ValueError):
            # Stream is closed, redirected to a non-text sink, or the
            # codec isn't available; degrade silently.
            pass


def main():
    _force_utf8_streams()
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
    parser.add_argument("--help-all", action="store_true",
                        help="emit markdown documentation for every subcommand to stdout and exit")

    sub = parser.add_subparsers(dest="command", title="commands")

    # ── Register subcommands ──────────────────────────────────
    from uofa_cli.commands import keygen, sign, verify, shacl, rules, check, validate, init, diff, schema, packs, migrate, import_excel, extract_cmd, adversarial, catalog, setup, demo
    from uofa_cli.commands import explain as explain_cmd

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
        "explain":     explain_cmd,
        "schema":      schema,
        "packs":       packs,
        "catalog":     catalog,
        "migrate":     migrate,
        "import":      import_excel,
        "extract":     extract_cmd,
        "adversarial": adversarial,
        "setup":       setup,
        "demo":        demo,
    }

    subparsers: dict[str, argparse.ArgumentParser] = {}
    for name, mod in modules.items():
        sp = sub.add_parser(name, help=mod.HELP, parents=[parent])
        mod.add_arguments(sp)
        subparsers[name] = sp

    # Pre-parse --pack so values supplied BEFORE the subcommand are preserved.
    # With parents=[parent], subparsers inherit a --pack action whose default
    # of None clobbers a top-level --pack value at full-parse time. The pre-
    # parse recovers it so `uofa --pack X catalog` and `uofa catalog --pack X`
    # behave identically.
    _pre_pack = argparse.ArgumentParser(add_help=False)
    _pre_pack.add_argument("--pack", action="append")
    _pre_args, _ = _pre_pack.parse_known_args()

    args = parser.parse_args()

    if getattr(args, "help_all", False):
        sys.stdout.write(_render_help_all(modules, subparsers))
        return 0

    if not args.command:
        parser.print_help()
        return 0

    if args.no_color:
        set_color(False)

    # Set active pack(s) before resolving repo root
    set_active_pack(_pre_args.pack or args.pack or ["vv40"])

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


def _render_help_all(
    modules: dict,
    subparsers: dict[str, argparse.ArgumentParser],
) -> str:
    """Emit a markdown reference for every subcommand.

    One section per command. Each section: heading, one-line summary,
    ``Usage`` block (from argparse format_usage), then a table of
    options when the parser has any beyond the inherited parent flags.
    """
    from datetime import datetime, timezone

    generated = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines: list[str] = [
        "---",
        f"title: '`uofa` CLI reference (v{__version__})'",
        "description: 'Auto-generated CLI reference covering every subcommand and flag. Re-runs on every site build via `uofa --help-all`.'",
        f"generated: {generated}",
        f"cli_version: v{__version__}",
        f"command_count: {len(modules)}",
        "---",
        "",
        f"Generated from `uofa --help-all` at {generated}. ",
        f"{len(modules)} subcommand{'s' if len(modules) != 1 else ''} available.",
        "",
        "## Synopsis",
        "",
        "```text",
        "uofa [--no-color] [--verbose] [--repo-root PATH] [--pack NAME] <command> [...]",
        "```",
        "",
        "Global flags inherited by every subcommand: `--no-color`, `--verbose`, "
        "`--repo-root`, `--pack`. See `uofa --help` for details.",
        "",
        "## Commands",
        "",
    ]

    for name in modules:
        mod = modules[name]
        sp = subparsers[name]
        usage = sp.format_usage().strip().replace("usage: ", "")
        lines.extend([
            f"### `uofa {name}`",
            "",
            f"_{getattr(mod, 'HELP', '').strip()}_",
            "",
            "```text",
            usage,
            "```",
            "",
        ])

        rows = _option_rows(sp)
        if rows:
            lines.extend([
                "| Flag | Description |",
                "|---|---|",
            ])
            lines.extend(rows)
            lines.append("")

    return "\n".join(lines) + "\n"


def _option_rows(sp: argparse.ArgumentParser) -> list[str]:
    """Return one markdown table row per command-specific option.

    Excludes inherited parent flags (--no-color, --verbose, --repo-root,
    --pack, -h/--help) since those are documented once in the synopsis.
    """
    skip = {"--no-color", "--verbose", "--repo-root", "--pack", "-h", "--help"}
    rows: list[str] = []
    for action in sp._actions:
        flags = action.option_strings
        if not flags or any(f in skip for f in flags):
            continue
        flag_str = ", ".join(f"`{f}`" for f in flags)
        if action.metavar:
            flag_str += f" `{action.metavar}`"
        elif action.choices:
            flag_str += f" {{{', '.join(str(c) for c in action.choices)}}}"
        help_text = (action.help or "").replace("|", "\\|").replace("\n", " ")
        rows.append(f"| {flag_str} | {help_text} |")
    return rows


if __name__ == "__main__":
    main()

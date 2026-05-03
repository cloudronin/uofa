"""uofa catalog — enumerate weakener patterns across active packs."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from uofa_cli import __version__
from uofa_cli.output import header, info, color, severity_badge, error
from uofa_cli import paths

HELP = "list all weakener patterns across active packs"

# Patterns in the rule body: a header comment then a rule block with
# patternId + severity + schema:description in the tail. The variable name
# (?ann, ?esc, ?override, …) varies across rules, so the regex binds on the
# pattern-id and severity literals.
_RULE_BLOCK = re.compile(
    r"^\s*#\s*(?P<title>W-[A-Z]+-\d{2}|COMPOUND-\d{2})[^:\n]*:\s*(?P<summary>[^\n]*)$"
    r"(?:[^[]*\[\s*\w+\s*:\s*)"
    r"(?:.*?)"
    r"\(\?\w+\s+uofa:patternId\s+'(?P<pid>W-[A-Z]+-\d{2}|COMPOUND-\d{2})'\).*?"
    r"\(\?\w+\s+uofa:severity\s+'(?P<severity>Critical|High|Medium|Low)'\).*?"
    r"(?:\(\?\w+\s+schema:description\s+'(?P<description>[^']*)'\)|\])",
    re.DOTALL | re.MULTILINE,
)


def add_arguments(parser):
    parser.add_argument("--format", "-f", default="table",
                        choices=["table", "json", "md"],
                        help="output format (default: table)")


def run(args) -> int:
    # Re-apply active pack from args: the subparser's --pack action clobbers
    # the parent parser's value at parse time, so the global set in cli.py
    # may not reflect what the user passed after the subcommand name.
    if args.pack:
        paths.set_active_pack(args.pack)
    records = _collect_patterns()
    if args.format == "json":
        print(json.dumps(records, indent=2))
        return 0
    if args.format == "md":
        print(_render_markdown(records))
        return 0
    return _render_table(records)


def _collect_patterns() -> list[dict]:
    """Gather all patterns from .rules files in active packs."""
    records: list[dict] = []
    for pack_name in _active_with_core():
        for rec in _parse_rules_for_pack(pack_name):
            records.append(rec)

    return sorted(records, key=lambda r: (r["pack"], r["patternId"]))


def _active_with_core() -> list[str]:
    active = paths.get_active_pack() or []
    ordered = ["core"]
    for name in active:
        if name != "core" and name not in ordered:
            ordered.append(name)
    return ordered


def _parse_rules_for_pack(pack_name: str) -> list[dict]:
    try:
        manifest = paths.pack_manifest(pack_name)
    except FileNotFoundError:
        return []

    rules_rel = manifest.get("rules")
    if not rules_rel:
        return []

    pack_dir = paths.pack_dir(pack_name)
    rules_path = pack_dir / rules_rel
    if not rules_path.exists():
        return []

    raw = rules_path.read_text()
    # Strip comment-only rule bodies so deferred rules (e.g. COMPOUND-02,
    # commented-out block) don't appear in the active catalog. Preserves
    # header comments (they document the rule) but removes rule bodies that
    # are fully commented out.
    cleaned_lines: list[str] = []
    for line in raw.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("#[") or stripped.startswith("#    ") or stripped == "#]":
            continue
        cleaned_lines.append(line)
    text = "\n".join(cleaned_lines)

    records: list[dict] = []
    seen: set[str] = set()
    for m in _RULE_BLOCK.finditer(text):
        pid = m.group("pid")
        if pid in seen:
            continue  # W-SI-02 etc. have multiple rule blocks
        seen.add(pid)
        records.append({
            "pack": pack_name,
            "patternId": pid,
            "severity": m.group("severity"),
            "description": m.group("description") or m.group("summary") or "",
        })
    return records


def _render_markdown(records: list[dict]) -> str:
    by_pack: dict[str, list[dict]] = {}
    for r in records:
        by_pack.setdefault(r["pack"], []).append(r)

    generated = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines: list[str] = [
        "---",
        f"title: 'Weakener catalog (v{__version__})'",
        "description: 'Auto-generated weakener pattern catalog across active packs. Re-runs on every site build via `uofa catalog --format md`.'",
        f"generated: {generated}",
        f"catalog_version: v{__version__}",
        f"total_patterns: {len(records)}",
        f"packs: [{', '.join(by_pack.keys())}]",
        "---",
        "",
        f"Generated from `uofa catalog --format md` at {generated}. ",
        f"{len(records)} pattern{'s' if len(records) != 1 else ''} across "
        f"{len(by_pack)} pack{'s' if len(by_pack) != 1 else ''}.",
        "",
    ]

    for pack_name, entries in by_pack.items():
        lines.extend([
            f"## Pack: `{pack_name}` ({len(entries)} pattern{'s' if len(entries) != 1 else ''})",
            "",
            "| Pattern | Severity | Description |",
            "|---|---|---|",
        ])
        for r in entries:
            desc = (r["description"] or "").replace("|", "\\|").strip()
            lines.append(f"| `{r['patternId']}` | {r['severity']} | {desc} |")
        lines.append("")

    return "\n".join(lines)


def _render_table(records: list[dict]) -> int:
    if not records:
        info("No patterns found.")
        return 0

    by_pack: dict[str, list[dict]] = {}
    for r in records:
        by_pack.setdefault(r["pack"], []).append(r)

    total = 0
    for pack_name, entries in by_pack.items():
        header(f"Pack: {pack_name} ({len(entries)} patterns)")
        for r in entries:
            sev = severity_badge(r["severity"])
            pack_tag = color(f"[{r['pack']}]", "dim")
            pid = color(r["patternId"], "yellow")
            desc = r["description"]
            if len(desc) > 90:
                desc = desc[:87] + "..."
            info(f"  {pid:<16} {sev} {pack_tag}  {desc}")
        total += len(entries)

    info("")
    info(f"  Total: {total} patterns across {len(by_pack)} pack(s)")
    return 0

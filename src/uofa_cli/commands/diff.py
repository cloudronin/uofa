"""uofa diff — compare weakener profiles across two UofA files."""

import json
from pathlib import Path

from uofa_cli.output import header, step_header, result_line, info, color, severity_badge

HELP = "compare weakener profiles between two UofA files (COU divergence)"


def add_arguments(parser):
    parser.add_argument("file_a", type=Path, help="first UofA JSON-LD file")
    parser.add_argument("file_b", type=Path, help="second UofA JSON-LD file")


def _load_weakeners(path: Path) -> tuple[str, list[dict]]:
    """Load a UofA file and extract its name and weakener annotations."""
    with open(path) as f:
        doc = json.load(f)

    name = doc.get("name", path.stem)
    weakeners = doc.get("hasWeakener", [])
    if isinstance(weakeners, dict):
        weakeners = [weakeners]

    return name, weakeners


def _weakener_set(weakeners: list[dict]) -> dict[str, list[dict]]:
    """Group weakeners by patternId."""
    grouped = {}
    for w in weakeners:
        pid = w.get("patternId", "unknown")
        grouped.setdefault(pid, []).append(w)
    return grouped


def _print_weakener_group(pid: str, items: list[dict], prefix: str = ""):
    """Print a group of weakeners for a pattern ID."""
    sev = items[0].get("severity", "Medium") if items else "Medium"
    badge = severity_badge(sev)
    print(f"  {prefix}{badge} {color(pid, 'bold')} — {len(items)} hit(s)")
    for w in items:
        node = w.get("affectedNode", "")
        if isinstance(node, str):
            short = node.rsplit("/", 1)[-1]
        else:
            short = str(node)
        print(f"      {prefix}  -> {short}")


def run(args) -> int:
    if not args.file_a.exists():
        raise FileNotFoundError(f"File not found: {args.file_a}")
    if not args.file_b.exists():
        raise FileNotFoundError(f"File not found: {args.file_b}")

    name_a, weak_a = _load_weakeners(args.file_a)
    name_b, weak_b = _load_weakeners(args.file_b)

    set_a = _weakener_set(weak_a)
    set_b = _weakener_set(weak_b)

    pids_a = set(set_a.keys())
    pids_b = set(set_b.keys())

    only_a = sorted(pids_a - pids_b)
    only_b = sorted(pids_b - pids_a)
    shared = sorted(pids_a & pids_b)

    header("COU Divergence Analysis")
    info(f"A: {name_a}  ({len(weak_a)} weakener(s))")
    info(f"B: {name_b}  ({len(weak_b)} weakener(s))")

    # ── Shared weakeners ──────────────────────────────────────
    if shared:
        step_header(f"Shared patterns ({len(shared)})")
        for pid in shared:
            count_a = len(set_a[pid])
            count_b = len(set_b[pid])
            sev = set_a[pid][0].get("severity", "Medium")
            badge = severity_badge(sev)
            diff_note = ""
            if count_a != count_b:
                diff_note = f"  (A: {count_a}, B: {count_b})"
            print(f"  {badge} {color(pid, 'bold')} — {count_a + count_b} total hit(s){diff_note}")

    # ── Only in A ─────────────────────────────────────────────
    if only_a:
        step_header(f"Only in A: {args.file_a.stem} ({len(only_a)} pattern(s))")
        for pid in only_a:
            _print_weakener_group(pid, set_a[pid])

    # ── Only in B ─────────────────────────────────────────────
    if only_b:
        step_header(f"Only in B: {args.file_b.stem} ({len(only_b)} pattern(s))")
        for pid in only_b:
            _print_weakener_group(pid, set_b[pid])

    # ── Summary ───────────────────────────────────────────────
    if not only_a and not only_b:
        print()
        result_line("No divergence", True, "Both files have identical weakener patterns")
    else:
        print()
        divergent = len(only_a) + len(only_b)
        info(f"Divergence: {divergent} pattern(s) differ between COUs")
        if only_a:
            info(f"  {len(only_a)} pattern(s) only in A — unique risks in {args.file_a.stem}")
        if only_b:
            info(f"  {len(only_b)} pattern(s) only in B — unique risks in {args.file_b.stem}")

    return 0

"""uofa diff — compare weakener profiles across two UofA files."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from uofa_cli.output import (
    header, step_header, result_line, info, color, severity_badge,
    muted, diamond, table_header, table_row, table_separator, table_footer,
)
from uofa_cli.explain import explain_divergence
from uofa_cli import paths

HELP = "compare weakener profiles between two UofA files (COU divergence)"

_SEVERITY_ORDER = ["Critical", "High", "Medium", "Low"]

# Regex to parse pattern lines from Jena rule engine output:
#   ⚠ W-EP-04 [High] — 6 hit(s)
#   ⚡ COMPOUND-01 [Critical] — 1 hit(s)
_ENGINE_PATTERN_RE = re.compile(
    r'[⚠⚡]\s+((?:W-[A-Z]{2}-\d{2}|COMPOUND-\d{2}))\s+'
    r'\[(Critical|High|Medium|Low)\]\s+—\s+(\d+)\s+hit'
)


def add_arguments(parser):
    parser.add_argument("file_a", type=Path, help="first UofA JSON-LD file")
    parser.add_argument("file_b", type=Path, help="second UofA JSON-LD file")
    parser.add_argument("--build", action="store_true",
                        help="auto-build the Jena JAR if missing")
    parser.add_argument("--skip-rules", action="store_true",
                        help="compare static hasWeakener arrays instead of running rules")


# ── Rules engine integration ────────────────────────────────

def _parse_weakeners_from_output(stdout: str) -> list[dict]:
    """Parse Jena rule engine text output into weakener dicts.

    Returns one dict per distinct pattern (deduplicated by patternId).
    Each dict has: patternId, severity.
    """
    seen = {}
    for m in _ENGINE_PATTERN_RE.finditer(stdout):
        pid, sev, _hits = m.group(1), m.group(2), m.group(3)
        if pid not in seen:
            seen[pid] = {"patternId": pid, "severity": sev}
    return list(seen.values())


def _load_rule_descriptions(rules_path: Path) -> dict[str, str]:
    """Parse schema:description strings from a .rules file by patternId.

    Scans each rule block for patternId and description literals.
    Returns {patternId: description}.
    """
    descriptions = {}
    try:
        text = rules_path.read_text()
    except (FileNotFoundError, OSError):
        return descriptions

    # Split into rule blocks (delimited by [...] sections)
    # Find all patternId and description pairs within the text
    pid_re = re.compile(r"uofa:patternId\s+'([^']+)'")
    desc_re = re.compile(r"schema:description\s+'([^']+)'")

    # Process rule blocks separated by blank lines or rule headers
    current_pid = None
    for line in text.splitlines():
        pid_match = pid_re.search(line)
        if pid_match:
            current_pid = pid_match.group(1)

        desc_match = desc_re.search(line)
        if desc_match and current_pid:
            descriptions[current_pid] = desc_match.group(1)
            current_pid = None

    return descriptions


def _run_rules_engine(jsonld_path: Path, build: bool = False) -> list[dict]:
    """Run Jena rule engine on a file and return parsed weakener dicts.

    Each dict has: patternId, severity, description (if available).
    Raises FileNotFoundError if Java or JAR is unavailable.
    """
    from uofa_cli.commands.rules import _ensure_java, _ensure_jar

    _ensure_java()
    jar = _ensure_jar(build)

    rules_path = paths.rules_file(jsonld_path)
    ctx = paths.context_file()

    cmd = [
        "java", "-jar", str(jar), str(jsonld_path),
        "--rules", str(rules_path), "--context", str(ctx),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Rule engine failed on {jsonld_path.name}")

    weakeners = _parse_weakeners_from_output(result.stdout)

    # Enrich with descriptions from the rules file
    descriptions = _load_rule_descriptions(rules_path)
    for w in weakeners:
        pid = w["patternId"]
        if pid in descriptions:
            w["description"] = descriptions[pid]

    return weakeners


# ── Data extraction ──────────────────────────────────────────

def _load_profile(path: Path) -> dict:
    """Load a UofA JSON-LD file and return the full document."""
    with open(path) as f:
        return json.load(f)


def _extract_weakeners(doc: dict) -> list[dict]:
    """Extract hasWeakener array from a document (static fallback)."""
    weakeners = doc.get("hasWeakener", [])
    if isinstance(weakeners, dict):
        weakeners = [weakeners]
    return weakeners


def _weakener_set(weakeners: list[dict]) -> dict[str, list[dict]]:
    """Group weakeners by patternId."""
    grouped = {}
    for w in weakeners:
        pid = w.get("patternId", "unknown")
        grouped.setdefault(pid, []).append(w)
    return grouped


def _extract_cou_identity(doc: dict) -> dict:
    """Extract COU identity metadata for the header block."""
    cou = doc.get("hasContextOfUse", {})
    if isinstance(cou, str):
        cou = {}

    cou_name = cou.get("name", doc.get("name", "(unnamed)"))
    cou_desc = cou.get("description", "")
    cou_name_and_desc = f"{cou_name} {cou_desc}"

    # Parse device class from COU name or description (e.g., "Class II", "Class III")
    device_class = _parse_regex(cou_name_and_desc, r"Class\s+(I{1,3}V?)")
    if device_class:
        device_class = f"Class {device_class}"

    # Parse model risk level (e.g., "Model Risk Level 2")
    mrl = _parse_regex(cou_name_and_desc, r"Model Risk Level\s+(\d+)")
    if mrl:
        mrl = f"MRL {mrl}"

    # Decision record
    dr = doc.get("hasDecisionRecord", {})
    if isinstance(dr, str):
        dr = {}
    outcome = dr.get("outcome", "(not specified)")

    assurance = doc.get("assuranceLevel", "(not specified)")

    return {
        "cou_name": cou_name,
        "device_class": device_class or "(not detected)",
        "model_risk_level": mrl or "(not detected)",
        "outcome": outcome,
        "assurance_level": assurance,
    }


def _parse_regex(text: str, pattern: str) -> str | None:
    """Extract first capture group from text, or None."""
    m = re.search(pattern, text, re.IGNORECASE)
    return m.group(1) if m else None


def _severity_tier_counts(weakeners: list[dict]) -> dict[str, int]:
    """Count weakeners by severity tier."""
    counts = {s: 0 for s in _SEVERITY_ORDER}
    for w in weakeners:
        sev = w.get("severity", "Medium")
        counts[sev] = counts.get(sev, 0) + 1
    return counts


def _is_compound(pid: str) -> bool:
    return pid.startswith("COMPOUND-")


# ── Section printers ─────────────────────────────────────────

def _print_identity_block(id_a: dict, id_b: dict, count_a: int, count_b: int):
    """Section 1: COU Identity Block."""
    header("COU Divergence Analysis")

    # Side-by-side identity
    label_w = 18
    print()
    print(f"  {'':>{label_w}}  {color('COU A', 'bold'):<32}  {color('COU B', 'bold')}")
    print(f"  {'Name':>{label_w}}  {id_a['cou_name']:<32}  {id_b['cou_name']}")
    print(f"  {'Device class':>{label_w}}  {id_a['device_class']:<32}  {id_b['device_class']}")
    print(f"  {'Model risk level':>{label_w}}  {id_a['model_risk_level']:<32}  {id_b['model_risk_level']}")
    print(f"  {'Decision':>{label_w}}  {id_a['outcome']:<32}  {id_b['outcome']}")
    print(f"  {'Assurance level':>{label_w}}  {id_a['assurance_level']:<32}  {id_b['assurance_level']}")
    print(f"  {'Weakeners':>{label_w}}  {count_a:<32}  {count_b}")


def _print_profile_table(all_pids: list[str], set_a: dict, set_b: dict):
    """Section 2: Weakener Profile Table."""
    core_pids = [p for p in all_pids if not _is_compound(p)]
    compound_pids = [p for p in all_pids if _is_compound(p)]

    if not all_pids:
        return

    cols = ["Pattern", "Severity", "COU A", "COU B", "Status"]
    widths = [12, 10, 7, 7, 12]

    def _render_table(pids, label):
        if not pids:
            return
        step_header(label)
        table_header(cols, widths)
        for pid in pids:
            in_a = pid in set_a
            in_b = pid in set_b
            sev = ""
            if in_a:
                sev = set_a[pid][0].get("severity", "Medium")
            elif in_b:
                sev = set_b[pid][0].get("severity", "Medium")

            mark_a = color("  ✓ ", "green") if in_a else color("  ✗ ", "red")
            mark_b = color("  ✓ ", "green") if in_b else color("  ✗ ", "red")

            divergent = in_a != in_b
            if divergent:
                status = f"{diamond()} divergent"
            else:
                status = muted("  same")

            table_row(
                [pid, severity_badge(sev), mark_a, mark_b, status],
                widths,
                highlight=False,
            )
        table_footer(widths)

    _render_table(core_pids, f"Weakener Patterns ({len(core_pids)})")
    _render_table(compound_pids, f"Compound Patterns ({len(compound_pids)})")


def _print_summary_counts(weak_a: list[dict], weak_b: list[dict],
                          id_a: dict, id_b: dict, divergence_count: int):
    """Section 3: Summary Counts."""
    step_header("Summary")

    counts_a = _severity_tier_counts(weak_a)
    counts_b = _severity_tier_counts(weak_b)

    info(f"COU A ({id_a['cou_name']}):")
    for sev in _SEVERITY_ORDER:
        if counts_a[sev]:
            info(f"  {severity_badge(sev)} {counts_a[sev]}")

    info(f"COU B ({id_b['cou_name']}):")
    for sev in _SEVERITY_ORDER:
        if counts_b[sev]:
            info(f"  {severity_badge(sev)} {counts_b[sev]}")

    print()
    if divergence_count == 0:
        result_line("No divergence", True, "Both files have identical weakener patterns")
    else:
        info(color(f"{divergence_count} divergence(s) detected", "yellow"))


def _print_divergence_explanations(only_a: list[str], only_b: list[str],
                                   set_a: dict, set_b: dict,
                                   doc_a: dict, doc_b: dict):
    """Section 4: Divergence Explanations."""
    if not only_a and not only_b:
        return

    step_header("Divergence Explanations")

    for pid in only_a:
        weakener = set_a[pid][0]
        sev = weakener.get("severity", "Medium")
        print(f"\n  {severity_badge(sev)} {color(pid, 'bold')} — only in COU A")
        lines = explain_divergence(pid, doc_a, doc_b, weakener)
        for line in lines:
            info(f"  {line}")

    for pid in only_b:
        weakener = set_b[pid][0]
        sev = weakener.get("severity", "Medium")
        print(f"\n  {severity_badge(sev)} {color(pid, 'bold')} — only in COU B")
        lines = explain_divergence(pid, doc_b, doc_a, weakener)
        for line in lines:
            info(f"  {line}")


# ── Entry point ──────────────────────────────────────────────

def run(args) -> int:
    if not args.file_a.exists():
        raise FileNotFoundError(f"File not found: {args.file_a}")
    if not args.file_b.exists():
        raise FileNotFoundError(f"File not found: {args.file_b}")

    doc_a = _load_profile(args.file_a)
    doc_b = _load_profile(args.file_b)

    # Determine weakener source: rule engine (default) or static hasWeakener
    if getattr(args, 'skip_rules', False):
        weak_a = _extract_weakeners(doc_a)
        weak_b = _extract_weakeners(doc_b)
    else:
        try:
            weak_a = _run_rules_engine(
                args.file_a, build=getattr(args, 'build', False))
            weak_b = _run_rules_engine(
                args.file_b, build=getattr(args, 'build', False))
        except (FileNotFoundError, RuntimeError):
            info("Java/Jena not available — falling back to static hasWeakener comparison")
            weak_a = _extract_weakeners(doc_a)
            weak_b = _extract_weakeners(doc_b)

    set_a = _weakener_set(weak_a)
    set_b = _weakener_set(weak_b)

    pids_a = set(set_a.keys())
    pids_b = set(set_b.keys())

    only_a = sorted(pids_a - pids_b)
    only_b = sorted(pids_b - pids_a)
    all_pids = sorted(pids_a | pids_b)

    id_a = _extract_cou_identity(doc_a)
    id_b = _extract_cou_identity(doc_b)

    divergence_count = len(only_a) + len(only_b)

    # Section 1: COU Identity Block
    _print_identity_block(id_a, id_b, len(pids_a), len(pids_b))

    # Section 2: Weakener Profile Table
    _print_profile_table(all_pids, set_a, set_b)

    # Section 3: Summary Counts
    _print_summary_counts(weak_a, weak_b, id_a, id_b, divergence_count)

    # Section 4: Divergence Explanations
    _print_divergence_explanations(only_a, only_b, set_a, set_b, doc_a, doc_b)

    return 0

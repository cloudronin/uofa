"""uofa rules — run the Jena rule engine for weakener detection."""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from uofa_cli.output import step_header, error, info, color, severity_badge
from uofa_cli import paths
from uofa_cli.python_rules import detect_w_prov_01, detect_w_con_02, detect_w_con_05

HELP = "detect quality gaps with Jena rule engine (C3)"

# Patterns to colorize in Jena output
_SEVERITY_RE = re.compile(r'\[(Critical|High|Medium|Low)\]')
_COMPOUND_RE = re.compile(r'(⚡\s*COMPOUND-\d+)')
_PATTERN_RE = re.compile(r'(⚠\s*W-[A-Z]+-\d{2})')
_SUMMARY_LINE_RE = re.compile(r'^(\s*)(Critical|High|Medium|Low):\s+(\d+)$')


def add_arguments(parser):
    parser.add_argument("file", type=Path, help="UofA JSON-LD file to analyze")
    parser.add_argument("--rules", "-r", type=Path, help="path to .rules file")
    parser.add_argument("--context", "-c", type=Path, help="JSON-LD context file")
    parser.add_argument("--build", action="store_true", help="auto-build the Jena JAR if missing")
    parser.add_argument("--raw", action="store_true", help="show raw output without coloring")
    parser.add_argument("--format", "-f", default="summary",
                        choices=["summary", "turtle", "ntriples", "jsonld"],
                        help="output format (default: summary)")
    parser.add_argument("--output", "-o", type=Path,
                        help="write reasoned output to a file (default: stdout)")


def _ensure_java():
    if not shutil.which("java"):
        raise FileNotFoundError(
            "Java not found. Install Java 17+: https://adoptium.net/\n"
            "  Or skip the rule engine: uofa check FILE --skip-rules"
        )


def _ensure_jar(build: bool):
    jar = paths.jar_path()
    if jar.exists():
        return jar

    if not build:
        raise FileNotFoundError(
            f"Jena engine not built: {jar}\n"
            "  Run: uofa rules FILE --build\n"
            "  Or:  cd weakener-engine && mvn package"
        )

    if not shutil.which("mvn"):
        raise FileNotFoundError(
            "Maven not found. Install Maven 3.8+ to build the rule engine.\n"
            "  Or build manually: cd weakener-engine && mvn package"
        )

    info("Building Jena rule engine...")
    result = subprocess.run(
        ["mvn", "package", "-q"],
        cwd=str(paths.engine_dir()),
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        error(f"Maven build failed:\n{result.stderr}")
        raise RuntimeError("Failed to build Jena rule engine")

    return jar


def _colorize_line(line: str) -> str:
    """Apply severity coloring to a single line of rule engine output."""
    # Colorize summary counts: "    Critical:  16"
    m = _SUMMARY_LINE_RE.match(line)
    if m:
        indent, sev, count = m.group(1), m.group(2), m.group(3)
        sev_colors = {"Critical": "red", "High": "yellow", "Medium": "cyan", "Low": "dim"}
        c = sev_colors.get(sev, "dim")
        return f"{indent}{color(sev + ':', c)}  {color(count, c)}"

    # Colorize [Critical], [High], etc. inline
    def _replace_severity(match):
        sev = match.group(1)
        return severity_badge(sev)

    line = _SEVERITY_RE.sub(_replace_severity, line)

    # Colorize compound pattern IDs
    line = _COMPOUND_RE.sub(lambda m: color(m.group(1), "red"), line)

    # Colorize core pattern IDs
    line = _PATTERN_RE.sub(lambda m: color(m.group(1), "yellow"), line)

    return line


def _combine_rules_files(rules_paths: list[Path]) -> Path:
    """Concatenate multiple rules files into a single temp file."""
    if len(rules_paths) == 1:
        return rules_paths[0]

    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".rules", delete=False)
    seen_prefixes = set()
    for rp in rules_paths:
        content = rp.read_text()
        # Deduplicate @prefix declarations
        lines = []
        for line in content.splitlines():
            if line.strip().startswith("@prefix"):
                if line.strip() not in seen_prefixes:
                    seen_prefixes.add(line.strip())
                    lines.append(line)
            else:
                lines.append(line)
        tmp.write("\n".join(lines))
        tmp.write("\n\n")
    tmp.close()
    return Path(tmp.name)


def run(args) -> int:
    if not args.file.exists():
        raise FileNotFoundError(f"File not found: {args.file}")

    _ensure_java()
    jar = _ensure_jar(args.build)

    if args.rules:
        rules = args.rules
    else:
        rules_list = paths.all_rules_files(args.file)
        rules = _combine_rules_files(rules_list)

    ctx = args.context or paths.context_file()

    step_header("C3: Jena rule engine — weakener detection")
    sys.stdout.flush()

    cmd = ["java", "-jar", str(jar), str(args.file), "--rules", str(rules), "--context", str(ctx)]
    if args.format and args.format != "summary":
        cmd += ["--format", args.format]
    if args.output:
        cmd += ["--output", str(args.output)]

    # If writing to a file, the engine produces no stdout content for the caller
    # to colorize — just pipe through.
    if args.output or args.raw:
        result = subprocess.run(cmd, capture_output=False)
        return result.returncode

    # Capture and colorize output
    result = subprocess.run(cmd, capture_output=True, text=True)

    # W-PROV-01 and W-CON-02 run as Python post-passes. Forward RETE cannot
    # express transitive-closure absence (W-PROV-01) or cross-subject dangling
    # reference checks (W-CON-02). Only runs on --format summary.
    python_annotations = []
    if not args.format or args.format == "summary":
        for detector_name, detector in (("W-PROV-01", detect_w_prov_01),
                                        # W-CON-02 ported to Jena at v0.5.2.
                                        ("W-CON-05", detect_w_con_05)):
            try:
                python_annotations.extend(detector(args.file, ctx))
            except Exception as e:  # noqa: BLE001
                # Never block Jena output on a Python-pass failure.
                print(f"  ({detector_name} Python detector skipped: {e})", file=sys.stderr)

    lines = result.stdout.splitlines()
    if python_annotations:
        lines = _merge_python_annotations(lines, python_annotations)

    for line in lines:
        print(_colorize_line(line))

    if result.stderr:
        print(result.stderr, file=sys.stderr, end="")

    return result.returncode


def _merge_python_annotations(jena_lines: list[str], annotations: list[dict]) -> list[str]:
    """Fold Python-rule annotations into Jena's summary output.

    - Bumps the "SUMMARY: N weakener(s) detected" line by len(annotations).
    - Bumps per-severity counts (currently all W-PROV-01 are Critical).
    - Appends a W-PROV-01 section after the last existing ⚠ block.
    """
    n_new = len(annotations)
    by_severity = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
    by_pid: dict[str, list[dict]] = {}
    for ann in annotations:
        by_severity[ann["severity"]] = by_severity.get(ann["severity"], 0) + 1
        by_pid.setdefault(ann["patternId"], []).append(ann)

    out: list[str] = []
    summary_re = re.compile(r"^(\s*)SUMMARY:\s+(\d+)\s+weakener\(s\) detected(.*)$")
    sev_re = _SUMMARY_LINE_RE
    last_pattern_block_end = -1

    for i, line in enumerate(jena_lines):
        m = summary_re.match(line)
        if m:
            indent, n, tail = m.group(1), int(m.group(2)), m.group(3)
            out.append(f"{indent}SUMMARY: {n + n_new} weakener(s) detected{tail}")
            continue

        m = sev_re.match(line)
        if m:
            indent, sev, n = m.group(1), m.group(2), int(m.group(3))
            new_n = n + by_severity.get(sev, 0)
            out.append(f"{indent}{sev}: {' ' * max(1, 6 - len(str(new_n)))}{new_n}")
            continue

        out.append(line)
        if line.strip().startswith(("⚠", "→ affected:")):
            last_pattern_block_end = len(out)

    # Append the W-PROV-01 block after the last Jena ⚠ block (or at end).
    insert_at = last_pattern_block_end if last_pattern_block_end > 0 else len(out)
    new_block: list[str] = []
    for pid in sorted(by_pid):
        anns = by_pid[pid]
        severity = anns[0]["severity"]
        new_block.append(f"  ⚠ {pid} [{severity}] — {len(anns)} hit(s)")
        for ann in anns:
            short = ann["affectedNode"].rsplit("/", 1)[-1].rsplit("#", 1)[-1]
            new_block.append(f"      → affected: {short}")

    out[insert_at:insert_at] = new_block
    return out

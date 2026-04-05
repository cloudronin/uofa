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

    if args.raw:
        result = subprocess.run(cmd, capture_output=False)
        return result.returncode

    # Capture and colorize output
    result = subprocess.run(cmd, capture_output=True, text=True)

    for line in result.stdout.splitlines():
        print(_colorize_line(line))

    if result.stderr:
        print(result.stderr, file=sys.stderr, end="")

    return result.returncode

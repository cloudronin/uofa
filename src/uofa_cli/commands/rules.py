"""uofa rules — run the Jena rule engine for weakener detection."""

import shutil
import subprocess
import sys
from pathlib import Path

from uofa_cli.output import step_header, error, info
from uofa_cli import paths

HELP = "detect quality gaps with Jena rule engine (C3)"


def add_arguments(parser):
    parser.add_argument("file", type=Path, help="UofA JSON-LD file to analyze")
    parser.add_argument("--rules", "-r", type=Path, help="path to .rules file")
    parser.add_argument("--context", "-c", type=Path, help="JSON-LD context file")
    parser.add_argument("--build", action="store_true", help="auto-build the Jena JAR if missing")


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


def run(args) -> int:
    if not args.file.exists():
        raise FileNotFoundError(f"File not found: {args.file}")

    _ensure_java()
    jar = _ensure_jar(args.build)

    rules = args.rules or paths.rules_file(args.file)
    ctx = args.context or paths.context_file()

    step_header("C3: Jena rule engine — weakener detection")
    sys.stdout.flush()

    cmd = ["java", "-jar", str(jar), str(args.file), "--rules", str(rules), "--context", str(ctx)]
    result = subprocess.run(cmd, capture_output=False)
    return result.returncode

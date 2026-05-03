"""Pre-tag release checklist for uofa-cli.

Run before tagging a new release to catch the kinds of issues that have
slipped past local testing in past tags. Each check addresses a real bug
that shipped to a tag and required a follow-up patch:

- v0.6.2 → v0.6.3: backslash-in-fstring valid in Python 3.12 but broke
  pytest collection on the 3.11 CI runner.
  → check_python_syntax_compat() ast-parses src/ under every supported
    Python interpreter that's installed locally.

- v0.6.3 → v0.6.4: `.github/workflows/release-wheels.yml` referenced
  pre-reorg paths (weakener-engine, hatch_build.py at root, etc.); the
  build-jar step couldn't `cd` into the engine directory.
  → check_workflow_paths() greps run/path/paths entries from every
    workflow and verifies the targets actually exist on disk.

- v0.6.4 hot-fix: devcontainer's postCreateCommand only installed
  [test,excel] extras, but the v0.6.x explain pipeline + LLM backends
  need jinja2/litellm/requests from [extract]. CI ran tests against an
  install missing those deps; 46 tests degraded.
  → check_test_imports_vs_install() scans tests/ for top-level imports,
    cross-references against pyproject.toml extras, and confirms the
    devcontainer install line covers everything tests touch.

Plus the standard pre-tag hygiene:
- check_git_state(): clean working tree, on main, up to date with origin
- check_version_match(): pyproject.toml version matches the intended tag

Usage:
    python dev/tools/scripts/release_check.py
    python dev/tools/scripts/release_check.py --tag v0.6.5
    python dev/tools/scripts/release_check.py --tag v0.6.5 --full

Without --full, runs in seconds (no pytest). Exits non-zero on any
failure so you can chain: `release_check.py --tag v0.6.5 && git tag ...`.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
import sys
from pathlib import Path

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:
    import tomli as tomllib  # type: ignore[no-redef]


REPO = Path(__file__).resolve().parents[3]
INDENT = "  "

# Imports that map to pip names that don't auto-derive from the import
# name (e.g. `import yaml` → pip install pyyaml). Used by the test-deps
# auditor to compare imports against pyproject extras.
IMPORT_TO_PIP_NAME = {
    "yaml": "pyyaml",
    "docx": "python-docx",
    "PIL": "pillow",
    "msoffcrypto": "msoffcrypto-tool",
}


# ── Output helpers ─────────────────────────────────────────


def step(name: str) -> None:
    print(f"\n── {name} ─────")


def ok(msg: str) -> None:
    print(f"{INDENT}✓ {msg}")


def fail(msg: str) -> None:
    print(f"{INDENT}✗ {msg}")


def warn(msg: str) -> None:
    print(f"{INDENT}⚠ {msg}")


# ── Check 1: git state ────────────────────────────────────


def check_git_state() -> bool:
    step("Git state")
    porcelain = subprocess.run(
        ["git", "status", "--porcelain"], cwd=REPO,
        capture_output=True, text=True,
    ).stdout.strip()
    if porcelain:
        n = len(porcelain.splitlines())
        fail(f"working tree has {n} uncommitted change(s); commit or stash first")
        for line in porcelain.splitlines()[:5]:
            print(f"{INDENT}    {line}")
        if n > 5:
            print(f"{INDENT}    ... and {n - 5} more")
        return False
    ok("working tree clean")

    branch = subprocess.run(
        ["git", "branch", "--show-current"], cwd=REPO,
        capture_output=True, text=True,
    ).stdout.strip()
    if branch != "main":
        fail(f"on branch {branch!r}, expected main")
        return False
    ok(f"on branch {branch}")

    # Refresh remote tracking so the ahead/behind count is current.
    subprocess.run(["git", "fetch", "origin", "main"], cwd=REPO, capture_output=True)
    parts = subprocess.run(
        ["git", "rev-list", "--left-right", "--count", "origin/main...HEAD"],
        cwd=REPO, capture_output=True, text=True,
    ).stdout.strip().split()
    if len(parts) != 2:
        warn("could not check upstream divergence — proceeding anyway")
        return True
    behind, ahead = int(parts[0]), int(parts[1])
    if behind > 0:
        fail(f"branch is {behind} commit(s) behind origin/main — pull first")
        return False
    ok(f"up to date with origin/main (ahead by {ahead})")
    return True


# ── Check 2: version coherence ─────────────────────────────


def check_version_match(tag: str | None) -> bool:
    step("Version coherence")
    if tag is None:
        ok("(no --tag passed; skipping)")
        return True
    if not tag.startswith("v"):
        fail(f"tag {tag!r} should start with 'v' (e.g. v0.6.5)")
        return False
    expected = tag[1:]
    pyproj = tomllib.loads((REPO / "pyproject.toml").read_text())
    actual = pyproj["project"]["version"]
    if actual != expected:
        fail(f"pyproject.toml version is {actual!r}, tag implies {expected!r}")
        print(f"{INDENT}    fix: update version = \"{expected}\" in pyproject.toml")
        return False
    ok(f"pyproject.toml version = {actual} matches tag {tag}")
    return True


# ── Check 3: Python syntax compat across supported versions ──


def check_python_syntax_compat() -> bool:
    step("Python syntax compat (ast.parse) under every installed supported version")
    pyproj = tomllib.loads((REPO / "pyproject.toml").read_text())
    requires = pyproj["project"]["requires-python"]
    m = re.match(r">=\s*(\d+)\.(\d+)", requires)
    if not m:
        fail(f"can't parse requires-python = {requires!r} for min version")
        return False
    min_minor = int(m.group(2))

    src_files = sorted((REPO / "src/uofa_cli").rglob("*.py"))

    # Run ast.parse via each installed python interpreter. Embed a small
    # script as a string so the child interpreter — not us — does the
    # parse using ITS Python version's syntax rules.
    parse_script = (
        "import ast, sys\n"
        "errors = []\n"
        "for f in sys.argv[1:]:\n"
        "    try: ast.parse(open(f, encoding='utf-8').read(), filename=f)\n"
        "    except SyntaxError as e: errors.append(f'{f}:{e.lineno}: {e.msg}')\n"
        "print('\\n'.join(errors))\n"
        "sys.exit(1 if errors else 0)\n"
    )

    overall_ok = True
    checked_any = False
    for minor in range(min_minor, 14):  # check up to 3.13 (extend as needed)
        py = f"python3.{minor}"
        which = subprocess.run(["which", py], capture_output=True, text=True)
        if which.returncode != 0:
            warn(f"{py} not installed; skipping (install via pyenv/uv if you maintain wheels for it)")
            continue
        checked_any = True
        result = subprocess.run(
            [py, "-c", parse_script] + [str(f) for f in src_files],
            capture_output=True, text=True, cwd=REPO,
        )
        if result.returncode != 0:
            fail(f"{py} found syntax errors:")
            for line in (result.stdout or "").strip().splitlines():
                print(f"{INDENT}    {line}")
            if result.stderr:
                print(f"{INDENT}    stderr: {result.stderr.strip()[:200]}")
            overall_ok = False
        else:
            ok(f"{py}: parsed {len(src_files)} files cleanly")

    if not checked_any:
        warn("no supported Python interpreter found — install at least the minimum supported version locally")
    return overall_ok


# ── Check 4: workflow path audit ───────────────────────────


def check_workflow_paths() -> bool:
    step("CI workflow path audit (paths referenced must exist)")
    workflows = sorted((REPO / ".github/workflows").glob("*.yml"))
    if not workflows:
        warn("no workflows found")
        return True

    # Three patterns we audit (the ones that drift after repo reorgs):
    #   `cd <path>` inside `run:` lines → must be a real directory
    #   `path: <path>` (artifact upload/download) → parent must exist
    #   `paths: ['<glob>', ...]` (filter) → leading directory of each glob
    overall_ok = True
    for wf in workflows:
        text = wf.read_text()
        problems: list[str] = []

        # Pattern 1: `cd <path>` in shell-style run blocks.
        for m in re.finditer(r"(?:^|[\s|;&])cd\s+([./a-zA-Z0-9_\-]+)", text):
            target = m.group(1)
            if not (REPO / target).exists():
                problems.append(f"cd {target!r} (does not exist)")

        # Pattern 2: `path:` keys (artifact upload/download).
        for m in re.finditer(r"^\s*path:\s*['\"]?([./a-zA-Z0-9_\-*/]+)['\"]?", text, re.MULTILINE):
            target = m.group(1)
            # Strip glob suffix; verify the directory part exists.
            head = target.split("*", 1)[0].rstrip("/")
            if head and not (REPO / head).exists():
                # Allow output-only paths created by earlier workflow steps —
                # these don't exist at audit time but are populated in CI.
                # `target/` is the Maven output dir; `dist/`/`build/` are PEP 517 outputs.
                BUILD_OUTPUT_DIRS = {"dist", "build", "tmp", "target"}
                if any(part in BUILD_OUTPUT_DIRS for part in head.split("/")):
                    continue
                problems.append(f"path: {target!r} (does not exist)")

        # Pattern 3: `paths:` filter list — check each glob's leading dir.
        # Match `paths:` block followed by indented `- 'path/glob'` lines.
        paths_block_re = re.compile(
            r"^\s*paths:\s*\n((?:\s*-\s*['\"][^'\"]+['\"]\s*\n)+)",
            re.MULTILINE,
        )
        for block_m in paths_block_re.finditer(text):
            for line_m in re.finditer(r"-\s*['\"]([^'\"]+)['\"]", block_m.group(1)):
                pat = line_m.group(1)
                head = pat.split("*", 1)[0].rstrip("/")
                if not head:
                    continue
                # Single file vs directory: existence is good enough.
                if not (REPO / head).exists():
                    problems.append(f"paths: {pat!r} (leading {head!r} does not exist)")

        if problems:
            fail(f"{wf.name} references {len(problems)} stale path(s):")
            for p in problems:
                print(f"{INDENT}    {p}")
            overall_ok = False
        else:
            ok(f"{wf.name}: all referenced paths exist")
    return overall_ok


# ── Check 5: test imports vs devcontainer install ─────────


def check_test_imports_vs_install() -> bool:
    step("Test imports vs devcontainer install (every test dep must be in extras)")
    dc_path = REPO / ".devcontainer/devcontainer.json"
    if not dc_path.exists():
        warn("no .devcontainer/devcontainer.json — skipping")
        return True

    dc_text = dc_path.read_text()
    # Plain JSON; postCreateCommand is a string we parse for the `pip install -e .[a,b,c]` form.
    dc = json.loads(dc_text)
    cmd = dc.get("postCreateCommand", "")
    extras_match = re.search(r"pip install -e ['\"`]?\.\[([^\]]+)\]['\"`]?", cmd)
    if not extras_match:
        warn("can't parse extras from devcontainer postCreateCommand — skipping")
        print(f"{INDENT}    cmd: {cmd[:120]}")
        return True
    installed_extras = sorted({e.strip() for e in extras_match.group(1).split(",")})

    pyproj = tomllib.loads((REPO / "pyproject.toml").read_text())

    # Build the set of pip-package names that the devcontainer's install
    # actually pulls in: core deps + every dep of every installed extra.
    installed_pkgs: set[str] = set()

    def add_dep(spec: str) -> None:
        # Split on version specifier / environment marker
        bare = re.split(r"[><=;~!]| ", spec.strip(), 1)[0].strip()
        if bare:
            installed_pkgs.add(bare.lower().replace("-", "_"))

    for d in pyproj["project"].get("dependencies", []):
        add_dep(d)
    extras_table = pyproj["project"].get("optional-dependencies", {})
    for extra in installed_extras:
        if extra not in extras_table:
            warn(f"devcontainer requests extra [{extra}] but pyproject doesn't define it")
            continue
        for d in extras_table[extra]:
            add_dep(d)

    # Only audit files pytest actually collects: test_*.py and conftest.py.
    # Helper modules (corpus builders, fixture generators) live under tests/
    # but aren't imported at collection time; their deps gate themselves.
    tests_dir = REPO / "tests"
    test_files = sorted(
        f for f in tests_dir.rglob("*.py")
        if f.name.startswith("test_") or f.name == "conftest.py"
    )

    # Build the set of local helper modules so cross-test imports
    # (e.g. `import edge_case_builders` from a sibling) aren't flagged.
    local_modules = {f.stem for f in tests_dir.rglob("*.py") if f.stem != "__init__"}

    # Top-level imports only — `ast.walk` would surface function-scoped
    # imports gated behind try/except (e.g. `from PIL import Image` inside
    # a corpus builder), which don't break test collection.
    test_imports: set[str] = set()
    for tf in test_files:
        try:
            tree = ast.parse(tf.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for node in tree.body:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    test_imports.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module and node.level == 0:
                    test_imports.add(node.module.split(".")[0])

    # Filter out stdlib + the package itself + pytest internals + local helpers.
    stdlib = set(getattr(sys, "stdlib_module_names", set()))
    excluded = stdlib | {"uofa_cli", "_pytest"} | local_modules
    third_party = sorted(test_imports - excluded)

    missing: list[tuple[str, str]] = []
    for imp in third_party:
        pip_name = IMPORT_TO_PIP_NAME.get(imp, imp).lower().replace("-", "_")
        if pip_name not in installed_pkgs and imp.lower() not in installed_pkgs:
            missing.append((imp, pip_name))

    if missing:
        fail(f"{len(missing)} test import(s) not covered by [{','.join(installed_extras)}]:")
        for imp, pip in missing:
            # Suggest which extra would supply it
            suggested = []
            for extra, deps in extras_table.items():
                for d in deps:
                    bare = re.split(r"[><=;~!]| ", d.strip(), 1)[0].strip().lower().replace("-", "_")
                    if bare == pip:
                        suggested.append(extra)
            sug = f" — add to devcontainer extras (in [{','.join(suggested)}])" if suggested else ""
            print(f"{INDENT}    import {imp} (pip: {pip}){sug}")
        return False

    ok(f"all {len(third_party)} third-party test imports covered by [{','.join(installed_extras)}]")
    return True


# ── Check 6 (optional): full pytest ────────────────────────


def check_full_test_suite() -> bool:
    step("Full test suite (pytest tests/ -q)")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "-q",
         "--ignore=tests/test_extract_eval.py"],
        cwd=REPO,
    )
    if result.returncode != 0:
        fail(f"pytest exited with code {result.returncode}")
        return False
    ok("all tests passed")
    return True


# ── Driver ─────────────────────────────────────────────────


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--tag", help="Intended tag (e.g. v0.6.5) — checks pyproject version match")
    parser.add_argument("--full", action="store_true",
                        help="Also run the full pytest suite (~10-15 min)")
    args = parser.parse_args()

    print("Pre-tag release check for uofa-cli")
    if args.tag:
        print(f"Target tag: {args.tag}")
    print(f"Repo: {REPO}")

    checks: list[tuple[str, bool]] = [
        ("git state", check_git_state()),
        ("version match", check_version_match(args.tag)),
        ("python syntax compat", check_python_syntax_compat()),
        ("workflow paths", check_workflow_paths()),
        ("test imports vs install", check_test_imports_vs_install()),
    ]
    if args.full:
        checks.append(("full pytest", check_full_test_suite()))

    print("\n── Summary ─────")
    for name, passed in checks:
        marker = "✓" if passed else "✗"
        print(f"{INDENT}{marker} {name}")

    if all(p for _, p in checks):
        print(f"\n✓ All {len(checks)} checks passed.")
        if args.tag:
            print(f"\nNext: git tag -a {args.tag} -m '...' && git push origin {args.tag}")
        return 0
    failed = sum(1 for _, p in checks if not p)
    print(f"\n✗ {failed} of {len(checks)} checks FAILED — fix before tagging.")
    return 1


if __name__ == "__main__":
    sys.exit(main())

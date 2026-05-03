"""uofa demo — zero-setup conference-floor evaluation (REQ-DIST-008).

Loads a small bundled fixture (passage + pre-computed UofA JSON-LD) and
runs the full C1 + C2 + C3 pipeline against it. No `uofa setup` required,
no LLM runtime, no internet — just `pip install uofa && uofa demo` should
produce a complete demonstration in under 30 seconds on a baseline laptop.
"""

from __future__ import annotations

import argparse
import importlib.resources
import json
import shutil
import tempfile
from argparse import Namespace
from pathlib import Path

from uofa_cli import paths
from uofa_cli.commands import check
from uofa_cli.output import info, step_header

HELP = "run the C1+C2+C3 pipeline against a bundled fixture (no setup needed)"


def add_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--no-passage", action="store_true",
        help="skip printing the input passage (useful for piping)",
    )
    parser.add_argument(
        "--no-jsonld", action="store_true",
        help="skip printing the pre-computed JSON-LD",
    )


def run(args) -> int:
    fixture_dir = _bundled_demo_dir()
    if fixture_dir is None or not (fixture_dir / "manifest.json").is_file():
        info("Demo fixture missing — this UofA install is incomplete.")
        return 1

    manifest = json.loads((fixture_dir / "manifest.json").read_text())
    passage = (fixture_dir / manifest["passage_file"]).read_text()
    uofa_path = fixture_dir / manifest["uofa_file"]

    step_header(f"uofa demo — {manifest['title']}")
    info(manifest["description"])
    info("")
    info("What this will show:")
    for item in manifest.get("what_it_shows", []):
        info(f"  • {item}")
    info("")

    if not args.no_passage:
        _print_section("Input passage", passage.rstrip())

    if not args.no_jsonld:
        _print_section(
            "Pre-computed UofA JSON-LD (as if just extracted)",
            uofa_path.read_text().rstrip(),
        )

    info("")
    info("══════════════════════════════════════════════════════════════")
    info("Running C1 + C2 + C3 pipeline against the demo artifact...")
    info("══════════════════════════════════════════════════════════════")

    # Set the active pack (the demo fixture conforms to vv40 shapes).
    paths.set_active_pack(manifest.get("pack", "vv40"))

    # The fixture's @context is a relative path that points at the wheel's
    # `_data/repo/spec/context/...`. In source-tree dev that location does
    # not exist (it's a wheel-build artifact), so the SHACL parser fails
    # to load @context. Mirror the fixture + bundled context into a tmp
    # dir whose layout makes the relative @context resolve correctly.
    rc = _run_pipeline_in_tmp_layout(uofa_path)

    info("")
    info("══════════════════════════════════════════════════════════════")
    info("What to try next")
    info("══════════════════════════════════════════════════════════════")
    info("  Live extraction (one-time runtime install, ~5 GB):")
    info("    uofa setup")
    info("    uofa extract <your-pdf>")
    info("")
    info("  Hands-on authoring (no LLM):")
    info("    uofa init my-project")
    info("")
    info("  Browse the example packs:")
    info("    https://github.com/cloudronin/uofa/tree/main/packs")
    return rc


# ── Helpers ────────────────────────────────────────────────────


def _bundled_demo_dir() -> Path | None:
    pkg = importlib.resources.files("uofa_cli")
    candidate = Path(str(pkg)) / "_data" / "fixtures" / "demo"
    return candidate if candidate.is_dir() else None


def _run_pipeline_in_tmp_layout(uofa_path: Path) -> int:
    """Stage the demo fixture into a tmp dir whose layout matches the
    wheel-bundled @context relative path, then run check.run().

    Layout mirrors what `_data/` looks like in an installed wheel — i.e.,
    fixtures/demo/<file>.jsonld with engine assets at ../../repo/. The
    paths.py repo-root cache is temporarily redirected so check.run()'s
    internal lookups (shacl_schema, context_file, default_pubkey, etc.)
    all resolve under the staged tree.
    """
    repo_root = paths.find_repo_root()  # source tree OR bundled location
    with tempfile.TemporaryDirectory() as tmp:
        staged_data = Path(tmp) / "_data"
        staged_demo = staged_data / "fixtures" / "demo"
        staged_repo = staged_data / "repo"
        staged_demo.mkdir(parents=True)
        staged_repo.mkdir(parents=True)
        shutil.copy(uofa_path, staged_demo / uofa_path.name)
        for sub in ("spec", "packs", "keys"):
            src = repo_root / sub
            if src.exists():
                shutil.copytree(src, staged_repo / sub, symlinks=True)
        # In source-tree dev there is no wheel-bundled JAR, so the rules
        # step falls through to repo_root/src/weakener-engine/target/...; mirror
        # that into the staged tree too. (In a real installed wheel the
        # bundled JAR resolves directly and this branch is a no-op.)
        if paths.bundled_jar() is None:
            jar_src = repo_root / "src" / "weakener-engine" / "target" / "uofa-weakener-engine-0.1.0.jar"
            if jar_src.exists():
                jar_dst = staged_repo / "src" / "weakener-engine" / "target" / jar_src.name
                jar_dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(jar_src, jar_dst)

        check_args = Namespace(
            file=staged_demo / uofa_path.name,
            pubkey=None,    # paths.default_pubkey() resolves under staged_repo
            context=None,   # paths.context_file() resolves under staged_repo
            rules=None,
            skip_rules=False,
            build=False,
        )
        saved_cache = paths._repo_root_cache
        paths._repo_root_cache = staged_repo
        try:
            return check.run(check_args)
        finally:
            paths._repo_root_cache = saved_cache


def _print_section(title: str, body: str) -> None:
    info("")
    info(f"── {title} " + "─" * max(0, 60 - len(title)))
    info(body)
    info("─" * 64)

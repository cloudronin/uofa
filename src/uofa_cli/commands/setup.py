"""uofa setup — install / verify the LLM extract runtime (REQ-DIST-003+)."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from uofa_cli import setup_bundle, setup_install, setup_state, setup_uninstall, setup_verify
from uofa_cli.output import error, info, step_header

HELP = "install or verify the LLM extract runtime (Ollama + qwen3.5:4b)"

_DEFAULT_MODEL = "qwen3.5:4b"


def add_arguments(parser: argparse.ArgumentParser) -> None:
    # Top-level options that select install variants without requiring a
    # subcommand keyword. `--bundle <path>` and `--create-bundle <path>`
    # mirror the spec wording in REQ-DIST-004.
    parser.add_argument(
        "--bundle", type=Path, default=None,
        help="install from an offline bundle (REQ-DIST-004 air-gapped path)",
    )
    parser.add_argument(
        "--create-bundle", type=Path, default=None, dest="create_bundle",
        help="package the current install into a tar.gz for an offline machine",
    )
    parser.add_argument(
        "--model", default=_DEFAULT_MODEL,
        help=f"model tag to pull (default: {_DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--port", type=int, default=11434,
        help="port for the managed Ollama daemon (default: 11434)",
    )
    parser.add_argument(
        "--no-byo", action="store_true",
        help="skip BYO Ollama detection; install a UofA-managed copy",
    )
    parser.add_argument(
        "--yes", "-y", action="store_true",
        help="skip confirmation prompts (downloads, uninstall)",
    )
    parser.add_argument(
        "--no-verify", action="store_true",
        help="skip the post-install verify step",
    )

    sub = parser.add_subparsers(dest="setup_cmd", required=False)

    sub.add_parser(
        "verify",
        help="run a known extraction against a fixture and assert F1 >= 0.95",
    )

    sub.add_parser(
        "uninstall",
        help="remove the UofA-managed Ollama runtime + model (REQ-DIST-007)",
    )


def run(args: argparse.Namespace) -> int:
    cmd = getattr(args, "setup_cmd", None)
    if cmd == "verify":
        return _run_verify(args)
    if cmd == "uninstall":
        return _run_uninstall(args)

    # No subcommand: pick install path based on flags.
    if getattr(args, "create_bundle", None) is not None:
        return _run_create_bundle(args)
    if getattr(args, "bundle", None) is not None:
        return _run_install_from_bundle(args)
    return _run_install(args)


# ── install ────────────────────────────────────────────────────


def _run_install(args: argparse.Namespace) -> int:
    step_header("uofa setup — install LLM extract runtime")

    prefer_byo = not args.no_byo
    byo = setup_state.detect_byo_ollama() if prefer_byo else None

    _print_install_summary(byo, args.model, args.port)

    if not args.yes and not _confirm("Proceed with install? [y/N] "):
        info("Aborted.")
        return 1

    started = time.monotonic()
    progress_state = {"last_label": ""}

    def on_status(msg: str) -> None:
        info(msg)

    def on_progress(done: int, total: int) -> None:
        if not total:
            return
        pct = (done / total) * 100
        mb_done = done / (1024 * 1024)
        mb_total = total / (1024 * 1024)
        label = f"  {pct:5.1f}%  {mb_done:7.1f} / {mb_total:7.1f} MB"
        if label != progress_state["last_label"]:
            print(label, file=sys.stderr)
            progress_state["last_label"] = label

    try:
        cfg = setup_install.install(
            prefer_byo=prefer_byo,
            model_tag=args.model,
            port=args.port,
            on_status=on_status,
            on_progress=on_progress,
        )
    except Exception as e:
        error(f"Install failed: {e}")
        return 1

    elapsed = time.monotonic() - started
    _print_install_success(cfg, elapsed)

    if args.no_verify:
        return 0

    info("")
    info("Running verify to confirm install...")
    verify_result = setup_verify.verify(cfg, on_status=on_status)
    if not verify_result.ok:
        error(f"Verify failed: {verify_result.diagnostic}")
        info("Try `uofa setup verify` again, or `uofa setup` to repair.")
        return 1
    info(f"✓ {verify_result.diagnostic} (in {verify_result.elapsed_seconds:.1f}s)")
    return 0


def _run_verify(args: argparse.Namespace) -> int:
    step_header("uofa setup verify — end-to-end smoke test")
    cfg = setup_state.load_config()
    if cfg is None:
        error("No install detected. Run `uofa setup` first.")
        return 1
    info(f"Using {cfg.mode} Ollama at {cfg.ollama_binary} (port {cfg.ollama_port}).")
    result = setup_verify.verify(cfg, on_status=info)
    if result.ok:
        info(f"✓ {result.diagnostic} (in {result.elapsed_seconds:.1f}s)")
        info(f"  Try next: uofa extract <your-pdf>")
        return 0
    error(f"✗ {result.diagnostic} (after {result.elapsed_seconds:.1f}s)")
    return 1


# ── create-bundle / install-from-bundle (REQ-DIST-004) ─────────


def _run_create_bundle(args: argparse.Namespace) -> int:
    step_header("uofa setup --create-bundle — package install for offline transport")
    cfg = setup_state.load_config()
    if cfg is None:
        error("No install to bundle. Run `uofa setup` first.")
        return 1
    output = args.create_bundle
    if output.is_dir():
        output = output / setup_bundle.default_bundle_filename()
    info(f"  Bundle target: {output}")
    info(f"  Source binary: {cfg.ollama_binary}")
    info(f"  Source models: {cfg.ollama_models_dir or '~/.ollama/models'}")
    info(f"  Model:         {cfg.model_tag}")
    if not args.yes and not _confirm("Proceed with bundle creation? [y/N] "):
        info("Aborted.")
        return 1
    try:
        result_path = setup_bundle.create_bundle(
            output, cfg=cfg, model_tag=cfg.model_tag,
        )
    except FileNotFoundError as e:
        error(str(e))
        return 1
    size_mb = result_path.stat().st_size / (1024 * 1024)
    info(f"✓ Wrote {result_path} ({size_mb:.1f} MB)")
    info("Transfer this file to the air-gapped machine and run:")
    info(f"  uofa setup --bundle {result_path.name}")
    return 0


def _run_install_from_bundle(args: argparse.Namespace) -> int:
    step_header("uofa setup --bundle — install from offline bundle")
    bundle_path = args.bundle
    if not bundle_path.is_file():
        error(f"Bundle not found: {bundle_path}")
        return 1
    info(f"Reading {bundle_path}")
    try:
        cfg = setup_bundle.consume_bundle(bundle_path, on_status=info)
    except setup_bundle.PlatformMismatchError as e:
        error(str(e))
        return 1
    except (FileNotFoundError, ValueError) as e:
        error(f"Bundle install failed: {e}")
        return 1

    info("")
    info("Running verify against the unpacked install...")
    result = setup_verify.verify(cfg, on_status=info)
    if result.ok:
        info(f"✓ {result.diagnostic} (in {result.elapsed_seconds:.1f}s)")
        info(f"  Try next: uofa extract <your-pdf>")
        return 0
    error(f"✗ Verify failed: {result.diagnostic}")
    return 1


# ── uninstall (REQ-DIST-007) ───────────────────────────────────


def _run_uninstall(args: argparse.Namespace) -> int:
    step_header("uofa setup uninstall — remove managed runtime + model")
    cfg = setup_state.load_config()
    plan = setup_uninstall.plan_uninstall(cfg)
    if not plan.targets:
        info("Nothing to remove.")
        return 0

    info("Will remove:")
    for target in plan.targets:
        info(f"  {target}")
    info(f"Disk space to free: {plan.mb_to_free:.1f} MB")
    if cfg is not None and cfg.mode == "byo":
        info(f"Will NOT touch BYO Ollama at {cfg.ollama_binary}")

    if not args.yes and not _confirm("Proceed with uninstall? [y/N] "):
        info("Aborted.")
        return 1

    result = setup_uninstall.uninstall(cfg, on_status=info)
    info(f"✓ Removed {len(result.removed)} target(s); freed {result.bytes_freed / (1024*1024):.1f} MB")
    if result.skipped:
        for s in result.skipped:
            info(f"  (skipped {s})")
    return 0


# ── helpers ────────────────────────────────────────────────────


def _print_install_summary(byo: Path | None, model: str, port: int) -> None:
    info("")
    if byo is not None:
        info(f"Detected existing Ollama:  {byo}")
        info(f"  → will register and pull {model} into its model store")
        info("  → no UofA-managed binary will be downloaded")
        info("  → estimated additional disk: ~3 GB (model only)")
    else:
        platform_tag = setup_install.detect_wheel_platform_tag()
        try:
            entry = setup_install.resolve_platform_entry(platform_tag)
            url = entry.url
            ver = entry.version
            info(f"Will install Ollama {ver} for {platform_tag}")
            info(f"  Source:  {url}")
        except Exception:
            info(f"Will install Ollama for {platform_tag} (manifest lookup failed)")
        info(f"Model:                    {model}")
        info(f"Daemon port:              {port}")
        info(f"Install location:         {setup_state.uofa_data_dir()}")
        info("Estimated disk usage:     ~5 GB total (Ollama runtime + model)")


def _confirm(prompt: str) -> bool:
    try:
        answer = input(prompt).strip().lower()
    except (EOFError, KeyboardInterrupt):
        return False
    return answer in ("y", "yes")


def _print_install_success(cfg: setup_state.SetupConfig, elapsed: float) -> None:
    info("")
    info("══════════════════════════════════════════════════════")
    info("✓ uofa setup complete")
    info(f"   Mode:          {cfg.mode}")
    info(f"   Ollama:        {cfg.ollama_binary}")
    info(f"   Model:         {cfg.model_tag}")
    info(f"   Port:          {cfg.ollama_port}")
    info(f"   Config:        {setup_state.config_path()}")
    info(f"   Elapsed:       {elapsed:.1f}s")
    info("")
    info("Try next:")
    info("   uofa extract <your-pdf-or-directory>")
    info("══════════════════════════════════════════════════════")

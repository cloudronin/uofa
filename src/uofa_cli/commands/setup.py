"""uofa setup — install / verify the LLM extract runtime (REQ-DIST-003+)."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from uofa_cli import setup_install, setup_state, setup_verify
from uofa_cli.output import error, info, step_header

HELP = "install or verify the LLM extract runtime (Ollama + qwen3.5:4b)"

_DEFAULT_MODEL = "qwen3.5:4b"


def add_arguments(parser: argparse.ArgumentParser) -> None:
    sub = parser.add_subparsers(dest="setup_cmd", required=False)

    install_p = sub.add_parser(
        "install",
        help="download Ollama runtime + pull the qwen3.5:4b model (default)",
    )
    install_p.add_argument(
        "--model", default=_DEFAULT_MODEL,
        help=f"model tag to pull (default: {_DEFAULT_MODEL})",
    )
    install_p.add_argument(
        "--port", type=int, default=11434,
        help="port for the managed Ollama daemon (default: 11434)",
    )
    install_p.add_argument(
        "--no-byo", action="store_true",
        help="skip BYO Ollama detection; install a UofA-managed copy",
    )
    install_p.add_argument(
        "--yes", "-y", action="store_true",
        help="skip the pre-download confirmation prompt",
    )
    install_p.add_argument(
        "--no-verify", action="store_true",
        help="skip the post-install verify step",
    )

    sub.add_parser(
        "verify",
        help="run a known extraction against a fixture and assert F1 >= 0.95",
    )


def run(args: argparse.Namespace) -> int:
    cmd = getattr(args, "setup_cmd", None) or "install"
    if cmd == "install":
        return _run_install(args)
    if cmd == "verify":
        return _run_verify(args)
    error(f"Unknown setup subcommand: {cmd}")
    return 2


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

"""Implementation of `uofa setup uninstall` (REQ-DIST-007).

Removes the UofA-managed Ollama runtime + cached model store + config
file. Leaves bring-your-own-Ollama installs (REQ-DIST-005) untouched —
we own only the trees inside ``~/.uofa/runtime/`` and
``~/.uofa/cache/ollama_models/`` that we created at setup time.

A disk-space estimate is computed and reported up front; the caller is
expected to prompt for confirmation before invoking ``uninstall()``.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from uofa_cli import setup_state


@dataclass(frozen=True)
class UninstallPlan:
    """What `uninstall(plan)` will remove if it runs."""

    targets: list[Path]
    bytes_to_free: int

    @property
    def mb_to_free(self) -> float:
        return self.bytes_to_free / (1024 * 1024)


@dataclass(frozen=True)
class UninstallResult:
    removed: list[Path]
    skipped: list[Path]
    bytes_freed: int


def plan_uninstall(cfg: setup_state.SetupConfig | None = None) -> UninstallPlan:
    """Return what `uninstall()` would remove without touching disk."""
    cfg = cfg if cfg is not None else setup_state.load_config()

    targets: list[Path] = []

    # Always remove the runtime/cache trees we own.
    runtime_root = setup_state.runtime_dir()
    if runtime_root.exists():
        targets.append(runtime_root)

    models_dir = setup_state.models_cache_dir()
    if models_dir.exists():
        targets.append(models_dir)

    config_path = setup_state.config_path()
    if config_path.exists():
        targets.append(config_path)

    # Stale download cache from setup_install.
    downloads_dir = setup_state.uofa_data_dir() / "downloads"
    if downloads_dir.exists():
        targets.append(downloads_dir)

    bytes_to_free = sum(_size_on_disk(t) for t in targets)
    return UninstallPlan(targets=targets, bytes_to_free=bytes_to_free)


def uninstall(
    cfg: setup_state.SetupConfig | None = None,
    *,
    on_status=None,
) -> UninstallResult:
    """Remove the managed install. Does not touch BYO Ollama installs."""
    say = on_status or (lambda _: None)

    plan = plan_uninstall(cfg)
    cfg = cfg if cfg is not None else setup_state.load_config()

    # If the recorded binary is a BYO install (lives outside our managed
    # runtime tree), we must NOT touch it. plan_uninstall already excludes
    # everything outside ~/.uofa, but be defensive.
    skipped: list[Path] = []
    if cfg is not None and cfg.mode == "byo":
        managed_root = setup_state.uofa_data_dir().resolve()
        try:
            cfg.ollama_binary.resolve().relative_to(managed_root)
        except ValueError:
            skipped.append(cfg.ollama_binary)
            say(f"Skipping BYO Ollama at {cfg.ollama_binary} (not managed by UofA).")

    removed: list[Path] = []
    for target in plan.targets:
        if target.is_dir():
            shutil.rmtree(target)
        else:
            target.unlink()
        removed.append(target)
        say(f"removed {target}")

    return UninstallResult(
        removed=removed,
        skipped=skipped,
        bytes_freed=plan.bytes_to_free,
    )


def _size_on_disk(path: Path) -> int:
    if path.is_file():
        return path.stat().st_size
    total = 0
    for p in path.rglob("*"):
        if p.is_file():
            total += p.stat().st_size
    return total

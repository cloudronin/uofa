"""State + config helpers for `uofa setup` (REQ-DIST-002, REQ-DIST-005).

The setup command writes/reads ``~/.uofa/config.toml`` (or
``$XDG_DATA_HOME/uofa/config.toml`` on Linux when set) to remember which
Ollama runtime is active and where the model lives. ``uofa extract``
calls ``assert_ready()`` to fail fast with a helpful message if setup has
not been run.

Bring-your-own-Ollama detection (REQ-DIST-005) checks the standard install
paths before installing a managed copy.
"""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from pathlib import Path


_CONFIG_FILENAME = "config.toml"

# Standard Ollama install locations checked by detect_byo_ollama().
# Order matters — we prefer Homebrew on Apple Silicon (`/opt/homebrew`),
# then the generic `/usr/local/bin` install, then the per-user fallback.
_BYO_OLLAMA_PATHS = [
    Path("/opt/homebrew/bin/ollama"),
    Path("/usr/local/bin/ollama"),
    Path.home() / ".ollama" / "bin" / "ollama",
]


@dataclass(frozen=True)
class SetupConfig:
    """In-memory view of ~/.uofa/config.toml."""

    mode: str            # "managed" or "byo"
    ollama_binary: Path
    ollama_port: int
    ollama_models_dir: Path | None  # only set for managed mode
    model_tag: str
    installed_at: str
    uofa_version: str

    def is_managed(self) -> bool:
        return self.mode == "managed"


# ── Path helpers ──────────────────────────────────────────────


def uofa_data_dir() -> Path:
    """Return the UofA-managed config + runtime + cache root."""
    xdg = os.environ.get("XDG_DATA_HOME")
    if xdg:
        return Path(xdg) / "uofa"
    return Path.home() / ".uofa"


def config_path() -> Path:
    return uofa_data_dir() / _CONFIG_FILENAME


def runtime_dir(platform_tag: str | None = None) -> Path:
    """Return the directory where the managed Ollama binary lives."""
    base = uofa_data_dir() / "runtime"
    if platform_tag:
        return base / platform_tag
    return base


def models_cache_dir() -> Path:
    """Return the OLLAMA_MODELS path used by a UofA-managed daemon."""
    return uofa_data_dir() / "cache" / "ollama_models"


# ── Config I/O ────────────────────────────────────────────────


def _load_toml_module():
    try:
        import tomllib
    except ModuleNotFoundError:
        import tomli as tomllib  # type: ignore[no-redef]
    return tomllib


def load_config() -> SetupConfig | None:
    """Return the parsed config, or None if `uofa setup` has not been run."""
    path = config_path()
    if not path.is_file():
        return None
    tomllib = _load_toml_module()
    with path.open("rb") as f:
        raw = tomllib.load(f)

    runtime = raw.get("runtime", {})
    model = raw.get("model", {})
    meta = raw.get("meta", {})
    binary = runtime.get("ollama_binary")
    if not binary:
        return None

    models_dir = runtime.get("ollama_models_dir")
    return SetupConfig(
        mode=runtime.get("mode", "managed"),
        ollama_binary=Path(binary),
        ollama_port=int(runtime.get("ollama_port", 11434)),
        ollama_models_dir=Path(models_dir) if models_dir else None,
        model_tag=model.get("tag", "qwen3.5:4b"),
        installed_at=meta.get("installed_at", ""),
        uofa_version=meta.get("uofa_version", ""),
    )


def save_config(cfg: SetupConfig) -> None:
    """Atomically write SetupConfig to ~/.uofa/config.toml.

    Uses a hand-rolled TOML writer (small fixed schema, no dependency on
    tomli_w) so this works in environments that haven't installed the
    [extract] extra — which the test environment is one example of.
    """
    lines: list[str] = ["[runtime]"]
    lines.append(f"mode = {_toml_str(cfg.mode)}")
    lines.append(f"ollama_binary = {_toml_str(str(cfg.ollama_binary))}")
    lines.append(f"ollama_port = {int(cfg.ollama_port)}")
    if cfg.ollama_models_dir is not None:
        lines.append(f"ollama_models_dir = {_toml_str(str(cfg.ollama_models_dir))}")
    lines.append("")
    lines.append("[model]")
    lines.append(f"tag = {_toml_str(cfg.model_tag)}")
    lines.append("")
    lines.append("[meta]")
    lines.append(f"installed_at = {_toml_str(cfg.installed_at)}")
    lines.append(f"uofa_version = {_toml_str(cfg.uofa_version)}")
    text = "\n".join(lines) + "\n"

    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".toml.tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def _toml_str(value: str) -> str:
    """Encode *value* as a TOML basic string. Escapes the characters TOML
    requires inside a basic string: backslash, double quote, control chars."""
    escaped = (
        value.replace("\\", "\\\\")
             .replace('"', '\\"')
             .replace("\n", "\\n")
             .replace("\r", "\\r")
             .replace("\t", "\\t")
    )
    return f'"{escaped}"'


# ── Readiness check (called from extract_cmd) ─────────────────


def is_ready() -> bool:
    """True if `uofa setup` has been run and the recorded binary still exists."""
    cfg = load_config()
    return cfg is not None and cfg.ollama_binary.exists()


def assert_ready() -> SetupConfig:
    """Raise a helpful error if extract prerequisites are not installed.

    Called from the top of extract_cmd.run(); keeps the failure message
    consistent with the REQ-DIST-002 acceptance criterion: "extract
    without setup gives a clear, actionable message and non-zero exit."
    """
    cfg = load_config()
    if cfg is None:
        raise SetupNotReadyError(
            "Extract pipeline not configured. Run `uofa setup` first.\n"
            "  Quick install (connected):  uofa setup\n"
            "  Air-gapped install:          uofa setup --bundle <path>"
        )
    if not cfg.ollama_binary.exists():
        raise SetupNotReadyError(
            f"Configured Ollama binary missing: {cfg.ollama_binary}\n"
            "  Re-run `uofa setup` to repair, or `uofa setup verify` "
            "for diagnostics."
        )
    return cfg


class SetupNotReadyError(RuntimeError):
    """Raised by assert_ready() when the extract pipeline isn't installed."""


# ── BYO Ollama detection (REQ-DIST-005) ───────────────────────


def detect_byo_ollama() -> Path | None:
    """Return path to an existing Ollama binary outside UofA's runtime dir.

    Checks the standard install locations first, then ``shutil.which``.
    Skips anything inside UofA's own runtime tree so detection never
    flags our managed copy as "BYO".
    """
    managed_root = runtime_dir().resolve()

    for candidate in _BYO_OLLAMA_PATHS:
        if candidate.is_file() and _is_outside(candidate, managed_root):
            return candidate

    if os.name == "nt":
        local = os.environ.get("LOCALAPPDATA")
        if local:
            win_path = Path(local) / "Ollama" / "ollama.exe"
            if win_path.is_file() and _is_outside(win_path, managed_root):
                return win_path

    on_path = shutil.which("ollama")
    if on_path:
        p = Path(on_path)
        if _is_outside(p, managed_root):
            return p

    return None


def _is_outside(path: Path, managed_root: Path) -> bool:
    try:
        path.resolve().relative_to(managed_root)
    except ValueError:
        return True
    return False

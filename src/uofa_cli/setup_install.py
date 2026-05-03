"""Implementation of `uofa setup` (REQ-DIST-003).

Downloads the Ollama runtime binary into the UofA-managed directory,
launches a managed daemon, pulls the qwen3.5:4b model into the
UofA-owned model store, and pre-warms the model so the first
``uofa extract`` invocation does not pay cold-start latency.

Network downloads support HTTP Range resume (REQ-DIST-003 AC 3) and
verify SHA-256 against ``ollama_manifest.toml`` (AC 4). Progress is
reported at >= 2-second intervals (AC 6) via a callback so the CLI
layer can render a bar without this module knowing about TTYs.
"""

from __future__ import annotations

import hashlib
import os
import platform as _platform
import shutil
import subprocess
import sys
import tarfile
import time
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from uofa_cli import setup_state


_PROGRESS_INTERVAL_SEC = 2.0
_DEFAULT_PORT = 11434
_HEALTH_CHECK_TIMEOUT_SEC = 30.0
_DOWNLOAD_CHUNK_BYTES = 1 << 20  # 1 MiB

ProgressCallback = Callable[[int, int], None]  # (bytes_so_far, total_bytes)


@dataclass(frozen=True)
class OllamaPlatformEntry:
    """Resolved manifest entry for a single platform."""

    version: str
    url: str
    sha256: str
    archive_format: str  # "binary" | "tgz" | "tar.zst" | "zip"
    binary_inside_archive: str  # POSIX-style path to the executable


# ── Manifest ────────────────────────────────────────────────────


def detect_wheel_platform_tag() -> str:
    """Map the current host to a wheel-platform-tag used by ollama_manifest.

    Mirrors the keys we use in jre_manifest.toml so contributors don't
    have to remember two parallel naming conventions.
    """
    system = _platform.system().lower()
    machine = _platform.machine().lower()
    if system == "darwin":
        return "macosx_11_0_arm64" if machine in ("arm64", "aarch64") else "macosx_11_0_x86_64"
    if system == "linux":
        return "manylinux_2_28_aarch64" if machine in ("arm64", "aarch64") else "manylinux_2_28_x86_64"
    if system == "windows":
        return "win_amd64"
    raise RuntimeError(f"Unsupported platform: system={system}, machine={machine}")


def load_ollama_manifest(repo_root: Path | None = None) -> dict:
    """Load ollama_manifest.toml from the source tree."""
    try:
        import tomllib
    except ModuleNotFoundError:
        import tomli as tomllib  # type: ignore[no-redef]

    if repo_root is None:
        # Walk up from this module looking for the manifest.
        here = Path(__file__).resolve()
        for parent in [here.parent, *here.parents]:
            candidate = parent / "ollama_manifest.toml"
            if candidate.is_file():
                repo_root = parent
                break
        else:
            raise FileNotFoundError("ollama_manifest.toml not found")

    with (repo_root / "ollama_manifest.toml").open("rb") as f:
        return tomllib.load(f)


def resolve_platform_entry(platform_tag: str, manifest: dict | None = None) -> OllamaPlatformEntry:
    if manifest is None:
        manifest = load_ollama_manifest()
    platforms = manifest.get("platforms", {})
    entry = platforms.get(platform_tag)
    if entry is None:
        raise KeyError(
            f"Platform {platform_tag} not in ollama_manifest.toml; "
            f"known: {sorted(platforms)}"
        )
    return OllamaPlatformEntry(
        version=entry["version"],
        url=entry["url"],
        sha256=entry["sha256"],
        archive_format=entry["archive_format"],
        binary_inside_archive=entry.get("binary_inside_archive", "ollama"),
    )


# ── Download ────────────────────────────────────────────────────


def download_ollama(
    entry: OllamaPlatformEntry,
    dest: Path,
    on_progress: ProgressCallback | None = None,
) -> None:
    """Download the Ollama archive (or raw binary) to *dest*.

    Resumes on partial files via HTTP Range; verifies SHA-256 after.
    """
    import requests  # imported here so the module imports without [extract] installed

    dest.parent.mkdir(parents=True, exist_ok=True)
    existing = dest.stat().st_size if dest.exists() else 0

    # HEAD first to learn total size and whether Range is supported.
    head = requests.head(entry.url, allow_redirects=True, timeout=30)
    head.raise_for_status()
    total = int(head.headers.get("Content-Length", "0"))
    accept_ranges = head.headers.get("Accept-Ranges", "").lower() == "bytes"

    if existing == total and total > 0:
        # Already downloaded; just verify.
        _verify_sha256(dest, entry.sha256)
        if on_progress is not None:
            on_progress(total, total)
        return

    headers = {}
    mode = "wb"
    if existing and accept_ranges:
        headers["Range"] = f"bytes={existing}-"
        mode = "ab"
    else:
        existing = 0  # restart from scratch if server doesn't support resume

    with requests.get(entry.url, headers=headers, stream=True, timeout=120) as resp:
        resp.raise_for_status()
        with dest.open(mode) as f:
            bytes_so_far = existing
            last_emit = 0.0
            for chunk in resp.iter_content(chunk_size=_DOWNLOAD_CHUNK_BYTES):
                if not chunk:
                    continue
                f.write(chunk)
                bytes_so_far += len(chunk)
                now = time.monotonic()
                if on_progress is not None and (now - last_emit) >= _PROGRESS_INTERVAL_SEC:
                    on_progress(bytes_so_far, total)
                    last_emit = now
            if on_progress is not None:
                on_progress(bytes_so_far, total)

    _verify_sha256(dest, entry.sha256)


def _verify_sha256(path: Path, expected: str) -> None:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(_DOWNLOAD_CHUNK_BYTES), b""):
            h.update(chunk)
    actual = h.hexdigest()
    if actual != expected:
        raise ValueError(
            f"SHA-256 mismatch for {path}\n"
            f"  expected: {expected}\n"
            f"  actual:   {actual}"
        )


# ── Extraction ──────────────────────────────────────────────────


def install_binary(
    entry: OllamaPlatformEntry,
    archive: Path,
    install_dir: Path,
) -> Path:
    """Extract or move the downloaded artifact and return the binary path.

    Handles four archive formats: ``binary`` (raw executable), ``tgz``,
    ``tar.zst`` (system tar's --zstd), and ``zip``.
    """
    install_dir.mkdir(parents=True, exist_ok=True)
    if entry.archive_format == "binary":
        # Raw binary: just chmod and move into place.
        target = install_dir / entry.binary_inside_archive
        shutil.copy2(archive, target)
        target.chmod(0o755)
        return target

    if entry.archive_format == "tgz":
        with tarfile.open(archive, "r:gz") as tf:
            tf.extractall(install_dir)
    elif entry.archive_format == "tar.zst":
        # Python's stdlib tarfile gained zstd in 3.14; use system tar for
        # broader compatibility. Requires GNU tar 1.31+ or macOS tar 11+.
        subprocess.run(
            ["tar", "--zstd", "-xf", str(archive), "-C", str(install_dir)],
            check=True,
        )
    elif entry.archive_format == "zip":
        with zipfile.ZipFile(archive) as zf:
            zf.extractall(install_dir)
    else:
        raise ValueError(f"Unknown archive_format: {entry.archive_format}")

    binary_path = install_dir / entry.binary_inside_archive
    if not binary_path.exists():
        raise FileNotFoundError(
            f"Expected binary {entry.binary_inside_archive} not found "
            f"after extraction; install_dir contents: "
            f"{sorted(p.name for p in install_dir.rglob('*'))[:20]}"
        )
    binary_path.chmod(binary_path.stat().st_mode | 0o755)
    return binary_path


# ── Daemon lifecycle ────────────────────────────────────────────


def start_managed_daemon(
    binary: Path,
    port: int = _DEFAULT_PORT,
    models_dir: Path | None = None,
) -> subprocess.Popen:
    """Start `ollama serve` on the given port; return the Popen handle."""
    env = os.environ.copy()
    env["OLLAMA_HOST"] = f"127.0.0.1:{port}"
    if models_dir is not None:
        env["OLLAMA_MODELS"] = str(models_dir)
    return subprocess.Popen(
        [str(binary), "serve"],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )


def wait_for_daemon(port: int = _DEFAULT_PORT, timeout: float = _HEALTH_CHECK_TIMEOUT_SEC) -> None:
    """Poll /api/tags until the daemon answers or *timeout* elapses."""
    import requests

    deadline = time.monotonic() + timeout
    last_err: Exception | None = None
    while time.monotonic() < deadline:
        try:
            r = requests.get(f"http://127.0.0.1:{port}/api/tags", timeout=2)
            if r.status_code == 200:
                return
        except requests.RequestException as e:
            last_err = e
        time.sleep(0.25)
    raise TimeoutError(
        f"Ollama daemon did not respond on port {port} within {timeout}s "
        f"(last error: {last_err})"
    )


def pull_model(
    port: int,
    model_tag: str,
    on_progress: ProgressCallback | None = None,
) -> None:
    """Stream-pull a model via the Ollama HTTP API.

    Ollama returns one JSON object per line on /api/pull; each object
    has 'completed' / 'total' fields during the layer download phase.
    """
    import json
    import requests

    with requests.post(
        f"http://127.0.0.1:{port}/api/pull",
        json={"model": model_tag, "stream": True},
        stream=True,
        timeout=None,
    ) as resp:
        resp.raise_for_status()
        last_emit = 0.0
        for raw in resp.iter_lines():
            if not raw:
                continue
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if "error" in msg:
                raise RuntimeError(f"Ollama pull failed: {msg['error']}")
            completed = int(msg.get("completed", 0))
            total = int(msg.get("total", 0))
            now = time.monotonic()
            if on_progress is not None and total and (now - last_emit) >= _PROGRESS_INTERVAL_SEC:
                on_progress(completed, total)
                last_emit = now


def prewarm_model(port: int, model_tag: str) -> None:
    """Issue one tiny generation request so the next `uofa extract` is hot."""
    import requests

    requests.post(
        f"http://127.0.0.1:{port}/api/generate",
        json={"model": model_tag, "prompt": "ok", "options": {"num_predict": 1}, "stream": False},
        timeout=120,
    ).raise_for_status()


# ── Top-level orchestration ─────────────────────────────────────


def install(
    *,
    prefer_byo: bool = True,
    model_tag: str = "qwen3.5:4b",
    port: int = _DEFAULT_PORT,
    on_status: Callable[[str], None] | None = None,
    on_progress: ProgressCallback | None = None,
) -> setup_state.SetupConfig:
    """End-to-end install. Returns the resulting SetupConfig.

    If ``prefer_byo`` is True (REQ-DIST-005 default) and a system Ollama
    is detected, register it instead of installing a managed copy.
    """
    say = on_status or (lambda _: None)

    byo = setup_state.detect_byo_ollama() if prefer_byo else None
    if byo is not None:
        say(f"Detected existing Ollama at {byo}; registering it.")
        binary = byo
        models_dir: Path | None = None  # let Ollama use its default model store
        mode = "byo"
    else:
        platform_tag = detect_wheel_platform_tag()
        say(f"Installing managed Ollama for {platform_tag}.")
        entry = resolve_platform_entry(platform_tag)
        archive_dir = setup_state.uofa_data_dir() / "downloads"
        archive_dir.mkdir(parents=True, exist_ok=True)
        archive_path = archive_dir / Path(entry.url).name
        say(f"Downloading {entry.url}")
        download_ollama(entry, archive_path, on_progress=on_progress)
        say("Extracting binary.")
        binary = install_binary(entry, archive_path, setup_state.runtime_dir(platform_tag))
        models_dir = setup_state.models_cache_dir()
        models_dir.mkdir(parents=True, exist_ok=True)
        mode = "managed"

    say(f"Starting daemon on port {port}.")
    daemon = start_managed_daemon(binary, port=port, models_dir=models_dir)
    try:
        wait_for_daemon(port)
        say(f"Pulling model {model_tag} (this may take several minutes).")
        pull_model(port, model_tag, on_progress=on_progress)
        say("Pre-warming model.")
        prewarm_model(port, model_tag)
    finally:
        # Leave the daemon stopped after install — `uofa extract` will
        # start its own short-lived daemon on the same port.
        daemon.terminate()
        try:
            daemon.wait(timeout=5)
        except subprocess.TimeoutExpired:
            daemon.kill()

    cfg = setup_state.SetupConfig(
        mode=mode,
        ollama_binary=binary,
        ollama_port=port,
        ollama_models_dir=models_dir,
        model_tag=model_tag,
        installed_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        uofa_version=_uofa_version(),
    )
    setup_state.save_config(cfg)
    say(f"Wrote {setup_state.config_path()}")
    return cfg


def _uofa_version() -> str:
    try:
        from importlib.metadata import version
        return version("uofa")
    except Exception:
        return "unknown"

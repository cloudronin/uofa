"""Air-gapped install bundle (REQ-DIST-004).

* ``create_bundle(output)`` — packages the local Ollama binary + the
  qwen3.5:4b model store + license files + a manifest.json into a
  ``uofa-llm-bundle-<platform>-v<version>.tar.gz``.
* ``consume_bundle(path)`` — verifies platform + SHA-256s, then unpacks
  the bundle into ``~/.uofa/runtime/<platform>/`` and
  ``~/.uofa/cache/ollama_models/`` to produce the same end state as a
  connected ``uofa setup``.

Bundles are platform-specific. macOS/Linux/Windows binaries are not
interchangeable, so the bundle's filename embeds the platform tag and
``consume_bundle`` rejects bundles whose tag does not match the host.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import importlib.resources
import json
import os
import shutil
import tarfile
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from uofa_cli import setup_install, setup_state


_MANIFEST_NAME = "manifest.json"
_MANIFEST_SCHEMA = "1"
_DEFAULT_MODEL = "qwen3.5:4b"


@dataclass(frozen=True)
class BundleManifest:
    """Parsed view of manifest.json inside the tarball."""

    schema_version: str
    uofa_version: str
    platform: str
    created_at: str
    ollama_version: str
    model_tag: str
    files: dict[str, dict]  # path -> {"sha256": ..., "size": ...}


# ── Filename helpers ──────────────────────────────────────────


def default_bundle_filename(platform: str | None = None, uofa_version: str | None = None) -> str:
    platform = platform or setup_install.detect_wheel_platform_tag()
    uofa_version = uofa_version or _uofa_version()
    return f"uofa-llm-bundle-{platform}-v{uofa_version}.tar.gz"


def _uofa_version() -> str:
    try:
        from importlib.metadata import version
        return version("uofa-cli")
    except Exception:
        return "0.0.0"


# ── Bundle creation ───────────────────────────────────────────


def create_bundle(
    output_path: Path,
    *,
    platform: str | None = None,
    model_tag: str = _DEFAULT_MODEL,
    cfg: setup_state.SetupConfig | None = None,
) -> Path:
    """Build a self-contained install bundle at *output_path*.

    Reads the local Ollama install + model store described by *cfg*
    (defaults to the active ~/.uofa/config.toml). Writes a tar.gz that
    ``consume_bundle`` can unpack on a disconnected machine.
    """
    cfg = cfg or setup_state.assert_ready()
    platform = platform or setup_install.detect_wheel_platform_tag()
    binary = cfg.ollama_binary
    if not binary.exists():
        raise FileNotFoundError(f"Configured Ollama binary missing: {binary}")

    models_root = cfg.ollama_models_dir or _detect_byo_models_dir(binary)
    if models_root is None or not models_root.is_dir():
        raise FileNotFoundError(
            f"Could not locate Ollama model store; tried {models_root}. "
            "Ensure `ollama pull qwen3.5:4b` has been run."
        )

    model_files = _collect_model_files(models_root, model_tag)
    if not model_files:
        raise FileNotFoundError(
            f"Model {model_tag} not found in {models_root}; pull it first."
        )

    licenses = _bundled_license_files()

    files_in_bundle: list[tuple[Path, str]] = []
    files_in_bundle.append((binary, _bundle_arcname_for_binary(platform, binary)))
    for src, rel in model_files:
        files_in_bundle.append((src, f"models/{rel}"))
    for license_src in licenses:
        files_in_bundle.append((license_src, license_src.name))

    manifest = _build_manifest(files_in_bundle, platform, model_tag)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        manifest_path = Path(tmp) / _MANIFEST_NAME
        manifest_path.write_text(json.dumps(manifest.__dict__, indent=2, sort_keys=True))
        readme_path = Path(tmp) / "README.txt"
        readme_path.write_text(_render_bundle_readme(manifest))

        with tarfile.open(output_path, "w:gz") as tf:
            tf.add(manifest_path, arcname=_MANIFEST_NAME)
            tf.add(readme_path, arcname="README.txt")
            for src, arcname in files_in_bundle:
                tf.add(src, arcname=arcname)

    return output_path


# ── Bundle consumption ────────────────────────────────────────


def consume_bundle(
    bundle_path: Path,
    *,
    on_status=None,
) -> setup_state.SetupConfig:
    """Verify and unpack a bundle into the UofA-managed locations."""
    say = on_status or (lambda _: None)
    if not bundle_path.is_file():
        raise FileNotFoundError(bundle_path)

    host_platform = setup_install.detect_wheel_platform_tag()

    with tarfile.open(bundle_path, "r:gz") as tf:
        manifest = _read_manifest_from_tar(tf)
        if manifest.platform != host_platform:
            raise PlatformMismatchError(
                f"Bundle was built for {manifest.platform!r}, but this host "
                f"is {host_platform!r}. Build a matching bundle on a "
                f"{host_platform} machine."
            )

        say(f"Verifying bundle contents ({len(manifest.files)} files)...")
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            tf.extractall(tmp_path)
            _verify_extracted_files(tmp_path, manifest)

            runtime_dir = setup_state.runtime_dir(host_platform)
            models_dir = setup_state.models_cache_dir()
            runtime_dir.mkdir(parents=True, exist_ok=True)
            models_dir.mkdir(parents=True, exist_ok=True)

            binary_arcname = _binary_arcname_in_manifest(manifest)
            binary_src = tmp_path / binary_arcname
            binary_dst = runtime_dir / Path(binary_arcname).name
            say(f"Installing binary -> {binary_dst}")
            shutil.copy2(binary_src, binary_dst)
            binary_dst.chmod(binary_dst.stat().st_mode | 0o755)

            say(f"Restoring model store -> {models_dir}")
            for arcname in manifest.files:
                if not arcname.startswith("models/"):
                    continue
                src = tmp_path / arcname
                dst = models_dir / arcname[len("models/"):]
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)

    cfg = setup_state.SetupConfig(
        mode="managed",
        ollama_binary=binary_dst,
        ollama_port=11434,
        ollama_models_dir=models_dir,
        model_tag=manifest.model_tag,
        installed_at=_dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
        uofa_version=_uofa_version(),
    )
    setup_state.save_config(cfg)
    say(f"Wrote {setup_state.config_path()}")
    return cfg


class PlatformMismatchError(RuntimeError):
    """Raised when the bundle's platform tag does not match the host."""


# ── Internals ─────────────────────────────────────────────────


def _detect_byo_models_dir(binary: Path) -> Path | None:
    """For BYO mode, return the user's pre-existing ~/.ollama/models dir."""
    env_dir = os.environ.get("OLLAMA_MODELS")
    if env_dir:
        return Path(env_dir)
    return Path.home() / ".ollama" / "models"


def _collect_model_files(models_root: Path, model_tag: str) -> list[tuple[Path, str]]:
    """Return (absolute_src, models-relative-arcname) for the given tag.

    Walks Ollama's standard layout: a manifest JSON under
    ``manifests/registry.ollama.ai/library/<name>/<tag>`` plus referenced
    blobs under ``blobs/sha256-<digest>``.
    """
    name, _, tag = model_tag.partition(":")
    if not tag:
        tag = "latest"

    manifest_path = (
        models_root / "manifests" / "registry.ollama.ai" / "library" / name / tag
    )
    if not manifest_path.is_file():
        return []

    files: list[tuple[Path, str]] = [
        (manifest_path, manifest_path.relative_to(models_root).as_posix())
    ]

    manifest_data = json.loads(manifest_path.read_text())
    digests: list[str] = []
    if isinstance(manifest_data.get("config"), dict):
        digests.append(manifest_data["config"]["digest"])
    for layer in manifest_data.get("layers", []):
        digests.append(layer["digest"])

    blobs_dir = models_root / "blobs"
    for digest in digests:
        # Ollama stores blobs as 'sha256-<hex>' (dash-separated, not colon).
        normalized = digest.replace(":", "-")
        blob_path = blobs_dir / normalized
        if not blob_path.is_file():
            raise FileNotFoundError(
                f"Model layer missing: {blob_path} (referenced by {manifest_path})"
            )
        files.append((blob_path, blob_path.relative_to(models_root).as_posix()))

    return files


def _bundle_arcname_for_binary(platform: str, binary: Path) -> str:
    if platform.startswith("win_"):
        return "ollama.exe"
    return "ollama"


def _binary_arcname_in_manifest(manifest: BundleManifest) -> str:
    for arcname in manifest.files:
        if arcname in ("ollama", "ollama.exe"):
            return arcname
    raise ValueError("Bundle manifest does not list an ollama binary")


def _bundled_license_files() -> list[Path]:
    """Return paths to LICENSE-ollama.txt and LICENSE-qwen.txt under LICENSES/."""
    pkg_files = importlib.resources.files("uofa_cli")
    here = Path(str(pkg_files)).resolve()
    # LICENSES/ lives at the wheel's repo root, not inside the package, so
    # walk up looking for it.
    for parent in [here, *here.parents]:
        candidate = parent / "LICENSES"
        if candidate.is_dir():
            return [
                candidate / "LICENSE-ollama.txt",
                candidate / "LICENSE-qwen.txt",
            ]
    return []  # tolerated; manifest will simply not list licenses


def _build_manifest(
    files: Iterable[tuple[Path, str]],
    platform: str,
    model_tag: str,
) -> BundleManifest:
    file_index: dict[str, dict] = {}
    for src, arcname in files:
        file_index[arcname] = {
            "sha256": _sha256_of(src),
            "size": src.stat().st_size,
        }
    return BundleManifest(
        schema_version=_MANIFEST_SCHEMA,
        uofa_version=_uofa_version(),
        platform=platform,
        created_at=_dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
        ollama_version=_local_ollama_version(),
        model_tag=model_tag,
        files=file_index,
    )


def _local_ollama_version() -> str:
    """Best-effort lookup of the Ollama version recorded in the manifest."""
    try:
        manifest = setup_install.load_ollama_manifest()
        return manifest.get("meta", {}).get("ollama_version", "unknown")
    except Exception:
        return "unknown"


def _sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _read_manifest_from_tar(tf: tarfile.TarFile) -> BundleManifest:
    try:
        member = tf.getmember(_MANIFEST_NAME)
    except KeyError:
        raise ValueError(f"Bundle missing {_MANIFEST_NAME}")
    f = tf.extractfile(member)
    if f is None:
        raise ValueError(f"Bundle's {_MANIFEST_NAME} is unreadable")
    raw = json.loads(f.read())
    return BundleManifest(**raw)


def _verify_extracted_files(extract_root: Path, manifest: BundleManifest) -> None:
    for arcname, entry in manifest.files.items():
        path = extract_root / arcname
        if not path.is_file():
            raise FileNotFoundError(f"Bundle is missing declared file: {arcname}")
        actual = _sha256_of(path)
        if actual != entry["sha256"]:
            raise ValueError(
                f"SHA-256 mismatch in bundle for {arcname}\n"
                f"  expected: {entry['sha256']}\n"
                f"  actual:   {actual}"
            )


def _render_bundle_readme(manifest: BundleManifest) -> str:
    return (
        "UofA LLM Install Bundle\n"
        "=======================\n\n"
        f"  Created:      {manifest.created_at}\n"
        f"  Platform:     {manifest.platform}\n"
        f"  Model:        {manifest.model_tag}\n"
        f"  Ollama:       {manifest.ollama_version}\n"
        f"  UofA:         {manifest.uofa_version}\n\n"
        "Install on the target machine with:\n\n"
        "    uofa setup --bundle <this-file>.tar.gz\n\n"
        "Licenses for bundled software are included in this archive\n"
        "(LICENSE-ollama.txt, LICENSE-qwen.txt).\n"
    )

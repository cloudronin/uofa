"""Tests for setup_bundle — air-gap bundle round trip + platform mismatch (PR 5)."""

from __future__ import annotations

import hashlib
import json
import tarfile
from pathlib import Path

import pytest

from uofa_cli import setup_bundle, setup_state


@pytest.fixture(autouse=True)
def isolated_uofa_dir(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    yield tmp_path


def _seed_managed_install(tmp_path: Path, model_tag: str = "qwen3.5:4b") -> setup_state.SetupConfig:
    """Create a fake managed install (binary + Ollama-shaped model store)."""
    runtime = setup_state.runtime_dir("macosx_11_0_arm64")
    runtime.mkdir(parents=True)
    binary = runtime / "ollama"
    binary.write_text("#!/bin/sh\nexit 0\n")
    binary.chmod(0o755)

    models = setup_state.models_cache_dir()
    name, _, tag = model_tag.partition(":")
    manifest_dir = models / "manifests" / "registry.ollama.ai" / "library" / name
    manifest_dir.mkdir(parents=True)

    blob_dir = models / "blobs"
    blob_dir.mkdir(parents=True)
    blob_a = blob_dir / "sha256-aaa111"
    blob_a.write_bytes(b"layer-a-bytes")
    blob_b = blob_dir / "sha256-bbb222"
    blob_b.write_bytes(b"config-bytes")

    manifest_doc = {
        "config": {"digest": "sha256:bbb222"},
        "layers": [{"digest": "sha256:aaa111"}],
    }
    (manifest_dir / tag).write_text(json.dumps(manifest_doc))

    cfg = setup_state.SetupConfig(
        mode="managed",
        ollama_binary=binary,
        ollama_port=11434,
        ollama_models_dir=models,
        model_tag=model_tag,
        installed_at="2026-04-26T00:00:00+00:00",
        uofa_version="0.5.4",
    )
    setup_state.save_config(cfg)
    return cfg


# ── create + consume round trip ────────────────────────────────


def test_round_trip_install_and_consume(tmp_path, monkeypatch):
    """create_bundle on machine A → consume_bundle on (simulated) machine B."""
    cfg = _seed_managed_install(tmp_path)
    bundle_path = tmp_path / "bundle.tar.gz"
    monkeypatch.setattr(setup_bundle.setup_install, "detect_wheel_platform_tag",
                        lambda: "macosx_11_0_arm64")
    setup_bundle.create_bundle(bundle_path, cfg=cfg)
    assert bundle_path.is_file()

    # Inspect the bundle: manifest + binary + 2 blobs + 1 model manifest + 2 licenses
    with tarfile.open(bundle_path) as tf:
        names = set(tf.getnames())
    assert "manifest.json" in names
    assert "README.txt" in names
    assert "ollama" in names
    assert "models/manifests/registry.ollama.ai/library/qwen3.5/4b" in names
    assert "models/blobs/sha256-aaa111" in names
    assert "models/blobs/sha256-bbb222" in names

    # Wipe the simulated machine A state and consume the bundle as machine B.
    import shutil
    shutil.rmtree(setup_state.uofa_data_dir())

    new_cfg = setup_bundle.consume_bundle(bundle_path)
    assert new_cfg.mode == "managed"
    assert new_cfg.ollama_binary.exists()
    assert new_cfg.ollama_models_dir is not None
    assert (new_cfg.ollama_models_dir / "manifests/registry.ollama.ai/library/qwen3.5/4b").is_file()
    assert (new_cfg.ollama_models_dir / "blobs/sha256-aaa111").is_file()


def test_consume_bundle_rejects_wrong_platform(tmp_path, monkeypatch):
    cfg = _seed_managed_install(tmp_path)
    bundle_path = tmp_path / "bundle.tar.gz"
    monkeypatch.setattr(setup_bundle.setup_install, "detect_wheel_platform_tag",
                        lambda: "macosx_11_0_arm64")
    setup_bundle.create_bundle(bundle_path, cfg=cfg, platform="macosx_11_0_arm64")

    # "Move" the bundle to a different platform.
    monkeypatch.setattr(setup_bundle.setup_install, "detect_wheel_platform_tag",
                        lambda: "manylinux_2_28_x86_64")
    with pytest.raises(setup_bundle.PlatformMismatchError, match="macosx_11_0_arm64"):
        setup_bundle.consume_bundle(bundle_path)


def test_consume_bundle_detects_tampering(tmp_path, monkeypatch):
    cfg = _seed_managed_install(tmp_path)
    bundle_path = tmp_path / "bundle.tar.gz"
    monkeypatch.setattr(setup_bundle.setup_install, "detect_wheel_platform_tag",
                        lambda: "macosx_11_0_arm64")
    setup_bundle.create_bundle(bundle_path, cfg=cfg)

    # Re-pack the tarball with a flipped byte in the binary; the manifest's
    # SHA-256 should now mismatch.
    import shutil
    work = tmp_path / "tamper"
    work.mkdir()
    with tarfile.open(bundle_path) as tf:
        tf.extractall(work)
    binary = work / "ollama"
    binary.write_bytes(b"#!/bin/sh\nexit 1\n")
    bad_path = tmp_path / "bad.tar.gz"
    with tarfile.open(bad_path, "w:gz") as tf:
        for item in work.rglob("*"):
            if item.is_file():
                tf.add(item, arcname=item.relative_to(work).as_posix())
    shutil.rmtree(setup_state.uofa_data_dir())

    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        setup_bundle.consume_bundle(bad_path)


def test_default_bundle_filename_includes_platform_and_version(monkeypatch):
    monkeypatch.setattr(setup_bundle.setup_install, "detect_wheel_platform_tag",
                        lambda: "win_amd64")
    name = setup_bundle.default_bundle_filename(uofa_version="0.5.4")
    assert name == "uofa-llm-bundle-win_amd64-v0.5.4.tar.gz"

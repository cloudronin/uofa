"""Tests for setup_uninstall — clean removal + BYO preservation (PR 5)."""

from __future__ import annotations

from pathlib import Path

import pytest

from uofa_cli import setup_state, setup_uninstall


@pytest.fixture(autouse=True)
def isolated_uofa_dir(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    yield tmp_path


def _seed(tmp_path: Path, *, mode: str = "managed", external_byo: Path | None = None):
    runtime = setup_state.runtime_dir("macosx_11_0_arm64")
    runtime.mkdir(parents=True)
    binary = external_byo if external_byo is not None else (runtime / "ollama")
    if external_byo is None:
        binary.write_text("#!/bin/sh\n")
        binary.chmod(0o755)
    models = setup_state.models_cache_dir()
    models.mkdir(parents=True)
    (models / "blobs").mkdir()
    (models / "blobs" / "sha256-aaa").write_bytes(b"x" * 1024)
    cfg = setup_state.SetupConfig(
        mode=mode,
        ollama_binary=binary,
        ollama_port=11434,
        ollama_models_dir=models if mode == "managed" else None,
        model_tag="qwen3.5:4b",
        installed_at="2026-04-26T00:00:00+00:00",
        uofa_version="0.5.4",
    )
    setup_state.save_config(cfg)
    return cfg


def test_plan_uninstall_lists_managed_targets():
    plan = setup_uninstall.plan_uninstall(None)
    # No install present → nothing to remove.
    assert plan.targets == []
    assert plan.bytes_to_free == 0


def test_uninstall_removes_managed_install(tmp_path):
    _seed(tmp_path, mode="managed")
    plan = setup_uninstall.plan_uninstall()
    assert plan.bytes_to_free > 0
    assert any("runtime" in str(t) for t in plan.targets)
    assert any("ollama_models" in str(t) for t in plan.targets)
    assert any("config.toml" in str(t) for t in plan.targets)

    result = setup_uninstall.uninstall()
    assert result.bytes_freed > 0
    assert not setup_state.config_path().exists()
    assert not setup_state.models_cache_dir().exists()


def test_uninstall_does_not_touch_byo_binary(tmp_path):
    # BYO binary lives outside ~/.uofa entirely.
    external = tmp_path.parent / "fake-homebrew-bin" / "ollama"
    external.parent.mkdir(parents=True, exist_ok=True)
    external.write_text("#!/bin/sh\n")
    external.chmod(0o755)
    cfg = _seed(tmp_path, mode="byo", external_byo=external)

    result = setup_uninstall.uninstall(cfg)
    # Config + downloads + runtime cleared, but BYO binary untouched.
    assert external.exists(), "BYO Ollama binary must not be removed"
    assert external in result.skipped or any(
        s == external for s in result.skipped
    )
    assert not setup_state.config_path().exists()


def test_uninstall_after_setup_makes_extract_print_setup_message(tmp_path):
    """REQ-DIST-007 AC 3: extract reverts to the same 'run uofa setup' error."""
    _seed(tmp_path, mode="managed")
    setup_uninstall.uninstall()
    with pytest.raises(setup_state.SetupNotReadyError, match="uofa setup"):
        setup_state.assert_ready()

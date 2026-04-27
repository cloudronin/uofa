"""Tests for setup_state — config I/O, BYO detection, assert_ready (PR 4)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from uofa_cli import setup_state


@pytest.fixture(autouse=True)
def isolated_uofa_dir(monkeypatch, tmp_path):
    """Force ~/.uofa lookups to a tmp dir for every test in this module."""
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    yield tmp_path


# ── data_dir / config_path ─────────────────────────────────────


def test_uofa_data_dir_uses_xdg_when_set(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    assert setup_state.uofa_data_dir() == tmp_path / "uofa"


def test_uofa_data_dir_falls_back_to_home(monkeypatch, tmp_path):
    monkeypatch.delenv("XDG_DATA_HOME", raising=False)
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    assert setup_state.uofa_data_dir() == tmp_path / ".uofa"


# ── load / save / assert_ready ─────────────────────────────────


def _sample_cfg(tmp_path: Path, *, binary_exists: bool = True) -> setup_state.SetupConfig:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    binary = bin_dir / "ollama"
    if binary_exists:
        binary.write_text("#!/bin/sh\n")
        binary.chmod(0o755)
    return setup_state.SetupConfig(
        mode="managed",
        ollama_binary=binary,
        ollama_port=11434,
        ollama_models_dir=tmp_path / "models",
        model_tag="qwen3.5:4b",
        installed_at="2026-04-26T00:00:00+00:00",
        uofa_version="0.5.3",
    )


def test_load_config_returns_none_when_missing():
    assert setup_state.load_config() is None


def test_save_then_load_roundtrip(tmp_path):
    cfg = _sample_cfg(tmp_path)
    setup_state.save_config(cfg)
    loaded = setup_state.load_config()
    assert loaded == cfg


def test_save_config_omits_models_dir_when_none(tmp_path):
    cfg = setup_state.SetupConfig(
        mode="byo",
        ollama_binary=tmp_path / "bin" / "ollama",
        ollama_port=11434,
        ollama_models_dir=None,  # BYO mode doesn't manage a models dir
        model_tag="qwen3.5:4b",
        installed_at="2026-04-26T00:00:00+00:00",
        uofa_version="0.5.3",
    )
    (tmp_path / "bin").mkdir()
    cfg.ollama_binary.write_text("#!/bin/sh\n")
    cfg.ollama_binary.chmod(0o755)

    setup_state.save_config(cfg)
    loaded = setup_state.load_config()
    assert loaded.ollama_models_dir is None


def test_is_ready_true_when_binary_exists(tmp_path):
    setup_state.save_config(_sample_cfg(tmp_path))
    assert setup_state.is_ready() is True


def test_is_ready_false_when_binary_missing(tmp_path):
    setup_state.save_config(_sample_cfg(tmp_path, binary_exists=False))
    assert setup_state.is_ready() is False


def test_assert_ready_raises_when_no_config():
    with pytest.raises(setup_state.SetupNotReadyError, match="uofa setup"):
        setup_state.assert_ready()


def test_assert_ready_raises_when_binary_missing(tmp_path):
    setup_state.save_config(_sample_cfg(tmp_path, binary_exists=False))
    with pytest.raises(setup_state.SetupNotReadyError, match="missing"):
        setup_state.assert_ready()


def test_assert_ready_returns_config_on_success(tmp_path):
    cfg = _sample_cfg(tmp_path)
    setup_state.save_config(cfg)
    result = setup_state.assert_ready()
    assert result == cfg


# ── BYO Ollama detection ───────────────────────────────────────


def test_detect_byo_returns_none_when_nothing_found(monkeypatch):
    monkeypatch.setattr(setup_state, "_BYO_OLLAMA_PATHS", [])
    monkeypatch.setattr(setup_state.shutil, "which", lambda _: None)
    assert setup_state.detect_byo_ollama() is None


def test_detect_byo_finds_path_in_BYO_list(monkeypatch, tmp_path):
    fake = tmp_path / "homebrew" / "bin" / "ollama"
    fake.parent.mkdir(parents=True)
    fake.write_text("#!/bin/sh\n")
    fake.chmod(0o755)
    monkeypatch.setattr(setup_state, "_BYO_OLLAMA_PATHS", [fake])
    monkeypatch.setattr(setup_state.shutil, "which", lambda _: None)
    assert setup_state.detect_byo_ollama() == fake


def test_detect_byo_falls_back_to_shutil_which(monkeypatch, tmp_path):
    fake = tmp_path / "elsewhere" / "ollama"
    fake.parent.mkdir(parents=True)
    fake.write_text("#!/bin/sh\n")
    fake.chmod(0o755)
    monkeypatch.setattr(setup_state, "_BYO_OLLAMA_PATHS", [])
    monkeypatch.setattr(setup_state.shutil, "which", lambda name: str(fake) if name == "ollama" else None)
    assert setup_state.detect_byo_ollama() == fake


def test_detect_byo_skips_uofa_managed_install(monkeypatch, tmp_path):
    # A managed binary inside ~/.uofa/runtime/ should NOT be reported as BYO.
    managed_dir = tmp_path / ".uofa" / "runtime" / "macosx_11_0_arm64"
    managed_dir.mkdir(parents=True)
    managed_binary = managed_dir / "ollama"
    managed_binary.write_text("#!/bin/sh\n")
    managed_binary.chmod(0o755)
    monkeypatch.delenv("XDG_DATA_HOME", raising=False)
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.setattr(setup_state, "_BYO_OLLAMA_PATHS", [managed_binary])
    monkeypatch.setattr(setup_state.shutil, "which", lambda _: None)
    assert setup_state.detect_byo_ollama() is None

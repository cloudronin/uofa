"""Tests for setup_verify — diagnostic surface area (PR 4).

Daemon + LLM are mocked so the test suite never depends on a real Ollama.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from uofa_cli import setup_state, setup_verify


def _stub_cfg(tmp_path: Path) -> setup_state.SetupConfig:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    binary = bin_dir / "ollama"
    binary.write_text("#!/bin/sh\nexit 0\n")
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


def test_verify_returns_no_config_message_when_no_setup():
    result = setup_verify.verify(cfg=None)
    assert result.ok is False
    assert "uofa setup" in result.diagnostic


def test_verify_reports_daemon_timeout(tmp_path, monkeypatch):
    cfg = _stub_cfg(tmp_path)
    # Daemon "starts" but health check times out.
    monkeypatch.setattr(setup_verify.setup_install, "start_managed_daemon",
                        lambda *a, **kw: _FakePopen())
    monkeypatch.setattr(setup_verify.setup_install, "wait_for_daemon",
                        _raise_timeout)

    result = setup_verify.verify(cfg=cfg)
    assert result.ok is False
    assert "model load timed out" in result.diagnostic


def test_verify_reports_extraction_failure(tmp_path, monkeypatch):
    cfg = _stub_cfg(tmp_path)
    monkeypatch.setattr(setup_verify.setup_install, "start_managed_daemon",
                        lambda *a, **kw: _FakePopen())
    monkeypatch.setattr(setup_verify.setup_install, "wait_for_daemon",
                        lambda *a, **kw: None)
    monkeypatch.setattr(setup_verify, "_run_extraction",
                        lambda cfg, p: (_ for _ in ()).throw(RuntimeError("daemon went away")))

    result = setup_verify.verify(cfg=cfg)
    assert result.ok is False
    assert "extraction failed" in result.diagnostic


def test_verify_reports_low_f1(tmp_path, monkeypatch):
    cfg = _stub_cfg(tmp_path)
    monkeypatch.setattr(setup_verify.setup_install, "start_managed_daemon",
                        lambda *a, **kw: _FakePopen())
    monkeypatch.setattr(setup_verify.setup_install, "wait_for_daemon",
                        lambda *a, **kw: None)
    # Return an extraction with no factors → low F1 against the 6-factor fixture.
    monkeypatch.setattr(setup_verify, "_run_extraction",
                        lambda cfg, p: {"credibility_factors": []})

    result = setup_verify.verify(cfg=cfg)
    assert result.ok is False
    assert result.f1 is not None
    assert "F1 below threshold" in result.diagnostic


# ── helpers ────────────────────────────────────────────────────


class _FakePopen:
    """Minimal Popen stand-in for daemon teardown in the finally block."""

    def terminate(self):
        pass

    def wait(self, timeout=None):
        return 0

    def kill(self):
        pass


def _raise_timeout(*a, **kw):
    raise TimeoutError("daemon never answered")

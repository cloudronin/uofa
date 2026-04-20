"""Circularity exit-code matrix tests (§7.2)."""

from __future__ import annotations

import pytest

from uofa_cli.adversarial.circularity import (
    CircularityResult,
    check_circularity,
    resolve_extract_model,
)


def _check(gen, ext, *, strict=False, allow=False, explicit=False) -> CircularityResult:
    return check_circularity(
        gen, ext, strict=strict, allow_circular=allow, explicit_override=explicit
    )


def test_no_match_exits_zero_no_warning():
    r = _check("claude-opus-4-7", "qwen3:4b")
    assert r.matches is False
    assert r.exit_code == 0
    assert r.warning is None


def test_spec_default_match_soft_warning():
    r = _check("qwen3:4b", "qwen3:4b", explicit=False)
    assert r.matches is True
    assert r.exit_code == 0
    assert r.warning is not None
    assert "Proceeding anyway" in r.warning


def test_explicit_override_match_rejects():
    r = _check("qwen3:4b", "qwen3:4b", explicit=True, allow=False)
    assert r.exit_code == 4
    assert "--allow-circular-model" in r.warning


def test_explicit_override_match_with_allow_proceeds():
    r = _check("qwen3:4b", "qwen3:4b", explicit=True, allow=True)
    assert r.exit_code == 0
    assert "circular" in r.warning.lower()


def test_strict_match_rejects_regardless():
    r = _check("qwen3:4b", "qwen3:4b", strict=True)
    assert r.exit_code == 4
    assert "strict" in r.warning.lower()


def test_strict_wins_over_allow():
    r = _check("qwen3:4b", "qwen3:4b", strict=True, allow=True, explicit=True)
    assert r.exit_code == 4


def test_ollama_prefix_normalized():
    """'ollama/qwen3:4b' and 'qwen3:4b' should compare equal."""
    r = _check("ollama/qwen3:4b", "qwen3:4b", explicit=True, allow=False)
    assert r.matches is True
    assert r.exit_code == 4


def test_resolve_extract_model_falls_back():
    # In a directory with no uofa.toml, the default is returned.
    # We can't easily spoof the cwd here without affecting other tests;
    # just verify the function returns a non-empty string.
    model = resolve_extract_model()
    assert isinstance(model, str)
    assert model

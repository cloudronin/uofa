"""Where the Space gets its model from, and when it declines to guess.

Hermetic: every case is monkeypatched env, no network. The point of the module
is that a misconfigured deployment falls back to the local path instead of
failing in a new way, so most of these assert on None.
"""

from __future__ import annotations

import pytest

from space import llm_env

TOGETHER = {
    llm_env.BACKEND_ENV: "openai-compatible",
    llm_env.MODEL_ENV: "meta-llama/Llama-3.3-70B-Instruct-Turbo",
    llm_env.BASE_URL_ENV: "https://api.together.xyz/v1",
    llm_env.KEY_ENV_ENV: "TOGETHER_API_KEY",
}


@pytest.fixture
def env(monkeypatch):
    def apply(mapping, key=None):
        for k, v in mapping.items():
            monkeypatch.setenv(k, v)
        if key is not None:
            monkeypatch.setenv("TOGETHER_API_KEY", key)
        else:
            monkeypatch.delenv("TOGETHER_API_KEY", raising=False)
    return apply


# ── the four resolution cases ────────────────────────────────────


def test_unconfigured_returns_none(monkeypatch):
    """A local run, and every test: behave exactly as before hosted inference."""
    monkeypatch.delenv(llm_env.BACKEND_ENV, raising=False)
    assert llm_env.space_llm_config() is None


def test_configured_with_key_returns_a_config(env):
    env(TOGETHER, key="tgp_x")
    cfg = llm_env.space_llm_config()
    assert cfg is not None
    assert cfg.backend == "openai-compatible"
    assert cfg.model == TOGETHER[llm_env.MODEL_ENV]
    assert cfg.base_url == "https://api.together.xyz/v1"
    assert cfg.api_key_env == "TOGETHER_API_KEY"


def test_configured_without_key_returns_none(env):
    """The duplicated-Space case: HF copies the declaration, not the secret."""
    env(TOGETHER, key=None)
    assert llm_env.space_llm_config() is None


def test_mock_beats_every_other_setting(env, monkeypatch):
    """Non-negotiable. llm_extractor._call_llm short-circuits on
    `model == "mock" and llm_config is None`, so returning a config here would
    defeat the mock and send the literal string "mock" to a paid endpoint."""
    env(TOGETHER, key="tgp_x")
    monkeypatch.setenv("UOFA_SPACE_MODEL", "mock")
    assert llm_env.space_llm_config() is None


# ── the missing-secret signal ────────────────────────────────────


def test_missing_key_env_names_the_secret(env):
    env(TOGETHER, key=None)
    assert llm_env.missing_key_env() == "TOGETHER_API_KEY"


def test_missing_key_env_is_silent_for_a_local_deployment(monkeypatch):
    """A developer running Ollama also gets None from space_llm_config(), and
    must not be told a secret is missing. Only a declared remote backend can be."""
    monkeypatch.delenv(llm_env.BACKEND_ENV, raising=False)
    assert llm_env.missing_key_env() is None


def test_missing_key_env_is_silent_for_a_local_backend(monkeypatch):
    monkeypatch.setenv(llm_env.BACKEND_ENV, "ollama")
    monkeypatch.setenv(llm_env.MODEL_ENV, "qwen3.5:4b")
    assert llm_env.missing_key_env() is None


def test_present_key_means_nothing_missing(env):
    env(TOGETHER, key="tgp_x")
    assert llm_env.missing_key_env() is None


# ── robustness ───────────────────────────────────────────────────


def test_blank_values_count_as_unset(monkeypatch):
    """HF settings hand back empty strings for cleared variables."""
    monkeypatch.setenv(llm_env.BACKEND_ENV, "   ")
    assert llm_env.space_llm_config() is None


def test_bad_config_falls_back_instead_of_raising(env, monkeypatch, capsys):
    """openai-compatible without base_url is a ConfigError. The Space must
    degrade to local and say why, not take the deployment down."""
    env(TOGETHER, key="tgp_x")
    monkeypatch.delenv(llm_env.BASE_URL_ENV, raising=False)
    assert llm_env.space_llm_config() is None
    assert "ignoring hosted-inference config" in capsys.readouterr().err


def test_unknown_backend_falls_back(env, monkeypatch):
    env(TOGETHER, key="tgp_x")
    monkeypatch.setenv(llm_env.BACKEND_ENV, "not-a-backend")
    assert llm_env.space_llm_config() is None


# ── disclosure helpers ───────────────────────────────────────────


def test_is_remote_drives_the_disclosure(env):
    env(TOGETHER, key="tgp_x")
    assert llm_env.is_remote(llm_env.space_llm_config()) is True
    assert llm_env.is_remote(None) is False


def test_provider_label_names_the_host_not_the_protocol(env):
    """'openai-compatible' is accurate and tells a reader nothing about where
    their documents went."""
    env(TOGETHER, key="tgp_x")
    label = llm_env.provider_label(llm_env.space_llm_config())
    assert "api.together.xyz" in label
    assert "openai-compatible" not in label


def test_provider_label_for_local_says_local():
    assert "this Space" in llm_env.provider_label(None)

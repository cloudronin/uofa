"""Tests for uofa_cli.llm.config + get_backend factory (spec v0.4 §3.6, §6.4)."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest

from uofa_cli.llm import (
    BUNDLED_MODEL,
    ConfigError,
    LiteLLMBackend,
    LLMConfig,
    MockBackend,
    REMOTE_BACKENDS,
    get_backend,
    resolve_api_key,
    resolve_llm_config,
)


# ── Fixtures ────────────────────────────────────────────────


@pytest.fixture
def hermetic_env(monkeypatch, tmp_path):
    """Force-isolate from the user's real ~/.uofa and project lookup.

    All tests get a `tmp_path` scratch dir. Project root and user config
    paths are passed explicitly so nothing escapes to the host filesystem.
    Also clears env vars commonly used for API keys so leakage tests are
    deterministic.
    """
    for key in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "TOGETHER_API_KEY"):
        monkeypatch.delenv(key, raising=False)
    return tmp_path


def _write_toml(path: Path, body: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dedent(body).lstrip(), encoding="utf-8")
    return path


# ── Bundled fallback (no config anywhere) ───────────────────


def test_bundled_fallback_when_nothing_configured(hermetic_env, monkeypatch):
    """No CLI, no project, no user, no setup_state → returns bundled defaults."""
    # Force setup_state to report "not installed"
    monkeypatch.setattr("uofa_cli.setup_state.load_config", lambda: None)
    config = resolve_llm_config(
        project_root=hermetic_env,
        user_config_path=hermetic_env / "no-such-file.toml",
    )
    assert config.backend == "ollama"  # bundled is expanded
    assert config.model == BUNDLED_MODEL
    assert config.provenance.get("backend") == "bundled"


def test_bundled_uses_setup_state_model_when_present(hermetic_env, monkeypatch):
    """If `uofa setup` ran with a non-default model, bundled inherits it."""
    class _FakeSetup:
        model_tag = "llama3.3:70b"
    monkeypatch.setattr("uofa_cli.setup_state.load_config", lambda: _FakeSetup())
    config = resolve_llm_config(
        project_root=hermetic_env,
        user_config_path=hermetic_env / "no-such-file.toml",
    )
    assert config.model == "llama3.3:70b"


# ── Precedence ──────────────────────────────────────────────


def test_cli_beats_project(hermetic_env, monkeypatch):
    monkeypatch.setattr("uofa_cli.setup_state.load_config", lambda: None)
    _write_toml(hermetic_env / "uofa.toml", """
        [llm]
        backend = "ollama"
        model = "qwen3.5:4b"
    """)
    config = resolve_llm_config(
        cli_overrides={"backend": "anthropic", "model": "claude-sonnet-5-2026", "api_key_env": "ANTHROPIC_API_KEY"},
        project_root=hermetic_env,
        user_config_path=hermetic_env / "no-such-file.toml",
    )
    assert config.backend == "anthropic"
    assert config.model == "claude-sonnet-5-2026"
    assert config.provenance["backend"] == "cli"


def test_project_beats_user(hermetic_env, monkeypatch):
    monkeypatch.setattr("uofa_cli.setup_state.load_config", lambda: None)
    _write_toml(hermetic_env / "uofa.toml", """
        [llm]
        backend = "anthropic"
        model = "claude-from-project"
        api_key_env = "ANTHROPIC_API_KEY"
    """)
    user_path = _write_toml(hermetic_env / "user-config.toml", """
        [llm]
        backend = "openai"
        model = "gpt-from-user"
        api_key_env = "OPENAI_API_KEY"
    """)
    config = resolve_llm_config(
        project_root=hermetic_env,
        user_config_path=user_path,
    )
    assert config.backend == "anthropic"
    assert config.model == "claude-from-project"
    assert config.provenance["backend"] == "project"


def test_user_beats_bundled(hermetic_env, monkeypatch):
    monkeypatch.setattr("uofa_cli.setup_state.load_config", lambda: None)
    user_path = _write_toml(hermetic_env / "user-config.toml", """
        [llm]
        backend = "anthropic"
        model = "claude-sonnet-5-2026"
        api_key_env = "ANTHROPIC_API_KEY"
    """)
    config = resolve_llm_config(
        project_root=hermetic_env,  # no uofa.toml here
        user_config_path=user_path,
    )
    assert config.backend == "anthropic"
    assert config.provenance["backend"] == "user"


def test_per_field_fallthrough(hermetic_env, monkeypatch):
    """CLI overrides only `backend`; `model` falls through to project."""
    monkeypatch.setattr("uofa_cli.setup_state.load_config", lambda: None)
    _write_toml(hermetic_env / "uofa.toml", """
        [llm]
        backend = "ollama"
        model = "qwen3.5:4b"
        max_tokens = 4096
    """)
    config = resolve_llm_config(
        cli_overrides={"backend": "anthropic", "api_key_env": "ANTHROPIC_API_KEY"},
        project_root=hermetic_env,
        user_config_path=hermetic_env / "no-such-file.toml",
    )
    assert config.backend == "anthropic"  # from cli
    assert config.model == "qwen3.5:4b"   # from project
    assert config.max_tokens == 4096      # from project
    assert config.provenance["backend"] == "cli"
    assert config.provenance["model"] == "project"


# ── Validation: literal API keys rejected (spec §6.4 Rule 1) ─


def test_literal_api_key_rejected_in_project_config(hermetic_env):
    _write_toml(hermetic_env / "uofa.toml", """
        [llm]
        backend = "anthropic"
        model = "claude-sonnet-5-2026"
        api_key = "sk-ant-leaked-this-everywhere"
    """)
    with pytest.raises(ConfigError, match="Literal `api_key`"):
        resolve_llm_config(
            project_root=hermetic_env,
            user_config_path=hermetic_env / "no-such-file.toml",
        )


def test_literal_api_key_rejected_in_user_config(hermetic_env):
    user_path = _write_toml(hermetic_env / "user-config.toml", """
        [llm]
        backend = "anthropic"
        model = "claude-sonnet-5-2026"
        api_key = "sk-ant-also-leaked"
    """)
    with pytest.raises(ConfigError, match="Literal `api_key`"):
        resolve_llm_config(
            project_root=hermetic_env,
            user_config_path=user_path,
        )


def test_literal_api_key_rejected_in_cli_overrides():
    """Defense-in-depth: even programmatic callers can't slip a literal key in."""
    with pytest.raises(ConfigError, match="Literal `api_key`"):
        resolve_llm_config(
            cli_overrides={"backend": "anthropic", "model": "x", "api_key": "secret"},
        )


# ── Validation: unknown fields, unknown backend, openai-compatible ──


def test_unknown_field_rejected(hermetic_env):
    _write_toml(hermetic_env / "uofa.toml", """
        [llm]
        backend = "ollama"
        model = "qwen3.5:4b"
        wat_is_this = "noise"
    """)
    with pytest.raises(ConfigError, match="Unknown \\[llm\\] fields"):
        resolve_llm_config(
            project_root=hermetic_env,
            user_config_path=hermetic_env / "no-such-file.toml",
        )


def test_unknown_backend_rejected():
    with pytest.raises(ConfigError, match="Unknown LLM backend"):
        resolve_llm_config(
            cli_overrides={"backend": "homegrown-magic", "model": "x"},
        )


def test_openai_compatible_requires_base_url():
    with pytest.raises(ConfigError, match="requires base_url"):
        resolve_llm_config(
            cli_overrides={
                "backend": "openai-compatible",
                "model": "meta-llama/Llama-3.3-70B-Instruct",
                "api_key_env": "TOGETHER_API_KEY",
            },
        )


def test_openai_compatible_with_base_url_resolves(hermetic_env):
    config = resolve_llm_config(
        cli_overrides={
            "backend": "openai-compatible",
            "model": "meta-llama/Llama-3.3-70B-Instruct",
            "base_url": "https://api.together.xyz/v1",
            "api_key_env": "TOGETHER_API_KEY",
        },
        project_root=hermetic_env,
        user_config_path=hermetic_env / "no-such-file.toml",
    )
    assert config.backend == "openai-compatible"
    assert config.base_url == "https://api.together.xyz/v1"


# ── Type coercion ───────────────────────────────────────────


def test_max_tokens_coerced_from_toml_int(hermetic_env, monkeypatch):
    monkeypatch.setattr("uofa_cli.setup_state.load_config", lambda: None)
    _write_toml(hermetic_env / "uofa.toml", """
        [llm]
        backend = "ollama"
        model = "qwen3.5:4b"
        max_tokens = 8192
        timeout_seconds = 120
    """)
    config = resolve_llm_config(
        project_root=hermetic_env,
        user_config_path=hermetic_env / "no-such-file.toml",
    )
    assert config.max_tokens == 8192
    assert config.timeout_seconds == 120.0


# ── API key resolution ─────────────────────────────────────


def test_resolve_api_key_returns_none_for_local():
    config = LLMConfig(backend="ollama", model="qwen3.5:4b")
    assert resolve_api_key(config) is None


def test_resolve_api_key_returns_value_when_env_set(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-real-value")
    config = LLMConfig(
        backend="anthropic",
        model="claude-sonnet-5-2026",
        api_key_env="ANTHROPIC_API_KEY",
    )
    assert resolve_api_key(config) == "sk-ant-real-value"


def test_resolve_api_key_raises_when_remote_missing_env_field():
    config = LLMConfig(backend="anthropic", model="claude-sonnet-5-2026")
    with pytest.raises(ConfigError, match="requires an API key"):
        resolve_api_key(config)


def test_resolve_api_key_raises_when_env_var_unset(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    config = LLMConfig(
        backend="anthropic",
        model="claude-sonnet-5-2026",
        api_key_env="ANTHROPIC_API_KEY",
    )
    with pytest.raises(ConfigError, match="ANTHROPIC_API_KEY.*not set"):
        resolve_api_key(config)


def test_resolve_api_key_error_does_not_echo_key_value(monkeypatch):
    """Spec §6.4: error messages never carry credential material."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-this-is-secret-XYZ")
    # Even though the env var IS set, the error path should not echo it.
    # (Trigger the error path by using a different env var name.)
    config = LLMConfig(
        backend="anthropic",
        model="claude-sonnet-5-2026",
        api_key_env="DOES_NOT_EXIST_VAR",
    )
    with pytest.raises(ConfigError) as exc:
        resolve_api_key(config)
    assert "sk-ant-this-is-secret-XYZ" not in str(exc.value)
    assert "sk-ant-this-is-secret-XYZ" not in str(exc.value.suggestion or "")


# ── get_backend() factory ──────────────────────────────────


def test_get_backend_mock(hermetic_env, monkeypatch):
    monkeypatch.setattr("uofa_cli.setup_state.load_config", lambda: None)
    backend = get_backend(LLMConfig(backend="mock", model="mock"))
    assert isinstance(backend, MockBackend)
    assert backend.model() == "mock"


def test_get_backend_ollama_no_key_needed(hermetic_env, monkeypatch):
    monkeypatch.setattr("uofa_cli.setup_state.load_config", lambda: None)
    backend = get_backend(LLMConfig(backend="ollama", model="qwen3.5:4b"))
    assert isinstance(backend, LiteLLMBackend)
    assert backend.api_key is None
    assert backend.base_url == "http://127.0.0.1:11434"


def test_get_backend_anthropic_resolves_env_var(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-key-only")
    backend = get_backend(LLMConfig(
        backend="anthropic",
        model="claude-sonnet-5-2026",
        api_key_env="ANTHROPIC_API_KEY",
    ))
    assert isinstance(backend, LiteLLMBackend)
    assert backend.api_key == "sk-ant-test-key-only"


def test_get_backend_anthropic_raises_when_key_missing(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(ConfigError):
        get_backend(LLMConfig(
            backend="anthropic",
            model="claude-sonnet-5-2026",
            api_key_env="ANTHROPIC_API_KEY",
        ))


def test_get_backend_resolves_config_when_none_passed(hermetic_env, monkeypatch):
    """Default constructor path: get_backend() with no config calls resolve."""
    monkeypatch.setattr("uofa_cli.setup_state.load_config", lambda: None)
    backend = get_backend(
        project_root=hermetic_env,
        user_config_path=hermetic_env / "no-such-file.toml",
    )
    # Bundled default → ollama
    assert backend.name() == "ollama"
    assert backend.model() == BUNDLED_MODEL


# ── REMOTE_BACKENDS membership (spec invariant) ────────────


def test_remote_backends_set_matches_spec():
    """Spec §3.6 lists exactly anthropic, openai, openai-compatible as remote."""
    assert REMOTE_BACKENDS == {"anthropic", "openai", "openai-compatible"}

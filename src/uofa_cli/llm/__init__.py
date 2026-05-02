"""Pluggable LLM backend abstraction shared by `uofa extract` and `uofa --explain`.

Per UofA `--explain` Flag Spec v0.4 §4.8. The Protocol surface lets callers
target Ollama, Anthropic, OpenAI, and OpenAI-compatible endpoints through a
single interface. Real backends route through `litellm`; tests use
`MockBackend`.
"""

from __future__ import annotations

from uofa_cli.llm.backend import (
    GenerationOptions,
    HealthStatus,
    LLMBackend,
)
from uofa_cli.llm.config import (
    ALLOWED_BACKENDS,
    BUNDLED_MODEL,
    LLMConfig,
    REMOTE_BACKENDS,
    resolve_api_key,
    resolve_llm_config,
)
from uofa_cli.llm.errors import (
    AuthenticationError,
    BackendNotInstalled,
    ConfigError,
    ContextWindowExceeded,
    LLMError,
    LLMUnavailable,
    ModelNotFound,
    RateLimited,
    TimeoutError as LLMTimeoutError,
)
from uofa_cli.llm.litellm_backend import LiteLLMBackend
from uofa_cli.llm.mock_backend import MockBackend


def get_backend(
    config: LLMConfig | None = None,
    **resolve_kwargs,
) -> LLMBackend:
    """Resolve config (if not given) and instantiate a concrete LLMBackend.

    The single entry point for callers (`extract`, the `--explain` pipeline,
    standalone `uofa explain`). Hides the choice between MockBackend and
    LiteLLMBackend so callers can be config-driven without branching.

    Args:
        config: Pre-resolved LLMConfig. If None, calls `resolve_llm_config`
            with `resolve_kwargs` (e.g. `cli_overrides=...`).
        **resolve_kwargs: Forwarded to `resolve_llm_config()` when `config`
            is None.

    Returns:
        A backend instance ready to call. For remote backends, the API key
        is resolved from the env var here (request time, never persisted)
        per spec §6.4 Rule 3.

    Raises:
        ConfigError: backend or model not configured, or API key env var
            referenced but not set.
    """
    if config is None:
        config = resolve_llm_config(**resolve_kwargs)

    if config.backend == "mock":
        return MockBackend(model_name=config.model)

    api_key = resolve_api_key(config) if config.backend in REMOTE_BACKENDS else None

    return LiteLLMBackend(
        backend_name=config.backend,
        model_name=config.model,
        api_key=api_key,
        base_url=config.base_url,
        default_timeout_seconds=config.timeout_seconds or 60.0,
    )


__all__ = [
    "LLMBackend",
    "GenerationOptions",
    "HealthStatus",
    "MockBackend",
    "LiteLLMBackend",
    "LLMConfig",
    "ALLOWED_BACKENDS",
    "REMOTE_BACKENDS",
    "BUNDLED_MODEL",
    "resolve_llm_config",
    "resolve_api_key",
    "get_backend",
    "LLMError",
    "LLMUnavailable",
    "AuthenticationError",
    "BackendNotInstalled",
    "ConfigError",
    "ContextWindowExceeded",
    "LLMTimeoutError",
    "ModelNotFound",
    "RateLimited",
]

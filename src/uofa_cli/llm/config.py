"""LLM configuration resolution (spec v0.4 §3.6).

Precedence (highest first):
    1. CLI overrides — `cli_overrides` dict (e.g. {"backend": "anthropic", "model": "..."})
    2. Project config — `[llm]` section in `<project_root>/uofa.toml`
    3. User config — `[llm]` section in `~/.uofa/config.toml`
    4. Bundled fallback — derived from `setup_state.load_config()` if `uofa setup`
       has been run; otherwise hardcoded defaults (ollama + qwen3.5:4b).

The precedence applies *per field*: a CLI flag setting only `backend` falls
through to project config for `model`, and so on. This matches the spec's
`uofa rules ... --explain --explain-backend anthropic` flow where the user
overrides backend on the command line but expects to inherit the model name
from their project config.

Security model (spec §6.4):
- API keys are referenced by ENV VAR NAME via the `api_key_env` field, never
  embedded directly. Config files containing a literal `api_key = "..."` field
  are rejected at validation time with a clear error.
- Env vars are read at request time (in `get_backend()`), never persisted.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from uofa_cli.llm.errors import ConfigError


# Backend names recognized by the resolver. `bundled` is an alias for the
# Ollama + bundled-model path (so users can be explicit even if the default
# changes); `mock` exists for tests and explicit offline development.
ALLOWED_BACKENDS = frozenset({
    "ollama",
    "anthropic",
    "openai",
    "openai-compatible",
    "bundled",
    "mock",
})

REMOTE_BACKENDS = frozenset({"anthropic", "openai", "openai-compatible"})

# Default model when nothing else is configured. Matches the bundled Qwen
# from `uofa setup` (REQ-DIST-002). Kept in sync with setup_install.py via
# manual review at release time.
BUNDLED_MODEL = "qwen3.5:4b"


@dataclass(frozen=True)
class LLMConfig:
    """Resolved LLM configuration.

    `api_key_env` is the ENV VAR NAME, not the value. Callers that need the
    actual key call `_resolve_api_key(config)` at request time.
    """

    backend: str
    model: str
    api_key_env: str | None = None
    base_url: str | None = None
    max_tokens: int | None = None
    timeout_seconds: float | None = None
    # Provenance for diagnostics. Maps each field name to the source that
    # supplied it ("cli", "project", "user", "bundled", "default").
    provenance: dict[str, str] = field(default_factory=dict)


# ── Public API ──────────────────────────────────────────────


def resolve_llm_config(
    *,
    cli_overrides: dict | None = None,
    project_root: Path | None = None,
    user_config_path: Path | None = None,
) -> LLMConfig:
    """Merge sources per the spec §3.6 precedence and return an LLMConfig.

    All arguments optional — defaults walk the standard discovery paths.
    Pass explicit paths in tests to keep them hermetic.
    """
    cli = _validate_section(cli_overrides or {}, source="cli flags")
    project = _read_project_llm(project_root)
    user = _read_user_llm(user_config_path)
    bundled = _read_bundled_defaults()

    merged: dict[str, object] = {}
    provenance: dict[str, str] = {}

    # Walk highest-priority first; only set fields that aren't already set.
    for src_name, src in (
        ("cli", cli),
        ("project", project),
        ("user", user),
        ("bundled", bundled),
    ):
        for key, value in src.items():
            if key in merged or value is None:
                continue
            merged[key] = value
            provenance[key] = src_name

    backend = merged.get("backend") or "bundled"
    if backend not in ALLOWED_BACKENDS:
        raise ConfigError(
            f"Unknown LLM backend: {backend!r}. "
            f"Allowed: {sorted(ALLOWED_BACKENDS)}",
            suggestion="Check the [llm] backend = '...' value in your config.",
        )

    # `bundled` is an alias for ollama + the bundled model. Resolve it here so
    # the rest of the system only sees concrete backend names.
    effective_backend = "ollama" if backend == "bundled" else backend
    if backend == "bundled" and "model" not in merged:
        merged["model"] = BUNDLED_MODEL
        provenance["model"] = "bundled"

    if "model" not in merged:
        raise ConfigError(
            f"No LLM model configured for backend {effective_backend!r}.",
            suggestion="Set [llm] model = '...' in uofa.toml, or pass "
                       "--explain-model / --extract-model on the command line.",
        )

    if effective_backend == "openai-compatible" and not merged.get("base_url"):
        raise ConfigError(
            "openai-compatible backend requires base_url",
            suggestion="Set [llm] base_url = 'https://...' in uofa.toml.",
        )

    return LLMConfig(
        backend=effective_backend,
        model=str(merged["model"]),
        api_key_env=_optional_str(merged.get("api_key_env")),
        base_url=_optional_str(merged.get("base_url")),
        max_tokens=_optional_int(merged.get("max_tokens")),
        timeout_seconds=_optional_float(merged.get("timeout_seconds")),
        provenance=provenance,
    )


# ── Source readers ──────────────────────────────────────────


def _read_project_llm(project_root: Path | None) -> dict:
    """Read the `[llm]` section from `<project_root>/uofa.toml`.

    If `project_root` is None we walk up from cwd looking for uofa.toml
    (matching `paths.find_project_root()` behaviour). Returns {} when no
    project config or no [llm] section is present.
    """
    if project_root is None:
        from uofa_cli import paths
        project_root = paths.find_project_root()
        if project_root is None:
            return {}
    toml_path = project_root / "uofa.toml"
    if not toml_path.is_file():
        return {}
    raw = _load_toml(toml_path)
    section = raw.get("llm") or {}
    return _validate_section(section, source=str(toml_path))


def _read_user_llm(user_config_path: Path | None) -> dict:
    """Read the `[llm]` section from `~/.uofa/config.toml`.

    Co-exists with the existing `[runtime]`/`[model]`/`[meta]` sections that
    `setup_state` manages — they live in the same file but `[llm]` is owned
    by this module.
    """
    if user_config_path is None:
        from uofa_cli import setup_state
        user_config_path = setup_state.config_path()
    if not user_config_path.is_file():
        return {}
    raw = _load_toml(user_config_path)
    section = raw.get("llm") or {}
    return _validate_section(section, source=str(user_config_path))


def _read_bundled_defaults() -> dict:
    """Lowest-precedence defaults.

    If `uofa setup` has been run, prefer its recorded `model_tag` (the
    user picked it during install); otherwise fall back to the spec
    constant. Always returns backend="bundled" — the resolver expands this
    to ollama internally.
    """
    from uofa_cli import setup_state
    cfg = setup_state.load_config()
    model = cfg.model_tag if cfg else BUNDLED_MODEL
    return {"backend": "bundled", "model": model}


# ── Validation ──────────────────────────────────────────────


_KNOWN_FIELDS = frozenset({
    "backend", "model", "api_key_env", "base_url",
    "max_tokens", "timeout_seconds",
})


def _validate_section(section: dict, source: str) -> dict:
    """Reject literal API keys (spec §6.4 Rule 1) and unknown fields.

    Returns a clean dict with only known fields. Unknown fields produce a
    ConfigError rather than being silently dropped — fail loudly so users
    catch typos immediately.
    """
    if "api_key" in section:
        raise ConfigError(
            f"Literal `api_key` found in {source}. API keys must never be "
            f"committed to config files.",
            suggestion="Use `api_key_env = \"YOUR_VAR_NAME\"` instead and "
                       "set the env var in your shell or secrets manager.",
        )
    unknown = set(section) - _KNOWN_FIELDS
    if unknown:
        raise ConfigError(
            f"Unknown [llm] fields in {source}: {sorted(unknown)}",
            suggestion=f"Allowed fields: {sorted(_KNOWN_FIELDS)}.",
        )
    return {k: v for k, v in section.items() if v is not None}


def _optional_str(value: object) -> str | None:
    return None if value is None else str(value)


def _optional_int(value: object) -> int | None:
    if value is None:
        return None
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError) as exc:
        raise ConfigError(f"Expected integer, got {value!r}") from exc


def _optional_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError) as exc:
        raise ConfigError(f"Expected number, got {value!r}") from exc


def _load_toml(path: Path) -> dict:
    try:
        import tomllib  # noqa: PLC0415
    except ModuleNotFoundError:
        import tomli as tomllib  # type: ignore[no-redef]  # noqa: PLC0415
    with path.open("rb") as f:
        return tomllib.load(f)


# ── API key resolution (request time, never persisted) ──────


def resolve_api_key(config: LLMConfig) -> str | None:
    """Read the env var named by `config.api_key_env` and return its value.

    Returns None for backends that don't need a key (ollama, mock). Raises
    ConfigError for remote backends with no key configured or with the env
    var unset — this is one of the spec §3.7 graceful-degradation triggers.
    """
    if config.backend not in REMOTE_BACKENDS:
        return None
    if not config.api_key_env:
        raise ConfigError(
            f"Backend {config.backend!r} requires an API key.",
            suggestion="Set [llm] api_key_env = \"YOUR_VAR\" in uofa.toml.",
        )
    value = os.environ.get(config.api_key_env)
    if not value:
        raise ConfigError(
            f"Environment variable {config.api_key_env!r} is not set.",
            suggestion=f"Export {config.api_key_env}=... in your shell, or "
                       f"use a secrets manager that injects it (direnv, "
                       f"1Password CLI, etc.).",
        )
    return value

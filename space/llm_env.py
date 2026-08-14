"""Where the Space gets its model from, and how it declines to guess.

Its own module rather than a few lines in `app.py` because `pipeline.py` and
`spike.py` both need it and neither may import `app.py` (the dependency runs the
other way), and because the resolution has to be testable without Gradio.

The contract is deliberately narrow: return an `LLMConfig` when this deployment
is configured for hosted inference, and `None` when it is not. `None` means "use
the legacy local path", which is exactly what the Space did before hosted
inference existed, so an unconfigured deployment behaves as it always has rather
than failing in a new way.

Configuration is split by whether it is a secret:

  UOFA_SPACE_LLM_BACKEND   openai-compatible          Dockerfile ENV (in git)
  UOFA_SPACE_LLM_MODEL     meta-llama/Llama-3.3-...   Dockerfile ENV (in git)
  UOFA_SPACE_LLM_BASE_URL  https://api.together.xyz/v1  Dockerfile ENV (in git)
  UOFA_SPACE_LLM_KEY_ENV   TOGETHER_API_KEY           Dockerfile ENV (in git)
  <that key's value>                                  HF Space secret ONLY

Keeping the first four in the image means the model choice is version-controlled
and reviewable, and `tests/space/test_docker_assets.py` can assert it. Only the
key itself is a secret, and it never reaches the repo: `space/deploy_to_hf.py`
refuses to upload `.key`, `.pem`, or `.env` at all.
"""

from __future__ import annotations

import os
import sys

from uofa_cli.llm.config import ConfigError, LLMConfig, resolve_llm_config

BACKEND_ENV = "UOFA_SPACE_LLM_BACKEND"
MODEL_ENV = "UOFA_SPACE_LLM_MODEL"
BASE_URL_ENV = "UOFA_SPACE_LLM_BASE_URL"
KEY_ENV_ENV = "UOFA_SPACE_LLM_KEY_ENV"

# Backends that reach a third party and therefore need a key present before we
# will claim to be configured. `ollama` and `mock` are local and need nothing.
REMOTE_BACKENDS = frozenset({"openai-compatible", "openai", "anthropic"})

DEFAULT_KEY_ENV = "TOGETHER_API_KEY"


def _env(name: str) -> str | None:
    value = (os.environ.get(name) or "").strip()
    return value or None


def space_llm_config() -> LLMConfig | None:
    """The hosted-inference config for this deployment, or None for local.

    Returns None, meaning "behave exactly as before", when:

    1. `UOFA_SPACE_MODEL` is `mock`. Non-negotiable: `llm_extractor._call_llm`
       short-circuits on `model == "mock" and llm_config is None`, so returning
       a config here would defeat the mock and send the literal string "mock" to
       a real paid endpoint. Every test that drives the UI relies on this.
    2. No backend is configured, i.e. this is a local run or a deployment that
       has not opted in.
    3. A remote backend is configured but its key is absent. That is the
       duplicated-Space case: HF does not copy secret values to a duplicate, so
       the config is present and the key is not. Reporting "not configured"
       lets the caller say so precisely instead of failing mid-extraction.
    """
    if (os.environ.get("UOFA_SPACE_MODEL") or "").strip() == "mock":
        return None

    backend = _env(BACKEND_ENV)
    if not backend:
        return None

    key_env = _env(KEY_ENV_ENV) or DEFAULT_KEY_ENV
    if backend in REMOTE_BACKENDS and not _env(key_env):
        return None

    overrides = {
        "backend": backend,
        "model": _env(MODEL_ENV),
        "base_url": _env(BASE_URL_ENV),
        "api_key_env": key_env,
    }
    try:
        # resolve_llm_config rather than LLMConfig(...) directly: it enforces
        # that openai-compatible carries a base_url, rejects a literal api_key,
        # and records provenance for diagnostics. All of that is worth having
        # on a path whose misconfiguration would otherwise surface as a generic
        # extraction failure.
        return resolve_llm_config(cli_overrides={k: v for k, v in overrides.items() if v})
    except ConfigError as exc:
        # Misconfiguration must not take the Space down: fall back to local and
        # say why, once, where a deploy log will show it.
        print(f"[llm_env] ignoring hosted-inference config: {exc}", file=sys.stderr)
        return None


def missing_key_env() -> str | None:
    """The secret this deployment declares it needs but does not have.

    Returns the env var NAME when hosted inference is configured for a remote
    backend and its key is absent; None otherwise. That combination is precisely
    the duplicated-Space case: HuggingFace does not copy secret VALUES to a
    duplicate, so the image's configuration arrives intact and the key does not.

    This is deliberately narrower than "space_llm_config() returned None".
    A developer running locally with Ollama also gets None there, and must not
    be told a secret is missing. Only a deployment that declares a remote
    backend can be missing one.
    """
    backend = _env(BACKEND_ENV)
    if not backend or backend not in REMOTE_BACKENDS:
        return None
    key_env = _env(KEY_ENV_ENV) or DEFAULT_KEY_ENV
    return None if _env(key_env) else key_env


def is_remote(config: LLMConfig | None) -> bool:
    """True when analysis text leaves this container. Drives the disclosure."""
    return bool(config and config.backend in REMOTE_BACKENDS)


def provider_label(config: LLMConfig | None) -> str:
    """How to name the extractor in provenance and in the readout.

    Names the vendor by host rather than the protocol: `openai-compatible` is
    accurate and tells a reader nothing about where their documents went.
    """
    if config is None:
        return "local model in this Space"
    host = ""
    if config.base_url:
        host = config.base_url.split("//", 1)[-1].split("/", 1)[0]
    return f"{config.model} via {host}" if host else config.model

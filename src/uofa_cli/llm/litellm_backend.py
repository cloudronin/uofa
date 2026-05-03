"""LiteLLMBackend — single concrete LLMBackend wrapping `litellm.completion()`.

Per the architecture decision in the implementation plan: rather than maintain
one adapter class per provider, we route everything through `litellm` (already
a hard dependency for `[extract]`). litellm normalizes the protocol-level
quirks of Ollama, Anthropic, OpenAI, and OpenAI-compatible endpoints; we
normalize the *error semantics* on top so callers see the same exceptions
regardless of backend.

Backend → litellm model-string mapping:
    backend="ollama",            model="qwen3.5:4b"            → "ollama/qwen3.5:4b" + api_base=http://127.0.0.1:11434
    backend="anthropic",         model="claude-sonnet-5-2026"  → "anthropic/claude-sonnet-5-2026" + api_key
    backend="openai",            model="gpt-4o"                → "openai/gpt-4o" + api_key
    backend="openai-compatible", model="meta-llama/...",       → "openai/meta-llama/..." + api_base + api_key
                                 base_url="https://..."

Spec references:
- §4.8 Protocol surface, capability advertisement, generation forms
- §3.7 failure-mode taxonomy → error class mapping
- §6.4 API key handling (read at request time, never logged)
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from dataclasses import dataclass, field

from uofa_cli.llm.backend import GenerationOptions, HealthStatus
from uofa_cli.llm.errors import (
    AuthenticationError,
    BackendNotInstalled,
    ContextWindowExceeded,
    LLMError,
    LLMUnavailable,
    ModelNotFound,
    RateLimited,
    TimeoutError as LLMTimeoutError,
)


# Capability table for the four supported backends. Values reflect spec §4.8
# table; if litellm.get_model_info() returns more accurate data at runtime we
# prefer that for max_context_tokens, but the booleans here are authoritative
# (litellm doesn't always advertise structured-output / streaming support
# accurately for every provider/model pairing).
_DEFAULT_CAPS: dict[str, dict[str, object]] = {
    "ollama": {
        "supports_seed": True,
        "supports_temperature": True,
        "supports_streaming": True,
        # NOTE: disabled in v0.6.0 because litellm's `ollama_chat/` provider
        # silently returns empty content when `response_format` is set on
        # thinking-capable models (qwen3.5, etc.) — even with `think:False`
        # in extras. The bug eats ~5min per call, then yields nothing.
        # Plain `generate()` works fine and the prompt template asks for
        # JSON output explicitly, so callers (extract, explain) get the
        # same shape via the fallback path. Revisit once litellm fixes the
        # Ollama+thinking-model+response_format interaction.
        # Users on non-thinking Ollama models can flip this back via
        # `capability_overrides={"supports_structured_output": True}`.
        "supports_structured_output": False,
        "max_context_tokens": 32_768,        # qwen3.5:4b default; overridable
    },
    "anthropic": {
        "supports_seed": False,
        "supports_temperature": True,
        "supports_streaming": True,
        "supports_structured_output": True,  # via tool use
        "max_context_tokens": 200_000,
    },
    "openai": {
        "supports_seed": True,                # GPT-4o-class; older models ignore
        "supports_temperature": True,
        "supports_streaming": True,
        "supports_structured_output": True,  # via response_format
        "max_context_tokens": 128_000,        # conservative; many models 200K+
    },
    "openai-compatible": {
        # Provider-dependent. Defaults are conservative; configs can override.
        "supports_seed": False,
        "supports_temperature": True,
        "supports_streaming": True,
        "supports_structured_output": False,
        "max_context_tokens": 32_768,
    },
}


@dataclass
class LiteLLMBackend:
    """Wraps `litellm.completion()`. One instance per (backend, model) pair."""

    backend_name: str          # "ollama" | "anthropic" | "openai" | "openai-compatible"
    model_name: str            # provider-native model id (e.g. "qwen3.5:4b")
    api_key: str | None = None # resolved from env var by config layer; never logged
    base_url: str | None = None  # required for openai-compatible; optional for ollama
    capability_overrides: dict[str, object] = field(default_factory=dict)
    default_timeout_seconds: float = 60.0

    def __post_init__(self) -> None:
        if self.backend_name not in _DEFAULT_CAPS:
            raise ValueError(
                f"Unknown backend: {self.backend_name!r}. "
                f"Supported: {sorted(_DEFAULT_CAPS)}"
            )
        # Default Ollama base_url to the local daemon if caller didn't pass one.
        if self.backend_name == "ollama" and not self.base_url:
            self.base_url = "http://127.0.0.1:11434"

    # ── Identity ──────────────────────────────────────────────

    def name(self) -> str:
        return self.backend_name

    def model(self) -> str:
        return self.model_name

    # ── Capability advertisement ──────────────────────────────

    def _cap(self, key: str) -> object:
        if key in self.capability_overrides:
            return self.capability_overrides[key]
        return _DEFAULT_CAPS[self.backend_name][key]

    def supports_seed(self) -> bool:
        return bool(self._cap("supports_seed"))

    def supports_temperature(self) -> bool:
        return bool(self._cap("supports_temperature"))

    def supports_streaming(self) -> bool:
        return bool(self._cap("supports_streaming"))

    def supports_structured_output(self) -> bool:
        return bool(self._cap("supports_structured_output"))

    def max_context_tokens(self) -> int:
        # Prefer litellm's runtime answer if available — it knows the
        # per-model context window for many providers.
        litellm = _import_litellm()
        try:
            info = litellm.get_model_info(self._litellm_model())
            window = info.get("max_input_tokens") or info.get("max_tokens")
            if window:
                return int(window)
        except Exception:  # noqa: BLE001 — litellm raises various things; fall through
            pass
        return int(self._cap("max_context_tokens"))

    # ── Generation ────────────────────────────────────────────

    def generate(self, prompt: str, options: GenerationOptions) -> str:
        # Ollama goes through a direct /api/chat HTTP path instead of
        # litellm. Reason: litellm's ollama_chat provider intermittently
        # returns empty content for thinking-capable models (qwen3.5+) on
        # non-trivial prompts, even with `think:False` in extras. The legacy
        # extract code (pre-v0.6.0) used direct HTTP to /api/chat with
        # `format:"json"` and was reliable; we restore that path here so the
        # spec's unified-abstraction story holds at the *interface* level
        # while the *implementation* sidesteps a real upstream bug.
        # Anthropic / OpenAI / openai-compatible continue through litellm.
        if self.backend_name == "ollama":
            return self._generate_ollama_direct(prompt, options)

        litellm = _import_litellm()
        kwargs = self._completion_kwargs(prompt, options)
        try:
            response = litellm.completion(**kwargs)
        except Exception as exc:  # noqa: BLE001
            raise self._normalize_exception(exc) from exc
        return _extract_text(response)

    def generate_streaming(
        self, prompt: str, options: GenerationOptions
    ) -> Iterator[str]:
        if not self.supports_streaming():
            raise NotImplementedError(
                f"Backend {self.backend_name!r} does not support streaming"
            )
        litellm = _import_litellm()
        kwargs = self._completion_kwargs(prompt, options)
        kwargs["stream"] = True
        try:
            stream = litellm.completion(**kwargs)
            for chunk in stream:
                yield _extract_delta(chunk)
        except Exception as exc:  # noqa: BLE001
            raise self._normalize_exception(exc) from exc

    def generate_structured(
        self, prompt: str, schema: dict, options: GenerationOptions
    ) -> dict:
        if not self.supports_structured_output():
            raise NotImplementedError(
                f"Backend {self.backend_name!r} does not advertise structured-output support"
            )
        litellm = _import_litellm()
        kwargs = self._completion_kwargs(prompt, options)
        # litellm's portable knob. For Ollama this maps to the daemon's
        # `format=json`; for OpenAI to response_format; for Anthropic to a
        # synthetic tool_use under the hood.
        kwargs["response_format"] = {"type": "json_object"}
        try:
            response = litellm.completion(**kwargs)
        except Exception as exc:  # noqa: BLE001
            raise self._normalize_exception(exc) from exc
        text = _extract_text(response)
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            # Schema enforcement isn't perfect — fall back with a useful
            # error rather than crashing the caller silently.
            raise LLMError(
                f"Backend returned non-JSON despite structured-output request: {text[:200]}",
                suggestion="Try a different model that better honors JSON mode, "
                           "or call generate() and parse manually.",
            ) from exc

    # ── Health + cost ────────────────────────────────────────

    def health_check(self) -> HealthStatus:
        """Cheap reachability probe.

        Strategy varies by backend:
        - ollama: GET /api/tags — confirms daemon is running and lists pulled
          models, so we can also tell the user to pull qwen3.5:4b if missing.
        - everything else: trust the credential check happens on the first
          real request. We could send a 1-token completion here, but that
          costs money for remote backends and slows every invocation.
          Returning healthy is fine — the next generate call will surface
          AuthenticationError / LLMUnavailable cleanly through normalization.
        """
        if self.backend_name == "ollama":
            return self._health_check_ollama()
        return HealthStatus.healthy()

    def _health_check_ollama(self) -> HealthStatus:
        try:
            import requests
        except ImportError:
            return HealthStatus(
                ok=False,
                diagnostic="`requests` is not installed",
                suggestion="pip install uofa[extract]",
            )
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=2.0)
        except requests.ConnectionError:
            return HealthStatus(
                ok=False,
                diagnostic=f"Ollama service not responding on {self.base_url}",
                suggestion="Start Ollama (`ollama serve`) or run `uofa setup`.",
            )
        except Exception as exc:  # noqa: BLE001
            return HealthStatus(
                ok=False,
                diagnostic=f"Ollama health probe failed: {exc}",
                suggestion="Check `ollama serve` is running and reachable.",
            )
        if resp.status_code != 200:
            return HealthStatus(
                ok=False,
                diagnostic=f"Ollama returned HTTP {resp.status_code} on /api/tags",
                suggestion="Restart Ollama or check its logs.",
            )
        # If the configured model isn't pulled, surface that proactively —
        # this is the most common Ollama failure for first-time users.
        try:
            tags = {m.get("name", "").split(":")[0] for m in resp.json().get("models", [])}
            if self.model_name and self.model_name.split(":")[0] not in tags:
                return HealthStatus(
                    ok=False,
                    diagnostic=f"Model {self.model_name!r} not pulled",
                    suggestion=f"Run `ollama pull {self.model_name}`.",
                )
        except (ValueError, KeyError):
            # Malformed response; fall through to healthy and let the next
            # real call surface the actual issue.
            pass
        return HealthStatus.healthy()

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        # Local backends have no cost — short-circuit.
        if self.backend_name == "ollama":
            return 0.0
        litellm = _import_litellm()
        try:
            input_cost, output_cost = litellm.cost_per_token(
                model=self._litellm_model(),
                prompt_tokens=input_tokens,
                completion_tokens=output_tokens,
            )
            return float(input_cost) + float(output_cost)
        except Exception:  # noqa: BLE001 — pricing table miss; report 0 rather than crash
            return 0.0

    # ── Internals ────────────────────────────────────────────

    def _litellm_model(self) -> str:
        """The model string litellm expects, e.g. 'anthropic/claude-...'.

        For Ollama we use the `ollama_chat/` prefix (which routes to /api/chat)
        rather than `ollama/` (which routes to /api/generate). The chat
        endpoint correctly handles `response_format={"type":"json_object"}`
        and produces clean streaming chunks; the legacy /api/generate
        transformer is buggy with both. This matches the existing extract
        code's preference for /api/chat.

        For openai-compatible we reuse the openai/ prefix because that's how
        litellm dispatches to the OpenAI-shaped client; the api_base override
        does the actual routing.
        """
        if self.backend_name == "ollama":
            return f"ollama_chat/{self.model_name}"
        if self.backend_name == "openai-compatible":
            return f"openai/{self.model_name}"
        return f"{self.backend_name}/{self.model_name}"

    def _completion_kwargs(self, prompt: str, options: GenerationOptions) -> dict:
        kwargs: dict[str, object] = {
            "model": self._litellm_model(),
            "messages": [{"role": "user", "content": prompt}],
            "timeout": options.timeout_seconds or self.default_timeout_seconds,
        }
        if options.temperature is not None and self.supports_temperature():
            kwargs["temperature"] = options.temperature
        if options.max_tokens is not None:
            kwargs["max_tokens"] = options.max_tokens
        if options.seed is not None and self.supports_seed():
            kwargs["seed"] = options.seed
        if self.api_key:
            kwargs["api_key"] = self.api_key
        if self.base_url:
            kwargs["api_base"] = self.base_url
        # Backend-specific extras (e.g. Ollama's `think` flag)
        if options.extra:
            kwargs.update(options.extra)
        return kwargs

    def _generate_ollama_direct(self, prompt: str, options: GenerationOptions) -> str:
        """Direct /api/chat call for Ollama (bypasses litellm — see `generate`)."""
        return _ollama_direct_chat(
            base_url=self.base_url,
            model=self.model_name,
            prompt=prompt,
            options=options,
        )

    def _normalize_exception(self, exc: Exception) -> LLMError:
        """Map litellm's exception hierarchy onto ours (spec §3.7)."""
        litellm_exc = _import_litellm_exceptions()
        msg = str(exc)
        # Order matters: subclass-first so AuthenticationError isn't caught
        # by APIError up the chain.
        if isinstance(exc, litellm_exc.ContextWindowExceededError):
            return ContextWindowExceeded(
                f"Prompt exceeds {self.model_name} context window: {msg}",
                suggestion="Configure a backend with a larger context window "
                           "(Claude 200K, GPT-5 128K-1M) or chunk the input.",
            )
        if isinstance(exc, litellm_exc.AuthenticationError):
            return AuthenticationError(
                f"{self.backend_name} authentication failed",  # never echo key
                suggestion=f"Verify the env var referenced by api_key_env is set "
                           f"and contains a valid {self.backend_name} key.",
            )
        if isinstance(exc, litellm_exc.RateLimitError):
            retry = _extract_retry_after(exc)
            return RateLimited(
                f"{self.backend_name} returned rate limit error: {msg}",
                retry_after_seconds=retry,
                suggestion="Wait and retry, or switch to a different backend.",
            )
        if isinstance(exc, litellm_exc.Timeout):
            return LLMTimeoutError(
                f"Request to {self.backend_name} timed out",
                suggestion="Increase timeout_seconds in [llm] config, or "
                           "switch to a faster backend.",
            )
        if isinstance(exc, litellm_exc.NotFoundError):
            return ModelNotFound(
                f"Model {self.model_name!r} not found on {self.backend_name}: {msg}",
                suggestion="Check the model name; verify availability with the provider.",
            )
        if isinstance(exc, (litellm_exc.APIConnectionError,
                            litellm_exc.ServiceUnavailableError)):
            return LLMUnavailable(
                f"Cannot reach {self.backend_name}: {msg}",
                suggestion="Check network connectivity and provider status.",
            )
        # Catch-all — preserve the original message but re-raise as our type
        # so the degradation formatter has something structured to work with.
        return LLMError(f"{self.backend_name} call failed: {msg}")


# ── Module-level helpers ─────────────────────────────────────


def _import_litellm():
    """Lazy import so the module loads in environments without [extract]."""
    try:
        import litellm  # noqa: PLC0415
    except ImportError as exc:
        raise BackendNotInstalled(
            "litellm is not installed",
            suggestion="pip install uofa[extract] (or pip install litellm)",
        ) from exc
    return litellm


def _import_litellm_exceptions():
    try:
        import litellm.exceptions as e  # noqa: PLC0415
    except ImportError as exc:
        raise BackendNotInstalled(
            "litellm is not installed",
            suggestion="pip install uofa[extract]",
        ) from exc
    return e


def _extract_text(response) -> str:
    """Pull the assistant text out of a litellm completion response."""
    try:
        return response.choices[0].message.content or ""
    except (AttributeError, IndexError, TypeError) as exc:
        raise LLMError(
            f"Malformed completion response: {response!r}",
        ) from exc


def _extract_delta(chunk) -> str:
    """Pull the partial text out of a streaming chunk; '' for non-content frames."""
    try:
        delta = chunk.choices[0].delta
        return getattr(delta, "content", None) or ""
    except (AttributeError, IndexError, TypeError):
        return ""


def _ollama_direct_chat(
    base_url: str,
    model: str,
    prompt: str,
    options: GenerationOptions,
    *,
    response_format: bool = False,
) -> str:
    """Direct call to Ollama's /api/chat endpoint, bypassing litellm.

    Workaround for litellm's ollama_chat provider returning empty content
    intermittently for thinking-capable models (qwen3.5, qwen3) on
    non-trivial prompts. Pre-v0.6.0 extract used this path directly and
    it was reliable.

    `response_format=True` adds Ollama's native `format:"json"` flag — used
    for callers that genuinely need JSON-shaped output (extract, structured
    explain). Off by default because explain's text-then-parse path is
    more robust to model wobble than format:json.
    """
    try:
        import requests  # noqa: PLC0415
    except ImportError as exc:
        raise BackendNotInstalled(
            "requests is not installed",
            suggestion="pip install uofa[extract]",
        ) from exc

    payload: dict = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        # Default 1h keep-alive so subsequent --explain runs within an
        # interactive session don't pay another cold-start. Ollama's own
        # default is 5 min, which expires quickly when a user is iterating
        # across COUs / examples. Override via options.extra["ollama_keep_alive"]
        # (e.g. "30m", "-1" for forever, "0" to unload immediately).
        "keep_alive": options.extra.get("ollama_keep_alive", "1h"),
    }
    if options.temperature is not None:
        payload.setdefault("options", {})["temperature"] = options.temperature
    if options.max_tokens is not None:
        payload.setdefault("options", {})["num_predict"] = options.max_tokens
    if options.seed is not None:
        payload.setdefault("options", {})["seed"] = options.seed
    if "think" in options.extra:
        payload["think"] = bool(options.extra["think"])
    if response_format:
        payload["format"] = "json"

    timeout = options.timeout_seconds if options.timeout_seconds is not None else 1800.0

    try:
        resp = requests.post(
            f"{base_url}/api/chat",
            json=payload,
            timeout=timeout,
        )
        resp.raise_for_status()
        data = resp.json()
    except requests.Timeout as exc:
        raise LLMTimeoutError(
            f"Ollama request timed out after {timeout}s",
            suggestion="Increase timeout_seconds, or use a faster backend.",
        ) from exc
    except requests.ConnectionError as exc:
        raise LLMUnavailable(
            f"Cannot reach Ollama at {base_url}",
            suggestion="Start Ollama (`ollama serve`) or run `uofa setup`.",
        ) from exc
    except requests.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else None
        if status == 404:
            raise ModelNotFound(
                f"Model {model!r} not pulled (Ollama returned 404)",
                suggestion=f"Run `ollama pull {model}`.",
            ) from exc
        raise LLMError(f"Ollama returned HTTP {status}") from exc
    except ValueError as exc:
        raise LLMError(
            f"Ollama returned non-JSON response: {resp.text[:200]}",
        ) from exc

    try:
        return data["message"]["content"]
    except (KeyError, TypeError) as exc:
        raise LLMError(f"Malformed Ollama response: {data!r}") from exc


def _extract_retry_after(exc: Exception) -> float | None:
    """Best-effort extraction of Retry-After from a RateLimitError."""
    # litellm.RateLimitError sometimes carries `.retry_after`, sometimes the
    # underlying response. Defensive — return None if we can't find one.
    for attr in ("retry_after", "retry_after_seconds"):
        val = getattr(exc, attr, None)
        if val is not None:
            try:
                return float(val)
            except (TypeError, ValueError):
                pass
    response = getattr(exc, "response", None)
    if response is not None:
        headers = getattr(response, "headers", {}) or {}
        retry_after = headers.get("retry-after") or headers.get("Retry-After")
        if retry_after:
            try:
                return float(retry_after)
            except (TypeError, ValueError):
                pass
    return None

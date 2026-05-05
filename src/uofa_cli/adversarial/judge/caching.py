"""Vendor-specific prompt-cache key construction (spec v1.5 §9.1).

Both OpenAI and Gemini support prompt caching at ~90% discount on cached
input tokens. The cache mechanism differs:

- **OpenAI**: implicit position-based prefix caching. Whatever appears at
  the head of the messages list is automatically cached after first use;
  subsequent calls with the same prefix bytes hit the cache. The
  cache_key here is informational (used for run-manifest accounting),
  not passed to the API.

- **Gemini**: explicit `cached_content` resource — the caller creates a
  cache resource via `client.caches.create(...)` with the static prefix
  text + display_name, then references the resource on subsequent calls.
  The cache_key here is used as the display_name on the resource.

Both keys must be stable across calls (so cache hits register) and
must not encode credential material (spec §4.8 design note).
"""

from __future__ import annotations

import hashlib


def build_cache_key(
    provider: str,
    prompt_prefix: str,
    model: str,
) -> str:
    """Produce a stable, vendor-appropriate cache key.

    The key embeds:
      - provider name (e.g. 'openai', 'gemini', 'hf-llama')
      - model id (so model upgrades invalidate the cache)
      - sha256 of the static prompt prefix (so prompt revs invalidate it)

    The hash is truncated to 16 hex chars (64 bits) — collision risk is
    negligible for the per-account cache scope of the vendors involved,
    and the shorter key reads better in logs and run manifests.

    Examples:
        >>> k = build_cache_key('openai', 'You are an expert...', 'gpt-5.4')
        >>> k.startswith('uofa:openai:gpt-5.4:')
        True
    """
    if not provider or not model:
        raise ValueError("provider and model are required for cache key")
    prefix_hash = hashlib.sha256(prompt_prefix.encode("utf-8")).hexdigest()[:16]
    return f"uofa:{provider}:{model}:{prefix_hash}"


def is_cacheable_prefix_size(prompt_prefix: str, *, min_tokens: int = 1024) -> bool:
    """Heuristic: is this prefix large enough to benefit from caching?

    Both OpenAI and Gemini have a minimum-prefix-size threshold below
    which caching is a no-op. Spec §7.1 estimates the static portion at
    ~12K tokens (framework context + verdict definitions + reasoning
    scaffold), well above the min for both vendors. This helper exists
    so calibration-only or smoke runs (small prompts) can skip the
    cache-resource creation overhead.

    Token count is approximated as len(text) / 4 (the standard "1 token
    ≈ 4 chars English" rule of thumb). Approximate is fine; we're
    deciding "cache or don't" not billing.
    """
    approx_tokens = max(0, len(prompt_prefix) // 4)
    return approx_tokens >= min_tokens


# ── Wave H: vendor cache wire-up ────────────────────────────────────────


def apply_cache_control_to_messages(
    messages: list[dict],
    provider_token: str,
    *,
    cache_static_prefix: bool = True,
) -> list[dict]:
    """Mutate `messages` to register vendor-specific prompt-cache hints.

    - **OpenAI**: implicit prefix caching — no flag needed; prefix bytes
      cache automatically. Returns messages unchanged.
    - **Anthropic**: tag the static prefix block(s) with
      `cache_control: {type: 'ephemeral'}` (5-min TTL). Litellm honors
      this when present.
    - **Gemini**: cached_content is created out-of-band via
      `litellm.create_cached_content` and referenced on the call as
      `cached_content=<resource_id>`. We don't mutate messages here;
      the provider builds the call kwargs.

    The mutation is in-place to avoid copying very large prompts. The
    function returns the same list for caller convenience.
    """
    from uofa_cli.adversarial.judge.providers.capabilities import (
        get_capabilities,
    )
    if not cache_static_prefix:
        return messages
    try:
        caps = get_capabilities(provider_token)
    except KeyError:
        return messages
    if not caps.supports_prompt_caching:
        return messages

    if provider_token == "anthropic":
        # Tag the FIRST system / user message that holds the static
        # prefix. Convention in our litellm provider: messages[0] is the
        # system prompt with the static prefix; messages[1] is the user
        # turn with per-case content.
        if messages and isinstance(messages[0], dict):
            content = messages[0].get("content")
            if isinstance(content, str):
                # Promote string content to the structured-block form
                # Anthropic requires for cache_control.
                messages[0]["content"] = [
                    {
                        "type": "text",
                        "text": content,
                        "cache_control": {"type": "ephemeral"},
                    }
                ]
            elif isinstance(content, list) and content:
                # Already structured — tag the first block.
                first = content[0]
                if isinstance(first, dict):
                    first.setdefault("cache_control", {"type": "ephemeral"})
    # OpenAI / Gemini: messages unchanged. (Gemini caching uses
    # cached_content kwargs, set on the call site, not on messages.)
    return messages


def build_gemini_cache_kwargs(
    cache_resource_id: str | None,
) -> dict:
    """Return the kwargs to merge into a litellm call for Gemini caching.

    `cache_resource_id` is the resource name returned by
    `litellm.create_cached_content` for the static prefix. None disables
    caching for the call.
    """
    if cache_resource_id is None:
        return {}
    return {"cached_content": cache_resource_id}


def get_or_create_gemini_cache(
    *,
    model: str,
    static_prefix: str,
    display_name: str,
    ttl_seconds: int = 3600,
) -> str | None:
    """Get-or-create a Gemini cached_content resource for the static prefix.

    Litellm exposes `litellm.create_cached_content` (Vertex AI uses the
    same endpoint as Google Generative AI's `caches.create`). On
    failure (insufficient context size, vendor outage, etc.), returns
    None so the caller proceeds without the cache discount.

    The display_name is used as the lookup key for an existing resource;
    we don't enumerate caches because Gemini doesn't expose a stable
    list-by-display-name API (as of 2026-04). On every run we attempt
    create; on quota/duplicate errors we fall back to None.
    """
    try:
        import litellm  # type: ignore
        res = litellm.create_cached_content(
            model=model,
            contents=[{"role": "user", "parts": [{"text": static_prefix}]}],
            display_name=display_name,
            ttl=f"{ttl_seconds}s",
        )
        return getattr(res, "name", None) or res.get("name")
    except Exception:
        return None

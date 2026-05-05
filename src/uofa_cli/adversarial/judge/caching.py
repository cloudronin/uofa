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

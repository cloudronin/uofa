"""Per-provider capability table (litellm-first refactor, Phase 3 v1.6).

This module is the single source of truth for vendor-specific behaviors that
the unified `LiteLLMProvider` must accommodate:

- `supports_strict_schema` — whether `response_format={'type':'json_schema','strict':True}`
  is honored end-to-end (server-side enforcement) vs. accepted but loosely interpreted
- `schema_keyword_blocklist` — JSONSchema keywords the vendor's strict-mode parser
  rejects; `strip_schema_for_provider()` removes them before the call and the
  runtime parser re-validates against the FULL schema post-call so dropped
  constraints still gate the verdict
- `supports_batch_api` — whether the vendor offers a 50%-discount batch endpoint
- `supports_prompt_caching` — whether prompt-prefix caching is reachable
- `litellm_model_prefix` — mapping from our provider token to litellm's model
  string namespace (e.g. `openai` → `openai/`, `hf-llama` → `huggingface/`)

Adding a new provider is a single dict entry plus a one-line FAMILY_MAP update.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable


@dataclass(frozen=True)
class ProviderCapabilities:
    """Capability snapshot for one provider token (e.g. 'openai', 'anthropic')."""

    family: str  # e.g. 'GPT', 'Claude', 'Gemini', 'Llama', 'Mistral'
    litellm_model_prefix: str  # e.g. 'openai/', 'anthropic/', 'huggingface/meta-llama/'
    default_model: str  # e.g. 'gpt-5.4', 'claude-sonnet-4-6', 'gemini-3.1-pro'

    supports_strict_schema: bool = False
    schema_keyword_blocklist: tuple[str, ...] = ()
    supports_batch_api: bool = False
    supports_prompt_caching: bool = False

    # Per-provider thinking/reasoning param overrides for litellm.acompletion.
    # litellm normalizes most thinking-mode params but Anthropic's
    # `extended_thinking` and OpenAI's `reasoning_effort` differ enough
    # that explicit per-provider overrides keep the call-site clean.
    thinking_kwargs: tuple[tuple[str, object], ...] = ()


# Standard JSONSchema 2020-12 keywords that some vendor strict-mode parsers
# reject. Provider entries below pull subsets that apply to that vendor.
_ANTHROPIC_BLOCKED = (
    "if", "then", "else",
    "$comment",
    "minimum", "maximum",
    "exclusiveMinimum", "exclusiveMaximum",
    "minLength", "maxLength",
    "minItems", "maxItems",
    "pattern",
)


CAPABILITIES: dict[str, ProviderCapabilities] = {
    "openai": ProviderCapabilities(
        family="GPT",
        litellm_model_prefix="openai/",
        default_model="gpt-5.4",
        supports_strict_schema=True,
        schema_keyword_blocklist=(),  # OpenAI strict mode accepts the full draft-2020-12 subset we use
        supports_batch_api=True,
        supports_prompt_caching=True,  # implicit prefix caching, no flag needed
        thinking_kwargs=(("reasoning_effort", "medium"),),
    ),
    "gemini": ProviderCapabilities(
        family="Gemini",
        litellm_model_prefix="gemini/",
        default_model="gemini-3.1-pro",
        supports_strict_schema=True,
        schema_keyword_blocklist=(),  # Gemini's response_schema accepts our shape
        supports_batch_api=True,
        supports_prompt_caching=True,  # via cached_content resource
        thinking_kwargs=(("thinking_config", {"thinking_budget": 8192}),),
    ),
    "hf-llama": ProviderCapabilities(
        family="Llama",
        litellm_model_prefix="huggingface/",
        default_model="meta-llama/Llama-3.3-70B-Instruct",
        supports_strict_schema=False,  # TGI: JSON-mode only; tolerant parser fallback
        schema_keyword_blocklist=(),  # not applicable; schema not sent to vendor
        supports_batch_api=False,
        supports_prompt_caching=False,
        thinking_kwargs=(),
    ),
    "anthropic": ProviderCapabilities(
        family="Claude",
        litellm_model_prefix="anthropic/",
        default_model="claude-sonnet-4-6",
        # Anthropic's strict-mode is more restrictive than OpenAI's. We strip
        # the blocked keywords and re-validate post-call against the full schema.
        supports_strict_schema=True,
        schema_keyword_blocklist=_ANTHROPIC_BLOCKED,
        supports_batch_api=True,  # message-batches; litellm exposes
        supports_prompt_caching=True,  # via cache_control: {type:'ephemeral'}
        thinking_kwargs=(
            ("thinking", {"type": "enabled", "budget_tokens": 8192}),
        ),
    ),
    "mistral": ProviderCapabilities(
        family="Mistral",
        litellm_model_prefix="mistral/",
        default_model="mistral-large-2",
        # Mistral's response_format=json_schema works; specific blocklist
        # populated when verify_mistral_strict_schema.py runs (Wave L).
        supports_strict_schema=True,
        schema_keyword_blocklist=(),  # TBD via real-API smoke; placeholder empty
        supports_batch_api=False,  # No Mistral batch API per spec §6.7
        supports_prompt_caching=False,
        thinking_kwargs=(),  # mistral-large-2 has implicit reasoning; no flag
    ),
}


def get_capabilities(provider_token: str) -> ProviderCapabilities:
    """Look up the capability table for a provider token.

    Raises KeyError on unknown provider — callers should validate against
    CAPABILITIES.keys() before construction.
    """
    if provider_token not in CAPABILITIES:
        raise KeyError(
            f"unknown provider token {provider_token!r}; "
            f"valid: {sorted(CAPABILITIES.keys())}"
        )
    return CAPABILITIES[provider_token]


def litellm_model_string(provider_token: str, model: str | None = None) -> str:
    """Build the litellm model string for a (provider, model) pair.

    Examples:
        >>> litellm_model_string('openai', 'gpt-4o-mini')
        'openai/gpt-4o-mini'
        >>> litellm_model_string('hf-llama')
        'huggingface/meta-llama/Llama-3.3-70B-Instruct'
        >>> litellm_model_string('mistral', 'mistral-medium-3')
        'mistral/mistral-medium-3'
    """
    caps = get_capabilities(provider_token)
    return caps.litellm_model_prefix + (model or caps.default_model)


def strip_schema_for_provider(schema: dict, provider_token: str) -> dict:
    """Recursively drop keywords the vendor strict-mode parser rejects.

    The post-call validator must re-check against the original (unstripped)
    schema so any constraints we removed still gate the verdict.

    Example: Anthropic strict-mode rejects `minimum`/`maximum`. We strip
    those for the API call; the runtime parser then validates the response
    against the full schema (including `minimum`/`maximum`) and rejects
    invalid responses.
    """
    blocklist = set(get_capabilities(provider_token).schema_keyword_blocklist)
    if not blocklist:
        return schema
    return _recursive_strip(schema, blocklist)


def _recursive_strip(node: object, blocklist: Iterable[str]) -> object:
    blockset = set(blocklist)
    if isinstance(node, dict):
        return {
            k: _recursive_strip(v, blockset)
            for k, v in node.items()
            if k not in blockset
        }
    if isinstance(node, list):
        return [_recursive_strip(item, blockset) for item in node]
    return node

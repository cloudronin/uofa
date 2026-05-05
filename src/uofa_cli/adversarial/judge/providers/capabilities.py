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

    # `seed` is honored by OpenAI for deterministic-output runs; other
    # vendors either ignore it or reject it through litellm's pre-flight
    # validator (Anthropic does the latter). Set False to suppress the
    # seed kwarg at the call site for providers that reject it.
    supports_seed: bool = False

    # Some providers (Gemini / Vertex) reject JSONSchema 2020-12
    # `"type": ["X", "null"]` arrays — they want OpenAPI-3-style
    # `"type": "X", "nullable": true`. Set True to apply that conversion
    # in `strip_schema_for_provider` before sending. The runtime parser
    # still validates the response against the full schema.
    convert_nullable_to_openapi: bool = False

    # Optional litellm-call api_base override. Used when the provider is
    # served through a non-standard endpoint that exposes an
    # OpenAI-compatible surface — e.g. HF Router
    # (`https://router.huggingface.co/v1`) for HF-hosted models behind
    # Sambanova / Novita / Together. None means use the litellm vendor
    # default endpoint.
    litellm_api_base: str | None = None

    # Environment variable to read for the litellm api_key parameter.
    # litellm's default lookup ({PROVIDER}_API_KEY) is correct for most
    # vendors; HF needs HF_TOKEN or HUGGINGFACE_API_KEY which doesn't
    # match the default openai-compat path. None means use litellm's
    # default env-driven auth.
    auth_env_var: str | None = None


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

# Mistral large-latest verified 2026-05-04 against
# specs/judge_e_output_schema.json: accepts the schema once if/then/else
# are stripped. The other JSONSchema keywords above (min/max, pattern,
# etc.) pass through cleanly. Probe in dev/tools/scripts/verify_mistral_strict_schema.py.
_MISTRAL_BLOCKED = ("if", "then", "else")

# OpenAI strict-mode also rejects if/then/else per their documented
# subset of JSONSchema 2020-12 (verified 2026-05-04 via the litellm-
# refactor smoke). Min/max, pattern, format pass through cleanly so
# the blocklist is narrower than Anthropic's.
_OPENAI_BLOCKED = ("if", "then", "else")

# Gemini's protobuf-derived schema parser rejects if/then/else (verified
# 2026-05-04). Same restriction as Anthropic / OpenAI / Mistral. Together
# this means the JSONSchema 2020-12 conditional-required block is
# universally rejected; the runtime parser enforces OOS → evidence_gap
# post-call across all four strict-mode providers.
_GEMINI_BLOCKED = ("if", "then", "else")


CAPABILITIES: dict[str, ProviderCapabilities] = {
    "openai": ProviderCapabilities(
        family="GPT",
        litellm_model_prefix="openai/",
        default_model="gpt-5.4",
        supports_strict_schema=True,
        # Verified 2026-05-04: OpenAI strict mode rejects if/then/else
        # ("'if' is not permitted in context"). Other JSONSchema 2020-12
        # keywords we use (min/max, pattern, format) pass through.
        # Runtime parser enforces the OOS → evidence_gap conditional
        # post-call same as for Anthropic / Mistral.
        schema_keyword_blocklist=_OPENAI_BLOCKED,
        supports_batch_api=True,
        supports_prompt_caching=True,  # implicit prefix caching, no flag needed
        thinking_kwargs=(("reasoning_effort", "medium"),),
        supports_seed=True,  # OpenAI honors `seed` for deterministic outputs
    ),
    "gemini": ProviderCapabilities(
        family="Gemini",
        litellm_model_prefix="gemini/",
        # Gemini 3.1 Pro is shipping under preview as `gemini-3.1-pro-preview`
        # (verified 2026-05-04 via the live Models API). Plain
        # `gemini-3.1-pro` returns 404. Capability default uses the preview
        # id; bump to the GA id when it's published.
        default_model="gemini-3.1-pro-preview",
        supports_strict_schema=True,
        # Verified 2026-05-04: Gemini's protobuf-derived schema parser
        # rejects type-array nullable form ("type": ["string", "null"])
        # with "Unknown name 'type' at properties[N].value". The
        # `convert_nullable_to_openapi` flag below converts those to
        # `"type": "string", "nullable": true` at send-time. Gemini
        # also rejects if/then/else (same restriction as the other
        # strict-mode providers).
        schema_keyword_blocklist=_GEMINI_BLOCKED,
        convert_nullable_to_openapi=True,
        # Litellm 1.30 only supports OpenAI in `create_batch`. Gemini batch
        # routing is wired in batch.py but gated OFF here until either
        # (a) litellm adds Gemini, or (b) we add a direct google.genai
        # BatchPredictionJob path. Until then, `submit_batch` raises
        # BatchNotSupported; callers fall back to synchronous + --parallel.
        supports_batch_api=False,
        supports_prompt_caching=True,  # via cached_content resource
        thinking_kwargs=(("thinking_config", {"thinking_budget": 8192}),),
    ),
    "hf-llama": ProviderCapabilities(
        family="Llama",
        # Llama 4 Maverick (verified 2026-05-05) ships through the HF
        # Inference Router behind external providers (sambanova /
        # novita). The Router exposes an OpenAI-compatible
        # /v1/chat/completions surface; we route via litellm's openai/
        # path with `api_base` and `api_key` overrides rather than the
        # legacy `huggingface/` provider class (which talks to the
        # serverless Inference API and has no Llama 4 entry as of the
        # current pin).
        litellm_model_prefix="openai/",
        default_model="meta-llama/Llama-4-Maverick-17B-128E-Instruct:sambanova",
        litellm_api_base="https://router.huggingface.co/v1",
        auth_env_var="HF_TOKEN",
        supports_strict_schema=False,  # JSON-mode only; tolerant parser fallback
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
        # Anthropic message-batches ARE supported by Anthropic's API, but
        # litellm 1.30's `create_batch` is OpenAI-only. The batch.py
        # Anthropic path uses `litellm.list_batch_results` which is
        # likewise vendor-specific. Until either gets first-class
        # support, route to synchronous + --parallel by default. Tests
        # mock the call paths to verify the dispatch wiring is correct.
        supports_batch_api=False,
        supports_prompt_caching=True,  # via cache_control: {type:'ephemeral'}
        # Verified 2026-05-04 against the Anthropic SDK directly:
        # claude-sonnet-4-6 accepts thinking={type:'enabled', budget_tokens:N}
        # and returns interleaved thinking + text content blocks. However,
        # litellm 1.63.7 (current pin) doesn't recognize thinking on this
        # model id and rejects the param at pre-flight. Setting
        # thinking_kwargs=() so the production path doesn't error; bump
        # the litellm pin to ≥1.81 (where the model id is registered) and
        # restore (("thinking", {"type":"enabled","budget_tokens":8192}),)
        # to enable extended thinking on the calibration runs.
        thinking_kwargs=(),
    ),
    "mistral": ProviderCapabilities(
        family="Mistral",
        litellm_model_prefix="mistral/",
        # Mistral Large 3 (verified 2026-05-05): API id `mistral-large-2512`,
        # alias `mistral-large-latest`. Pinning the dated id for run
        # reproducibility. v1.6 spec called for Large 2 (`mistral-large-2411`);
        # bumped to Large 3 per current generation per "no methodology
        # change, just version freshness" decision (2026-05-05).
        default_model="mistral-large-2512",
        # Mistral's response_format=json_schema works; verified via
        # verify_mistral_strict_schema.py 2026-05-04. Mistral rejects
        # the JSONSchema 2020-12 if/then/else conditional-required block;
        # runtime parser enforces OUT-OF-SCOPE → evidence_gap post-call
        # the same way it does for Anthropic.
        supports_strict_schema=True,
        schema_keyword_blocklist=_MISTRAL_BLOCKED,
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
    """Apply per-provider schema transforms before sending to the API.

    Two transforms run in order:
      1. Drop blocklisted keywords (e.g. Anthropic / Mistral / OpenAI
         strict mode rejecting `if/then/else`).
      2. Convert JSONSchema 2020-12 type-array nullable
         (`"type": ["string", "null"]`) to OpenAPI-3 form
         (`"type": "string", "nullable": true`) when the provider
         requires it (Gemini / Vertex).

    The runtime parser must re-check responses against the original
    (unstripped) schema so any constraints we removed still gate the
    verdict. Both transforms are loss-tolerant in that direction —
    valid responses to the transformed schema remain valid against the
    original.
    """
    caps = get_capabilities(provider_token)
    out = schema
    blocklist = set(caps.schema_keyword_blocklist)
    if blocklist:
        out = _recursive_strip(out, blocklist)
    if caps.convert_nullable_to_openapi:
        out = _convert_nullable_arrays(out)
    return out


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


def _convert_nullable_arrays(node: object) -> object:
    """Convert `"type": ["X", "null"]` arrays to `"type": "X", "nullable": true`.

    Recursive over dicts/lists. Single-type strings pass through unchanged.

    Multi-type unions (`["number", "string", "null"]`) collapse to the
    first non-null type since Gemini's protobuf-derived schema parser
    doesn't accept union types either. The runtime parser still
    validates the response against the original schema, so any
    divergence (e.g. a Gemini response returning a string where the
    schema expected number) gets caught post-call. In practice the
    judge output schema's multi-type fields (model temperature, seed)
    are conventionally single-type per provider, so the loss of the
    union semantic doesn't bite.
    """
    if isinstance(node, dict):
        result = {}
        for k, v in node.items():
            if k == "type" and isinstance(v, list):
                non_null = [t for t in v if t != "null"]
                has_null = "null" in v
                # Always collapse to a single type (Gemini-safe).
                if non_null:
                    result[k] = non_null[0]
                if has_null:
                    result["nullable"] = True
            else:
                result[k] = _convert_nullable_arrays(v)
        return result
    if isinstance(node, list):
        return [_convert_nullable_arrays(x) for x in node]
    return node

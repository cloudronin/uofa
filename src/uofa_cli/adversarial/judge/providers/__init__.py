"""Judge provider registry + family resolution (spec v1.6 §6.2).

`FAMILY_MAP` maps provider-prefixed model identifiers to a model family
label. Used by the cross-family circularity check (spec §6.2) and by
agreement-statistics naming (canonical A=GPT, B=Gemini, C=Llama, D=Claude
calibration anchor, E=Mistral arbiter).

Resolution order in `resolve_family`:
    1. Exact literal-key match (e.g. 'openai').
    2. Glob match in dict iteration order (e.g. 'openai/*', 'huggingface/meta-llama/*').

Supports two styles of model identifier:
    - Provider tokens: 'openai', 'gemini', 'anthropic', 'meta', 'mistral'
    - litellm model strings: 'openai/gpt-5.4', 'anthropic/claude-sonnet-4-6',
      'gemini/gemini-3.1-pro', 'huggingface/meta-llama/Llama-3.3-70B-Instruct',
      'mistral/mistral-large-2'

Canonical map for the 5-family v1.6 ensemble:
    Claude  → Judge D (calibration anchor; same family as Phase 2 generator)
    GPT     → Judge A (production)
    Gemini  → Judge B (production)
    Llama   → Judge C (production)
    Mistral → Judge E (disagreement arbiter)
"""

from __future__ import annotations

import fnmatch
from collections import OrderedDict


class UnknownFamilyError(Exception):
    """Raised when a model identifier matches no FAMILY_MAP entry."""


# Order matters: literal keys first (matched O(1)), then globs in
# specificity order. Each glob is tried in insertion order.
FAMILY_MAP: "OrderedDict[str, str]" = OrderedDict(
    [
        # Literal provider tokens (vendor names).
        ("anthropic", "Claude"),
        ("google", "Gemini"),
        ("openai", "GPT"),
        ("meta", "Llama"),
        ("mistral", "Mistral"),
        # litellm-style model-string prefixes (`provider/model_id`).
        # Listed before the legacy hf/ollama globs so litellm strings
        # match first when both forms could apply.
        ("anthropic/*", "Claude"),
        ("openai/*", "GPT"),
        ("gemini/*", "Gemini"),
        ("mistral/*", "Mistral"),
        # HuggingFace-hosted variants. The `huggingface/` prefix is litellm's;
        # the `huggingface:` prefix is legacy from the v1.5 OpenAI-compat path.
        ("huggingface/meta-llama/*", "Llama"),
        ("huggingface:meta-llama/*", "Llama"),
        # Direct mistralai/ HF prefix (covers HF-hosted Mistral if used).
        ("mistralai/*", "Mistral"),
        # Local Ollama variants.
        ("ollama:qwen*", "Qwen"),
        ("ollama:llama*", "Llama"),
        ("ollama/qwen*", "Qwen"),
        ("ollama/llama*", "Llama"),
    ]
)


def resolve_family(model_id: str) -> str:
    """Resolve a model identifier to a family label.

    Examples:
        >>> resolve_family('openai')
        'GPT'
        >>> resolve_family('openai/gpt-4o')
        'GPT'
        >>> resolve_family('huggingface/meta-llama/Llama-3.3-70B-Instruct')
        'Llama'
        >>> resolve_family('mistral/mistral-large-2')
        'Mistral'
        >>> resolve_family('ollama:qwen3:4b')
        'Qwen'

    Raises:
        UnknownFamilyError: if no entry matches.
    """
    if not model_id:
        raise UnknownFamilyError("empty model identifier")

    # Step 1: literal key.
    if model_id in FAMILY_MAP:
        return FAMILY_MAP[model_id]

    # Step 2: glob match in insertion order.
    for key, family in FAMILY_MAP.items():
        if "*" in key and fnmatch.fnmatchcase(model_id, key):
            return family

    raise UnknownFamilyError(
        f"no FAMILY_MAP entry matches model_id={model_id!r}; "
        f"add a literal or glob entry to providers/__init__.py"
    )

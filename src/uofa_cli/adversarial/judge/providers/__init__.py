"""Judge provider registry + family resolution (spec v1.5 §6.2).

`FAMILY_MAP` maps provider-prefixed model identifiers to a model family
label. Used by the cross-family circularity check (spec §6.2) and by
agreement-statistics naming (canonical A=GPT, B=Gemini, C=Llama).

Resolution order in `resolve_family`:
    1. Exact literal-key match (e.g. 'openai').
    2. Glob match in dict iteration order (e.g. 'huggingface:meta-llama/*').
       Insertion order is preserved so the most-specific globs come first.

Glob support is needed because HF-hosted Llama variants share a family
('Llama') but have model-specific paths under 'meta-llama/...' that the
spec wants to keep visible in run manifests.
"""

from __future__ import annotations

import fnmatch
from collections import OrderedDict


class UnknownFamilyError(Exception):
    """Raised when a model identifier matches no FAMILY_MAP entry."""


# Order matters: literal keys first (matched O(1)), then globs in
# specificity order (most specific first). Each glob is tried in
# insertion order via OrderedDict.
FAMILY_MAP: "OrderedDict[str, str]" = OrderedDict(
    [
        # Literal provider tokens.
        ("anthropic", "Claude"),
        ("google", "Gemini"),
        ("openai", "GPT"),
        ("meta", "Llama"),
        # Glob patterns for hosted variants. More specific patterns first.
        ("huggingface:meta-llama/*", "Llama"),
        ("ollama:qwen*", "Qwen"),
        ("ollama:llama*", "Llama"),
    ]
)


def resolve_family(model_id: str) -> str:
    """Resolve a model identifier to a family label.

    Examples:
        >>> resolve_family('openai')
        'GPT'
        >>> resolve_family('huggingface:meta-llama/Llama-3.3-70B-Instruct')
        'Llama'
        >>> resolve_family('ollama:qwen3:4b')
        'Qwen'

    Raises:
        UnknownFamilyError: if no entry matches.
    """
    if not model_id:
        raise UnknownFamilyError(f"empty model identifier")

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

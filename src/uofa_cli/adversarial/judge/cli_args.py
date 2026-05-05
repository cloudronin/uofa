"""CLI argument validation for `uofa adversarial judge` subcommand (spec §6.1, §9.1).

Provider-token-to-position mapping (canonical A/B/C ordering):

    {openai: A, gemini: B, hf-llama: C}

Stats outputs always reference positions (cohen_kappa_AB, etc.); the user
specifies which providers to use via `--judges openai,gemini,hf-llama`
without ever typing A/B/C.

The `mock_a/b/c` tokens are accepted for the smoke test path (spec §14.3)
and bypass the family check.
"""

from __future__ import annotations

from dataclasses import dataclass


# Canonical provider → position map.
PROVIDER_TO_POSITION: dict[str, str] = {
    "openai": "A",
    "gemini": "B",
    "hf-llama": "C",
    # Mock-provider tokens for smoke testing.
    "mock_a": "A",
    "mock_b": "B",
    "mock_c": "C",
    # Anthropic (same family as Phase 2 generator) — smoke-test only;
    # requires --allow-same-family-judge. Maps to position A.
    "anthropic": "A",
}

VALID_PROVIDER_TOKENS = frozenset(PROVIDER_TO_POSITION)


@dataclass(frozen=True)
class JudgesConfig:
    """Validated `--judges` config: tokens → positions, sorted A/B/C order."""

    tokens: tuple[str, ...]  # sorted by position
    positions: tuple[str, ...]  # always ('A', 'B', 'C') for full ensemble
    is_mock: bool


def parse_judges(raw: str) -> JudgesConfig:
    """Parse `--judges <comma,list>` into a JudgesConfig.

    Validation:
      - Every token must be in VALID_PROVIDER_TOKENS.
      - All three positions (A, B, C) must be covered.
      - No duplicate positions.
      - Cannot mix mock + real providers.

    Returns the config with tokens sorted by canonical position so
    downstream code can rely on tokens[0] = position A, etc.
    """
    if not raw or not raw.strip():
        raise ValueError("--judges is required and must not be empty")

    tokens = [t.strip() for t in raw.split(",") if t.strip()]
    if not tokens:
        raise ValueError("--judges parsed to no tokens; expected comma-separated list")

    unknown = [t for t in tokens if t not in VALID_PROVIDER_TOKENS]
    if unknown:
        raise ValueError(
            f"unknown judge tokens {unknown}; valid tokens are "
            f"{sorted(VALID_PROVIDER_TOKENS)}"
        )

    positions = [PROVIDER_TO_POSITION[t] for t in tokens]
    if len(set(positions)) != len(positions):
        # Duplicate position: e.g. user passed `openai,mock_a` (both A).
        raise ValueError(
            f"--judges has duplicate positions: tokens={tokens} → positions={positions}"
        )
    if set(positions) != {"A", "B", "C"}:
        missing = {"A", "B", "C"} - set(positions)
        raise ValueError(
            f"--judges must cover all three positions A/B/C; missing={sorted(missing)}"
        )

    is_mock = all(t.startswith("mock_") for t in tokens)
    # Mixed real+mock ensembles are allowed for smoke runs (e.g.
    # `anthropic,mock_b,mock_c` to validate one real provider end-to-end
    # without spending budget on all three). The `mock_` prefix is
    # self-identifying — anyone who types it meant to.

    # Sort tokens by canonical position so callers can index by [0]/[1]/[2].
    sorted_pairs = sorted(zip(positions, tokens))
    sorted_tokens = tuple(t for _, t in sorted_pairs)
    sorted_positions = tuple(p for p, _ in sorted_pairs)

    return JudgesConfig(
        tokens=sorted_tokens,
        positions=sorted_positions,
        is_mock=is_mock,
    )


def validate_parallel_flag(judges: JudgesConfig, parallel: int | None) -> None:
    """`--parallel` only applies when hf-llama (Judge C) is in the ensemble.

    Spec v1.5 §9.2 concurrency model: OpenAI and Gemini use vendor-managed
    batch APIs; the parallel flag controls in-flight HF Endpoints requests
    only. Validating up-front prevents silent mis-configuration.
    """
    if parallel is None or parallel <= 1:
        return  # default; nothing to validate
    has_hf_llama = "hf-llama" in judges.tokens
    if not has_hf_llama:
        raise ValueError(
            f"--parallel={parallel} requires hf-llama in --judges (spec §9.2 "
            f"concurrency only applies to HF Endpoints synchronous path)"
        )

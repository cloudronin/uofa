"""CLI argument validation for `uofa adversarial judge` subcommand (spec §6.1, §6.7, §9.1).

Provider-token-to-position mapping (canonical 5-family ensemble per v1.6):

    Production ensemble (judge subcommand):
      openai → A, gemini → B, hf-llama → C
    Calibration anchor (calibrate-anchor subcommand):
      anthropic → D
    Disagreement arbiter (arbitrate subcommand):
      mistral → E

Stats outputs always reference positions (cohen_kappa_AB, confusion_matrix_EA, etc.);
the user specifies which providers to use via `--judges openai,gemini,hf-llama`
without ever typing A/B/C.

Mock tokens (`mock_a/b/c/d/e`) bypass the family check and are accepted for
the smoke-test path (spec §14.3).
"""

from __future__ import annotations

from dataclasses import dataclass


# Position constants for the 5-family v1.6 ensemble (spec §6.0, §6.1, §6.7).
JUDGE_A = "A"
JUDGE_B = "B"
JUDGE_C = "C"
JUDGE_D = "D"  # Calibration anchor (Claude)
JUDGE_E = "E"  # Disagreement arbiter (Mistral)

# Canonical provider → position map.
PROVIDER_TO_POSITION: dict[str, str] = {
    # Production judges.
    "openai": JUDGE_A,
    "gemini": JUDGE_B,
    "hf-llama": JUDGE_C,
    # Calibration anchor (Judge D, spec §6.0).
    "anthropic": JUDGE_D,
    # Disagreement arbiter (Judge E, spec §6.7).
    "mistral": JUDGE_E,
    # Mock-provider tokens for smoke testing.
    "mock_a": JUDGE_A,
    "mock_b": JUDGE_B,
    "mock_c": JUDGE_C,
    "mock_d": JUDGE_D,
    "mock_e": JUDGE_E,
}

VALID_PROVIDER_TOKENS = frozenset(PROVIDER_TO_POSITION)

# Production-ensemble positions (the `judge` subcommand requires all three).
PRODUCTION_POSITIONS: frozenset[str] = frozenset({JUDGE_A, JUDGE_B, JUDGE_C})


@dataclass(frozen=True)
class JudgesConfig:
    """Validated `--judges` config: tokens → positions, sorted A/B/C order."""

    tokens: tuple[str, ...]  # sorted by position
    positions: tuple[str, ...]  # always ('A', 'B', 'C') for full ensemble
    is_mock: bool


def parse_judges(raw: str) -> JudgesConfig:
    """Parse `--judges <comma,list>` into a JudgesConfig.

    Validation (production ensemble — `judge` subcommand):
      - Every token must be in VALID_PROVIDER_TOKENS.
      - All three production positions (A, B, C) must be covered.
      - No duplicate positions.
      - Production-only tokens (D=anthropic, E=mistral, mock_d, mock_e) are
        rejected here; they belong to `calibrate-anchor` and `arbitrate`
        subcommands respectively.

    Returns the config with tokens sorted by canonical A/B/C position so
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
    non_production = set(positions) - PRODUCTION_POSITIONS
    if non_production:
        # Tokens for D (anthropic) and E (mistral) belong to the
        # calibrate-anchor / arbitrate subcommands respectively. The
        # `judge` subcommand should reject them so the user gets a clear
        # error rather than silently re-purposing a Judge D / Judge E
        # provider as a production judge.
        wrong_tokens = [t for t in tokens if PROVIDER_TO_POSITION[t] in non_production]
        raise ValueError(
            f"--judges accepts only production-ensemble tokens (A/B/C); "
            f"saw {wrong_tokens} mapping to position(s) {sorted(non_production)}. "
            f"Judge D (anthropic) is for `uofa adversarial calibrate-anchor`; "
            f"Judge E (mistral) is for `uofa adversarial arbitrate`."
        )
    if set(positions) != PRODUCTION_POSITIONS:
        missing = PRODUCTION_POSITIONS - set(positions)
        raise ValueError(
            f"--judges must cover all three production positions A/B/C; missing={sorted(missing)}"
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

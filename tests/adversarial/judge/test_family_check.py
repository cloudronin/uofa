"""Tests for FAMILY_MAP resolution and cross-family circularity check."""

from __future__ import annotations

import pytest

from uofa_cli.adversarial.judge.family_check import (
    FamilyCheckResult,
    check_judge_ensemble,
)
from uofa_cli.adversarial.judge.providers import (
    FAMILY_MAP,
    UnknownFamilyError,
    resolve_family,
)


# ── resolve_family ──────────────────────────────────────────────────────


class TestResolveFamily:
    @pytest.mark.parametrize(
        ("model_id", "expected"),
        [
            ("anthropic", "Claude"),
            ("google", "Gemini"),
            ("openai", "GPT"),
            ("meta", "Llama"),
        ],
    )
    def test_literal_keys_match(self, model_id: str, expected: str) -> None:
        assert resolve_family(model_id) == expected

    def test_hf_meta_llama_glob_matches(self) -> None:
        assert (
            resolve_family("huggingface:meta-llama/Llama-3.3-70B-Instruct") == "Llama"
        )
        # Different specific model under the same prefix still resolves.
        assert resolve_family("huggingface:meta-llama/Llama-3.1-8B") == "Llama"

    def test_ollama_qwen_glob_matches(self) -> None:
        assert resolve_family("ollama:qwen3:4b") == "Qwen"
        assert resolve_family("ollama:qwen2.5") == "Qwen"

    def test_ollama_llama_glob_matches(self) -> None:
        assert resolve_family("ollama:llama3.1") == "Llama"

    def test_empty_string_raises(self) -> None:
        with pytest.raises(UnknownFamilyError):
            resolve_family("")

    def test_unknown_model_raises(self) -> None:
        with pytest.raises(UnknownFamilyError) as exc:
            resolve_family("unknown:weird-model")
        assert "no FAMILY_MAP entry matches" in str(exc.value)

    def test_literal_takes_precedence_over_glob(self) -> None:
        # 'meta' is a literal key returning 'Llama'. There's no glob that
        # could compete here, but verify the lookup path: a literal hit
        # must short-circuit before any fnmatch iteration.
        assert resolve_family("meta") == "Llama"

    def test_family_map_is_ordered(self) -> None:
        # OrderedDict preserves insertion order; literal keys come first
        # so glob iteration is deterministic.
        keys = list(FAMILY_MAP.keys())
        glob_indices = [i for i, k in enumerate(keys) if "*" in k]
        literal_indices = [i for i, k in enumerate(keys) if "*" not in k]
        # Every literal index must precede every glob index.
        assert max(literal_indices) < min(glob_indices)


# ── check_judge_ensemble ────────────────────────────────────────────────


class TestCheckJudgeEnsemble:
    def _spec_default_roles(self) -> list[tuple[str, str]]:
        """The canonical Phase 3 default ensemble (spec §6.1)."""
        return [
            ("generator", "anthropic"),
            ("judge_A", "openai"),
            ("judge_B", "google"),
            ("judge_C", "huggingface:meta-llama/Llama-3.3-70B-Instruct"),
        ]

    def test_clean_ensemble_passes(self) -> None:
        result = check_judge_ensemble(self._spec_default_roles())
        assert result.exit_code == 0
        assert result.violations == []
        assert result.warning is None
        assert result.families == {
            "generator": "Claude",
            "judge_A": "GPT",
            "judge_B": "Gemini",
            "judge_C": "Llama",
        }

    def test_two_judges_same_family_blocks(self) -> None:
        roles = [
            ("generator", "anthropic"),
            ("judge_A", "openai"),
            ("judge_B", "openai"),  # duplicate family
            ("judge_C", "google"),
        ]
        result = check_judge_ensemble(roles)
        assert result.exit_code == 5
        assert result.violations == [("judge_A", "judge_B", "GPT")]
        assert "family circularity" in result.warning

    def test_judge_matches_generator_family_blocks(self) -> None:
        roles = [
            ("generator", "openai"),
            ("judge_A", "openai"),
            ("judge_B", "google"),
            ("judge_C", "huggingface:meta-llama/Llama-3.3-70B-Instruct"),
        ]
        result = check_judge_ensemble(roles)
        assert result.exit_code == 5
        assert result.violations == [("generator", "judge_A", "GPT")]

    def test_three_judges_same_family_emits_three_violations(self) -> None:
        roles = [
            ("generator", "anthropic"),
            ("judge_A", "openai"),
            ("judge_B", "openai"),
            ("judge_C", "openai"),
        ]
        result = check_judge_ensemble(roles)
        assert result.exit_code == 5
        # Pairs A+B, A+C, B+C — three violations.
        assert len(result.violations) == 3
        assert all(v[2] == "GPT" for v in result.violations)

    def test_allow_same_family_overrides(self) -> None:
        roles = [
            ("generator", "anthropic"),
            ("judge_A", "openai"),
            ("judge_B", "openai"),
            ("judge_C", "google"),
        ]
        result = check_judge_ensemble(roles, allow_same_family=True)
        assert result.exit_code == 0
        # Violations are still recorded (so callers can log them); just
        # not blocking.
        assert result.violations == [("judge_A", "judge_B", "GPT")]
        assert "allow-same-family-judge" in result.warning
        assert "Stage 0 smoke" in result.warning

    def test_unknown_model_returns_exit_2(self) -> None:
        roles = [
            ("generator", "anthropic"),
            ("judge_A", "openai"),
            ("judge_B", "google"),
            ("judge_C", "unknown:totally-unknown-model"),
        ]
        result = check_judge_ensemble(roles)
        # Exit 2 is the unresolvable-model path, distinct from the
        # cross-family violation exit 5.
        assert result.exit_code == 2
        assert "no FAMILY_MAP entry" in result.warning

    def test_empty_roles_passes(self) -> None:
        result = check_judge_ensemble([])
        assert result.exit_code == 0
        assert result.families == {}
        assert result.violations == []

    def test_single_role_passes(self) -> None:
        result = check_judge_ensemble([("solo", "openai")])
        assert result.exit_code == 0
        assert result.families == {"solo": "GPT"}

    def test_result_is_dataclass(self) -> None:
        result = check_judge_ensemble([("solo", "openai")])
        assert isinstance(result, FamilyCheckResult)

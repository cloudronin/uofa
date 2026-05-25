"""Regression tests for the v0.6.0 extract → uofa_cli.llm migration.

Spec v0.4 §4.10 + §9.11 require that extract continue to produce
structurally-identical output after the refactor. The full ~30-document
byte-identical regression lives in `tests/regression/` (gated on the bundled
fixtures + a real Ollama daemon, not run in CI). This module is the cheap,
deterministic gate that catches structural changes in the migration code path
itself: it pumps the same prompt through the legacy direct mock path and the
new LLMConfig-driven path and asserts identical results.

If a future change breaks parity here, the heavyweight regression won't be
green either — and we want to fail loud, fast, and locally rather than
discovering it on a 30-doc CI run.
"""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest

from uofa_cli.document_reader import DocumentChunk, ExtractionCorpus
from uofa_cli.llm import LLMConfig, MockBackend
from uofa_cli.llm_extractor import (
    _call_llm,
    _legacy_model_to_config,
    _mock_extract,
    extract,
)


# ── Fixtures ────────────────────────────────────────────────


@pytest.fixture
def vv40_pack_prompt(tmp_path):
    """Minimal pack prompt — content doesn't matter for migration parity."""
    p = tmp_path / "vv40_prompt.txt"
    p.write_text("You are extracting V&V 40 credibility factors.\n")
    return p


@pytest.fixture
def tiny_corpus():
    """A tiny corpus that won't trip the chunking branch."""
    return ExtractionCorpus(
        chunks=[
            DocumentChunk(
                text="The CFD model was validated.",
                source_file="report.pdf",
                source_path="/tmp/report.pdf",
                page_number=1,
                format="pdf",
            ),
        ],
        total_tokens=10,
        file_manifest=[{"name": "report.pdf", "format": "pdf", "tokens": 10}],
    )


# ── _legacy_model_to_config: the translation table ─────────


@pytest.mark.parametrize("model_str,expected_backend,expected_model", [
    # Standard provider/model convention
    ("ollama/qwen3.5:4b",                    "ollama",    "qwen3.5:4b"),
    ("anthropic/claude-sonnet-5-2026",       "anthropic", "claude-sonnet-5-2026"),
    ("openai/gpt-4o",                        "openai",    "gpt-4o"),
    # Bare model names assumed Ollama (matches setup_state.model_tag default)
    ("qwen3.5:4b",                           "ollama",    "qwen3.5:4b"),
    ("llama3.3:70b",                         "ollama",    "llama3.3:70b"),
    # Model names with colons (Ollama tag convention) survive
    ("ollama/llama3.3:70b-instruct-q4_K_M",  "ollama",    "llama3.3:70b-instruct-q4_K_M"),
])
def test_legacy_model_to_config_translation(model_str, expected_backend, expected_model):
    config = _legacy_model_to_config(model_str)
    assert config.backend == expected_backend
    assert config.model == expected_model


def test_legacy_model_anthropic_gets_default_api_key_env():
    """Convention env var must be set for remote backends so users on the
    legacy CLI flag (`--model anthropic/...`) get a working call without
    having to switch to the new --extract-* flags."""
    config = _legacy_model_to_config("anthropic/claude-sonnet-5-2026")
    assert config.api_key_env == "ANTHROPIC_API_KEY"


def test_legacy_model_openai_gets_default_api_key_env():
    config = _legacy_model_to_config("openai/gpt-4o")
    assert config.api_key_env == "OPENAI_API_KEY"


def test_legacy_model_ollama_no_api_key_env():
    config = _legacy_model_to_config("ollama/qwen3.5:4b")
    assert config.api_key_env is None


def test_legacy_unknown_provider_falls_through_to_ollama():
    """An unrecognized prefix is treated as a bare model name → Ollama.
    Avoids surprise routing if the user typos a provider."""
    config = _legacy_model_to_config("some-unknown-provider/foo")
    assert config.backend == "ollama"
    assert config.model == "some-unknown-provider/foo"


# ── Mock path: legacy short-circuit unchanged ──────────────


def test_legacy_mock_string_short_circuits_to_mock_extract(tiny_corpus, vv40_pack_prompt):
    """Passing model='mock' with no llm_config still uses the pack-aware
    _mock_extract — the new abstraction must NOT swallow this code path."""
    result = extract(tiny_corpus, "mock", "vv40", vv40_pack_prompt)
    # _mock_extract's signature: pack-aware factor list. VV40 has 13 factors.
    assert len(result.credibility_factors) == 13
    assert result.assessment_summary["project_name"].value == "Mock Project"


def test_legacy_mock_string_does_not_call_get_backend(tiny_corpus, vv40_pack_prompt):
    """Defense in depth: if get_backend() were ever invoked for model='mock'
    with no llm_config, that would silently change the extraction shape
    (MockBackend returns generic content, not pack-aware extraction JSON).
    Asserting via patch is the cheapest catch."""
    with patch("uofa_cli.llm.get_backend") as mock_get_backend:
        result = extract(tiny_corpus, "mock", "vv40", vv40_pack_prompt)
        mock_get_backend.assert_not_called()
    assert len(result.credibility_factors) == 13


# ── Mock path via the new abstraction ──────────────────────


def test_mock_backend_via_llm_config_produces_equivalent_result(
    tiny_corpus, vv40_pack_prompt
):
    """Threading an LLMConfig(backend='mock', ...) through the new code path
    must produce a structurally-equivalent ExtractionResult to the legacy
    model='mock' short-circuit, when MockBackend is preloaded with the same
    canned JSON.

    This is the load-bearing parity check for the migration.
    """
    legacy_result = extract(tiny_corpus, "mock", "vv40", vv40_pack_prompt)

    # Configure a MockBackend that returns the same JSON _mock_extract emits.
    # Extract now uses generate() (not generate_structured) since commit 7b0f41c —
    # the v4-kv prompts explicitly forbid JSON, so the structured-output path
    # was dropped. Plumb the canned response through `responses` (substring
    # match) which generate() consults, not `structured_responses`.
    canned_json_str = _mock_extract("vv40")
    backend = MockBackend(responses={"V&V 40": canned_json_str})

    # Patch get_backend so the new code path receives our configured mock.
    with patch("uofa_cli.llm.get_backend", return_value=backend):
        new_result = extract(
            tiny_corpus,
            model="ignored-when-llm-config-given",
            pack_name="vv40",
            pack_prompt_path=vv40_pack_prompt,
            llm_config=LLMConfig(backend="mock", model="mock"),
        )

    # Structural equivalence: same field counts, same factor names, same values
    assert len(new_result.credibility_factors) == len(legacy_result.credibility_factors)
    assert {f["factor_type"].value for f in new_result.credibility_factors} == {
        f["factor_type"].value for f in legacy_result.credibility_factors
    }
    assert new_result.assessment_summary["project_name"].value == \
        legacy_result.assessment_summary["project_name"].value
    assert new_result.decision["outcome"].value == legacy_result.decision["outcome"].value


# ── _call_llm respects llm_config override ─────────────────


def test_call_llm_uses_llm_config_when_provided():
    """When llm_config is given, the model string argument is ignored for
    backend selection (it's still used for the legacy mock short-circuit)."""
    backend = MockBackend(default_response='{"answer": 1}')
    with patch("uofa_cli.llm.get_backend", return_value=backend) as mock_get_backend:
        out = _call_llm(
            "any prompt",
            model="this-model-string-is-ignored",
            pack_name="vv40",
            llm_config=LLMConfig(backend="mock", model="custom-tag"),
        )
    # get_backend was called once with our LLMConfig, not the legacy string
    assert mock_get_backend.call_count == 1
    called_with = mock_get_backend.call_args.args[0]
    assert called_with.backend == "mock"
    assert called_with.model == "custom-tag"
    assert json.loads(out) == {"answer": 1}


def test_call_llm_legacy_path_constructs_config_from_string():
    """When llm_config is None, _call_llm must construct an LLMConfig from
    the legacy model string — preserving the existing API contract."""
    backend = MockBackend(default_response='{"answer": 2}')
    with patch("uofa_cli.llm.get_backend", return_value=backend) as mock_get_backend:
        _call_llm(
            "any prompt",
            model="anthropic/claude-sonnet-5-2026",
            pack_name="vv40",
            llm_config=None,
        )
    called_with = mock_get_backend.call_args.args[0]
    assert called_with.backend == "anthropic"
    assert called_with.model == "claude-sonnet-5-2026"
    assert called_with.api_key_env == "ANTHROPIC_API_KEY"


# ── Thinking flag plumbing ─────────────────────────────────


def test_thinking_true_passes_through_to_backend_options():
    """The legacy code passed `think: True` directly to the Ollama JSON
    payload. The new path puts it in GenerationOptions.extra; verify it
    survives the trip."""
    backend = MockBackend(default_response='{"x": 1}')
    with patch("uofa_cli.llm.get_backend", return_value=backend):
        _call_llm(
            "any prompt",
            model="ollama/qwen3.5:4b",
            pack_name="vv40",
            thinking=True,
        )
    # Extract now uses generate() not generate_structured (commit 7b0f41c
    # — v4-kv prompts forbid JSON). The thinking-flag plumbing must still
    # survive the trip.
    methods_called = [c[0] for c in backend.calls]
    last_options = backend.calls[-1][2]
    assert methods_called[-1] == "generate"
    assert last_options.extra.get("think") is True


def test_thinking_false_sets_think_extra_false():
    """`think: False` is set explicitly when thinking=False.

    Updated from the previous "omits think key" behavior: qwen3.5 (and
    other Qwen3-family models) have thinking-mode ON by default at the
    daemon level. Letting the daemon default through caused 5-10x silent
    reasoning-token generation (22 min/bundle vs 7 min on local extract;
    see commit 088d745). We now send think=False explicitly to override
    the model default for structured extraction.
    """
    backend = MockBackend(default_response='{"x": 1}')
    with patch("uofa_cli.llm.get_backend", return_value=backend):
        _call_llm(
            "any prompt",
            model="ollama/qwen3.5:4b",
            pack_name="vv40",
            thinking=False,
        )
    last_options = backend.calls[-1][2]
    assert last_options.extra.get("think") is False

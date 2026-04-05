"""Tests for llm_extractor — prompt assembly, mock provider, JSON parsing, factor validation."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from uofa_cli.document_reader import DocumentChunk, ExtractionCorpus
from uofa_cli.llm_extractor import (
    assemble_corpus_text,
    build_prompt,
    extract,
    _parse_response,
    _mock_extract,
    _json_to_result,
    _validate_factor,
    _coerce_int,
    ExtractionResult,
    FieldExtraction,
)
from uofa_cli.excel_constants import VV40_FACTOR_NAMES, NASA_ALL_FACTOR_NAMES


# ── Fixtures ─────────────────────────────────────────────────


@pytest.fixture
def simple_corpus():
    """A minimal corpus with two chunks from different files."""
    return ExtractionCorpus(
        chunks=[
            DocumentChunk(
                text="The CFD model was validated against PIV data.",
                source_file="report.pdf",
                source_path="/tmp/report.pdf",
                page_number=1,
                format="pdf",
            ),
            DocumentChunk(
                text="| mesh | GCI |\n|---|---|\n| Fine | 0.9% |",
                source_file="mesh.csv",
                source_path="/tmp/mesh.csv",
                format="csv",
            ),
        ],
        total_tokens=25,
        file_manifest=[
            {"name": "report.pdf", "format": "pdf", "tokens": 12},
            {"name": "mesh.csv", "format": "csv", "tokens": 13},
        ],
    )


@pytest.fixture
def vv40_prompt_path(tmp_path):
    """Create a minimal VV40 prompt file."""
    p = tmp_path / "vv40_prompt.txt"
    p.write_text("You are extracting V&V 40 credibility factors.\n")
    return p


# ── assemble_corpus_text ─────────────────────────────────────


class TestAssembleCorpus:
    def test_source_markers(self, simple_corpus):
        text = assemble_corpus_text(simple_corpus)
        assert "=== SOURCE: report.pdf" in text
        assert "=== SOURCE: mesh.csv" in text

    def test_page_markers(self, simple_corpus):
        text = assemble_corpus_text(simple_corpus)
        assert "--- PAGE 1 ---" in text

    def test_content_preserved(self, simple_corpus):
        text = assemble_corpus_text(simple_corpus)
        assert "CFD model was validated" in text
        assert "GCI" in text


# ── build_prompt ─────────────────────────────────────────────


class TestBuildPrompt:
    def test_includes_pack_prompt(self, simple_corpus, vv40_prompt_path):
        corpus_text = assemble_corpus_text(simple_corpus)
        prompt = build_prompt(corpus_text, vv40_prompt_path, "vv40")
        assert "V&V 40" in prompt

    def test_includes_json_schema(self, simple_corpus, vv40_prompt_path):
        corpus_text = assemble_corpus_text(simple_corpus)
        prompt = build_prompt(corpus_text, vv40_prompt_path, "vv40")
        assert "assessment_summary" in prompt
        assert "credibility_factors" in prompt

    def test_includes_guardrails(self, simple_corpus, vv40_prompt_path):
        corpus_text = assemble_corpus_text(simple_corpus)
        prompt = build_prompt(corpus_text, vv40_prompt_path, "vv40")
        assert "Do not fabricate" in prompt


# ── Mock provider ────────────────────────────────────────────


class TestMockProvider:
    def test_vv40_mock_factors(self):
        raw = json.loads(_mock_extract("vv40"))
        factors = raw["credibility_factors"]
        assert len(factors) == 13
        names = [f["factor_type"]["value"] for f in factors]
        assert names == VV40_FACTOR_NAMES

    def test_nasa_mock_factors(self):
        raw = json.loads(_mock_extract("nasa-7009b"))
        factors = raw["credibility_factors"]
        assert len(factors) == 19
        names = [f["factor_type"]["value"] for f in factors]
        assert names == NASA_ALL_FACTOR_NAMES

    def test_mock_has_summary(self):
        raw = json.loads(_mock_extract("vv40"))
        assert "project_name" in raw["assessment_summary"]
        assert raw["assessment_summary"]["project_name"]["value"] is not None

    def test_mock_has_decision(self):
        raw = json.loads(_mock_extract("vv40"))
        assert raw["decision"]["outcome"]["value"] == "Accepted"

    def test_mock_deterministic(self):
        r1 = _mock_extract("vv40")
        r2 = _mock_extract("vv40")
        assert r1 == r2


# ── JSON parsing ─────────────────────────────────────────────


class TestParseResponse:
    def test_plain_json(self):
        data = {"key": "value"}
        result = _parse_response(json.dumps(data))
        assert result == data

    def test_code_fenced_json(self):
        data = {"key": "value"}
        raw = f"```json\n{json.dumps(data)}\n```"
        result = _parse_response(raw)
        assert result == data

    def test_json_with_preamble(self):
        data = {"key": "value"}
        raw = f"Here is the result:\n{json.dumps(data)}\nDone."
        result = _parse_response(raw)
        assert result == data

    def test_malformed_raises(self):
        with pytest.raises(ValueError, match="Could not parse"):
            _parse_response("this is not json at all")


# ── Factor validation ────────────────────────────────────────


class TestValidateFactor:
    def test_exact_match(self):
        factor = {
            "factor_type": {"value": "Software quality assurance", "confidence": 0.9},
            "required_level": {"value": 3, "confidence": 0.8},
            "achieved_level": {"value": 3, "confidence": 0.8},
            "status": {"value": "assessed", "confidence": 0.9},
        }
        result = _validate_factor(factor, VV40_FACTOR_NAMES, (1, 5))
        assert result is not None
        assert result["factor_type"].value == "Software quality assurance"

    def test_fuzzy_match(self):
        factor = {
            "factor_type": {"value": "Software quality asurance", "confidence": 0.9},
            "required_level": {"value": 2, "confidence": 0.8},
            "achieved_level": {"value": 2, "confidence": 0.8},
            "status": {"value": "assessed", "confidence": 0.9},
        }
        result = _validate_factor(factor, VV40_FACTOR_NAMES, (1, 5))
        assert result is not None
        assert result["factor_type"].value == "Software quality assurance"

    def test_invalid_factor_rejected(self):
        factor = {
            "factor_type": {"value": "Completely wrong factor name", "confidence": 0.9},
        }
        result = _validate_factor(factor, VV40_FACTOR_NAMES, (1, 5))
        assert result is None

    def test_integer_level_enforcement(self):
        factor = {
            "factor_type": {"value": "Model form", "confidence": 0.9},
            "required_level": {"value": "3", "confidence": 0.8},
            "achieved_level": {"value": 2.7, "confidence": 0.8},
            "status": {"value": "assessed", "confidence": 0.9},
        }
        result = _validate_factor(factor, VV40_FACTOR_NAMES, (1, 5))
        assert result["required_level"].value == 3
        assert result["achieved_level"].value == 2

    def test_level_clamped_to_range(self):
        factor = {
            "factor_type": {"value": "Model form", "confidence": 0.9},
            "required_level": {"value": 10, "confidence": 0.8},
            "achieved_level": {"value": -1, "confidence": 0.8},
            "status": {"value": "assessed", "confidence": 0.9},
        }
        result = _validate_factor(factor, VV40_FACTOR_NAMES, (1, 5))
        assert result["required_level"].value == 5
        assert result["achieved_level"].value == 1

    def test_text_level_returns_none(self):
        factor = {
            "factor_type": {"value": "Model form", "confidence": 0.9},
            "required_level": {"value": "High", "confidence": 0.8},
            "status": {"value": "assessed", "confidence": 0.9},
        }
        result = _validate_factor(factor, VV40_FACTOR_NAMES, (1, 5))
        assert result["required_level"].value is None


# ── coerce_int ───────────────────────────────────────────────


class TestCoerceInt:
    def test_int(self):
        assert _coerce_int(3, (1, 5)) == 3

    def test_float(self):
        assert _coerce_int(2.7, (1, 5)) == 2

    def test_string(self):
        assert _coerce_int("4", (1, 5)) == 4

    def test_none(self):
        assert _coerce_int(None, (1, 5)) is None

    def test_text(self):
        assert _coerce_int("High", (1, 5)) is None

    def test_clamp_high(self):
        assert _coerce_int(10, (0, 4)) == 4

    def test_clamp_low(self):
        assert _coerce_int(-1, (0, 4)) == 0


# ── Full extraction with mock ────────────────────────────────


class TestExtractMock:
    def test_extract_vv40_mock(self, simple_corpus, vv40_prompt_path):
        result = extract(simple_corpus, "mock", "vv40", vv40_prompt_path)
        assert isinstance(result, ExtractionResult)
        assert len(result.credibility_factors) == 13
        assert result.model_used == "mock"

    def test_extract_nasa_mock(self, simple_corpus, vv40_prompt_path):
        result = extract(simple_corpus, "mock", "nasa-7009b", vv40_prompt_path)
        assert len(result.credibility_factors) == 19

    def test_extract_summary_populated(self, simple_corpus, vv40_prompt_path):
        result = extract(simple_corpus, "mock", "vv40", vv40_prompt_path)
        assert result.assessment_summary["project_name"].value == "Mock Project"
        assert result.assessment_summary["project_name"].confidence >= 0.85

    def test_extract_decision_populated(self, simple_corpus, vv40_prompt_path):
        result = extract(simple_corpus, "mock", "vv40", vv40_prompt_path)
        assert result.decision["outcome"].value == "Accepted"

    def test_extract_factors_have_levels(self, simple_corpus, vv40_prompt_path):
        result = extract(simple_corpus, "mock", "vv40", vv40_prompt_path)
        for factor in result.credibility_factors:
            assert factor["required_level"].value is not None
            assert isinstance(factor["required_level"].value, int)

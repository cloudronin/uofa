"""LLM-based extraction — assembles corpus, calls LLM, parses structured output."""

from __future__ import annotations

import difflib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from uofa_cli.document_reader import ExtractionCorpus
from uofa_cli.excel_constants import (
    VV40_FACTOR_NAMES, NASA_ALL_FACTOR_NAMES,
    VV40_LEVEL_RANGE, NASA_LEVEL_RANGE,
    VALID_FACTOR_STATUSES, VALID_DECISION_OUTCOMES,
)


@dataclass
class FieldExtraction:
    """A single extracted field with confidence and source attribution."""
    value: object = None
    confidence: float = 0.0
    source_file: str | None = None
    source_page: int | None = None


@dataclass
class ExtractionResult:
    """Complete extraction result from the LLM."""
    assessment_summary: dict[str, FieldExtraction] = field(default_factory=dict)
    model_and_data: list[dict[str, FieldExtraction]] = field(default_factory=list)
    validation_results: list[dict[str, FieldExtraction]] = field(default_factory=list)
    credibility_factors: list[dict[str, FieldExtraction]] = field(default_factory=list)
    decision: dict[str, FieldExtraction] = field(default_factory=dict)
    raw_json: dict = field(default_factory=dict)
    model_used: str = ""
    corpus_tokens: int = 0


# ── Corpus assembly ──────────────────────────────────────────


def assemble_corpus_text(corpus: ExtractionCorpus) -> str:
    """Format all chunks with source attribution markers."""
    parts: list[str] = []
    current_file: str | None = None

    for chunk in corpus.chunks:
        # Emit file header when source changes
        if chunk.source_file != current_file:
            current_file = chunk.source_file
            tokens = sum(
                c.token_estimate for c in corpus.chunks
                if c.source_file == current_file
            )
            parts.append(f"\n=== SOURCE: {current_file} ({tokens} tokens) ===\n")

        # Add page/section/sheet marker
        if chunk.page_number is not None:
            parts.append(f"--- PAGE {chunk.page_number} ---")
        if chunk.section_heading:
            parts.append(f"--- SECTION: {chunk.section_heading} ---")
        if chunk.sheet_name:
            parts.append(f'--- SHEET: "{chunk.sheet_name}" ---')

        parts.append(chunk.text)

    return "\n".join(parts)


# ── Prompt construction ──────────────────────────────────────


_JSON_SCHEMA_INSTRUCTIONS = """
Return your extraction as a single JSON object with this exact structure:

{
  "assessment_summary": {
    "project_name": {"value": "...", "confidence": 0.0-1.0, "source_file": "...", "source_page": null},
    "cou_name": {"value": "...", "confidence": 0.0-1.0, "source_file": "...", "source_page": null},
    "cou_description": {"value": "...", "confidence": 0.0-1.0, "source_file": "...", "source_page": null},
    "profile": {"value": "Complete or Minimal", "confidence": 0.0-1.0, "source_file": null, "source_page": null},
    "device_class": {"value": "Class I/II/III", "confidence": 0.0-1.0, "source_file": "...", "source_page": null},
    "model_risk_level": {"value": "MRL 1-5", "confidence": 0.0-1.0, "source_file": "...", "source_page": null},
    "assurance_level": {"value": "Low/Medium/High", "confidence": 0.0-1.0, "source_file": "...", "source_page": null},
    "standards_reference": {"value": "...", "confidence": 0.0-1.0, "source_file": "...", "source_page": null},
    "assessor_name": {"value": "...", "confidence": 0.0-1.0, "source_file": "...", "source_page": null},
    "has_uq": {"value": "Yes or No", "confidence": 0.0-1.0, "source_file": null, "source_page": null}
  },
  "model_and_data": [
    {
      "entity_type": {"value": "Requirement or Model or Dataset", "confidence": 0.0-1.0, "source_file": "..."},
      "name": {"value": "...", "confidence": 0.0-1.0, "source_file": "..."},
      "description": {"value": "...", "confidence": 0.0-1.0, "source_file": "..."}
    }
  ],
  "validation_results": [
    {
      "name": {"value": "...", "confidence": 0.0-1.0, "source_file": "..."},
      "evidence_type": {"value": "ValidationResult", "confidence": 0.0-1.0, "source_file": "..."},
      "description": {"value": "...", "confidence": 0.0-1.0, "source_file": "..."},
      "compares_to": {"value": null, "confidence": 0.0, "source_file": null},
      "has_uq": {"value": "Yes or No", "confidence": 0.0-1.0, "source_file": "..."},
      "metric_value": {"value": "...", "confidence": 0.0-1.0, "source_file": "..."},
      "pass_fail": {"value": "Pass or Fail", "confidence": 0.0-1.0, "source_file": "..."}
    }
  ],
  "credibility_factors": [
    {
      "factor_type": {"value": "exact factor name", "confidence": 0.0-1.0, "source_file": "..."},
      "required_level": {"value": integer, "confidence": 0.0-1.0, "source_file": "..."},
      "achieved_level": {"value": integer, "confidence": 0.0-1.0, "source_file": "..."},
      "acceptance_criteria": {"value": "...", "confidence": 0.0-1.0, "source_file": "..."},
      "rationale": {"value": "...", "confidence": 0.0-1.0, "source_file": "..."},
      "status": {"value": "assessed", "confidence": 0.0-1.0, "source_file": "..."}
    }
  ],
  "decision": {
    "outcome": {"value": "Accepted or Not accepted", "confidence": 0.0-1.0, "source_file": "...", "source_page": null},
    "rationale": {"value": "...", "confidence": 0.0-1.0, "source_file": "...", "source_page": null},
    "decided_by": {"value": "...", "confidence": 0.0-1.0, "source_file": "...", "source_page": null},
    "decision_date": {"value": "YYYY-MM-DD", "confidence": 0.0-1.0, "source_file": "...", "source_page": null}
  }
}

IMPORTANT RULES:
- If you cannot find evidence for a field, return null for the value. Do not fabricate.
- Factor levels must be integers (1-5 for V&V 40 factors, 0-4 for NASA factors). Do not use text like 'High' or 'Medium'.
- Each extracted field must cite the source file and page/sheet where the evidence was found.
- For credibility factors, assess based on explicit evidence in the documents. Do not infer levels from absence of information.
- Confidence: 0.85+ = high (clear explicit evidence), 0.50-0.84 = medium (implied or indirect), <0.50 = low (weak guess).
- Return ONLY the JSON object, no other text.
"""


def build_prompt(corpus_text: str, pack_prompt_path: Path, pack_name: str) -> str:
    """Combine pack-specific factor definitions with corpus and output schema."""
    pack_prompt = ""
    if pack_prompt_path.is_file():
        pack_prompt = pack_prompt_path.read_text(encoding="utf-8")
    elif pack_prompt_path.is_dir():
        # Try to find a prompt file in the directory
        for f in sorted(pack_prompt_path.iterdir()):
            if f.suffix == ".txt":
                pack_prompt = f.read_text(encoding="utf-8")
                break

    parts = [
        pack_prompt,
        "\n\n--- EVIDENCE DOCUMENTS ---\n",
        corpus_text,
        "\n\n--- OUTPUT FORMAT ---\n",
        _JSON_SCHEMA_INSTRUCTIONS,
    ]
    return "\n".join(parts)


# ── LLM calling ──────────────────────────────────────────────


def extract(
    corpus: ExtractionCorpus,
    model: str,
    pack_name: str,
    pack_prompt_path: Path | None = None,
    token_budget: int = 24000,
) -> ExtractionResult:
    """Run LLM extraction on the corpus.

    If corpus fits in token_budget, sends as single prompt.
    Otherwise, chunks by file and merges results.
    """
    if pack_prompt_path is None:
        from uofa_cli import paths
        pack_prompt_path = paths.extract_prompt()

    corpus_text = assemble_corpus_text(corpus)

    if corpus.total_tokens <= token_budget:
        prompt = build_prompt(corpus_text, pack_prompt_path, pack_name)
        raw_response = _call_llm(prompt, model, pack_name)
        raw_json = _parse_response(raw_response)
    else:
        # Chunk by file and merge
        raw_json = _chunked_extraction(corpus, model, pack_name, pack_prompt_path, token_budget)

    result = _json_to_result(raw_json, pack_name)
    result.model_used = model
    result.corpus_tokens = corpus.total_tokens
    result.raw_json = raw_json
    return result


def _chunked_extraction(
    corpus: ExtractionCorpus,
    model: str,
    pack_name: str,
    pack_prompt_path: Path,
    token_budget: int,
) -> dict:
    """Process files in batches when corpus exceeds budget."""
    from uofa_cli.document_reader import ExtractionCorpus as EC

    # Group chunks by source file
    file_groups: dict[str, list] = {}
    for chunk in corpus.chunks:
        file_groups.setdefault(chunk.source_file, []).append(chunk)

    all_results: list[dict] = []
    for filename, chunks in file_groups.items():
        sub_corpus = EC(
            chunks=chunks,
            total_tokens=sum(c.token_estimate for c in chunks),
            file_manifest=[],
            warnings=[],
        )
        corpus_text = assemble_corpus_text(sub_corpus)
        prompt = build_prompt(corpus_text, pack_prompt_path, pack_name)
        raw = _call_llm(prompt, model, pack_name)
        parsed = _parse_response(raw)
        all_results.append(parsed)

    return _merge_json_results(all_results)


def _call_llm(prompt: str, model: str, pack_name: str = "vv40") -> str:
    """Call the LLM — routes to mock or litellm."""
    if model == "mock":
        return _mock_extract(pack_name)

    import litellm

    messages = [{"role": "user", "content": prompt}]

    # Thinking mode control for Qwen 3
    if "qwen3" in model.lower() or "qwen3.5" in model.lower():
        messages[0]["content"] = "/no_think\n" + messages[0]["content"]

    response = litellm.completion(model=model, messages=messages)
    return response.choices[0].message.content


# ── Response parsing ─────────────────────────────────────────


def _parse_response(raw: str) -> dict:
    """Parse LLM response to JSON, handling code fences and malformed output."""
    text = raw.strip()

    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Strip markdown code fences
    if "```" in text:
        # Remove ```json ... ``` or ``` ... ```
        cleaned = re.sub(r"```(?:json)?\s*\n?", "", text)
        cleaned = cleaned.strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

    # Extract first { ... } block via brace matching
    start = text.find("{")
    if start >= 0:
        depth = 0
        for i in range(start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[start:i + 1])
                    except json.JSONDecodeError:
                        break

    raise ValueError(f"Could not parse LLM response as JSON: {text[:200]}...")


def _merge_json_results(results: list[dict]) -> dict:
    """Merge multiple extraction results — highest confidence wins for duplicates."""
    merged: dict = {
        "assessment_summary": {},
        "model_and_data": [],
        "validation_results": [],
        "credibility_factors": [],
        "decision": {},
    }

    for result in results:
        # Summary: highest confidence per field
        for key, val in result.get("assessment_summary", {}).items():
            existing = merged["assessment_summary"].get(key)
            if existing is None or (val and val.get("confidence", 0) > existing.get("confidence", 0)):
                merged["assessment_summary"][key] = val

        # Entities and validation: append all
        merged["model_and_data"].extend(result.get("model_and_data", []))
        merged["validation_results"].extend(result.get("validation_results", []))

        # Factors: deduplicate by factor_type, highest confidence wins
        for factor in result.get("credibility_factors", []):
            ft = factor.get("factor_type", {})
            ft_val = ft.get("value", "") if isinstance(ft, dict) else ft
            # Check if already exists
            found = False
            for i, existing in enumerate(merged["credibility_factors"]):
                eft = existing.get("factor_type", {})
                eft_val = eft.get("value", "") if isinstance(eft, dict) else eft
                if eft_val == ft_val:
                    # Keep higher confidence
                    new_conf = ft.get("confidence", 0) if isinstance(ft, dict) else 0
                    old_conf = eft.get("confidence", 0) if isinstance(eft, dict) else 0
                    if new_conf > old_conf:
                        merged["credibility_factors"][i] = factor
                    found = True
                    break
            if not found:
                merged["credibility_factors"].append(factor)

        # Decision: highest confidence per field
        for key, val in result.get("decision", {}).items():
            existing = merged["decision"].get(key)
            if existing is None or (val and val.get("confidence", 0) > existing.get("confidence", 0)):
                merged["decision"][key] = val

    return merged


# ── JSON → ExtractionResult ──────────────────────────────────


def _json_to_result(raw: dict, pack_name: str) -> ExtractionResult:
    """Convert parsed JSON dict to ExtractionResult with validation."""
    result = ExtractionResult()

    # Summary
    for key, val in raw.get("assessment_summary", {}).items():
        result.assessment_summary[key] = _to_field(val)

    # Entities
    for entity in raw.get("model_and_data", []):
        result.model_and_data.append({k: _to_field(v) for k, v in entity.items()})

    # Validation results
    for vr in raw.get("validation_results", []):
        result.validation_results.append({k: _to_field(v) for k, v in vr.items()})

    # Factors — validate and clean
    valid_names = NASA_ALL_FACTOR_NAMES if "nasa" in pack_name.lower() else VV40_FACTOR_NAMES
    level_range = NASA_LEVEL_RANGE if "nasa" in pack_name.lower() else VV40_LEVEL_RANGE

    for factor in raw.get("credibility_factors", []):
        cleaned = _validate_factor(factor, valid_names, level_range)
        if cleaned is not None:
            result.credibility_factors.append(cleaned)

    # Decision
    for key, val in raw.get("decision", {}).items():
        result.decision[key] = _to_field(val)

    return result


def _to_field(val: object) -> FieldExtraction:
    """Convert a JSON value to a FieldExtraction."""
    if isinstance(val, dict):
        return FieldExtraction(
            value=val.get("value"),
            confidence=float(val.get("confidence", 0.0)),
            source_file=val.get("source_file"),
            source_page=val.get("source_page"),
        )
    # Plain value — no confidence info
    return FieldExtraction(value=val, confidence=0.5)


def _validate_factor(
    factor: dict,
    valid_names: list[str],
    level_range: tuple[int, int],
) -> dict[str, FieldExtraction] | None:
    """Validate and clean a single factor extraction."""
    ft_raw = factor.get("factor_type", {})
    ft_val = ft_raw.get("value", "") if isinstance(ft_raw, dict) else str(ft_raw)

    if not ft_val:
        return None

    # Fuzzy match factor name
    matches = difflib.get_close_matches(ft_val, valid_names, n=1, cutoff=0.6)
    if matches:
        ft_val = matches[0]
    else:
        # Not a valid factor — skip
        return None

    result: dict[str, FieldExtraction] = {}
    result["factor_type"] = _to_field(ft_raw)
    result["factor_type"].value = ft_val  # Use corrected name

    # Integer level enforcement
    for level_key in ("required_level", "achieved_level"):
        raw = factor.get(level_key, {})
        fe = _to_field(raw)
        fe.value = _coerce_int(fe.value, level_range)
        result[level_key] = fe

    # Text fields
    for text_key in ("acceptance_criteria", "rationale"):
        result[text_key] = _to_field(factor.get(text_key, {}))

    # Status
    status_raw = factor.get("status", {})
    status_fe = _to_field(status_raw)
    if status_fe.value and status_fe.value not in VALID_FACTOR_STATUSES:
        # Try fuzzy match
        matches = difflib.get_close_matches(
            str(status_fe.value), VALID_FACTOR_STATUSES, n=1, cutoff=0.6
        )
        status_fe.value = matches[0] if matches else "assessed"
    result["status"] = status_fe

    return result


def _coerce_int(value: object, level_range: tuple[int, int]) -> int | None:
    """Coerce a value to an integer within the valid range, or None."""
    if value is None:
        return None
    try:
        n = int(float(str(value)))
        lo, hi = level_range
        return max(lo, min(hi, n))
    except (ValueError, TypeError):
        return None


# ── Mock provider ────────────────────────────────────────────


def _mock_extract(pack_name: str) -> str:
    """Return deterministic mock JSON for testing — no external dependencies."""
    is_nasa = "nasa" in pack_name.lower()
    factor_names = NASA_ALL_FACTOR_NAMES if is_nasa else VV40_FACTOR_NAMES
    standard = "NASA-STD-7009B" if is_nasa else "ASME-VV40-2018"
    level_default = 2 if is_nasa else 3

    factors = []
    for name in factor_names:
        factors.append({
            "factor_type": {"value": name, "confidence": 0.90, "source_file": "mock-report.pdf", "source_page": 1},
            "required_level": {"value": level_default, "confidence": 0.85, "source_file": "mock-report.pdf", "source_page": 1},
            "achieved_level": {"value": level_default, "confidence": 0.85, "source_file": "mock-report.pdf", "source_page": 1},
            "acceptance_criteria": {"value": f"Acceptance criteria for {name}", "confidence": 0.80, "source_file": "mock-report.pdf", "source_page": 1},
            "rationale": {"value": f"Rationale for {name}", "confidence": 0.85, "source_file": "mock-report.pdf", "source_page": 1},
            "status": {"value": "assessed", "confidence": 0.95, "source_file": "mock-report.pdf", "source_page": 1},
        })

    result = {
        "assessment_summary": {
            "project_name": {"value": "Mock Project", "confidence": 0.95, "source_file": "mock-report.pdf", "source_page": 1},
            "cou_name": {"value": "Mock Context of Use", "confidence": 0.90, "source_file": "mock-report.pdf", "source_page": 1},
            "cou_description": {"value": "A mock credibility assessment for testing.", "confidence": 0.85, "source_file": "mock-report.pdf", "source_page": 1},
            "profile": {"value": "Complete", "confidence": 0.80, "source_file": None, "source_page": None},
            "device_class": {"value": "Class II", "confidence": 0.90, "source_file": "mock-report.pdf", "source_page": 1},
            "model_risk_level": {"value": "MRL 2", "confidence": 0.85, "source_file": "mock-report.pdf", "source_page": 1},
            "assurance_level": {"value": "Medium", "confidence": 0.75, "source_file": None, "source_page": None},
            "standards_reference": {"value": standard, "confidence": 0.95, "source_file": "mock-report.pdf", "source_page": 1},
            "assessor_name": {"value": "Mock Assessor", "confidence": 0.70, "source_file": "mock-report.pdf", "source_page": 1},
            "has_uq": {"value": "Yes", "confidence": 0.80, "source_file": None, "source_page": None},
        },
        "model_and_data": [
            {
                "entity_type": {"value": "Requirement", "confidence": 0.90, "source_file": "mock-report.pdf"},
                "name": {"value": "Safety requirement", "confidence": 0.85, "source_file": "mock-report.pdf"},
                "description": {"value": "Mock safety requirement description", "confidence": 0.80, "source_file": "mock-report.pdf"},
            },
            {
                "entity_type": {"value": "Model", "confidence": 0.95, "source_file": "mock-report.pdf"},
                "name": {"value": "Mock CFD Model", "confidence": 0.90, "source_file": "mock-report.pdf"},
                "description": {"value": "Computational model for mock analysis", "confidence": 0.85, "source_file": "mock-report.pdf"},
            },
        ],
        "validation_results": [
            {
                "name": {"value": "Mesh convergence study", "confidence": 0.95, "source_file": "mock-report.pdf"},
                "evidence_type": {"value": "ValidationResult", "confidence": 0.90, "source_file": "mock-report.pdf"},
                "description": {"value": "Grid convergence analysis", "confidence": 0.85, "source_file": "mock-report.pdf"},
                "compares_to": {"value": None, "confidence": 0.0, "source_file": None},
                "has_uq": {"value": "Yes", "confidence": 0.85, "source_file": "mock-report.pdf"},
                "metric_value": {"value": "GCI = 1.2%", "confidence": 0.90, "source_file": "mock-report.pdf"},
                "pass_fail": {"value": "Pass", "confidence": 0.85, "source_file": "mock-report.pdf"},
            },
        ],
        "credibility_factors": factors,
        "decision": {
            "outcome": {"value": "Accepted", "confidence": 0.95, "source_file": "mock-report.pdf", "source_page": 1},
            "rationale": {"value": "All factors meet required levels.", "confidence": 0.90, "source_file": "mock-report.pdf", "source_page": 1},
            "decided_by": {"value": "Mock Review Board", "confidence": 0.85, "source_file": "mock-report.pdf", "source_page": 1},
            "decision_date": {"value": "2026-01-15", "confidence": 0.80, "source_file": "mock-report.pdf", "source_page": 1},
        },
    }

    return json.dumps(result)

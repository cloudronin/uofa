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
    """Combine pack-specific factor definitions with corpus and output schema.

    If the pack prompt contains a ``{corpus}`` placeholder, the prompt is
    treated as self-contained — the placeholder is replaced with the corpus
    text and no additional schema instructions are appended.

    Otherwise falls back to the legacy concatenation approach (pack prompt +
    evidence + JSON schema instructions).
    """
    pack_prompt = ""
    if pack_prompt_path.is_file():
        pack_prompt = pack_prompt_path.read_text(encoding="utf-8")
    elif pack_prompt_path.is_dir():
        # Try to find a prompt file in the directory
        for f in sorted(pack_prompt_path.iterdir()):
            if f.suffix == ".txt":
                pack_prompt = f.read_text(encoding="utf-8")
                break

    # Self-contained prompt with {corpus} placeholder
    if "{corpus}" in pack_prompt:
        return pack_prompt.replace("{corpus}", corpus_text)

    # Legacy: concatenate pack prompt + evidence + schema
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
    thinking: bool = False,
    llm_config=None,  # LLMConfig | None — typed as str to avoid an import cycle
) -> ExtractionResult:
    """Run LLM extraction on the corpus.

    If corpus fits in token_budget, sends as single prompt.
    Otherwise, chunks by file and merges results.

    Args:
        thinking: If True, enable thinking/reasoning mode for models that
            support it (e.g. qwen3/qwen3.5). Default is False for faster
            structured extraction.
        llm_config: Optional pre-resolved LLMConfig. When given, takes
            precedence over the `model` string and lets callers pass full
            backend configuration (api_key_env, base_url, etc.) without
            squeezing it through the legacy provider/model convention.
            Most callers should use this; the `model` string remains for
            back-compat with tests and users on existing CLI flags.
    """
    if pack_prompt_path is None:
        from uofa_cli import paths
        pack_prompt_path = paths.extract_prompt()

    corpus_text = assemble_corpus_text(corpus)

    if corpus.total_tokens <= token_budget:
        prompt = build_prompt(corpus_text, pack_prompt_path, pack_name)
        raw_json = _call_and_parse_with_retry(
            prompt, model, pack_name,
            thinking=thinking, llm_config=llm_config,
            max_attempts=3,
        )
    else:
        # Chunk by file and merge
        raw_json = _chunked_extraction(
            corpus, model, pack_name, pack_prompt_path, token_budget,
            thinking=thinking, llm_config=llm_config,
        )

    # Save raw response for debugging
    _save_debug_response(raw_json)

    result = _json_to_result(raw_json, pack_name)
    result.model_used = model
    result.corpus_tokens = corpus.total_tokens
    result.raw_json = raw_json
    return result


def _save_debug_response(raw_json: dict) -> None:
    """Save raw LLM JSON response to /tmp for debugging."""
    try:
        debug_path = Path("/tmp/uofa-extract-last-response.json")
        debug_path.write_text(json.dumps(raw_json, indent=2), encoding="utf-8")
    except OSError:
        pass  # Non-critical — don't fail extraction over debug logging


def _chunked_extraction(
    corpus: ExtractionCorpus,
    model: str,
    pack_name: str,
    pack_prompt_path: Path,
    token_budget: int,
    thinking: bool = False,
    llm_config=None,
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
        raw = _call_llm(
            prompt, model, pack_name, thinking=thinking, llm_config=llm_config,
        )
        parsed = _parse_response(raw)
        all_results.append(parsed)

    return _merge_json_results(all_results)


def _call_and_parse_with_retry(
    prompt: str,
    model: str,
    pack_name: str,
    *,
    thinking: bool = False,
    llm_config=None,
    max_attempts: int = 3,
) -> dict:
    """Call the LLM and parse the response, retrying on parse failure.

    Local qwen3.5:4b drops closing braces in long structured outputs roughly
    25-33% of the time on the v3-nasa-aero extract prompt. Each retry is a
    fresh model call with stochastic sampling (temp > 0), so structural
    errors in one attempt are statistically independent of the next.
    With 3 attempts and 30% per-call failure rate, expected success rate
    is 1 - 0.3^3 = 97.3%.

    Saves the raw response of every attempt to /tmp/uofa-extract-last-raw.txt
    (overwritten each call) so the most recent attempt — successful or not —
    is available for inspection.
    """
    last_err: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        raw_response = _call_llm(
            prompt, model, pack_name, thinking=thinking, llm_config=llm_config,
        )
        try:
            Path("/tmp/uofa-extract-last-raw.txt").write_text(raw_response)
        except OSError:
            pass
        try:
            return _parse_response(raw_response)
        except ValueError as exc:
            last_err = exc
            if attempt < max_attempts:
                import sys
                print(
                    f"  [extract] attempt {attempt}/{max_attempts} produced "
                    f"malformed JSON; retrying...",
                    file=sys.stderr,
                )
    assert last_err is not None
    raise last_err


def _call_llm(
    prompt: str,
    model: str,
    pack_name: str = "vv40",
    thinking: bool = False,
    llm_config=None,
) -> str:
    """Call the LLM — routes to mock or to the unified backend abstraction.

    Migrated in v0.6.0 from a hand-rolled `requests.post`/`litellm.completion`
    split (spec v0.4 §4.10). Model resolution still accepts the legacy
    convention so existing callers, tests, and `uofa.toml` configs continue
    to work unchanged:

    - "mock" → in-process canned JSON (preserves _mock_extract behavior).
    - "ollama/MODEL" → Ollama via the new LiteLLMBackend (now uses
      /api/chat with response_format=json — matches the previous
      hand-rolled behavior).
    - "PROVIDER/MODEL" (e.g. "anthropic/claude-..., "openai/gpt-...") →
      remote backend; API key resolved from the convention env var.
    - bare "MODEL" (no slash) → assumed Ollama (matches the setup_state
      `model_tag` convention).

    Args:
        thinking: If True, enable thinking/reasoning mode. For qwen3/qwen3.5
            models via Ollama this maps to the `think` extra option that
            litellm forwards to the daemon. Default is False for faster
            structured extraction.
    """
    if model == "mock" and llm_config is None:
        return _mock_extract(pack_name)

    from uofa_cli.llm import GenerationOptions, get_backend

    config = llm_config if llm_config is not None else _legacy_model_to_config(model)
    backend = get_backend(config)

    options = GenerationOptions(
        timeout_seconds=1800.0,
        # Cap output tokens to catch runaway generation, but generous enough
        # not to truncate normal output. The extract prompt mandates per-field
        # {value, confidence, source_file, source_page} quadruples, producing
        # ~10K tokens of JSON for 13-factor vv40 and ~14K for 19-factor NASA.
        max_tokens=16384,
        # qwen3.5 (and other Qwen3-family) models have thinking-mode ON by
        # default — they generate reasoning tokens that don't appear in the
        # final response but ARE computed (often 5-10x more than visible
        # output). For structured extraction we don't want this — the prompt
        # is explicit and the model should produce JSON directly. Setting
        # think=False is the fast path. Caller can override by passing
        # thinking=True (which sends think=True explicitly).
        extra={"think": True} if thinking else {"think": False},
    )

    # Prefer structured generation so backends enforce JSON shape (matches
    # the previous Ollama `format:"json"` behavior; remote backends gain
    # the same guarantee for free). Fall back to plain generate() for
    # backends that don't advertise structured-output support.
    if backend.supports_structured_output():
        try:
            result_dict = backend.generate_structured(prompt, schema={}, options=options)
            return json.dumps(result_dict)
        except NotImplementedError:
            pass

    return backend.generate(prompt, options)


def _legacy_model_to_config(model: str):
    """Translate a legacy `model` string into an LLMConfig.

    Local helper — kept private until extract_cmd is migrated to use the
    new resolver directly (Phase 3b).
    """
    from uofa_cli.llm.config import ALLOWED_BACKENDS, LLMConfig

    _DEFAULT_KEY_ENV = {
        "anthropic": "ANTHROPIC_API_KEY",
        "openai": "OPENAI_API_KEY",
    }

    if "/" in model:
        backend_name, model_name = model.split("/", 1)
        if backend_name in ALLOWED_BACKENDS and backend_name != "mock":
            return LLMConfig(
                backend=backend_name,
                model=model_name,
                api_key_env=_DEFAULT_KEY_ENV.get(backend_name),
            )
    # Bare model name → Ollama. Matches setup_state.model_tag convention.
    return LLMConfig(backend="ollama", model=model)


# ── Response parsing ─────────────────────────────────────────


# v4-kv format: response is divided into `=== SECTION ===` blocks containing
# `key: value` lines. Avoids the nested-JSON failure mode of local qwen3.5:4b
# (drops closing braces in long structured outputs ~25-33% of the time).
# Downstream code (`_to_field`, `_validate_factor`) already handles flat
# string values, so kv values flow through to xlsx/JSON-LD without changes.
_KV_BLOCK_RE = re.compile(r"^===\s*([A-Z_]+)\s*===\s*$", re.MULTILINE)
_KV_LINE_RE = re.compile(r"^([a-zA-Z_][a-zA-Z0-9_]*):\s*(.*)$")


def _parse_kv_block(content: str) -> dict:
    """Parse `key: value` lines within one section, with continuation support.

    Lines matching `^<ident>:` start a new key. Any line that doesn't match
    is treated as a continuation of the previous value (separated by space).
    Empty lines are skipped. Values are stripped; empty values become None.
    """
    out: dict[str, object] = {}
    current_key: str | None = None
    for line in content.splitlines():
        if not line.strip():
            continue
        match = _KV_LINE_RE.match(line)
        if match:
            current_key = match.group(1)
            value = match.group(2).strip()
            out[current_key] = value if value else None
        elif current_key is not None:
            # Continuation — append to previous value
            existing = out.get(current_key) or ""
            out[current_key] = f"{existing} {line.strip()}".strip()
    return out


def _parse_kv_response(text: str) -> dict:
    """Parse v4-kv format extract response into the shape `_json_to_result` expects.

    Format:
        === ASSESSMENT_SUMMARY ===
        project_name: AquaDrive 550 Pump
        ...

        === ENTITY ===
        entity_type: Model
        name: ANSYS CFX RANS-SST
        ...

        === FACTOR ===
        factor_type: Software quality assurance
        required_level: 2
        ...
        (one FACTOR block per canonical factor)

        === DECISION ===
        outcome: Accepted
        ...

    Multiple ENTITY/VALIDATION_RESULT/FACTOR blocks accumulate into lists.
    ASSESSMENT_SUMMARY/DECISION are singletons (last wins).
    """
    result: dict = {
        "assessment_summary": {},
        "model_and_data": [],
        "validation_results": [],
        "credibility_factors": [],
        "decision": {},
    }
    parts = _KV_BLOCK_RE.split(text)
    if len(parts) < 3:
        raise ValueError("KV format markers not found (=== SECTION ===)")

    i = 1
    while i + 1 < len(parts):
        section = parts[i].upper()
        kv = _parse_kv_block(parts[i + 1])
        if section == "ASSESSMENT_SUMMARY":
            result["assessment_summary"] = kv
        elif section == "ENTITY":
            result["model_and_data"].append(kv)
        elif section == "VALIDATION_RESULT":
            result["validation_results"].append(kv)
        elif section == "FACTOR":
            result["credibility_factors"].append(kv)
        elif section == "DECISION":
            result["decision"] = kv
        # Unknown sections are silently ignored
        i += 2
    return result


def _parse_response(raw: str) -> dict:
    """Parse LLM response. Tries kv-format first (v4+), falls back to JSON."""
    text = raw.strip()

    # KV-format detection: `=== SECTION ===` marker line. Cheap regex check
    # before committing to the kv parser.
    if _KV_BLOCK_RE.search(text):
        try:
            return _parse_kv_response(text)
        except ValueError:
            pass  # fall through to JSON path

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

    # Extract first { ... } block via brace matching (string-aware so braces
    # inside string values don't throw off the depth count).
    start = text.find("{")
    if start >= 0:
        depth = 0
        in_string = False
        escape = False
        for i in range(start, len(text)):
            c = text[i]
            if escape:
                escape = False
                continue
            if c == "\\":
                escape = True
                continue
            if c == '"':
                in_string = not in_string
                continue
            if in_string:
                continue
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[start:i + 1])
                    except json.JSONDecodeError:
                        break

    # Tolerant fallback: progressive prefix truncation. Local qwen3.5:4b
    # occasionally drops 1-2 closing braces in long structured outputs, with
    # the malformation often deep mid-document. Strategy:
    #   1. Find safe truncation points (string-aware positions of `},` or `}`)
    #   2. From the LAST one backwards, try truncating + balancing braces
    #   3. First successful parse wins (recovers everything UP TO the bad point)
    if start >= 0:
        body = text[start:]
        # Build list of safe truncation points: positions just after a `}` or
        # `},` (outside strings). These are likely end-of-object boundaries.
        safe_points: list[int] = []
        depth = 0
        in_string = False
        escape = False
        for i, c in enumerate(body):
            if escape:
                escape = False
                continue
            if c == "\\":
                escape = True
                continue
            if c == '"':
                in_string = not in_string
                continue
            if in_string:
                continue
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth >= 0:
                    safe_points.append(i + 1)  # position just past the `}`

        # Try truncating at each safe point from latest to earliest, balancing
        # open braces. Cap attempts at 30 to keep this O(N), not O(N²).
        for sp in reversed(safe_points[-30:]):
            candidate = body[:sp].rstrip().rstrip(",")
            # Count open vs close in this prefix (string-aware)
            d = 0
            in_s = False
            esc = False
            for c in candidate:
                if esc:
                    esc = False
                    continue
                if c == "\\":
                    esc = True
                    continue
                if c == '"':
                    in_s = not in_s
                    continue
                if in_s:
                    continue
                if c == "{":
                    d += 1
                elif c == "}":
                    d -= 1
            if d < 0 or d > 10:
                continue
            patched = candidate + ("}" * d)
            try:
                return json.loads(patched)
            except json.JSONDecodeError:
                continue

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

"""Judge prompt assembly (spec v1.5 §7.1).

Two prompt versions ship:

* **v1.0.0** — full template at `packs/core/judge_prompts/v1.0.0.md`
  with framework context, full UofA catalog reference, 6 verdict-class
  definitions, reasoning scaffold, and few-shot placeholders that get
  substituted from `specs/calibration/calibration_set_v1.jsonl` entries
  marked `is_canonical_few_shot: true`. This is the production prompt.

* **v0.1.0-tier-a** — inline minimal template (no framework context, no
  few-shots) used as a fall-back when the v1.0.0 file is missing or the
  calibration set has no canonical entries. Keeps tests + smoke runs
  working pre-calibration.

The split between `build_prompt_static_prefix()` and `build_prompt_for_case()`
exists so prompt-prefix caching (spec §9.1) works uniformly: the static
prefix is the cacheable portion (~12K tokens for v1.0.0, ~2K for the
fall-back), the per-case content is the variable portion (~3-5K tokens)
appended each call.
"""

from __future__ import annotations

import functools
import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Default version is v1.0.0; provider construction can override.
PROMPT_TEMPLATE_VERSION = "v1.0.0"
FALLBACK_VERSION = "v0.1.0-tier-a"

# Verdict classes paired with the placeholder name in v1.0.0.md.
_VERDICT_PLACEHOLDERS: dict[str, str] = {
    "CORRECT-DETECTION": "{{few_shot_correct_detection}}",
    "REAL-GAP": "{{few_shot_real_gap}}",
    "GENERATOR-ARTIFACT": "{{few_shot_generator_artifact}}",
    "EXISTING-RULE-MISBEHAVIOR": "{{few_shot_existing_rule_misbehavior}}",
    "OUT-OF-SCOPE": "{{few_shot_out_of_scope}}",
    "UNCERTAIN": "{{few_shot_uncertain}}",
}

# Inline fallback used when v1.0.0.md is missing.
_FALLBACK_PREFIX = """\
You are an expert in computational modeling and simulation credibility
assurance, evaluating synthetic evidence packages generated for the
Unit of Assurance (UofA) weakener catalog.

(Tier A fallback prompt; see packs/core/judge_prompts/v1.0.0.md for the
production template once the calibration set is populated.)

# Verdict classes

Choose ONE: CORRECT-DETECTION, REAL-GAP, GENERATOR-ARTIFACT,
EXISTING-RULE-MISBEHAVIOR, OUT-OF-SCOPE, UNCERTAIN.

# Reasoning scaffold (REQUIRED)

Populate `reasoning_steps` BEFORE committing the verdict:
  1. source_taxonomy_identified (≥10 chars)
  2. target_rule_identified (≥5 chars)
  3. rule_firings_inspected (≥10 chars)
  4. instantiation_check (≥20 chars)
  5. verdict_commitment (must match `verdict`)

# Output

Return a single JSON object conforming to the JudgeVerdictOutput schema.
Use temperature=0.0 and seed=42 (null if not honored).
"""


def _repo_root() -> Path:
    """Resolve the repo root from this module's location."""
    return Path(__file__).resolve().parents[4]


def _template_path(version: str) -> Path:
    return _repo_root() / "packs" / "core" / "judge_prompts" / f"{version}.md"


def _calibration_set_path() -> Path:
    return _repo_root() / "specs" / "calibration" / "calibration_set_v1.jsonl"


@functools.lru_cache(maxsize=4)
def _load_template_text(version: str) -> str | None:
    """Read the markdown template by version; return None if missing."""
    p = _template_path(version)
    if not p.exists():
        return None
    return p.read_text()


@functools.lru_cache(maxsize=2)
def _load_canonical_few_shots() -> dict[str, list[dict]]:
    """Load is_canonical_few_shot=true entries from the calibration set.

    Returns a dict mapping verdict class → list of canonical records.
    Empty dict if the file is missing or has no canonical entries.
    Cached so providers don't pay the disk read per call.
    """
    p = _calibration_set_path()
    if not p.exists():
        return {}
    out: dict[str, list[dict]] = {}
    for line in p.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not rec.get("is_canonical_few_shot"):
            continue
        verdict = rec.get("ground_truth_verdict")
        if not isinstance(verdict, str) or verdict.startswith("TODO_"):
            continue
        out.setdefault(verdict, []).append(rec)
    return out


def _render_few_shot_block(verdict: str, records: list[dict]) -> str:
    """Render a few-shot example block for one verdict class.

    Picks the FIRST canonical record per class (typically only one).
    Embeds: case_id, source_taxonomy, expected target rule, ground-truth
    verdict, ground-truth reasoning. Excludes the package content (too
    long for the prefix; case content goes in the per-case section).
    """
    if not records:
        return ""
    rec = records[0]
    case_id = rec.get("case_id", "<missing>")
    taxonomy = rec.get("source_taxonomy", "<missing>")
    target = rec.get("expected_target_rule") or "(none)"
    section = rec.get("ground_truth_section_6_7_candidate")
    section_str = f", §6.7 candidate {section}" if section else ""
    reasoning = rec.get("ground_truth_reasoning", "")

    return f"""
**Worked example ({case_id})** — verdict {verdict}{section_str}

Source taxonomy: `{taxonomy}` · Expected target rule: `{target}`

Reasoning: {reasoning}
"""


def _substitute_few_shots(template: str) -> str:
    """Replace `{{few_shot_*}}` placeholders with rendered examples.

    Placeholders without matching canonical entries are replaced with an
    empty-block notice so the prompt is still valid.
    """
    few_shots = _load_canonical_few_shots()
    out = template
    for verdict, placeholder in _VERDICT_PLACEHOLDERS.items():
        recs = few_shots.get(verdict, [])
        block = _render_few_shot_block(verdict, recs)
        if not block:
            block = (
                f"\n*(No canonical few-shot for {verdict} in the calibration "
                f"set yet. Mark one record with is_canonical_few_shot=true.)*\n"
            )
        out = out.replace(placeholder, block)
    return out


def build_prompt_static_prefix(
    *,
    template_version: str = PROMPT_TEMPLATE_VERSION,
) -> str:
    """Return the static, cacheable portion of the judge prompt.

    Loading order:
        1. Try `packs/core/judge_prompts/<version>.md`. If found,
           substitute few-shot placeholders from the calibration set.
        2. Fall back to the inline FALLBACK_PREFIX (no framework
           context, no few-shots) so tests + smoke runs still work
           pre-calibration.

    The version stamp at the end becomes part of the cache key (spec
    §9.1) — bumping the prompt invalidates the prefix cache.
    """
    text = _load_template_text(template_version)
    if text is None:
        logger.info(
            "prompt template %s not found; falling back to inline %s",
            template_version, FALLBACK_VERSION,
        )
        return _FALLBACK_PREFIX + f"\nTemplate version: {FALLBACK_VERSION}\n"
    return _substitute_few_shots(text) + f"\nTemplate version: {template_version}\n"


def build_prompt_for_case(case: dict) -> str:
    """Return the per-case (variable) portion of the judge prompt.

    `case` is a dict with at least:
        - case_id: str
        - coverage_class: normalized Phase 2 outcome class
        - phase2_outcome_class_raw: original Phase 2 class name
        - source_taxonomy: str
        - rules_fired: list[str]
        - expected_rule: str | None
        - section_6_7_mapping: str | None (revealed only at §11.3 reveal stage)
        - package: dict (the JSON-LD payload)

    The `section_6_7_mapping` is intentionally NOT shown in the prompt;
    spec §7.6 (anti-patterns) prohibits it as a verdict hint. It comes
    in via the §11.3 self-blinding reveal during author adjudication only.
    """
    case_id = case.get("case_id", "<missing>")
    coverage = case.get("coverage_class", "<missing>")
    raw_class = case.get("phase2_outcome_class_raw", coverage)
    source_taxonomy = case.get("source_taxonomy", "<missing>")
    rules_fired = case.get("rules_fired", [])
    expected = case.get("expected_rule") or "(none — gap_probe or negative_control)"

    package_text = _format_package(case.get("package", {}))

    return f"""

--- Case to judge ---

case_id: {case_id}
coverage_class (normalized): {coverage}
phase2_outcome_class_raw: {raw_class}
source_taxonomy: {source_taxonomy}
expected_target_rule: {expected}
rules_that_fired: {rules_fired}

--- Package (JSON-LD; package may be truncated for length) ---

{package_text}

--- Now produce the verdict ---

Use case_id={case_id} in the output. Populate reasoning_steps BEFORE
committing the verdict. Confidence in [0.0, 1.0]; reflect honest
uncertainty when the package is ambiguous.
"""


def _format_package(package: Any, *, max_chars: int = 12000) -> str:
    """Render the JSON-LD payload, truncating at a budget if very large."""
    if not isinstance(package, dict):
        return repr(package)
    text = json.dumps(package, indent=2, default=str, sort_keys=False)
    if len(text) <= max_chars:
        return text
    head = text[: max_chars - 100]
    return head + f"\n\n[... package truncated at {max_chars} chars ...]"


def clear_prompt_caches() -> None:
    """Clear the lru_caches; used by tests + when the calibration set changes."""
    _load_template_text.cache_clear()
    _load_canonical_few_shots.cache_clear()

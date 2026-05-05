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

# Default version is v1.1.0 (Phase 3 v1.6 productive-OOS framing);
# provider construction can override. v1.0.0 is retained in the repo
# for reproducibility of pre-v1.6 calibration runs.
PROMPT_TEMPLATE_VERSION = "v1.1.0"
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
    Embeds: anonymized case_id, source_taxonomy, expected target rule,
    ground-truth verdict, ground-truth reasoning, and (for OUT-OF-SCOPE)
    a sample evidence_gap object. Excludes the package content (too long
    for the prefix; case content goes in the per-case section).

    The case_id shown to the judge is anonymized (verdict tokens
    stripped) so the few-shot example doesn't reveal the labeling
    convention to the judge when the same convention is used for cases
    the judge must evaluate.
    """
    if not records:
        return ""
    rec = records[0]
    raw_case_id = rec.get("case_id", "<missing>")
    case_id = _sanitize_case_id(raw_case_id)
    taxonomy = rec.get("source_taxonomy", "<missing>")
    target = rec.get("expected_target_rule") or "(none)"
    section = rec.get("ground_truth_section_6_7_candidate")
    section_str = f", §6.7 candidate {section}" if section else ""
    reasoning = rec.get("ground_truth_reasoning", "")

    block = f"""
**Worked example ({case_id})** — verdict {verdict}{section_str}

Source taxonomy: `{taxonomy}` · Expected target rule: `{target}`

Reasoning: {reasoning}
"""

    # For OOS examples, include a sample evidence_gap so the model sees
    # the productive-OOS output shape. Drawn from the OOS package's
    # adversarialProvenance.evidenceGapDescription if available; otherwise
    # synthesized from the ground-truth reasoning.
    if verdict == "OUT-OF-SCOPE":
        gap_text = _extract_oos_evidence_gap(rec)
        if gap_text:
            block += f"\nevidence_gap exemplar:\n{gap_text}\n"

    return block


# Verdict-class tokens that may appear in the case_id and leak the
# answer to the judge (W1 in the calibration validator). Stripped from
# few-shot case_ids and from per-case prompts so the judge sees a
# neutral identifier.
_VERDICT_TOKENS_TO_STRIP = (
    "correct_detection",
    "real_gap",
    "generator_artifact",
    "existing_rule_misbehavior",
    "out_of_scope",
    "uncertain",
)


def _sanitize_case_id(case_id: str) -> str:
    """Strip verdict-class tokens from a calibration case_id (W1 leak fix).

    The calibration set's case_id convention `cal-NNN-<verdict_class>-<hint>`
    leaks the answer if shown to the judge verbatim. We replace the
    verdict-class segment with `_` so the case is still uniquely
    identifiable across the calibration set but the verdict token is
    gone.
    """
    if not case_id:
        return case_id
    out = case_id
    for token in _VERDICT_TOKENS_TO_STRIP:
        out = out.replace(token, "_")
    return out


def _extract_oos_evidence_gap(rec: dict) -> str | None:
    """Build an OOS evidence_gap exemplar from a calibration record.

    Reads the package file (if present) and pulls
    `adversarialProvenance.evidenceGapDescription`. Falls back to a
    paraphrase of the ground_truth_reasoning if the package can't be
    loaded.
    """
    pkg_path = rec.get("package_path")
    if pkg_path:
        full = Path(pkg_path)
        if not full.is_absolute():
            full = _repo_root() / pkg_path
        if full.exists():
            try:
                pkg = json.loads(full.read_text())
                prov = pkg.get("adversarialProvenance", {})
                missing_text = prov.get("evidenceGapDescription")
                if missing_text:
                    # Render as a JSON-shaped exemplar matching the
                    # output schema the judge will produce.
                    return (
                        '  "missing_evidence_type": '
                        f'{json.dumps(missing_text[:240])},\n'
                        '  "would_support_defeater_evaluation": '
                        f'{json.dumps(rec.get("source_taxonomy", "(in-scope defeater evaluation)"))}'
                    )
            except (json.JSONDecodeError, OSError):
                pass
    # Fallback: terse exemplar derived from the reasoning text.
    reasoning = rec.get("ground_truth_reasoning", "")
    return (
        '  "missing_evidence_type": "<see ground-truth reasoning>",\n'
        '  "would_support_defeater_evaluation": '
        f'{json.dumps(rec.get("source_taxonomy", "(in-scope defeater evaluation)"))}'
    )


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

    The `case_id` shown to the judge is anonymized: when `phase2_case_id`
    is present (Phase 2 corpus cases), we use that; otherwise we
    sanitize the calibration `case_id` to strip verdict-class tokens
    that would leak the answer (validator W1).
    """
    raw_case_id = case.get("case_id", "<missing>")
    # Anonymize the case_id for the prompt to avoid leaking the verdict
    # class encoded in the calibration set's case_id convention.
    phase2_id = case.get("phase2_case_id")
    if phase2_id:
        prompt_case_id = phase2_id
    else:
        prompt_case_id = _sanitize_case_id(raw_case_id)
    coverage = case.get("coverage_class", "<missing>")
    raw_class = case.get("phase2_outcome_class_raw", coverage)
    source_taxonomy = case.get("source_taxonomy", "<missing>")
    rules_fired = case.get("rules_fired", [])
    expected = case.get("expected_rule") or "(none — gap_probe or negative_control)"

    package_text = _format_package(case.get("package", {}))

    # The model echoes case_id back to us in its output. We tell it to
    # use the original raw_case_id (which downstream tooling indexes by);
    # the prompt body shows the anonymized form for context. Note: this
    # introduces a small leak surface — the judge reads the raw_case_id
    # in the "Use case_id=..." line. Mitigation: we instruct it to
    # IGNORE the verdict tokens in the case_id string when reasoning,
    # and the case_id is the LAST line of the prompt, after the package
    # content has anchored the judge's reasoning.
    return f"""

--- Case to judge ---

case_id: {prompt_case_id}
coverage_class (normalized): {coverage}
phase2_outcome_class_raw: {raw_class}
source_taxonomy: {source_taxonomy}
expected_target_rule: {expected}
rules_that_fired: {rules_fired}

--- Package (JSON-LD; package may be truncated for length) ---

{package_text}

--- Now produce the verdict ---

Populate reasoning_steps BEFORE committing the verdict. Confidence in
[0.0, 1.0]; reflect honest uncertainty when the package is ambiguous.
Echo the case_id verbatim in your output: {raw_case_id}

Note on case_id naming: any apparent verdict-class hints in the
case_id string (e.g. "_correct_detection_", "_real_gap_") are
data-organization labels from the calibration set scaffolder, NOT
ground truth. Disregard them; the verdict must come from your
reasoning over the package content + rule firings + source taxonomy.
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


# ── Judge E arbitration prompt (Phase 3 v1.6 §7.8) ─────────────────────


ARBITRATION_PROMPT_VERSION = "arbitration_v1.0.0"


def build_arbitration_prompt_static_prefix(
    *,
    template_version: str = ARBITRATION_PROMPT_VERSION,
) -> str:
    """Return the static, cacheable portion of the Judge E arbitration prompt.

    Loads `packs/core/judge_prompts/arbitration_v1.0.0.md` and substitutes
    few-shot placeholders from the calibration set canonical entries.
    """
    text = _load_template_text(template_version)
    if text is None:
        logger.info(
            "arbitration template %s not found; falling back to inline %s",
            template_version, FALLBACK_VERSION,
        )
        return _FALLBACK_PREFIX + f"\nTemplate version: {FALLBACK_VERSION}\n"
    return _substitute_few_shots(text) + f"\nTemplate version: {template_version}\n"


def build_arbitration_prompt_for_case(
    case: dict,
    production_verdicts: list[dict],
) -> str:
    """Per-case section for Judge E arbitration.

    `case` is the same shape as the production-judge per-case input.
    `production_verdicts` is a list of three dicts (one per production
    judge in canonical A/B/C order) with at least:
      - judge_position: 'A' | 'B' | 'C'
      - judge_model: str
      - verdict: str (one of the 6 spec classes)
      - confidence: float
      - reasoning_steps: dict[str, str]
      - reasoning: str

    Per spec §7.8 anti-patterns, this prompt does NOT include Judge D's
    calibration verdict for the specific case being arbitrated.
    """
    raw_case_id = case.get("case_id", "<missing>")
    phase2_id = case.get("phase2_case_id")
    prompt_case_id = phase2_id if phase2_id else _sanitize_case_id(raw_case_id)
    coverage = case.get("coverage_class", "<missing>")
    raw_class = case.get("phase2_outcome_class_raw", coverage)
    source_taxonomy = case.get("source_taxonomy", "<missing>")
    rules_fired = case.get("rules_fired", [])
    expected = case.get("expected_rule") or "(none — gap_probe or negative_control)"
    package_text = _format_package(case.get("package", {}))

    judge_block = _format_production_judge_summary(production_verdicts)

    return f"""

--- Case to arbitrate ---

case_id: {prompt_case_id}
coverage_class (normalized): {coverage}
phase2_outcome_class_raw: {raw_class}
source_taxonomy: {source_taxonomy}
expected_target_rule: {expected}
rules_that_fired: {rules_fired}

--- Production-judge verdicts (the three judges have failed majority-of-3 at confidence ≥ 0.6) ---

{judge_block}

--- Package (JSON-LD; package may be truncated for length) ---

{package_text}

--- Arbitrate ---

Form your own verdict from the package + rule firings + source taxonomy.
Then assess each production judge's reasoning quality
(production_judge_evaluation: sound | weak | irrelevant per judge).
Set arbitration_basis to package_content, production_judge_evaluation,
or independent_disagreement per the prompt instructions.

Echo the case_id verbatim in your output: {raw_case_id}

Your output must conform to the JudgeEArbitrationOutput schema. If your
verdict is OUT-OF-SCOPE, the evidence_gap field is required.
"""


def _format_production_judge_summary(verdicts: list[dict]) -> str:
    """Side-by-side rendering of the three production-judge verdicts."""
    if not verdicts:
        return "(no production verdicts provided — invalid arbitration input)"
    lines = []
    for v in verdicts:
        pos = v.get("judge_position", "?")
        model = v.get("judge_model", "<unknown>")
        verdict = v.get("verdict", "<missing>")
        conf = v.get("confidence", "?")
        rs = v.get("reasoning_steps", {})
        reasoning = v.get("reasoning", "")
        lines.append(f"### Judge {pos} ({model})\n")
        lines.append(f"Verdict: {verdict}  ·  Confidence: {conf}\n")
        lines.append("Reasoning steps:")
        for k, val in rs.items():
            lines.append(f"  - {k}: {val}")
        lines.append(f"\nReasoning: {reasoning}\n")
    return "\n".join(lines)

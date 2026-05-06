"""Verify specs/judge_output_schema.json is accepted by OpenAI strict mode.

Run this BEFORE building Phase 3 judge providers (Wave 1 of the impl plan).
Confirms the schema is structurally compatible with OpenAI structured outputs
(`response_format={'type':'json_schema', 'strict':true}`) and that a real model
can produce a response that validates against it via jsonschema.

Cost: one OpenAI call against `gpt-4o` (~$0.01 with thinking off, no caching).
gpt-4o is used instead of `gpt-5.4` for cost; strict-mode acceptance criteria
are model-agnostic at the schema-shape level.

Usage:
    OPENAI_API_KEY=sk-... python dev/tools/scripts/verify_openai_strict_schema.py

Exit codes:
    0  PASS — schema accepted, response valid
    1  FAIL — strict-mode rejection or validation error (details printed)
    2  ENV — OPENAI_API_KEY missing or `pip install uofa[judge]` not done
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path


# Synthetic case the judge is asked to verdict against. Deliberately
# unambiguous (a clear REAL-GAP) so a sane response should pass schema
# validation without invoking real Phase 2 corpus content.
SAMPLE_USER_PROMPT = """You are evaluating a single synthetic credibility evidence package for the
Unit of Assurance (UofA) weakener catalog.

Case id: cal-001-real-gap-data-drift
Source taxonomy: Gohar (2025) / Evidence Validity / Data Drift
Phase 2 outcome: COV-MISS (no rules fired)
Expected target: W-EV-01 (Stale validation data) — not yet in catalog

Package excerpt:
- Validation dataset vintage: 2018
- Model revision: 2024
- Re-calibration activity: none recorded

Decide one of the six verdicts: CORRECT-DETECTION, REAL-GAP, GENERATOR-ARTIFACT,
EXISTING-RULE-MISBEHAVIOR, OUT-OF-SCOPE, UNCERTAIN.

Populate the reasoning_steps scaffold before committing the verdict. Use
prompt_template_version='v0.0.0-verify', judge_model='gpt-4o',
judge_thinking_enabled=false, temperature=0.0, seed=42, and report
generator_provenance.generator_model='anthropic/claude-sonnet-4-6'."""


def _repo_root() -> Path:
    """Resolve the repo root from this script's location."""
    return Path(__file__).resolve().parents[3]


def _load_schema() -> dict:
    schema_path = _repo_root() / "specs" / "judge_output_schema.json"
    if not schema_path.exists():
        print(f"ENV: schema not found at {schema_path}", file=sys.stderr)
        sys.exit(2)
    return json.loads(schema_path.read_text())


def _check_env() -> None:
    if not os.environ.get("OPENAI_API_KEY"):
        print("ENV: OPENAI_API_KEY not set; export your key and re-run.", file=sys.stderr)
        sys.exit(2)
    try:
        import openai  # noqa: F401
        import jsonschema  # noqa: F401
    except ImportError as e:
        print(f"ENV: missing dep ({e.name}). Run `pip install uofa[judge]`.", file=sys.stderr)
        sys.exit(2)


def main() -> int:
    _check_env()
    schema = _load_schema()

    from openai import OpenAI
    import jsonschema

    client = OpenAI()

    print("→ Submitting strict-mode call to gpt-4o...")
    try:
        completion = client.chat.completions.create(
            model="gpt-4o",
            temperature=0.0,
            seed=42,
            messages=[
                {"role": "system", "content": "You output strictly-typed JSON per the provided schema."},
                {"role": "user", "content": SAMPLE_USER_PROMPT},
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "judge_verdict_output",
                    "strict": True,
                    "schema": schema,
                },
            },
        )
    except Exception as e:
        # OpenAI strict-mode rejections come back as BadRequestError with the
        # offending property in the body. Print the full error so the schema
        # author sees exactly what to fix.
        print(f"FAIL: OpenAI rejected the schema or call.\n  {type(e).__name__}: {e}", file=sys.stderr)
        return 1

    raw = completion.choices[0].message.content
    if not raw:
        print("FAIL: empty response from OpenAI.", file=sys.stderr)
        return 1

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"FAIL: response is not valid JSON ({e}).\n  body: {raw[:500]}", file=sys.stderr)
        return 1

    try:
        jsonschema.validate(parsed, schema)
    except jsonschema.ValidationError as e:
        print(f"FAIL: response did not validate against schema.\n  path: {list(e.absolute_path)}\n  msg: {e.message}", file=sys.stderr)
        return 1

    print("PASS: schema accepted, response valid against jsonschema.")
    print(f"  case_id: {parsed['case_id']}")
    print(f"  verdict: {parsed['verdict']} (confidence {parsed['confidence']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())

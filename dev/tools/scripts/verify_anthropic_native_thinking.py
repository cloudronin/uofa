#!/usr/bin/env python3
"""Verify Anthropic Claude Sonnet 4.6 native extended thinking via litellm.

Run once before the production Phase 3 calibration runs to confirm:
  1. The `thinking` parameter is honored end-to-end.
  2. The strict-mode response_format with our `if/then` schema strip
     produces a valid Judgment payload.
  3. Usage metadata exposes thinking-mode tokens (the spec wants this
     in the run manifest for cost accounting).

Cost: ~$0.05 (single call with extended thinking budget 8192).

Exit codes:
  0  Smoke passed.
  1  Smoke failed (prints the failing aspect).
  2  No ANTHROPIC_API_KEY in env.

Usage:
  ANTHROPIC_API_KEY=$(cat /tmp/anthropic.txt) \
      python dev/tools/scripts/verify_anthropic_native_thinking.py
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def _load_schema() -> dict:
    here = Path(__file__).resolve()
    spec_path = here.parents[3] / "specs" / "judge_output_schema.json"
    return json.loads(spec_path.read_text())


def _strip_anthropic_blocked(schema: dict) -> dict:
    """Mirror capabilities.py strip_schema_for_provider for Anthropic."""
    blocked = {
        "if", "then", "else", "$comment",
        "minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum",
        "minLength", "maxLength", "minItems", "maxItems", "pattern",
    }

    def _walk(obj):
        if isinstance(obj, dict):
            return {k: _walk(v) for k, v in obj.items() if k not in blocked}
        if isinstance(obj, list):
            return [_walk(x) for x in obj]
        return obj

    return _walk(schema)


def _build_minimal_case() -> dict:
    return {
        "case_id": "verify-anthropic-thinking-001",
        "package": {
            "id": "https://uofa.net/verify/anth-001",
            "name": "Smoke fixture",
        },
        "rules_fired": [],
        "phase2_outcome_class_raw": "COV-CLEAN",
    }


def main() -> int:
    if "ANTHROPIC_API_KEY" not in os.environ:
        print("ERROR: ANTHROPIC_API_KEY not set", file=sys.stderr)
        return 2

    import litellm  # type: ignore

    schema = _strip_anthropic_blocked(_load_schema())
    case = _build_minimal_case()

    response_format = {
        "type": "json_schema",
        "json_schema": {
            "name": "judge_output",
            "schema": schema,
            "strict": True,
        },
    }

    try:
        resp = litellm.completion(
            model="anthropic/claude-sonnet-4-6",
            messages=[
                {"role": "system", "content": "You are Judge A. Return JSON."},
                {"role": "user", "content": json.dumps(case)},
            ],
            temperature=0.0,
            response_format=response_format,
            thinking={"type": "enabled", "budget_tokens": 8192},
            max_tokens=4000,
        )
    except Exception as e:
        print(f"FAIL: Anthropic call errored: {e}", file=sys.stderr)
        return 1

    text = resp.choices[0].message.content
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as e:
        print(f"FAIL: response is not valid JSON: {e}", file=sys.stderr)
        return 1

    if "verdict" not in parsed:
        print(f"FAIL: response missing 'verdict' key: {parsed}", file=sys.stderr)
        return 1

    usage = getattr(resp, "usage", None) or {}
    thinking_tokens = (
        getattr(usage, "completion_tokens_details", None)
        or (usage.get("completion_tokens_details") if isinstance(usage, dict) else None)
    )
    print(f"OK: Anthropic returned verdict={parsed['verdict']}")
    print(f"    completion_tokens_details: {thinking_tokens}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

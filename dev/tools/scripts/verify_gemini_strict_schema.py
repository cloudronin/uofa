#!/usr/bin/env python3
"""Verify Gemini 3.1 Pro accepts our judge_output_schema in strict mode.

Run once when GEMINI_API_KEY is provisioned to confirm the capability
table's schema transforms (drop if/then/else + nullable-array →
OpenAPI-3 form) produce a schema Gemini's protobuf-derived parser
accepts.

Cost: ~$0.02 (single call against the Gemini default model from the
capability table; currently `gemini-2.5-pro` per the substitution
documented in TIER_A_HANDOFF.md).

Exit codes:
  0  Gemini accepted the transformed schema and returned a valid response.
  1  Gemini rejected the schema; prints the rejected fragment for the
     capability-table update.
  2  No GEMINI_API_KEY in env.

Usage:
  GEMINI_API_KEY=$(cat /tmp/gemini.txt) \
      python dev/tools/scripts/verify_gemini_strict_schema.py
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


def _strip_for_gemini(schema: dict) -> dict:
    """Apply the capability-table transforms before sending."""
    here = Path(__file__).resolve()
    src = here.parents[3] / "src"
    sys.path.insert(0, str(src))
    from uofa_cli.adversarial.judge.providers.capabilities import (
        strip_schema_for_provider,
    )
    return strip_schema_for_provider(schema, "gemini")


def _build_minimal_case() -> dict:
    return {
        "case_id": "cal-901-gemini-smoke",
        "package": {
            "id": "https://uofa.net/verify/gemini-001",
            "name": "Smoke fixture",
        },
        "rules_fired": [],
        "phase2_outcome_class_raw": "COV-CLEAN",
    }


def main() -> int:
    if "GEMINI_API_KEY" not in os.environ:
        print("ERROR: GEMINI_API_KEY not set in environment", file=sys.stderr)
        return 2

    import litellm  # type: ignore

    schema = _strip_for_gemini(_load_schema())
    case = _build_minimal_case()

    response_format = {
        "type": "json_schema",
        "json_schema": {
            "name": "judge_output",
            "schema": schema,
            "strict": True,
        },
    }

    # Pull the default Gemini model from the capability table so this
    # script tracks any future model bumps without manual edits.
    from uofa_cli.adversarial.judge.providers.capabilities import (
        litellm_model_string,
    )
    gemini_model = litellm_model_string("gemini")

    try:
        resp = litellm.completion(
            model=gemini_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are Judge B (Gemini) for the UofA "
                        "credibility-package judge ensemble. Return JSON "
                        "matching the schema."
                    ),
                },
                {"role": "user", "content": json.dumps(case)},
            ],
            temperature=0.0,
            response_format=response_format,
            max_tokens=4000,
        )
    except Exception as e:
        print(f"FAIL: Gemini rejected the schema: {e}", file=sys.stderr)
        return 1

    text = resp.choices[0].message.content
    parsed = json.loads(text)
    print(f"OK: Gemini accepted the schema; verdict={parsed.get('verdict')}")
    if parsed.get("verdict") == "OUT-OF-SCOPE":
        gap = parsed.get("evidence_gap") or {}
        if gap:
            print(
                f"   evidence_gap: missing_type={gap.get('missing_evidence_type')!r}"
            )
    return 0


if __name__ == "__main__":
    sys.exit(main())

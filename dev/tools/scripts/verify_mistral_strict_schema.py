#!/usr/bin/env python3
"""Verify Mistral large-2 accepts our judge_e_output_schema in strict mode.

Run once when MISTRAL_API_KEY is provisioned to populate the
`schema_keyword_blocklist` for Mistral in
`src/uofa_cli/adversarial/judge/providers/capabilities.py` if any
keywords need stripping.

Cost: ~$0.01 (single call against mistral-large-2 with our schema and
a small one-case prompt).

Exit codes:
  0  Mistral accepted the schema and returned a valid response.
  1  Mistral rejected the schema; prints the rejected keywords for the
     blocklist update.
  2  No MISTRAL_API_KEY in env.

Usage:
  MISTRAL_API_KEY=$(cat /tmp/mistral.txt) \
      python dev/tools/scripts/verify_mistral_strict_schema.py
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def _load_schema() -> dict:
    """Load the Judge E schema from the canonical location."""
    here = Path(__file__).resolve()
    spec_path = here.parents[3] / "specs" / "judge_e_output_schema.json"
    return json.loads(spec_path.read_text())


def _strip_for_mistral(schema: dict) -> dict:
    """Apply the capability-table blocklist before sending."""
    here = Path(__file__).resolve()
    src = here.parents[3] / "src"
    sys.path.insert(0, str(src))
    from uofa_cli.adversarial.judge.providers.capabilities import (
        strip_schema_for_provider,
    )
    return strip_schema_for_provider(schema, "mistral")


def _build_minimal_arbitration_case() -> dict:
    """A tiny one-case fixture so the smoke runs at minimum cost."""
    return {
        "case_id": "verify-mistral-001",
        "package": {
            "id": "https://uofa.net/verify/mistral-001",
            "name": "Smoke-test package for Mistral schema acceptance",
        },
        "rules_fired": [],
        "production_verdicts": [
            {"position": "A", "verdict": "REAL-GAP", "confidence": 0.7,
             "reasoning": "smoke fixture A"},
            {"position": "B", "verdict": "GENERATOR-ARTIFACT", "confidence": 0.7,
             "reasoning": "smoke fixture B"},
            {"position": "C", "verdict": "OUT-OF-SCOPE", "confidence": 0.7,
             "reasoning": "smoke fixture C"},
        ],
    }


def main() -> int:
    if "MISTRAL_API_KEY" not in os.environ:
        print("ERROR: MISTRAL_API_KEY not set in environment", file=sys.stderr)
        return 2

    import litellm  # type: ignore

    schema = _strip_for_mistral(_load_schema())
    case = _build_minimal_arbitration_case()

    response_format = {
        "type": "json_schema",
        "json_schema": {
            "name": "judge_e_output",
            "schema": schema,
            "strict": True,
        },
    }

    try:
        resp = litellm.completion(
            model="mistral/mistral-large-latest",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are Judge E (arbiter) for the UofA "
                        "credibility-package judge ensemble. Return JSON "
                        "matching the schema."
                    ),
                },
                {"role": "user", "content": json.dumps(case)},
            ],
            temperature=0.0,
            response_format=response_format,
            max_tokens=1500,
        )
    except Exception as e:
        print(f"FAIL: Mistral rejected the schema: {e}", file=sys.stderr)
        # Heuristic blocklist extraction — common error formats.
        msg = str(e).lower()
        candidates = [
            "if", "then", "else", "$comment", "minimum", "maximum",
            "minlength", "maxlength", "minitems", "maxitems",
            "exclusiveminimum", "exclusivemaximum", "pattern",
        ]
        rejected = [c for c in candidates if c in msg]
        if rejected:
            print(f"  Suggested schema_keyword_blocklist: {rejected}")
        return 1

    text = resp.choices[0].message.content
    parsed = json.loads(text)
    print(f"OK: Mistral accepted the schema; verdict={parsed.get('verdict')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Verify Llama 4 Maverick via HF Router (Sambanova) returns parseable JSON.

The HF-hosted Llama judge runs through litellm's openai-compat path
with `api_base=https://router.huggingface.co/v1` and the HF Router's
`<model>:provider` model id format. This smoke confirms:
  1. The capability table's auth_env_var + litellm_api_base wiring
     produces a successful chat completion against the Router.
  2. response_format json_object yields valid JSON the runtime parser
     can ingest (Llama 4 Maverick doesn't enforce strict-mode schema
     server-side, so the tolerant parser is the actual contract).
  3. The expected verdict-class enum is honored when prompted.

Cost: ~$0.005 (one short call against Sambanova-hosted Llama 4 Maverick).

Exit codes:
  0  Smoke passed.
  1  Call errored or response failed JSON parse.
  2  No HF_TOKEN / HUGGINGFACE_API_KEY in env.

Usage:
  HF_TOKEN=$(cat /tmp/huggingface.txt) \
      python dev/tools/scripts/verify_hf_llama_inference.py
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def _build_minimal_case() -> dict:
    return {
        "case_id": "cal-901-llama-smoke",
        "package": {
            "id": "https://uofa.net/verify/llama-001",
            "name": "Smoke fixture",
        },
        "rules_fired": [],
        "phase2_outcome_class_raw": "COV-CLEAN",
    }


def main() -> int:
    api_key = os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_API_KEY")
    if not api_key:
        print("ERROR: HF_TOKEN or HUGGINGFACE_API_KEY required", file=sys.stderr)
        return 2

    # Pick up the capability defaults so this smoke matches what the
    # production path actually sends.
    here = Path(__file__).resolve()
    sys.path.insert(0, str(here.parents[3] / "src"))
    from uofa_cli.adversarial.judge.providers.capabilities import (
        get_capabilities,
        litellm_model_string,
    )

    caps = get_capabilities("hf-llama")
    model = litellm_model_string("hf-llama")

    import litellm  # type: ignore
    case = _build_minimal_case()

    try:
        resp = litellm.completion(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are Judge C (Llama 4 Maverick). Return ONLY a "
                        "JSON object with keys case_id, verdict, confidence, "
                        "reasoning. verdict must be one of "
                        "CORRECT-DETECTION REAL-GAP GENERATOR-ARTIFACT "
                        "EXISTING-RULE-MISBEHAVIOR OUT-OF-SCOPE UNCERTAIN."
                    ),
                },
                {"role": "user", "content": json.dumps(case)},
            ],
            max_tokens=600,
            temperature=0.0,
            response_format={"type": "json_object"},
            api_base=caps.litellm_api_base,
            api_key=api_key,
        )
    except Exception as e:
        print(f"FAIL: HF Router call errored: {e}", file=sys.stderr)
        return 1

    text = resp.choices[0].message.content or ""
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as e:
        print(f"FAIL: response is not valid JSON: {e}\n{text[:200]}", file=sys.stderr)
        return 1

    verdict = parsed.get("verdict")
    valid = {
        "CORRECT-DETECTION", "REAL-GAP", "GENERATOR-ARTIFACT",
        "EXISTING-RULE-MISBEHAVIOR", "OUT-OF-SCOPE", "UNCERTAIN",
    }
    if verdict not in valid:
        print(f"FAIL: verdict {verdict!r} not in expected enum", file=sys.stderr)
        return 1
    print(f"OK: HF Router -> Llama 4 Maverick returned verdict={verdict}")
    print(f"    model={model}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

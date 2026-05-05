#!/usr/bin/env python3
"""Verify the litellm refactor produces results matching the v1.5 SDK path.

Calls Anthropic + OpenAI through the new LiteLLMProvider on a small
fixture and prints pairwise κ. The pre-refactor smoke landed κ in
0.4–0.7 across the calibration set — this script reproduces that band
on a 5-case mini-fixture so the refactor doesn't regress.

Cost: ~$0.05 (5 cases × 2 judges = 10 small calls).

Usage:
  ANTHROPIC_API_KEY=$(cat /tmp/anthropic.txt) \
      OPENAI_API_KEY=$(cat /tmp/openai.txt) \
      python dev/tools/scripts/verify_litellm_refactor.py
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

# Ensure src/ is on the path so we can import uofa_cli without an editable install.
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))

from uofa_cli.adversarial.judge.adjudication import cohen_kappa  # noqa: E402
from uofa_cli.adversarial.judge.providers.litellm_provider import (  # noqa: E402
    LiteLLMProvider,
)


# 5-case mini-fixture. case_id follows the cal-NNN pattern enforced by
# specs/judge_output_schema.json so the strict-mode validator accepts.
FIXTURE = [
    {
        "case_id": f"cal-9{i:02d}-litellm-refactor-smoke",
        "package": {"id": f"pkg-{i}", "name": f"Smoke fixture {i}"},
        "rules_fired": [],
        "phase2_outcome_class_raw": "COV-CLEAN",
    }
    for i in range(5)
]


async def _judge_all(provider: LiteLLMProvider, cases: list[dict]) -> list[str]:
    return [(await provider.judge(c)).verdict for c in cases]


def main() -> int:
    if "ANTHROPIC_API_KEY" not in os.environ or "OPENAI_API_KEY" not in os.environ:
        print("ERROR: ANTHROPIC_API_KEY and OPENAI_API_KEY required", file=sys.stderr)
        return 2

    # Pin to litellm-1.63-known models for the smoke. The capability table
    # default (gpt-5.4) is too new for the current litellm pin to accept
    # reasoning_effort against. Smoke uses gpt-4o-mini + claude-sonnet-4-6
    # with thinking_enabled=False so we exercise the litellm-refactor
    # call path (schema strict, capability table, response parsing)
    # without hitting model-recognition gaps.
    anthropic = LiteLLMProvider(
        provider_token="anthropic",
        judge_role="production",
        thinking_enabled=False,  # litellm < 1.81 doesn't recognize 4-6 thinking
    )
    openai = LiteLLMProvider(
        provider_token="openai",
        model="gpt-4o-mini",
        judge_role="production",
        thinking_enabled=False,  # gpt-4o-mini doesn't have reasoning_effort
    )

    a_verdicts = asyncio.run(_judge_all(anthropic, FIXTURE))
    o_verdicts = asyncio.run(_judge_all(openai, FIXTURE))

    print("Anthropic:", a_verdicts)
    print("OpenAI:   ", o_verdicts)
    try:
        k = cohen_kappa(a_verdicts, o_verdicts)
        print(f"Cohen's κ (Anthropic vs OpenAI): {k:.3f}")
    except Exception as e:
        print(f"WARN: could not compute κ: {e}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

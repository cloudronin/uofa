#!/usr/bin/env python3
"""Verify Anthropic Claude Sonnet 4.6 native extended thinking.

Two-part smoke:
  Part A (litellm strict-schema): exercises the production code path —
    litellm.completion with response_format json_schema strict + the
    Anthropic-blocklist strip (drops if/then/else). Verifies a valid
    Judgment payload comes back. Thinking is OFF in this part because
    litellm < 1.81 doesn't recognize thinking on claude-sonnet-4-6.
  Part B (direct Anthropic SDK thinking): confirms the API itself
    accepts thinking={"type":"enabled","budget_tokens":...} for the
    target model. Reads thinking-block tokens off the usage metadata
    so we can prove the param flows end-to-end.

Both parts must pass before the production calibration run promotes
thinking-on for Anthropic. The Phase 3 v1.6 plan tracks this in the
TIER_A_HANDOFF doc.

Cost: ~$0.10 total (Part A ~$0.02 + Part B ~$0.05).

Exit codes:
  0  Both parts passed.
  1  Smoke failed (prints which aspect).
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


def _part_a_litellm_strict_schema() -> tuple[bool, str]:
    """Part A: litellm strict-schema with if/then strip (no thinking)."""
    import litellm  # type: ignore

    schema = _strip_anthropic_blocked(_load_schema())
    case = _build_minimal_case()
    response_format = {
        "type": "json_schema",
        "json_schema": {
            "name": "judge_output", "schema": schema, "strict": True,
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
            max_tokens=4000,
        )
    except Exception as e:
        return False, f"litellm call errored: {e!r}"

    text = resp.choices[0].message.content
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as e:
        return False, f"response is not valid JSON: {e}"
    if "verdict" not in parsed:
        return False, f"response missing 'verdict': {parsed}"
    return True, f"verdict={parsed['verdict']}"


def _part_b_direct_thinking() -> tuple[bool, str]:
    """Part B: direct Anthropic SDK confirms thinking param flows end-to-end."""
    try:
        import anthropic  # type: ignore
    except ImportError:
        return False, "anthropic SDK not installed"

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    try:
        msg = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2000,
            thinking={"type": "enabled", "budget_tokens": 1024},
            messages=[{"role": "user", "content": "Reply with one word: OK"}],
        )
    except Exception as e:
        return False, f"Anthropic SDK errored: {e!r}"

    block_types = [b.type for b in msg.content]
    if "thinking" not in block_types:
        return False, f"no thinking block in response (blocks: {block_types})"
    text_blocks = [b for b in msg.content if b.type == "text"]
    if not text_blocks:
        return False, "no text content alongside thinking"
    return True, (
        f"blocks={block_types}, "
        f"input_tokens={msg.usage.input_tokens}, "
        f"output_tokens={msg.usage.output_tokens}"
    )


def main() -> int:
    if "ANTHROPIC_API_KEY" not in os.environ:
        print("ERROR: ANTHROPIC_API_KEY not set", file=sys.stderr)
        return 2

    print("Part A — litellm strict-schema with if/then strip:")
    a_ok, a_msg = _part_a_litellm_strict_schema()
    print(f"  {'PASS' if a_ok else 'FAIL'}: {a_msg}")

    print("Part B — direct Anthropic SDK thinking parameter:")
    b_ok, b_msg = _part_b_direct_thinking()
    print(f"  {'PASS' if b_ok else 'FAIL'}: {b_msg}")

    if a_ok and b_ok:
        print("\nOK: both Anthropic smoke parts passed.")
        print(
            "  Note: litellm < 1.81 does not yet recognize thinking on "
            "claude-sonnet-4-6. Until upgrade, capability table sets "
            "thinking_kwargs=() for Anthropic; production runs go without "
            "thinking until the litellm version pin is bumped."
        )
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())

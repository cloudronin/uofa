#!/usr/bin/env python3
"""Re-run UNCERTAIN candidate sampling with thinking-mode enabled.

Bypasses litellm (which doesn't recognize claude-sonnet-4-6 thinking
yet) by calling the Anthropic SDK directly. Tests whether extended
thinking changes Judge D's verdict distribution from "always commits
to non-UNCERTAIN with hedge language" to "produces UNCERTAIN on
genuinely ambiguous cases".

Cost: ~$1.50 (10 candidates × thinking-mode at ~$0.15/case).

Usage:
  ANTHROPIC_API_KEY=$(cat /tmp/anthropic.txt) \
      python dev/tools/scripts/sample_uncertain_with_thinking.py \
          --bundle dev/build/adversarial/phase2/2026-04-26/judge_ready_bundle.tgz \
          --n-candidates 10
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[3] / "src"))

from uofa_cli.adversarial.judge.bundle import open_bundle  # noqa: E402
from uofa_cli.adversarial.judge.prompts import (  # noqa: E402
    build_prompt_for_case,
    build_prompt_static_prefix,
)


def _existing_phase2_ids() -> set[str]:
    path = Path("specs/calibration/calibration_set_v1.jsonl")
    if not path.exists():
        return set()
    out: set[str] = set()
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        pcid = rec.get("phase2_case_id")
        if pcid:
            out.add(pcid)
    return out


def _select_candidates(bundle_path: Path, n: int) -> list[dict]:
    excluded = _existing_phase2_ids()
    out = []
    with open_bundle(bundle_path) as bundle:
        for entry in bundle.iter_entries():
            if entry.case_id in excluded:
                continue
            outcome_class = (
                entry.outcome.get("phase2_outcome_class_raw")
                or entry.outcome.get("coverage_class")
            )
            if outcome_class not in {"COV-WRONG", "COV-CLEAN-WRONG"}:
                continue
            rules_fired = entry.outcome.get("rules_fired") or []
            if len(set(rules_fired)) < 5:
                continue
            out.append({
                "case_id": entry.case_id,
                "phase2_case_id": entry.case_id,
                "package": entry.package,
                "outcome": dict(entry.outcome),
            })
            if len(out) >= n:
                break
    return out


async def _call_anthropic_with_thinking(
    client, prefix: str, per_case: str, schema: dict
) -> dict:
    """Direct Anthropic SDK call with thinking enabled. Returns parsed JSON."""
    # Anthropic message-batches doesn't expose a json_schema response_format
    # like OpenAI does; the API accepts a schema in the system message
    # and returns text that the caller parses. We rely on prompt-level
    # structure (the v1.1.0 prompt instructs JSON output) + the tolerant
    # parser pattern.
    msg = await asyncio.to_thread(
        client.messages.create,
        model="claude-sonnet-4-6",
        max_tokens=8000,
        thinking={"type": "enabled", "budget_tokens": 4096},
        messages=[
            {"role": "user", "content": per_case},
        ],
        system=prefix,
    )
    # Extract text content (skip thinking blocks).
    text_blocks = [b for b in msg.content if b.type == "text"]
    if not text_blocks:
        raise RuntimeError("no text content in thinking-mode response")
    text = text_blocks[0].text
    # Tolerant parse — the model emits JSON-shaped output but may have
    # leading/trailing prose. Use the same parser as LiteLLMProvider.
    from uofa_cli.llm_extractor import _parse_response as tolerant_parse
    return tolerant_parse(text)


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--n-candidates", type=int, default=10)
    parser.add_argument(
        "--out", type=Path,
        default=Path("dev/build/adversarial/phase3/uncertain_candidates_thinking/"),
    )
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    if "ANTHROPIC_API_KEY" not in os.environ:
        print("ERROR: ANTHROPIC_API_KEY required", file=sys.stderr)
        return 2

    import anthropic  # type: ignore
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    candidates = _select_candidates(Path(args.bundle), args.n_candidates)
    print(f"Selected {len(candidates)} candidates")

    prefix = build_prompt_static_prefix(template_version="v1.1.0")
    schema_path = Path("specs/judge_output_schema.json")
    schema = json.loads(schema_path.read_text())

    results = []
    for i, c in enumerate(candidates, 1):
        case_for_judge = {
            "case_id": c["case_id"],
            "phase2_case_id": c["phase2_case_id"],
            "source_taxonomy": c["outcome"].get("source_taxonomy"),
            "rules_fired": c["outcome"].get("rules_fired", []),
            "expected_rule": c["outcome"].get("expected_rule"),
            "section_6_7_mapping": c["outcome"].get("section_6_7_mapping"),
            "phase2_outcome_class_raw": c["outcome"].get(
                "phase2_outcome_class_raw"
            ) or c["outcome"].get("coverage_class"),
            "package": c["package"],
        }
        per_case = build_prompt_for_case(case_for_judge)
        t0 = time.perf_counter()
        try:
            parsed = await _call_anthropic_with_thinking(
                client, prefix, per_case, schema
            )
            verdict = parsed.get("verdict")
            confidence = parsed.get("confidence")
            reasoning = parsed.get("reasoning", "")
            print(f"  #{i:02d} {c['case_id'][:50]:50s} verdict={verdict!r:25s} conf={confidence}")
            results.append({
                "case_id": c["case_id"],
                "phase2_case_id": c["phase2_case_id"],
                "verdict": verdict,
                "confidence": confidence,
                "reasoning": reasoning,
                "raw": parsed,
                "latency_s": time.perf_counter() - t0,
            })
        except Exception as e:
            print(f"  #{i:02d} {c['case_id'][:50]:50s} FAIL: {e!r}")
            results.append({
                "case_id": c["case_id"],
                "phase2_case_id": c["phase2_case_id"],
                "verdict": None,
                "error": repr(e)[:300],
            })

    raw_path = args.out / "uncertain_candidates_thinking_raw.jsonl"
    with raw_path.open("w") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")

    counter = Counter(r.get("verdict") for r in results)
    print(f"\nVerdict distribution (thinking-mode): {dict(counter)}")
    print(f"Wrote {raw_path}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

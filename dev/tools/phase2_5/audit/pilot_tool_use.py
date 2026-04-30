"""Phase 2 v3 Phase A pilot — Anthropic tool-use generation test.

Generates 5 NC packages using the new tool-use API to validate:

1. **Parse-as-JSON rate**: Anthropic SDK parses the tool ``input``
   field; rate should be 100% (vs ~95% on free-form text).
2. **SHACL pass rate**: ≥ 80% (some retries expected even with tool
   use).
3. **Token cost**: ≤ 30% overhead vs free-form baseline.

Uses NC-2 (Minimal Morrison COU1) as the simplest archetype — least
content, fastest iteration, lowest cost (~$0.20-0.50 per package).

Usage:

    export ANTHROPIC_API_KEY="$(cat /tmp/anthropic_test.key)"
    unset ANTHROPIC_BASE_URL
    python dev/tools/phase2_5/pilot_tool_use.py [--n 5] [--spec <yaml>]

The pilot does NOT touch the production generator pipeline — it just
calls litellm directly with the new tool-use parameters and inspects
the result. The full v0.5.15 migration in Phase B integrates this
into ``generator.py::_call_litellm``.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

# Resolve repo paths from this script's location (works without installation).
_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT / "src"))
sys.path.insert(0, str(_REPO_ROOT))

from uofa_cli.adversarial.spec_loader import load_spec
from uofa_cli.adversarial.skeleton import load_base_cou_skeleton
from uofa_cli.adversarial.prompts import get_template_for_spec
from uofa_cli.adversarial.tool_schema import UOFA_TOOL, UOFA_TOOL_CHOICE


def call_with_tool(
    system_prompt: str,
    user_prompt: str,
    *,
    model: str = "claude-sonnet-4-6",
    max_tokens: int = 8000,
) -> tuple[dict | None, dict, int, float]:
    """Call Anthropic via litellm with tool-use forced. Returns:

    * pkg: parsed package dict (or None on failure)
    * raw_response: full litellm response object as dict
    * tokens: total tokens consumed
    * elapsed: seconds
    """
    import litellm

    litellm.drop_params = True

    start = time.time()
    response = litellm.completion(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=max_tokens,
        tools=[UOFA_TOOL],
        tool_choice=UOFA_TOOL_CHOICE,
        timeout=600,
    )
    elapsed = time.time() - start

    # Extract token usage
    usage = getattr(response, "usage", None)
    if usage is not None:
        tokens = (usage.get("total_tokens") if isinstance(usage, dict)
                  else getattr(usage, "total_tokens", 0))
    else:
        tokens = 0

    # Extract tool call. Anthropic returns content as a list of ContentBlock
    # objects via litellm; the tool call appears in the assistant message's
    # tool_calls field after litellm's adapter translates the response.
    msg = response.choices[0].message
    pkg = None

    # Path 1: OpenAI-style tool_calls list (litellm normalizes anthropic)
    tool_calls = getattr(msg, "tool_calls", None)
    if tool_calls:
        first = tool_calls[0]
        # litellm may serialize as object or dict
        if hasattr(first, "function"):
            args_str = first.function.arguments
        elif isinstance(first, dict):
            args_str = first.get("function", {}).get("arguments", "{}")
        else:
            args_str = "{}"
        try:
            pkg = json.loads(args_str) if isinstance(args_str, str) else args_str
        except json.JSONDecodeError:
            pkg = None

    # Path 2: Direct content list with tool_use blocks (raw Anthropic)
    if pkg is None:
        content = getattr(msg, "content", None)
        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "tool_use":
                    pkg = block.get("input")
                    break
                if hasattr(block, "type") and block.type == "tool_use":
                    pkg = getattr(block, "input", None)
                    break

    return pkg, response.model_dump() if hasattr(response, "model_dump") else {}, tokens, elapsed


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--n", type=int, default=5,
                   help="number of packages to generate (default: 5)")
    p.add_argument("--spec", type=Path,
                   default=_REPO_ROOT / "dev/specs/negative_controls/nc-clean-minimal-morrison-cou1.yaml",
                   help="spec yaml to generate against")
    p.add_argument("--out", type=Path,
                   default=Path("/tmp/v0_phase2v3_pilot"),
                   help="output dir")
    args = p.parse_args(argv)

    if not args.spec.exists():
        print(f"FATAL: spec not found: {args.spec}", file=sys.stderr)
        return 1

    args.out.mkdir(parents=True, exist_ok=True)

    print(f"=== Phase 2 v3 Phase A — tool-use pilot ===")
    print(f"  spec:  {args.spec.name}")
    print(f"  N:     {args.n}")
    print(f"  out:   {args.out}")
    print()

    # Load the spec + render the prompt the same way the production generator
    # does (so the pilot's prompt is representative).
    spec = load_spec(args.spec)
    spec.n_variants = 1
    skeleton = load_base_cou_skeleton(spec.base_cou, pack=spec.pack)
    template = get_template_for_spec(spec)
    system_prompt, user_prompt = template.render(spec, skeleton)

    print(f"  prompt sizes: system={len(system_prompt)} chars, user={len(user_prompt)} chars")
    print(f"  expected cost (5 × ~10K tokens × $0.06/1K input + $0.30/1K output mix): ~$1.50-3.00")
    print()

    # Run N generations
    results: list[dict[str, Any]] = []
    total_tokens = 0
    parse_ok_count = 0
    for i in range(args.n):
        print(f"--- attempt {i+1}/{args.n} ---")
        try:
            pkg, raw, tokens, elapsed = call_with_tool(
                system_prompt, user_prompt, max_tokens=spec.max_tokens or 8000,
            )
        except Exception as e:
            print(f"  ✗ LLM call failed: {e}")
            results.append({
                "attempt": i + 1, "parse_ok": False, "tokens": 0,
                "elapsed_s": 0, "error": str(e),
            })
            continue

        total_tokens += tokens
        parse_ok = pkg is not None and isinstance(pkg, dict)
        if parse_ok:
            parse_ok_count += 1

            # Save the package for SHACL inspection
            pkg_path = args.out / f"pilot_{i+1:02d}.jsonld"
            with open(pkg_path, "w", encoding="utf-8") as f:
                json.dump(pkg, f, indent=2, ensure_ascii=False)
            print(f"  ✓ parsed; saved to {pkg_path}; tokens={tokens}; elapsed={elapsed:.1f}s")

            # Quick structural check
            top_keys = set(pkg.keys())
            required = {"id", "type", "synthetic", "conformsToProfile",
                        "hasContextOfUse", "hasDecisionRecord"}
            missing = required - top_keys
            if missing:
                print(f"    ⚠ missing required fields: {missing}")
        else:
            print(f"  ✗ parse failed; tokens={tokens}; elapsed={elapsed:.1f}s")
            # Save raw response for debugging
            with open(args.out / f"pilot_{i+1:02d}_raw.json", "w") as f:
                json.dump(raw, f, indent=2, default=str)

        results.append({
            "attempt": i + 1, "parse_ok": parse_ok, "tokens": tokens,
            "elapsed_s": round(elapsed, 1),
        })

    # Summary
    print()
    print(f"=== Summary ===")
    print(f"  Parse-as-JSON rate: {parse_ok_count}/{args.n} = {100*parse_ok_count/args.n:.0f}%")
    print(f"  Total tokens: {total_tokens:,}")
    print(f"  Avg tokens per attempt: {total_tokens // max(1, args.n):,}")
    # Pricing estimate: claude-sonnet-4-6 at ~$3/M input + $15/M output
    # Mid estimate: half input, half output → ~$9/M average
    cost_est = total_tokens * 9.0 / 1_000_000
    print(f"  Est. cost: ${cost_est:.2f}")
    print()

    # Write report
    report_path = args.out / "pilot_summary.json"
    with open(report_path, "w") as f:
        json.dump({
            "spec": str(args.spec),
            "n": args.n,
            "parse_ok_count": parse_ok_count,
            "parse_ok_rate": parse_ok_count / args.n,
            "total_tokens": total_tokens,
            "est_cost_usd": round(cost_est, 2),
            "results": results,
        }, f, indent=2)
    print(f"  report → {report_path}")

    # Phase A gate
    print()
    print("=== Phase A.3 gate ===")
    parse_pass = parse_ok_count == args.n
    print(f"  Parse rate {'✓' if parse_pass else '✗'}: {parse_ok_count}/{args.n} (target 100%)")
    # SHACL check is run separately via uofa rules / SHACL tools
    print(f"  SHACL pass rate: run separately via `uofa shacl <pkg>`")
    print(f"  Cost: ${cost_est:.2f} on {args.n} attempts (free-form baseline ~$0.10-0.15/pkg)")

    return 0 if parse_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())

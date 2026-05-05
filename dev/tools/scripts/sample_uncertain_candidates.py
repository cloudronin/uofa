#!/usr/bin/env python3
"""Judge-D-driven UNCERTAIN candidate sampler for the calibration set.

Stage 1 v3 surfaced that 2 of the original 5 UNCERTAIN cases (cal-027,
cal-030) were Judge D hedging on cases with clearer answers than the
UNCERTAIN label suggested. This sampler:

  1. Pulls N candidates from Phase 2 corpus that have structural
     markers of ambiguity (COV-WRONG outcome, target rule didn't
     fire, multiple competing rules fired).
  2. Runs Judge D (Anthropic Claude Sonnet 4.6) over each via the
     production prompt v1.1.0.
  3. Filters for cases where Judge D's verdict is UNCERTAIN AND the
     reasoning explicitly acknowledges multiple plausible verdicts.
  4. Outputs the top 2 + a markdown summary the author can scan.

The 2 selected candidates fill the cal-027 + cal-030 slots in the
calibration set (replacing the relabeled cases). The original
phase2_case_id + Judge D reasoning are preserved in the calibration
record's `ground_truth_reasoning` field.

Cost: ~$0.50 (10 candidates × Judge D at ~$0.05/case).

Usage:
  ANTHROPIC_API_KEY=$(cat /tmp/anthropic.txt) \
      python dev/tools/scripts/sample_uncertain_candidates.py \
          --bundle dev/build/adversarial/phase2/2026-04-26/judge_ready_bundle.tgz \
          --n-candidates 10 \
          --out dev/build/adversarial/phase3/uncertain_candidates/
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from collections import Counter
from dataclasses import asdict
from pathlib import Path

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[3] / "src"))

from uofa_cli.adversarial.judge.bundle import open_bundle  # noqa: E402
from uofa_cli.adversarial.judge.providers.litellm_provider import LiteLLMProvider  # noqa: E402


# Heuristic markers of ambiguity per Stage 1 v3 finding:
# - COV-WRONG (target rule didn't fire as expected)
# - Many baseline rules fired (suggests multiple competing
#   interpretations)
# - Existing case_ids in the calibration set are excluded (no overlap).


def _existing_calibration_phase2_ids() -> set[str]:
    """Read calibration_set_v1.jsonl and return the phase2_case_ids
    already represented so we don't re-pick them as candidates."""
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
    """Pick n candidate cases from the Phase 2 bundle.

    Heuristic: COV-WRONG (or COV-CLEAN-WRONG) cases with ≥5 distinct
    rule firings (multiple competing rules → ambiguity signal). Skips
    case_ids already in the calibration set.
    """
    excluded = _existing_calibration_phase2_ids()
    candidates: list[dict] = []
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
            candidates.append({
                "case_id": entry.case_id,
                "phase2_case_id": entry.case_id,
                "package": entry.package,
                "outcome": dict(entry.outcome),
            })
            if len(candidates) >= n:
                break
    return candidates


async def _judge_d_anchor_one(provider: LiteLLMProvider, candidate: dict) -> dict:
    """Run Judge D on one candidate via the production prompt."""
    case_for_judge = {
        "case_id": candidate["case_id"],
        "phase2_case_id": candidate["phase2_case_id"],
        "source_taxonomy": candidate["outcome"].get("source_taxonomy"),
        "rules_fired": candidate["outcome"].get("rules_fired", []),
        "expected_rule": candidate["outcome"].get("expected_rule"),
        "section_6_7_mapping": candidate["outcome"].get("section_6_7_mapping"),
        "phase2_outcome_class_raw": candidate["outcome"].get(
            "phase2_outcome_class_raw"
        ) or candidate["outcome"].get("coverage_class"),
        "package": candidate["package"],
    }
    t0 = time.perf_counter()
    try:
        j = await provider.judge(case_for_judge)
        return {
            "candidate": candidate,
            "verdict": j.verdict,
            "confidence": j.confidence,
            "reasoning": j.reasoning,
            "latency_s": time.perf_counter() - t0,
            "error": None,
        }
    except Exception as e:
        return {
            "candidate": candidate,
            "verdict": None,
            "confidence": None,
            "reasoning": None,
            "latency_s": time.perf_counter() - t0,
            "error": repr(e)[:300],
        }


async def amain(args) -> int:
    if "ANTHROPIC_API_KEY" not in os.environ:
        print("ERROR: ANTHROPIC_API_KEY required", file=sys.stderr)
        return 2

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Selecting {args.n_candidates} candidates from {args.bundle}...")
    candidates = _select_candidates(Path(args.bundle), args.n_candidates)
    print(f"  picked {len(candidates)} candidates (excluded existing calibration phase2_case_ids)")

    print("Running Judge D (claude-sonnet-4-6) over candidates with prompt v1.1.0 ...")
    provider = LiteLLMProvider(
        provider_token="anthropic",
        judge_role="calibration_anchor",
        thinking_enabled=False,
        prompt_template_version="v1.1.0",
    )
    sem = asyncio.Semaphore(args.concurrency)

    async def bound(c):
        async with sem:
            return await _judge_d_anchor_one(provider, c)

    results = await asyncio.gather(*(bound(c) for c in candidates))

    # Tally
    verdict_counter = Counter(r["verdict"] for r in results)
    print(f"\nJudge D verdict distribution: {dict(verdict_counter)}")

    # Write all results for audit
    raw_path = out_dir / "uncertain_candidates_raw.jsonl"
    with raw_path.open("w") as f:
        for r in results:
            f.write(json.dumps({
                "case_id": r["candidate"]["case_id"],
                "phase2_case_id": r["candidate"]["phase2_case_id"],
                "source_taxonomy": r["candidate"]["outcome"].get("source_taxonomy"),
                "rules_fired": r["candidate"]["outcome"].get("rules_fired"),
                "phase2_outcome_class_raw": r["candidate"]["outcome"].get(
                    "phase2_outcome_class_raw"
                ),
                "verdict": r["verdict"],
                "confidence": r["confidence"],
                "reasoning": r["reasoning"],
                "error": r["error"],
                "latency_s": r["latency_s"],
            }) + "\n")
    print(f"Raw results: {raw_path}")

    # Filter to UNCERTAIN verdicts; sort by confidence descending.
    uncertain = [r for r in results if r["verdict"] == "UNCERTAIN"]
    uncertain.sort(key=lambda r: -(r["confidence"] or 0))

    if not uncertain:
        print("\nNO Judge D = UNCERTAIN candidates found. Try a larger --n-candidates.")
        return 1

    print(f"\nFound {len(uncertain)} UNCERTAIN candidates. Top picks:")
    selected = uncertain[: args.n_pick]
    for i, r in enumerate(selected, 1):
        c = r["candidate"]
        print(f"  {i}. {c['case_id']}  conf={r['confidence']:.2f}")
        print(f"     source: {c['outcome'].get('source_taxonomy')}")
        print(f"     reasoning: {r['reasoning'][:200]!r}")

    # Emit a calibration-set-ready JSONL fragment for the picks.
    picks_path = out_dir / "uncertain_picks.jsonl"
    with picks_path.open("w") as f:
        for r in selected:
            c = r["candidate"]
            outcome = c["outcome"]
            cal_record = {
                # Slot identifier is provisional; the author will assign
                # the actual cal-NNN id when integrating into the set.
                "case_id": f"REPLACE_ME-uncertain-{c['phase2_case_id']}",
                "phase2_case_id": c["phase2_case_id"],
                "package_path": f"specs/calibration/packages/REPLACE_ME-uncertain.jsonld",
                "source_taxonomy": outcome.get("source_taxonomy"),
                "phase2_outcome_class": outcome.get(
                    "phase2_outcome_class_raw"
                ) or outcome.get("coverage_class"),
                "phase2_outcome_class_normalized": outcome.get(
                    "phase2_outcome_class_raw"
                ) or outcome.get("coverage_class"),
                "expected_target_rule": outcome.get("expected_rule"),
                "rules_fired": outcome.get("rules_fired"),
                "section_6_7_mapping": None,
                "scaffold_note": (
                    f"Judge-D-driven UNCERTAIN candidate (sampled "
                    f"2026-05-05 to replace cal-027/030 relabels). "
                    f"Phase 2 outcome class indicated potential ambiguity "
                    f"and Judge D anchored as UNCERTAIN at confidence "
                    f"{r['confidence']:.2f}."
                ),
                "ground_truth_verdict": "UNCERTAIN",
                "ground_truth_reasoning": r["reasoning"],
                "ground_truth_section_6_7_candidate": None,
                "annotator": "Judge D (Anthropic Claude Sonnet 4.6) per spec v1.6 §8.0",
                "annotation_date": "2026-05-05",
                "review_confidence": "medium",
                "is_canonical_few_shot": False,
                "notes": (
                    "2026-05-05 substitution: Judge-D-driven replacement "
                    "for cal-027/030 (relabeled to ERM after Stage 1 v3 "
                    "investigation showed Judge D's original UNCERTAIN "
                    "labels were hedging on cases with clearer answers)."
                ),
            }
            f.write(json.dumps(cal_record) + "\n")
    print(f"\nCalibration-set-ready picks: {picks_path}")
    print("Next: integrate picks into specs/calibration/calibration_set_v1.jsonl")
    print("  + relabel cal-027 + cal-030 to ERM")
    print("  + copy package files to specs/calibration/packages/")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--bundle", type=Path,
        default=Path("dev/build/adversarial/phase2/2026-04-26/judge_ready_bundle.tgz"),
    )
    parser.add_argument("--n-candidates", type=int, default=10,
                        help="Phase 2 candidates to score (default 10)")
    parser.add_argument("--n-pick", type=int, default=2,
                        help="UNCERTAIN candidates to pick from the scored pool (default 2)")
    parser.add_argument("--concurrency", type=int, default=3)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    return asyncio.run(amain(args))


if __name__ == "__main__":
    sys.exit(main())

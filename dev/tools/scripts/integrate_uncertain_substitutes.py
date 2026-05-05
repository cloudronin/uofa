#!/usr/bin/env python3
"""Integrate the 2 thinking-mode UNCERTAIN substitutes into the calibration set.

Replaces cal-027 and cal-030 with the picked substitutes. The original
cal-027/030 case content is discarded (those slots are reserved for
UNCERTAIN cases per the spec's 5-per-class invariant; the original
cases were Judge D hedging on cases with clearer answers per Stage 1
v3 investigation).

Side effects:
  - Writes 2 package files to specs/calibration/packages/cal-027-... + cal-030-...jsonld
  - Replaces the cal-027 + cal-030 records in specs/calibration/calibration_set_v1.jsonl
  - Backs up the original calibration_set_v1.jsonl to .bak before writing
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[3] / "src"))

from uofa_cli.adversarial.judge.bundle import open_bundle  # noqa: E402


# Picks per the thinking-mode sampler raw output (2026-05-05).
# Order = which slot they fill (cal-027 first, cal-030 second).
PICKS = [
    {
        "slot_case_id": "cal-027-uncertain-undermining-d1",
        "phase2_case_id": "adv-2026-p2-001-w-ar-01_high_morrison-cou1-v05",
        "source_taxonomy": "jarzebowicz-wardzinski/argument_defeaters/D1-undermining",
    },
    {
        "slot_case_id": "cal-030-uncertain-variability",
        "phase2_case_id": "adv-2026-p2-001-w-ar-01_high_nagaraja-cou1-v06",
        "source_taxonomy": "jarzebowicz-wardzinski/argument_defeaters/D1-undermining",
    },
]

# Note on slot_case_id: the human-readable suffix is preserved from
# the original cal-027/030 names ("undermining-d1", "variability"). The
# case_id is just an identifier — what matters for the set is that
# cal-027 + cal-030 are still 2 of the 5 UNCERTAIN cases.


def _read_thinking_results(path: Path) -> dict[str, dict]:
    """Load Judge D's thinking-mode reasoning keyed by case_id."""
    out: dict[str, dict] = {}
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        out[rec["case_id"]] = rec
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--bundle", type=Path,
        default=Path("dev/build/adversarial/phase2/2026-04-26/judge_ready_bundle.tgz"),
    )
    parser.add_argument(
        "--thinking-results", type=Path,
        default=Path("dev/build/adversarial/phase3/uncertain_candidates_thinking/uncertain_candidates_thinking_raw.jsonl"),
    )
    parser.add_argument(
        "--calibration-set", type=Path,
        default=Path("specs/calibration/calibration_set_v1.jsonl"),
    )
    parser.add_argument(
        "--packages-dir", type=Path,
        default=Path("specs/calibration/packages"),
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print the substitutions without writing any files.",
    )
    args = parser.parse_args()

    if not args.thinking_results.exists():
        print(f"ERROR: thinking-mode results not found at {args.thinking_results}", file=sys.stderr)
        print("  Run dev/tools/scripts/sample_uncertain_with_thinking.py first.", file=sys.stderr)
        return 2

    thinking = _read_thinking_results(args.thinking_results)

    # Extract package files + bundle outcome metadata for each pick.
    print(f"Reading bundle: {args.bundle}")
    pick_data: list[dict] = []
    with open_bundle(args.bundle) as bundle:
        case_ids_wanted = {p["phase2_case_id"] for p in PICKS}
        for entry in bundle.iter_entries():
            if entry.case_id not in case_ids_wanted:
                continue
            pick_data.append({
                "case_id": entry.case_id,
                "package": entry.package,
                "outcome": dict(entry.outcome),
            })

    if len(pick_data) != len(PICKS):
        found = {p["case_id"] for p in pick_data}
        missing = {p["phase2_case_id"] for p in PICKS} - found
        print(f"ERROR: missing pick(s) in bundle: {missing}", file=sys.stderr)
        return 3

    # Index by phase2_case_id for the join.
    bundle_by_id = {p["case_id"]: p for p in pick_data}

    # Read existing calibration set
    existing = [
        json.loads(line)
        for line in args.calibration_set.read_text().splitlines()
        if line.strip()
    ]
    existing_by_case_id = {r["case_id"]: r for r in existing}

    # Build replacement records.
    replacements: dict[str, dict] = {}
    for pick in PICKS:
        slot = pick["slot_case_id"]
        bd = bundle_by_id[pick["phase2_case_id"]]
        thinking_result = thinking.get(pick["phase2_case_id"], {})

        old_record = existing_by_case_id.get(slot)
        original_judge_d_reasoning = old_record.get("ground_truth_reasoning", "") if old_record else ""

        new_record = {
            "case_id": slot,
            "phase2_case_id": pick["phase2_case_id"],
            "package_path": str(args.packages_dir / f"{slot}.jsonld"),
            "source_taxonomy": pick["source_taxonomy"],
            "phase2_outcome_class": bd["outcome"].get(
                "phase2_outcome_class_raw"
            ) or bd["outcome"].get("coverage_class"),
            "phase2_outcome_class_normalized": bd["outcome"].get(
                "phase2_outcome_class_raw"
            ) or bd["outcome"].get("coverage_class"),
            "expected_target_rule": bd["outcome"].get("expected_rule"),
            "rules_fired": bd["outcome"].get("rules_fired"),
            "section_6_7_mapping": None,
            "scaffold_note": (
                f"Judge-D-driven UNCERTAIN substitute (sampled 2026-05-05 "
                f"with thinking_budget=4096 to recover thinking-mode "
                f"anchoring used for the original cal-026..030 cases). "
                f"Confidence {thinking_result.get('confidence', 0):.2f}."
            ),
            "ground_truth_verdict": "UNCERTAIN",
            "ground_truth_reasoning": thinking_result.get("reasoning", ""),
            "ground_truth_section_6_7_candidate": None,
            "annotator": (
                "Judge D (Anthropic Claude Sonnet 4.6, thinking-mode "
                "budget=4096) per spec v1.6 §8.0"
            ),
            "annotation_date": "2026-05-05",
            "review_confidence": "medium",
            "is_canonical_few_shot": False,
            "notes": (
                f"2026-05-05 substitution: replaces original {slot} content. "
                f"Original case ({old_record.get('phase2_case_id') if old_record else 'unknown'}) "
                f"was Judge D hedging without thinking-mode; production judges "
                f"all classified it as EXISTING-RULE-MISBEHAVIOR. New case "
                f"is Judge D thinking-mode anchor: {pick['phase2_case_id']}. "
                f"Original Judge D reasoning preserved in audit log at "
                f"dev/build/adversarial/phase3/uncertain_candidates_thinking/."
            ),
        }
        replacements[slot] = new_record

    # Stitch: replace old records in-place; preserve order.
    new_records = []
    for r in existing:
        if r["case_id"] in replacements:
            new_records.append(replacements[r["case_id"]])
        else:
            new_records.append(r)

    if args.dry_run:
        print("\n=== DRY RUN ===")
        for slot, r in replacements.items():
            print(f"\n{slot}:")
            print(f"  phase2_case_id: {r['phase2_case_id']}")
            print(f"  ground_truth_verdict: {r['ground_truth_verdict']}")
            print(f"  reasoning preview: {r['ground_truth_reasoning'][:200]!r}")
        return 0

    # Write package files.
    args.packages_dir.mkdir(parents=True, exist_ok=True)
    for slot, r in replacements.items():
        pkg_path = args.packages_dir / f"{slot}.jsonld"
        bd = bundle_by_id[r["phase2_case_id"]]
        pkg_path.write_text(json.dumps(bd["package"], indent=2))
        print(f"  wrote {pkg_path}")

    # Backup + write calibration set.
    bak = args.calibration_set.with_suffix(".jsonl.bak")
    shutil.copy2(args.calibration_set, bak)
    print(f"  backed up: {bak}")

    with args.calibration_set.open("w") as f:
        for r in new_records:
            f.write(json.dumps(r) + "\n")
    print(f"  rewrote: {args.calibration_set}")

    # Sanity: confirm class distribution still 5-per-class.
    from collections import Counter
    dist = Counter(r["ground_truth_verdict"] for r in new_records)
    print(f"\nNew class distribution: {dict(dist)}")
    if any(c != 5 for c in dist.values()):
        print("WARNING: class distribution drifted from 5-per-class.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

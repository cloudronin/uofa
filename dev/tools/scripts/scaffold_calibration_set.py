"""Generate a scaffolded calibration set from the real Phase 2 bundle.

Produces `specs/calibration/calibration_set_v1.jsonl` with 30 cases stratified
across the 6 verdict classes (5 per class) plus per-case package copies under
`specs/calibration/packages/`. The author then opens the JSONL and fills in
the `ground_truth_*` fields case by case.

Stratification (spec §8.1):

    CORRECT-DETECTION         5  confirm_existing + COV-HIT cases (target rule fired)
    REAL-GAP                  5  gap_probe cases mapping to §6.7 Tier 1 candidates
    GENERATOR-ARTIFACT        5  GEN-INVALID class (SHACL-failed packages)
    EXISTING-RULE-MISBEHAVIOR 5  negative_control + COV-CLEAN-WRONG (false positives)
    OUT-OF-SCOPE              5  STUB entries — author-constructed per spec §8.1
    UNCERTAIN                 5  confirm_existing + COV-WRONG (target missed, others fired)

For each case:
    - Pre-fills phase2_case_id, source_taxonomy, outcome class, expected rule,
      rules_fired, section_6_7_mapping
    - Copies the JSON-LD package to specs/calibration/packages/<case_id>.jsonld
    - Stubs ground_truth_verdict / ground_truth_reasoning / review_confidence
      with TODO_AUTHOR markers the validator checks for

Usage:
    python dev/tools/scripts/scaffold_calibration_set.py \\
        --bundle dev/build/adversarial/phase2/2026-04-26/judge_ready_bundle.tgz \\
        --out specs/calibration/calibration_set_v1.jsonl

Idempotent: re-running with the same bundle + seed produces the same selection.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path
from typing import Any

# Allow `python dev/tools/scripts/scaffold_calibration_set.py` from repo root.
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))

from uofa_cli.adversarial.judge.bundle import open_bundle


# Spec §6.7 Tier 1 candidate IDs — REAL-GAP class draws from cases whose
# source_taxonomy hints at one of these patterns.
SECTION_6_7_CANDIDATES: dict[str, list[str]] = {
    "W-EV-01": ["evidence_validity/data-drift", "evidence_validity/stale-validation"],
    "W-EV-02": ["evidence_validity/inadequate-metrics", "evidence_validity/coverage-edge"],
    "W-REQ-01": ["requirements/ambiguous", "requirements/incomplete"],
    "W-CX-01": ["contextual/configuration", "contextual/environmental"],
    "W-AR-06": ["argument/eliminative-argumentation"],
    "W-AR-07": ["argument/sustained-defeater", "argument/residual-risk"],
}


def _section_6_7_for(source_taxonomy: str) -> str | None:
    """Best-effort match of a source_taxonomy substring to a §6.7 candidate."""
    if not source_taxonomy:
        return None
    s = source_taxonomy.lower()
    for candidate, hints in SECTION_6_7_CANDIDATES.items():
        for hint in hints:
            if hint in s:
                return candidate
    return None


def _canonical_case_id(verdict_class: str, idx: int, hint: str) -> str:
    """Build a stable cal-NNN-<class>-<hint> id."""
    cls_short = verdict_class.lower().replace("-", "_")
    safe_hint = hint.lower().replace("/", "-").replace(" ", "-")[:40].strip("-")
    return f"cal-{idx:03d}-{cls_short}-{safe_hint}"


def _bucket_entries(entries: list[Any]) -> dict[str, list[Any]]:
    """Sort the bundle entries into raw stratification buckets."""
    buckets = {
        "correct_detection_candidates": [],   # confirm_existing + COV-HIT
        "real_gap_candidates": [],            # gap_probe + §6.7 hint
        "generator_artifact_candidates": [],  # GEN-INVALID
        "existing_rule_misbehavior_candidates": [],  # negative_control + COV-CLEAN-WRONG
        "uncertain_candidates": [],           # confirm_existing + COV-WRONG (target missed)
    }
    for e in entries:
        outcome = e.outcome
        coverage = outcome.get("coverage_class")
        coverage_intent = outcome.get("experimental_factors", {}).get("coverage_intent")
        raw_class = outcome.get("phase2_outcome_class_raw")
        target_fired = outcome.get("target_rule_fired", False)

        if coverage_intent == "confirm_existing" and coverage == "COV-HIT":
            buckets["correct_detection_candidates"].append(e)
        elif coverage_intent == "gap_probe" and _section_6_7_for(outcome.get("source_taxonomy") or ""):
            buckets["real_gap_candidates"].append(e)
        elif coverage == "GEN-INVALID":
            buckets["generator_artifact_candidates"].append(e)
        elif raw_class == "COV-CLEAN-WRONG":
            buckets["existing_rule_misbehavior_candidates"].append(e)
        elif coverage_intent == "confirm_existing" and coverage == "COV-WRONG" and not target_fired:
            buckets["uncertain_candidates"].append(e)
    return buckets


def _stratified_sample(
    candidates: list[Any], n: int, *, rng: random.Random,
    diversify_by: str | None = None,
) -> list[Any]:
    """Pick n cases, optionally diversifying by an outcome field (e.g. expected_rule)."""
    if len(candidates) <= n:
        return list(candidates)
    if diversify_by is None:
        return rng.sample(candidates, n)
    # Group by the diversify field, pick round-robin from groups.
    groups: dict[str, list[Any]] = {}
    for e in candidates:
        key = e.outcome.get(diversify_by) or "_other"
        groups.setdefault(key, []).append(e)
    keys = sorted(groups)
    rng.shuffle(keys)
    out: list[Any] = []
    while len(out) < n and any(groups[k] for k in keys):
        for k in keys:
            if not groups[k]:
                continue
            out.append(groups[k].pop(rng.randrange(len(groups[k]))))
            if len(out) >= n:
                break
    return out


def _build_case_record(
    *,
    verdict_class: str,
    idx: int,
    bundle_entry: Any | None,
    package_dir: Path,
    note: str,
) -> dict:
    """Construct one calibration JSONL record.

    If bundle_entry is None, emits a STUB record for author-constructed
    cases (OUT-OF-SCOPE class).
    """
    if bundle_entry is None:
        case_id = _canonical_case_id(verdict_class, idx, "stub")
        return {
            "case_id": case_id,
            "phase2_case_id": None,
            "package_path": None,
            "source_taxonomy": "TODO_AUTHOR_TAXONOMY",
            "phase2_outcome_class": None,
            "phase2_outcome_class_normalized": None,
            "expected_target_rule": None,
            "rules_fired": [],
            "section_6_7_mapping": None,
            "scaffold_note": note,
            "ground_truth_verdict": verdict_class,  # pre-filled — class is intent
            "ground_truth_reasoning": "TODO_AUTHOR_REASONING (≥30 words; describe the constructed package + why it instantiates an out-of-scope defeater)",
            "ground_truth_section_6_7_candidate": None,
            "annotator": "Vettrivel",
            "annotation_date": None,
            "review_confidence": "TODO_AUTHOR (high|medium|low)",
            "is_canonical_few_shot": False,
            "notes": "STUB — author constructs the package separately and updates package_path",
        }

    outcome = bundle_entry.outcome
    case_hint = outcome.get("source_taxonomy", "case").split("/")[-1] or "case"
    case_id = _canonical_case_id(verdict_class, idx, case_hint)
    package_path = package_dir / f"{case_id}.jsonld"
    return {
        "case_id": case_id,
        "phase2_case_id": bundle_entry.case_id,
        "package_path": str(package_path).removeprefix(
            str(Path(__file__).resolve().parents[3]) + "/"
        ),
        "source_taxonomy": outcome.get("source_taxonomy"),
        "phase2_outcome_class": outcome.get("phase2_outcome_class_raw"),
        "phase2_outcome_class_normalized": outcome.get("coverage_class"),
        "expected_target_rule": outcome.get("expected_rule"),
        "rules_fired": outcome.get("rules_fired", []),
        "section_6_7_mapping": outcome.get("section_6_7_mapping"),
        "scaffold_note": note,
        "ground_truth_verdict": "TODO_AUTHOR_VERDICT",
        "ground_truth_reasoning": "TODO_AUTHOR_REASONING (≥30 words; reference package content + source taxonomy + existing catalog)",
        "ground_truth_section_6_7_candidate": None,
        "annotator": "Vettrivel",
        "annotation_date": None,
        "review_confidence": "TODO_AUTHOR (high|medium|low)",
        "is_canonical_few_shot": False,
        "notes": "",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--bundle", type=Path, required=True,
                        help="path to judge_ready_bundle.tgz")
    parser.add_argument("--out", type=Path, required=True,
                        help="output JSONL path (e.g. specs/calibration/calibration_set_v1.jsonl)")
    parser.add_argument("--seed", type=int, default=42,
                        help="random seed for reproducible sampling (default 42)")
    args = parser.parse_args()

    if not args.bundle.exists():
        print(f"bundle not found: {args.bundle}", file=sys.stderr)
        return 2

    package_dir = args.out.parent / "packages"
    package_dir.mkdir(parents=True, exist_ok=True)

    print(f"reading bundle: {args.bundle}")
    with open_bundle(args.bundle) as bundle:
        entries = list(bundle.iter_entries())
    print(f"  {len(entries)} entries")

    buckets = _bucket_entries(entries)
    for k, v in buckets.items():
        print(f"  {k}: {len(v)} candidates")

    rng = random.Random(args.seed)
    records: list[dict] = []

    # CORRECT-DETECTION — diversify by expected_rule across the catalog.
    selected = _stratified_sample(
        buckets["correct_detection_candidates"], 5,
        rng=rng, diversify_by="expected_rule",
    )
    for i, e in enumerate(selected, start=1):
        records.append(_build_case_record(
            verdict_class="CORRECT-DETECTION",
            idx=i,
            bundle_entry=e,
            package_dir=package_dir,
            note="Auto-selected confirm_existing + COV-HIT case. Verify the package legitimately instantiates the target defeater AND the expected rule firing is correct (not just incidental).",
        ))

    # REAL-GAP — diversify by §6.7 candidate.
    rg_candidates = buckets["real_gap_candidates"]
    rg_by_section = {}
    for e in rg_candidates:
        key = _section_6_7_for(e.outcome.get("source_taxonomy") or "")
        rg_by_section.setdefault(key, []).append(e)
    rg_picked: list[Any] = []
    section_keys = sorted(rg_by_section)
    rng.shuffle(section_keys)
    for k in section_keys:
        if rg_by_section[k] and len(rg_picked) < 5:
            rg_picked.append(rng.choice(rg_by_section[k]))
    # Top up if any §6.7 sections were empty.
    while len(rg_picked) < 5 and rg_candidates:
        candidate = rng.choice(rg_candidates)
        if candidate not in rg_picked:
            rg_picked.append(candidate)
    for i, e in enumerate(rg_picked, start=6):
        section = _section_6_7_for(e.outcome.get("source_taxonomy") or "")
        rec = _build_case_record(
            verdict_class="REAL-GAP",
            idx=i,
            bundle_entry=e,
            package_dir=package_dir,
            note=f"Auto-selected gap_probe case mapping to §6.7 candidate {section}. Verify the package correctly instantiates the defeater AND no existing rule covers it (if existing rule(s) fired, this may be EXISTING-RULE-MISBEHAVIOR instead).",
        )
        rec["ground_truth_section_6_7_candidate"] = section
        records.append(rec)

    # GENERATOR-ARTIFACT — sample from GEN-INVALID class.
    selected = _stratified_sample(
        buckets["generator_artifact_candidates"], 5,
        rng=rng, diversify_by="source_taxonomy",
    )
    for i, e in enumerate(selected, start=11):
        records.append(_build_case_record(
            verdict_class="GENERATOR-ARTIFACT",
            idx=i,
            bundle_entry=e,
            package_dir=package_dir,
            note="Auto-selected GEN-INVALID case (Phase 2 SHACL-failed package). Likely GENERATOR-ARTIFACT — verify the package is malformed in a way that prevented legitimate instantiation. If the malformation is incidental and the defeater IS instantiated, the verdict may differ.",
        ))

    # EXISTING-RULE-MISBEHAVIOR — negative_control false positives.
    selected = _stratified_sample(
        buckets["existing_rule_misbehavior_candidates"], 5,
        rng=rng, diversify_by="source_taxonomy",
    )
    for i, e in enumerate(selected, start=16):
        records.append(_build_case_record(
            verdict_class="EXISTING-RULE-MISBEHAVIOR",
            idx=i,
            bundle_entry=e,
            package_dir=package_dir,
            note="Auto-selected negative_control + COV-CLEAN-WRONG case. A rule fired on a deliberately-clean COU = false positive. Identify which rule misfired and why; this verdict implies a rule refinement (not a new rule).",
        ))

    # OUT-OF-SCOPE — STUB entries; author constructs.
    for i in range(1, 6):
        records.append(_build_case_record(
            verdict_class="OUT-OF-SCOPE",
            idx=20 + i,
            bundle_entry=None,
            package_dir=package_dir,
            note="STUB — author constructs a package instantiating an out-of-scope defeater (subjective model-form adequacy, human factors, organizational, etc.). Place the constructed package at specs/calibration/packages/<case_id>.jsonld and update package_path.",
        ))

    # UNCERTAIN — confirm_existing + COV-WRONG (target missed, ambiguous).
    selected = _stratified_sample(
        buckets["uncertain_candidates"], 5,
        rng=rng, diversify_by="source_taxonomy",
    )
    for i, e in enumerate(selected, start=26):
        records.append(_build_case_record(
            verdict_class="UNCERTAIN",
            idx=i,
            bundle_entry=e,
            package_dir=package_dir,
            note="Auto-selected confirm_existing + COV-WRONG case where the target rule did NOT fire but other rules did. These are the natural ambiguity space — verdict could be REAL-GAP, EXISTING-RULE-MISBEHAVIOR, GENERATOR-ARTIFACT, or genuinely UNCERTAIN. Reserve UNCERTAIN for cases that resist resolution after careful inspection.",
        ))

    # Write package copies.
    for rec in records:
        if rec.get("package_path") is None:
            continue
        # Find the matching bundle entry to copy its package.
        phase2_id = rec["phase2_case_id"]
        match = next((e for e in entries if e.case_id == phase2_id), None)
        if match is None:
            continue
        out_path = Path(rec["package_path"])
        if not out_path.is_absolute():
            out_path = Path(__file__).resolve().parents[3] / out_path
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(match.package, indent=2))

    # Write the JSONL.
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w") as f:
        for rec in records:
            f.write(json.dumps(rec) + "\n")

    print(f"\nwrote {len(records)} scaffolded cases to {args.out}")
    print(f"package copies under {package_dir}/")
    print()
    print("Next steps:")
    print("  1. Open specs/calibration/calibration_set_v1.jsonl in your editor.")
    print("  2. For each case, read the package at the package_path.")
    print("  3. Replace TODO_AUTHOR_VERDICT with one of:")
    print("     CORRECT-DETECTION, REAL-GAP, GENERATOR-ARTIFACT,")
    print("     EXISTING-RULE-MISBEHAVIOR, OUT-OF-SCOPE, UNCERTAIN")
    print("  4. Replace TODO_AUTHOR_REASONING with rationale (≥30 words).")
    print("  5. Set review_confidence to 'high', 'medium', or 'low'.")
    print("  6. Mark ONE case per verdict class as is_canonical_few_shot=true.")
    print("     (These become the few-shot examples in v1.0.0 prompt.)")
    print("  7. Run: python dev/tools/scripts/validate_calibration_set.py")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())

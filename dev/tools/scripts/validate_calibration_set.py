"""Validate the author-annotated calibration set (spec v1.5 §8.1, §8.2).

Checks (all must pass before Stage 1):

    1. File parses as JSONL with exactly 30 records.
    2. Each verdict class has exactly 5 records.
    3. No TODO_AUTHOR_* markers remain.
    4. Each record has all required fields populated.
    5. ground_truth_verdict ∈ the 6 spec verdict classes.
    6. review_confidence ∈ {high, medium, low}.
    7. ground_truth_reasoning has ≥30 words.
    8. Each verdict class has exactly 1 record marked is_canonical_few_shot=true
       (spec §7.1: "one canonical example per class").
    9. Every package_path exists and parses as JSON.
    10. annotation_date is a valid ISO-format date string.
    11. REAL-GAP records have section_6_7_mapping populated (spec §13.2).
    12. REAL-GAP cases collectively cover ≥4 of the 6 §6.7 Tier 1 candidates
        (per spec §15 hard gate #13 calibration anchor).

Soft warnings (reported but do not fail):

    W1. case_id contains the verdict class as a token. Verify the prompt builder
        uses phase2_case_id (or strips the verdict token) so the judge does not
        see the answer in the case_id. Use --allow-verdict-in-case-id to silence.
    W2. Source spec diversity within auto-selected classes: no single Phase 2
        spec should account for more than 2 of 5 cases in any class.

Exits 0 on pass (warnings allowed), 1 on any hard failure with all issues listed.

Usage:
    python dev/tools/scripts/validate_calibration_set.py \\
        --in specs/calibration/calibration_set_v1.jsonl
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

VERDICT_CLASSES = {
    "CORRECT-DETECTION", "REAL-GAP", "GENERATOR-ARTIFACT",
    "EXISTING-RULE-MISBEHAVIOR", "OUT-OF-SCOPE", "UNCERTAIN",
}

EXPECTED_PER_CLASS = 5
EXPECTED_TOTAL = 30

REQUIRED_FIELDS = {
    "case_id", "source_taxonomy", "ground_truth_verdict",
    "ground_truth_reasoning", "annotator", "annotation_date",
    "review_confidence", "is_canonical_few_shot",
}

# §6.7 Tier 1 candidates per spec §13.2. REAL-GAP cases must collectively
# cover at least 4 of these to anchor §15 hard gate #13.
SECTION_6_7_CANDIDATES = {
    "W-EV-01", "W-EV-02", "W-REQ-01", "W-CX-01", "W-AR-06", "W-AR-07",
}
SECTION_6_7_MIN_COVERAGE = 4

# Auto-selected classes (i.e., not author-constructed). Diversity warnings
# apply to these classes only; OUT-OF-SCOPE is hand-built so single-source
# diversity is expected.
AUTO_SELECTED_CLASSES = {
    "CORRECT-DETECTION", "REAL-GAP", "GENERATOR-ARTIFACT",
    "EXISTING-RULE-MISBEHAVIOR", "UNCERTAIN",
}
SOURCE_SPEC_MAX_PER_CLASS = 2  # at most this many cases per class from one spec

# Verdict tokens that may appear in a case_id and leak the answer to the prompt.
VERDICT_TOKENS = {
    "correct_detection", "real_gap", "generator_artifact",
    "existing_rule_misbehavior", "out_of_scope", "uncertain",
}


def _has_todo(value: object) -> bool:
    """True if the value is or contains a TODO_AUTHOR_* marker."""
    if isinstance(value, str):
        return value.startswith("TODO_AUTHOR")
    return False


def validate(
    path: Path,
    *,
    repo_root: Path,
    allow_verdict_in_case_id: bool = False,
) -> tuple[list[str], list[str]]:
    """Return (issues, warnings) where issues block (exit 1) and warnings inform (exit 0)."""
    issues: list[str] = []
    warnings: list[str] = []
    if not path.exists():
        return [f"calibration set not found: {path}"], []

    records: list[dict] = []
    for lineno, line in enumerate(path.read_text().splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError as e:
            issues.append(f"line {lineno}: invalid JSON ({e})")
            continue

    if not records:
        issues.append("calibration set has no records")
        return issues, warnings

    # 1. Total count.
    if len(records) != EXPECTED_TOTAL:
        issues.append(
            f"expected {EXPECTED_TOTAL} records, got {len(records)}"
        )

    # 2. Per-class count.
    by_class: dict[str, int] = {}
    for rec in records:
        verdict = rec.get("ground_truth_verdict")
        if isinstance(verdict, str) and not _has_todo(verdict):
            by_class[verdict] = by_class.get(verdict, 0) + 1
    for cls in VERDICT_CLASSES:
        if by_class.get(cls, 0) != EXPECTED_PER_CLASS:
            issues.append(
                f"verdict class {cls}: expected {EXPECTED_PER_CLASS} records, "
                f"got {by_class.get(cls, 0)}"
            )

    # Per-record checks.
    canonical_per_class: dict[str, int] = {}
    for rec in records:
        case_id = rec.get("case_id", "<no id>")

        # 3. No TODO markers anywhere in the record values.
        for k, v in rec.items():
            if _has_todo(v):
                issues.append(f"{case_id}: field {k!r} still has TODO_AUTHOR marker")

        # 4. Required fields present (non-null where applicable).
        for f in REQUIRED_FIELDS:
            if f not in rec:
                issues.append(f"{case_id}: missing field {f!r}")
            elif rec[f] is None and f not in ("annotation_date",):
                issues.append(f"{case_id}: field {f!r} is null")

        # 5. Verdict in the spec set.
        verdict = rec.get("ground_truth_verdict")
        if isinstance(verdict, str) and not _has_todo(verdict):
            if verdict not in VERDICT_CLASSES:
                issues.append(
                    f"{case_id}: ground_truth_verdict {verdict!r} not in spec set"
                )

        # 6. review_confidence in canonical set.
        rc = rec.get("review_confidence")
        if isinstance(rc, str) and not _has_todo(rc):
            if rc not in ("high", "medium", "low"):
                issues.append(
                    f"{case_id}: review_confidence {rc!r} must be high|medium|low"
                )

        # 7. Reasoning ≥30 words.
        reasoning = rec.get("ground_truth_reasoning") or ""
        if isinstance(reasoning, str) and not _has_todo(reasoning):
            wc = len(reasoning.split())
            if wc < 30:
                issues.append(
                    f"{case_id}: ground_truth_reasoning has {wc} words; need ≥30"
                )

        # 8. Canonical few-shot tally.
        if rec.get("is_canonical_few_shot") is True:
            cls = rec.get("ground_truth_verdict")
            if isinstance(cls, str) and cls in VERDICT_CLASSES:
                canonical_per_class[cls] = canonical_per_class.get(cls, 0) + 1

        # 9. Package exists and parses.
        package_path = rec.get("package_path")
        if package_path:
            full = Path(package_path)
            if not full.is_absolute():
                full = repo_root / full
            if not full.exists():
                issues.append(f"{case_id}: package_path does not exist: {package_path}")
            else:
                try:
                    json.loads(full.read_text())
                except json.JSONDecodeError as e:
                    issues.append(f"{case_id}: package_path is not valid JSON: {e}")

        # 10. annotation_date.
        date_val = rec.get("annotation_date")
        if isinstance(date_val, str) and not _has_todo(date_val):
            # Loose check — must have a YYYY-MM-DD prefix.
            try:
                from datetime import date
                date.fromisoformat(date_val[:10])
            except ValueError:
                issues.append(
                    f"{case_id}: annotation_date {date_val!r} not parseable as ISO date"
                )

        # 11. REAL-GAP cases must have section_6_7_mapping populated
        # (per spec §13.2 catalog formalization workflow).
        if verdict == "REAL-GAP":
            s67 = rec.get("section_6_7_mapping")
            if not s67 or _has_todo(s67):
                issues.append(
                    f"{case_id}: REAL-GAP verdict requires section_6_7_mapping "
                    f"(per spec §13.2; ensures REAL-GAP feeds the §15 hard gate #13 "
                    f"catalog extension workflow)"
                )

        # W1. case_id contains a verdict token, which would leak the answer if
        # the prompt builder echoes case_id into the prompt. Suppressed by
        # --allow-verdict-in-case-id when the prompt builder strips the token.
        if not allow_verdict_in_case_id:
            case_id_lower = case_id.lower()
            leaks = sorted(t for t in VERDICT_TOKENS if t in case_id_lower)
            if leaks:
                warnings.append(
                    f"{case_id}: case_id contains verdict token {leaks[0]!r}. "
                    f"Confirm prompt builder uses phase2_case_id (or strips the "
                    f"verdict token) so the judge does not see the answer in "
                    f"the case_id. Pass --allow-verdict-in-case-id to silence."
                )

    # 8 (continued): each verdict class has exactly 1 canonical few-shot
    # (spec §7.1: "one canonical example per class drawn from calibration set").
    for cls in VERDICT_CLASSES:
        count = canonical_per_class.get(cls, 0)
        if count == 0:
            issues.append(
                f"verdict class {cls}: needs exactly 1 record with "
                f"is_canonical_few_shot=true (used as the v1.0.0 prompt's "
                f"few-shot anchor for this class)"
            )
        elif count > 1:
            issues.append(
                f"verdict class {cls}: has {count} records marked "
                f"is_canonical_few_shot=true; spec §7.1 requires exactly one "
                f"canonical example per class (otherwise the prompt has no "
                f"clear few-shot anchor)"
            )

    # 12. §6.7 Tier 1 candidate coverage across REAL-GAP cases.
    # Spec §15 hard gate #13 requires ≥3 of 6 candidates validated as REAL-GAP.
    # The calibration set must give the judges a chance to learn ≥4 of the 6
    # so the gate has a real anchor at full-corpus time.
    real_gap_mappings = set()
    for rec in records:
        if rec.get("ground_truth_verdict") == "REAL-GAP":
            mapping = rec.get("section_6_7_mapping")
            if isinstance(mapping, str) and not _has_todo(mapping):
                real_gap_mappings.add(mapping)
    covered = real_gap_mappings & SECTION_6_7_CANDIDATES
    if len(covered) < SECTION_6_7_MIN_COVERAGE:
        missing = sorted(SECTION_6_7_CANDIDATES - covered)
        issues.append(
            f"REAL-GAP §6.7 coverage: only {len(covered)} of "
            f"{len(SECTION_6_7_CANDIDATES)} candidates represented "
            f"(covered: {sorted(covered) or '[]'}; missing: {missing}). "
            f"Need ≥{SECTION_6_7_MIN_COVERAGE} for the §15 hard gate #13 "
            f"calibration anchor."
        )

    # W2. Source spec diversity within auto-selected verdict classes.
    # Within each auto-selected class, no single Phase 2 spec should account for
    # more than SOURCE_SPEC_MAX_PER_CLASS of 5 cases. Helps avoid calibrating on
    # one cluster of cases that all share idiosyncratic structure.
    from collections import Counter
    for cls in AUTO_SELECTED_CLASSES:
        spec_ids: list[str] = []
        for rec in records:
            if rec.get("ground_truth_verdict") != cls:
                continue
            p2_id = rec.get("phase2_case_id", "") or ""
            # Phase 2 case_id pattern: adv-2026-p2-NNN-<spec_slug>...; take first 4 parts.
            parts = p2_id.split("-")
            if len(parts) >= 4:
                spec_ids.append("-".join(parts[:4]))
        counts = Counter(spec_ids)
        most_common = counts.most_common(1)
        if most_common and most_common[0][1] > SOURCE_SPEC_MAX_PER_CLASS:
            warnings.append(
                f"verdict class {cls}: {most_common[0][1]} of "
                f"{EXPECTED_PER_CLASS} cases drawn from spec "
                f"{most_common[0][0]!r}. Diversity warning — distinct Phase 2 "
                f"specs preferred to avoid calibrating on a single cluster."
            )

    return issues, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "--in", dest="in_path", type=Path,
        default=Path("specs/calibration/calibration_set_v1.jsonl"),
        help="path to calibration set JSONL (default specs/calibration/calibration_set_v1.jsonl)",
    )
    parser.add_argument(
        "--repo-root", type=Path, default=None,
        help="repo root for resolving package_path (default: parents[3] of this script)",
    )
    parser.add_argument(
        "--allow-verdict-in-case-id", action="store_true",
        help="suppress W1 (verdict-token-in-case-id warning). Use only when the "
             "prompt builder is verified to strip verdict tokens from case_id "
             "or to use phase2_case_id instead.",
    )
    parser.add_argument(
        "--strict", action="store_true",
        help="treat warnings as failures (exit 1 on any warning).",
    )
    args = parser.parse_args()

    repo_root = args.repo_root or Path(__file__).resolve().parents[3]
    issues, warnings = validate(
        args.in_path,
        repo_root=repo_root,
        allow_verdict_in_case_id=args.allow_verdict_in_case_id,
    )

    # Print warnings first so they appear above the pass/fail summary.
    if warnings:
        print(f"WARN: {len(warnings)} warning(s) in {args.in_path}", file=sys.stderr)
        for w in warnings:
            print(f"  - {w}", file=sys.stderr)
        print("", file=sys.stderr)

    if issues:
        print(f"FAIL: {len(issues)} issue(s) in {args.in_path}\n", file=sys.stderr)
        for issue in issues:
            print(f"  - {issue}", file=sys.stderr)
        print(f"\nFix the issues above and re-run.", file=sys.stderr)
        return 1

    if args.strict and warnings:
        print(
            f"FAIL (--strict): {len(warnings)} warning(s) treated as failures.",
            file=sys.stderr,
        )
        return 1

    # Re-count for the success summary.
    records = [json.loads(l) for l in args.in_path.read_text().splitlines() if l.strip()]
    canonical = sum(1 for r in records if r.get("is_canonical_few_shot"))
    real_gap_mappings = sorted({
        r.get("section_6_7_mapping") for r in records
        if r.get("ground_truth_verdict") == "REAL-GAP"
        and isinstance(r.get("section_6_7_mapping"), str)
        and not _has_todo(r.get("section_6_7_mapping"))
    })
    print(f"PASS: {len(records)} records, {canonical} canonical few-shots")
    print(f"  REAL-GAP §6.7 coverage: {real_gap_mappings}")
    if warnings:
        print(f"  ({len(warnings)} non-blocking warning(s) — see stderr)")
    print(f"  ready for Stage 1 calibration runs (spec §8)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

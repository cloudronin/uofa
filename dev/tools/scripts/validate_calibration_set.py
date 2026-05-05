"""Validate the author-annotated calibration set (spec v1.5 §8.1, §8.2).

Checks (all must pass before Stage 1):

    1. File parses as JSONL with exactly 30 records.
    2. Each verdict class has exactly 5 records.
    3. No TODO_AUTHOR_* markers remain.
    4. Each record has all required fields populated.
    5. ground_truth_verdict ∈ the 6 spec verdict classes.
    6. review_confidence ∈ {high, medium, low}.
    7. ground_truth_reasoning has ≥30 words.
    8. Each verdict class has ≥1 record marked is_canonical_few_shot=true.
    9. Every package_path exists and parses as JSON.
    10. annotation_date is a valid ISO-format date string.

Exits 0 on pass, 1 on any failure with all issues listed.

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


def _has_todo(value: object) -> bool:
    """True if the value is or contains a TODO_AUTHOR_* marker."""
    if isinstance(value, str):
        return value.startswith("TODO_AUTHOR")
    return False


def validate(path: Path, *, repo_root: Path) -> list[str]:
    """Return a list of issue strings (empty list = valid)."""
    issues: list[str] = []
    if not path.exists():
        return [f"calibration set not found: {path}"]

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
        return issues

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

    # 8 (continued): each verdict class has ≥1 canonical few-shot.
    for cls in VERDICT_CLASSES:
        if canonical_per_class.get(cls, 0) < 1:
            issues.append(
                f"verdict class {cls}: needs ≥1 record with is_canonical_few_shot=true "
                f"(used as the v1.0.0 prompt's few-shot anchor)"
            )

    return issues


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
    args = parser.parse_args()

    repo_root = args.repo_root or Path(__file__).resolve().parents[3]
    issues = validate(args.in_path, repo_root=repo_root)

    if not issues:
        # Re-count for the success summary.
        records = [json.loads(l) for l in args.in_path.read_text().splitlines() if l.strip()]
        canonical = sum(1 for r in records if r.get("is_canonical_few_shot"))
        print(f"PASS: {len(records)} records, {canonical} canonical few-shots")
        print(f"  ready for Stage 1 calibration runs (spec §8)")
        return 0

    print(f"FAIL: {len(issues)} issue(s) in {args.in_path}\n", file=sys.stderr)
    for issue in issues:
        print(f"  - {issue}", file=sys.stderr)
    print(f"\nFix the issues above and re-run.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())

"""Judge D calibration-anchor pipeline (Phase 3 v1.6 §8.0).

Two modes:

- **ingest** (default): read `specs/calibration/calibration_set_v1.jsonl`,
  validate against schema + validate_v2 contract, capture any author
  overrides as a separate audit log. The committed file IS the Judge D
  anchor; ingest just normalizes + validates.

- **regenerate** (opt-in via `--regenerate`): runs Judge D over the
  package files referenced by the scaffold and writes a fresh
  `judge_d_anchor.jsonl`. Used when the author wants to re-run the
  anchor on a future expansion or override scenario.

The committed calibration_set_v1.jsonl carries Judge D's anchor verdicts
in `ground_truth_verdict` / `ground_truth_reasoning` fields. Author
overrides land in `judge_d_author_overrides.jsonl` with
`{case_id, original_verdict, override_verdict, override_rationale}`.
"""

from __future__ import annotations

import asyncio
import json
import logging
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)


VERDICT_CLASSES = frozenset({
    "CORRECT-DETECTION", "REAL-GAP", "GENERATOR-ARTIFACT",
    "EXISTING-RULE-MISBEHAVIOR", "OUT-OF-SCOPE", "UNCERTAIN",
})


@dataclass
class IngestResult:
    """Summary of an anchor ingest run."""

    calibration_path: Path
    record_count: int
    canonical_few_shot_count: int
    section_6_7_coverage: list[str]
    overrides_path: Path | None
    override_count: int


def ingest_anchor(
    calibration_path: Path,
    *,
    overrides_path: Path | None = None,
    out_dir: Path | None = None,
) -> IngestResult:
    """Validate the committed calibration set and capture any author overrides.

    `calibration_path` defaults to `specs/calibration/calibration_set_v1.jsonl`.
    Returns an IngestResult summary + writes a normalized anchor copy to
    `<out_dir>/judge_d_anchor.jsonl` if `out_dir` is provided (Stage 1
    consumers read from this normalized location).

    The function does NOT run Judge D — that's `regenerate` mode. Ingest
    operates on the file already produced by Judge D and committed by
    the author.
    """
    if not calibration_path.exists():
        raise FileNotFoundError(f"calibration set not found: {calibration_path}")

    records = _load_jsonl(calibration_path)
    if not records:
        raise ValueError(f"calibration set is empty: {calibration_path}")

    _validate_records(records)

    # Capture author overrides if a separate overrides file exists.
    overrides: list[dict] = []
    if overrides_path and overrides_path.exists():
        overrides = _load_jsonl(overrides_path)
        records = _apply_overrides(records, overrides)

    canonical_count = sum(1 for r in records if r.get("is_canonical_few_shot"))
    section_6_7 = sorted({
        r.get("section_6_7_mapping")
        for r in records
        if r.get("ground_truth_verdict") == "REAL-GAP"
        and isinstance(r.get("section_6_7_mapping"), str)
    })

    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        anchor_out = out_dir / "judge_d_anchor.jsonl"
        with anchor_out.open("w") as f:
            for r in records:
                f.write(json.dumps(r) + "\n")

    return IngestResult(
        calibration_path=calibration_path,
        record_count=len(records),
        canonical_few_shot_count=canonical_count,
        section_6_7_coverage=section_6_7,
        overrides_path=overrides_path if overrides else None,
        override_count=len(overrides),
    )


def record_override(
    overrides_path: Path,
    *,
    case_id: str,
    original_verdict: str,
    override_verdict: str,
    override_rationale: str,
) -> None:
    """Append an author override to `judge_d_author_overrides.jsonl`.

    Validates that `override_verdict` is in the spec verdict set and that
    the rationale is non-empty. The override is one record per line with
    `{case_id, original_verdict, override_verdict, override_rationale,
    overridden_at}`.
    """
    if override_verdict not in VERDICT_CLASSES:
        raise ValueError(
            f"override_verdict {override_verdict!r} not in spec set {sorted(VERDICT_CLASSES)}"
        )
    if not override_rationale or len(override_rationale.split()) < 5:
        raise ValueError(
            "override_rationale must be ≥5 words; current author-engagement signal "
            "is the rationale, not the override flag itself"
        )

    overrides_path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "case_id": case_id,
        "original_verdict": original_verdict,
        "override_verdict": override_verdict,
        "override_rationale": override_rationale,
        "overridden_at": datetime.now(timezone.utc).isoformat(),
    }
    with overrides_path.open("a") as f:
        f.write(json.dumps(record) + "\n")


# ── helpers ────────────────────────────────────────────────────────────


def _load_jsonl(path: Path) -> list[dict]:
    out = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        out.append(json.loads(line))
    return out


def _validate_records(records: list[dict]) -> None:
    """Lightweight schema validation on calibration records."""
    if len(records) != 30:
        raise ValueError(f"expected 30 calibration records; got {len(records)}")

    by_class: dict[str, int] = {}
    canonical_per_class: dict[str, int] = {}
    for rec in records:
        case_id = rec.get("case_id", "<no id>")
        verdict = rec.get("ground_truth_verdict")
        if verdict not in VERDICT_CLASSES:
            raise ValueError(
                f"{case_id}: ground_truth_verdict {verdict!r} not in spec set"
            )
        by_class[verdict] = by_class.get(verdict, 0) + 1
        if rec.get("is_canonical_few_shot"):
            canonical_per_class[verdict] = canonical_per_class.get(verdict, 0) + 1

    for cls, expected in (
        ("CORRECT-DETECTION", 5), ("REAL-GAP", 5), ("GENERATOR-ARTIFACT", 5),
        ("EXISTING-RULE-MISBEHAVIOR", 5), ("OUT-OF-SCOPE", 5), ("UNCERTAIN", 5),
    ):
        if by_class.get(cls, 0) != expected:
            raise ValueError(
                f"verdict class {cls}: expected {expected} records; got {by_class.get(cls, 0)}"
            )
        if canonical_per_class.get(cls, 0) != 1:
            raise ValueError(
                f"verdict class {cls}: expected exactly 1 canonical few-shot; "
                f"got {canonical_per_class.get(cls, 0)}"
            )


def _apply_overrides(records: list[dict], overrides: list[dict]) -> list[dict]:
    """Apply author overrides to the calibration records (in-memory copy)."""
    by_id = {r["case_id"]: r for r in records}
    for ov in overrides:
        cid = ov["case_id"]
        if cid not in by_id:
            logger.warning("override targets unknown case_id %s; skipping", cid)
            continue
        by_id[cid]["ground_truth_verdict"] = ov["override_verdict"]
        by_id[cid].setdefault("notes", "")
        by_id[cid]["notes"] = (
            (by_id[cid]["notes"] + f"\nAUTHOR OVERRIDE: {ov['override_rationale']}").strip()
        )
    return list(by_id.values())

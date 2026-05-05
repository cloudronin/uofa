"""Run idempotency / `--resume` support (spec v1.6 §11.5, plan Wave I).

Per-judge `judgments_<position>.jsonl` files are append-only — one JSON
object per case. On rerun with `--resume`, we:

  1. Read existing JSONL files for each judge to build a set of done
     case_ids.
  2. Skip cases already present in ALL active judges' files.
  3. Open the JSONL files in append mode so the resumed run continues
     where the previous one stopped.
  4. Tolerate corrupted trailing lines: a partial write at SIGTERM time
     leaves a malformed last line; the resume loader skips it (with a
     warning) and the case is re-judged.

We deliberately DON'T track partial-bundle progress in a separate
manifest — the JSONL files themselves are the source of truth. Manifest
files drift; JSONL doesn't.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def load_done_case_ids(jsonl_path: Path) -> set[str]:
    """Return the set of case_ids already judged in `jsonl_path`.

    Skips empty / malformed lines so a partial last write doesn't
    silently corrupt the resume set. The corrupted line is dropped at
    next-write time (we open in 'a' which appends; the broken line
    stays at its old position and the case re-judges into a new line).
    """
    if not jsonl_path.exists():
        return set()
    done: set[str] = set()
    for i, line in enumerate(jsonl_path.read_text().splitlines(), start=1):
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            logger.warning(
                "resume: skipping malformed line %d in %s", i, jsonl_path
            )
            continue
        cid = rec.get("case_id")
        if cid:
            done.add(cid)
    return done


def compute_remaining_cases(
    all_case_ids: list[str],
    done_per_judge: dict[str, set[str]],
) -> list[str]:
    """Return case_ids that still need at least one judge's verdict.

    A case is 'done' only when every active judge has produced a verdict
    for it. Any case missing from any judge is re-judged across ALL
    judges so the per-case row count stays consistent (downstream triage
    requires aligned trios).
    """
    if not done_per_judge:
        return list(all_case_ids)
    fully_done: set[str] = set.intersection(*done_per_judge.values()) \
        if done_per_judge else set()
    return [cid for cid in all_case_ids if cid not in fully_done]


def open_append_handles(
    out_dir: Path, positions: tuple[str, ...]
) -> dict[str, "object"]:
    """Open per-position judgments_<pos>.jsonl handles in append mode."""
    handles: dict[str, object] = {}
    for pos in positions:
        path = out_dir / f"judgments_{pos}.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        handles[pos] = path.open("a")
    return handles


def write_resume_manifest(
    *,
    out_dir: Path,
    bundle_path: Path,
    total_case_count: int,
    skipped_case_count: int,
    judged_case_count: int,
) -> None:
    """Write a small manifest describing what the resume run did.

    Audit-engineer-facing: lets us confirm the resume math at a glance
    without diffing JSONL files. Spec §11.5 wants this on every resumed
    run.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "resume_manifest.json").write_text(json.dumps({
        "bundle": str(bundle_path),
        "total_case_count": total_case_count,
        "skipped_case_count_resumed_from_existing": skipped_case_count,
        "judged_case_count_this_run": judged_case_count,
    }, indent=2))

"""refinement_log.jsonl reader/writer + predicate SHA tracking.

Per spec §7, every iteration (accepted, rejected, reverted, stuck)
writes one JSON record with predicate_before_sha / predicate_after_sha,
unified-diff path, rationale, train+dev metrics, decision, git_sha.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class IterationRecord:
    """One row of refinement_log.jsonl."""
    rule_id: str
    iteration: int
    timestamp: str
    proposed_by: str               # "claude_code" | "manual"
    review_decision: str           # "accepted" | "accepted-auto" | "rejected" | "reverted" | "stuck" | "loosened-rejected"
    predicate_before_sha: str
    predicate_after_sha: str
    predicate_diff_path: str
    rationale: str
    train_metrics: dict
    dev_metrics: dict
    decision: str                  # final state machine state
    git_sha: str
    holdout_metrics: dict | None = None
    notes: str = ""

    def to_jsonl(self) -> str:
        return json.dumps(asdict(self))


def predicate_sha(rule_body: str) -> str:
    """SHA-256 of a rule body. Used for predicate_before_sha / _after_sha."""
    return "sha256:" + hashlib.sha256(rule_body.encode("utf-8")).hexdigest()[:16]


def current_git_sha() -> str:
    """Best-effort; returns short SHA or 'unknown'."""
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], text=True
        ).strip()
    except Exception:
        return "unknown"


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class RefinementLog:
    """Append-only writer for refinement_log.jsonl.

    Idempotent on each call to ``append`` — caller is responsible for not
    duplicating iteration numbers per rule.
    """

    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, record: IterationRecord) -> None:
        with open(self.path, "a") as f:
            f.write(record.to_jsonl() + "\n")

    def read_all(self) -> list[dict]:
        if not self.path.exists():
            return []
        out = []
        with open(self.path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                out.append(json.loads(line))
        return out

    def records_for_rule(self, rule_id: str) -> list[dict]:
        return [r for r in self.read_all() if r.get("rule_id") == rule_id]

    def latest_iteration(self, rule_id: str) -> int:
        recs = self.records_for_rule(rule_id)
        return max((r["iteration"] for r in recs), default=0)


def write_predicate_diff(
    diff_text: str, out_dir: Path, rule_id: str, iteration: int
) -> Path:
    """Write a predicate unified-diff to predicate_diffs/{rule}_iter{N}.diff
    and return the path."""
    rule_slug = rule_id.lower().replace("-", "_")
    out_path = out_dir / f"{rule_slug}_iter{iteration:02d}.diff"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(diff_text)
    return out_path


def extract_rule_body(rules_file: Path, rule_name: str) -> str:
    """Extract a single Jena rule body by name from a rules file.

    Jena rule syntax: ``[name: ... -> ... ]``. We slice on the rule's
    opening bracket+name and the next top-level closing bracket. Tolerant
    of whitespace.
    """
    text = rules_file.read_text()
    # Find "[<rule_name>:" anywhere in the file. Allow optional whitespace.
    marker = f"[{rule_name}:"
    start = text.find(marker)
    if start == -1:
        raise ValueError(f"rule {rule_name!r} not found in {rules_file}")
    # Walk forward to find the matching ']' at the rule's bracket depth.
    depth = 0
    for i in range(start, len(text)):
        ch = text[i]
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    raise ValueError(f"no closing bracket for rule {rule_name!r}")

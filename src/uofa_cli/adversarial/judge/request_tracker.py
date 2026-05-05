"""Per-judge daily-request-cap tracker (sibling to BudgetTracker).

Vendor RPD (requests-per-day) limits force the Phase 3 v1.6 production
run across multiple UTC days. Gemini's 1,000 RPD cap on `gemini-2.5-pro`
is the binding constraint: 4,556 cases × 1 Gemini call/case > 1 day's
quota.

Design:
  - One `RequestTracker` per run, configured with per-judge caps
    (`{"gemini": 950, ...}`).
  - `authorize(token)` checks count vs cap *before* a call dispatch.
  - `record(token)` increments after a call (success OR failure — both
    burn quota).
  - `over_cap` flag fires once any judge has hit its cap; runner halts
    gracefully, writes a date-stamped manifest, and exits.
  - `read_manifest(path)` resumes the next day: if the manifest's
    `date` matches today (UTC), accumulate; if earlier, reset counts
    to zero (new day, fresh quota).

The runner's existing `--resume` flag (case-id idempotency) covers the
case-level resume; the RequestTracker covers the quota-level resume.
Together they let a single `uofa adversarial judge --resume
--max-requests-per-judge "gemini=950,..."` command be re-fired daily
until the corpus completes, without manually tracking what's been done.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path


def _utc_today() -> str:
    """ISO date string in UTC. The vendor quota windows reset at UTC
    midnight (Google AI Studio docs); using UTC keeps the rollover
    aligned with the vendor's accounting."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


@dataclass
class RequestTracker:
    """Per-judge call-count tracker with daily-cap enforcement.

    `per_judge_cap` keys are provider tokens (`openai`, `gemini`,
    `hf-llama`, etc.); values are the maximum number of requests
    allowed for that judge today. Tokens NOT in the dict are
    uncapped — vendors with generous limits don't need entries.
    """

    per_judge_cap: dict[str, int] = field(default_factory=dict)
    per_judge_count: dict[str, int] = field(default_factory=dict)
    date: str = field(default_factory=_utc_today)
    halted: bool = False
    halt_reason: str = ""

    def authorize(self, judge_token: str) -> bool:
        """Return True if a call to `judge_token` is within today's cap."""
        cap = self.per_judge_cap.get(judge_token)
        if cap is None:
            return True
        used = self.per_judge_count.get(judge_token, 0)
        if used >= cap:
            self.halted = True
            self.halt_reason = (
                f"per-judge daily cap hit: {judge_token} reached "
                f"{used}/{cap} on {self.date}"
            )
            return False
        return True

    def record(self, judge_token: str) -> None:
        """Increment the per-judge counter (success OR failure)."""
        self.per_judge_count[judge_token] = (
            self.per_judge_count.get(judge_token, 0) + 1
        )

    @property
    def over_cap(self) -> bool:
        """True when any judge has hit its cap."""
        return self.halted

    def write_manifest(self, path: Path) -> None:
        """Dump the tracker state to a JSON manifest for cross-day resume."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {
                    "date": self.date,
                    "per_judge_cap": dict(self.per_judge_cap),
                    "per_judge_count": dict(self.per_judge_count),
                    "halted": self.halted,
                    "halt_reason": self.halt_reason,
                },
                indent=2,
            )
        )

    @classmethod
    def from_manifest(
        cls,
        path: Path,
        *,
        per_judge_cap: dict[str, int],
    ) -> "RequestTracker":
        """Resume from a prior manifest, applying day-rollover semantics.

        - If the manifest's `date` matches today (UTC), restore counts
          → resumed run accumulates against the same daily cap.
        - If earlier (a different UTC day), reset counts to zero → new
          day, fresh quota.
        - If the manifest is missing or malformed, return a fresh
          tracker with the configured caps and zero counts.
        """
        if not path.exists():
            return cls(per_judge_cap=dict(per_judge_cap))

        try:
            data = json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            return cls(per_judge_cap=dict(per_judge_cap))

        prior_date = data.get("date")
        today = _utc_today()
        if prior_date == today:
            # Same UTC day — accumulate against existing counts.
            return cls(
                per_judge_cap=dict(per_judge_cap),
                per_judge_count=dict(data.get("per_judge_count", {})),
                date=today,
                halted=False,  # caller will re-enter judging; clear halt flag
                halt_reason="",
            )
        # Different day — reset counts to zero.
        return cls(per_judge_cap=dict(per_judge_cap))


def parse_per_judge_cap(arg: str | None) -> dict[str, int]:
    """Parse a CLI 'gemini=950,openai=2000' string into a dict.

    Empty / None input returns an empty dict (no caps). Mirrors the
    parsing convention used for `--concurrency-per-judge`.
    """
    if not arg:
        return {}
    out: dict[str, int] = {}
    for pair in arg.split(","):
        pair = pair.strip()
        if not pair or "=" not in pair:
            continue
        k, v = pair.split("=", 1)
        try:
            out[k.strip()] = int(v.strip())
        except ValueError:
            raise ValueError(
                f"--max-requests-per-judge: bad value {pair!r}"
            ) from None
    return out

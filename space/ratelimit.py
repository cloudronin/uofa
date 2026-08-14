"""Bound what a public Space can spend at a metered provider.

Together AI offers no spend cap, so the ceiling has to live here.

Three limits, because they stop different things, and it matters which one is
actually protecting the money:

**Per session** (`SESSION_LIMIT`) is fairness, not cost control. It stops a
visitor re-running the same analysis a dozen times. It does NOT stop a crawler:
Gradio session state is per browser session, so anything loading the page fresh
gets a fresh counter. Treating a session limit as a spend cap is the mistake
this docstring exists to prevent.

**Per day, in dollars** (`DAILY_USD_LIMIT`) is the real cap. It is backed by a
ledger in a private HF Dataset, so it survives the container restarts that a
sleeping Space does constantly -- an in-process counter resets every wake, which
would let the same budget be spent again each time.

**Per hour, in-process** (`HOURLY_LIMIT`) is a burst brake. It bounds a spike
that arrives faster than the ledger round-trip, and it is the only limit still
standing if the dataset is unreachable.

Cost is ESTIMATED, deliberately and visibly. `generate()` returns a bare string,
so exact provider usage is not available without changing the shared CLI
interface; the estimate uses the corpus token count we already compute and the
response length we already have. It is good to roughly the right factor, which
is what a guard needs -- it is not an invoice, and the ledger records it as
`estimated_usd` so nobody later mistakes it for one.

Only metered calls count. Local and mock backends are free, so a developer, the
test suite, and an unconfigured deployment are never limited: otherwise the
limiter would be the thing that breaks local development.

Config (Space secrets / env):
  UOFA_SPACE_DAILY_USD     default 5.0
  UOFA_SPACE_SESSION_LIMIT default 8
  UOFA_SPACE_HOURLY_LIMIT  default 60
  HF_DATASET_REPO, HF_TOKEN   the ledger (shared with leadcapture)
"""

from __future__ import annotations

import io
import json
import logging
import os
import re
import threading
import time
from datetime import datetime, timezone

_log = logging.getLogger("uofa.space.budget")


def _num_env(name: str, default: float) -> float:
    try:
        value = float(os.environ.get(name, "").strip())
    except (TypeError, ValueError):
        return default
    return value if value > 0 else default


SESSION_LIMIT = int(_num_env("UOFA_SPACE_SESSION_LIMIT", 8))
HOURLY_LIMIT = int(_num_env("UOFA_SPACE_HOURLY_LIMIT", 60))
DAILY_USD_LIMIT = _num_env("UOFA_SPACE_DAILY_USD", 5.0)

WINDOW_SECONDS = 3600
LEDGER_PREFIX = "usage"
_REFRESH_SECONDS = 300

# Rough per-token prices for the default hosted model, used only when litellm
# has no entry. Over-estimating is the safe direction for a guard.
_FALLBACK_USD_PER_1M = 0.90

_lock = threading.Lock()
_recent: list[float] = []          # timestamps, for the hourly brake
_day: str | None = None            # UTC date the counters below belong to
_ledger_usd = 0.0                  # last total read from the dataset
_local_usd = 0.0                   # spent since that read, this process
_ledger_read_at = 0.0
_ledger_ever_read = False

SESSION_MESSAGE = (
    "You have run the maximum number of analyses for one session. This is a "
    "public demo on a metered model, so each run costs real money. Reload to "
    "start a new session, or run the CLI locally for unlimited use:\n\n"
    "`pip install \"uofa[extract]\"`"
)

BUDGET_MESSAGE = (
    "This demo has reached its daily analysis budget. It runs on a metered "
    "model with a fixed allowance and stops rather than billing without bound. "
    "Please try again tomorrow, or run the CLI locally for unlimited use:\n\n"
    "`pip install \"uofa[extract]\"`"
)

BUSY_MESSAGE = (
    "This demo is handling more analyses than it allows in one hour. Please try "
    "again shortly, or run the CLI locally for unlimited use:\n\n"
    "`pip install \"uofa[extract]\"`"
)


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def estimate_usd(input_tokens: int, output_tokens: int, llm_config=None) -> float:
    """Estimated cost of one call. Never raises; 0.0 for local backends."""
    if llm_config is None:
        return 0.0
    try:
        from uofa_cli.llm import get_backend

        cost = get_backend(llm_config).estimate_cost(input_tokens, output_tokens)
        if cost and cost > 0:
            return float(cost)
    except Exception:  # noqa: BLE001 - pricing lookup must never break a run
        pass
    return (input_tokens + output_tokens) / 1_000_000 * _FALLBACK_USD_PER_1M


# ── the ledger ───────────────────────────────────────────────────


def _micros(usd: float) -> int:
    return max(0, int(round(usd * 1_000_000)))


_NAME_RE = re.compile(r"-(\d+)u\.json$")


def _read_ledger_usd(day: str) -> float | None:
    """Today's total from the dataset, or None if unavailable.

    The amount is encoded in each filename, so this is ONE list call with no
    downloads however many runs the day holds.
    """
    repo = os.environ.get("HF_DATASET_REPO")
    token = os.environ.get("HF_TOKEN")
    if not repo or not token:
        return None
    try:
        from huggingface_hub import HfApi

        files = HfApi(token=token).list_repo_files(repo_id=repo, repo_type="dataset")
    except Exception as exc:  # noqa: BLE001
        _log.warning("usage ledger unreadable: %s", exc)
        return None

    total = 0
    prefix = f"{LEDGER_PREFIX}/{day}/"
    for name in files:
        if not name.startswith(prefix):
            continue
        m = _NAME_RE.search(name)
        if m:
            total += int(m.group(1))
    return total / 1_000_000


def _append_ledger(day: str, record: dict, usd: float) -> None:
    """One uniquely-named file per run: no read-modify-write race, and the
    amount lives in the name so totalling never downloads anything."""
    repo = os.environ.get("HF_DATASET_REPO")
    token = os.environ.get("HF_TOKEN")
    if not repo or not token:
        return
    try:
        from huggingface_hub import HfApi

        stamp = record["timestamp"].replace(":", "-")
        name = f"{LEDGER_PREFIX}/{day}/{stamp}-{os.getpid()}-{_micros(usd)}u.json"
        HfApi(token=token).upload_file(
            path_or_fileobj=io.BytesIO(json.dumps(record).encode("utf-8")),
            path_in_repo=name, repo_id=repo, repo_type="dataset",
        )
    except Exception as exc:  # noqa: BLE001 - a ledger write must never fail a run
        _log.warning("usage ledger write failed: %s", exc)


def _roll_day(day: str) -> None:
    """Caller holds the lock."""
    global _day, _ledger_usd, _local_usd, _ledger_read_at, _ledger_ever_read
    if _day != day:
        _day, _ledger_usd, _local_usd = day, 0.0, 0.0
        _ledger_read_at, _ledger_ever_read = 0.0, False


def spent_today(now: float | None = None, *, force: bool = False) -> float:
    """Best known spend for the current UTC day.

    Refreshed from the dataset at most every _REFRESH_SECONDS; between reads the
    in-process delta is added, so concurrent containers under-count each other
    but never under-count themselves.
    """
    now = time.time() if now is None else now
    day = _today()
    with _lock:
        _roll_day(day)
        stale = force or (now - _ledger_read_at) > _REFRESH_SECONDS
        if not stale:
            return _ledger_usd + _local_usd
    total = _read_ledger_usd(day)          # network call outside the lock
    with _lock:
        _roll_day(day)
        globals()["_ledger_read_at"] = now
        if total is not None:
            globals()["_ledger_usd"] = total
            globals()["_local_usd"] = 0.0
            globals()["_ledger_ever_read"] = True
        return _ledger_usd + _local_usd


# ── the gate ─────────────────────────────────────────────────────


def consume(session_used: int, *, metered: bool = True,
            now: float | None = None) -> tuple[bool, str | None]:
    """Claim one analysis. Returns (allowed, message_when_refused).

    Checked BEFORE the model call, so a refusal costs nothing. `metered` is
    False for local/mock backends, which are never limited.

    On a ledger the process has never managed to read, this allows and leans on
    the hourly brake: failing closed would take the demo down for a transient
    HF outage, and failing open with no brake at all would be the unbounded
    bill this module exists to prevent.
    """
    if not metered:
        return True, None

    if session_used >= SESSION_LIMIT:
        return False, SESSION_MESSAGE

    now = time.time() if now is None else now
    if spent_today(now) >= DAILY_USD_LIMIT:
        return False, BUDGET_MESSAGE

    with _lock:
        cutoff = now - WINDOW_SECONDS
        _recent[:] = [t for t in _recent if t >= cutoff]
        if len(_recent) >= HOURLY_LIMIT:
            return False, BUSY_MESSAGE
        _recent.append(now)
    return True, None


def record(*, pack: str, input_tokens: int, output_tokens: int,
           llm_config=None, usd: float | None = None) -> float:
    """Book the cost of a completed run. Returns the amount charged.

    Called AFTER the run, when the response size is known. Never raises: a
    ledger failure must not turn a successful analysis into an error the user
    sees.
    """
    usd = estimate_usd(input_tokens, output_tokens, llm_config) if usd is None else usd
    day = _today()
    # The in-process total is updated FIRST and unconditionally. If the durable
    # write then fails, this run still counts against the cap for the life of
    # the process -- the safe direction for a guard.
    with _lock:
        _roll_day(day)
        globals()["_local_usd"] = _local_usd + usd
    try:
        _append_ledger(day, {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "pack": pack,
            "input_tokens": int(input_tokens),
            "output_tokens": int(output_tokens),
            "estimated_usd": round(usd, 6),
            "model": getattr(llm_config, "model", None),
        }, usd)
    except Exception as exc:  # noqa: BLE001
        # _append_ledger guards internally too. Guarding again here is not
        # redundant: this function's contract is "never raises", and a contract
        # that depends on the callee keeping its own is one refactor from being
        # false. Accounting must never turn a good analysis into an error.
        _log.warning("usage ledger write failed: %s", exc)
    return usd


def snapshot(now: float | None = None) -> dict:
    """Current usage, for logs and tests. Never shown to users."""
    return {
        "spent_today_usd": round(spent_today(now), 4),
        "daily_limit_usd": DAILY_USD_LIMIT,
        "hour_used": len(_recent),
        "hour_limit": HOURLY_LIMIT,
        "session_limit": SESSION_LIMIT,
        "ledger_ever_read": _ledger_ever_read,
    }


def reset() -> None:
    """Clear process-wide state. Tests only."""
    with _lock:
        _recent.clear()
        globals().update(_day=None, _ledger_usd=0.0, _local_usd=0.0,
                         _ledger_read_at=0.0, _ledger_ever_read=False)

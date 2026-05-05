"""Per-judge tokens-per-minute (TPM) tracker with sliding-window throttle.

Sibling to RequestTracker (which is a daily counter for vendor RPD
limits). TokenRateTracker enforces TPM ceilings via a 1-minute sliding
window: before a call, the tracker computes how many tokens would
fall inside the window and asks the caller to sleep until the window
has rolled forward enough to admit the new call.

Use case: Mistral Large 2's 600K TPM cap is reachable on a 30-case
arbitration sweep at ~7K input tokens/case + 800 output if concurrency
is too aggressive. Rather than hard-halting (RequestTracker's
behavior for daily caps), TPM throttling is naturally a soft pause —
the window resets within seconds.

Key API:
  - `await tracker.sleep_until_authorized(judge_token, projected_tokens)`
    blocks the caller until the projected call fits inside the
    next 1-minute window. No-op when no cap is configured.
  - `tracker.record(judge_token, actual_tokens)` appends a (timestamp,
    count) entry; older entries fall out of the window automatically.
"""

from __future__ import annotations

import asyncio
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Deque


WINDOW_SECONDS = 60.0


@dataclass
class _Entry:
    """One recorded call's contribution to the per-judge TPM window."""

    ts: float  # monotonic seconds
    tokens: int


@dataclass
class TokenRateTracker:
    """Per-judge TPM tracker with 1-minute sliding window.

    `per_judge_tpm` keys are provider tokens (`mistral`, `gemini`, ...);
    values are the maximum sum of input+output tokens permitted across
    a sliding 60-second window. Tokens NOT in the dict are uncapped
    (`authorize` and `sleep_until_authorized` are no-ops for them).

    The tracker uses `time.monotonic()` so it's robust to wall-clock
    jumps (NTP sync, DST). A 1-second floor on the sleep duration
    avoids busy-spinning on tight windows.
    """

    per_judge_tpm: dict[str, int] = field(default_factory=dict)
    _windows: dict[str, Deque[_Entry]] = field(default_factory=dict)

    def _window(self, judge_token: str) -> Deque[_Entry]:
        if judge_token not in self._windows:
            self._windows[judge_token] = deque()
        return self._windows[judge_token]

    def _expire(self, w: Deque[_Entry], now: float) -> None:
        """Drop entries older than WINDOW_SECONDS from the left."""
        cutoff = now - WINDOW_SECONDS
        while w and w[0].ts < cutoff:
            w.popleft()

    def current_tokens(self, judge_token: str) -> int:
        """Sum of tokens currently inside the window."""
        w = self._window(judge_token)
        self._expire(w, time.monotonic())
        return sum(e.tokens for e in w)

    def authorize(self, judge_token: str, projected_tokens: int) -> bool:
        """True if a call costing `projected_tokens` fits the window now."""
        cap = self.per_judge_tpm.get(judge_token)
        if cap is None:
            return True
        if projected_tokens >= cap:
            # Single call exceeds the entire cap — structurally unsendable.
            # Caller should treat this as a configuration error rather
            # than retry. Return True so the call proceeds and the
            # vendor returns whatever it returns (likely a 400).
            return True
        return self.current_tokens(judge_token) + projected_tokens <= cap

    async def sleep_until_authorized(
        self, judge_token: str, projected_tokens: int
    ) -> None:
        """Block until a call costing `projected_tokens` fits the window.

        Computes how long until the oldest in-window entry expires
        enough room. Sleeps that duration, then re-checks. Loops until
        authorize returns True.
        """
        cap = self.per_judge_tpm.get(judge_token)
        if cap is None:
            return
        if projected_tokens >= cap:
            # Structurally unsendable — see `authorize`.
            return
        while True:
            w = self._window(judge_token)
            now = time.monotonic()
            self._expire(w, now)
            current = sum(e.tokens for e in w)
            if current + projected_tokens <= cap:
                return
            # Find the oldest entry whose expiration would free up
            # enough room. Conservative: pop oldest entries until
            # `current + projected_tokens <= cap` would hold; sleep
            # until that entry's age exceeds WINDOW_SECONDS.
            needed = (current + projected_tokens) - cap
            freed = 0
            target_ts = w[0].ts if w else now
            for entry in w:
                freed += entry.tokens
                target_ts = entry.ts
                if freed >= needed:
                    break
            sleep_for = max(1.0, (target_ts + WINDOW_SECONDS) - now)
            await asyncio.sleep(sleep_for)

    def record(self, judge_token: str, actual_tokens: int) -> None:
        """Append a window entry after a call completes."""
        cap = self.per_judge_tpm.get(judge_token)
        if cap is None:
            return  # not tracked; skip the bookkeeping
        w = self._window(judge_token)
        w.append(_Entry(ts=time.monotonic(), tokens=int(actual_tokens)))
        self._expire(w, time.monotonic())


def parse_per_judge_tpm(arg: str | None) -> dict[str, int]:
    """Parse a CLI 'mistral=550000,gemini=950000' string into a dict.

    Empty / None input returns an empty dict (no caps). Mirrors the
    parsing convention used for `--max-requests-per-judge` and
    `--concurrency-per-judge`.
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
                f"--max-tpm-per-judge: bad value {pair!r}"
            ) from None
    return out


def caps_from_capability_table(judge_tokens: list[str]) -> dict[str, int]:
    """Resolve default TPM caps from the capability table for a list of tokens.

    Convenience for the CLI: when `--max-tpm-per-judge` is NOT set, we
    auto-populate caps from each judge's `default_tpm_cap`. Tokens
    without a default tpm cap are omitted (uncapped).
    """
    from uofa_cli.adversarial.judge.providers.capabilities import (
        get_capabilities,
    )
    out: dict[str, int] = {}
    for token in judge_tokens:
        try:
            cap = get_capabilities(token).default_tpm_cap
        except KeyError:
            continue
        if cap is not None:
            out[token] = cap
    return out

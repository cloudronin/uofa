"""Tests for TokenRateTracker — 1-minute sliding-window TPM throttle."""

from __future__ import annotations

import asyncio
import time
from unittest.mock import patch

import pytest

from uofa_cli.adversarial.judge.token_rate_tracker import (
    TokenRateTracker,
    caps_from_capability_table,
    parse_per_judge_tpm,
)


# ── authorize() ─────────────────────────────────────────────────────────


class TestAuthorize:
    def test_uncapped_token_always_authorized(self) -> None:
        t = TokenRateTracker(per_judge_tpm={"mistral": 1000})
        # 'openai' isn't in per_judge_tpm → uncapped → always True.
        for _ in range(100):
            assert t.authorize("openai", 100_000) is True

    def test_authorize_when_under_cap(self) -> None:
        t = TokenRateTracker(per_judge_tpm={"mistral": 1000})
        t.record("mistral", 500)
        assert t.authorize("mistral", 400) is True  # 500+400=900 ≤ 1000

    def test_blocks_when_window_would_exceed(self) -> None:
        t = TokenRateTracker(per_judge_tpm={"mistral": 1000})
        t.record("mistral", 800)
        # 800 + 300 > 1000 → False
        assert t.authorize("mistral", 300) is False

    def test_returns_true_when_single_call_exceeds_cap(self) -> None:
        # Single call larger than the entire cap is structurally unsendable;
        # we return True so the vendor's own error surfaces (caller can't
        # fix it by waiting). Tracker treats it as a config error.
        t = TokenRateTracker(per_judge_tpm={"mistral": 1000})
        assert t.authorize("mistral", 5_000) is True


# ── current_tokens() + window expiry ────────────────────────────────────


class TestWindowExpiry:
    def test_old_entries_drop_after_window(self) -> None:
        # Stuff entries directly into the deque with controlled timestamps,
        # then call current_tokens which expires older-than-window entries.
        from uofa_cli.adversarial.judge.token_rate_tracker import (
            WINDOW_SECONDS, _Entry,
        )
        t = TokenRateTracker(per_judge_tpm={"mistral": 1000})
        now = time.monotonic()
        # Old entry: 65s ago → outside the 60s window.
        t._window("mistral").append(_Entry(ts=now - 65.0, tokens=500))
        # Recent entry: 30s ago → inside the window.
        t._window("mistral").append(_Entry(ts=now - 30.0, tokens=300))
        # Only the recent entry should remain.
        assert t.current_tokens("mistral") == 300
        # And the deque should have only 1 entry now (the old was popped).
        assert len(t._window("mistral")) == 1

    def test_record_no_op_when_uncapped(self) -> None:
        t = TokenRateTracker(per_judge_tpm={"mistral": 1000})
        t.record("openai", 50_000)  # not tracked
        assert t.current_tokens("openai") == 0


# ── sleep_until_authorized() ────────────────────────────────────────────


class TestSleepUntilAuthorized:
    def test_no_op_when_uncapped(self) -> None:
        t = TokenRateTracker(per_judge_tpm={"mistral": 1000})
        async def go():
            await t.sleep_until_authorized("openai", 100_000)
            return True
        # Returns immediately.
        assert asyncio.run(go()) is True

    def test_returns_immediately_when_under_cap(self) -> None:
        t = TokenRateTracker(per_judge_tpm={"mistral": 1000})
        t.record("mistral", 200)
        async def go():
            await t.sleep_until_authorized("mistral", 400)
            return True
        assert asyncio.run(go()) is True

    def test_sleeps_when_over_cap(self) -> None:
        # Stuff a recent entry that fills the window, then call
        # sleep_until_authorized with enough projected tokens to push
        # over. asyncio.sleep is patched so we count invocations and
        # synthesize "time has passed" by mutating the entry's timestamp
        # to be old enough that the next loop iteration admits the call.
        from uofa_cli.adversarial.judge.token_rate_tracker import (
            TokenRateTracker as TRT, WINDOW_SECONDS, _Entry,
        )
        sleep_calls: list[float] = []

        async def fake_sleep(d: float) -> None:
            sleep_calls.append(d)
            # Shift the entry's timestamp into the past so the next
            # loop iteration sees the window as empty.
            t._window("mistral")[0].ts -= (WINDOW_SECONDS + 5.0)

        t = TRT(per_judge_tpm={"mistral": 1000})
        t._window("mistral").append(_Entry(ts=time.monotonic(), tokens=800))

        with patch(
            "uofa_cli.adversarial.judge.token_rate_tracker.asyncio.sleep",
            side_effect=fake_sleep,
        ):
            asyncio.run(t.sleep_until_authorized("mistral", 400))

        assert len(sleep_calls) == 1
        assert sleep_calls[0] >= 1.0  # 1s floor


# ── parse_per_judge_tpm ────────────────────────────────────────────────


class TestParsePerJudgeTpm:
    def test_basic(self) -> None:
        assert parse_per_judge_tpm("mistral=550000,gemini=950000") == {
            "mistral": 550_000, "gemini": 950_000,
        }

    def test_empty_input(self) -> None:
        assert parse_per_judge_tpm(None) == {}
        assert parse_per_judge_tpm("") == {}

    def test_whitespace_tolerated(self) -> None:
        assert parse_per_judge_tpm(" mistral = 550000 , gemini=950000 ") == {
            "mistral": 550_000, "gemini": 950_000,
        }

    def test_bad_value_raises(self) -> None:
        with pytest.raises(ValueError, match="bad value"):
            parse_per_judge_tpm("mistral=notanumber")


# ── caps_from_capability_table ─────────────────────────────────────────


class TestCapsFromCapabilityTable:
    def test_picks_up_defaults_from_capabilities(self) -> None:
        # Mistral, Gemini, OpenAI, Anthropic all have default_tpm_cap set;
        # hf-llama is None (Sambanova doesn't publish TPM).
        caps = caps_from_capability_table([
            "mistral", "gemini", "openai", "anthropic", "hf-llama"
        ])
        assert "mistral" in caps and caps["mistral"] == 550_000
        assert "gemini" in caps and caps["gemini"] == 950_000
        assert "openai" in caps and caps["openai"] == 750_000
        assert "anthropic" in caps and caps["anthropic"] == 750_000
        assert "hf-llama" not in caps  # uncapped

    def test_skips_unknown_tokens(self) -> None:
        # Don't crash on bogus tokens; just skip them.
        caps = caps_from_capability_table(["mistral", "fake-token"])
        assert "mistral" in caps
        assert "fake-token" not in caps

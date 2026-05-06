"""Tests for the exponential-backoff retry decorator."""

from __future__ import annotations

import asyncio
import time

import pytest

# Async test cases use @pytest.mark.asyncio which requires pytest-asyncio.
# Listed in the [judge] optional extras (pyproject.toml). Skip cleanly
# when extras aren't installed so a base-only `pytest tests/` doesn't
# error out on the unknown marker.
pytest.importorskip("pytest_asyncio", reason="install [judge] extras")

from uofa_cli.adversarial.judge.retry import (
    DEFAULT_MAX_RETRIES,
    TransientError,
    _compute_delay,
    with_retry,
)


# ── _compute_delay ──────────────────────────────────────────────────────


class TestComputeDelay:
    def test_first_attempt_uses_initial_delay(self) -> None:
        # attempt=0, factor=2.0, initial=1.0, no jitter → 1.0
        d = _compute_delay(0, 1.0, 2.0, 0.0, None)
        assert d == 1.0

    def test_backoff_doubles(self) -> None:
        d0 = _compute_delay(0, 1.0, 2.0, 0.0, None)
        d1 = _compute_delay(1, 1.0, 2.0, 0.0, None)
        d2 = _compute_delay(2, 1.0, 2.0, 0.0, None)
        assert d0 == 1.0 and d1 == 2.0 and d2 == 4.0

    def test_jitter_within_bounds(self) -> None:
        # ±25% of 1.0 → in [0.75, 1.25]
        for _ in range(50):
            d = _compute_delay(0, 1.0, 2.0, 0.25, None)
            assert 0.75 <= d <= 1.25

    def test_retry_after_overrides_schedule(self) -> None:
        # Server says 10s; jitter 0; should be exactly 10.
        d = _compute_delay(0, 1.0, 2.0, 0.0, retry_after=10.0)
        assert d == 10.0

    def test_negative_jitter_clamps_at_zero(self) -> None:
        # Edge case: huge jitter (200%) on a tiny base; should never go negative.
        for _ in range(20):
            d = _compute_delay(0, 0.001, 2.0, 2.0, None)
            assert d >= 0.0


# ── sync decorator ──────────────────────────────────────────────────────


class TestSyncDecorator:
    def test_returns_value_on_success(self) -> None:
        @with_retry()
        def succeed() -> int:
            return 42
        assert succeed() == 42

    def test_retries_on_transient_then_succeeds(self) -> None:
        attempts = {"n": 0}

        @with_retry(max_retries=3, initial_delay=0.001, jitter=0.0)
        def flaky() -> str:
            attempts["n"] += 1
            if attempts["n"] < 3:
                raise TransientError("simulated 503")
            return "ok"

        assert flaky() == "ok"
        assert attempts["n"] == 3

    def test_gives_up_after_max_retries(self) -> None:
        attempts = {"n": 0}

        @with_retry(max_retries=2, initial_delay=0.001, jitter=0.0)
        def always_fails() -> str:
            attempts["n"] += 1
            raise TransientError("perma-503")

        with pytest.raises(TransientError, match="perma-503"):
            always_fails()
        # Initial call + 2 retries = 3 attempts.
        assert attempts["n"] == 3

    def test_non_transient_error_propagates_immediately(self) -> None:
        attempts = {"n": 0}

        @with_retry(max_retries=5, initial_delay=0.001)
        def boom() -> None:
            attempts["n"] += 1
            raise ValueError("schema validation failed")

        with pytest.raises(ValueError):
            boom()
        # Only the first call ran; no retries on non-TransientError.
        assert attempts["n"] == 1

    def test_default_max_retries_is_3(self) -> None:
        assert DEFAULT_MAX_RETRIES == 3


# ── async decorator ─────────────────────────────────────────────────────


class TestAsyncDecorator:
    @pytest.mark.asyncio
    async def test_async_succeeds_on_first_call(self) -> None:
        @with_retry()
        async def succeed() -> int:
            return 7
        assert await succeed() == 7

    @pytest.mark.asyncio
    async def test_async_retries_then_succeeds(self) -> None:
        attempts = {"n": 0}

        @with_retry(max_retries=3, initial_delay=0.001, jitter=0.0)
        async def flaky() -> str:
            attempts["n"] += 1
            if attempts["n"] < 2:
                raise TransientError("503")
            return "ok"

        assert await flaky() == "ok"
        assert attempts["n"] == 2

    @pytest.mark.asyncio
    async def test_async_gives_up(self) -> None:
        @with_retry(max_retries=1, initial_delay=0.001, jitter=0.0)
        async def boom() -> None:
            raise TransientError("perma")

        with pytest.raises(TransientError):
            await boom()


class TestRetryAfterHonored:
    def test_retry_after_short_delay_actually_waits(self) -> None:
        attempts = {"n": 0}

        @with_retry(max_retries=1, initial_delay=10.0, jitter=0.0)
        def flaky() -> str:
            attempts["n"] += 1
            if attempts["n"] < 2:
                # Server says 0.05s; we should wait ~that, not the
                # 10s-initial baseline.
                raise TransientError("rl", retry_after=0.05)
            return "ok"

        start = time.monotonic()
        assert flaky() == "ok"
        elapsed = time.monotonic() - start
        # Should be ~0.05s, well under the 10s baseline.
        assert elapsed < 1.0

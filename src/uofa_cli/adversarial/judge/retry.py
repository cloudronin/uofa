"""Exponential-backoff retry decorator for judge API calls (spec v1.5 §9.2).

Configuration:
    - Max retries: 3 per call
    - Initial delay: 1.0s, backoff factor 2.0 (1s → 2s → 4s)
    - Jitter: ±25% of computed delay (uniform)
    - Retry classes: HTTP 5xx, timeout, rate limit (429 with Retry-After)
    - Never retry: HTTP 4xx (except 429), schema validation, auth errors

Used by both sync and async provider call sites. The decorator detects
whether the wrapped callable is a coroutine via `asyncio.iscoroutinefunction`
and dispatches accordingly.
"""

from __future__ import annotations

import asyncio
import inspect
import logging
import random
import time
from collections.abc import Awaitable
from functools import wraps
from typing import Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")

DEFAULT_MAX_RETRIES = 3
DEFAULT_INITIAL_DELAY = 1.0
DEFAULT_BACKOFF_FACTOR = 2.0
DEFAULT_JITTER = 0.25  # ±25%


class TransientError(Exception):
    """Marker base class — raise this from provider code to opt into retry.

    Provider adapters should translate vendor-specific transient errors
    (httpx.TimeoutException, openai.RateLimitError, openai.APIStatusError
    with 5xx code, etc.) into TransientError before the decorator sees them.
    The decorator only retries TransientError; all other exceptions
    propagate immediately.
    """

    def __init__(self, message: str, *, retry_after: float | None = None):
        super().__init__(message)
        self.retry_after = retry_after


def _compute_delay(
    attempt: int,
    initial: float,
    factor: float,
    jitter: float,
    retry_after: float | None,
) -> float:
    """Delay before the next retry. `attempt` is 0-indexed (0 = first retry)."""
    if retry_after is not None and retry_after > 0:
        # Server-supplied delay overrides the schedule. Spec §9.2 says
        # "honor Retry-After"; jitter still applies so callers don't
        # thunder.
        base = retry_after
    else:
        base = initial * (factor ** attempt)
    j = random.uniform(-jitter, jitter)
    return max(0.0, base * (1.0 + j))


def with_retry(
    max_retries: int = DEFAULT_MAX_RETRIES,
    initial_delay: float = DEFAULT_INITIAL_DELAY,
    backoff_factor: float = DEFAULT_BACKOFF_FACTOR,
    jitter: float = DEFAULT_JITTER,
):
    """Decorator factory: wrap a callable with exponential backoff.

    Works on both sync and async callables. Only TransientError instances
    trigger retries; all other exceptions propagate immediately. After
    `max_retries` retries, the last TransientError is re-raised.

    Example::

        @with_retry(max_retries=3)
        async def call_openai(case): ...

        @with_retry()
        def call_hf(case): ...
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                last_exc: TransientError | None = None
                for attempt in range(max_retries + 1):
                    try:
                        return await func(*args, **kwargs)
                    except TransientError as e:
                        last_exc = e
                        if attempt >= max_retries:
                            break
                        delay = _compute_delay(
                            attempt, initial_delay, backoff_factor, jitter, e.retry_after
                        )
                        logger.info(
                            "retry %d/%d after %.2fs: %s",
                            attempt + 1, max_retries, delay, e,
                        )
                        await asyncio.sleep(delay)
                assert last_exc is not None
                raise last_exc
            return async_wrapper  # type: ignore[return-value]

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            last_exc: TransientError | None = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except TransientError as e:
                    last_exc = e
                    if attempt >= max_retries:
                        break
                    delay = _compute_delay(
                        attempt, initial_delay, backoff_factor, jitter, e.retry_after
                    )
                    logger.info(
                        "retry %d/%d after %.2fs: %s",
                        attempt + 1, max_retries, delay, e,
                    )
                    time.sleep(delay)
            assert last_exc is not None
            raise last_exc

        return sync_wrapper

    return decorator

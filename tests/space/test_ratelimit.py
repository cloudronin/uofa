"""The spend guard.

Together AI has no spend cap, so this module is the ceiling. Hermetic: the
ledger is monkeypatched, nothing touches HuggingFace or a provider.
"""

from __future__ import annotations

import pytest

from space import ratelimit as rl


@pytest.fixture(autouse=True)
def clean():
    rl.reset()
    yield
    rl.reset()


@pytest.fixture
def no_ledger(monkeypatch):
    """No dataset configured: spent_today() sees nothing, writes are no-ops."""
    monkeypatch.setattr(rl, "_read_ledger_usd", lambda day: None)
    monkeypatch.setattr(rl, "_append_ledger", lambda *a, **k: None)


# ── free backends are never limited ──────────────────────────────


def test_local_backend_is_never_limited(no_ledger):
    """The limiter must not be the thing that breaks local development, the
    test suite, or an unconfigured deployment."""
    for _ in range(rl.SESSION_LIMIT + rl.HOURLY_LIMIT + 10):
        assert rl.consume(999, metered=False) == (True, None)


# ── per session: fairness, explicitly NOT a spend cap ────────────


def test_session_limit_refuses_after_its_quota(no_ledger):
    assert rl.consume(rl.SESSION_LIMIT - 1, metered=True)[0] is True
    allowed, msg = rl.consume(rl.SESSION_LIMIT, metered=True)
    assert allowed is False
    assert "session" in msg.lower()


def test_a_fresh_session_bypasses_the_session_limit(no_ledger):
    """Documents the hole deliberately: Gradio session state is per browser
    session, so anything loading the page fresh gets a fresh counter. This is
    why the daily ledger exists -- a session limit is not a spend cap, and a
    reader who assumes otherwise should find this test."""
    assert rl.consume(rl.SESSION_LIMIT, metered=True)[0] is False
    assert rl.consume(0, metered=True)[0] is True


# ── per hour: the burst brake ────────────────────────────────────


def test_hourly_brake_bounds_a_burst_across_sessions(no_ledger):
    allowed = sum(1 for _ in range(rl.HOURLY_LIMIT + 20)
                  if rl.consume(0, metered=True)[0])
    assert allowed == rl.HOURLY_LIMIT


def test_hourly_window_rolls_forward(no_ledger):
    for _ in range(rl.HOURLY_LIMIT):
        rl.consume(0, metered=True, now=1000.0)
    assert rl.consume(0, metered=True, now=1000.0)[0] is False
    assert rl.consume(0, metered=True, now=1000.0 + rl.WINDOW_SECONDS + 1)[0] is True


def test_a_refusal_does_not_consume_budget(no_ledger):
    """A refused call never reached the provider, so it must not eat a slot."""
    for _ in range(rl.HOURLY_LIMIT):
        rl.consume(0, metered=True)
    before = rl.snapshot()["hour_used"]
    rl.consume(0, metered=True)
    assert rl.snapshot()["hour_used"] == before


# ── per day, in dollars: the real cap ────────────────────────────


def test_daily_budget_refuses_when_the_ledger_is_over(monkeypatch):
    monkeypatch.setattr(rl, "_read_ledger_usd", lambda day: rl.DAILY_USD_LIMIT + 0.01)
    monkeypatch.setattr(rl, "_append_ledger", lambda *a, **k: None)
    allowed, msg = rl.consume(0, metered=True)
    assert allowed is False
    assert "daily" in msg.lower() or "budget" in msg.lower()


def test_daily_budget_survives_a_restart(monkeypatch):
    """The whole point of the ledger. A sleeping Space restarts constantly; an
    in-process counter would hand back the same budget on every wake."""
    monkeypatch.setattr(rl, "_append_ledger", lambda *a, **k: None)
    monkeypatch.setattr(rl, "_read_ledger_usd", lambda day: rl.DAILY_USD_LIMIT)
    assert rl.consume(0, metered=True)[0] is False

    rl.reset()   # simulate the container coming back up
    assert rl.consume(0, metered=True)[0] is False, "budget reset on restart"


def test_local_spend_counts_between_ledger_reads(monkeypatch):
    """Between refreshes the in-process delta still applies, so a burst inside
    one refresh window cannot overshoot the cap unnoticed."""
    monkeypatch.setattr(rl, "_read_ledger_usd", lambda day: 0.0)
    monkeypatch.setattr(rl, "_append_ledger", lambda *a, **k: None)
    assert rl.consume(0, metered=True)[0] is True
    rl.record(pack="vv40", input_tokens=0, output_tokens=0, usd=rl.DAILY_USD_LIMIT)
    assert rl.consume(0, metered=True)[0] is False


def test_unreadable_ledger_allows_but_leaves_the_brake(monkeypatch):
    """Failing closed would take the demo down for a transient HF outage;
    failing fully open would be the unbounded bill. So: allow, and rely on the
    hourly brake."""
    monkeypatch.setattr(rl, "_read_ledger_usd", lambda day: None)
    monkeypatch.setattr(rl, "_append_ledger", lambda *a, **k: None)
    assert rl.consume(0, metered=True)[0] is True
    assert rl.snapshot()["ledger_ever_read"] is False
    allowed = sum(1 for _ in range(rl.HOURLY_LIMIT + 5) if rl.consume(0, metered=True)[0])
    assert allowed == rl.HOURLY_LIMIT - 1


# ── accounting ───────────────────────────────────────────────────


def test_record_never_raises_on_a_ledger_failure(monkeypatch):
    """Accounting must not turn a successful analysis into a user-visible error."""
    def boom(*a, **k):
        raise RuntimeError("hub down")
    monkeypatch.setattr(rl, "_append_ledger", boom)
    monkeypatch.setattr(rl, "_read_ledger_usd", lambda day: 0.0)
    with pytest.raises(RuntimeError):
        boom()
    # record() swallows it via _append_ledger's own guard in production; here the
    # patched version raises, so assert the caller-side contract instead.
    try:
        rl.record(pack="vv40", input_tokens=10, output_tokens=10, usd=0.01)
    except RuntimeError:
        pytest.fail("record() propagated a ledger failure")


def test_estimate_is_zero_for_local_backends():
    assert rl.estimate_usd(10_000, 10_000, None) == 0.0


def test_estimate_is_positive_and_scales(monkeypatch):
    from uofa_cli.llm.config import LLMConfig

    cfg = LLMConfig(backend="openai-compatible", model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
                    base_url="https://api.together.xyz/v1", api_key_env="K")
    small = rl.estimate_usd(1_000, 500, cfg)
    large = rl.estimate_usd(20_000, 4_000, cfg)
    assert 0 < small < large


def test_filename_encodes_the_amount_so_totalling_needs_no_downloads():
    """A day's total is one list call. If the naming drifts, _read_ledger_usd
    silently sums nothing and the cap stops applying."""
    assert rl._NAME_RE.search("usage/2026-08-14/12-00-00-99-6200u.json").group(1) == "6200"
    assert rl._NAME_RE.search("usage/2026-08-14/x.json") is None
    assert rl._micros(0.0062) == 6200

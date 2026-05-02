"""Tests for the interpretation result cache (spec v0.4 §4.7, P-N).

Covers:
- Hit / miss semantics (round-trip a value, verify exact contents)
- Key-component sensitivity (changing prompt / backend / model / version → miss)
- Pipeline integration (second invocation skips backend call)
- `--explain-no-cache` bypass
- Schema-version invalidation
- Corruption recovery (bad row → miss + auto-cleanup)
"""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest

from uofa_cli.interpretation import (
    InterpretationOptions,
    interpret_rules_output,
)
from uofa_cli.interpretation.cache import (
    CACHE_SCHEMA_VERSION,
    ExplanationCache,
    compute_key,
    default_db_path,
)
from uofa_cli.llm import MockBackend


# ── compute_key ────────────────────────────────────────────


class TestComputeKey:
    def test_deterministic(self):
        a = compute_key(prompt="p", backend="ollama", model="qwen3.5:4b", interp_version="0.2.0")
        b = compute_key(prompt="p", backend="ollama", model="qwen3.5:4b", interp_version="0.2.0")
        assert a == b

    def test_changes_when_prompt_changes(self):
        a = compute_key(prompt="A", backend="ollama", model="qwen3.5:4b", interp_version="0.2.0")
        b = compute_key(prompt="B", backend="ollama", model="qwen3.5:4b", interp_version="0.2.0")
        assert a != b

    def test_changes_when_backend_changes(self):
        a = compute_key(prompt="p", backend="ollama", model="m", interp_version="v")
        b = compute_key(prompt="p", backend="anthropic", model="m", interp_version="v")
        assert a != b

    def test_changes_when_model_changes(self):
        a = compute_key(prompt="p", backend="b", model="m1", interp_version="v")
        b = compute_key(prompt="p", backend="b", model="m2", interp_version="v")
        assert a != b

    def test_changes_when_version_changes(self):
        a = compute_key(prompt="p", backend="b", model="m", interp_version="0.2.0")
        b = compute_key(prompt="p", backend="b", model="m", interp_version="0.3.0")
        assert a != b

    def test_no_collision_under_concatenation(self):
        """NUL separators in compute_key prevent the classic
        ('ab', 'cd') == ('a', 'bcd') collision."""
        a = compute_key(prompt="ab", backend="cd", model="m", interp_version="v")
        b = compute_key(prompt="a", backend="bcd", model="m", interp_version="v")
        assert a != b


# ── ExplanationCache KV behavior ───────────────────────────


class TestExplanationCacheKV:
    def test_miss_returns_none(self, tmp_path):
        with ExplanationCache(tmp_path / "c.db") as c:
            assert c.get("nonexistent") is None

    def test_round_trip(self, tmp_path):
        with ExplanationCache(tmp_path / "c.db") as c:
            c.put("k1", {"foo": "bar", "n": 42})
            assert c.get("k1") == {"foo": "bar", "n": 42}

    def test_overwrite(self, tmp_path):
        with ExplanationCache(tmp_path / "c.db") as c:
            c.put("k1", {"v": 1})
            c.put("k1", {"v": 2})
            assert c.get("k1") == {"v": 2}

    def test_clear(self, tmp_path):
        with ExplanationCache(tmp_path / "c.db") as c:
            c.put("k1", {"v": 1})
            c.put("k2", {"v": 2})
            assert c.clear() == 2
            assert c.get("k1") is None
            assert c.get("k2") is None

    def test_persistence_across_open_close(self, tmp_path):
        """Cache should survive close + reopen of the same DB file."""
        path = tmp_path / "c.db"
        with ExplanationCache(path) as c:
            c.put("k1", {"v": 1})
        with ExplanationCache(path) as c:
            assert c.get("k1") == {"v": 1}

    def test_unserializable_value_silently_skipped(self, tmp_path):
        """Caller bug — should never break the live call."""
        with ExplanationCache(tmp_path / "c.db") as c:
            c.put("k1", {"obj": object()})  # not JSON-serializable
            assert c.get("k1") is None  # nothing was stored

    def test_stats_reports_entry_count(self, tmp_path):
        with ExplanationCache(tmp_path / "c.db") as c:
            c.put("k1", {"v": 1})
            c.put("k2", {"v": 2})
            assert c.stats()["entries"] == 2


# ── Schema-version invalidation ────────────────────────────


class TestSchemaInvalidation:
    def test_old_schema_drops_entries(self, tmp_path, monkeypatch):
        """Bumping CACHE_SCHEMA_VERSION should clear stale entries on next open."""
        path = tmp_path / "c.db"
        # Write entries under the current schema
        with ExplanationCache(path) as c:
            c.put("k1", {"v": 1})

        # Simulate a future version bump (current code = newer schema)
        import uofa_cli.interpretation.cache as cache_mod
        monkeypatch.setattr(cache_mod, "CACHE_SCHEMA_VERSION", CACHE_SCHEMA_VERSION + 1)

        with ExplanationCache(path) as c:
            assert c.get("k1") is None
            assert c.stats()["entries"] == 0


# ── Corruption recovery ────────────────────────────────────


class TestCorruption:
    def test_corrupt_row_returns_miss_and_cleans_up(self, tmp_path):
        path = tmp_path / "c.db"
        with ExplanationCache(path) as c:
            # Insert raw garbage at the SQL level
            c._conn.execute(
                "INSERT INTO entries (key, value, created_at, accessed_at) VALUES (?, ?, ?, ?)",
                ("k1", "{not valid json", 0.0, 0.0),
            )
            c._conn.commit()
            # Lookup returns None and removes the bad row
            assert c.get("k1") is None
            assert c.stats()["entries"] == 0


# ── Pipeline integration ───────────────────────────────────


def _canned_explanation() -> str:
    """v0.4.0 three-field schema (no confidence)."""
    return json.dumps({
        "patternId": "MOCK", "severity": "High",
        "affected_evidence_summary": "From the LLM (evidence).",
        "gap_description": "From the LLM.",
        "relevance_to_cou": "From the LLM (relevance).",
    })


class TestPipelineIntegration:
    def test_second_call_hits_cache_no_backend_invocation(self):
        """Run the pipeline twice with identical input. Second run should
        produce the same explanations WITHOUT calling the backend."""
        firings = [{"patternId": "W-EP-04", "severity": "High", "hits": 1}]

        backend = MockBackend(default_response=_canned_explanation())

        # First invocation: backend should be called
        env1 = interpret_rules_output(
            structured_output={"firings": firings},
            package_doc={},
            firings=firings,
            options=InterpretationOptions(backend=backend, pack_name="vv40", functions=["explain"]),
        )
        n_calls_after_first = len(backend.calls)
        assert n_calls_after_first == 1
        assert env1.interpretation.explanations[0]["gap_description"] == "From the LLM."

        # Second invocation: cache hit, no new backend calls
        env2 = interpret_rules_output(
            structured_output={"firings": firings},
            package_doc={},
            firings=firings,
            options=InterpretationOptions(backend=backend, pack_name="vv40", functions=["explain"]),
        )
        assert len(backend.calls) == n_calls_after_first  # no new calls
        # Same content
        assert env2.interpretation.explanations[0]["gap_description"] == "From the LLM."

    def test_no_cache_flag_bypasses(self):
        """`options.no_cache=True` should always invoke the backend."""
        firings = [{"patternId": "W-EP-04", "severity": "High", "hits": 1}]
        backend = MockBackend(default_response=_canned_explanation())

        for _ in range(3):
            interpret_rules_output(
                structured_output={"firings": firings},
                package_doc={},
                firings=firings,
                options=InterpretationOptions(
                    backend=backend, pack_name="vv40", no_cache=True,
                    functions=["explain"],
                ),
            )
        # Three runs → three backend calls (no caching)
        assert len(backend.calls) == 3

    def test_backend_change_misses_cache(self):
        """Spec §4.7: switching backends produces different cached results."""
        firings = [{"patternId": "W-EP-04", "severity": "High", "hits": 1}]
        b1 = MockBackend(default_response=_canned_explanation(), backend_name="ollama", model_name="qwen3.5:4b")
        b2 = MockBackend(default_response=_canned_explanation(), backend_name="anthropic", model_name="claude-sonnet-5-2026")

        # Warm cache with backend 1
        interpret_rules_output(
            structured_output={"firings": firings}, package_doc={},
            firings=firings,
            options=InterpretationOptions(backend=b1, pack_name="vv40", functions=["explain"]),
        )
        n_b1 = len(b1.calls)
        assert n_b1 == 1

        # Switch to backend 2 — should miss cache, call b2
        interpret_rules_output(
            structured_output={"firings": firings}, package_doc={},
            firings=firings,
            options=InterpretationOptions(backend=b2, pack_name="vv40", functions=["explain"]),
        )
        assert len(b2.calls) == 1  # b2 was called (cache miss)
        assert len(b1.calls) == n_b1  # b1 not called again

    def test_different_firing_misses_cache(self):
        """Different firings → different prompts → cache miss."""
        backend = MockBackend(default_response=_canned_explanation())

        for pid in ("W-A", "W-B", "W-C"):
            interpret_rules_output(
                structured_output={"firings": [{"patternId": pid}]}, package_doc={},
                firings=[{"patternId": pid, "severity": "High", "hits": 1}],
                options=InterpretationOptions(backend=backend, pack_name="vv40", functions=["explain"]),
            )
        assert len(backend.calls) == 3

    def test_cache_failure_does_not_break_interpretation(self, monkeypatch):
        """If sqlite is unwritable (read-only fs, etc.), interpretation
        should still succeed using the live backend path."""
        firings = [{"patternId": "W-EP-04", "severity": "High", "hits": 1}]
        backend = MockBackend(default_response=_canned_explanation())

        # Force ExplanationCache.open to fail
        def boom(self):
            raise OSError("read-only filesystem")
        monkeypatch.setattr(ExplanationCache, "open", boom)

        env = interpret_rules_output(
            structured_output={"firings": firings}, package_doc={},
            firings=firings,
            options=InterpretationOptions(backend=backend, pack_name="vv40", functions=["explain"]),
        )
        assert len(env.interpretation.explanations) == 1
        assert len(backend.calls) == 1


# ── default_db_path ────────────────────────────────────────


class TestDefaultDbPath:
    def test_default_path_under_uofa_data_dir(self, monkeypatch, tmp_path):
        """default_db_path() lives under the uofa data dir per setup_state."""
        monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
        # Re-import to bypass the conftest autouse override
        import importlib
        import uofa_cli.interpretation.cache as cache_mod
        importlib.reload(cache_mod)
        path = cache_mod.default_db_path()
        assert path == tmp_path / "uofa" / "cache" / "explain.db"

"""SQLite-backed cache for interpretation function results (spec v0.4 §4.7).

Per-firing LLM calls are the dominant cost of the `--explain` pipeline (one
HTTP call per firing × ~10s on bundled Qwen × dozens of firings on a
real package). Caching the (deterministic) inputs → outputs makes repeat
invocations near-free; spec target is <100ms cache hit.

Cache key (hashed to a fixed-length hex digest):
    sha256(prompt + "\\0" + backend + "\\0" + model + "\\0" + interp_version)

The prompt already encodes the structured-output payload (the template
substitutes firing fields into it), so we don't need a separate hash of
the structured output. `backend` and `model` separate cached results
across providers (spec §4.7: "switching from Ollama to Anthropic produces
different cached results"). `interp_version` invalidates everything when
the envelope schema changes.

What's deliberately NOT in the key:
- API keys (spec §6.4 Rule 2 — never in cache)
- Timestamps (would force every run to miss)
- The raw structured_output (it's already inside the prompt; double-counting
  would make the key brittle)

Storage: simple SQLite table at `~/.uofa/cache/explain.db`. One row per
(key) → (value JSON, created_at, accessed_at). No expiry policy yet — the
key includes interp_version, so a release bump invalidates everything
implicitly.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path

# Bumped together with envelope.INTERPRETATION_VERSION when output shape
# changes. Independent constant here so we can invalidate the cache
# without changing the envelope's user-facing version field.
CACHE_SCHEMA_VERSION = 1


def default_db_path() -> Path:
    """Return `<XDG cache>/uofa/explain.db` (or `~/.uofa/cache/explain.db`)."""
    from uofa_cli import setup_state
    return setup_state.uofa_data_dir() / "cache" / "explain.db"


def compute_key(
    *,
    prompt: str,
    backend: str,
    model: str,
    interp_version: str,
) -> str:
    """Stable hex digest for the (prompt, backend, model, version) tuple.

    NUL byte separators prevent collisions of the form
    `("ab", "cd") == ("a", "bcd")`. SHA-256 truncated to 16 hex chars
    (64-bit prefix) — plenty of collision resistance for a single user's
    cache, and short enough to fit in tight SQLite indexes.
    """
    h = hashlib.sha256()
    for part in (prompt, backend, model, interp_version):
        h.update(part.encode("utf-8"))
        h.update(b"\x00")
    return h.hexdigest()[:32]


class ExplanationCache:
    """Lightweight SQLite KV store for interpretation results.

    Used as a context manager so the connection is closed cleanly:

        with ExplanationCache() as cache:
            cached = cache.get(key)
            if cached is None:
                cached = expensive_call(...)
                cache.put(key, cached)
    """

    def __init__(self, db_path: Path | None = None):
        self.db_path = db_path or default_db_path()
        self._conn: sqlite3.Connection | None = None

    # ── Lifecycle ────────────────────────────────────────────

    def open(self) -> "ExplanationCache":
        if self._conn is not None:
            return self
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.row_factory = sqlite3.Row
        self._init_schema()
        return self

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def __enter__(self) -> "ExplanationCache":
        return self.open()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    # ── Public KV API ────────────────────────────────────────

    def get(self, key: str) -> dict | None:
        """Return the cached value for `key`, or None on miss.

        Updates the row's `accessed_at` so consumers can prune by LRU later
        if needed. Returns None on any deserialization error rather than
        raising — a corrupt cache entry should never break the live call.
        """
        conn = self._require_open()
        row = conn.execute(
            "SELECT value FROM entries WHERE key = ?", (key,),
        ).fetchone()
        if row is None:
            return None
        try:
            value = json.loads(row["value"])
        except (json.JSONDecodeError, TypeError):
            # Corrupt entry — drop it and signal miss.
            conn.execute("DELETE FROM entries WHERE key = ?", (key,))
            conn.commit()
            return None
        conn.execute(
            "UPDATE entries SET accessed_at = ? WHERE key = ?",
            (time.time(), key),
        )
        conn.commit()
        return value

    def put(self, key: str, value: dict) -> None:
        conn = self._require_open()
        now = time.time()
        try:
            payload = json.dumps(value)
        except (TypeError, ValueError):
            # Caller's responsibility — values must be JSON-serializable.
            # We skip rather than raise so caching failures don't break
            # the live call path.
            return
        conn.execute(
            "INSERT OR REPLACE INTO entries (key, value, created_at, accessed_at) "
            "VALUES (?, ?, ?, ?)",
            (key, payload, now, now),
        )
        conn.commit()

    def clear(self) -> int:
        """Drop all entries; returns the number deleted."""
        conn = self._require_open()
        cur = conn.execute("DELETE FROM entries")
        conn.commit()
        return cur.rowcount

    def stats(self) -> dict:
        conn = self._require_open()
        row = conn.execute(
            "SELECT COUNT(*) AS n, MIN(created_at) AS oldest, MAX(accessed_at) AS newest FROM entries"
        ).fetchone()
        return {
            "entries": row["n"] or 0,
            "oldest_seconds": (time.time() - row["oldest"]) if row["oldest"] else None,
            "newest_seconds": (time.time() - row["newest"]) if row["newest"] else None,
            "db_path": str(self.db_path),
            "db_size_bytes": self.db_path.stat().st_size if self.db_path.exists() else 0,
        }

    # ── Internals ────────────────────────────────────────────

    def _require_open(self) -> sqlite3.Connection:
        if self._conn is None:
            self.open()
        assert self._conn is not None
        return self._conn

    def _init_schema(self) -> None:
        conn = self._conn
        assert conn is not None
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY
            );
            CREATE TABLE IF NOT EXISTS entries (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                created_at REAL NOT NULL,
                accessed_at REAL NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_entries_accessed ON entries (accessed_at);
            """
        )
        # Detect schema-version mismatch and rebuild if needed.
        row = conn.execute("SELECT version FROM schema_version").fetchone()
        current = row["version"] if row else None
        if current != CACHE_SCHEMA_VERSION:
            conn.execute("DELETE FROM entries")
            conn.execute("DELETE FROM schema_version")
            conn.execute("INSERT INTO schema_version (version) VALUES (?)", (CACHE_SCHEMA_VERSION,))
        conn.commit()


@contextmanager
def open_default_cache():
    """Convenience: `with open_default_cache() as c: ...` for the default
    db path. Functions wanting a custom path instantiate ExplanationCache
    directly."""
    cache = ExplanationCache()
    try:
        cache.open()
        yield cache
    finally:
        cache.close()

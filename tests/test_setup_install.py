"""Tests for setup_install — manifest, download, SHA verify (PR 4).

Daemon lifecycle and full pull/prewarm flow are exercised in CI integration
tests (opt-in via -m setup_integration); the unit tests here cover the
deterministic helpers + the SHA-256 + resume logic.
"""

from __future__ import annotations

import hashlib
import io
from pathlib import Path

import pytest

from uofa_cli import setup_install


# ── Manifest resolution ────────────────────────────────────────


def test_resolve_platform_entry_round_trips(tmp_path):
    manifest = {
        "platforms": {
            "macosx_11_0_arm64": {
                "version": "v0.21.2",
                "url": "https://example.com/ollama-darwin.tgz",
                "sha256": "abc123",
                "archive_format": "tgz",
                "binary_inside_archive": "Ollama.app/Contents/Resources/ollama",
            }
        }
    }
    entry = setup_install.resolve_platform_entry("macosx_11_0_arm64", manifest)
    assert entry.url.endswith("ollama-darwin.tgz")
    assert entry.sha256 == "abc123"
    assert entry.archive_format == "tgz"
    assert entry.binary_inside_archive == "Ollama.app/Contents/Resources/ollama"


def test_resolve_platform_entry_unknown_raises():
    with pytest.raises(KeyError, match="not in ollama_manifest"):
        setup_install.resolve_platform_entry("solaris_sparc64", {"platforms": {}})


# ── SHA-256 verification ───────────────────────────────────────


def test_verify_sha256_passes_on_match(tmp_path):
    payload = b"hello world\n"
    expected = hashlib.sha256(payload).hexdigest()
    f = tmp_path / "blob"
    f.write_bytes(payload)
    setup_install._verify_sha256(f, expected)  # no exception


def test_verify_sha256_raises_on_mismatch(tmp_path):
    f = tmp_path / "blob"
    f.write_bytes(b"hello world\n")
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        setup_install._verify_sha256(f, "0" * 64)


# ── Download with resume + progress (mocked HTTP) ──────────────


class _FakeResponse:
    def __init__(self, body: bytes, status: int = 200, headers=None):
        self._body = body
        self.status_code = status
        self.headers = headers or {}

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def iter_content(self, chunk_size: int):
        view = memoryview(self._body)
        for i in range(0, len(view), chunk_size):
            yield bytes(view[i : i + chunk_size])


def test_download_ollama_resumes_partial(monkeypatch, tmp_path):
    payload = b"A" * 10_000 + b"B" * 5_000
    expected_sha = hashlib.sha256(payload).hexdigest()
    dest = tmp_path / "ollama-darwin.tgz"
    # Pre-write the first 10_000 bytes as if a previous attempt was interrupted.
    dest.write_bytes(payload[:10_000])

    seen_headers: dict = {}

    def fake_head(url, allow_redirects=True, timeout=30):
        return _FakeResponse(b"", status=200, headers={
            "Content-Length": str(len(payload)),
            "Accept-Ranges": "bytes",
        })

    def fake_get(url, headers=None, stream=True, timeout=120):
        seen_headers.update(headers or {})
        # Server should serve from byte 10_000 onward.
        return _FakeResponse(payload[10_000:], status=206)

    fake_requests = type("FakeRequests", (), {"head": staticmethod(fake_head), "get": staticmethod(fake_get)})()
    monkeypatch.setitem(__import__("sys").modules, "requests", fake_requests)

    entry = setup_install.OllamaPlatformEntry(
        version="v0", url="http://example/ollama", sha256=expected_sha,
        archive_format="binary", binary_inside_archive="ollama",
    )
    progress_calls: list[tuple[int, int]] = []
    setup_install.download_ollama(
        entry, dest,
        on_progress=lambda done, total: progress_calls.append((done, total)),
    )

    assert dest.read_bytes() == payload
    assert seen_headers.get("Range") == "bytes=10000-"
    assert progress_calls  # at least one progress callback fired
    # Final callback reflects the full payload.
    assert progress_calls[-1] == (len(payload), len(payload))


def test_download_ollama_skips_when_already_complete(monkeypatch, tmp_path):
    payload = b"already-downloaded"
    expected_sha = hashlib.sha256(payload).hexdigest()
    dest = tmp_path / "ollama"
    dest.write_bytes(payload)

    def fake_head(url, allow_redirects=True, timeout=30):
        return _FakeResponse(b"", status=200, headers={"Content-Length": str(len(payload))})

    def fake_get(*a, **kw):
        raise AssertionError("get should not be called when file is already complete")

    fake_requests = type("FakeRequests", (), {"head": staticmethod(fake_head), "get": staticmethod(fake_get)})()
    monkeypatch.setitem(__import__("sys").modules, "requests", fake_requests)

    entry = setup_install.OllamaPlatformEntry(
        version="v0", url="http://example/ollama", sha256=expected_sha,
        archive_format="binary", binary_inside_archive="ollama",
    )
    setup_install.download_ollama(entry, dest)
    assert dest.read_bytes() == payload


def test_download_ollama_raises_on_sha_mismatch(monkeypatch, tmp_path):
    payload = b"corrupted"
    dest = tmp_path / "ollama"

    def fake_head(url, allow_redirects=True, timeout=30):
        return _FakeResponse(b"", status=200, headers={"Content-Length": str(len(payload))})

    def fake_get(url, headers=None, stream=True, timeout=120):
        return _FakeResponse(payload, status=200)

    fake_requests = type("FakeRequests", (), {"head": staticmethod(fake_head), "get": staticmethod(fake_get)})()
    monkeypatch.setitem(__import__("sys").modules, "requests", fake_requests)

    entry = setup_install.OllamaPlatformEntry(
        version="v0", url="http://example/ollama", sha256="0" * 64,
        archive_format="binary", binary_inside_archive="ollama",
    )
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        setup_install.download_ollama(entry, dest)


# ── install_binary (raw + tgz + zip) ───────────────────────────


def test_install_binary_handles_raw(tmp_path):
    src = tmp_path / "src" / "ollama"
    src.parent.mkdir()
    src.write_text("#!/bin/sh\necho stub\n")

    entry = setup_install.OllamaPlatformEntry(
        version="v0", url="x", sha256="x", archive_format="binary",
        binary_inside_archive="ollama",
    )
    target = setup_install.install_binary(entry, src, tmp_path / "install")
    assert target.is_file()
    assert target.name == "ollama"
    assert target.stat().st_mode & 0o111  # executable bit set


def test_install_binary_handles_zip(tmp_path):
    import zipfile
    src = tmp_path / "ollama.zip"
    with zipfile.ZipFile(src, "w") as zf:
        zf.writestr("ollama.exe", "MZ\x90stub")

    entry = setup_install.OllamaPlatformEntry(
        version="v0", url="x", sha256="x", archive_format="zip",
        binary_inside_archive="ollama.exe",
    )
    target = setup_install.install_binary(entry, src, tmp_path / "install")
    assert target.is_file()
    assert target.name == "ollama.exe"

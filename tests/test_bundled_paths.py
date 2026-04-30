"""Tests for bundled-asset path resolution (PR 1: bundled JAR).

Covers paths.bundled_jar() and the bundled-first behavior of paths.jar_path().
Monkeypatches _package_dir() so tests don't depend on the real wheel-build
state of src/uofa_cli/_engine/.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from uofa_cli import paths


def _fake_package_layout(tmp_path: Path, with_jar: bool) -> Path:
    pkg = tmp_path / "uofa_cli"
    engine = pkg / "_engine"
    engine.mkdir(parents=True)
    if with_jar:
        (engine / "uofa-weakener-engine-0.1.0.jar").write_bytes(b"PK\x03\x04stub")
    return pkg


def test_bundled_jar_returns_none_when_absent(tmp_path, monkeypatch):
    fake_pkg = _fake_package_layout(tmp_path, with_jar=False)
    monkeypatch.setattr(paths, "_package_dir", lambda: fake_pkg)
    assert paths.bundled_jar() is None


def test_bundled_jar_returns_path_when_present(tmp_path, monkeypatch):
    fake_pkg = _fake_package_layout(tmp_path, with_jar=True)
    monkeypatch.setattr(paths, "_package_dir", lambda: fake_pkg)
    result = paths.bundled_jar()
    assert result is not None
    assert result == fake_pkg / "_engine" / "uofa-weakener-engine-0.1.0.jar"
    assert result.exists()


def test_jar_path_prefers_bundled(tmp_path, monkeypatch):
    fake_pkg = _fake_package_layout(tmp_path, with_jar=True)
    monkeypatch.setattr(paths, "_package_dir", lambda: fake_pkg)
    # find_repo_root() must not be consulted; passing a deliberately invalid
    # root would only be reached on the source-tree fallback path.
    expected = fake_pkg / "_engine" / "uofa-weakener-engine-0.1.0.jar"
    assert paths.jar_path(root=tmp_path / "no-such-root") == expected


def test_jar_path_falls_back_to_source_tree(tmp_path, monkeypatch):
    fake_pkg = _fake_package_layout(tmp_path, with_jar=False)
    monkeypatch.setattr(paths, "_package_dir", lambda: fake_pkg)
    fake_root = tmp_path / "fake-repo"
    fake_root.mkdir()
    expected = fake_root / "src" / "weakener-engine" / "target" / "uofa-weakener-engine-0.1.0.jar"
    assert paths.jar_path(root=fake_root) == expected

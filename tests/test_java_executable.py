"""Tests for bundled-JRE path resolution (PR 2).

Covers paths.bundled_jre_executable() and the bundled-first behavior of
paths.java_executable(). Monkeypatches _package_dir() and shutil.which so
tests don't depend on the real wheel-build state of src/uofa_cli/_runtime/.
"""

from __future__ import annotations

import os
import stat
from pathlib import Path

import pytest

from uofa_cli import paths


def _fake_package_with_jre(tmp_path: Path, *, executable: bool = True) -> Path:
    pkg = tmp_path / "uofa_cli"
    bin_dir = pkg / "_runtime" / "jre" / "bin"
    bin_dir.mkdir(parents=True)
    java_name = "java.exe" if os.name == "nt" else "java"
    java = bin_dir / java_name
    java.write_text("#!/bin/sh\nexit 0\n")
    if executable:
        java.chmod(java.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return pkg


def _fake_package_without_jre(tmp_path: Path) -> Path:
    pkg = tmp_path / "uofa_cli"
    (pkg / "_runtime").mkdir(parents=True)
    return pkg


def test_bundled_jre_executable_returns_none_when_runtime_missing(tmp_path, monkeypatch):
    pkg = tmp_path / "uofa_cli"
    pkg.mkdir()
    # No _runtime/ directory at all.
    monkeypatch.setattr(paths, "_package_dir", lambda: pkg)
    assert paths.bundled_jre_executable() is None


def test_bundled_jre_executable_returns_none_when_jre_dir_missing(tmp_path, monkeypatch):
    pkg = _fake_package_without_jre(tmp_path)
    monkeypatch.setattr(paths, "_package_dir", lambda: pkg)
    assert paths.bundled_jre_executable() is None


def test_bundled_jre_executable_returns_path_when_present(tmp_path, monkeypatch):
    pkg = _fake_package_with_jre(tmp_path)
    monkeypatch.setattr(paths, "_package_dir", lambda: pkg)
    java_name = "java.exe" if os.name == "nt" else "java"
    expected = pkg / "_runtime" / "jre" / "bin" / java_name
    assert paths.bundled_jre_executable() == expected


def test_java_executable_prefers_bundled_over_system(tmp_path, monkeypatch):
    pkg = _fake_package_with_jre(tmp_path)
    monkeypatch.setattr(paths, "_package_dir", lambda: pkg)
    # System java is on PATH but should not be selected.
    monkeypatch.setattr(paths.shutil, "which", lambda name: "/usr/bin/java" if name == "java" else None)
    java_name = "java.exe" if os.name == "nt" else "java"
    expected = pkg / "_runtime" / "jre" / "bin" / java_name
    assert paths.java_executable() == str(expected)


def test_java_executable_falls_back_to_path(tmp_path, monkeypatch):
    pkg = _fake_package_without_jre(tmp_path)
    monkeypatch.setattr(paths, "_package_dir", lambda: pkg)
    monkeypatch.setattr(paths.shutil, "which", lambda name: "/usr/bin/java" if name == "java" else None)
    assert paths.java_executable() == "/usr/bin/java"


def test_java_executable_raises_when_no_java_anywhere(tmp_path, monkeypatch):
    pkg = _fake_package_without_jre(tmp_path)
    monkeypatch.setattr(paths, "_package_dir", lambda: pkg)
    monkeypatch.setattr(paths.shutil, "which", lambda name: None)
    with pytest.raises(FileNotFoundError, match="Java not found"):
        paths.java_executable()

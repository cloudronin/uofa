"""Shared fixtures for tests/adversarial/judge/.

Mirrors the style of `tests/adversarial/conftest.py` (path-based fixtures
loaded from a sibling `fixtures/` directory) so tests across the
adversarial subtree feel consistent.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from .fixtures.mock_bundle import write_mock_bundle

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def mock_bundle_path(tmp_path: Path) -> Path:
    """Generate a fresh 5-case mock bundle in `tmp_path` and return its path."""
    return write_mock_bundle(tmp_path / "mock_bundle.tgz")

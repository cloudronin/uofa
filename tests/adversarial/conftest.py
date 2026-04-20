"""Shared fixtures for adversarial tests."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("yaml", reason="PyYAML is required for adversarial specs; install .[llm]")


FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES


@pytest.fixture
def valid_spec_path() -> Path:
    return FIXTURES / "spec_w_ar_05_valid.yaml"


@pytest.fixture
def bad_weakener_spec_path() -> Path:
    return FIXTURES / "spec_w_ar_05_bad_weakener.yaml"


@pytest.fixture
def bad_mode_spec_path() -> Path:
    return FIXTURES / "spec_w_ar_05_bad_mode.yaml"


@pytest.fixture
def bad_factor_spec_path() -> Path:
    return FIXTURES / "spec_w_ar_05_bad_factor.yaml"

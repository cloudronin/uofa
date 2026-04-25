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


# Phase 2 source-taxonomy fixtures (spec §6.1, §5.2)


@pytest.fixture
def gap_probe_valid_spec_path() -> Path:
    return FIXTURES / "spec_gap_probe_valid.yaml"


@pytest.fixture
def gap_probe_missing_taxonomy_spec_path() -> Path:
    return FIXTURES / "spec_gap_probe_missing_taxonomy.yaml"


@pytest.fixture
def gap_probe_unresolved_taxonomy_spec_path() -> Path:
    return FIXTURES / "spec_gap_probe_unresolved_taxonomy.yaml"


@pytest.fixture
def negative_control_valid_spec_path() -> Path:
    return FIXTURES / "spec_negative_control_valid.yaml"


@pytest.fixture
def negative_control_bad_taxonomy_spec_path() -> Path:
    return FIXTURES / "spec_negative_control_bad_taxonomy.yaml"


@pytest.fixture
def confirm_existing_explicit_taxonomy_spec_path() -> Path:
    return FIXTURES / "spec_confirm_existing_explicit_taxonomy.yaml"

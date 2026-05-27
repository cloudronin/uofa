"""Fixtures for the OOS substrate validation test.

Post-T4: the substrate test runs against the unified fat JAR via the
``substrate-test`` subcommand (see net.uofa.Engine for dispatch). The
classifier-attached substrate-test JAR was retired in T4.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
ENGINE_JAR = (
    REPO_ROOT
    / "src"
    / "weakener-engine"
    / "target"
    / "uofa-weakener-engine-0.1.0.jar"
)


@pytest.fixture(scope="session")
def java_executable() -> str:
    """Resolve a usable `java` binary; fail the test cleanly if missing."""
    on_path = shutil.which("java")
    if not on_path:
        pytest.skip("java not found on PATH")
    return on_path


@pytest.fixture(scope="session")
def substrate_jar() -> Path:
    """Path to the unified engine fat JAR; require a fresh `mvn package` build.

    Substrate test invokes via the ``substrate-test`` subcommand on this JAR.
    """
    if not ENGINE_JAR.exists():
        pytest.skip(
            f"Engine JAR not built at {ENGINE_JAR}. "
            "Run: cd src/weakener-engine && mvn package -DskipTests"
        )
    return ENGINE_JAR


@pytest.fixture(scope="session")
def substrate_paths() -> dict:
    """Standard input file paths for the substrate test."""
    return {
        "cal_021_path": REPO_ROOT
        / "specs/calibration/packages/cal-021-out_of_scope-stub.jsonld",
        "c3_rules_path": REPO_ROOT / "packs/core/rules/uofa_weakener.rules",
        "oos_rule_path": REPO_ROOT / "packs/vv40/rules/oos_backward_v0.1.rules",
        "vocab_path": REPO_ROOT / "uofa/vocab/v0.5/oos_substrate_test.ttl",
        "context_path": REPO_ROOT / "spec/context/v0.5.jsonld",
    }


@pytest.fixture
def substrate_report_path(tmp_path: Path) -> Path:
    """Per-test report destination for the substrate test JAR.

    Writes go to pytest's ``tmp_path`` instead of an in-repo location so the
    committed snapshot at ``tests/substrate/oos_backward_substrate_test_report.json``
    — referenced by ``docs/decisions/2026-05-05-oos-substrate.md`` as a
    decision-relevant artifact — isn't mutated by test runs.
    """
    return tmp_path / "oos_backward_substrate_test_report.json"

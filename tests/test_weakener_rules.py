"""Table-driven unit tests for v0.5 weakener rules.

Each rule has positive/negative (mandatory) and optionally boundary fixtures
under tests/fixtures/weakeners/{pattern_id}/. The test runs `uofa rules` on
each fixture and asserts whether the pattern ID appears in the output.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent
FIXTURES = REPO_ROOT / "tests" / "fixtures" / "weakeners"

JAVA_AVAILABLE = shutil.which("java") is not None
JENA_JAR = REPO_ROOT / "weakener-engine" / "target" / "uofa-weakener-engine-0.1.0.jar"
JENA_AVAILABLE = JAVA_AVAILABLE and JENA_JAR.exists()


CASES: list[tuple[str, str, bool]] = [
    # (pattern_id, variant, should_fire)
    ("W-ON-02", "positive", True),
    ("W-ON-02", "negative", False),

    ("W-AR-03", "positive", True),
    ("W-AR-03", "negative", False),
    ("W-AR-03", "boundary", False),

    ("W-AL-02", "positive", True),
    ("W-AL-02", "negative", False),
    ("W-AL-02", "boundary", True),   # SA class exists but no property link → still fires

    ("W-EP-03", "positive", True),
    ("W-EP-03", "negative", False),
    ("W-EP-03", "boundary", False),  # equal timestamps → lessThan false

    ("W-AR-04", "positive", True),
    ("W-AR-04", "negative", False),

    ("W-CON-03", "positive", True),
    ("W-CON-03", "negative", False),
    ("W-CON-03", "boundary", False),

    ("W-CON-05", "positive", True),
    ("W-CON-05", "negative", False),

    ("W-PROV-01", "positive", True),
    ("W-PROV-01", "negative", False),

    ("W-CON-01", "positive", True),
    ("W-CON-01", "negative", False),
    ("W-CON-01", "boundary", False),

    ("W-CON-02", "positive", True),
    ("W-CON-02", "negative", False),

    ("W-CON-04", "positive", True),
    ("W-CON-04", "negative", False),
]


def _run_uofa_rules(fixture: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["python", "-m", "uofa_cli", "rules", str(fixture)],
        capture_output=True, text=True,
        cwd=str(REPO_ROOT),
    )


@pytest.mark.skipif(not JENA_AVAILABLE, reason="Jena rules require Java")
@pytest.mark.parametrize("pattern_id,variant,should_fire", CASES)
def test_rule_fires_as_expected(pattern_id: str, variant: str, should_fire: bool):
    fixture = FIXTURES / pattern_id / f"{variant}.jsonld"
    assert fixture.exists(), f"missing fixture: {fixture}"

    result = _run_uofa_rules(fixture)
    assert result.returncode == 0, f"uofa rules failed:\n{result.stderr}"

    in_output = pattern_id in result.stdout
    if should_fire:
        assert in_output, (
            f"{pattern_id} should fire on {variant} fixture but did not.\n"
            f"stdout:\n{result.stdout}"
        )
    else:
        assert not in_output, (
            f"{pattern_id} should NOT fire on {variant} fixture but did.\n"
            f"stdout:\n{result.stdout}"
        )

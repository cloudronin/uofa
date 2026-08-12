"""Table-driven fixture tests for the pack's Group-B weakener rules.

Mirrors `tests/test_weakener_rules.py` and `tests/test_iso42001_weakener_fixtures.py`,
with `active_packs=["model-credibility"]` so the W-EV-* rules are loaded at all.

The boundary row is the reason this file exists. `W-EV-COU-05` splits severity on
whether the operator supplied `--cou`, and an earlier draft of the rule
discriminated *only* on that flag. That version would fire a Critical against a
model whose card properly states its context of use -- reporting on the
operator's input instead of on the evidence. The finding is
`noValue(?vr, uofa:claimedCOU)`; the flag only picks the severity. The boundary
fixture pins the case that distinguishes the two readings.
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

import pytest

from uofa_cli import paths

REPO_ROOT = Path(__file__).parent.parent
FIXTURES = REPO_ROOT / "tests" / "fixtures" / "weakeners"

JENA_AVAILABLE = shutil.which("java") is not None and paths.jar_path().exists()
_needs_engine = pytest.mark.skipif(not JENA_AVAILABLE, reason="weakener engine JAR not built")

CASES: list[tuple[str, str, bool]] = [
    # (pattern_id, variant, should_fire)
    ("W-EV-COU-05", "positive", True),    # record states no context of use
    ("W-EV-COU-05", "negative", False),   # record states its context of use
    # Record states its COU AND --cou was supplied. MUST stay silent: the
    # severity split rides on top of the absence condition, never instead of it.
    ("W-EV-COU-05", "boundary", False),
]


def _firings(fixture_path: Path) -> set[str]:
    from uofa_cli.commands.check import run_structured as check_run_structured

    args = argparse.Namespace(
        file=fixture_path, pubkey=None, context=None, rules=None, skip_rules=False,
        build=False, raw=False, format="jsonld", output=None, strict=False,
        no_color=True, verbose=False, repo_root=None, explain=None,
        active_packs=["model-credibility"],
    )
    result = check_run_structured(args)
    return {r.get("patternId") for r in (result.rules.firings or []) if r.get("patternId")}


@_needs_engine
@pytest.mark.parametrize("pattern_id,variant,should_fire", CASES,
                         ids=[f"{p}-{v}" for p, v, _ in CASES])
def test_group_b_rule_fixture(pattern_id, variant, should_fire):
    fixture = FIXTURES / pattern_id / f"{variant}.jsonld"
    assert fixture.exists(), f"missing fixture {fixture}"
    fired = _firings(fixture)
    if should_fire:
        assert pattern_id in fired, f"{pattern_id} should fire on {variant} but did not"
    else:
        assert pattern_id not in fired, (
            f"{pattern_id} fired on {variant}, which must stay silent. For the boundary "
            "case this means the rule is keyed on the operator's --cou flag rather than "
            "on the record's missing claimedCOU."
        )

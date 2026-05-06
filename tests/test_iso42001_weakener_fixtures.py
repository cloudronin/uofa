"""Direct-test coverage for iso42001 W-AIMS C3 weakener patterns (v0.4.1).

For each pattern with positive/negative/boundary fixtures, asserts:
  - positive.jsonld triggers the pattern
  - negative.jsonld does not trigger
  - boundary.jsonld matches its documented design decision

Mirrors the convention established by core patterns under
tests/fixtures/weakeners/W-AR-03/ etc., extended to the iso42001 pack.

This suite covers the two W-AIMS patterns NOT slated for v0.5 pre-pass
migration:
  - W-AR-02 (translated from core; works cleanly in pure Jena rules)
  - W-AIMS-OBJECTIVE-UNMEASURED (presence check; no derived flag needed)

The other four engine-only-verified W-AIMS patterns
  (W-AIMS-AUDIT-STALE, W-AIMS-DATA-DRIFT-UNDETECTED,
   W-AIMS-CROSSWALK-INVALID, plus W-AIMS-MODEL-EVAL-* family)
get fixtures as part of the v0.5 brittleness oracle suite per
UofA_Derivation_PrePass_Spec_v0_1.md §5.1, since they migrate to
derived-flag form.
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

import pytest

from uofa_cli import paths
from uofa_cli.commands import rules as rules_mod


REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = REPO_ROOT / "tests/fixtures/weakeners"
JAR = REPO_ROOT / "src/weakener-engine/target/uofa-weakener-engine-0.1.0.jar"
JAVA_AVAILABLE = shutil.which("java") is not None

needs_jar = pytest.mark.skipif(
    not (JAVA_AVAILABLE and JAR.exists()),
    reason="java + built JAR required",
)


@pytest.fixture(autouse=True)
def _activate_iso42001_pack():
    """Activate iso42001 pack for all tests; restore prior pack after."""
    prior = paths.get_active_pack()
    paths.set_active_pack(["iso42001"])
    yield
    paths.set_active_pack(prior or ["vv40"])


def _firings(fixture_path: Path) -> set[str]:
    """Run the FULL check pipeline (with default-on derivations for iso42001)
    and return the set of patternIds that fired in C3.

    v0.5 update: switched from rules.run_structured (which doesn't run
    derivations) to check.run_structured (which runs the C2.5 pre-pass
    before C3). Required for the v0.4.1 fixtures whose targeted W-AIMS
    patterns now consume derived flags materialized by the pre-pass."""
    from uofa_cli.commands.check import run_structured as check_run_structured
    args = argparse.Namespace(
        file=fixture_path,
        pubkey=None,
        context=None,
        rules=None,
        skip_rules=False,
        build=False,
        enable_oos=False,
        disable_oos=True,
        enable_derivations=False,
        disable_derivations=False,
        no_color=True,
        verbose=False,
        repo_root=None,
        pack=["iso42001"],
    )
    result = check_run_structured(args)
    return {r.get("patternId") for r in (result.rules.firings or []) if r.get("patternId")}


PATTERNS = [
    "W-AR-02",
    "W-AIMS-OBJECTIVE-UNMEASURED",
]


@needs_jar
class TestW_AIMS_FixtureCoverage:
    """Positive/negative coverage for the two engine-only-verified W-AIMS
    patterns NOT migrating to derived-flag form in v0.5."""

    @pytest.mark.parametrize("pattern", PATTERNS)
    def test_positive_fires(self, pattern):
        fp = FIXTURES / pattern / "positive.jsonld"
        assert fp.exists(), f"positive fixture missing for {pattern}"
        fired = _firings(fp)
        assert pattern in fired, (
            f"{pattern} must fire on positive fixture; "
            f"actual firings: {sorted(fired)}"
        )

    @pytest.mark.parametrize("pattern", PATTERNS)
    def test_negative_silent(self, pattern):
        fp = FIXTURES / pattern / "negative.jsonld"
        assert fp.exists(), f"negative fixture missing for {pattern}"
        fired = _firings(fp)
        assert pattern not in fired, (
            f"{pattern} must NOT fire on negative fixture; "
            f"actual firings: {sorted(fired)}"
        )


@needs_jar
class TestW_AIMS_BoundaryDesignDecisions:
    """Boundary fixtures encode explicit design decisions about edge cases.

    v0.5 update: the empty-string semantics changed with the v0.5 derivation
    pre-pass migration (per pre-pass spec §3.3.7). The boundary tests now
    assert v0.5 post-migration behavior — empty-string is treated as missing
    and the rule FIRES, not the v0.4 noValue-semantics behavior of treating
    empty-string as present-and-rule-silent."""

    def test_W_AR_02_empty_string_justification_now_fires_v0_5(self):
        """v0.5 DESIGN DECISION (changed from v0.4): empty-string
        justification is treated as missing via the
        _justificationNonEmpty derived flag. The consumer rule's
        noValue check on the derived flag returns true when the flag
        is absent (which happens when justification is empty-string)
        → rule FIRES correctly."""
        fp = FIXTURES / "W-AR-02" / "boundary.jsonld"
        fired = _firings(fp)
        assert "W-AR-02" in fired, (
            "W-AR-02 v0.5 expectation: empty-string justification is "
            "treated as missing via _justificationNonEmpty derivation; "
            "rule fires correctly."
        )

    def test_W_AIMS_OBJECTIVE_UNMEASURED_empty_string_target_measure_now_fires_v0_5(self):
        """v0.5 DESIGN DECISION (changed from v0.4): empty-string
        targetMeasure is treated as missing via the
        _targetMeasureNonEmpty derived flag."""
        fp = FIXTURES / "W-AIMS-OBJECTIVE-UNMEASURED" / "boundary.jsonld"
        fired = _firings(fp)
        assert "W-AIMS-OBJECTIVE-UNMEASURED" in fired, (
            "W-AIMS-OBJECTIVE-UNMEASURED v0.5 expectation: empty-string "
            "targetMeasure is treated as missing via _targetMeasureNonEmpty "
            "derivation; rule fires correctly."
        )

"""P2.5 — the firewall chokepoint: one mandatory, fail-closed boundary (§0/§4).

Every pack output crosses check_crossing, which consults the mandatory,
non-pluggable policy (token-ban + structural + signature-scoping) keyed on the
capability's firewallPlacement. These tests pin both halves: legitimate outputs
pass per placement, and — the load-bearing invariant — an unknown placement, an
unsigned action, a smuggled verdict/scalar/action-block, or any policy error
DENIES the crossing. The firewall never silently allows.
"""

from __future__ import annotations

import pytest

from uofa_cli import firewall
from uofa_cli.firewall import (
    PLACEMENT_ACTION,
    PLACEMENT_MEASUREMENT,
    PLACEMENT_REFERENCE,
    FirewallViolation,
    check_crossing,
    enforce_crossing,
)

# The four open-core measurement block shapes — all must cross cleanly.
_LEGIT_MEASUREMENT_BLOCKS = [
    [{"quantityOfInterest": "cl", "statistics": {"mean": 0.1}, "measurementRef": "m-residuals"}],
    {"benchmarkSpansEnvelope": True, "evaluationPointInEnvelope": False, "measurementRef": "m-envelope"},
    [{"constraintId": "continuity", "statistics": {"max": 0.002}, "measurementRef": "m-physics"}],
    {"surrogateUQMethod": "conformal", "empiricalCoverage": 1.0, "measurementRef": "m-uq"},
]


@pytest.mark.parametrize("block", _LEGIT_MEASUREMENT_BLOCKS)
def test_legitimate_measurement_blocks_allowed(block):
    assert check_crossing(block, placement=PLACEMENT_MEASUREMENT).allowed


def test_measurement_forbidden_token_denied():
    d = check_crossing({"verdict": "pass"}, placement=PLACEMENT_MEASUREMENT)
    assert not d.allowed and any("verdict" in r for r in d.reasons)


def test_measurement_nested_forbidden_token_denied():
    block = [{"quantityOfInterest": "cl", "statistics": {"accepted": True}}]
    assert not check_crossing(block, placement=PLACEMENT_MEASUREMENT).allowed


def test_measurement_scalar_denied():
    # A bare scalar is not measurement-shaped — a verdict could hide as one.
    d = check_crossing("Accepted", placement=PLACEMENT_MEASUREMENT)
    assert not d.allowed and any("scalar" in r for r in d.reasons)


def test_measurement_nested_action_block_denied():
    # An action-region block smuggled inside a measurement output is denied.
    block = {"measurementRef": "m-x", "engineerDecision": {"decisionValue": "Accepted"}}
    d = check_crossing(block, placement=PLACEMENT_MEASUREMENT)
    assert not d.allowed and any("action-region" in r for r in d.reasons)


def test_reference_truth_allowed_verdict_denied():
    assert check_crossing({"cl": [0.5, 0.8]}, placement=PLACEMENT_REFERENCE).allowed
    assert not check_crossing({"score": 0.9}, placement=PLACEMENT_REFERENCE).allowed


def test_action_signed_allowed_unsigned_denied():
    signed = {"action": "restrict", "actionSignature": "ed25519:deadbeef"}
    assert check_crossing(signed, placement=PLACEMENT_ACTION).allowed
    # An action carrying decision content but NO signature fails closed.
    unsigned = {"action": "restrict", "decisionValue": "Accepted"}
    d = check_crossing(unsigned, placement=PLACEMENT_ACTION)
    assert not d.allowed and any("not signed" in r for r in d.reasons)
    # Explicit signed flag overrides inference.
    assert check_crossing({"action": "x"}, placement=PLACEMENT_ACTION, signed=True).allowed
    assert not check_crossing(signed, placement=PLACEMENT_ACTION, signed=False).allowed


def test_unknown_placement_fails_closed():
    for bogus in ("", "measurement", None, "decision-region"):
        d = check_crossing({"cl": [1]}, placement=bogus)
        assert not d.allowed and any("fail closed" in r for r in d.reasons)


def test_policy_error_fails_closed(monkeypatch):
    # If the policy itself errors, the crossing is denied — never allowed-by-default.
    def boom(_output, _path="$"):
        raise RuntimeError("policy blew up")
    monkeypatch.setattr(firewall, "find_forbidden_property_names", boom)
    d = check_crossing({"cl": [1]}, placement=PLACEMENT_MEASUREMENT)
    assert not d.allowed and any("policy error" in r for r in d.reasons)


def test_enforce_raises_on_denial_and_passes_on_allow():
    enforce_crossing({"measurementRef": "m"}, placement=PLACEMENT_MEASUREMENT)  # no raise
    with pytest.raises(FirewallViolation, match="firewall denied"):
        enforce_crossing({"verdict": "pass"}, placement=PLACEMENT_MEASUREMENT)


def test_chokepoint_is_wired_into_the_orchestrator():
    # The orchestrator routes every measurement block through the chokepoint, so
    # the relaxed measurement region is guarded at the orchestration seam.
    import inspect
    from uofa_cli.interrogate import orchestrator
    src = inspect.getsource(orchestrator.run_measurements)
    assert "enforce_crossing" in src and "PLACEMENT_MEASUREMENT" in src

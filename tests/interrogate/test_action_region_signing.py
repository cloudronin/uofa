"""Phase 1a — generalized action-region two-scope signing.

The engineerDecision two-scope mechanism is generalized so any action-region
block (guardrailAction, future verified-outcome labels) signs in its own scope,
excluded from the measurement signature and exempt from the measurement-region
denylist. These tests pin: (1) a generic action block round-trips and is
tamper-evident, (2) the measurement signature survives an appended action block,
(3) the engineerDecision path is unchanged (byte-identical wrapper), (4) the
firewall exempts top-level action-region blocks ONLY at the top level.
"""

from __future__ import annotations

import json

from uofa_cli import integrity
from uofa_cli.interrogate import signing
from uofa_cli.interrogate.forbidden import (
    ACTION_REGION_KEYS,
    find_forbidden_in_measurement_region,
)


def _pkg() -> dict:
    return {
        "schemaVersion": "sip-evidence-bundle/v0.1",
        "bundleId": "b1",
        "measurements": {
            "referenceResiduals": [{"quantityOfInterest": "cl", "statistics": {"mean": 0.1}}]
        },
    }


def _keys(tmp_path):
    key = tmp_path / "k.key"
    integrity.generate_keypair(key)
    return key, key.with_suffix(".pub")


def test_action_region_keys_include_decision_and_guardrail():
    assert "engineerDecision" in ACTION_REGION_KEYS
    assert "guardrailAction" in ACTION_REGION_KEYS


def test_measurement_excluded_covers_every_action_region_key():
    for k in ACTION_REGION_KEYS:
        assert k in signing.MEASUREMENT_EXCLUDED


def test_scoped_block_signs_verifies_and_is_tamper_evident(tmp_path):
    key, pub = _keys(tmp_path)
    p = tmp_path / "pkg.json"
    p.write_text(json.dumps(_pkg()))
    signing.sign_measurement(p, key)
    pkg = json.loads(p.read_text())
    assert signing.verify_measurement(pkg, pub) == (True, True)

    # A generic guardrail action block, signed in its OWN ("action") scope.
    block = {"actionId": "restrict-envelope", "attributedTo": signing.fingerprint_from_public_key(pub)}
    pkg["guardrailAction"] = signing.sign_scoped_block(
        pkg, key, block, scope_key="action", signature_field="actionSignature"
    )
    ok, reason = signing.verify_scoped_block(
        pkg, pub, block_key="guardrailAction", scope_key="action",
        signature_field="actionSignature", attributed_by_field="attributedTo",
    )
    assert ok, reason

    # The measurement signature STILL verifies — the action block is excluded.
    assert signing.verify_measurement(pkg, pub) == (True, True)

    # Tampering any measurement breaks the action signature (bound to the
    # recomputed measurement hash), even though the action block is untouched.
    pkg["measurements"]["referenceResiduals"][0]["statistics"]["mean"] = 0.999
    ok2, _ = signing.verify_scoped_block(
        pkg, pub, block_key="guardrailAction", scope_key="action",
        signature_field="actionSignature", attributed_by_field="attributedTo",
    )
    assert not ok2


def test_decision_path_unchanged_after_generalization(tmp_path):
    key, pub = _keys(tmp_path)
    p = tmp_path / "pkg.json"
    p.write_text(json.dumps(_pkg()))
    signing.sign_measurement(p, key)
    pkg = json.loads(p.read_text())
    block = signing.build_decision_block(
        key_path=key, acceptance_criterion="Cl within 3% over envelope",
        decision_value="Accepted", decided_at="2026-05-31T00:00:00Z",
    )
    pkg["engineerDecision"] = signing.sign_decision(pkg, key, block)
    ok, reason = signing.verify_decision(pkg, pub)
    assert ok, reason
    # decisionSignature is still the field name; scope is still "decision".
    assert "decisionSignature" in pkg["engineerDecision"]


def test_firewall_exempts_action_region_only_at_top_level():
    # Forbidden tokens INSIDE top-level action-region blocks are exempt.
    bundle = {
        "measurements": {"referenceResiduals": []},
        "engineerDecision": {"accepted": True},        # 'accepted' is a forbidden token
        "guardrailAction": {"outcome": "restrict"},     # 'outcome' is a forbidden token
    }
    assert list(find_forbidden_in_measurement_region(bundle)) == []

    # A forbidden token in the measurement region is still caught.
    leaked = {"measurements": {"verdict": "pass"}}
    assert any(t == "verdict" for _, t in find_forbidden_in_measurement_region(leaked))

    # An action-region key smuggled DEEPER is not exempt — its contents are scanned.
    smuggled = {"measurements": {"guardrailAction": {"verdict": "pass"}}}
    assert any(t == "verdict" for _, t in find_forbidden_in_measurement_region(smuggled))

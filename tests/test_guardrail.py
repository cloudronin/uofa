"""P6 §6 — the Guardrail interface: a new consumer of detection firings.

A guardrail consumes `check.run_structured(...).rules.firings` and emits an
action-region `guardrailAction` block, signed in its own §4 "action" scope —
excluded from the measurement signature, tamper-evident, verifying independently.
This ships the INTERFACE + a STUB only (the real threshold/fix logic is
downstream), so the tests pin the contract and its firewall placement, not policy:

- the stub consumes firings and emits a structurally-valid action block;
- that block signs + verifies in the action scope, the measurement signature is
  unaffected, and tampering a measurement breaks the action signature;
- forbidden tokens inside the top-level action block are exempt, but the
  measurement region stays guarded;
- the core pack's guardrail capability resolves and passes the load gate.
"""

from __future__ import annotations

import argparse
import json

import pytest

from uofa_cli import guardrail as G
from uofa_cli import integrity, paths
from uofa_cli.interrogate import signing
from uofa_cli.interrogate.forbidden import find_forbidden_in_measurement_region

FIRINGS = [
    {"patternId": "W-SURR-03", "severity": "High", "hits": 1, "pack": "surrogate"},
    {"patternId": "W-EP-04", "severity": "High", "hits": 6, "pack": "core"},
]


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


def test_stub_consumes_firings_and_decides_nothing():
    block = G.ThresholdGuardrailStub().assess(FIRINGS)
    assert block["capabilityId"] == "guardrail:basic-threshold-stub"
    assert block["firingsConsidered"] == 2
    assert block["patternsFired"] == ["W-SURR-03", "W-EP-04"]
    assert block["packsFired"] == ["core", "surrogate"]
    assert block["action"] == "none"  # interface only — no policy


def test_build_attributes_raw_firings_without_mutating_caller():
    # Raw check-report firings arrive WITHOUT a pack key; the guardrail attributes
    # them via the manifest index (§7.3), recording which pack fired which weakener.
    raw = [
        {"patternId": "W-AIMS-AUDIT-STALE", "severity": "High", "hits": 1},
        {"patternId": "W-EP-04", "severity": "High", "hits": 6},
    ]
    block = G.build_guardrail_action(G.ThresholdGuardrailStub(), raw)
    assert block["packsFired"] == ["core", "iso42001"]
    assert "pack" not in raw[0]  # caller's firings left untouched (attributed on copies)


def test_guardrail_action_signs_verifies_and_is_tamper_evident(tmp_path):
    key, pub = _keys(tmp_path)
    p = tmp_path / "pkg.json"
    p.write_text(json.dumps(_pkg()))
    signing.sign_measurement(p, key)
    pkg = json.loads(p.read_text())

    block = G.build_guardrail_action(G.ThresholdGuardrailStub(), FIRINGS)
    pkg["guardrailAction"] = G.sign_guardrail_action(pkg, key, block)

    ok, reason = G.verify_guardrail_action(pkg, pub)
    assert ok, reason
    # The action is attributed to the signing key; measurement signature intact.
    assert pkg["guardrailAction"]["attributedTo"] == signing.fingerprint_from_public_key(pub)
    assert signing.verify_measurement(pkg, pub) == (True, True)

    # Tampering any measurement breaks the action signature (bound to the
    # recomputed measurement hash) even though the action block is untouched.
    pkg["measurements"]["referenceResiduals"][0]["statistics"]["mean"] = 0.999
    ok2, _ = G.verify_guardrail_action(pkg, pub)
    assert not ok2


def test_missing_or_unsigned_action_is_no_action_not_failure(tmp_path):
    _, pub = _keys(tmp_path)
    ok, reason = G.verify_guardrail_action(_pkg(), pub)  # no guardrailAction block
    assert not ok and "guardrailAction" in reason


def test_action_block_is_firewall_exempt_at_top_level_only():
    # The action block holds action content; at the top level it is exempt from
    # the measurement-region denylist (its signature governs it).
    bundle = {"measurements": {"referenceResiduals": []},
              "guardrailAction": {"action": "restrict", "outcome": "noted"}}  # 'outcome' forbidden elsewhere
    assert list(find_forbidden_in_measurement_region(bundle)) == []
    # The same token in the measurement region is still caught.
    leaked = {"measurements": {"outcome": "noted"}}
    assert any(t == "outcome" for _, t in find_forbidden_in_measurement_region(leaked))


def test_load_guardrail_resolves_core_stub():
    g = G.load_guardrail("uofa_cli.guardrail:ThresholdGuardrailStub")
    assert isinstance(g, G.Guardrail)
    assert g.capability_id == "guardrail:basic-threshold-stub"


def test_load_guardrail_rejects_non_guardrail():
    with pytest.raises(ValueError, match="Guardrail subclass"):
        G.load_guardrail("uofa_cli.paths:find_repo_root")


def test_core_guardrail_capability_resolves_and_passes_load_gate():
    # CORE_INTERFACE_VERSIONS recognizes the guardrail interface, so core's own
    # guardrail capability is accepted at the load gate, and its payload.impl
    # resolves to the stub.
    assert paths.CORE_INTERFACE_VERSIONS.get("guardrail") == "1.0"
    paths.validate_active_packs()  # core (incl. its guardrail capability) + active set
    core = paths.pack_manifest("core")
    impl = next(c["payload"]["impl"] for c in core["capabilities"] if c["leg"] == "guardrail")
    assert isinstance(G.load_guardrail(impl), G.Guardrail)


# ── Basic ThresholdGuardrail (B1 — real policy on the §6 interface) ───────────


def test_threshold_fires_and_commands_envelope_restriction():
    block = G.ThresholdGuardrail().assess(FIRINGS)  # two High firings, default threshold High
    assert block["capabilityId"] == "guardrail:basic-threshold"
    assert block["action"] == "restrict"            # engineer-commanded default
    assert block["trigger"]["thresholdSeverity"] == "High"
    assert set(block["triggeringPatterns"]) == {"W-SURR-03", "W-EP-04"}


def test_below_threshold_is_no_action():
    low = [{"patternId": "W-X", "severity": "Medium", "hits": 1, "pack": "core"}]
    block = G.ThresholdGuardrail().assess(low)       # Medium < High threshold
    assert block["action"] == "none"
    assert block["triggeringPatterns"] == []


def test_engineer_commands_threshold_and_action():
    # Raise the bar to Critical: the two High firings no longer trigger.
    assert G.ThresholdGuardrail().assess(FIRINGS, context={"threshold": "Critical"})["action"] == "none"
    # Command a different basic action on a Critical firing.
    crit = [{"patternId": "W-SURR-02", "severity": "Critical", "hits": 1, "pack": "surrogate"}]
    block = G.ThresholdGuardrail().assess(crit, context={"threshold": "Critical", "action": "refuse"})
    assert block["action"] == "refuse"


def test_non_basic_action_is_refused_scope_discipline():
    # apply-fix / modify-model / retrain are Product B — the basic guardrail refuses them.
    with pytest.raises(ValueError, match="Product B"):
        G.ThresholdGuardrail().assess(FIRINGS, context={"action": "apply-fix"})


def test_real_guardrail_action_signs_and_verifies(tmp_path):
    key, pub = _keys(tmp_path)
    p = tmp_path / "pkg.json"
    p.write_text(json.dumps(_pkg()))
    signing.sign_measurement(p, key)
    pkg = json.loads(p.read_text())

    block = G.build_guardrail_action(G.ThresholdGuardrail(), FIRINGS)
    assert block["action"] == "restrict"
    pkg["guardrailAction"] = G.sign_guardrail_action(pkg, key, block)
    ok, reason = G.verify_guardrail_action(pkg, pub)
    assert ok, reason
    # Action content stays out of the measurement region (firewall).
    assert list(find_forbidden_in_measurement_region(pkg)) == []


def test_guardrail_command_signs_and_verifies(tmp_path, monkeypatch):
    # The `uofa guardrail` command: firings → signed action-region block on the
    # package. Stub the check pipeline (the rule engine is covered by the
    # demo-chain test); this pins the command's build → sign → write wiring.
    key, pub = _keys(tmp_path)
    p = tmp_path / "pkg.json"
    p.write_text(json.dumps(_pkg()))
    signing.sign_measurement(p, key)

    fake = type("R", (), {"rules": type("RR", (), {"firings": list(FIRINGS)})()})()
    monkeypatch.setattr("uofa_cli.commands.check.run_structured", lambda _a: fake)

    from uofa_cli.commands import guardrail as gcmd
    args = argparse.Namespace(
        file=p, key=key, threshold="High", action="restrict", min_hits=1, output=None,
        active_packs=["surrogate"], no_color=True, repo_root=None,
    )
    assert gcmd.run(args) == 0

    pkg = json.loads(p.read_text())
    assert pkg["guardrailAction"]["action"] == "restrict"
    ok, reason = G.verify_guardrail_action(pkg, pub)
    assert ok, reason
    assert list(find_forbidden_in_measurement_region(pkg)) == []

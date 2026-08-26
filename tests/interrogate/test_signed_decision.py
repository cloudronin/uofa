"""Addendum A10/A13: the signed-engineer-decision lifecycle and firewall behaviors.

Exercises the two-scope signatures, the decision command, and dual-signature
verify directly (no model framework needed — bundles are built in-process).
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import pytest

from uofa_cli import integrity
from uofa_cli.interrogate import signing
from uofa_cli.interrogate.forbidden import FORBIDDEN_TOKENS, find_forbidden_in_measurement_region
from uofa_cli.commands import decision, verify

REPO_ROOT = Path(__file__).resolve().parents[2]


def _bundle() -> dict:
    return {
        "bundleId": "b", "sipVersion": "0.1.0", "schemaVersion": "sip-evidence-bundle/v0.1",
        "generatedAt": "2026-05-30T12:00:00Z",
        "subject": {"surrogateId": "s", "modelVersion": "1", "surrogateType": "PINN",
                    "modelFingerprint": "sha256:x", "adapterRef": "m:A"},
        "declaredScope": {"trainingEnvelope": {"dimensions": [{"name": "re", "min": 1.0, "max": 2.0}]},
                          "declaredPhysicsConstraint": []},
        "measurementProvenance": [{"measurementId": "m1", "producedBy": {"library": "numpy", "version": "1.26"}}],
        "measurements": {
            "referenceResiduals": [{"quantityOfInterest": "cl", "statistics": {"count": 10, "mean": 0.01, "rms": 0.02, "max": 0.05}}],
            "envelopeCoverage": {"benchmarkSpansEnvelope": True, "evaluationPointInEnvelope": True},
            "physicsConstraintResidual": [],
            "uqCalibration": {"surrogateUQMethod": "conformal-prediction", "empiricalCoverage": 0.9, "nominalCoverage": 0.9},
        },
        "provenance": {"activity": {"id": "sip:run", "type": "prov:Activity"}},
        "completeness": {"fieldsPresent": ["referenceResiduals"], "fieldsDeliberatelyOmitted": []},
    }


@pytest.fixture
def keys(tmp_path):
    sip = tmp_path / "sip.key"; integrity.generate_keypair(sip)
    eng = tmp_path / "eng.key"; integrity.generate_keypair(eng)
    return sip, eng


def _signed(tmp_path, sip_key, name="pkg.json") -> Path:
    path = tmp_path / name
    path.write_text(json.dumps(_bundle()), encoding="utf-8")
    signing.sign_measurement(path, sip_key)
    return path


DECIDER = "https://uofa.net/org/demo-reviewer"


def _sign_decision(pkg, eng_key, value="accepted", decided_at="2026-05-30T00:00:00Z") -> int:
    """The two acts, in order: author the judgment, then attest it.

    These used to be one call, because `decision sign` both authored and signed.
    They are two now, and the helper keeps its old signature so every test below
    reads as before while exercising the split underneath.
    """
    rc = _record_decision(pkg, value=value, decided_at=decided_at)
    if rc != 0:
        return rc
    return _attest(pkg, eng_key)


def _record_decision(pkg, value="accepted", decided_at="2026-05-30T00:00:00Z",
                     actor=DECIDER, append=False) -> int:
    return decision.run(argparse.Namespace(
        decision_cmd="record", file=pkg, criterion="Cl within 3% over envelope",
        value=value, rationale="residuals within tolerance", decided_at=decided_at,
        actor=actor, append=append, output=None,
    ))


def _attest(pkg, eng_key) -> int:
    """Attest an already-authored record.

    The namespace is built by the REAL parser rather than hand-listed, so this
    helper cannot drift from the CLI's own contract -- a hand-built namespace
    silently omits whatever flag the command grows next, and the test then
    exercises a shape no user can actually type.
    """
    from uofa_cli.commands import sign as sign_cmd

    parser = argparse.ArgumentParser()
    sign_cmd.add_arguments(parser)
    args = parser.parse_args([str(pkg), "--key", str(eng_key), "--as", "reviewer"])
    return sign_cmd.run(args)


def test_measurement_pass_has_no_decision(tmp_path, keys):
    sip, _ = keys
    bundle = json.loads(_signed(tmp_path, sip).read_text())
    assert "hasDecisionRecord" not in bundle
    assert list(find_forbidden_in_measurement_region(bundle)) == []


def test_sign_then_verify(tmp_path, keys):
    sip, eng = keys
    pkg = _signed(tmp_path, sip)
    assert _sign_decision(pkg, eng) == 0
    bundle = json.loads(pkg.read_text())
    assert bundle["hasDecisionRecord"]["decisionValue"] == "Accepted"  # permitted inside the block
    ok, reason = signing.verify_decision(bundle, eng.with_suffix(".pub"))
    assert ok, reason


def test_unsigned_block_is_no_decision(tmp_path, keys):
    sip, eng = keys
    bundle = json.loads(_signed(tmp_path, sip).read_text())
    bundle["hasDecisionRecord"] = {"decidedBy": "sha256:x", "acceptanceCriterion": "c",
                                  "decisionValue": "Accepted", "decidedAt": "t"}  # no signature
    ok, _ = signing.verify_decision(bundle, eng.with_suffix(".pub"))
    assert not ok


def test_decision_only_scope_rejected(tmp_path, keys):
    sip, eng = keys
    bundle = json.loads(_signed(tmp_path, sip).read_text())
    from uofa_cli.integrity import canonicalize_and_hash, sign_hash
    block = {"decidedBy": signing.fingerprint_from_private_key(eng), "acceptanceCriterion": "c",
             "decisionValue": "Accepted", "decidedAt": "t"}
    _, scope_hash = canonicalize_and_hash({"decision": block})  # scope omits measurementHash
    bundle["hasDecisionRecord"] = {**block, "decisionSignature": "ed25519:" + sign_hash(scope_hash, eng)}
    ok, _ = signing.verify_decision(bundle, eng.with_suffix(".pub"))
    assert not ok  # measurements can't be swapped under a signed decision


def test_tamper_breaks_decision_signature(tmp_path, keys):
    sip, eng = keys
    pkg = _signed(tmp_path, sip)
    _sign_decision(pkg, eng)
    bundle = json.loads(pkg.read_text())
    bundle["measurements"]["referenceResiduals"][0]["statistics"]["max"] = 9.9
    ok, _ = signing.verify_decision(bundle, eng.with_suffix(".pub"))
    assert not ok


def test_verify_reports_independently_decision_nonfatal(tmp_path, keys):
    sip, eng = keys
    pkg = _signed(tmp_path, sip)
    _sign_decision(pkg, eng)
    other = tmp_path / "other.key"; integrity.generate_keypair(other)
    # Wrong decision key → decision not verified, but measurement is fine → rc 0.
    rc = verify.run(argparse.Namespace(file=pkg, pubkey=sip.with_suffix(".pub"),
                                       decision_pubkey=other.with_suffix(".pub"), context=None))
    assert rc == 0


def test_stale_bundle_refusal(tmp_path, keys):
    sip, eng = keys
    pkg = _signed(tmp_path, sip)
    bundle = json.loads(pkg.read_text())
    bundle["measurements"]["referenceResiduals"][0]["statistics"]["max"] = 9.9  # measurements ≠ signed hash
    pkg.write_text(json.dumps(bundle), encoding="utf-8")
    # Under the split, AUTHORING is where this must refuse: attestation refusing
    # afterwards would leave the drifted package already carrying the verdict.
    assert _record_decision(pkg) == 1
    assert "hasDecisionRecord" not in json.loads(pkg.read_text())  # wrote nothing
    assert _sign_decision(pkg, eng) != 0  # and the fused sequence still refuses


def test_attesting_requires_an_external_key(tmp_path, keys):
    """No key, no attestation -- and a refused attestation writes nothing.

    This once asserted that a keyless invocation left NO decision block at all,
    because authoring and signing were one act. They are two now, so authoring
    without a key is the documented path and an unsigned block is the correct
    intermediate. What survives is the part that was always the point: the
    ATTESTATION cannot happen without the decider's own key, and a refusal must
    not leave a half-attested record behind.
    """
    sip, _ = keys
    pkg = _signed(tmp_path, sip)
    assert _record_decision(pkg) == 0
    before = json.loads(pkg.read_text())["hasDecisionRecord"]
    assert "hasDecisionSignature" not in before

    result = subprocess.run(
        [sys.executable, "-m", "uofa_cli", "sign", str(pkg), "--as", "reviewer"],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )
    assert result.returncode != 0
    assert "key" in (result.stderr + result.stdout).lower()
    assert json.loads(pkg.read_text())["hasDecisionRecord"] == before, \
        "a refused attestation must leave the record exactly as it found it"


def test_no_fused_approve_path():
    from uofa_cli.commands import interrogate
    parser = argparse.ArgumentParser()
    interrogate.add_arguments(parser)
    opts = [s for action in parser._actions for s in action.option_strings]
    for banned in ["--decide", "--accept", "--auto-accept", "--value", "--sign", "--verdict", "--criterion", "--threshold"]:
        assert banned not in opts, f"interrogate must not offer {banned} (no fused measure+sign)"


def test_review_is_read_only_and_silent(tmp_path, keys, capsys):
    sip, eng = keys
    pkg = _signed(tmp_path, sip)
    _sign_decision(pkg, eng)  # even with a decision present, review stays silent on the verdict
    capsys.readouterr()  # discard the sign command's output; capture only review below
    rc = decision.run(argparse.Namespace(decision_cmd="review", file=pkg))
    assert rc == 0
    out = capsys.readouterr().out.lower()
    for token in FORBIDDEN_TOKENS:
        assert token.lower() not in out, f"review leaked verdict token {token!r}"
    for word in ["recommend", "should ", "looks good", "verdict", "approve"]:
        assert word not in out


def test_round_trip_mode_independence(tmp_path, keys):
    # ed25519 is deterministic, so the same engineer + bundle + fields yields a
    # byte-identical hasDecisionRecord whether driven from the terminal or a vendor
    # product — conformance is a property of the artifact (A12).
    sip, eng = keys
    p1 = _signed(tmp_path, sip, "p1.json"); _sign_decision(p1, eng)
    p2 = _signed(tmp_path, sip, "p2.json"); _sign_decision(p2, eng)
    b1, b2 = json.loads(p1.read_text()), json.loads(p2.read_text())
    assert (b1["hasDecisionRecord"]["hasDecisionSignature"]["signatureValue"]
            == b2["hasDecisionRecord"]["hasDecisionSignature"]["signatureValue"])
    assert signing.verify_decision(b1, eng.with_suffix(".pub"))[0]
    assert signing.verify_decision(b2, eng.with_suffix(".pub"))[0]

"""Third-party statements about who signed, and under what authority.

A decision signature names a key; the decision record names an actor; nothing
connected them. A verifier learned "some key signed this" and "a field claims an
actor" and could not establish they were the same party -- so anyone holding that
private key, person or agent, produced a byte-identical artifact.

These two blocks are the missing link, and the tests below are mostly about the
ways a link can LOOK like evidence while establishing nothing: a binding that
verifies and names somebody else, an authority that vouches only for itself, a
grant that existed but was not in force.
"""

from __future__ import annotations

import pytest

from uofa_cli import attestations as A
from uofa_cli import integrity
from uofa_cli.interrogate import forbidden, signing

FP = "sha256:" + "a" * 64
OTHER_FP = "sha256:" + "b" * 64


@pytest.fixture
def authority(tmp_path):
    key, pub = integrity.generate_keypair(tmp_path / "authority.key")
    return key, pub


@pytest.fixture
def stranger(tmp_path):
    key, pub = integrity.generate_keypair(tmp_path / "stranger.key")
    return key, pub


def _package():
    return {
        "@context": "https://uofa.net/ns/v0.9",
        "id": "urn:uofa:pkg:1",
        "measured": 1,
        "hasDecisionRecord": {"id": "urn:uofa:decision:1",
                              "actor": "urn:actor/alice",
                              "outcome": "Conditional"},
    }


def _binding(**over):
    args = dict(bound_actor="urn:actor/alice", bound_key=FP,
                provider_issuer="https://huggingface.co",
                provider_subject="hmac:9f2c", possession_proven_at="2026-09-14T19:12:03Z",
                deployment_id="preview", issued_at="2026-09-14T19:12:04Z",
                context_version="v0.10")
    args.update(over)
    return A.build_identity_binding(**args)


def _authorization(**over):
    args = dict(authorized_actor="urn:actor/alice", project="studyone",
                decision_record="urn:uofa:decision:1", grant_id="grant-7",
                effective_from="2026-09-14T18:00:00Z",
                authorization_checked_at="2026-09-14T19:30:00Z",
                decision_signed_at="2026-09-14T19:30:00Z",
                deployment_id="preview", issued_at="2026-09-14T19:30:01Z",
                context_version="v0.10")
    args.update(over)
    return A.build_authorization_attestation(**args)


# ── the placement property, which is the one that breaks silently ───────────

def test_both_blocks_are_action_regions_so_the_seal_survives_them():
    """THE structural property. A block outside `ACTION_REGION_KEYS` is inside
    the measurement view, so the issuer seal would cover it -- and an attestation
    arriving AFTER sealing would then break the seal it was added beside."""
    for key in (A.IDENTITY_BLOCK_KEY, A.AUTHORIZATION_BLOCK_KEY):
        assert key in forbidden.ACTION_REGION_KEYS, key
        assert key in signing.MEASUREMENT_EXCLUDED, key


def test_attaching_a_binding_does_not_move_the_measurement_hash(authority):
    """Measured, not asserted: the seal has to survive a binding arriving later
    exactly as it survives a decision arriving later."""
    key, _pub = authority
    pkg = _package()
    before = signing.measurement_hash(pkg)
    pkg[A.IDENTITY_BLOCK_KEY] = A.sign_identity_binding(pkg, _binding(), key_path=key)
    pkg[A.AUTHORIZATION_BLOCK_KEY] = A.sign_authorization_attestation(
        pkg, _authorization(), key_path=key)
    assert signing.measurement_hash(pkg) == before


# ── the round trip ──────────────────────────────────────────────────────────

def test_a_binding_verifies_and_names_its_authority(authority):
    key, pub = authority
    pkg = _package()
    signed = A.sign_identity_binding(pkg, _binding(), key_path=key)
    pkg[A.IDENTITY_BLOCK_KEY] = signed
    assert A.verify_identity_binding(pkg, pub) == (True, "ok")
    assert signed[A.AUTHORITY_FIELD] == signing.fingerprint_from_public_key(pub)


def test_an_authorization_verifies(authority):
    key, pub = authority
    pkg = _package()
    pkg[A.AUTHORIZATION_BLOCK_KEY] = A.sign_authorization_attestation(
        pkg, _authorization(), key_path=key)
    assert A.verify_authorization_attestation(pkg, pub) == (True, "ok")


def test_an_in_memory_key_signs_without_touching_the_filesystem(authority, tmp_path):
    """A hosted deployment receives its authority key as a secret env var and
    must never write it to the filesystem it serves downloads from."""
    key, pub = authority
    pkg = _package()
    pkg[A.IDENTITY_BLOCK_KEY] = A.sign_identity_binding(
        pkg, _binding(), key_bytes=key.read_bytes())
    assert A.verify_identity_binding(pkg, pub) == (True, "ok")


def test_the_two_scopes_cannot_stand_in_for_each_other(authority):
    """Cross-scope separation by construction: the wrapper object's second key
    differs, so a binding's bytes can never verify as an authorization."""
    key, pub = authority
    pkg = _package()
    binding = A.sign_identity_binding(pkg, _binding(), key_path=key)
    pkg[A.AUTHORIZATION_BLOCK_KEY] = {
        **{k: v for k, v in binding.items() if k != A.IDENTITY_SIGNATURE_FIELD},
        A.AUTHORIZATION_SIGNATURE_FIELD: binding[A.IDENTITY_SIGNATURE_FIELD]}
    ok, _why = A.verify_authorization_attestation(pkg, pub)
    assert not ok, "a binding's signature verified as an authorization"


# ── RED CHECKS: evidence that establishes nothing ───────────────────────────

def test_a_binding_for_the_wrong_actor_does_not_satisfy_this_decision(authority):
    """The most dangerous shape here: cryptographically valid, and about
    somebody else."""
    key, _pub = authority
    signed = A.sign_identity_binding(_package(), _binding(), key_path=key)
    ok, why = A.binding_links(signed, decision_actor="urn:actor/mallory",
                              signer_identity=FP)
    assert not ok and "somebody else" in why


def test_a_binding_for_the_wrong_key_does_not_satisfy_this_decision(authority):
    key, _pub = authority
    signed = A.sign_identity_binding(_package(), _binding(), key_path=key)
    ok, why = A.binding_links(signed, decision_actor="urn:actor/alice",
                              signer_identity=OTHER_FP)
    assert not ok and "different key" in why


def test_an_authority_that_did_not_sign_it_cannot_vouch_for_it(authority, stranger):
    key, _pub = authority
    _skey, spub = stranger
    pkg = _package()
    pkg[A.IDENTITY_BLOCK_KEY] = A.sign_identity_binding(pkg, _binding(), key_path=key)
    ok, _why = A.verify_identity_binding(pkg, spub)
    assert not ok


def test_editing_any_signed_field_invalidates_the_binding(authority):
    """Every field that affects what the statement MEANS is inside the bytes."""
    key, pub = authority
    pkg = _package()
    signed = A.sign_identity_binding(pkg, _binding(), key_path=key)
    for field, value in (("boundActor", "urn:actor/mallory"),
                         ("boundKey", OTHER_FP),
                         ("identityProviderIssuer", "https://evil.example"),
                         ("identityProviderSubject", "hmac:0000"),
                         ("possessionProvenAt", "2020-01-01T00:00:00Z"),
                         ("proofPurpose", "decision-signing"),
                         ("deploymentId", "production"),
                         ("contextVersion", "v0.9")):
        pkg[A.IDENTITY_BLOCK_KEY] = {**signed, field: value}
        ok, _why = A.verify_identity_binding(pkg, pub)
        assert not ok, f"editing {field} left the binding verifying"


def test_an_authorization_for_another_project_or_decision_is_refused(authority):
    key, _pub = authority
    auth = A.sign_authorization_attestation(_package(), _authorization(), key_path=key)
    ok, why = A.authorization_links(auth, bound_actor="urn:actor/alice",
                                    project="a-different-study",
                                    decision_record="urn:uofa:decision:1")
    assert not ok and "project" in why
    ok, why = A.authorization_links(auth, bound_actor="urn:actor/alice",
                                    project="studyone",
                                    decision_record="urn:uofa:decision:99")
    assert not ok and "not this decision" in why


def test_an_authorization_for_a_different_actor_than_the_binding_is_refused(authority):
    """The chain has to hold end to end: binding says who holds the key,
    authorization must speak about that same party."""
    key, _pub = authority
    auth = A.sign_authorization_attestation(_package(), _authorization(), key_path=key)
    ok, why = A.authorization_links(auth, bound_actor="urn:actor/mallory",
                                    project="studyone",
                                    decision_record="urn:uofa:decision:1")
    assert not ok and "bound actor" in why


def test_a_signature_outside_the_grant_interval_is_not_authorized(authority):
    """A grant that EXISTED is not a grant that was IN FORCE. This is the check
    an implementation is most likely to skip."""
    key, _pub = authority
    auth = A.sign_authorization_attestation(_package(), _authorization(), key_path=key)
    common = dict(bound_actor="urn:actor/alice", project="studyone",
                  decision_record="urn:uofa:decision:1")

    ok, why = A.authorization_links(auth, signed_at=50.0, effective_from=100.0, **common)
    assert not ok and "before the grant became effective" in why

    ok, why = A.authorization_links(auth, signed_at=300.0, effective_from=100.0,
                                    effective_until=200.0, **common)
    assert not ok and "after the grant ended" in why

    ok, _why = A.authorization_links(auth, signed_at=150.0, effective_from=100.0,
                                     effective_until=200.0, **common)
    assert ok


def test_an_absent_end_does_not_mean_perpetual(authority):
    """`effectiveUntil` absent means no end was RECORDED, not that the grant is
    still valid. Reading absence as validity infers a present fact from a
    historical one."""
    auth = _authorization()
    assert "effectiveUntil" not in auth


# ── refusals at build time ──────────────────────────────────────────────────

@pytest.mark.parametrize("field", ["bound_actor", "bound_key", "provider_issuer",
                                   "provider_subject", "possession_proven_at",
                                   "deployment_id"])
def test_a_binding_missing_a_meaning_bearing_field_is_refused(field):
    """An attestation with a hole in it is not a weaker attestation; it is a
    different one."""
    with pytest.raises(A.AttestationRefused):
        _binding(**{field: ""})


@pytest.mark.parametrize("field", ["authorized_actor", "project", "decision_record",
                                   "grant_id", "effective_from",
                                   "authorization_checked_at", "decision_signed_at"])
def test_an_authorization_missing_a_meaning_bearing_field_is_refused(field):
    with pytest.raises(A.AttestationRefused):
        _authorization(**{field: ""})


def test_every_payload_states_its_contract_and_context_version():
    """Canonicalization is local and version-stamped: a statement whose meaning
    depended on a document fetched later is not a statement."""
    for block in (_binding(), _authorization()):
        assert block["schemaVersion"] == A.SCHEMA_VERSION
        assert block["contextVersion"] == "v0.10"


def test_the_proof_purpose_distinguishes_enrolment_from_decision_signing():
    assert A.PROOF_PURPOSE_ENROLLMENT == "signing-key-enrollment"
    assert _binding()["proofPurpose"] == A.PROOF_PURPOSE_ENROLLMENT

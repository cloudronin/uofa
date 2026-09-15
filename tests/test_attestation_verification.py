"""What a verifier may conclude from an attestation, and what it may not.

These are the §8.3 red checks from the attestation spec: each one is a shape
where the artifact LOOKS like evidence and establishes nothing. A binding that
verifies perfectly and names somebody else. An authority that vouches only for
itself, riding inside the package it endorses. A grant that existed but was not
in force at the moment the signature was accepted. Every one of them passes a
naive "does the signature check out" test, which is why the states are separate
and why each is asserted on its own here.

The correction this file also pins: uofa used to print "reviewer authorization is
not assessed by uofa" on EVERY verified signature. That was honest while uofa
could not read an authorization claim. Once a trusted authorization verifies and
links, it is no longer true -- it understates the artifact in the same breath the
artifact improved. What remains unassessed is the producer's POLICY, which is a
narrower sentence, and the narrower sentence is what must appear.
"""

from __future__ import annotations

import json

import pytest

from uofa_cli import attestations as A
from uofa_cli import integrity

FP = "sha256:" + "a" * 64
OTHER_FP = "sha256:" + "b" * 64
DECISION = "urn:uofa:decision:1"
ACTOR = "urn:actor/alice"


@pytest.fixture
def authority(tmp_path):
    return integrity.generate_keypair(tmp_path / "authority.key")


@pytest.fixture
def stranger(tmp_path):
    return integrity.generate_keypair(tmp_path / "stranger.key")


def _record():
    return {"id": DECISION, "actor": ACTOR, "outcome": "Conditional"}


def _package():
    return {"@context": "https://uofa.net/ns/v0.9", "id": "urn:uofa:pkg:1",
            "measured": 1, "hasDecisionRecord": _record()}


def _binding(**over):
    args = dict(bound_actor=ACTOR, bound_key=FP,
                provider_issuer="https://huggingface.co",
                provider_subject="hmac:9f2c",
                possession_proven_at="2026-09-14T19:12:03Z",
                deployment_id="preview", issued_at="2026-09-14T19:12:04Z",
                context_version="v0.10")
    args.update(over)
    return A.build_identity_binding(**args)


def _authorization(**over):
    args = dict(authorized_actor=ACTOR, project="studyone",
                decision_record=DECISION, grant_id="grant-7",
                effective_from="2026-09-14T18:00:00Z",
                authorization_checked_at="2026-09-14T19:30:00Z",
                decision_signed_at="2026-09-14T19:30:00Z",
                deployment_id="preview", issued_at="2026-09-14T19:30:01Z",
                context_version="v0.10")
    args.update(over)
    return A.build_authorization_attestation(**args)


def _sealed(authority, *, binding=None, auth=None):
    """A package carrying whichever attestations were asked for, each signed."""
    key, _pub = authority
    pkg = _package()
    if binding is not None:
        pkg[A.IDENTITY_BLOCK_KEY] = A.sign_identity_binding(
            pkg, binding, key_path=key)
    if auth is not None:
        pkg[A.AUTHORIZATION_BLOCK_KEY] = A.sign_authorization_attestation(
            pkg, auth, key_path=key)
    return pkg


def _evaluate(pkg, *, trusted=(), packaged=()):
    return A.evaluate_record(
        pkg, pkg["hasDecisionRecord"], signer_identity=FP, signature_valid=True,
        trusted_keys=list(trusted), packaged_keys=list(packaged))


# ── the baseline that must not regress (IA-06, IA-12) ────────────────────────

def test_a_legacy_package_with_no_attestations_reports_signed_unbound():
    """A package cut before any of this existed is not broken by it. Nothing is
    claimed about the actor-to-key link, and the absence says so plainly rather
    than reading as a failure."""
    r = _evaluate(_package())
    assert r["state"] == A.STATE_SIGNED_UNBOUND
    assert r["identityBinding"] == A.TRUST_ABSENT
    assert r["signature"] == "valid"
    assert A.BINDING_LINES[r["identityBinding"]] == \
        "actor-to-key binding not established."
    assert A.AUTHORIZATION_LINES[r["authorizationAtSigning"]] == \
        "authorization not established."


def test_an_invalid_decision_signature_stops_before_any_attestation_is_read():
    """An attestation about a signature that does not verify is not evidence of
    anything; reading it first would let a good binding dress up a bad
    signature."""
    r = A.evaluate_record(_package(), _record(), signer_identity=FP,
                          signature_valid=False)
    assert r["state"] == A.STATE_SIGNATURE_INVALID


# ── trust is not membership of the package (IA-04, IA-05) ────────────────────

def test_an_authority_key_that_travelled_with_the_package_is_never_trusted(
        authority):
    """The single most important line here. A key riding inside the artifact it
    vouches for proves the file is internally consistent. It says nothing about
    who controls that key, and 'it verified' must not be printed as if it did."""
    _key, pub = authority
    pkg = _sealed(authority, binding=_binding())
    r = _evaluate(pkg, packaged=[pub])
    assert r["identityBinding"] == A.TRUST_UNTRUSTED
    assert r["state"] == A.STATE_AUTHORITY_UNTRUSTED
    assert "not established" in A.BINDING_LINES[r["identityBinding"]]


def test_a_supplied_trust_anchor_produces_a_trusted_binding(authority):
    _key, pub = authority
    pkg = _sealed(authority, binding=_binding())
    r = _evaluate(pkg, trusted=[pub])
    assert r["identityBinding"] == A.TRUST_TRUSTED
    assert r["state"] == A.STATE_AUTHORIZATION_UNASSESSED


def test_a_nonmatching_anchor_does_not_produce_a_trusted_binding(
        authority, stranger):
    _key, pub = stranger
    pkg = _sealed(authority, binding=_binding())
    r = _evaluate(pkg, trusted=[pub])
    assert r["identityBinding"] == A.TRUST_INVALID
    assert r["state"] == A.STATE_SIGNED_UNBOUND


def test_a_present_attestation_with_no_key_at_all_is_unchecked_not_untrusted(
        authority):
    """`valid-but-untrusted` asserts the signature WAS checked. With no key
    supplied it was not, and saying otherwise would claim a verification that
    never ran."""
    pkg = _sealed(authority, binding=_binding())
    r = _evaluate(pkg)
    assert r["identityBinding"] == A.TRUST_UNCHECKED
    assert "was not checked" in A.BINDING_LINES[r["identityBinding"]]


# ── a perfect signature about the wrong party (IA-02, IA-03) ─────────────────

def test_a_binding_naming_another_actor_cannot_satisfy_this_decision(authority):
    _key, pub = authority
    pkg = _sealed(authority, binding=_binding(bound_actor="urn:actor/mallory"))
    r = _evaluate(pkg, trusted=[pub])
    assert r["identityBinding"] == A.TRUST_INVALID, (
        "a cryptographically perfect statement about somebody else was accepted "
        "as evidence about this decision")
    assert "somebody else" in r["bindingReason"]


def test_a_binding_naming_another_key_cannot_satisfy_this_decision(authority):
    _key, pub = authority
    pkg = _sealed(authority, binding=_binding(bound_key=OTHER_FP))
    r = _evaluate(pkg, trusted=[pub])
    assert r["identityBinding"] == A.TRUST_INVALID
    assert "different key" in r["bindingReason"]


# ── authorization (IA-08, IA-09) ─────────────────────────────────────────────

def test_a_trusted_linked_authorization_reaches_the_attested_state(authority):
    _key, pub = authority
    pkg = _sealed(authority, binding=_binding(), auth=_authorization())
    r = _evaluate(pkg, trusted=[pub])
    assert r["state"] == A.STATE_AUTHORIZATION_ATTESTED
    assert r["authorizationAtSigning"] == A.TRUST_TRUSTED


def test_authorization_is_never_read_without_a_trusted_binding(authority):
    """Authorization says a NAMED ACTOR held a permission. With no trusted link
    from that name to the key that signed, the permission attaches to nobody in
    this artifact, so it is not assessed.

    **But not-assessed is not absent, and the two must not print alike.** This
    first shipped reporting `absent` here -- which tells a reader the producer
    shipped no authorization at all, when the producer shipped one this verifier
    declined to read. Observed on a real package carrying both blocks, verified
    with no anchor: `authorization not established`, beside an authorization
    block sitting in the file.
    """
    pkg = _sealed(authority, auth=_authorization())
    _key, pub = authority
    r = _evaluate(pkg, trusted=[pub])
    assert r["state"] == A.STATE_SIGNED_UNBOUND
    assert r["authorizationAtSigning"] == A.TRUST_UNCHECKED, (
        "a present-but-unread authorization was reported as absent")
    assert "attaches to nobody" in r["authorizationReason"]
    assert A.AUTHORIZATION_LINES[r["authorizationAtSigning"]] != \
        A.AUTHORIZATION_LINES[A.TRUST_ABSENT]


def test_a_package_with_no_authorization_block_still_reports_absent():
    """The other half: `absent` must stay reachable, or the fix above would have
    made every package look like it shipped an authorization."""
    r = _evaluate(_package())
    assert r["authorizationAtSigning"] == A.TRUST_ABSENT


def test_authorization_for_another_project_does_not_authorize_this_one(authority):
    _key, pub = authority
    pkg = _sealed(authority, binding=_binding(),
                  auth=_authorization(project="studytwo"))
    # The project comes from the CALLER, not from the attestation. Reading it
    # out of the block would compare the block against itself and agree every
    # time -- the one comparison that can never fail.
    r = A.evaluate_record(pkg, pkg["hasDecisionRecord"], signer_identity=FP,
                          signature_valid=True, project="studyone",
                          trusted_keys=[pub])
    assert r["authorizationAtSigning"] == A.TRUST_INVALID
    assert r["state"] == A.STATE_AUTHORIZATION_UNASSESSED


def test_authorization_for_another_decision_does_not_authorize_this_one(authority):
    _key, pub = authority
    pkg = _sealed(authority, binding=_binding(),
                  auth=_authorization(decision_record="urn:uofa:decision:9"))
    r = _evaluate(pkg, trusted=[pub])
    assert r["authorizationAtSigning"] == A.TRUST_INVALID
    assert "not this" in r["authorizationReason"]


def test_a_signature_made_before_the_grant_began_is_not_authorized(authority):
    _key, pub = authority
    pkg = _sealed(authority, binding=_binding(), auth=_authorization(
        decision_signed_at="2026-09-14T17:00:00Z"))
    r = _evaluate(pkg, trusted=[pub])
    assert r["authorizationAtSigning"] == A.TRUST_INVALID
    assert "before the grant" in r["authorizationReason"]


def test_a_signature_made_after_the_grant_ended_is_not_authorized(authority):
    """A grant that EXISTED is not a grant that was IN FORCE. This is the check
    an implementation is most likely to skip, because the grant row is right
    there and looks like an answer."""
    _key, pub = authority
    pkg = _sealed(authority, binding=_binding(), auth=_authorization(
        effective_until="2026-09-14T19:00:00Z"))
    r = _evaluate(pkg, trusted=[pub])
    assert r["authorizationAtSigning"] == A.TRUST_INVALID
    assert "after the grant ended" in r["authorizationReason"]


def test_an_absent_end_time_does_not_mean_the_grant_is_still_in_force(authority):
    """It means no end was recorded. The attested state covers the signing
    moment only, and current status is reported separately and never inferred."""
    _key, pub = authority
    pkg = _sealed(authority, binding=_binding(), auth=_authorization())
    r = _evaluate(pkg, trusted=[pub])
    assert r["state"] == A.STATE_AUTHORIZATION_ATTESTED
    assert r["currentStatus"] == A.CURRENT_STATUS_NOT_EVALUATED


# ── the wording correction ───────────────────────────────────────────────────

def test_the_blanket_disclaimer_is_gone_from_the_verifier():
    """It was printed on every verified signature, whatever the package carried.
    A sentence that cannot be falsified by any artifact is not a finding."""
    from pathlib import Path
    src = (Path(__file__).resolve().parents[1] / "src" / "uofa_cli" /
           "commands" / "verify.py").read_text()
    body = src[src.index("def _report_record"):]
    # **Code only.** The comment above the replacement QUOTES the old sentence
    # to explain why it went -- a check that read the comment would fail on the
    # explanation of its own fix, and would pass if someone deleted the
    # explanation and kept the line.
    code = "\n".join(l for l in body.splitlines()
                     if not l.lstrip().startswith("#"))
    assert "authorization is not assessed by" not in code, (
        "the unconditional line is back; it now contradicts what uofa can "
        "actually establish from a trusted authorization attestation")


def test_a_trusted_authorization_narrows_the_disclaimer_rather_than_dropping_it():
    """Policy adequacy stays unassessed forever -- uofa verifies that a third
    party made a signed statement and reports whose it is. It does not become
    the judge of whether that party was right."""
    line = A.AUTHORIZATION_LINES[A.TRUST_TRUSTED]
    assert "cryptographically verified" in line
    assert "policy adequacy not assessed" in line


def test_absent_authorization_says_not_established_not_not_assessed():
    assert A.AUTHORIZATION_LINES[A.TRUST_ABSENT] == "authorization not established."


# ── separation (IA-10, IA-11) ────────────────────────────────────────────────

def test_the_five_results_stay_separate_fields(authority):
    """IA-10. A caller must be able to read 'signature valid' without inheriting
    'and the actor was authorized', which is what a single collapsed verdict
    would hand them."""
    _key, pub = authority
    pkg = _sealed(authority, binding=_binding(), auth=_authorization())
    r = _evaluate(pkg, trusted=[pub])
    for field in ("signature", "signingKey", "claimedActor", "identityBinding",
                  "bindingAuthority", "authorizationAtSigning",
                  "authorizationAuthority", "currentStatus", "state"):
        assert field in r, field
    assert json.dumps(r)  # the whole result is machine-readable


def test_current_status_is_never_inferred_from_historical_validity(authority):
    _key, pub = authority
    pkg = _sealed(authority, binding=_binding(), auth=_authorization())
    r = _evaluate(pkg, trusted=[pub])
    assert r["currentStatus"] == A.CURRENT_STATUS_NOT_EVALUATED, (
        "the best possible historical result still says nothing about whether "
        "the key, account or grant is live today")


# ── the two lines that used to contradict each other ─────────────────────────

def test_the_relation_line_defaults_to_exactly_what_it_said_before():
    """Both flags default False, so every package carrying no attestation --
    which is every package that has ever shipped -- reads unchanged."""
    from uofa_cli import sign_roles
    rec = {"decisionProvenance": "asserted", "actor": ACTOR}
    assert sign_roles.describe_relation(rec, sign_roles.INDETERMINATE) == \
        sign_roles.describe_relation(rec, sign_roles.INDETERMINATE,
                                     binding_trusted=False,
                                     authorization_trusted=False)
    assert "NOT ESTABLISHED" in sign_roles.describe_relation(
        rec, sign_roles.INDETERMINATE)


def test_a_trusted_binding_supplies_what_the_relation_line_says_is_missing():
    """Observed on a real package verified with its anchor:

        signer-actor relationship NOT ESTABLISHED -- ... not in a comparable form
        a trusted authority states this actor proved possession of this key

    Two lines, one screen, flatly contradicting each other. The first is
    computed from the package's own strings -- an actor URI and a key
    fingerprint are different kinds of name, so it can only ever say "not
    established". A trusted binding is the thing it reports as missing.
    """
    from uofa_cli import sign_roles
    rec = {"decisionProvenance": "asserted", "actor": ACTOR}
    bound = sign_roles.describe_relation(rec, sign_roles.INDETERMINATE,
                                         binding_trusted=True)
    assert "NOT ESTABLISHED" not in bound
    assert "trusted identity binding" in bound
    # And it must not claim the OTHER kind of evidence: this is an attested
    # link, not two identifiers that matched.
    assert "not by comparing" in bound


def test_a_trusted_authorization_removes_the_stale_qualifier_everywhere():
    """`describe_relation` carried its own copy of "authorization not assessed".
    Fixing only the verifier's line would have left the same false sentence one
    line higher up."""
    from uofa_cli import sign_roles
    rec = {"decisionProvenance": "asserted", "actor": ACTOR}
    for relation in (sign_roles.DECIDER, sign_roles.CONCURRENCE):
        assert "authorization not assessed" in sign_roles.describe_relation(
            rec, relation)
        assert "authorization not assessed" not in sign_roles.describe_relation(
            rec, relation, authorization_trusted=True)


def test_a_bound_decider_is_no_longer_described_as_self_declared():
    """"Self-declared" is the right word for a package vouching for itself. It
    is the wrong word once a third party has vouched for the same fact."""
    from uofa_cli import sign_roles
    rec = {"decisionProvenance": "asserted", "actor": ACTOR}
    line = sign_roles.describe_relation(rec, sign_roles.DECIDER,
                                        binding_trusted=True,
                                        authorization_trusted=True)
    assert "self-declared" not in line
    assert line.count("(") == line.count(")"), f"unbalanced parentheses: {line}"


def test_every_relation_line_has_balanced_parentheses():
    """The qualifier is spliced in; an empty one used to leave a stray `)`."""
    from uofa_cli import sign_roles
    rec = {"decisionProvenance": "asserted", "actor": ACTOR, "role": "R"}
    for relation in (sign_roles.DECIDER, sign_roles.CONCURRENCE,
                     sign_roles.TRANSCRIPTION_ATTESTATION,
                     sign_roles.INDETERMINATE, sign_roles.UNRELATED):
        for b in (False, True):
            for a in (False, True):
                line = sign_roles.describe_relation(
                    rec, relation, binding_trusted=b, authorization_trusted=a)
                assert line.count("(") == line.count(")"), (relation, b, a, line)


# ── an authority key that does not live in this process ──────────────────────

def test_an_external_signer_following_the_description_produces_the_same_bytes(
        authority):
    """The description is only worth shipping if it is exactly right.

    An authority key may sit in a KMS or a customer's own custody, so the signer
    gets bytes and returns a signature rather than handing over a file. The trap
    is that uofa signs the UTF-8 of the 64-char hex STRING, not the 32 raw bytes
    -- a signer that signs the digest produces a signature verifying against
    nothing while looking entirely correct.

    So this does not check the wording. It follows the instruction literally and
    asserts the result is byte-identical to what the in-process signer makes.
    """
    from uofa_cli import integrity
    from uofa_cli.interrogate import signing

    key, pub = authority
    pkg = _package()
    block = {**_binding(),
             A.AUTHORITY_FIELD: signing.fingerprint_from_private_key(key)}

    desc = A.describe_attestation_signing_scope(
        pkg, block, scope_key=A.IDENTITY_SCOPE_KEY)
    external = {**block, desc["signature_field"]:
                "ed25519:" + integrity.sign_hash(desc["digest_hex"], key)}
    in_process = A.sign_identity_binding(pkg, block, key_path=key)

    assert external[desc["signature_field"]] == \
        in_process[A.IDENTITY_SIGNATURE_FIELD], (
        "an external signer following the returned instruction produced "
        "different bytes than the in-process signer; the instruction is wrong")
    pkg[A.IDENTITY_BLOCK_KEY] = external
    assert A.verify_identity_binding(pkg, pub)[0]


def test_the_two_attestation_scopes_produce_different_bytes(authority):
    """Domain separation, checked rather than assumed: a signature made over the
    identity scope must not verify as an authorization, and the only thing
    preventing that is the scope key inside the canonical payload."""
    from uofa_cli.interrogate import signing

    key, _pub = authority
    pkg = _package()
    binding = {**_binding(),
               A.AUTHORITY_FIELD: signing.fingerprint_from_private_key(key)}
    auth = {**_authorization(),
            A.AUTHORITY_FIELD: binding[A.AUTHORITY_FIELD]}

    a = A.describe_attestation_signing_scope(
        pkg, binding, scope_key=A.IDENTITY_SCOPE_KEY)
    b = A.describe_attestation_signing_scope(
        pkg, auth, scope_key=A.AUTHORIZATION_SCOPE_KEY)
    assert a["digest_hex"] != b["digest_hex"]
    assert a["signature_field"] != b["signature_field"]


def test_the_scope_cannot_be_described_before_the_authority_is_stamped(authority):
    """`attestationAuthority` is INSIDE the signed payload. Describing bytes
    without it hands an external signer a different statement than the one the
    package will end up carrying -- it would sign honestly and produce a
    signature that verifies against nothing."""
    pkg = _package()
    block = _binding()          # unsigned, and not yet stamped with an authority
    assert A.AUTHORITY_FIELD not in block
    with pytest.raises(A.AttestationRefused, match="BEFORE its bytes"):
        A.describe_attestation_signing_scope(
            pkg, block, scope_key=A.IDENTITY_SCOPE_KEY)


def test_an_unknown_scope_is_refused_rather_than_silently_signed():
    pkg = _package()
    with pytest.raises(A.AttestationRefused, match="not an attestation scope"):
        A.describe_attestation_signing_scope(pkg, _binding(), scope_key="decision")


# ── the done gate, walked point by point ─────────────────────────────────────

def test_the_done_gate_is_reachable_from_the_artifact_alone(authority):
    """§12 of the attestation spec: what a CLEAN verifier must be able to
    establish with the released package and an independently obtained trusted
    authority key, and NO access to the producer's database or journal.

    Six points, asserted separately, because the gate is that they are separate.
    A tool that collapsed them into one verdict would pass a reader the last
    point's weight on the first point's evidence.
    """
    _key, pub = authority
    pkg = _sealed(authority, binding=_binding(), auth=_authorization())
    r = _evaluate(pkg, trusted=[pub])

    # 1. the decision signature is cryptographically valid
    assert r["signature"] == "valid"
    # 2. the signed decision names actor A
    assert r["claimedActor"] == ACTOR
    # 3. a trusted attestation states A proved possession of key K
    assert r["identityBinding"] == A.TRUST_TRUSTED
    assert r["bindingAuthority"]
    # 4. K is the key that signed the decision
    assert pkg[A.IDENTITY_BLOCK_KEY]["boundKey"] == r["signingKey"] == FP
    # 5. a trusted authorization states A held the permission when accepted
    assert r["authorizationAtSigning"] == A.TRUST_TRUSTED
    assert r["state"] == A.STATE_AUTHORIZATION_ATTESTED
    # 6. and none of it proves identity, understanding, correctness or status
    assert r["currentStatus"] == A.CURRENT_STATUS_NOT_EVALUATED
    joined = " ".join(A.PROHIBITED_CLAIMS).lower()
    for must_disclaim in ("legal name", "human", "understood", "policy",
                          "correct", "valid now", "trusted"):
        assert must_disclaim in joined, must_disclaim


def test_the_disclaimers_are_printed_at_the_strongest_state():
    """The one moment they matter. Below a trusted binding the report already
    says, line by line, what is not established; at the top there is nothing
    left saying no, and 'cryptographically verified' is a true sentence about
    bytes that a reader will happily read as being about a person."""
    from pathlib import Path
    src = (Path(__file__).resolve().parents[1] / "src" / "uofa_cli" /
           "commands" / "verify.py").read_text()
    body = src[src.index("def _report_attestations"):]
    code = "\n".join(l for l in body.splitlines()
                     if not l.lstrip().startswith("#"))
    assert "PROHIBITED_CLAIMS" in code, (
        "the verifier reaches its strongest state and says nothing about what "
        "that state does not mean")


def test_the_prohibited_claims_are_data_not_prose():
    """A producer has to render the same words into its own custody statement.
    Prose in a docstring gets paraphrased; a tuple gets rendered."""
    assert isinstance(A.PROHIBITED_CLAIMS, tuple)
    assert len(A.PROHIBITED_CLAIMS) >= 7
    assert all(isinstance(c, str) and c.strip() for c in A.PROHIBITED_CLAIMS)

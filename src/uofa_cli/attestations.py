"""Third-party statements about WHO signed and under what authority.

A decision signature names a key. The decision record names an actor. Nothing
connected them, so a verifier learned "some key signed this" and "a field claims
an actor" and could not establish they were the same party -- anyone holding that
private key, person or agent, produced a byte-identical artifact. The producing
system witnessed the binding and discarded it at export.

Two sibling blocks close that, each signed in its own scope by an **attestation
authority** -- a party distinct from both the measurement issuer and the reviewer:

  * ``hasIdentityBinding`` -- this authority observed this actor prove possession
    of this key, through this identity provider, at this time.
  * ``hasAuthorizationAttestation`` -- this authority enforced a recorded policy
    and found this actor held this permission when it accepted this signature.

**What uofa does with them, and what it refuses to do.** It verifies the
signature, the linkage and the time relationships, and reports whose claim it is.
It does NOT adjudicate whether the authority was right, whether the policy was
adequate, or who the actor is in the world. That is the standing ruling in
``sign_roles`` -- *"who was permitted to sign is not a question uofa answers"* --
and these objects do not weaken it. They make a producer's claim CHECKABLE and
ATTRIBUTABLE; they do not make uofa the judge of it.

**Trust is not membership of the package.** An authority key travelling inside
the zip proves internal consistency and nothing about who controls it. The four
states below keep that distinction visible rather than collapsing it into
"valid".

**Canonicalization is local and version-stamped.** The signed payload carries
``contextVersion`` and ``schemaVersion``, and NOTHING here resolves a context over
the network -- at signing or at verification. An attestation whose meaning depended
on a document fetched later is not an attestation.
"""

from __future__ import annotations

from pathlib import Path

# ── The two blocks ───────────────────────────────────────────────────────────
#
# Both keys MUST also appear in `interrogate.forbidden.ACTION_REGION_KEYS`, or
# they land inside the issuer seal -- which would break the seal every time an
# attestation arrived and make it impossible for one to arrive after sealing.

IDENTITY_BLOCK_KEY = "hasIdentityBinding"
IDENTITY_SCOPE_KEY = "identity"
IDENTITY_SIGNATURE_FIELD = "bindingSignature"

AUTHORIZATION_BLOCK_KEY = "hasAuthorizationAttestation"
AUTHORIZATION_SCOPE_KEY = "authorization"
AUTHORIZATION_SIGNATURE_FIELD = "authorizationSignature"

#: The field naming the key that made the statement, checked against whatever
#: anchor the verifier supplied. Same role `attributedTo` plays for a guardrail
#: action and `decidedBy` for a decision.
AUTHORITY_FIELD = "attestationAuthority"

#: Closed value distinguishing enrollment proof from decision signing. The
#: producer's challenge is domain-separated; this records which purpose the
#: proof served so a signature over one can never be read as the other.
PROOF_PURPOSE_ENROLLMENT = "signing-key-enrollment"

#: The only action an authorization attestation currently speaks about.
ACTION_SIGN_DECISION = "sign-decision"

#: Contract version for both payload shapes and their canonicalization. Bumped
#: when the SIGNED bytes change meaning, never for an additive report field.
SCHEMA_VERSION = "attestation/v1"


# ── Trust states ─────────────────────────────────────────────────────────────
#
# Four, kept apart on purpose. "The signature verifies" and "I know who holds
# that key" are different questions, and a reader who cannot tell them apart has
# been told something false by omission.

TRUST_TRUSTED = "trusted-valid"
TRUST_UNTRUSTED = "valid-untrusted-authority"
TRUST_INVALID = "invalid"
TRUST_ABSENT = "absent"


#: What these attestations do NOT establish, at their very best -- a trusted
#: binding AND a trusted authorization, both verified and linked.
#:
#: **A tuple rather than prose, so a producer renders it instead of retyping
#: it.** The custody statement a package ships and the docs that describe it
#: have to say the same thing as the verifier, and the way two documents drift
#: is that somebody paraphrases one of them. Credenza writes these lines into
#: `SIGNING.txt` verbatim.
#:
#: Every entry is a claim a reader might otherwise infer from "cryptographically
#: verified", which is the phrase that does the damage: it is true, and it is
#: about bytes.
PROHIBITED_CLAIMS: tuple[str, ...] = (
    "This does not establish a legal name, a licensed professional, or any "
    "real-world identity. It establishes that an authority stated an actor "
    "identifier proved possession of a key.",
    "This does not establish that a human signed rather than an agent "
    "operating an authenticated account.",
    "This does not establish that the signer read or understood the evidence.",
    "This does not establish that the producer's authorization policy was "
    "adequate, only that the producer enforced the policy it recorded.",
    "This does not establish that the decision was correct.",
    "This does not establish that any key, account or grant is valid NOW. "
    "Every statement here is about the moment it was made; current status is "
    "separate evidence.",
    "This does not establish that an authority key shipped inside the package "
    "is trusted. Trust comes from an anchor the verifier obtains out of band.",
)


class AttestationRefused(Exception):
    """A statement this library will not make or accept."""


def _authority_fingerprint(key_path=None, key_bytes=None) -> str:
    from uofa_cli.interrogate import signing

    if key_bytes is not None:
        return signing.fingerprint_from_private_key(key_bytes=key_bytes)
    return signing.fingerprint_from_private_key(Path(key_path))


def _require_fields(block: dict, required: tuple[str, ...], what: str) -> None:
    missing = [f for f in required if not str(block.get(f, "")).strip()]
    if missing:
        raise AttestationRefused(
            f"an {what} must state {', '.join(missing)}. A field that affects "
            f"what the statement MEANS cannot be absent from the bytes that are "
            f"signed; an attestation with a hole in it is not a weaker "
            f"attestation, it is a different one.")


# ── Identity binding ─────────────────────────────────────────────────────────

IDENTITY_REQUIRED = (
    "boundActor", "boundKey", "identityProviderIssuer",
    "identityProviderSubject", "possessionProvenAt", "proofPurpose",
    "deploymentId", "issuedAt", "contextVersion", "schemaVersion",
)


def build_identity_binding(
    *, bound_actor: str, bound_key: str, provider_issuer: str,
    provider_subject: str, possession_proven_at: str, deployment_id: str,
    issued_at: str, context_version: str, authenticated_at: str = "",
    proof_purpose: str = PROOF_PURPOSE_ENROLLMENT,
) -> dict:
    """The unsigned binding block.

    `bound_actor` is the actor identifier AS IT APPEARS in the decision record --
    matching is by exact string, so a producer that exports one spelling and
    binds another has made a statement about nobody.

    `bound_key` is the `sha256:<hex over DER SubjectPublicKeyInfo>` fingerprint,
    the same form `DecisionSignature.signerIdentity` carries.
    """
    block = {
        "type": "IdentityBindingAttestation",
        "boundActor": bound_actor,
        "boundKey": bound_key,
        "identityProviderIssuer": provider_issuer,
        "identityProviderSubject": provider_subject,
        "possessionProvenAt": possession_proven_at,
        "proofPurpose": proof_purpose,
        "deploymentId": deployment_id,
        "issuedAt": issued_at,
        "contextVersion": context_version,
        "schemaVersion": SCHEMA_VERSION,
    }
    if authenticated_at:
        block["authenticatedAt"] = authenticated_at
    _require_fields(block, IDENTITY_REQUIRED, "identity binding")
    return block


def sign_identity_binding(package: dict, block: dict, *,
                          key_path=None, key_bytes: bytes = None) -> dict:
    """Sign a binding into the `identity` scope, stamped with the authority."""
    from uofa_cli.interrogate import signing

    _require_fields(block, IDENTITY_REQUIRED, "identity binding")
    stamped = {**block, AUTHORITY_FIELD: _authority_fingerprint(key_path, key_bytes)}
    return signing.sign_scoped_block(
        package, key_path, stamped, key_bytes=key_bytes,
        scope_key=IDENTITY_SCOPE_KEY, signature_field=IDENTITY_SIGNATURE_FIELD)


def verify_identity_binding(package: dict, pubkey_path, *,
                            block: dict | None = None) -> tuple[bool, str]:
    """Verify a binding's signature over its own scope. Returns (ok, reason)."""
    from uofa_cli.interrogate import signing

    return signing.verify_scoped_block(
        package, pubkey_path, block=block,
        block_key=IDENTITY_BLOCK_KEY, scope_key=IDENTITY_SCOPE_KEY,
        signature_field=IDENTITY_SIGNATURE_FIELD,
        attributed_by_field=AUTHORITY_FIELD)


# ── Authorization at signing ─────────────────────────────────────────────────

AUTHORIZATION_REQUIRED = (
    "authorizedActor", "project", "decisionRecord", "authorizedAction",
    "grantId", "effectiveFrom", "authorizationCheckedAt", "decisionSignedAt",
    "deploymentId", "issuedAt", "contextVersion", "schemaVersion",
)


def build_authorization_attestation(
    *, authorized_actor: str, project: str, decision_record: str,
    grant_id: str, effective_from: str, authorization_checked_at: str,
    decision_signed_at: str, deployment_id: str, issued_at: str,
    context_version: str, grant_version: str = "", granted_by: str = "",
    effective_until: str = "", authorized_action: str = ACTION_SIGN_DECISION,
) -> dict:
    """The unsigned authorization block.

    **`effective_until` absent does not mean perpetual.** It means no end was
    recorded at the time of the statement. A verifier that read absence as
    "still valid" would be inferring a present fact from a historical one, which
    is the thing current-status evidence exists to answer separately.
    """
    block = {
        "type": "AuthorizationAttestation",
        "authorizedActor": authorized_actor,
        "project": project,
        "decisionRecord": decision_record,
        "authorizedAction": authorized_action,
        "grantId": grant_id,
        "effectiveFrom": effective_from,
        "authorizationCheckedAt": authorization_checked_at,
        "decisionSignedAt": decision_signed_at,
        "deploymentId": deployment_id,
        "issuedAt": issued_at,
        "contextVersion": context_version,
        "schemaVersion": SCHEMA_VERSION,
    }
    for name, value in (("grantVersion", grant_version),
                        ("grantedBy", granted_by),
                        ("effectiveUntil", effective_until)):
        if value:
            block[name] = value
    _require_fields(block, AUTHORIZATION_REQUIRED, "authorization attestation")
    return block


def sign_authorization_attestation(package: dict, block: dict, *,
                                   key_path=None, key_bytes: bytes = None) -> dict:
    from uofa_cli.interrogate import signing

    _require_fields(block, AUTHORIZATION_REQUIRED, "authorization attestation")
    stamped = {**block, AUTHORITY_FIELD: _authority_fingerprint(key_path, key_bytes)}
    return signing.sign_scoped_block(
        package, key_path, stamped, key_bytes=key_bytes,
        scope_key=AUTHORIZATION_SCOPE_KEY,
        signature_field=AUTHORIZATION_SIGNATURE_FIELD)


def verify_authorization_attestation(package: dict, pubkey_path, *,
                                     block: dict | None = None) -> tuple[bool, str]:
    from uofa_cli.interrogate import signing

    return signing.verify_scoped_block(
        package, pubkey_path, block=block,
        block_key=AUTHORIZATION_BLOCK_KEY, scope_key=AUTHORIZATION_SCOPE_KEY,
        signature_field=AUTHORIZATION_SIGNATURE_FIELD,
        attributed_by_field=AUTHORITY_FIELD)


# ── Linkage ──────────────────────────────────────────────────────────────────


def binding_links(binding: dict, *, decision_actor: str, signer_identity: str) -> tuple[bool, str]:
    """Does this binding actually speak about THIS decision's actor and key?

    A binding that verifies cryptographically and names somebody else is the
    most dangerous shape available here: it looks like evidence and attests
    nothing about the artifact it travels in. Both comparisons are exact.
    """
    if binding.get("boundActor") != decision_actor:
        return False, (
            f"the binding names actor {binding.get('boundActor')!r} and this "
            f"decision names {decision_actor!r}; it is a statement about "
            f"somebody else")
    if binding.get("boundKey") != signer_identity:
        return False, (
            f"the binding names key {binding.get('boundKey')!r} and this "
            f"decision was signed by {signer_identity!r}; it is a statement "
            f"about a different key")
    return True, "ok"


def authorization_links(auth: dict, *, bound_actor: str, project: str,
                        decision_record: str, signed_at: float | None = None,
                        effective_from: float | None = None,
                        effective_until: float | None = None) -> tuple[bool, str]:
    """Does this authorization speak about this actor, project, decision and time?

    The time test is the one that matters and the one an implementation is most
    likely to skip: a grant that existed is not a grant that was in force when
    the signature was accepted.
    """
    if auth.get("authorizedActor") != bound_actor:
        return False, (
            f"the authorization names {auth.get('authorizedActor')!r}, not the "
            f"bound actor {bound_actor!r}")
    if auth.get("project") != project:
        return False, (
            f"the authorization is for project {auth.get('project')!r}, not "
            f"{project!r}")
    if auth.get("decisionRecord") != decision_record:
        return False, (
            f"the authorization covers {auth.get('decisionRecord')!r}, not this "
            f"decision")
    if signed_at is not None and effective_from is not None:
        if signed_at < effective_from:
            return False, (
                "the decision was signed before the grant became effective")
        if effective_until is not None and effective_until > 0 and signed_at >= effective_until:
            return False, (
                "the decision was signed after the grant ended; a grant that "
                "existed is not a grant that was in force")
    return True, "ok"


# ── Human-readable states ────────────────────────────────────────────────────
#
# Five, and the ordering matters: each one names what the PREVIOUS one could not
# establish. A reader who is handed only the last word ("attested") learns
# nothing about which of the four earlier questions were actually answered.

STATE_SIGNATURE_INVALID = "signature-invalid"
STATE_SIGNED_UNBOUND = "signed-unbound"
STATE_AUTHORITY_UNTRUSTED = "bound-authority-untrusted"
STATE_AUTHORIZATION_UNASSESSED = "identity-bound-authorization-unassessed"
STATE_AUTHORIZATION_ATTESTED = "identity-bound-authorization-attested"

#: A block is present and no key was supplied that could speak to it. Distinct
#: from `TRUST_UNTRUSTED`, which says the signature WAS checked and the holder of
#: the key is unknown. Reporting an unchecked signature as "valid but untrusted"
#: would assert a verification that never ran -- the exact false-by-omission the
#: four states exist to prevent.
TRUST_UNCHECKED = "present-unchecked"

#: Current key, account and grant status are a different question from historical
#: validity, answered by separate and separately-signed evidence. Never inferred
#: here, and never left implied.
CURRENT_STATUS_NOT_EVALUATED = "not-evaluated"


def _instant(value) -> float | None:
    """ISO-8601 to epoch seconds, or None when it is not a time."""
    from datetime import datetime

    text = str(value or "").strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def _check_block(package, block, *, verifier, trusted_keys, packaged_keys):
    """(trust_state, authority, reason) for one attestation block.

    `trusted_keys` came from the verifier out of band; `packaged_keys` travelled
    with the artifact. Keeping the two lists apart is the whole point: a key that
    rode in beside the thing it vouches for establishes internal consistency and
    nothing about who controls it.
    """
    if not isinstance(block, dict) or not block:
        return TRUST_ABSENT, "", "no attestation is present"
    authority = str(block.get(AUTHORITY_FIELD, "") or "")
    for key in trusted_keys:
        ok, why = verifier(package, key, block=block)
        if ok:
            return TRUST_TRUSTED, authority, "verified against a supplied trust anchor"
    reasons = []
    for key in packaged_keys:
        ok, why = verifier(package, key, block=block)
        if ok:
            return TRUST_UNTRUSTED, authority, (
                "the signature verifies against a key that travelled inside the "
                "package; no supplied anchor establishes who controls it")
        reasons.append(why)
    if not trusted_keys and not packaged_keys:
        return TRUST_UNCHECKED, authority, (
            "no authority key was supplied, so the signature was not checked")
    return TRUST_INVALID, authority, (
        reasons[0] if reasons else "no supplied key verified this attestation")


def evaluate_record(package: dict, record: dict, *, signer_identity: str,
                    signature_valid: bool, project: str = "",
                    trusted_keys=(), packaged_keys=()) -> dict:
    """The separated result for one decision record.

    Every field is reported independently, because they answer independent
    questions and a reader who cannot tell them apart has been told something
    false by omission. In particular a trusted, well-linked authorization says
    the producer's policy was ENFORCED, never that it was ADEQUATE.
    """
    actor = str(record.get("actor") or record.get("decidedBy") or "")
    out = {
        "decisionRecord": str(record.get("id") or ""),
        "signature": "valid" if signature_valid else "invalid",
        "signingKey": signer_identity,
        "claimedActor": actor,
        "identityBinding": TRUST_ABSENT,
        "bindingAuthority": "",
        "bindingReason": "",
        "authorizationAtSigning": TRUST_ABSENT,
        "authorizationAuthority": "",
        "authorizationReason": "",
        "currentStatus": CURRENT_STATUS_NOT_EVALUATED,
        "state": STATE_SIGNATURE_INVALID,
    }
    if not signature_valid:
        return out

    binding = package.get(IDENTITY_BLOCK_KEY)
    state, authority, reason = _check_block(
        package, binding, verifier=verify_identity_binding,
        trusted_keys=trusted_keys, packaged_keys=packaged_keys)
    # A cryptographically perfect statement about somebody else is the most
    # dangerous shape here: it looks like evidence and attests nothing about the
    # artifact it travels in. Linkage is checked BEFORE trust is reported.
    if state in (TRUST_TRUSTED, TRUST_UNTRUSTED):
        linked, why = binding_links(
            binding, decision_actor=actor, signer_identity=signer_identity)
        if not linked:
            state, reason = TRUST_INVALID, why
    out.update(identityBinding=state, bindingAuthority=authority,
               bindingReason=reason)

    if state != TRUST_TRUSTED:
        out["state"] = (STATE_AUTHORITY_UNTRUSTED if state == TRUST_UNTRUSTED
                        else STATE_SIGNED_UNBOUND)
        # **Stopping here must not read as "there was nothing here."** An
        # authorization says a NAMED ACTOR held a permission; with no trusted
        # link from that name to the key that signed, it attaches to nobody, so
        # it is not assessed. But the block is IN THE FILE, and printing
        # "authorization not established" -- the absent wording -- would tell a
        # reader the producer shipped nothing when the producer shipped
        # something this verifier declined to read.
        if isinstance(package.get(AUTHORIZATION_BLOCK_KEY), dict):
            out.update(
                authorizationAtSigning=TRUST_UNCHECKED,
                authorizationAuthority=str(
                    package[AUTHORIZATION_BLOCK_KEY].get(AUTHORITY_FIELD, "") or ""),
                authorizationReason=(
                    "not assessed: no trusted binding connects the named actor "
                    "to the key that signed, so a permission held by that name "
                    "attaches to nobody in this artifact"))
        return out

    out["state"] = STATE_AUTHORIZATION_UNASSESSED
    auth = package.get(AUTHORIZATION_BLOCK_KEY)
    a_state, a_authority, a_reason = _check_block(
        package, auth, verifier=verify_authorization_attestation,
        trusted_keys=trusted_keys, packaged_keys=packaged_keys)
    if a_state in (TRUST_TRUSTED, TRUST_UNTRUSTED):
        linked, why = authorization_links(
            auth, bound_actor=binding.get("boundActor", ""),
            project=project or str(auth.get("project", "")),
            decision_record=str(record.get("id") or ""),
            signed_at=_instant(auth.get("decisionSignedAt")),
            effective_from=_instant(auth.get("effectiveFrom")),
            effective_until=_instant(auth.get("effectiveUntil")))
        if not linked:
            a_state, a_reason = TRUST_INVALID, why
    out.update(authorizationAtSigning=a_state, authorizationAuthority=a_authority,
               authorizationReason=a_reason)
    if a_state == TRUST_TRUSTED:
        out["state"] = STATE_AUTHORIZATION_ATTESTED
    return out


#: What `verify` prints for each authorization trust state. Correction to the
#: previous blanket line: once a TRUSTED authorization verifies and links, "uofa
#: does not assess authorization" is no longer true and must not be printed.
#: What remains unassessed is the POLICY, which is a different sentence.
AUTHORIZATION_LINES = {
    TRUST_TRUSTED: ("authorization assertion cryptographically verified; "
                    "policy adequacy not assessed."),
    TRUST_UNTRUSTED: ("an authorization assertion verifies against a key that "
                      "travelled with the package; who controls that key is not "
                      "established, so authorization is not established."),
    TRUST_INVALID: ("an authorization assertion is present and does not hold; "
                    "authorization is not established."),
    # Deliberately does NOT say why. There are two whys -- no authority key was
    # supplied, or no trusted binding made the assertion readable -- and the
    # reason line carries whichever applies. A fixed why would be wrong half
    # the time.
    TRUST_UNCHECKED: "an authorization assertion is present and was not assessed.",
    TRUST_ABSENT: "authorization not established.",
}

BINDING_LINES = {
    TRUST_TRUSTED: ("a trusted authority states this actor proved possession of "
                    "this signing key."),
    TRUST_UNTRUSTED: ("an identity binding verifies against a key that travelled "
                      "with the package; who controls that key is not "
                      "established, so the actor-to-key binding is not "
                      "established."),
    TRUST_INVALID: ("an identity binding is present and does not hold; the "
                    "actor-to-key binding is not established."),
    TRUST_UNCHECKED: ("an identity binding is present and was not checked: no "
                      "authority key was supplied."),
    TRUST_ABSENT: "actor-to-key binding not established.",
}


# ── Signing from outside this process ────────────────────────────────────────


def describe_attestation_signing_scope(package: dict, block: dict, *,
                                       scope_key: str) -> dict:
    """The exact bytes an attestation signature must cover.

    The sibling of ``sign_roles.describe_decision_signing_scope``, and it exists
    for the same reason that one does: an authority key does not have to live in
    this process. The spec contemplates a KMS-backed or customer-controlled
    attestation authority, and such a signer has the bytes and a signature over
    them with no way to hand either to a path-based API.

    **The instruction is the part outside signers get wrong**, so it travels in
    the payload rather than in documentation somebody has to go and read: sign
    the UTF-8 bytes of the 64-character lowercase hex STRING, not the 32 raw
    digest bytes. ``integrity.sign_hash`` has documented that as intentional and
    non-standard since it was written, and a signer that signs the digest
    produces a signature verifying against nothing while looking entirely
    correct.

    `scope_key` is `IDENTITY_SCOPE_KEY` or `AUTHORIZATION_SCOPE_KEY`. Passing the
    wrong one yields bytes for the wrong scope, which is the domain separation
    working: a signature made in one scope must not verify in the other.
    """
    from uofa_cli.interrogate import signing

    if scope_key not in (IDENTITY_SCOPE_KEY, AUTHORIZATION_SCOPE_KEY):
        raise AttestationRefused(
            f"{scope_key!r} is not an attestation scope. The two are "
            f"{IDENTITY_SCOPE_KEY!r} and {AUTHORIZATION_SCOPE_KEY!r}, and they "
            f"are separate so a statement made in one can never be read as a "
            f"statement made in the other.")
    required = (IDENTITY_REQUIRED if scope_key == IDENTITY_SCOPE_KEY
                else AUTHORIZATION_REQUIRED)
    what = ("identity binding" if scope_key == IDENTITY_SCOPE_KEY
            else "authorization attestation")
    _require_fields(block, required, what)
    if block.get(AUTHORITY_FIELD) is None:
        raise AttestationRefused(
            f"an {what} must carry {AUTHORITY_FIELD} BEFORE its bytes are "
            f"described. The authority is inside the signed payload, so bytes "
            f"described without it are not the bytes that will be verified -- "
            f"the external signer would sign a different statement than the one "
            f"the package ends up carrying.")
    signature_field = (IDENTITY_SIGNATURE_FIELD
                       if scope_key == IDENTITY_SCOPE_KEY
                       else AUTHORIZATION_SIGNATURE_FIELD)
    unsigned = {k: v for k, v in block.items() if k != signature_field}
    scope = {"measurementHash": signing.measurement_hash(package),
             scope_key: unsigned}
    from uofa_cli.integrity import canonicalize_and_hash

    canonical, digest = canonicalize_and_hash(scope)
    return {
        "scope_key": scope_key,
        "signature_field": signature_field,
        "canonicalization": "json-sortkeys/v1",
        "canonical_bytes": canonical,
        "digest_hex": digest,
        "signature_algorithm": "ed25519",
        "schema_version": SCHEMA_VERSION,
        "sign_these_bytes": (
            "the UTF-8 bytes of `digest_hex` -- the 64 lowercase hex characters "
            "themselves, NOT the 32 raw bytes they encode. See "
            "uofa_cli.integrity.sign_hash."),
    }

"""Roles for the unified signing surface — two, because two kinds of mind.

The role axis IS the machine/human boundary: the same single axis every layer
enforces — the escalation table at act, dual attribution at record, provenance
tokens at claim, roles at seal.

- ``issuer`` — infrastructure key, seals the measurement view. Custody,
  integrity, well-formedness: what a machine can know.
- ``reviewer`` — person-class key, signs the decision layer. A named person
  stands behind a judgment.

**Why not four.** `deciding-engineer`, `concurring-reviewer` and
`encoder-of-record` were declarations of facts the artifact already carries: all
three are derivable by matching the signer against the decision records and
their provenance fork. A declaration that can only agree with the record or lie
is the two-sources-of-truth disease, and this one had a live misdeclaration
channel — sign your own verdict as `encoder-of-record` and ownership is softened
in the permanent record, uncatchably, because the flag WAS the truth-source.
Collapsing the vocabulary closes that channel by construction.

The relation is derived at verify and stored nowhere: signer matching an
`asserted` record's actor is a decider; a reviewer signature over extracted-only
records is a transcription attestation; a second party signing their own stacked
record is concurrence. The words survive in output, never in the artifact.

One signature may never span both scopes: an issuer seal covering a judgment
would be infrastructure vouching for a human commitment.
"""

from __future__ import annotations

import re
from pathlib import Path

ISSUER = "issuer"
REVIEWER = "reviewer"

#: Closed, and closed at the boundary's width. A future role proposal must argue
#: against the machine/human boundary itself, not request a flag; a relation that
#: genuinely is not derivable extends the model by a RECORD TYPE, never a role.
ROLES: tuple[str, ...] = (ISSUER, REVIEWER)

#: The person-class role. Everything here signs a judgment or an attestation
#: about one, and needs a person-class key.
DECISION_ROLES: frozenset = frozenset({REVIEWER})


class RoleError(ValueError):
    """A refusal about roles, keys, or the order signatures must happen in."""


def parse_roles(spec: str | None) -> tuple[str, ...]:
    """`--as issuer,deciding-engineer` -> the roles, or a refusal naming the set."""
    if not spec or not spec.strip():
        return ()
    out = []
    for raw in spec.split(","):
        role = raw.strip()
        if not role:
            continue
        if role not in ROLES:
            raise RoleError(
                f"unknown signing role {role!r}. The closed set is: "
                f"{', '.join(ROLES)}.")
        if role not in out:
            out.append(role)
    return tuple(out)


def decision_records(doc: dict) -> list[dict]:
    """Every decision record, however many. `hasDecisionRecord` is repeatable:
    a package may carry the source's acceptance, an independent concurrence and
    a program approval, and each is its own claim by its own actor."""
    from uofa_cli.package_policy import DECISION_BLOCK_KEY

    block = (doc or {}).get(DECISION_BLOCK_KEY)
    if block is None:
        return []
    if isinstance(block, list):
        return [b for b in block if isinstance(b, dict)]
    return [block] if isinstance(block, dict) else []


def has_decision_layer(doc: dict) -> bool:
    """Whether this package has a decision layer at all, in ANY representation.

    `decision_records()` returns the readable RECORDS -- dicts it can inspect.
    A package may instead reference its decision by IRI, and then the records
    list is empty while the layer plainly exists. The concept guard already read
    it that way, so the two disagreed: the guard refused a bare signature over
    such a package, while the scope routing called it decision-free.

    That disagreement is not cosmetic. Sealing took the measurement-view scope
    and verifying took the whole-document scope, so the package sealed cleanly
    and then failed its own verification -- the two-scope split, applied by two
    functions that did not agree on which packages had two scopes.
    """
    return DECISION_BLOCK_KEY_PRESENT(doc)


def DECISION_BLOCK_KEY_PRESENT(doc: dict) -> bool:
    from uofa_cli.package_policy import DECISION_BLOCK_KEY

    value = (doc or {}).get(DECISION_BLOCK_KEY)
    if value is None:
        return False
    if isinstance(value, (list, tuple)):
        return len(value) > 0
    return bool(value)


def unsigned_asserted(doc: dict) -> list[dict]:
    """Asserted records carrying no signature.

    `asserted` means the record's actor participates in this package's
    production — a live party who can sign, and must. `extracted` records are
    absent here on purpose: their actor is the source's, the source never signs,
    and their warrant is the anchor.
    """
    return [r for r in decision_records(doc)
            if str(r.get("decisionProvenance", "")).strip() == ASSERTED
            and not r.get("hasDecisionSignature")]


ASSERTED = "asserted"
EXTRACTED = "extracted"
FORKS = (ASSERTED, EXTRACTED)

#: The context version that introduced `decisionProvenance`. A package whose
#: own `@context` predates this CANNOT state a fork -- the term is not in its
#: vocabulary -- so reporting it as unclassifiable describes the checker's
#: expectation rather than the package's condition.
#:
#: Reported live on `packs/vv40/examples/morrison/cou1/`, which declares v0.5
#: and drew "provenance '<absent>' -- this record cannot be checked at all"
#: beside two passing signatures. The same shape `protocol_check` already
#: fixed for the run-log pins: refusing a package for lacking a field that did
#: not exist when it was written punishes age rather than negligence.
PROVENANCE_INTRODUCED = (0, 9)


def context_version(doc: dict) -> tuple[int, ...]:
    """The version the PACKAGE declares, from its own `@context`.

    An inlined context -- a resolved or signed document -- declares no version
    and returns (), which sorts below everything and takes the advisory path
    rather than being guessed at.
    """
    ref = doc.get("@context")
    if not isinstance(ref, str):
        return ()
    tail = ref.rsplit("/", 1)[-1]
    return tuple(int(x) for x in tail.lstrip("vV").removesuffix(".jsonld").split(".")
                 if x.isdigit())


def predates_provenance(doc: dict) -> bool:
    """Can this package state a fork at all?

    False for a document that declares no context version: silence is not a
    claim of age, and an inlined context is usually a SIGNED package, which had
    the term available when it was made.
    """
    v = context_version(doc)
    return bool(v) and v < PROVENANCE_INTRODUCED


def unclassified_records(doc: dict) -> list[dict]:
    """Records whose fork is absent or unrecognised.

    The totality backstop, and it closes a live hole rather than a theoretical
    one. `unsigned_asserted` compared against the string "asserted", so a record
    that DECLARED its fork was caught and a record that declared nothing was
    exempt -- omission was the way past the boundary, and the excel path emitted
    forkless records by default. A gate correct on the declared case and silent
    on the undeclared one is the same defect as a guard that knew one spelling.

    A signature does not rescue an unclassified record: the fork is what says
    which warrant is owed, so without it there is no way to know whether that
    signature was the right warrant or whether an anchor was owed instead.
    """
    out = []
    for rec in decision_records(doc):
        fork = str(rec.get("decisionProvenance", "")).strip()
        if fork not in FORKS:
            out.append(rec)
    return out


def key_class(key_path: Path) -> str | None:
    """Which anchor this private key matches: 'issuer', 'reviewer', or None.

    Derived from the key itself, never from what the caller says it is. The two
    demo keys are structurally separated so the wrong-key refusal is provable in
    both directions rather than being a naming convention.
    """
    from uofa_cli import paths
    from uofa_cli.interrogate.signing import (
        fingerprint_from_private_key, fingerprint_from_public_key,
    )
    try:
        fp = fingerprint_from_private_key(Path(key_path))
    except Exception:                                   # noqa: BLE001
        return None
    for name, anchor in (("issuer", paths.issuer_pubkey()),
                         ("reviewer", paths.reviewer_pubkey())):
        try:
            if anchor.exists() and fingerprint_from_public_key(anchor) == fp:
                return name
        except Exception:                               # noqa: BLE001
            continue
    return None


def assert_key_matches_roles(key_path: Path, roles: tuple[str, ...]) -> None:
    """Refuse a key used outside its class — in both directions.

    An unrecognised key is permitted: a customer deployment signs with its own
    key and this tool holds no registry of them. What is refused is a key we CAN
    identify being used for the scope it is not for, because that is the
    two-scopes-one-key confusion arriving through the back door.
    """
    klass = key_class(key_path)
    if klass is None:
        return
    wants_decision = bool(set(roles) & DECISION_ROLES)
    if klass == "issuer" and wants_decision:
        raise RoleError(
            "this is the ISSUER key and the requested role signs a judgment. An "
            "issuer key attests provenance, never a human judgment (AGENTS.md "
            "section 12). Sign decision roles with the reviewer's own key.")
    if klass == "reviewer" and ISSUER in roles:
        raise RoleError(
            "this is the REVIEWER key and `--as issuer` seals the package. The "
            "seal is the producing infrastructure's claim; a person's key must "
            "not make it.")


# ── which records a role signs ──────────────────────────────────────────────

def records_for_role(doc: dict, role: str) -> list[dict]:
    """The decision records a reviewer signature attaches to.

    Every record not already carrying one. The RELATION -- decider,
    transcription attestation, concurrence -- is not chosen here and is not
    stored: it is read back at verify from the signer's identity against each
    record's actor and fork. Morrison and Johnson are the same command; the
    difference lives in the records, where it always did.
    """
    if role != REVIEWER:
        return []
    return [r for r in decision_records(doc) if not r.get("hasDecisionSignature")]


def sign_decision_records(doc: dict, key_path: Path, role: str,
                          *, now: str, key_bytes: bytes = None) -> int:
    """Attach a `hasDecisionSignature` to every record this role signs.

    The signature binds `{measurementHash (RECOMPUTED), decision}` -- the A6
    scope -- so altering any measurement breaks it, and a signature scoped to
    the decision alone fails too. That embedded hash is what chains the judgment
    to the evidence it judged.
    """
    from uofa_cli.integrity import sign_hash
    from uofa_cli.interrogate.signing import (
        _scoped_block_hash, fingerprint_from_private_key, measurement_hash,
    )

    targets = records_for_role(doc, role)
    if not targets:
        raise RoleError(
            f"`--as {role}` has nothing to sign: every decision record in this "
            f"package already carries a signature, or there are none. A "
            f"signature with no act under it is a claim about nothing.")

    mh = measurement_hash(doc)
    signer = (fingerprint_from_private_key(key_bytes=key_bytes) if key_bytes
              else fingerprint_from_private_key(Path(key_path)))
    for rec in targets:
        block = {k: v for k, v in rec.items() if k != "hasDecisionSignature"}
        scope_hash = _scoped_block_hash(doc, "decision", block)
        rec["hasDecisionSignature"] = {
            "type": "DecisionSignature",
            # One axis, never two fields that could disagree about which kind
            # signed. `signerKind` retired into this: the role IS the kind.
            "signatureRole": role,
            "signerIdentity": signer,
            "measurementHash": mh,
            "signatureAlgorithm": "ed25519",
            "signatureValue": "ed25519:" + (
                sign_hash(scope_hash, key_bytes=key_bytes) if key_bytes
                else sign_hash(scope_hash, Path(key_path))),
            "signedAt": now,
        }
    return len(targets)


def _is_real_seal(doc: dict) -> bool:
    """Whether the integrity fields hold a seal or a placeholder.

    `uofa import` writes zero-filled `hash` and `signature` fields so the shape
    is complete before signing. A presence check therefore answers "are these
    fields here?" when the question asked was "has this been sealed?" -- and the
    all-zeros package passed. Presence is not existence when the absent value has
    a spelling.
    """
    for field in ("hash", "signature"):
        raw = str(doc.get(field) or "").strip()
        if not raw:
            return False
        value = raw.split(":", 1)[1] if ":" in raw else raw
        if not value or set(value) <= {"0"}:
            return False
    return True


def assert_measurement_seal_present(doc: dict) -> None:
    """A decision signature binds the recomputed measurement hash, so there must
    BE a measurement seal to bind to. Signing a judgment over an unsealed
    package would leave the chain's first link missing (A6's stale-bundle rule).
    """
    if not _is_real_seal(doc):
        raise RoleError(
            "this package carries no measurement seal, and a decision signature "
            "binds the recomputed measurement hash. Seal it first "
            "(`--as issuer`), or sign both in one act "
            "(`--as issuer,reviewer`).")

    # A-11, and it is a SEPARATE question from presence. The fused
    # `decision sign` recomputed the measurement hash and refused a bundle whose
    # content had drifted from what its seal covers; checking only that a seal
    # EXISTS would attest a judgment over measurements that have since changed --
    # a signature binding a hash that no longer describes the package it sits in.
    from uofa_cli.interrogate.signing import measurement_hash

    stored = doc["hash"]
    stored = stored.split(":", 1)[1] if ":" in stored else stored
    if measurement_hash(doc) != stored:
        raise RoleError(
            "the measurement content does not match its signed hash (stale or "
            "tampered) -- refusing to sign a judgment over measurements that "
            "have drifted from their seal. Nothing written.")


# ── the derivation: the only place these words exist ────────────────────────

DECIDER = "decider"
TRANSCRIPTION_ATTESTATION = "transcription-attestation"
CONCURRENCE = "concurrence"
UNRELATED = "unrelated"

#: Neither established nor refuted: at least one of the two identities cannot
#: take part in a comparison at all, so no relation can be computed.
#:
#: Distinct from `UNRELATED` on purpose. `unrelated` is a FINDING -- both parties
#: were legible and they are different. `indeterminate` is the ABSENCE of a
#: finding, and collapsing the two would report a conclusion the artifact does
#: not support. Silence sorts below both.
INDETERMINATE = "indeterminate"


# ── the identity grammar: one definition, read by the guard AND the derivation ──
#
# Actor-match is the truth substrate under every derived relation, so identity
# representation is not a formatting concern -- it is the one input everything
# downstream stands on. Two parties normalising to one accidental path would not
# raise an error; it would produce silently wrong relations reported with
# verify's full authority, which is the worst failure this system can have: a
# confident lie from the layer everyone trusts.
#
# So the grammar is stated once, here, beside the guard that enforces it, and
# the reference documentation is transcribed from these cases so the two cannot
# drift.

#: The EXACT form `interrogate.signing._fingerprint` emits:
#: `"sha256:" + hashlib.sha256(der).hexdigest()`. Stated as a precise pattern
#: rather than a permissive character class, because the permissive one is what
#: broke.
#:
#: **The defect this replaces.** The pattern was `[0-9a-fA-F:]{16,}`, whose `:`
#: anticipates colon-separated hex (`aa:bb:…`) and whose class contains no `s`
#: or `h` -- so it could never fullmatch `sha256:…`, the one form the product
#: actually writes into `signerIdentity`. Every real signature's signer was
#: therefore unclassifiable, `identity_is_comparable` was False on it, and
#: `derive_relation` fell through to `unrelated` for EVERY package in
#: existence -- including one whose actor and signer were byte-for-byte equal.
#: `decider` and `concurrence` were unreachable outside the unit tests, which
#: passed hand-written identity strings as the signer and so exercised a shape
#: the product never produces.
_FINGERPRINT_SHA256 = re.compile(r"sha256:[0-9a-f]{64}")

#: The legacy colon-grouped hex form (`aa:bb:cc:…`), kept because it is a pinned
#: legal identity. At least eight groups, so a short hex-looking accident cannot
#: pass as a key.
_FINGERPRINT_GROUPED = re.compile(r"(?:[0-9a-fA-F]{2}:){7,}[0-9a-fA-F]{2}")


def _is_fingerprint(v: str) -> bool:
    """Whether this is a key fingerprint in a form the project actually emits.

    Case-sensitive on the sha256 form deliberately: `hexdigest()` is lowercase,
    and accepting an uppercase variant would admit a value no code here writes,
    which is how a second spelling of one identity enters and two spellings of
    one party start reading as two parties.
    """
    return bool(_FINGERPRINT_SHA256.fullmatch(v)
                or _FINGERPRINT_GROUPED.fullmatch(v))

PERSON = "person"
INFRASTRUCTURE = "infrastructure"
ACT_REFERENCE = "act-reference"

#: Schemes that are never an identity. `file://` is the one that has actually
#: bitten: a bare name in an `@id` field resolves against wherever the document
#: happened to sit, so `V. Vettrivel` became a filesystem path -- an identifier
#: that points nowhere and differs by machine.
_REFUSED_SCHEMES = ("file://", "path://", "urn:path:")


class IdentityFormError(ValueError):
    """An identity whose form the grammar cannot classify."""


def classify_identity(value) -> str:
    """Which class of identity this is, or a refusal naming the form.

    Total by construction, for the same reason the decision fork is: a
    classification that guesses on unfamiliar input lets the empty-value genus
    in through the one door that must not have one.

    - person-class: an org-scoped handle IRI (`https://…/org/<handle>`)
    - infrastructure-class: a tool or deployment identifier (`urn:uofa:…`, or a
      key fingerprint, which is what the signer envelopes actually carry)
    - act-reference: `ledger://<assessor>/<entry>` -- an act, not a party
    """
    if not isinstance(value, str) or not value.strip():
        raise IdentityFormError(
            "an identity must be a non-empty string; refusing to compare "
            f"{type(value).__name__}.")
    v = value.strip()
    low = v.casefold()
    for bad in _REFUSED_SCHEMES:
        if low.startswith(bad):
            raise IdentityFormError(
                f"{v!r} is a filesystem-shaped identifier, not an identity. It "
                f"points nowhere and differs by machine, so two different "
                f"parties can normalise onto it -- refusing to compare it.")
    if low.startswith("ledger://"):
        return ACT_REFERENCE
    if "/org/" in low and low.startswith(("http://", "https://")):
        return PERSON
    if low.startswith("urn:"):
        return INFRASTRUCTURE
    if _is_fingerprint(v):
        # INFRASTRUCTURE, never PERSON. A fingerprint identifies a KEY. That the
        # key's holder is a person is a fact about custody, which no parser can
        # read off the bytes -- so parsing must never promote a fingerprint into
        # a human or an authorized reviewer.
        return INFRASTRUCTURE
    raise IdentityFormError(
        f"cannot classify identity {v!r}: expected an org-scoped handle IRI "
        f"(https://…/org/<handle>), a `urn:` or key-fingerprint infrastructure "
        f"identifier, or a `ledger://` act reference. Refusing to guess.")


#: The KIND of identifier, finer than the class. `classify_identity` answers
#: "what sort of party is this", which lumps a `urn:` name and a key fingerprint
#: together as INFRASTRUCTURE. For comparison the finer question matters: two
#: identifiers of DIFFERENT kinds are not the same identifier written two ways,
#: and nothing in a package binds one to another.
_KIND_HANDLE = "handle"
_KIND_URN = "urn"
_KIND_KEY = "key"
_KIND_ACT = "act"


def _identity_kind(value) -> str | None:
    """Which kind of identifier this is, or None if it is not one."""
    try:
        klass = classify_identity(value)
    except IdentityFormError:
        return None
    v = str(value).strip()
    if klass == ACT_REFERENCE:
        return _KIND_ACT
    if klass == PERSON:
        return _KIND_HANDLE
    return _KIND_KEY if _is_fingerprint(v) else _KIND_URN


def identity_is_comparable(value) -> bool:
    """Whether this identity may take part in an actor match at all."""
    try:
        return classify_identity(value) in (PERSON, INFRASTRUCTURE)
    except IdentityFormError:
        return False


def identities_are_bindable(a, b) -> bool:
    """Whether a relation between these two identities is even computable.

    **Author ruling 2026-09-11: UofA does not infer authority from an identifier
    form.** It follows that it cannot infer a relation ACROSS forms either. A
    handle names a person; a fingerprint names a key; nothing inside a package
    binds one to the other. Comparing them as strings and reporting the
    inevitable inequality as `unrelated` states a finding -- "these are two
    different parties" -- that no check performed.

    That conflation is not hypothetical. Every published C-series package names a
    person-class actor and carries a key fingerprint as signer, and so reported
    `unrelated`: a category error rendered as a conclusion.

    Same kind, both legible, is the only case where equality means anything.
    """
    ka, kb = _identity_kind(a), _identity_kind(b)
    if ka is None or kb is None:
        return False
    if _KIND_ACT in (ka, kb):
        # An act is not a party. Nothing about it can establish who decided.
        return False
    return ka == kb


def _same_actor(a, b) -> bool:
    """Whether two actor identities are the same party.

    **Actor-match is what the whole derivation stands on**, so it is strict
    about form. The `file://` class of bug -- a bare name landing in an `@id`
    field and resolving against wherever the document sat -- would silently
    corrupt every relation computed here, because two different parties could
    both normalise to the same accidental path.
    """
    if not (identity_is_comparable(a) and identity_is_comparable(b)):
        return False
    # Full-string comparison, never a normalised fragment. Two legal identities
    # that share a handle under different authorities are DIFFERENT parties, and
    # collapsing them is the collision half of the same silent-wrong-relation
    # disease the refusal set guards from the other side.
    return str(a).strip().casefold() == str(b).strip().casefold()


def derive_relation(record: dict, signer_identity: str,
                    *, all_records: list[dict] | None = None) -> str:
    """What a reviewer signature over this record MEANS. Computed, never stored.

    Three relations, each read off facts the artifact already carries:

    - the signer matches an `asserted` record's actor -> **decider**: they made
      this judgment and are standing behind it;
    - a signature over an `extracted` record -> **transcription attestation**:
      the judgment belongs to the source, cited by the anchor, and the signer is
      attesting the faithfulness of the transcription. The source never signs;
    - a signer standing behind their own asserted record that is scoped as
      concurrence with a prior one -> **concurrence**.

    Storing any of these would reintroduce the misdeclaration channel the
    two-role collapse closed: a stored relation can disagree with the record,
    and then a reader has to decide which to believe.
    """
    fork = str(record.get("decisionProvenance", "")).strip()
    if fork == "extracted":
        return TRANSCRIPTION_ATTESTATION
    if fork == "asserted":
        actor = record.get("actor")
        # **Cannot-establish is its own answer.** Two ways to land here: one side
        # is illegible to the grammar, or the two are legible but of DIFFERENT
        # KINDS, with nothing in the package binding a handle to a key. Either
        # way no comparison happened, and reporting `unrelated` would state a
        # finding nothing checked.
        if not identities_are_bindable(actor, signer_identity):
            return INDETERMINATE
        if _same_actor(actor, signer_identity):
            scope = str(record.get("decisionScope", "")).strip()
            if scope == "concurrence-with-prior-decision":
                return CONCURRENCE
            return DECIDER
    return UNRELATED


def describe_relation(record: dict, relation: str) -> str:
    """One line of verify output for a derived relation."""
    if relation == DECIDER:
        # **Self-declared, and labelled as such.** The package says its actor is
        # this key and that key signed. That is internal consistency, not an
        # external warrant: no one outside the artifact vouched for who holds the
        # key or whether they were entitled to decide.
        return "decided by the signer (self-declared by the package; authorization not assessed)"
    if relation == CONCURRENCE:
        return ("concurrence with a prior decision (self-declared by the "
                "package; authorization not assessed)")
    if relation == TRANSCRIPTION_ATTESTATION:
        who = record.get("role") or record.get("actor") or "the source"
        return (f"transcription attested; the decision belongs to {who} "
                f"per the cited passage")
    if relation == INDETERMINATE:
        # Says what was NOT done, and never implies a party. A reader must be
        # able to tell this apart from `unrelated` at a glance, because one is a
        # finding and the other is its absence.
        return ("signer-actor relationship NOT ESTABLISHED -- one of the two "
                "identities is not in a comparable form, so no relation was "
                "computed. This is neither a match nor a mismatch.")
    return "signature present, but it matches no record this signer authored"


def independence(signatures: list[dict]) -> str:
    """Whether the scopes were signed by one party or several.

    Derived from key IDENTITY, never key count: two envelopes carrying the same
    fingerprint are one party wearing two hats, and reporting that as
    independent attestation would overstate what the artifact proves.
    """
    ids = {str(s.get("signerIdentity", "")).strip() for s in signatures if s}
    ids.discard("")
    if len(ids) <= 1:
        return "single-party configuration: one key across the scopes signed"
    return f"independent attestation: {len(ids)} distinct signing identities"


# ── externally produced decision signatures ─────────────────────────────────
#
# Everything above assumes the signing process HOLDS the private key. That is
# true of the CLI and false of every deployment that means it when it says
# private keys stay with their owners: a browser, a hardware token, an HSM, a
# reviewer signing on a machine the service will never see.
#
# What such a caller has instead is (a) the exact bytes uofa wants signed and
# (b) a signature over them. The two functions below are the general form of
# that: one DESCRIBES the scope for a named record, the other VALIDATES a
# returned signature and incorporates it.
#
# Deliberately general, and deliberately narrow. No caller's account model, no
# registry of who may sign what, no authority inferred from an identifier. Who
# was permitted to sign is not a question uofa answers, here or anywhere.


class SignatureRefused(ValueError):
    """An externally produced signature that must not be incorporated."""


def decision_record_by_id(doc: dict, record_id: str) -> dict | None:
    """The one record with this `id`, or None.

    Exact-record selection, which `records_for_role` deliberately does not do:
    it returns every unsigned record, so `sign_decision_records` signs the lot.
    That is right for a CLI holding one key and signing its own package, and
    wrong for a reviewer attesting to ONE decision among several -- which would
    otherwise silently acquire signatures over records they never read.
    """
    for rec in decision_records(doc):
        if str(rec.get("id", "")) == str(record_id):
            return rec
    return None


def describe_decision_signing_scope(doc: dict, *, record_id: str) -> dict:
    """The exact bytes a signature over one decision record must cover.

    Returns the canonical string, its SHA-256 hex, the measurement hash it
    embeds, and the signing instruction -- explicitly, because the instruction
    is the part outside signers get wrong:

        **Sign the UTF-8 bytes of the 64-character lowercase hex STRING**, not
        the 32 raw digest bytes.

    `integrity.sign_hash` has documented that as intentional and non-standard
    since it was written, and a signer that hashes-then-signs-the-digest
    produces a signature that verifies against nothing while looking correct.
    Stating it in the returned payload means an implementer meets it rather
    than reading for it.
    """
    from uofa_cli.interrogate.signing import _scoped_block_hash, measurement_hash

    rec = decision_record_by_id(doc, record_id)
    if rec is None:
        raise SignatureRefused(
            f"no decision record with id {record_id!r} in this package. A "
            f"signature must name the record it covers; signing whatever is "
            f"unsigned is how a reviewer attests to something they never read.")
    if rec.get("hasDecisionSignature"):
        raise SignatureRefused(
            f"decision {record_id!r} already carries a signature. Replacing one "
            f"is not this operation: a corrected judgment is a successor "
            f"record, and overwriting would erase who attested to what.")

    block = {k: v for k, v in rec.items() if k != "hasDecisionSignature"}
    mh = measurement_hash(doc)
    scope = {"measurementHash": mh, "decision": block}
    canonical, _ = _canonical(scope)
    return {
        "record_id": record_id,
        "measurement_hash": mh,
        "canonicalization": "json-sortkeys/v1",
        "canonical_bytes": canonical,
        "digest_hex": _scoped_block_hash(doc, "decision", block),
        "signature_algorithm": "ed25519",
        "sign_these_bytes": (
            "the UTF-8 bytes of `digest_hex` -- the 64 lowercase hex characters "
            "themselves, NOT the 32 raw bytes they encode. See "
            "uofa_cli.integrity.sign_hash."),
    }


def _canonical(obj: dict) -> tuple[str, str]:
    from uofa_cli.integrity import canonicalize_and_hash

    return canonicalize_and_hash(obj)


def _public_key_from(public_key) -> object:
    """Accept a PEM, a DER SubjectPublicKeyInfo, or a loaded key object.

    A browser's `crypto.subtle.exportKey("spki", ...)` yields DER, and requiring
    PEM would push every web caller into hand-assembling base64 and header
    lines -- a step with nothing to check it.
    """
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

    if isinstance(public_key, Ed25519PublicKey):
        return public_key
    raw = public_key.encode() if isinstance(public_key, str) else bytes(public_key)
    try:
        if b"BEGIN" in raw:
            loaded = serialization.load_pem_public_key(raw)
        else:
            loaded = serialization.load_der_public_key(raw)
    except Exception as exc:                             # noqa: BLE001
        raise SignatureRefused(f"the public key could not be read: {exc}") from exc
    if not isinstance(loaded, Ed25519PublicKey):
        raise SignatureRefused(
            f"a decision signature is ed25519; this key is "
            f"{type(loaded).__name__}. uofa will not verify one algorithm's "
            f"signature by pretending it is another's.")
    return loaded


def public_fingerprint(public_key) -> str:
    """The `signerIdentity` form, from a public key alone.

    `fingerprint_from_private_key` needs the private half, which an external
    signer by definition does not hand over. Same derivation -- SHA-256 over the
    DER SubjectPublicKeyInfo -- so the two agree for the same keypair.
    """
    import hashlib

    from cryptography.hazmat.primitives import serialization

    der = _public_key_from(public_key).public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo)
    return "sha256:" + hashlib.sha256(der).hexdigest()


def incorporate_decision_signature(doc: dict, *, record_id: str, public_key,
                                   signature, role: str = REVIEWER,
                                   now: str) -> dict:
    """Validate a signature made elsewhere, then attach it. Returns the block.

    **Verified before it is attached, against the scope recomputed here.** The
    caller's claim about which bytes were signed is not evidence: a signature
    that only verifies against bytes the caller supplied alongside it proves
    that the caller is self-consistent.

    The document is mutated only after the signature checks out, so a refusal
    leaves no half-attested record behind.
    """
    from cryptography.exceptions import InvalidSignature

    if role not in DECISION_ROLES:
        raise SignatureRefused(
            f"{role!r} is not a decision role; a decision signature is made as "
            f"{sorted(DECISION_ROLES)}")

    scope = describe_decision_signing_scope(doc, record_id=record_id)
    pub = _public_key_from(public_key)

    raw = signature
    if isinstance(raw, str):
        raw = raw.split(":", 1)[1] if raw.startswith("ed25519:") else raw
        try:
            raw = bytes.fromhex(raw.strip())
        except ValueError as exc:
            raise SignatureRefused(
                "the signature is not hex; a decision signature travels as "
                "`ed25519:<hex>` or bare hex") from exc
    raw = bytes(raw)
    if len(raw) != 64:
        raise SignatureRefused(
            f"an ed25519 signature is 64 bytes; this one is {len(raw)}")

    try:
        pub.verify(raw, scope["digest_hex"].encode("utf-8"))
    except InvalidSignature:
        raise SignatureRefused(
            "the signature does not verify against this package's scope for "
            f"decision {record_id!r}. Nothing was attached. If it was made "
            "over the raw digest bytes rather than over the hex string, it is "
            "the wrong bytes -- see `sign_these_bytes` in "
            "`describe_decision_signing_scope`.") from None

    block = {
        "type": "DecisionSignature",
        "signatureRole": role,
        "signerIdentity": public_fingerprint(pub),
        "measurementHash": scope["measurement_hash"],
        "signatureAlgorithm": "ed25519",
        "signatureValue": "ed25519:" + raw.hex(),
        "signedAt": now,
    }
    decision_record_by_id(doc, record_id)["hasDecisionSignature"] = block
    return block

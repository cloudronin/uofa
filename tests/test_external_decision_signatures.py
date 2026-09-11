"""A signature made somewhere else, verified and incorporated here.

Every other signing path in uofa assumes the process HOLDS the private key.
That is true of the CLI and false of every deployment that means it when it
says private keys stay with their owners -- a browser, a token, an HSM, a
reviewer on a machine the service will never see.

These tests drive the general form: ask uofa what bytes to sign, sign them
somewhere uofa cannot reach, hand back the signature and the public half.

**The signing key here never touches a file and is never given to uofa.** It is
an in-memory Ed25519 key standing in for a browser's non-exportable CryptoKey,
and if any of this needed the private half the tests could not be written this
way.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from uofa_cli import sign_roles as S

NOW = "2026-09-11T00:00:00Z"


def _package() -> dict:
    """A real shipped package that carries a decision layer."""
    src = (Path(__file__).resolve().parents[1] / "specs" / "calibration" /
           "packages" / "cal-030-uncertain-variability.jsonld")
    if not src.exists():
        pytest.skip(f"fixture package missing: {src}")
    doc = json.loads(src.read_text(encoding="utf-8"))
    for rec in S.decision_records(doc):
        rec.pop("hasDecisionSignature", None)
    return doc


def _elsewhere():
    """A keypair uofa never sees the private half of."""
    priv = Ed25519PrivateKey.generate()
    spki = priv.public_key().public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo)
    return priv, spki


@pytest.fixture
def doc():
    return _package()


@pytest.fixture
def record_id(doc):
    recs = S.decision_records(doc)
    assert recs, "the fixture package has no decision layer"
    return recs[0]["id"]


# ── the scope ───────────────────────────────────────────────────────────────

def test_the_scope_states_which_bytes_to_sign_rather_than_leaving_it_to_be_read(
        doc, record_id):
    """The instruction is the part outside signers get wrong.

    A signature over the raw digest bytes verifies against nothing while looking
    entirely correct, so the payload says which bytes in words.
    """
    scope = S.describe_decision_signing_scope(doc, record_id=record_id)
    assert scope["signature_algorithm"] == "ed25519"
    assert scope["canonicalization"] == "json-sortkeys/v1"
    assert len(scope["digest_hex"]) == 64
    assert scope["digest_hex"].islower()
    assert "NOT the 32 raw bytes" in scope["sign_these_bytes"]


def test_the_scope_digest_is_the_one_the_in_process_signer_would_use(doc,
                                                                    record_id):
    """Same bytes as `sign_decision_records`, or an external signature is a
    different format wearing the same field name."""
    from uofa_cli.interrogate.signing import _scoped_block_hash

    rec = S.decision_record_by_id(doc, record_id)
    block = {k: v for k, v in rec.items() if k != "hasDecisionSignature"}
    scope = S.describe_decision_signing_scope(doc, record_id=record_id)
    assert scope["digest_hex"] == _scoped_block_hash(doc, "decision", block)


def test_an_unknown_record_is_refused(doc):
    with pytest.raises(S.SignatureRefused) as exc:
        S.describe_decision_signing_scope(doc, record_id="no-such-record")
    assert "never read" in str(exc.value)


# ── the round trip ──────────────────────────────────────────────────────────

def test_a_signature_made_elsewhere_is_accepted_and_reads_as_uofa_wrote_it(
        doc, record_id):
    priv, spki = _elsewhere()
    scope = S.describe_decision_signing_scope(doc, record_id=record_id)
    signature = priv.sign(scope["digest_hex"].encode("utf-8"))

    block = S.incorporate_decision_signature(
        doc, record_id=record_id, public_key=spki, signature=signature, now=NOW)

    assert block["signatureAlgorithm"] == "ed25519"
    assert block["signatureRole"] == S.REVIEWER
    assert block["signatureValue"].startswith("ed25519:")
    assert block["measurementHash"] == scope["measurement_hash"]
    assert block["signedAt"] == NOW
    # Attached to the document, not merely returned.
    assert S.decision_record_by_id(doc, record_id)["hasDecisionSignature"] == block


def test_the_signer_identity_matches_the_in_process_derivation(doc, record_id):
    """`fingerprint_from_private_key` needs the private half an external signer
    never hands over. Both derivations must agree or one keypair gets two
    identities."""
    from uofa_cli.interrogate.signing import fingerprint_from_private_key

    priv, spki = _elsewhere()
    pem = priv.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption())
    assert S.public_fingerprint(spki) == fingerprint_from_private_key(key_bytes=pem)


def test_a_pem_public_key_works_as_well_as_der(doc, record_id):
    priv, _spki = _elsewhere()
    pem = priv.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo)
    scope = S.describe_decision_signing_scope(doc, record_id=record_id)
    block = S.incorporate_decision_signature(
        doc, record_id=record_id, public_key=pem,
        signature=priv.sign(scope["digest_hex"].encode("utf-8")), now=NOW)
    assert block["signerIdentity"] == S.public_fingerprint(pem)


def test_a_hex_string_signature_is_accepted_in_either_spelling(doc, record_id):
    priv, spki = _elsewhere()
    scope = S.describe_decision_signing_scope(doc, record_id=record_id)
    sig = priv.sign(scope["digest_hex"].encode("utf-8")).hex()
    block = S.incorporate_decision_signature(
        doc, record_id=record_id, public_key=spki,
        signature="ed25519:" + sig, now=NOW)
    assert block["signatureValue"] == "ed25519:" + sig


# ── negative controls, each failing for its own reason ──────────────────────

def test_a_signature_over_the_raw_digest_bytes_is_refused_and_told_why(
        doc, record_id):
    """The single most likely implementation mistake, so the refusal names it."""
    priv, spki = _elsewhere()
    scope = S.describe_decision_signing_scope(doc, record_id=record_id)
    wrong = priv.sign(bytes.fromhex(scope["digest_hex"]))      # digest, not hex
    with pytest.raises(S.SignatureRefused) as exc:
        S.incorporate_decision_signature(doc, record_id=record_id,
                                         public_key=spki, signature=wrong,
                                         now=NOW)
    assert "over the raw digest bytes" in str(exc.value)
    assert not S.decision_record_by_id(doc, record_id).get("hasDecisionSignature")


def test_a_substituted_key_is_refused(doc, record_id):
    priv, _spki = _elsewhere()
    _other, other_spki = _elsewhere()
    scope = S.describe_decision_signing_scope(doc, record_id=record_id)
    with pytest.raises(S.SignatureRefused):
        S.incorporate_decision_signature(
            doc, record_id=record_id, public_key=other_spki,
            signature=priv.sign(scope["digest_hex"].encode()), now=NOW)


def test_a_signature_over_another_record_is_refused(doc):
    """Two records, one signature. It verifies -- against the wrong scope."""
    recs = S.decision_records(doc)
    if len(recs) < 2:
        extra = dict(recs[0])
        extra["id"] = str(extra["id"]) + "-second"
        extra["outcome"] = "SYNTHETIC second outcome"
        doc["hasDecisionRecord"] = [recs[0], extra]
    a, b = [r["id"] for r in S.decision_records(doc)][:2]
    priv, spki = _elsewhere()
    scope_a = S.describe_decision_signing_scope(doc, record_id=a)
    with pytest.raises(S.SignatureRefused) as exc:
        S.incorporate_decision_signature(
            doc, record_id=b, public_key=spki,
            signature=priv.sign(scope_a["digest_hex"].encode()), now=NOW)
    assert "does not verify" in str(exc.value)


def test_an_altered_decision_invalidates_a_signature_prepared_before_it(
        doc, record_id):
    priv, spki = _elsewhere()
    scope = S.describe_decision_signing_scope(doc, record_id=record_id)
    signature = priv.sign(scope["digest_hex"].encode())
    S.decision_record_by_id(doc, record_id)["outcome"] = "SYNTHETIC changed"
    with pytest.raises(S.SignatureRefused):
        S.incorporate_decision_signature(doc, record_id=record_id,
                                         public_key=spki, signature=signature,
                                         now=NOW)


def test_an_altered_measurement_invalidates_it_too(doc, record_id):
    """The embedded measurement hash is what chains judgment to evidence."""
    priv, spki = _elsewhere()
    scope = S.describe_decision_signing_scope(doc, record_id=record_id)
    signature = priv.sign(scope["digest_hex"].encode())
    doc["name"] = str(doc.get("name", "")) + " SYNTHETIC EDIT"
    with pytest.raises(S.SignatureRefused):
        S.incorporate_decision_signature(doc, record_id=record_id,
                                         public_key=spki, signature=signature,
                                         now=NOW)


def test_an_already_signed_record_is_not_overwritten(doc, record_id):
    priv, spki = _elsewhere()
    scope = S.describe_decision_signing_scope(doc, record_id=record_id)
    S.incorporate_decision_signature(
        doc, record_id=record_id, public_key=spki,
        signature=priv.sign(scope["digest_hex"].encode()), now=NOW)
    other, other_spki = _elsewhere()
    with pytest.raises(S.SignatureRefused) as exc:
        S.incorporate_decision_signature(
            doc, record_id=record_id, public_key=other_spki,
            signature=other.sign(scope["digest_hex"].encode()), now=NOW)
    assert "successor" in str(exc.value)


def test_a_non_ed25519_key_is_refused_rather_than_coerced(doc, record_id):
    from cryptography.hazmat.primitives.asymmetric import rsa

    pub = rsa.generate_private_key(public_exponent=65537, key_size=2048).public_key()
    pem = pub.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo)
    with pytest.raises(S.SignatureRefused) as exc:
        S.incorporate_decision_signature(doc, record_id=record_id,
                                         public_key=pem, signature=b"\x00" * 64,
                                         now=NOW)
    assert "ed25519" in str(exc.value)


def test_a_wrong_length_signature_is_refused_before_any_crypto(doc, record_id):
    _priv, spki = _elsewhere()
    with pytest.raises(S.SignatureRefused) as exc:
        S.incorporate_decision_signature(doc, record_id=record_id,
                                         public_key=spki, signature=b"\x00" * 32,
                                         now=NOW)
    assert "64 bytes" in str(exc.value)


def test_nothing_here_can_reach_a_private_key():
    """The API must not grow a key argument, or a call that wants one.

    Walked as an AST, not grepped. A text scan matched this module's own
    docstrings -- which name `sign_hash` precisely in order to warn about it --
    and a guard that fires on its own explanation teaches the next person to
    delete the guard.
    """
    import ast
    import inspect
    import textwrap

    banned_args = {"key_path", "key_bytes", "private_key"}
    banned_calls = {"sign_hash", "sign_file", "load_pem_private_key",
                    "fingerprint_from_private_key", "sign_decision_records"}

    for fn in (S.describe_decision_signing_scope,
               S.incorporate_decision_signature, S.public_fingerprint,
               S._public_key_from, S.decision_record_by_id):
        tree = ast.parse(textwrap.dedent(inspect.getsource(fn)))
        for node in ast.walk(tree):
            if isinstance(node, ast.arg):
                assert node.arg not in banned_args, (
                    f"{fn.__name__} takes {node.arg!r}. These functions exist "
                    f"because the private key is somewhere uofa cannot reach.")
            if isinstance(node, ast.Call):
                f = node.func
                name = (f.attr if isinstance(f, ast.Attribute)
                        else getattr(f, "id", ""))
                assert name not in banned_calls, (
                    f"{fn.__name__} calls {name!r}, which needs a private key")

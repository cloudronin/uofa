"""Two-scope signing for SIP packages (Addendum A6) — measurement + decision.

A finished surrogate package carries two distinct signatures meaning two
distinct claims:

- **Measurement signature** (the bundle's top-level ``hash``/``signature``):
  over the measurement bundle = the package MINUS the integrity fields MINUS
  ``hasDecisionRecord``. Attests "SIP measured this." Excluding ``hasDecisionRecord``
  is what lets the measurement signature keep verifying after a decision is
  appended.
- **Decision signature** (``hasDecisionRecord.decisionSignature``): over the
  decision block PLUS the measurements it references — implemented as a
  signature over ``{"measurementHash": <recomputed>, "decision": <block−sig>}``.
  Binding to the *recomputed* measurement hash (never the stored ``hash`` field)
  makes it tamper-evident: altering any measurement changes the recomputed hash,
  so the decision signature fails (A10 tamper test); a signature scoped to the
  decision alone fails because verification always reconstructs the scope WITH
  ``measurementHash`` (A10 mis-scope test).

This module reuses the low-level ``integrity`` primitives
(``canonicalize_and_hash``/``sign_hash``/``verify_signature``) without the
whole-file semantics — **no core mutation**. UofA verifies; it never holds the
engineer's key (A7).
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives import serialization

from uofa_cli.integrity import (
    CANONICALIZATION_ALG,
    INTEGRITY_FIELDS,
    canonicalize_and_hash,
    sign_hash,
    verify_signature,
)
from uofa_cli.interrogate.forbidden import ACTION_REGION_KEYS, DECISION_BLOCK_KEY

# The measurement signature's scope excludes the integrity fields AND every
# action-region block (hasDecisionRecord, guardrailAction, …) — each signed
# separately in its own scope. Excluding them is what lets the measurement
# signature keep verifying after a decision/action block is appended.
MEASUREMENT_EXCLUDED = set(INTEGRITY_FIELDS) | set(ACTION_REGION_KEYS)


def is_sip_bundle(doc: dict) -> bool:
    """True for a SIP evidence bundle (by schemaVersion)."""
    return isinstance(doc, dict) and str(doc.get("schemaVersion", "")).startswith(
        "sip-evidence-bundle"
    )


# ── Measurement scope ───────────────────────────────────────────────────────


def _measurement_view(package: dict) -> dict:
    return {k: v for k, v in package.items() if k not in MEASUREMENT_EXCLUDED}


def measurement_hash(package: dict) -> str:
    """SHA-256 hex of the canonical measurement view (excludes hasDecisionRecord)."""
    _, sha256_hex = canonicalize_and_hash(_measurement_view(package))
    return sha256_hex


def sign_measurement(package_path: Path, key_path: Path, output_path: Path | None = None) -> tuple[str, str]:
    """Sign the measurement scope in place; embed top-level integrity fields."""
    package = json.loads(Path(package_path).read_text(encoding="utf-8"))
    sha256_hex = measurement_hash(package)
    sig_hex = sign_hash(sha256_hex, Path(key_path))
    package["hash"] = f"sha256:{sha256_hex}"
    package["signature"] = f"ed25519:{sig_hex}"
    package["signatureAlg"] = "ed25519"
    package["canonicalizationAlg"] = CANONICALIZATION_ALG
    out = Path(output_path or package_path)
    out.write_text(json.dumps(package, indent=2, ensure_ascii=False), encoding="utf-8")
    return sha256_hex, sig_hex


def verify_measurement(package: dict, pubkey_path: Path) -> tuple[bool, bool]:
    """Return (hash_ok, sig_ok) for the measurement signature on a loaded package."""
    sha256_hex = measurement_hash(package)
    declared = package.get("hash", "")
    declared_hex = declared.split(":", 1)[1] if ":" in declared else declared
    hash_ok = declared_hex == sha256_hex
    sig = package.get("signature", "")
    sig_hex = sig.split(":", 1)[1] if ":" in sig else sig
    sig_ok = verify_signature(sha256_hex, sig_hex, Path(pubkey_path)) if sig_hex else False
    return hash_ok, sig_ok


# ── Key fingerprints (decidedBy is a key identity, not free text — A4/A8) ────


def _fingerprint(public_key) -> str:
    der = public_key.public_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return "sha256:" + hashlib.sha256(der).hexdigest()


def fingerprint_from_private_key(key_path: Path) -> str:
    private_key = serialization.load_pem_private_key(Path(key_path).read_bytes(), password=None)
    return _fingerprint(private_key.public_key())


def fingerprint_from_public_key(pubkey_path: Path) -> str:
    public_key = serialization.load_pem_public_key(Path(pubkey_path).read_bytes())
    return _fingerprint(public_key)


# ── Action-region scopes (generalized two-scope signing) ─────────────────────
# An action-region block (hasDecisionRecord, guardrailAction, downstream labels)
# is signed over its OWN scope = {"measurementHash": <recomputed>, <scope_key>:
# <block − signature>}. Binding to the *recomputed* measurement hash makes it
# tamper-evident (altering any measurement breaks it) and lets the measurement
# signature and the block signature verify independently. hasDecisionRecord uses
# scope_key="decision"; the guardrail leg uses scope_key="action".


def _scoped_block_hash(package: dict, scope_key: str, block_without_signature: dict) -> str:
    scope = {"measurementHash": measurement_hash(package), scope_key: block_without_signature}
    _, sha256_hex = canonicalize_and_hash(scope)
    return sha256_hex


def _decision_scope_hash(package: dict, decision_block_without_signature: dict) -> str:
    """Back-compat alias: the hasDecisionRecord scope (scope_key='decision')."""
    return _scoped_block_hash(package, "decision", decision_block_without_signature)


def sign_scoped_block(
    package: dict, key_path: Path, block_without_signature: dict,
    *, scope_key: str, signature_field: str,
) -> dict:
    """Sign an action-region block over its scope; return block + ``signature_field``."""
    sha256_hex = _scoped_block_hash(package, scope_key, block_without_signature)
    sig_hex = sign_hash(sha256_hex, Path(key_path))
    return {**block_without_signature, signature_field: f"ed25519:{sig_hex}"}


def verify_scoped_block(
    package: dict, pubkey_path: Path,
    *, block_key: str, scope_key: str, signature_field: str,
    attributed_by_field: str | None = None,
) -> tuple[bool, str]:
    """Verify an action-region block's signature over its scope. Returns (ok, reason).

    A missing/unsigned/mis-scoped/unverifiable block, or an attributed-key
    mismatch, all resolve to (False, reason) — the caller treats any of these as
    "no such block", never package failure.
    """
    block = package.get(block_key)
    if not isinstance(block, dict):
        return False, f"no {block_key} block present"
    sig_field = block.get(signature_field)
    if not sig_field:
        return False, f"{block_key} present but unsigned"
    block_without_sig = {k: v for k, v in block.items() if k != signature_field}
    sha256_hex = _scoped_block_hash(package, scope_key, block_without_sig)
    sig_hex = sig_field.split(":", 1)[1] if ":" in sig_field else sig_field
    if not verify_signature(sha256_hex, sig_hex, Path(pubkey_path)):
        return False, f"{block_key} signature does not verify over scope ({scope_key} + measurements)"
    if attributed_by_field:
        expected = fingerprint_from_public_key(Path(pubkey_path))
        if block.get(attributed_by_field) != expected:
            return False, f"{attributed_by_field} does not match the supplied key fingerprint"
    return True, "ok"


def build_decision_block(
    *,
    acceptance_criterion: str,
    decision_value: str,
    decided_at: str,
    rationale: str | None = None,
    actor: str | None = None,
    key_path: Path | None = None,
) -> dict:
    """Assemble the hasDecisionRecord block (without its signature).

    Two identity inputs, and the difference is the whole point of splitting
    authoring from signing:

    - ``actor`` -- WHO DECIDED. A person-class identity per the grammar in
      ``sign_roles``. Known at authoring time, because it is a fact about the
      judgment.
    - ``key_path`` -- WHICH KEY ATTESTED. Stamped as ``decidedBy``, a fingerprint.
      This is a fact about the *attestation*, not about the judgment, so it is
      knowable only when a key is present and belongs to the signing step.

    The original signature required ``key_path``, which quietly made "who
    decided" underivable without a private key -- so a decision could not exist
    before its signature, and the two acts had to be fused. They are not fused
    any more, so this takes either, and the caller supplies what its step knows.
    """
    block = {}
    if key_path is not None:
        block["decidedBy"] = fingerprint_from_private_key(Path(key_path))
    if actor is not None:
        block["actor"] = actor
    block.update({
        "acceptanceCriterion": acceptance_criterion,
        "decisionValue": decision_value,
        "decidedAt": decided_at,
    })
    if rationale:
        block["decisionRationale"] = rationale
    return block


def sign_decision(package: dict, key_path: Path, decision_block_without_signature: dict) -> dict:
    """Engineer-decision block signed over the A6 scope (decision + measurements).

    Thin wrapper over ``sign_scoped_block`` (scope_key='decision') — behaviour and
    output bytes are identical to the pre-generalization implementation.
    """
    return sign_scoped_block(
        package, key_path, decision_block_without_signature,
        scope_key="decision", signature_field="decisionSignature",
    )


def verify_decision(package: dict, decision_pubkey_path: Path) -> tuple[bool, str]:
    """Verify the engineer-decision signature over its A6 scope. Returns (ok, reason).

    A missing block, missing/unverifiable/mis-scoped signature, or a decidedBy
    that doesn't match the supplied key all resolve to (False, reason) — the
    caller treats any of these as "no engineer decision," never failure. Thin
    wrapper over ``verify_scoped_block``.
    """
    block = package.get(DECISION_BLOCK_KEY)

    # `hasDecisionRecord` is repeatable. A list reaching a verifier that only
    # understands dicts would report "no block present" over a package carrying
    # several signed judgments -- absent and unreadable are not the same answer,
    # and only one of them is true.
    if isinstance(block, list):
        reasons = []
        for rec in block:
            ok, reason = verify_decision({**package, DECISION_BLOCK_KEY: rec},
                                         decision_pubkey_path)
            if ok:
                return True, "ok"
            reasons.append(reason)
        return False, ("no decision record verifies against this key: "
                       + "; ".join(reasons) if reasons else "no decision record present")

    # The canonical form: a `DecisionSignature` node carrying its own role,
    # identity, algorithm and bound measurement hash. The legacy `decisionSignature`
    # string below predates it and is still read, because packages carrying it
    # exist and were honestly signed.
    if isinstance(block, dict) and isinstance(block.get("hasDecisionSignature"), dict):
        return _verify_decision_signature_node(package, block, decision_pubkey_path)

    return verify_scoped_block(
        package, decision_pubkey_path,
        block_key=DECISION_BLOCK_KEY, scope_key="decision",
        signature_field="decisionSignature", attributed_by_field="decidedBy",
    )


def _verify_decision_signature_node(
    package: dict, block: dict, decision_pubkey_path: Path,
) -> tuple[bool, str]:
    """Verify a canonical `DecisionSignature` node over the A6 scope."""
    node = block["hasDecisionSignature"]
    sig_field = node.get("signatureValue")
    if not sig_field:
        return False, f"{DECISION_BLOCK_KEY} carries a signature node with no signatureValue"

    block_without_sig = {k: v for k, v in block.items() if k != "hasDecisionSignature"}
    sha256_hex = _scoped_block_hash(package, "decision", block_without_sig)
    sig_hex = sig_field.split(":", 1)[1] if ":" in sig_field else sig_field
    if not verify_signature(sha256_hex, sig_hex, Path(decision_pubkey_path)):
        return False, (f"{DECISION_BLOCK_KEY} signature does not verify over scope "
                       f"(decision + measurements)")

    # The embedded hash is the chain link between judgment and evidence. Not
    # checking it would leave the binding decorative: the signature would still
    # verify while naming a measurement state the package no longer has.
    recomputed = measurement_hash(package)
    if node.get("measurementHash") not in (None, recomputed):
        return False, ("the decision signature binds a measurement hash that does "
                       "not match this package's measurements (stale or tampered)")

    expected = fingerprint_from_public_key(Path(decision_pubkey_path))
    if node.get("signerIdentity") not in (None, expected):
        return False, "signerIdentity does not match the supplied key fingerprint"
    return True, "ok"

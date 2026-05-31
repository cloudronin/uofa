"""Two-scope signing for SIP packages (Addendum A6) — measurement + decision.

A finished surrogate package carries two distinct signatures meaning two
distinct claims:

- **Measurement signature** (the bundle's top-level ``hash``/``signature``):
  over the measurement bundle = the package MINUS the integrity fields MINUS
  ``engineerDecision``. Attests "SIP measured this." Excluding ``engineerDecision``
  is what lets the measurement signature keep verifying after a decision is
  appended.
- **Decision signature** (``engineerDecision.decisionSignature``): over the
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
# action-region block (engineerDecision, guardrailAction, …) — each signed
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
    """SHA-256 hex of the canonical measurement view (excludes engineerDecision)."""
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
# An action-region block (engineerDecision, guardrailAction, downstream labels)
# is signed over its OWN scope = {"measurementHash": <recomputed>, <scope_key>:
# <block − signature>}. Binding to the *recomputed* measurement hash makes it
# tamper-evident (altering any measurement breaks it) and lets the measurement
# signature and the block signature verify independently. engineerDecision uses
# scope_key="decision"; the guardrail leg uses scope_key="action".


def _scoped_block_hash(package: dict, scope_key: str, block_without_signature: dict) -> str:
    scope = {"measurementHash": measurement_hash(package), scope_key: block_without_signature}
    _, sha256_hex = canonicalize_and_hash(scope)
    return sha256_hex


def _decision_scope_hash(package: dict, decision_block_without_signature: dict) -> str:
    """Back-compat alias: the engineerDecision scope (scope_key='decision')."""
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
    key_path: Path,
    acceptance_criterion: str,
    decision_value: str,
    decided_at: str,
    rationale: str | None = None,
) -> dict:
    """Assemble the engineerDecision block (without its signature)."""
    block = {
        "decidedBy": fingerprint_from_private_key(Path(key_path)),
        "acceptanceCriterion": acceptance_criterion,
        "decisionValue": decision_value,
        "decidedAt": decided_at,
    }
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
    return verify_scoped_block(
        package, decision_pubkey_path,
        block_key=DECISION_BLOCK_KEY, scope_key="decision",
        signature_field="decisionSignature", attributed_by_field="decidedBy",
    )

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
    INTEGRITY_FIELDS,
    canonicalize_and_hash,
    sign_hash,
    verify_signature,
)

DECISION_BLOCK_KEY = "engineerDecision"
# The measurement signature's scope excludes the integrity fields AND the
# engineer-decision block (which is signed separately, later, by a human).
MEASUREMENT_EXCLUDED = set(INTEGRITY_FIELDS) | {DECISION_BLOCK_KEY}


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
    package["canonicalizationAlg"] = "RDFC-1.0"
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


# ── Decision scope ───────────────────────────────────────────────────────────


def _decision_scope_hash(package: dict, decision_block_without_signature: dict) -> str:
    scope = {
        "measurementHash": measurement_hash(package),
        "decision": decision_block_without_signature,
    }
    _, sha256_hex = canonicalize_and_hash(scope)
    return sha256_hex


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
    """Return the engineerDecision block with a decisionSignature over the A6 scope."""
    sha256_hex = _decision_scope_hash(package, decision_block_without_signature)
    sig_hex = sign_hash(sha256_hex, Path(key_path))
    return {**decision_block_without_signature, "decisionSignature": f"ed25519:{sig_hex}"}


def verify_decision(package: dict, decision_pubkey_path: Path) -> tuple[bool, str]:
    """Verify the decision signature over its A6 scope. Returns (ok, reason).

    A missing block, missing/unverifiable signature, mis-scoped signature, or a
    decidedBy that doesn't match the supplied key all resolve to (False, reason)
    — the caller treats any of these as "no engineer decision," never failure.
    """
    block = package.get(DECISION_BLOCK_KEY)
    if not isinstance(block, dict):
        return False, "no engineerDecision block present"
    sig_field = block.get("decisionSignature")
    if not sig_field:
        return False, "engineerDecision present but unsigned"
    block_without_sig = {k: v for k, v in block.items() if k != "decisionSignature"}
    sha256_hex = _decision_scope_hash(package, block_without_sig)
    sig_hex = sig_field.split(":", 1)[1] if ":" in sig_field else sig_field
    if not verify_signature(sha256_hex, sig_hex, Path(decision_pubkey_path)):
        return False, "decision signature does not verify over scope (decision + measurements)"
    expected = fingerprint_from_public_key(Path(decision_pubkey_path))
    if block.get("decidedBy") != expected:
        return False, "decidedBy does not match the supplied decision key fingerprint"
    return True, "ok"

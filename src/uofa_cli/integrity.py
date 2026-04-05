"""Cryptographic integrity operations for UofA evidence packages.

Provides hashing, signing, and verification for UofA JSON-LD files.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization

# ── Fields stripped before hashing ─────────────────────────────

INTEGRITY_FIELDS = {"hash", "signature", "signatureAlg", "canonicalizationAlg"}


def resolve_context(doc: dict, jsonld_path: Path, context_path: Path = None) -> dict:
    """Resolve external @context reference to inline object."""
    ctx_ref = doc.get("@context")
    if isinstance(ctx_ref, dict):
        return doc

    if isinstance(ctx_ref, str):
        candidates = []
        if context_path:
            candidates.append(context_path)
        candidates.append(jsonld_path.parent / ctx_ref)

        for p in candidates:
            if p.exists():
                with open(p, "r") as f:
                    ctx_doc = json.load(f)
                doc["@context"] = ctx_doc.get("@context", ctx_doc)
                return doc

    return doc


def strip_integrity_fields(doc: dict) -> dict:
    """Return a copy with integrity fields removed."""
    return {k: v for k, v in doc.items() if k not in INTEGRITY_FIELDS}


def canonicalize_and_hash(doc: dict) -> tuple[str, str]:
    """Canonicalize JSON-LD and compute SHA-256. Returns (canonical_str, hex_digest)."""
    canonical = json.dumps(doc, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    canonical_bytes = canonical.encode("utf-8")
    sha256_hex = hashlib.sha256(canonical_bytes).hexdigest()
    return canonical, sha256_hex


def generate_keypair(key_path: Path):
    """Generate ed25519 keypair and save to disk. Returns (key_path, pub_path)."""
    private_key = Ed25519PrivateKey.generate()

    key_path.parent.mkdir(parents=True, exist_ok=True)
    with open(key_path, "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ))

    pub_path = key_path.with_suffix(".pub")
    public_key = private_key.public_key()
    with open(pub_path, "wb") as f:
        f.write(public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ))

    return key_path, pub_path


def sign_hash(sha256_hex: str, key_path: Path) -> str:
    """Sign the SHA-256 hex string with ed25519 private key. Returns signature hex."""
    with open(key_path, "rb") as f:
        private_key = serialization.load_pem_private_key(f.read(), password=None)

    signature_bytes = private_key.sign(sha256_hex.encode("utf-8"))
    return signature_bytes.hex()


def verify_signature(sha256_hex: str, signature_hex: str, pubkey_path: Path) -> bool:
    """Verify ed25519 signature against public key."""
    with open(pubkey_path, "rb") as f:
        public_key = serialization.load_pem_public_key(f.read())

    try:
        public_key.verify(
            bytes.fromhex(signature_hex),
            sha256_hex.encode("utf-8"),
        )
        return True
    except Exception:
        return False


def load_and_hash(input_path: Path, context_path: Path = None) -> tuple[dict, str, str]:
    """Load a UofA JSON-LD file, resolve context, strip integrity fields, and hash.

    Returns (original_doc, canonical_str, sha256_hex).
    """
    with open(input_path, "r") as f:
        doc = json.load(f)

    resolved = resolve_context(doc.copy(), input_path, context_path)
    stripped = strip_integrity_fields(resolved)
    canonical, sha256_hex = canonicalize_and_hash(stripped)
    return doc, canonical, sha256_hex


def sign_file(input_path: Path, key_path: Path, context_path: Path = None,
              output_path: Path = None) -> tuple[str, str]:
    """Sign a UofA file in place. Returns (hash_hex, signature_hex)."""
    doc, canonical, sha256_hex = load_and_hash(input_path, context_path)
    sig_hex = sign_hash(sha256_hex, key_path)

    # Re-read original (preserves original @context reference)
    with open(input_path, "r") as f:
        original = json.load(f)

    original["hash"] = f"sha256:{sha256_hex}"
    original["signature"] = f"ed25519:{sig_hex}"
    original["signatureAlg"] = "ed25519"
    original["canonicalizationAlg"] = "RDFC-1.0"

    out = output_path or input_path
    with open(out, "w") as f:
        json.dump(original, f, indent=2, ensure_ascii=False)

    return sha256_hex, sig_hex


def verify_file(input_path: Path, pubkey_path: Path,
                context_path: Path = None) -> tuple[bool, bool]:
    """Verify hash and signature of a UofA file. Returns (hash_ok, sig_ok)."""
    doc, canonical, sha256_hex = load_and_hash(input_path, context_path)

    declared_hash = doc.get("hash", "")
    declared_hex = declared_hash.split(":", 1)[1] if ":" in declared_hash else declared_hash
    hash_ok = declared_hex == sha256_hex

    declared_sig = doc.get("signature", "")
    sig_hex = declared_sig.split(":", 1)[1] if ":" in declared_sig else declared_sig
    sig_ok = verify_signature(sha256_hex, sig_hex, pubkey_path) if sig_hex else False

    return hash_ok, sig_ok

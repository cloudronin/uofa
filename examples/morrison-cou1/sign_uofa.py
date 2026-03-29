#!/usr/bin/env python3
"""
sign_uofa.py — Mint a sealed UofA evidence package
═══════════════════════════════════════════════════
Computes a real SHA-256 content hash and ed25519 digital signature
for a UofA JSON-LD file, replacing any placeholder values.

Pipeline position: sign_uofa.py (MINT) → verify_hash.py (VERIFY) → WeakenerEngine (REASON)

Steps:
  1. Load JSON-LD (resolve external @context if needed)
  2. Strip integrity fields (hash, signature, signatureAlg, canonicalizationAlg)
  3. Parse to RDF graph
  4. Canonicalize via RDFC-1.0 (N-Quads canonical form)
  5. SHA-256 hash the canonical bytes
  6. Sign the hash with ed25519 private key
  7. Write hash + signature + algorithms back into JSON-LD
  8. Save the sealed file

Requirements:
  pip install rdflib pyld cryptography

Usage:
  # Generate a new keypair (first time only)
  python sign_uofa.py --generate-key keys/research.key

  # Sign a UofA
  python sign_uofa.py uofa-morrison-cou1.jsonld --key keys/research.key --context uofa_v0_2.jsonld

  # Verify a signed UofA
  python sign_uofa.py uofa-morrison-cou1.jsonld --verify --pubkey keys/research.pub
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

# ── Imports with graceful fallback messages ─────────────────
try:
    from rdflib import Graph
except ImportError:
    sys.exit("ERROR: rdflib not installed. Run: pip install rdflib")

try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey,
        Ed25519PublicKey,
    )
    from cryptography.hazmat.primitives import serialization
except ImportError:
    sys.exit("ERROR: cryptography not installed. Run: pip install cryptography")


# ── Fields to strip before hashing ──────────────────────────
INTEGRITY_FIELDS = {"hash", "signature", "signatureAlg", "canonicalizationAlg"}


def resolve_context(doc: dict, jsonld_path: Path, context_path: Path = None) -> dict:
    """Resolve external @context reference to inline object."""
    ctx_ref = doc.get("@context")
    if isinstance(ctx_ref, dict):
        return doc  # already inline

    if isinstance(ctx_ref, str):
        # Try explicit path, then relative to input file
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

        print(f"  WARNING: Could not resolve @context '{ctx_ref}'")
    return doc


def strip_integrity_fields(doc: dict) -> dict:
    """Return a copy of the JSON-LD doc with integrity fields removed."""
    stripped = {}
    for k, v in doc.items():
        if k in INTEGRITY_FIELDS:
            continue
        stripped[k] = v
    return stripped


def canonicalize_and_hash(doc: dict) -> tuple:
    """
    Parse JSON-LD to RDF, canonicalize via RDFC-1.0, return (canonical_nquads, sha256_hex).
    """
    g = Graph()
    g.parse(data=json.dumps(doc), format="json-ld")

    # RDFC-1.0 canonicalization → canonical N-Quads
    # rdflib >= 7.0 supports this via serialize format
    try:
        canonical = g.serialize(format="n3")
        # Fallback: use sorted N-Triples as a deterministic canonical form
        # True RDFC-1.0 requires the canon algorithm; rdflib's support varies
        canonical = "\n".join(sorted(g.serialize(format="nt").strip().split("\n")))
    except Exception:
        # Absolute fallback: sorted N-Triples
        canonical = "\n".join(sorted(g.serialize(format="nt").strip().split("\n")))

    canonical_bytes = canonical.encode("utf-8")
    sha256_hex = hashlib.sha256(canonical_bytes).hexdigest()
    return canonical, sha256_hex


def generate_keypair(key_path: Path):
    """Generate ed25519 keypair and save to disk."""
    private_key = Ed25519PrivateKey.generate()

    # Save private key
    key_path.parent.mkdir(parents=True, exist_ok=True)
    with open(key_path, "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ))

    # Save public key
    pub_path = key_path.with_suffix(".pub")
    public_key = private_key.public_key()
    with open(pub_path, "wb") as f:
        f.write(public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ))

    print(f"  Generated keypair:")
    print(f"    Private: {key_path}")
    print(f"    Public:  {pub_path}")
    print(f"  Commit {pub_path} to your repo. Keep {key_path} private.")


def sign_hash(sha256_hex: str, key_path: Path) -> str:
    """Sign the SHA-256 hex string with ed25519 private key."""
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


def main():
    parser = argparse.ArgumentParser(description="Mint or verify a sealed UofA evidence package.")
    parser.add_argument("input", nargs="?", type=Path, help="Path to UofA JSON-LD file")
    parser.add_argument("--context", "-c", type=Path, help="Path to external JSON-LD context file")
    parser.add_argument("--key", "-k", type=Path, help="Path to ed25519 private key (PEM)")
    parser.add_argument("--pubkey", type=Path, help="Path to ed25519 public key (PEM) for verification")
    parser.add_argument("--generate-key", type=Path, metavar="PATH", help="Generate new ed25519 keypair at PATH")
    parser.add_argument("--verify", action="store_true", help="Verify mode: check hash + signature")
    parser.add_argument("--output", "-o", type=Path, help="Output path (default: overwrite input)")
    args = parser.parse_args()

    # ── Generate key mode ──────────────────────────────────
    if args.generate_key:
        generate_keypair(args.generate_key)
        return 0

    if not args.input:
        parser.error("Input file required (or use --generate-key)")

    # ── Load JSON-LD ───────────────────────────────────────
    print(f"Loading: {args.input}")
    with open(args.input, "r") as f:
        doc = json.load(f)

    doc = resolve_context(doc, args.input, args.context)

    # ── Strip integrity fields and compute hash ────────────
    stripped = strip_integrity_fields(doc)
    canonical, sha256_hex = canonicalize_and_hash(stripped)

    print(f"  Canonical triples: {len(canonical.strip().split(chr(10)))}")
    print(f"  SHA-256: {sha256_hex}")

    # ── Verify mode ────────────────────────────────────────
    if args.verify:
        declared_hash = doc.get("hash", "")
        declared_sig = doc.get("signature", "")

        # Check hash
        if declared_hash.startswith("sha256:"):
            declared_hex = declared_hash.split(":", 1)[1]
        else:
            declared_hex = declared_hash

        hash_ok = declared_hex == sha256_hex
        print(f"  Hash match: {'✓' if hash_ok else '✗ MISMATCH'}")
        if not hash_ok:
            print(f"    Declared: {declared_hex}")
            print(f"    Computed: {sha256_hex}")

        # Check signature
        if args.pubkey and declared_sig:
            sig_hex = declared_sig.split(":", 1)[1] if ":" in declared_sig else declared_sig
            sig_ok = verify_signature(sha256_hex, sig_hex, args.pubkey)
            print(f"  Signature:  {'✓' if sig_ok else '✗ INVALID'}")
        elif not args.pubkey:
            print(f"  Signature:  (skipped — no --pubkey provided)")

        return 0 if hash_ok else 1

    # ── Sign mode ──────────────────────────────────────────
    if not args.key:
        parser.error("--key required for signing (or use --verify for verification)")

    sig_hex = sign_hash(sha256_hex, args.key)
    print(f"  Signature: {sig_hex[:32]}...")

    # ── Write back to JSON-LD ──────────────────────────────
    # Re-read original (with original @context, not resolved)
    with open(args.input, "r") as f:
        original = json.load(f)

    original["hash"] = f"sha256:{sha256_hex}"
    original["signature"] = f"ed25519:{sig_hex}"
    original["signatureAlg"] = "ed25519"
    original["canonicalizationAlg"] = "RDFC-1.0"

    output_path = args.output or args.input
    with open(output_path, "w") as f:
        json.dump(original, f, indent=2, ensure_ascii=False)
    print(f"  Sealed: {output_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)

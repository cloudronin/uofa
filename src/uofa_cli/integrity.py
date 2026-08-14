"""Cryptographic integrity operations for UofA evidence packages.

Provides hashing, signing, and verification for UofA JSON-LD files.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization

# ── Fields stripped before hashing ─────────────────────────────

INTEGRITY_FIELDS = {"hash", "signature", "signatureAlg", "canonicalizationAlg"}

# Honest label for what canonicalize_and_hash actually does: sorted-key compact
# JSON, NOT RDF Dataset Canonicalization. This field was previously mislabeled
# "RDFC-1.0" — a claim the code never implemented. Adopting a standardized
# canonicalization (RFC 8785 JCS / RDFC) is a separate, later capability
# decision; this names the scheme truthfully in the meantime.
CANONICALIZATION_ALG = "json-sortkeys/v1"


def _local_context_for_url(url: str) -> Path | None:
    """Map a published context URL back to the file in this checkout.

    Packages in the wild reference the raw.githubusercontent URL rather than a
    relative path. Without this they cannot be resolved offline at all, and the
    only thing that made them hash correctly was falling back to whatever
    context the toolchain happened to point at -- which is the coupling this
    function exists to remove.
    """
    marker = "/spec/context/"
    if not url.startswith("http") or marker not in url:
        return None
    name = url.rsplit("/", 1)[-1]
    if not name.endswith(".jsonld"):
        return None
    try:
        from uofa_cli import paths
        candidate = paths.find_repo_root() / "spec" / "context" / name
    except Exception:
        return None
    return candidate if candidate.exists() else None


def resolve_context(doc: dict, jsonld_path: Path, context_path: Path = None) -> dict:
    """Resolve external @context reference to inline object.

    **The document's own @context wins.** The inlined context is part of what
    gets canonicalized and hashed, so whichever file is chosen here decides the
    package's hash and therefore whether its signature verifies. Preferring the
    caller's context over the document's made a package's hash a property of
    the tool that happened to read it rather than of the document: moving the
    toolchain's default context re-hashed every package that had been signed
    against a different one, and 5 of the shipped examples failed verification
    on exactly that.

    Order, most specific first:

    1. ``context_path`` when the caller passed one **explicitly** (``--context``
       is a deliberate override and still wins),
    2. the document's own reference, as a path relative to the document,
    3. the document's own reference, when it is a published context URL that
       maps to a file in this checkout,
    4. ``context_path`` as a fallback for documents that name no context.

    Forces UTF-8 decoding of the @context file: JSON-LD documents are
    UTF-8 by spec, but Python's bare ``open(p, "r")`` uses the locale
    default encoding. On Windows that's cp1252, which mis-decodes
    multi-byte UTF-8 sequences (e.g., em-dash U+2014) into different
    code points. The resulting parsed dict differs across platforms,
    canonicalization produces different bytes, and the package's
    hash + signature both fail on Windows. Pinning UTF-8 makes the
    canonical-hash / signature computation platform-independent.
    """
    ctx_ref = doc.get("@context")
    if isinstance(ctx_ref, dict):
        return doc

    # A document that names no context has nothing to resolve, and inlining one
    # anyway would change its hash. Two shipped nasa-7009b packages are signed
    # in exactly that state.
    if not isinstance(ctx_ref, str):
        return doc

    candidates: list[Path] = []
    if context_path is not None:
        # An explicit --context. Callers must pass None when the user did not
        # give one, or this collapses back into "the tool decides", which is
        # the bug this ordering exists to fix.
        candidates.append(Path(context_path))
    candidates.append(jsonld_path.parent / ctx_ref)
    mapped = _local_context_for_url(ctx_ref)
    if mapped is not None:
        candidates.append(mapped)
    if context_path is None:
        # Last resort for a reference this checkout cannot resolve at all.
        try:
            from uofa_cli import paths
            candidates.append(paths.context_file())
        except Exception:
            pass

    for p in candidates:
        try:
            if not p.exists():
                continue
        except OSError:
            # A long or malformed relative reference can raise rather than
            # return False; treat it as simply not resolvable.
            continue
        with open(p, "r", encoding="utf-8") as f:
            ctx_doc = json.load(f)
        doc["@context"] = ctx_doc.get("@context", ctx_doc)
        return doc

    return doc


def strip_integrity_fields(doc: dict) -> dict:
    """Return a copy with integrity fields removed."""
    return {k: v for k, v in doc.items() if k not in INTEGRITY_FIELDS}


def canonicalize_and_hash(doc: dict) -> tuple[str, str]:
    """Serialize as sorted-key compact JSON and SHA-256 it. Returns (canonical_str, hex_digest).

    Scheme (``CANONICALIZATION_ALG`` = ``json-sortkeys/v1``): UTF-8, keys sorted
    lexicographically, ``,``/``:`` separators, no ASCII escaping. This operates on
    the JSON *serialization*, NOT RDF/JSON-LD canonicalization — it is sensitive
    to JSON structure, not RDF semantics. Adopting RFC 8785 JCS or RDF Dataset
    Canonicalization is a separate, later decision.
    """
    canonical = json.dumps(doc, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    canonical_bytes = canonical.encode("utf-8")
    sha256_hex = hashlib.sha256(canonical_bytes).hexdigest()
    return canonical, sha256_hex


def generate_keypair(key_path: Path, *, force: bool = False):
    """Generate ed25519 keypair and save to disk. Returns (key_path, pub_path).

    Refuses to clobber existing key material unless ``force``. Overwriting a
    signing key silently invalidates every package already signed with it, and
    the damage surfaces much later as an unexplained "Signature valid: False"
    with nothing pointing back at the cause.

    Both halves are checked, not just the private one: ``pub_path`` is derived
    with ``with_suffix``, so ``keygen keys/research`` collides only on
    ``keys/research.pub`` while writing an extensionless private key that no
    ``*.key`` ignore rule matches.

    The private key is created 0600 rather than chmod-ed after writing, which
    would leave a window where it is world-readable.
    """
    key_path = Path(key_path)
    pub_path = key_path.with_suffix(".pub")

    if not force:
        clashes = [p for p in (key_path, pub_path) if p.exists()]
        if clashes:
            raise FileExistsError(
                "refusing to overwrite existing key material: "
                + ", ".join(str(p) for p in clashes)
                + " — every package signed with it would stop verifying. "
                "Pass --force to rotate deliberately."
            )

    private_key = Ed25519PrivateKey.generate()

    key_path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(key_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ))
    # O_CREAT's mode is ignored when the file already existed (the --force
    # path), so restate it unconditionally.
    os.chmod(key_path, 0o600)

    public_key = private_key.public_key()
    with open(pub_path, "wb") as f:
        f.write(public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ))

    return key_path, pub_path


def sign_hash(sha256_hex: str, key_path: Path = None, *, key_bytes: bytes = None) -> str:
    """Sign the SHA-256 hex *string* with an ed25519 private key. Returns signature hex.

    Note: the signature is over the lowercase hex-string bytes (``sha256_hex``
    UTF-8 encoded), NOT the raw 32-byte digest. This is intentional and
    self-consistent (``verify_signature`` reconstructs the same hex string), but
    it is non-standard — an external verifier expecting ed25519-over-digest-bytes
    must hex-encode the digest first.

    ``key_bytes`` supplies the PEM directly, for deployments that receive the
    private key as a secret and must not write it to a filesystem the process
    also serves files from. Exactly one of ``key_path`` / ``key_bytes``.
    """
    if (key_path is None) == (key_bytes is None):
        raise ValueError("sign_hash requires exactly one of key_path or key_bytes")

    pem = key_bytes if key_bytes is not None else Path(key_path).read_bytes()
    private_key = serialization.load_pem_private_key(pem, password=None)

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

    Forces UTF-8 decoding of the input file: see ``resolve_context``
    docstring for the Windows / cp1252 cross-platform-hash bug this
    avoids.
    """
    with open(input_path, "r", encoding="utf-8") as f:
        doc = json.load(f)

    resolved = resolve_context(doc.copy(), input_path, context_path)
    stripped = strip_integrity_fields(resolved)
    canonical, sha256_hex = canonicalize_and_hash(stripped)
    return doc, canonical, sha256_hex


def sign_file(input_path: Path, key_path: Path = None, context_path: Path = None,
              output_path: Path = None, *, key_bytes: bytes = None) -> tuple[str, str]:
    """Sign a UofA file in place. Returns (hash_hex, signature_hex).

    Purely cryptographic by design: this signs whatever it is handed. Callers
    that must also enforce *what may be signed* (synthetic samples, issuer-key
    scope) should go through ``package_policy.sign_package`` instead.
    """
    doc, canonical, sha256_hex = load_and_hash(input_path, context_path)
    sig_hex = sign_hash(sha256_hex, key_path, key_bytes=key_bytes)

    # Re-read original (preserves original @context reference). UTF-8
    # for the same cross-platform hash-stability reason — and the
    # paired write below uses the same encoding so round-trip is clean.
    with open(input_path, "r", encoding="utf-8") as f:
        original = json.load(f)

    original["hash"] = f"sha256:{sha256_hex}"
    original["signature"] = f"ed25519:{sig_hex}"
    original["signatureAlg"] = "ed25519"
    original["canonicalizationAlg"] = CANONICALIZATION_ALG

    out = output_path or input_path
    with open(out, "w", encoding="utf-8") as f:
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

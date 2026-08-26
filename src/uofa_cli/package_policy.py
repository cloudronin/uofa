"""What may be signed, and by whom. The single definition of package refusal.

``integrity`` is purely cryptographic on purpose: it will sign whatever bytes it
is handed. The refusals that make signing *meaningful* -- no synthetic
adversarial samples (v1.1 section 10.2), no issuer key over a human decision
(AGENTS.md section 12) -- lived only inside the argparse command modules, as
**two different implementations** of the same predicate:

    commands/sign.py:56    _is_synthetic(path: Path) -> bool    # reads the file
    commands/verify.py:112 _is_synthetic(doc: dict|None) -> bool  # takes a dict

Any non-CLI caller -- the demo Space, a notebook, a future service -- that
reached for ``integrity.sign_file`` directly got the cryptography and none of
the policy. This module is the seam that makes that impossible, following the
precedent of ``report_state`` (shared by the CLI and the Space so the two
"cannot drift").

Two tiers, because they answer different questions:

- ``assert_signable``  -- may this document be signed *at all*? Used by
  ``uofa sign``, where the key belongs to the person running the command.
- ``assert_issuable``  -- may an *issuer-held* key sign this? Strictly stronger.
  Used by ``sign_package``, the only entry point a hosted service should call.
  Adds the section 12 boundary: an issuer key attests "these bytes are what we
  emitted," and must never end up attesting over someone's judgment.
"""

from __future__ import annotations

import json
from pathlib import Path

from uofa_cli import integrity

# The block a human signs with their own key to record a judgment. An
# issuer-held key must never produce a whole-document signature that spans one:
# `uofa decision` deliberately signs it under its own narrow scope and leaves
# the document's own signature alone (see interrogate/signing.py).
#: Imported, never redefined. This constant was declared here AND in
#: `interrogate/forbidden.py`, two copies of one wire term -- the same drift
#: hazard that let the guard know `hasDecisionRecord` while the product emitted
#: `hasDecisionRecord`. `forbidden` owns the action-region family and imports
#: nothing from this package, so it is the safe single home.
from uofa_cli.interrogate.forbidden import DECISION_BLOCK_KEY

SYNTHETIC_TYPE = "uofa:SyntheticAdversarialSample"


class PackagePolicyError(RuntimeError):
    """A document that policy refuses to sign. Carries a user-facing reason."""

    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


def is_synthetic(doc: dict | None) -> bool:
    """True for adversarial samples, which are not evidence and cannot be signed.

    The single definition. Accepts a parsed document (not a path) so the same
    predicate serves sign, verify, and the issuer path without re-reading files.
    """
    if not doc:
        return False
    if doc.get("synthetic") is True:
        return True
    type_val = doc.get("type") or doc.get("@type") or []
    if isinstance(type_val, str):
        type_val = [type_val]
    return SYNTHETIC_TYPE in type_val


def load_doc(path: Path) -> dict | None:
    """Parse a package, or None if it is unreadable or not an object.

    Policy treats unreadable input as "no signal" rather than an error: the
    caller's own error handling (or the signer itself) reports the real problem.
    """
    try:
        doc = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return None
    return doc if isinstance(doc, dict) else None


def assert_signable(doc: dict | None) -> None:
    """Raise PackagePolicyError if this document must not be signed by anyone.

    Preserves exactly the refusal `uofa sign` has always applied; this function
    is where it now lives rather than a new restriction.
    """
    if is_synthetic(doc):
        raise PackagePolicyError(
            "refusing to sign a synthetic adversarial sample. "
            "Synthetic packages are not valid evidence and cannot be signed."
        )


def assert_issuable(doc: dict | None) -> None:
    """Raise PackagePolicyError if an *issuer-held* key must not sign this.

    Strictly stronger than assert_signable. The added refusal is the AGENTS.md
    section 12 boundary: UofA may attest that a package is the one it emitted,
    and may never hold a key that ends up attesting over a human's decision. A
    whole-document signature spans every field, so a document carrying a
    decision block cannot be issuer-signed without confusing the two scopes.

    Nothing in the current build path emits a decision block -- but that is an
    emergent property of today's code, not a contract, which is why it is
    checked here rather than assumed.
    """
    assert_signable(doc)
    if doc and DECISION_BLOCK_KEY in doc:
        raise PackagePolicyError(
            f"refusing to issuer-sign a package carrying a {DECISION_BLOCK_KEY!r} "
            f"block. An issuer key attests provenance, never a human judgment "
            f"(AGENTS.md section 12). Sign the decision with the engineer's own "
            f"key via `uofa decision`, which scopes its signature to the block."
        )


def sign_package(
    jsonld_path: Path,
    key_path: Path | None = None,
    *,
    key_bytes: bytes | None = None,
    context_path: Path | None = None,
    output_path: Path | None = None,
) -> tuple[str, str]:
    """Policy-checked signing. The only signer a UI or service should call.

    Returns (sha256_hex, signature_hex). Raises PackagePolicyError before any
    cryptography happens, so a refused document is never partially signed.

    ``key_bytes`` accepts a PEM in memory, for deployments that receive the
    private key as a secret env var and should not write it to disk.
    """
    doc = load_doc(jsonld_path)
    assert_issuable(doc)
    return integrity.sign_file(
        Path(jsonld_path), key_path,
        context_path=context_path, output_path=output_path, key_bytes=key_bytes,
    )


def sign_package_scoped(
    jsonld_path: Path,
    *,
    issuer_key_path: Path | None = None,
    issuer_key_bytes: bytes | None = None,
    reviewer_key_path: Path | None = None,
    reviewer_key_bytes: bytes | None = None,
    now: str | None = None,
) -> dict:
    """The two-scope act for a service. Returns a summary dict.

    `sign_package` produces ONE signature over the whole document, which is
    correct only when there is no decision layer -- and `assert_issuable` refuses
    it otherwise, so a hosted product emitting decision records has no path
    through it at all. This is that path, and it is here rather than in the CLI
    because `package_policy` is the door a UI or service is supposed to enter by.

    Two scopes, in the only order that works:

    1. the **issuer seal** over the measurement view (document minus integrity
       fields minus the decision layer), so it survives a decision arriving later;
    2. a **decision signature** per asserted record, binding the recomputed
       measurement hash.

    Atomic: both land or the file is untouched. A package sealed but with its
    verdict unsigned states something nobody meant, and is indistinguishable
    from one whose reviewer simply has not signed yet.

    A reviewer key is optional. Without one the package is sealed and honestly
    incomplete -- `uofa check` reports the decision layer as owed -- which is the
    lawful multi-party state, not a failure.
    """
    import json as _json
    import os as _os
    import tempfile as _tempfile
    from datetime import datetime, timezone

    from uofa_cli import sign_roles
    from uofa_cli.integrity import sign_hash
    from uofa_cli.interrogate.signing import measurement_hash

    if (issuer_key_path is None) == (issuer_key_bytes is None):
        raise ValueError("exactly one of issuer_key_path / issuer_key_bytes")

    path = Path(jsonld_path)
    doc = load_doc(path)
    stamp = now or (datetime.now(timezone.utc).replace(microsecond=0)
                    .isoformat().replace("+00:00", "Z"))

    unclassified = sign_roles.unclassified_records(doc)
    if unclassified:
        raise PackagePolicyError(
            f"this package carries {len(unclassified)} decision record(s) whose "
            f"provenance is unstated. The fork says which warrant is owed, so "
            f"there is nothing to check the record against.")

    # **Route on what the package carries, exactly as verify does.** With no
    # decision layer the whole document IS the measurement view, and the bare
    # signature is the issuer seal under another name -- byte-identical to
    # pre-consolidation output and regression-pinned. Using the measurement-view
    # hash unconditionally would seal decision-free packages under a scope no
    # verifier checks them against: correctly signed, and reported broken.
    if not sign_roles.has_decision_layer(doc):
        from uofa_cli.integrity import sign_file

        sha, _sig = sign_file(path, issuer_key_path, key_bytes=issuer_key_bytes)
        return {
            "package_hash": sha,
            "decision_records_signed": 0,
            "decision_signatures_owed": 0,
            "complete": True,
        }

    sha = measurement_hash(doc)
    doc["hash"] = f"sha256:{sha}"
    doc["signature"] = "ed25519:" + (
        sign_hash(sha, key_bytes=issuer_key_bytes) if issuer_key_bytes
        else sign_hash(sha, Path(issuer_key_path)))

    signed_records = 0
    owed = len(sign_roles.unsigned_asserted(doc))
    if reviewer_key_path is not None or reviewer_key_bytes is not None:
        if owed:
            signed_records = sign_roles.sign_decision_records(
                doc, reviewer_key_path, sign_roles.REVIEWER,
                now=stamp, key_bytes=reviewer_key_bytes)
            owed = len(sign_roles.unsigned_asserted(doc))

    # Temp-file-and-rename: no half-attested artifact ever exists on disk.
    fd, tmp = _tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with _os.fdopen(fd, "w", encoding="utf-8") as fh:
            _json.dump(doc, fh, indent=2, ensure_ascii=False)
        _os.replace(tmp, path)
    except BaseException:
        _os.unlink(tmp)
        raise

    return {
        "package_hash": sha,
        "decision_records_signed": signed_records,
        "decision_signatures_owed": owed,
        "complete": owed == 0,
    }

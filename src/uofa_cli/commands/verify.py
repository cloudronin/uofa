"""uofa verify — verify hash and signature of a UofA file.

Adds a synthetic-sample pre-check and a provenance-block tamper check
(v1.1 §10.2). If an ``adversarialProvenance`` block is present, verify
recomputes its hash and warns on mismatch OR on a stripped synthetic
flag, then refuses.
"""

from __future__ import annotations

import json
from pathlib import Path

from uofa_cli.integrity import verify_file
from uofa_cli.output import error, info, result_line, step_header, warn
from uofa_cli import paths

HELP = "verify hash + ed25519 signature (C1 integrity)"

_PROVENANCE_BLOCK_KEY = "adversarialProvenance"


def add_arguments(parser):
    parser.add_argument("file", type=Path, help="UofA JSON-LD file to verify")
    parser.add_argument("--pubkey", type=Path, help="ed25519 public key (default: keys/research.pub)")
    parser.add_argument("--context", "-c", type=Path, help="JSON-LD context file")
    parser.add_argument("--decision-pubkey", type=Path,
                        help="engineer's public key, to verify a SIP engineerDecision signature (Addendum A6)")


def run(args) -> int:
    if not args.file.exists():
        raise FileNotFoundError(f"File not found: {args.file}")

    # Synthetic pre-check + provenance-block tamper detection.
    doc = _safe_load(args.file)
    tampered = False
    if doc is not None:
        tampered = _warn_on_tampering(doc)

    if _is_synthetic(doc):
        error("refusing to verify a synthetic adversarial sample.")
        return 2
    if tampered:
        # Provenance block present but synthetic marker stripped. The
        # tamper warnings have already printed "hash does not match …".
        error("refusing to verify a tampered synthetic sample.")
        return 2

    pubkey = args.pubkey or paths.default_pubkey()
    if not pubkey.exists():
        raise FileNotFoundError(f"Public key not found: {pubkey}")

    # SIP evidence bundles carry two independent signatures with two scopes
    # (Addendum A6); route them through the dual-signature path.
    from uofa_cli.interrogate.signing import is_sip_bundle
    if doc is not None and is_sip_bundle(doc):
        return _verify_sip(args, doc, pubkey)

    ctx = args.context or paths.context_file()
    step_header("C1: Integrity verification (hash + signature)")

    hash_ok, sig_ok = verify_file(args.file, pubkey, ctx)

    result_line("Hash match", hash_ok)
    result_line("Signature valid", sig_ok)

    return 0 if (hash_ok and sig_ok) else 1


def _verify_sip(args, doc: dict, measurement_pubkey: Path) -> int:
    """Verify a SIP bundle's measurement signature and, independently, any
    engineer decision signature (Addendum A6).

    Only the measurement signature gates the package. A missing, unsupplied-key,
    mis-scoped, or unverifiable decision signature is surfaced as "no engineer
    decision" — never as a failure of the whole package (A6 step 3 / A10).
    """
    from uofa_cli.interrogate import signing

    step_header("C1: SIP integrity (measurement + decision signatures)")
    hash_ok, sig_ok = signing.verify_measurement(doc, measurement_pubkey)
    result_line("Measurement hash match", hash_ok)
    result_line("Measurement signature valid", sig_ok)

    if "engineerDecision" not in doc:
        info("Engineer decision: none present (valid measurement package, no judgment).")
    elif args.decision_pubkey is None:
        info("Engineer decision: present but no --decision-pubkey supplied → treated as no decision.")
    else:
        ok, reason = signing.verify_decision(doc, args.decision_pubkey)
        if ok:
            decided_by = doc["engineerDecision"].get("decidedBy", "")
            result_line("Engineer decision signature valid", True, f"decidedBy {decided_by}")
        else:
            info(f"Engineer decision: not verified → treated as no decision ({reason}).")

    # The measurement signature is the only gate on the package.
    return 0 if (hash_ok and sig_ok) else 1


def _safe_load(path: Path) -> dict | None:
    try:
        doc = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(doc, dict):
        return None
    return doc


def _is_synthetic(doc: dict | None) -> bool:
    if not doc:
        return False
    if doc.get("synthetic") is True:
        return True
    type_val = doc.get("type") or doc.get("@type") or []
    if isinstance(type_val, str):
        type_val = [type_val]
    return "uofa:SyntheticAdversarialSample" in type_val


def _warn_on_tampering(doc: dict) -> bool:
    """Emit tamper warnings based on the adversarialProvenance block state.

    Returns True iff any tamper signal fired. The warning strings all contain
    the substring "hash does not match" so the acceptance test grep works
    regardless of which tamper mode was used (§11.4 step 7).
    """
    block = doc.get(_PROVENANCE_BLOCK_KEY)
    if not isinstance(block, dict):
        return False

    tampered = False
    synth_flag = doc.get("synthetic")

    if synth_flag is not True:
        warn(
            "adversarialProvenance block present but synthetic flag is false or "
            "missing — hash does not match expected synthetic-marker state. "
            "Possible tampering with synthetic flag detection."
        )
        tampered = True

    from uofa_cli.adversarial.hash_utils import verify_provenance_block_hash

    ok, stored, recomputed = verify_provenance_block_hash(block)
    if not ok:
        warn(
            f"package adversarialProvenance block hash does not match stored value.\n"
            f"  stored:     sha256:{stored}\n"
            f"  recomputed: sha256:{recomputed}\n"
            f"  Possible tampering with synthetic flag detection. Refusing to verify."
        )
        tampered = True

    return tampered

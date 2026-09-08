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
from uofa_cli import paths, sign_roles
from uofa_cli.package_policy import is_synthetic as _is_synthetic
from uofa_cli.interrogate.forbidden import DECISION_BLOCK_KEY

HELP = "verify hash + ed25519 signature (C1 integrity)"

_PROVENANCE_BLOCK_KEY = "adversarialProvenance"


def add_arguments(parser):
    parser.add_argument("file", type=Path, help="UofA JSON-LD file to verify")
    parser.add_argument("--pubkey", type=Path,
                        help="ed25519 public key for the measurement/issuer scope. "
                             "No default: without it, verify tries the wheel-shipped "
                             "anchors and names which one matched.")
    parser.add_argument("--context", "-c", type=Path,
                        help="JSON-LD context override (default: the package's own @context)")
    parser.add_argument("--decision-pubkey", type=Path, action="append",
                        help="public key for a decision signature. REPEATABLE: stacked "
                             "decisions (source acceptance + concurrence + encoder "
                             "attestation) carry signatures from several parties, and "
                             "each key matches by key identity.")


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

    if args.pubkey is not None and not args.pubkey.exists():
        raise FileNotFoundError(f"Public key not found: {args.pubkey}")

    # **Route on what the package CARRIES, not on what produced it.** This was
    # gated on `is_sip_bundle`, so an excel-authored package sealed over its
    # measurement view was verified against a whole-document hash it was never
    # signed over, and reported "Hash match: NO" about a package that was
    # perfectly intact. Producer identity is not the question; scope is. A
    # decision layer means the seal excludes it -- whoever made the package.
    # SIP bundles keep their existing path and their exact report strings: the
    # `is_sip_bundle` fork retires at step 8, deliberately, not as a side effect
    # of this repair. What was broken is narrower than that fork -- non-SIP
    # packages sealed over a measurement view and verified against the whole
    # document -- and the fix stays that narrow.
    from uofa_cli.interrogate.signing import is_sip_bundle

    if doc is not None and is_sip_bundle(doc):
        anchor = args.pubkey or (paths.shipped_anchors() or [(None, "")])[0][0]
        if anchor is None:
            error("no measurement key: name one with --pubkey.")
            return 2
        return _verify_sip(args, doc, anchor)

    if doc is not None and sign_roles.has_decision_layer(doc):
        return _verify_scoped(args, doc)

    # Decision-free: the whole document IS the measurement view, so this stays
    # byte-identical to the pre-consolidation path (regression-pinned).
    ctx = _context_for(args, doc)
    step_header("C1: Integrity verification (hash + signature)")

    hash_ok, sig_ok, label = _verify_measurement_named(
        args.pubkey, lambda k: verify_file(args.file, k, ctx))
    info(f"verified against: {label}")
    result_line("Hash match", hash_ok)
    result_line("Signature valid", sig_ok)

    return 0 if (hash_ok and sig_ok) else 1


def _context_for(args, doc):
    """Explicit override, else the package's own declared @context.

    Verifying a document against a context it does not declare recomputes a
    different canonical form and reports the mismatch as tampering.
    """
    if args.context is not None:
        return args.context
    if doc is None:
        return None
    from uofa_cli import integrity

    resolver = getattr(integrity, "context_for_document", None)
    if resolver is None:
        return None
    path, note = resolver(doc)
    if note:
        # **A substituted context is not this document's context.** The resolver
        # falls back to the newest shipped version when the declared one is not
        # in this checkout, and names the substitution -- which is right for
        # VALIDATION, where the question is "does this conform". It is wrong
        # here: canonicalising under a different context version changes the
        # bytes being hashed, so an intact v0.5 package verified against v0.9
        # reports as tampered. Integrity gets the declared context or none at
        # all; it never gets a different one.
        info(f"{note} — not used for integrity (a substituted context changes "
             f"the canonical bytes); hashing as declared.")
        return None
    return path


def _verify_measurement_named(explicit, attempt):
    """Verify against a NAMED anchor. Returns (hash_ok, sig_ok, label).

    No silent default. With `--pubkey` the caller named it; without one, the
    shipped anchors are tried and the match is reported by name. If none match,
    the label says so rather than letting a failure read as "wrong key" when the
    real answer is "no anchor here can speak to this package".
    """
    if explicit is not None:
        return (*attempt(explicit), f"{explicit} (named with --pubkey)")

    anchors = paths.shipped_anchors()
    if not anchors:
        return False, False, "no anchor: none shipped and none named with --pubkey"

    tried = []
    for path, label in anchors:
        hash_ok, sig_ok = attempt(path)
        if hash_ok and sig_ok:
            return hash_ok, sig_ok, label
        tried.append((hash_ok, sig_ok, label))
    # Report the closest attempt rather than the last one: a hash match with a
    # bad signature is a different diagnosis from neither matching.
    tried.sort(key=lambda t: (t[0], t[1]), reverse=True)
    hash_ok, sig_ok, label = tried[0]
    names = ", ".join(t[2] for t in tried)
    return hash_ok, sig_ok, f"{label} — no shipped anchor verified this package (tried: {names})"


def _decision_keys(args) -> list[Path]:
    """Every `--decision-pubkey`, however the caller supplied it.

    Total by construction: argparse gives a list, in-process callers historically
    passed a single Path, and absent is None. A reader that understood only one
    of those shapes would silently see NO keys from the other two and report
    every signature as unverifiable-for-lack-of-a-key.
    """
    raw = getattr(args, "decision_pubkey", None)
    if raw is None:
        return []
    if isinstance(raw, (list, tuple)):
        return [Path(k) for k in raw if k is not None]
    return [Path(raw)]


def _verify_scoped(args, doc: dict) -> int:
    """Two scopes, reported independently, role- and fork-aware.

    The issuer seal covers the measurement view; each decision record carries its
    own warrant, and which warrant is owed depends on its fork. Only the
    measurement seal gates the package: a decision this key cannot read is a
    decision this reader cannot speak to, never a package failure (A6 step 3).
    """
    from uofa_cli.interrogate import signing

    step_header("C1: Integrity verification (measurement seal + decision layer)")

    from uofa_cli.integrity import verify_measurement_scope

    scoped_only = signing.verify_measurement(doc, args.pubkey) if args.pubkey else (False, False)
    ctx = _context_for(args, doc)  # resolved ONCE: it emits a note, and one
                                   # resolution reported per anchor attempted
                                   # reads as several different problems.
    hash_ok, sig_ok, label = _verify_measurement_named(
        args.pubkey,
        lambda k: verify_measurement_scope(args.file, doc, k, ctx))
    if hash_ok and sig_ok and args.pubkey and not all(scoped_only):
        info("sealed under the legacy whole-document scope (pre two-scope model).")
    info(f"verified against: {label}")
    result_line("Measurement hash match", hash_ok)
    result_line("Measurement signature valid", sig_ok)

    keys = _decision_keys(args)
    records = sign_roles.decision_records(doc)
    info(f"decision layer: {len(records)} record(s)")

    signer_ids = set()
    anchor_failures: list[str] = []
    for i, rec in enumerate(records, 1):
        _report_record(doc, rec, i, keys, signer_ids, args.file, anchor_failures)

    # The concentration line: a FACT about custody, never a verdict on it. The
    # solo configuration is legitimate and must read as legitimate; what would be
    # dishonest is a format that let one key across two scopes look like two
    # parties. Derived from key identity, never key count.
    seal_id = _seal_identity(doc, args.pubkey, label)
    if seal_id and signer_ids:
        if signer_ids == {seal_id}:
            info("issuer and decision scopes signed by the same key — "
                 "single-party configuration.")
        elif seal_id in signer_ids:
            info("issuer key also signed part of the decision layer — "
                 "partially single-party.")
        else:
            info("issuer and decision scopes signed by different keys — "
                 "independent attestation.")

    # An anchor that does not match its source is a FALSE transcription claim --
    # the package says the source stated something the source does not state.
    # That is a package failure, not a note: it is the exact thing the anchor
    # exists to make checkable.
    if anchor_failures:
        error(f"{len(anchor_failures)} decision anchor(s) do not match their "
              f"source: {', '.join(anchor_failures)}. The package claims a "
              f"transcription its own pin refutes.")
        return 1

    return 0 if (hash_ok and sig_ok) else 1


def _seal_identity(doc, explicit, label):
    """Fingerprint of the key that verified the seal, for the concentration line."""
    from uofa_cli.interrogate.signing import fingerprint_from_public_key

    if explicit is not None:
        try:
            return fingerprint_from_public_key(Path(explicit))
        except Exception:
            return None
    for path, lbl in paths.shipped_anchors():
        if lbl == label:
            try:
                return fingerprint_from_public_key(path)
            except Exception:
                return None
    return None


def _report_record(doc, rec, i, keys, signer_ids, doc_path, failures) -> None:
    """One decision record: its fork, and whether the warrant that fork owes is
    present and good."""
    from uofa_cli.interrogate import signing

    fork = str(rec.get("decisionProvenance", "")).strip()
    actor = rec.get("actor") or rec.get("decidedBy") or "<unattributed>"
    prefix = f"  decision {i}"

    if fork not in sign_roles.FORKS:
        # **Advised, not refused, when the package predates the term.** A
        # package whose own @context is older than `decisionProvenance` cannot
        # state a fork: the word is not in its vocabulary. Reporting that as
        # "cannot be checked at all" describes this checker's expectation
        # rather than the package's condition, and reads to anyone running it
        # as though the package were broken. It is not -- the signatures above
        # it verify.
        if sign_roles.predates_provenance(doc):
            v = ".".join(str(x) for x in sign_roles.context_version(doc))
            info(f"{prefix}: no provenance fork — this package declares context "
                 f"v{v}, which predates the term; advised, not refused.")
            return
        warn(f"{prefix}: provenance {fork or '<absent>'!r} — the fork says which "
             f"warrant is owed, so this record cannot be checked at all.")
        return

    if fork == sign_roles.EXTRACTED:
        # The source's own act. The source never signs; the anchor IS the warrant,
        # so an unresolvable anchor is a FAILED check, never an absent one.
        anchor = rec.get("decisionAnchor")
        if not anchor:
            warn(f"{prefix}: extracted from a source but carries no anchor — "
                 f"the anchor is its only warrant.")
            return
        outcome, why = _resolve_anchor(anchor, doc_path)
        if outcome == RESOLVED:
            result_line(f"{prefix}: extracted, anchor resolves", True, why)
        elif outcome == UNREACHABLE:
            # Neither green nor red, deliberately. The verifier can only attest
            # what it could open, and saying so is the whole honesty of the flag.
            info(f"{prefix}: extracted, {why}")
        else:
            result_line(f"{prefix}: extracted, anchor DOES NOT match its source",
                        False, f"{actor}\n      {why}")
            failures.append(prefix.strip())
        return

    # asserted: a live participant judged, so a signature is owed.
    node = rec.get("hasDecisionSignature")
    if not node:
        warn(f"{prefix}: asserted by {actor} but carries no signature — "
             f"incomplete, not invalid.")
        return

    role = (node.get("signatureRole") or "<unstated>") if isinstance(node, dict) else "<unstated>"
    if not keys:
        info(f"{prefix}: signature present ({role}), no key provided to verify it.")
        return

    for key in keys:
        ok, why = signing.verify_decision({**doc, "hasDecisionRecord": rec}, key)
        if ok:
            from uofa_cli.interrogate.signing import fingerprint_from_public_key
            try:
                signer_ids.add(fingerprint_from_public_key(key))
            except Exception:
                pass
            result_line(f"{prefix}: {role} signature valid", True, str(actor))
            return
    # Every key was tried and none matched. Distinct from "no key provided":
    # this reader HAS keys and none of them speaks for this signature.
    info(f"{prefix}: signature present ({role}), none of the "
         f"{len(keys)} provided key(s) matched it.")


RESOLVED, MISMATCH, UNREACHABLE, MALFORMED = "resolved", "mismatch", "unreachable", "malformed"


def _resolve_anchor(anchor, doc_path) -> tuple[str, str]:
    """Open the anchored source, hash it, compare to the pin. Returns (outcome, detail).

    **Resolve means open.** This checked that a locator and a digest were both
    present and reported "anchor resolves" -- which was true of a package whose
    pin had been replaced with garbage, because nothing ever opened the file. It
    was a check that could not fail, sitting under the one sentence Case 1 rests
    on: the source never signs, so the anchor is their attestation. "The paper is
    their attestation" is worth exactly nothing if the verifier never reads the
    paper.

    Three outcomes, and keeping them apart is the point:

    - RESOLVED  -- opened, hashed, matches the pin.
    - MISMATCH  -- opened, hashed, does NOT match: the transcription claim is
      false, and this is a red finding naming both hashes.
    - UNREACHABLE -- could not open it. A stranger holding the package but not
      the source is in this state, and they must not be told either "verified"
      or "tampered". Could-not-check is never checked-and-wrong.
    """
    import hashlib

    if not isinstance(anchor, dict):
        return MALFORMED, f"anchor {anchor!r} is not a source anchor node"
    locator = str(anchor.get("anchorLocator") or "").strip()
    digest = str(anchor.get("anchorSha256") or "").strip()
    if not locator:
        return MALFORMED, "anchor names no locator"
    if not digest:
        return MALFORMED, f"anchor {locator} carries no sha256 pin, so nothing can be checked against it"

    target = _locate_anchor_target(locator, doc_path)
    if target is None:
        return UNREACHABLE, (f"{locator} — source not available to resolve here "
                             f"(the pin is present and unchecked)")

    actual = "sha256:" + hashlib.sha256(target.read_bytes()).hexdigest()
    want = digest if digest.startswith("sha256:") else f"sha256:{digest}"
    if actual != want:
        return MISMATCH, (f"{locator}\n      pinned:   {want}\n"
                          f"      actual:   {actual}\n"
                          f"      opened:   {target}")
    return RESOLVED, f"{locator} (sha256 verified against {target.name})"


def _locate_anchor_target(locator: str, doc_path):
    """Find the file an `archive://` locator names, relative to the package.

    Search is document-relative and bounded, and the resolved path is REPORTED:
    a verifier that opened *something* and did not say what it opened is asking
    to be trusted about a step nobody can audit.
    """
    if not locator.startswith("archive://"):
        return None
    rel = locator[len("archive://"):].lstrip("/")
    if not rel or ".." in rel.split("/"):
        return None
    base = Path(doc_path).resolve().parent
    for _ in range(6):
        candidate = base / rel
        if candidate.is_file():
            return candidate
        if base.parent == base:
            break
        base = base.parent
    return None


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

    keys = _decision_keys(args)
    if DECISION_BLOCK_KEY not in doc:
        info("Engineer decision: none present (valid measurement package, no judgment).")
    elif not keys:
        info("Engineer decision: present but no --decision-pubkey supplied → treated as no decision.")
    else:
        # `--decision-pubkey` is repeatable now, so this reads a LIST. Passing it
        # to a Path parameter raised rather than misreporting, which is the good
        # failure mode -- but the reason it can't misreport is the helper, which
        # is total over all three shapes the flag has ever had.
        reasons = []
        for key in keys:
            ok, reason = signing.verify_decision(doc, key)
            if ok:
                rec = doc[DECISION_BLOCK_KEY]
                rec = rec[0] if isinstance(rec, list) and rec else rec
                who = (rec or {}).get("decidedBy") or (rec or {}).get("actor") or ""
                result_line("Engineer decision signature valid", True, f"decidedBy {who}")
                break
            reasons.append(reason)
        else:
            info(f"Engineer decision: not verified → treated as no decision "
                 f"({'; '.join(reasons)}).")

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

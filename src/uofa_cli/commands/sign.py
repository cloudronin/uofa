"""uofa sign — sign a UofA evidence package with ed25519.

Synthetic adversarial samples are refused (v1.1 §10.2). The ``integrity``
helpers stay purely cryptographic; the refusal is policy, and it now lives in
``package_policy`` so that every signer — this command, the demo Space, any
future service — applies the same one. It used to be a private predicate here,
with a second, separately-written copy in ``verify.py``.
"""

from __future__ import annotations

from pathlib import Path

from uofa_cli import package_policy, sign_roles
from uofa_cli.integrity import sign_file
from uofa_cli.output import error, info, result_line, step_header, warn

HELP = "sign (or re-sign) a UofA file"


def add_arguments(parser):
    parser.add_argument("file", type=Path, help="UofA JSON-LD file to sign")
    parser.add_argument("--key", "-k", type=Path, required=True, help="ed25519 private key (PEM)")
    parser.add_argument("--context", "-c", type=Path, help="JSON-LD context file")
    parser.add_argument("--output", "-o", type=Path, help="output path (default: overwrite input)")
    parser.add_argument(
        "--as", dest="roles", default="", metavar="ROLES",
        help="comma-separated signing roles: "
             + ", ".join(sign_roles.ROLES)
             + ". One party signing both scopes uses one invocation "
               "(`--as issuer,deciding-engineer`); separate parties use "
               "separate invocations with their own keys.")


def run(args) -> int:
    if not args.file.exists():
        raise FileNotFoundError(f"File not found: {args.file}")
    if not args.key.exists():
        raise FileNotFoundError(
            f"Private key not found: {args.key}. Generate one: uofa keygen {args.key}"
        )

    doc = package_policy.load_doc(args.file)

    try:
        roles = sign_roles.parse_roles(getattr(args, "roles", ""))
        sign_roles.assert_key_matches_roles(args.key, roles)
    except sign_roles.RoleError as exc:
        error(str(exc))
        return 2

    # **Synthetic first, before any scope reasoning.** An adversarial sample is
    # unsignable in EVERY scope, so asking "which scope?" about one is already
    # the wrong conversation. Ordering this after the decision-layer guard made
    # the synthetic refusal unreachable for any sample carrying a decision
    # record -- and worse, the message told the operator to add `--as`, which
    # reads as "you are one flag away from signing this". They are not.
    try:
        package_policy.assert_signable(doc)
    except package_policy.PackagePolicyError as exc:
        error(exc.reason)
        return 2

    records = sign_roles.decision_records(doc)

    # **Bare `sign` on a decision-carrying package refuses, and teaches.** The
    # whole document is the measurement view only when there is no decision
    # layer in it; otherwise an unscoped signature would span a human judgment.
    if not roles and records:
        error(
            "this package carries a decision record, so an unscoped signature "
            "would span a human judgment. Name the scope with `--as`: "
            f"{', '.join(sign_roles.ROLES)}. To seal only the measurement view, "
            "use `--as issuer`.")
        return 2

    # `--as issuer` alone must never seal around a verdict nobody signed. An
    # `extracted` record is fine here: its actor is the source's, the source
    # never signs, and its warrant is the anchor.
    if roles == (sign_roles.ISSUER,):
        # Totality first: a record with no fork is not "not asserted", it is
        # unclassified, and exempting it let omission walk past this gate.
        unclassified = sign_roles.unclassified_records(doc)
        if unclassified:
            forms = sorted({str(r.get("decisionProvenance") or "<absent>")
                            for r in unclassified})
            error(
                f"this package carries {len(unclassified)} decision record(s) "
                f"whose provenance is {', '.join(repr(f) for f in forms)}. The "
                f"fork says which warrant is owed -- a signature for `asserted`, "
                f"a sha-pinned anchor for `extracted` -- so without it there is "
                f"nothing to check the record against. Refusing to seal around "
                f"a verdict whose warrant is unstated.")
            return 2

        # **A warning, not a refusal, and the architecture is why.** The seal
        # never wraps the decision at all: the measurement view excludes it by
        # construction, which is A6's whole purpose and the property pinned by
        # `test_a_seal_survives_a_decision_added_afterwards`. Refusing here made
        # the lawful multi-party order -- seal first, decision after, seal
        # survives -- unreachable, and deadlocked both parties in both orders:
        # the issuer could not seal until the reviewer signed, and the reviewer
        # could not sign until a seal existed.
        #
        # "Is every asserted record signed?" is a COMPLETENESS question, owned by
        # `uofa check` and the export gates -- the same layer-vs-record split
        # already ruled for encoder attestation. The signer states the fact; the
        # completeness gate enforces it.
        unsigned = sign_roles.unsigned_asserted(doc)
        if unsigned:
            warn(
                f"sealing with {len(unsigned)} unsigned asserted decision "
                f"record(s); decision signature owed. The seal covers the "
                f"measurement view only and survives the decision arriving "
                f"later -- but this package is INCOMPLETE until its decider "
                f"signs, and `uofa check` refuses it as such.")

    try:
        if not roles:
            # **Only the unscoped path.** `assert_issuable` refuses a
            # WHOLE-DOCUMENT signature over a decision block, and that is
            # exactly what a bare `sign` produces. `--as issuer` signs the
            # measurement view instead -- document minus integrity fields minus
            # the decision layer -- so the judgment is excluded by construction
            # and the guard's premise does not hold. Applying it there would
            # refuse Morrison's shape, which the constitution permits: the seal
            # never touches the decision, and the extracted record's warrant is
            # its anchor.
            package_policy.assert_issuable(doc)
    except package_policy.PackagePolicyError as exc:
        error(exc.reason)
        return 2

    # Explicit override only: resolve_context prefers the package's own
    # @context when the user did not name one.
    ctx = args.context

    if not roles:
        step_header(f"Signing {args.file.name}")
        # The ordinary path, byte-identical to before the consolidation: with no
        # decision layer the whole document IS the measurement view, so this is
        # the issuer seal under another name.
        sha256_hex, sig_hex = sign_file(args.file, args.key, ctx, args.output)
        result_line("Signed", True)
        info(f"SHA-256: {sha256_hex}")
        info(f"Signature: {sig_hex[:32]}...")
        info(f"Sealed: {args.output or args.file}")
        return 0

    try:
        return _sign_with_roles(args, doc, roles)
    except sign_roles.RoleError as exc:
        error(str(exc))
        return 2


def _sign_with_roles(args, doc: dict, roles) -> int:
    """Scoped signing, and **atomic** when one party wears two hats.

    Both signatures land or neither touches disk. A half-attested artifact --
    sealed but with its verdict unsigned, or the reverse -- is a package that
    states something nobody meant, and it would be indistinguishable from one
    where the second party simply hasn't signed yet.
    """
    import datetime
    import json
    import os
    import tempfile

    from uofa_cli.interrogate.signing import measurement_hash, sign_measurement

    target = Path(args.output or args.file)
    now = datetime.datetime.now(datetime.timezone.utc).replace(
        microsecond=0).isoformat().replace("+00:00", "Z")

    decision_roles = [r for r in roles if r in sign_roles.DECISION_ROLES]
    step_header(f"Signing {args.file.name} as {', '.join(roles)}")

    if sign_roles.ISSUER in roles:
        sha = measurement_hash(doc)
        from uofa_cli.integrity import sign_hash
        doc["hash"] = f"sha256:{sha}"
        doc["signature"] = f"ed25519:{sign_hash(sha, Path(args.key))}"
        doc["signatureAlg"] = "ed25519"
        result_line("Issuer seal (measurement view)", True)
        info(f"SHA-256: {sha}")
    elif decision_roles:
        # A decision signature binds the recomputed measurement hash, so the
        # seal must already exist and verify -- A6's stale-bundle rule.
        sign_roles.assert_measurement_seal_present(doc)

    for role in decision_roles:
        n = sign_roles.sign_decision_records(doc, args.key, role, now=now)
        result_line(f"Decision signature ({role})", True)
        info(f"records signed: {n}")

    # temp-file-and-rename: no half-attested artifact ever exists on disk.
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(target.parent), suffix=".part")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(doc, fh, indent=2, ensure_ascii=False)
        os.replace(tmp, target)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise

    info(f"Sealed: {target}")
    return 0

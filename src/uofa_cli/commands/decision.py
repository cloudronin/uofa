"""uofa decision — git-shaped review-and-sign for a SIP evidence bundle.

Modeled on `git diff` then `git commit -S`: the tool states facts and verifies;
the engineer decides and signs. Two subcommands, two moments, by design — there
is no fused measure-and-sign step (that would be the tool deciding, the breach).

- `uofa decision review <pkg>` — read-only. Prints the surrogate-vs-reference
  comparison and stops. No key, no prompts, no commentary, no suggested verdict
  (Addendum A14.2 terminal silence).
- `uofa decision record <pkg> --criterion … --value <accepted|not-accepted>
  --rationale … --key <engineer-key>` — re-verifies SIP's measurement signature
  (stale-bundle refusal, A11), then writes the engineer's signed `hasDecisionRecord`
  block. `--key` is REQUIRED with no default/fallback; there is no headless/batch
  mode and no default decider identity (A8). The tool never suggests or defaults
  the criterion or value; `accepted` and `not-accepted` are symmetric.

UofA never holds the engineer's key (A7) — `--key` is consumed, never stored.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from uofa_cli.output import error, info, result_line, step_header
from uofa_cli.interrogate.forbidden import DECISION_BLOCK_KEY

HELP = "review a SIP comparison (read-only) or sign an engineer decision"

_VALUE_MAP = {"accepted": "Accepted", "not-accepted": "Not accepted", "conditional": "Conditional"}


def add_arguments(parser):
    sub = parser.add_subparsers(dest="decision_cmd", title="decision commands")

    review = sub.add_parser("review", help="print the surrogate-vs-reference comparison (read-only)")
    review.add_argument("file", type=Path, help="SIP evidence bundle (.json)")

    record = sub.add_parser(
        "record", help="author a decision record into the bundle (no signature)")
    record.add_argument("file", type=Path, help="evidence bundle (.json/.jsonld)")
    record.add_argument("--criterion", required=True,
                        help="the acceptance criterion this judgment is against")
    record.add_argument("--value", required=True,
                        choices=["accepted", "not-accepted", "conditional"],
                        help="the judgment (no default; accepted and not-accepted are symmetric)")
    record.add_argument("--actor", required=True,
                        help="who decided: an org-scoped handle IRI (https://…/org/<handle>)")
    record.add_argument("--rationale", default=None, help="short free-text rationale")
    record.add_argument("--decided-at", default=None,
                        help="ISO-8601 timestamp (default: now, UTC)")
    record.add_argument("--append", action="store_true",
                        help="deliberately add a SECOND decision record (records are "
                             "append-only; without this a bundle that already carries "
                             "one is refused)")
    record.add_argument("--output", "-o", type=Path, default=None,
                        help="output path (default: overwrite input)")


def _mint_decision_id(doc: dict, ordinal: int) -> str:
    """A stable IRI for this decision record.

    The record must be nameable: a blank node cannot be referenced, cited, or
    pointed at by a later concurrence, and the shapes require an IRI for exactly
    that reason. The name is DERIVED from the package it judges, so it is stable
    across re-runs and says what it belongs to -- never a random identifier that
    would differ every time the same decision was recorded.
    """
    base = doc.get("@id") or doc.get("id")
    if not base:
        cou = doc.get("hasContextOfUse")
        if isinstance(cou, dict):
            base = cou.get("@id") or cou.get("id")
    suffix = "decision" if ordinal == 0 else f"decision-{ordinal + 1}"
    if base:
        return f"{str(base).rstrip('/')}/{suffix}"
    # No base to hang it on. A urn is honest here: it names the record without
    # claiming an authority the package never established.
    import hashlib

    seed = f"{doc.get('name', '')}|{suffix}".encode("utf-8")
    return f"urn:uofa:decision:{hashlib.sha256(seed).hexdigest()[:16]}"


def _record(args) -> int:
    """Author a decision record. **No key, no signature — authoring only.**

    Splitting this from signing is the constitution's own grain: a decision
    coming into existence (outcome, rationale, owner, timestamp) and a signature
    attesting one that exists are two different acts, and they were fused here.
    The excel path already lived the split -- the product authors, the CLI signs
    -- so this makes the SIP path structurally identical rather than specially
    fused: one decision model, two front doors, the same two steps.

    The two-step cost is the honest price: a decision deserves a moment of
    existence before its signature, where it is reviewable, refusable at the
    shape, and visible as owed-unsigned.
    """
    from uofa_cli import sign_roles
    from uofa_cli.interrogate import signing

    doc = json.loads(args.file.read_text(encoding="utf-8"))
    existing = sign_roles.decision_records(doc)

    # Append-only, and deliberately so: a second entry is a real event (an
    # independent concurrence, a program approval) and must be asked for, never
    # arrived at by re-running a command that silently overwrote the first.
    if existing and not args.append:
        error(
            f"this bundle already carries {len(existing)} decision record(s). "
            f"Records accumulate and are never overwritten -- pass `--append` if "
            f"this is a deliberate second entry (a concurrence or an approval).")
        return 2

    # A-11 applies to AUTHORING, not only to attesting. The judgment attaches to
    # this package here; if the measurements have already drifted from the seal
    # that covers them, a verdict written over them is a verdict about evidence
    # that no longer exists. Total by construction: no seal means there is
    # nothing to contradict (a decision may legitimately precede sealing), a
    # seal that matches is fine, and only a seal that DISAGREES refuses.
    # `_is_real_seal`, not a truthiness test: `uofa import` writes zero-filled
    # placeholders, which are truthy, so a presence check here would compare the
    # content against a hash of zeros and call every fresh template tampered.
    # One definition for "has this been sealed", shared with the signer, because
    # the same blindness fixed in one place and not the other is how it survives.
    if sign_roles._is_real_seal(doc):
        from uofa_cli.interrogate.signing import measurement_hash

        stored = doc["hash"]
        stored = stored.split(":", 1)[1] if ":" in stored else stored
        if measurement_hash(doc) != stored:
            error("the measurement content does not match its signed hash (stale "
                  "or tampered) -- refusing to record a judgment over measurements "
                  "that have drifted from their seal. Nothing written.")
            return 1

    try:
        sign_roles.classify_identity(args.actor)
    except sign_roles.IdentityFormError as exc:
        error(str(exc))
        return 2

    decided_at = args.decided_at or _now_iso()

    # The same builder the fused command used -- one block shape, two front doors.
    # No key: `decidedBy` is a fingerprint, a fact about the attestation, and
    # there is no attestation yet.
    block = signing.build_decision_block(
        acceptance_criterion=args.criterion,
        decision_value=_VALUE_MAP[args.value],
        decided_at=decided_at,
        rationale=args.rationale,
        actor=args.actor,
    )
    block["type"] = "DecisionRecord"
    block["id"] = _mint_decision_id(doc, len(existing))
    # Authored here by a live participant, so the fork is `asserted` and the
    # warrant is a signature that does not exist yet. The package is now
    # honestly incomplete, and the seal refuses to close around it -- which is
    # the intermediate state being VISIBLE, not the package being broken.
    block["decisionProvenance"] = "asserted"

    doc[DECISION_BLOCK_KEY] = (existing + [block]) if existing else block
    out = Path(args.output or args.file)
    out.write_text(json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8")

    step_header(f"Recorded a decision in {args.file.name}")
    result_line("Decision recorded (unsigned)", True)
    info(f"{block['decisionValue']} \u2014 decided by {args.actor}")
    info("next: `uofa sign --key <your key> --as reviewer` to attest it")
    return 0


def run(args) -> int:
    cmd = getattr(args, "decision_cmd", None)
    if cmd == "review":
        return _review(args)
    if cmd == "record":
        return _record(args)
    error("usage: uofa decision <review|record> <bundle.json>")
    return 2


def _load_bundle(path: Path) -> dict:
    from uofa_cli.interrogate.signing import is_sip_bundle
    bundle = json.loads(Path(path).read_text(encoding="utf-8"))
    if not is_sip_bundle(bundle):
        raise ValueError(f"{path} is not a SIP evidence bundle (schemaVersion mismatch)")
    return bundle


def _review(args) -> int:
    """Facts, then stop. No key, no judgment (A14.2)."""
    from uofa_cli.interrogate.comparison import render_comparison

    bundle = _load_bundle(args.file)
    print(render_comparison(bundle))
    # Factual pointer only — weakener findings come from the pack via `uofa check`
    # on the imported package; stated as a fact, with no verdict or recommendation.
    print()
    print("For pack weakener findings, import the bundle and run `uofa check`.")
    return 0


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

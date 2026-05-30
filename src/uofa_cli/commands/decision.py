"""uofa decision — git-shaped review-and-sign for a SIP evidence bundle.

Modeled on `git diff` then `git commit -S`: the tool states facts and verifies;
the engineer decides and signs. Two subcommands, two moments, by design — there
is no fused measure-and-sign step (that would be the tool deciding, the breach).

- `uofa decision review <pkg>` — read-only. Prints the surrogate-vs-reference
  comparison and stops. No key, no prompts, no commentary, no suggested verdict
  (Addendum A14.2 terminal silence).
- `uofa decision sign <pkg> --criterion … --value <accepted|not-accepted>
  --rationale … --key <engineer-key>` — re-verifies SIP's measurement signature
  (stale-bundle refusal, A11), then writes the engineer's signed `engineerDecision`
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

HELP = "review a SIP comparison (read-only) or sign an engineer decision"

_VALUE_MAP = {"accepted": "Accepted", "not-accepted": "Not accepted", "conditional": "Conditional"}


def add_arguments(parser):
    sub = parser.add_subparsers(dest="decision_cmd", title="decision commands")

    review = sub.add_parser("review", help="print the surrogate-vs-reference comparison (read-only)")
    review.add_argument("file", type=Path, help="SIP evidence bundle (.json)")

    sign = sub.add_parser("sign", help="sign an engineer decision into the bundle")
    sign.add_argument("file", type=Path, help="SIP evidence bundle (.json)")
    sign.add_argument("--key", "-k", type=Path, required=True,
                      help="the engineer's ed25519 private key (REQUIRED; no default, no service key)")
    sign.add_argument("--criterion", required=True,
                      help="the engineer's acceptance criterion, e.g. 'Cl within 3%% of reference over the envelope'")
    sign.add_argument("--value", required=True, choices=["accepted", "not-accepted", "conditional"],
                      help="the engineer's judgment (no default; accepted and not-accepted are symmetric)")
    sign.add_argument("--rationale", default=None, help="short free-text rationale")
    sign.add_argument("--decided-at", default=None, help="ISO-8601 timestamp (default: now, UTC)")
    sign.add_argument("--measurement-pubkey", type=Path, default=None,
                      help="SIP measurement public key — when supplied, the measurement signature is cryptographically verified before signing")
    sign.add_argument("--output", "-o", type=Path, default=None, help="output path (default: overwrite input)")


def run(args) -> int:
    cmd = getattr(args, "decision_cmd", None)
    if cmd == "review":
        return _review(args)
    if cmd == "sign":
        return _sign(args)
    error("usage: uofa decision <review|sign> <bundle.json>")
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


def _sign(args) -> int:
    from uofa_cli.interrogate import signing

    bundle = _load_bundle(args.file)

    # Stale-bundle refusal (A11): the measurements must match their signed hash,
    # and the bundle must actually carry a SIP measurement signature.
    if not bundle.get("hash") or not bundle.get("signature"):
        error("bundle has no SIP measurement signature — refusing to sign a decision "
              "over unsigned measurements. Nothing written.")
        return 1
    stored = bundle["hash"].split(":", 1)[1] if ":" in bundle["hash"] else bundle["hash"]
    if signing.measurement_hash(bundle) != stored:
        error("SIP measurement content does not match its signed hash (stale or tampered) "
              "— refusing to sign. Nothing written.")
        return 1
    if args.measurement_pubkey is not None:
        hash_ok, sig_ok = signing.verify_measurement(bundle, args.measurement_pubkey)
        if not (hash_ok and sig_ok):
            error("SIP measurement signature does not verify against the supplied key "
                  "— refusing to sign. Nothing written.")
            return 1

    if not Path(args.key).exists():
        raise FileNotFoundError(
            f"Engineer key not found: {args.key}. The decision must be signed with "
            f"the engineer's own key (no default identity)."
        )

    step_header("Signing engineer decision")
    block = signing.build_decision_block(
        key_path=args.key,
        acceptance_criterion=args.criterion,
        decision_value=_VALUE_MAP[args.value],
        decided_at=args.decided_at or _now_iso(),
        rationale=args.rationale,
    )
    signed = signing.sign_decision(bundle, args.key, block)
    bundle["engineerDecision"] = signed

    out = Path(args.output or args.file)
    out.write_text(json.dumps(bundle, indent=2, ensure_ascii=False), encoding="utf-8")

    result_line("Signed engineer decision", True, str(out))
    info(f"decidedBy: {signed['decidedBy']}")
    info(f"decisionValue: {signed['decisionValue']}  (the engineer's input, attributed to their key)")
    info("verify with: uofa verify <pkg> --decision-pubkey <engineer.pub>")
    return 0

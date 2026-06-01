"""uofa guardrail — the basic action leg over detection firings (spec §6).

Consumes ``check.run_structured(...).rules.firings`` and emits a signed,
action-region ``guardrailAction`` block: an engineer-commanded threshold trigger
plus a basic envelope-restriction response (``restrict`` / ``clip`` / ``refuse``).

It **acts**; it never adjudicates credibility — no verdict, no pass/fail (the
inverse of SIP's measure-don't-judge). The sophisticated guardrail and any actual
surrogate mitigation/fixing are Product B and are deliberately out of scope: a
non-basic ``--action`` is refused by :class:`ThresholdGuardrail`.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from uofa_cli import paths
from uofa_cli.output import error, info, step_header

HELP = "basic guardrail: turn weakener firings into a signed engineer-commanded action (§6)"


def add_arguments(parser):
    parser.add_argument("file", type=Path, help="evidence package / COU to assess")
    parser.add_argument("--key", "-k", type=Path,
                        help="ed25519 key to sign the action (auto-detected from project keys/ if omitted)")
    parser.add_argument("--threshold", default="High", choices=["Critical", "High", "Medium", "Low"],
                        help="engineer-commanded severity threshold to trigger (default: High)")
    parser.add_argument("--action", default="restrict", choices=["restrict", "clip", "refuse"],
                        help="engineer-commanded response on trigger (default: restrict)")
    parser.add_argument("--min-hits", type=int, default=1, dest="min_hits",
                        help="minimum hits for a firing to count toward the trigger (default: 1)")
    parser.add_argument("--output", "-o", type=Path,
                        help="output path for the package + guardrailAction (default: in place)")


def _resolve_key(args) -> Path | None:
    if getattr(args, "key", None):
        return Path(args.key)
    root = paths.find_project_root()
    if root and (root / "keys").is_dir():
        for candidate in sorted((root / "keys").glob("*.key")):
            return candidate
    return None


def run(args) -> int:
    from uofa_cli import guardrail as G
    from uofa_cli.commands.check import run_structured

    active = paths.resolve_active_packs(args)

    # 1) Firings from the real check pipeline (derive → rules → oos), so
    #    derivation-gated weakeners (e.g. W-SURR-03) are included.
    check_args = argparse.Namespace(
        file=args.file, pubkey=None, context=None, rules=None, skip_rules=False, build=False,
        enable_oos=False, disable_oos=False, no_color=getattr(args, "no_color", True),
        verbose=False, repo_root=getattr(args, "repo_root", None),
        pack=active, active_packs=active,
    )
    result = run_structured(check_args)
    if result.rules is None:
        error("rule engine did not run — cannot assess firings (is Java available?)")
        return 1
    firings = result.rules.firings or []

    # 2) Build the engineer-commanded action (basic tier only; non-basic → refused).
    context = {"threshold": args.threshold, "action": args.action, "min_hits": args.min_hits}
    try:
        block = G.build_guardrail_action(G.ThresholdGuardrail(), firings, context=context)
    except ValueError as exc:  # a Product-B action was requested
        error(str(exc))
        return 2

    # 3) Sign the action into the package's action-region scope (§4).
    key_path = _resolve_key(args)
    if key_path is None:
        error("no signing key found — pass --key or place one under the project keys/.")
        return 2
    pkg = json.loads(Path(args.file).read_text(encoding="utf-8"))
    pkg["guardrailAction"] = G.sign_guardrail_action(pkg, key_path, block)

    out = Path(args.output) if args.output else Path(args.file)
    out.write_text(json.dumps(pkg, indent=2, ensure_ascii=False), encoding="utf-8")

    # 4) Report — action only, NEVER a verdict (the firewall).
    step_header("Guardrail — basic, engineer-commanded (§6)")
    triggering = ", ".join(block["triggeringPatterns"]) or "—"
    info(f"firings considered: {block['firingsConsidered']}; triggering (≥{args.threshold}): {triggering}")
    info(f"ACTION: {block['action']}  —  {block['rationale']}")
    info(f"signed action-region block (scope 'action') written to {out}")
    return 0

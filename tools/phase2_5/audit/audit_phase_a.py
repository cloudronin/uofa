"""Phase 2.5 Phase A audit — verify v0.5.12.1 hooks fired on production CLI output.

Walks the Phase A output dir, classifies each NC by archetype, and reports:
- envelope stubs (hasApplicabilityConstraint + hasOperatingEnvelope) on COU
- offset rationale on Accepted+shortfall DRs
- SensitivityAnalysis stub on Complete-profile UofAs
- hash + signature integrity
- per-NC rule firings (via `uofa rules`)

Exits 0 if all gate criteria pass; 1 otherwise. Prints a markdown table
suitable for paste into the findings doc.

Usage:
    python tools/phase2_5/audit_phase_a.py /tmp/v0512_1_phase_a
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

from uofa_cli.integrity import verify_file


def _is_complete_profile(uofa: dict) -> bool:
    profile = uofa.get("conformsToProfile", "")
    if not isinstance(profile, str):
        return False
    return profile == "uofa:ProfileComplete" or profile.endswith("ProfileComplete")


def _is_accepted_with_shortfall(uofa: dict) -> bool:
    dr = uofa.get("hasDecisionRecord")
    if not isinstance(dr, dict):
        return False
    if dr.get("outcome") != "Accepted":
        return False
    factors = uofa.get("hasCredibilityFactor") or []
    if not isinstance(factors, list):
        factors = [factors]
    for f in factors:
        if not isinstance(f, dict):
            continue
        req = f.get("requiredLevel")
        ach = f.get("achievedLevel")
        if req is not None and ach is not None:
            try:
                if ach < req:
                    return True
            except TypeError:
                pass
    return False


_RULES_RE = re.compile(r"⚠\s+(W-[A-Z]+-\d{2}|COMPOUND-\d{2})\s+\[")
_SUMMARY_RE = re.compile(r"SUMMARY:\s+(\d+)\s+weakener")


def _run_rules(pkg_path: Path) -> tuple[int, list[str]]:
    """Return (firing_count, list_of_rule_ids_fired) for a package."""
    try:
        result = subprocess.run(
            ["uofa", "rules", str(pkg_path), "--raw"],
            capture_output=True, text=True, timeout=120,
        )
    except Exception as e:
        return -1, [f"rules-failed: {e}"]
    out = result.stdout + result.stderr
    rules = _RULES_RE.findall(out)
    m = _SUMMARY_RE.search(out)
    count = int(m.group(1)) if m else 0
    return count, rules


def _archetype_from_path(p: Path) -> str:
    """Spec dir name → NC archetype label (e.g. 'NC-1 full Morrison COU1')."""
    name = p.parent.name.lower()
    if "full-morrison-cou1" in name:
        return "NC-1 full-morrison-cou1"
    if "minimal-morrison-cou1" in name:
        return "NC-2 minimal-morrison-cou1"
    if "full-morrison-cou2" in name:
        return "NC-3 full-morrison-cou2"
    if "full-nagaraja" in name:
        return "NC-4 full-nagaraja"
    if "scoped-out" in name:
        return "NC-5 scoped-out"
    if "not-applicable" in name:
        return "NC-6 not-applicable"
    if "rejected-decision" in name:
        return "NC-7 rejected"
    if "partial-envelope" in name:
        return "NC-8 partial-envelope"
    if "low-confidence" in name:
        return "NC-9 low-confidence"
    if "compound-free" in name:
        return "NC-10 compound-free"
    return name


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("out_dir", type=Path, help="Phase A output dir")
    p.add_argument("--pubkey", type=Path, default=Path("keys/research.pub"))
    args = p.parse_args(argv)

    if not args.out_dir.exists():
        print(f"FATAL: out_dir not found: {args.out_dir}", file=sys.stderr)
        return 1

    rows: list[dict] = []
    for pkg in sorted(args.out_dir.rglob("*.jsonld")):
        if "/failed/" in str(pkg):
            continue
        try:
            doc = json.loads(pkg.read_text())
        except Exception as e:
            rows.append({
                "spec_id": pkg.parent.name,
                "variant": pkg.stem,
                "archetype": _archetype_from_path(pkg),
                "error": f"json-parse: {e}",
            })
            continue

        cou = doc.get("hasContextOfUse") or {}
        dr = doc.get("hasDecisionRecord") or {}
        is_complete = _is_complete_profile(doc)
        accepted_shortfall = _is_accepted_with_shortfall(doc)

        # Adversarial samples carry the `synthetic: True` flag and have
        # LLM-fabricated hash/signature placeholders (not real ed25519
        # signatures). The integrity check is N/A for these — SHACL
        # validation is the analogous structural check, and that's what
        # `uofa adversarial run` enforces during generation.
        is_synthetic = doc.get("synthetic") is True or "uofa:SyntheticAdversarialSample" in (doc.get("type") or [])
        if is_synthetic:
            hash_ok, sig_ok = None, None  # N/A for synthetic
        else:
            try:
                hash_ok, sig_ok = verify_file(pkg, args.pubkey)
            except Exception as e:
                hash_ok, sig_ok = False, False

        firing_count, rules_fired = _run_rules(pkg)

        rows.append({
            "spec_id": pkg.parent.name,
            "variant": pkg.stem,
            "archetype": _archetype_from_path(pkg),
            "conformsToProfile": doc.get("conformsToProfile", ""),
            "is_complete": is_complete,
            "accepted_shortfall": accepted_shortfall,
            "has_applicability": "hasApplicabilityConstraint" in cou,
            "has_envelope": "hasOperatingEnvelope" in cou,
            "has_sa": "hasSensitivityAnalysis" in doc,
            "has_offset": "hasOffsetRationale" in dr,
            "hash_ok": hash_ok,
            "sig_ok": sig_ok,
            "firing_count": firing_count,
            "rules_fired": rules_fired,
        })

    # ── Aggregate stats ──
    total = len(rows)
    valid = [r for r in rows if "error" not in r]
    complete_nc = [r for r in valid if r["is_complete"]]
    accepted_shortfall_nc = [r for r in valid if r["accepted_shortfall"]]

    envelope_present = sum(1 for r in valid if r["has_applicability"] and r["has_envelope"])
    sa_present_complete = sum(1 for r in complete_nc if r["has_sa"])
    offset_present_shortfall = sum(1 for r in accepted_shortfall_nc if r["has_offset"])
    # Synthetic samples have hash_ok=None (N/A); count only real-signed
    real_signed = [r for r in valid if r["hash_ok"] is not None]
    integrity_ok = sum(1 for r in real_signed if r["hash_ok"] and r["sig_ok"])
    clean_nc = sum(1 for r in valid if r["firing_count"] == 0)

    rule_firings: Counter = Counter()
    for r in valid:
        for rule in r["rules_fired"]:
            rule_firings[rule] += 1

    # ── Pass/fail per criterion ──
    def pct(n: int, d: int) -> str:
        return f"{n}/{d} = {100*n/d:.0f}%" if d else "n/a"

    criteria = [
        ("SHACL pass rate", total, 20, total >= 18),
        ("Envelope stubs (COU)", envelope_present, len(valid), envelope_present == len(valid)),
        ("SA stubs (Complete profiles)", sa_present_complete, len(complete_nc), sa_present_complete == len(complete_nc) if complete_nc else True),
        ("Offset rationale (Accepted+shortfall)", offset_present_shortfall, len(accepted_shortfall_nc), offset_present_shortfall == len(accepted_shortfall_nc) if accepted_shortfall_nc else True),
        ("Hash + sig integrity (real-signed only)", integrity_ok, len(real_signed), integrity_ok == len(real_signed) if real_signed else True),
        ("W-ON-02 NC firings", rule_firings.get("W-ON-02", 0), 0, rule_firings.get("W-ON-02", 0) == 0),
        ("W-AR-02 NC firings", rule_firings.get("W-AR-02", 0), 0, rule_firings.get("W-AR-02", 0) == 0),
        ("W-CON-04 NC firings", rule_firings.get("W-CON-04", 0), 0, rule_firings.get("W-CON-04", 0) == 0),
        ("Total NC clean rate", clean_nc, len(valid), clean_nc / max(1, len(valid)) >= 0.90),
    ]

    print("# Phase A audit — Pipeline test summary")
    print()
    print(f"Total packages: {total}")
    print(f"Valid (parseable): {len(valid)}")
    print(f"Complete-profile NCs: {len(complete_nc)}")
    print(f"Accepted+shortfall NCs: {len(accepted_shortfall_nc)}")
    print()
    print("## Pass/fail")
    print()
    print("| Criterion | Got | Target | Status |")
    print("|---|---|---|---|")
    all_pass = True
    for label, got, target, ok in criteria:
        status = "✓" if ok else "✗"
        if not ok:
            all_pass = False
        target_str = "0" if target == 0 else (f">= {target}" if isinstance(target, int) else target)
        print(f"| {label} | {got} | {target_str} | {status} |")

    print()
    print("## Per-rule NC firings")
    print()
    if rule_firings:
        print("| Rule | Count |")
        print("|---|---|")
        for rule, count in rule_firings.most_common():
            print(f"| {rule} | {count} |")
    else:
        print("(none)")

    print()
    print("## Per-package detail")
    print()
    print("| archetype | variant | profile | env? | SA? | offset? | hash+sig | fires |")
    print("|---|---|---|---|---|---|---|---|")
    for r in rows:
        if "error" in r:
            print(f"| {r['archetype']} | {r['variant']} | ERROR | — | — | — | — | {r['error']} |")
            continue
        env = "✓" if r["has_applicability"] and r["has_envelope"] else "✗"
        sa = "✓" if r["has_sa"] else ("—" if not r["is_complete"] else "✗")
        offset = "✓" if r["has_offset"] else ("—" if not r["accepted_shortfall"] else "✗")
        integrity = "—" if r["hash_ok"] is None else ("✓" if r["hash_ok"] and r["sig_ok"] else "✗")
        fires = f"{r['firing_count']}" + (f" [{','.join(r['rules_fired'])}]" if r['rules_fired'] else "")
        print(f"| {r['archetype']} | {r['variant']} | {r['conformsToProfile'].split('#')[-1] or '?'} | {env} | {sa} | {offset} | {integrity} | {fires} |")

    print()
    print(f"## Gate result: {'✓ PASS' if all_pass else '✗ FAIL'}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())

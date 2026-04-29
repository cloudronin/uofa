"""Phase 2.5 Phase B.4 audit — field-presence compliance on fresh NC corpus.

Walks the Phase B.3 output, classifies each NC, and reports compliance
with the v0.5.13 prompt directives:

- Complete-profile NCs (NC-1, NC-3, NC-4): emit `conformsToProfile: ProfileComplete`
- Complete-profile NCs: emit inline `hasSensitivityAnalysis` (substantive,
  not placeholder-stub)
- All NCs: emit `hasApplicabilityConstraint` + `hasOperatingEnvelope` on COU
- NC-7 (rejected): zero `factorStatus='not-assessed'` at MRL>2
- NC-5/6 (scoped-out / N/A): zero vestigial `requiredLevel`/`achievedLevel`
  on those factor statuses

Usage:
    python tools/phase2_5/audit_phase_b.py out/adversarial/phase2/2026-04-29-v0_phase2v2-test
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path


def _archetype(p: Path) -> str:
    """Map dir name to NC archetype short label."""
    name = p.parent.name.lower()
    mapping = [
        ("full-morrison-cou1", "NC-1"),
        ("minimal-morrison-cou1", "NC-2"),
        ("full-morrison-cou2", "NC-3"),
        ("full-nagaraja", "NC-4"),
        ("scoped-out", "NC-5"),
        ("not-applicable", "NC-6"),
        ("rejected", "NC-7"),
        ("partial-envelope", "NC-8"),
        ("low-confidence", "NC-9"),
        ("compound-free", "NC-10"),
    ]
    for needle, label in mapping:
        if needle in name:
            return label
    return "?"


def _is_placeholder(obj) -> bool:
    """Detect the v0.5.10/v0.5.12 hook-injected placeholder vs substantive content."""
    if not isinstance(obj, dict):
        return False
    desc = (obj.get("description") or "").lower()
    name = (obj.get("name") or "").lower()
    return "placeholder" in name or "not substantively meaningful" in desc


def _is_complete(profile: str) -> bool:
    if not isinstance(profile, str):
        return False
    return profile.endswith("ProfileComplete")


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("out_dir", type=Path)
    args = p.parse_args(argv)

    if not args.out_dir.exists():
        print(f"FATAL: {args.out_dir} not found", file=sys.stderr)
        return 1

    rows = []
    for pkg in sorted(args.out_dir.rglob("*.jsonld")):
        if "/failed/" in str(pkg):
            continue
        try:
            doc = json.loads(pkg.read_text())
        except Exception:
            continue
        cou = doc.get("hasContextOfUse") or {}
        # Some NCs emit COU as an IRI string rather than inline object; treat as empty
        if not isinstance(cou, dict):
            cou = {}
        applicab = cou.get("hasApplicabilityConstraint")
        envelope = cou.get("hasOperatingEnvelope")
        sa = doc.get("hasSensitivityAnalysis")

        # Detect substantive vs placeholder
        applicab_substantive = isinstance(applicab, dict) and not _is_placeholder(applicab)
        envelope_substantive = isinstance(envelope, dict) and not _is_placeholder(envelope)
        sa_substantive = isinstance(sa, dict) and not _is_placeholder(sa)

        # Check factor encoding
        scoped_out_with_levels = 0
        not_applicable_with_levels = 0
        not_assessed_at_high_mrl = 0
        mrl = doc.get("modelRiskLevel", 0) or 0
        for f in doc.get("hasCredibilityFactor") or []:
            if not isinstance(f, dict):
                continue
            status = f.get("factorStatus")
            has_levels = "requiredLevel" in f or "achievedLevel" in f
            if status == "scoped-out" and has_levels:
                scoped_out_with_levels += 1
            if status == "not-applicable" and has_levels:
                not_applicable_with_levels += 1
            if status == "not-assessed" and mrl > 2:
                not_assessed_at_high_mrl += 1

        rows.append({
            "path": pkg,
            "archetype": _archetype(pkg),
            "profile": doc.get("conformsToProfile", ""),
            "is_complete": _is_complete(doc.get("conformsToProfile", "")),
            "mrl": mrl,
            "has_applicab": applicab is not None,
            "applicab_substantive": applicab_substantive,
            "has_envelope": envelope is not None,
            "envelope_substantive": envelope_substantive,
            "has_sa": sa is not None,
            "sa_substantive": sa_substantive,
            "scoped_out_with_levels": scoped_out_with_levels,
            "not_applicable_with_levels": not_applicable_with_levels,
            "not_assessed_at_high_mrl": not_assessed_at_high_mrl,
        })

    n = len(rows)
    by_arch: dict = defaultdict(list)
    for r in rows:
        by_arch[r["archetype"]].append(r)

    # ── Aggregate metrics ──
    complete_archetypes = ("NC-1", "NC-3", "NC-4")
    expected_complete = [r for r in rows if r["archetype"] in complete_archetypes]
    actually_complete = [r for r in expected_complete if r["is_complete"]]
    sa_in_complete = [r for r in actually_complete if r["has_sa"]]
    sa_substantive_in_complete = [r for r in actually_complete if r["sa_substantive"]]

    envelope_present = [r for r in rows if r["has_applicab"] and r["has_envelope"]]
    envelope_substantive = [r for r in rows if r["applicab_substantive"] and r["envelope_substantive"]]

    nc7 = by_arch.get("NC-7", [])
    nc7_violations = [r for r in nc7 if r["not_assessed_at_high_mrl"] > 0]
    nc56 = by_arch.get("NC-5", []) + by_arch.get("NC-6", [])
    nc56_violations = [r for r in nc56 if r["scoped_out_with_levels"] + r["not_applicable_with_levels"] > 0]

    print(f"# Phase B.4 audit — fresh corpus field-presence")
    print(f"\nTotal packages: {n}\n")

    print(f"## Per-archetype counts")
    print(f"\n| Archetype | Successful packages |")
    print(f"|---|---|")
    for arch in sorted(by_arch):
        print(f"| {arch} | {len(by_arch[arch])} |")
    print()

    def pct(num, den):
        return f"{num}/{den} = {100*num/den:.0f}%" if den else "n/a"

    print(f"## Compliance metrics")
    print(f"\n| Metric | Result | Target | Status |")
    print(f"|---|---|---|---|")
    metrics = [
        ("Complete-profile compliance (NC-1/3/4 emit ProfileComplete)",
         pct(len(actually_complete), len(expected_complete)),
         "≥ 90%",
         len(actually_complete) / max(1, len(expected_complete)) >= 0.90),
        ("hasSensitivityAnalysis present on Complete NCs",
         pct(len(sa_in_complete), len(actually_complete)),
         "≥ 90%",
         len(sa_in_complete) / max(1, len(actually_complete)) >= 0.90 if actually_complete else None),
        ("hasSensitivityAnalysis is SUBSTANTIVE (not placeholder)",
         pct(len(sa_substantive_in_complete), len(actually_complete)),
         "≥ 70% (substantive content)",
         len(sa_substantive_in_complete) / max(1, len(actually_complete)) >= 0.70 if actually_complete else None),
        ("Envelope stubs present (all NCs)",
         pct(len(envelope_present), n),
         "≥ 90%",
         len(envelope_present) / max(1, n) >= 0.90),
        ("Envelope is SUBSTANTIVE (not placeholder)",
         pct(len(envelope_substantive), n),
         "≥ 70%",
         len(envelope_substantive) / max(1, n) >= 0.70),
        ("NC-7 with factorStatus=not-assessed at MRL>2",
         f"{len(nc7_violations)} of {len(nc7)}",
         "0",
         len(nc7_violations) == 0),
        ("NC-5/6 with vestigial requiredLevel/achievedLevel",
         f"{len(nc56_violations)} of {len(nc56)}",
         "0",
         len(nc56_violations) == 0),
    ]
    all_pass = True
    for label, got, target, ok in metrics:
        if ok is None:
            status = "n/a"
        elif ok:
            status = "✓"
        else:
            status = "✗"
            all_pass = False
        print(f"| {label} | {got} | {target} | {status} |")

    # ── Detail: per-archetype profile distribution ──
    print(f"\n## Profile distribution per archetype")
    print(f"\n| Archetype | profile distribution |")
    print(f"|---|---|")
    for arch in sorted(by_arch):
        profiles = Counter(r["profile"].split("#")[-1] for r in by_arch[arch])
        dist = ", ".join(f"{k}={v}" for k, v in profiles.most_common())
        print(f"| {arch} | {dist} |")

    print(f"\n## Gate result: {'✓ PASS' if all_pass else '⚠ MIXED — see detail'}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())

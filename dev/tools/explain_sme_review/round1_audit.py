"""Round 1 audit: dump exactly what's in the explain prompt today vs what
SHOULD be in it, for the SME-flagged W-EP-04 firing in Morrison COU2.

Per the SME handoff doc (Task 1), this is the cheapest possible diagnostic:
print the actual rendered prompt for one canonical bad firing, then show
the data the engine emits in jsonld mode + the data resolvable from the
package itself. The diff between "what's in the prompt" and "what's
available" is the fix scope.

Output: prints to stdout; pipe to round1_audit.md or copy/paste into the
audit document.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "src"))

from uofa_cli.commands import rules
from uofa_cli.interpretation.context import extract_firing_contexts
from uofa_cli.interpretation.templates import render

PKG = REPO_ROOT / "packs/vv40/examples/morrison/cou2/uofa-morrison-cou2.jsonld"
TARGET_PATTERN = "W-EP-04"


def section(title: str) -> None:
    print()
    print("=" * 70)
    print(title)
    print("=" * 70)


def main() -> int:
    section("0. Setup")
    print(f"Package: {PKG.relative_to(REPO_ROOT)}")
    print(f"Target firing: {TARGET_PATTERN} (SME-flagged canonical generic case)")

    # ── 1. Run the engine in summary mode (the path explain currently uses)
    section("1. Current path: rules.run_structured() → parse_firings (summary)")
    args = argparse.Namespace(
        file=PKG, rules=None, context=None, build=False,
        raw=False, format="summary", output=None,
    )
    result = rules.run_structured(args)
    print(f"firings count: {len(result.firings)}")
    target_firing = next(
        (f for f in result.firings if f.get("patternId") == TARGET_PATTERN),
        None,
    )
    print(f"target firing dict: {json.dumps(target_firing, indent=2) if target_firing else None}")
    print()
    print("→ Available fields: patternId, severity, hits.")
    print("→ Missing: which factors were unassessed, what their levels are.")

    # ── 2. Build the FiringContext (current production path)
    section("2. extract_firing_contexts() → FiringContext (current shape)")
    package_doc = json.loads(PKG.read_text())
    contexts = extract_firing_contexts(result.firings, package_doc, "vv40")
    target_ctx = next((c for c in contexts if c.pattern_id == TARGET_PATTERN), None)
    print(f"target FiringContext:")
    print(f"  pattern_id:        {target_ctx.pattern_id}")
    print(f"  severity:          {target_ctx.severity}")
    print(f"  hits:              {target_ctx.hits}")
    print(f"  description:       {target_ctx.description!r}")
    print(f"  affected_node:     {target_ctx.affected_node!r}  ← always empty")
    print(f"  evidence_excerpt:  {target_ctx.evidence_excerpt!r}  ← always empty")
    print(f"  pack:              {target_ctx.pack}")
    print(f"  cou:               {target_ctx.cou}")

    # ── 3. Render the prompt that's actually sent to the LLM today
    section("3. Rendered prompt (what Qwen actually sees)")
    template_vars = target_ctx.to_template_vars()
    prompt = render("rules", "explain", "vv40", **template_vars)
    print(prompt)

    # ── 4. Run the engine in jsonld mode (richer data we COULD use)
    section("4. Same engine, --format jsonld: rich firings available NOW")
    args_json = argparse.Namespace(
        file=PKG, rules=None, context=None, build=False,
        raw=False, format="jsonld", output=None,
    )
    json_result = rules.run_structured(args_json)
    try:
        graph = json.loads(json_result.raw_stdout).get("@graph", [])
    except json.JSONDecodeError as exc:
        print(f"jsonld parse failed: {exc}")
        print(f"first 200 chars: {json_result.raw_stdout[:200]!r}")
        return 1

    weakener_annotations = [
        n for n in graph
        if isinstance(n, dict)
        and n.get("@type") == "https://uofa.net/vocab#WeakenerAnnotation"
    ]
    target_annotations = [
        n for n in weakener_annotations
        if n.get("https://uofa.net/vocab#patternId") == TARGET_PATTERN
    ]
    print(f"WeakenerAnnotation nodes total: {len(weakener_annotations)}")
    print(f"  for {TARGET_PATTERN}: {len(target_annotations)}")
    print()
    print(f"First {TARGET_PATTERN} annotation (truncated):")
    print(json.dumps(target_annotations[0], indent=2) if target_annotations else "(none)")
    print()
    print(f"All {TARGET_PATTERN} affectedNode IRIs:")
    for ann in target_annotations:
        node = ann.get("https://uofa.net/vocab#affectedNode", {})
        if isinstance(node, dict):
            print(f"  • {node.get('@id', '?')}")

    # ── 5. Walk the package JSON-LD to resolve those IRIs to evidence content
    section("5. Resolved evidence at affectedNode IRIs (the KEY missing data)")
    factors = package_doc.get("hasCredibilityFactor", [])
    print(f"Package has {len(factors)} credibility factors total.")
    print()
    affected_iris = {
        ann.get("https://uofa.net/vocab#affectedNode", {}).get("@id", "")
        for ann in target_annotations
    }
    print(f"Resolving the {len(affected_iris)} affected IRIs:")
    for f in factors:
        fid = f.get("id") or f.get("@id", "")
        if fid in affected_iris:
            print(f"  • {f.get('factorType', '?'):<35} (status={f.get('factorStatus', '?')}, "
                  f"requiredLevel={f.get('requiredLevel', '?')}, "
                  f"achievedLevel={f.get('achievedLevel', '?')})")

    # ── 6. Diff
    section("6. Gap summary")
    print("CURRENT prompt tells the model:")
    print("  - Pattern W-EP-04 fired 6 times")
    print("  - Severity High")
    print("  - Description: 'Unassessed Factor at Elevated Risk'")
    print("  - In COU2 Class III VAD")
    print()
    print("CURRENT prompt does NOT tell the model:")
    print("  - WHICH 6 factors were unassessed")
    print("  - What their factorType labels are (e.g. 'Use error')")
    print("  - What their required/achieved levels are")
    print()
    print("All of this data is available via jsonld engine output + package walk.")
    print("Fix: re-invoke engine in jsonld mode for explain pipeline only;")
    print("     parse WeakenerAnnotation @graph; resolve affectedNode IRIs against")
    print("     package_doc; surface as `affected_evidence` field on FiringContext.")

    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Do gap_probe REAL-GAP verdicts rest on the package, or on the prompt header?

The Stage 4 adjudication surfaced a structural worry about the gap_probe
instrument. The production judge rubric (packs/core/judge_prompts/v1.1.0.md)
sets REAL-GAP as:

    coverage_intent = gap_probe
    AND the package content visibly instantiates the SECTION 6.7 candidate's defeater
    AND either no rules fired, or the rules that fired are semantically distinct

The middle condition presumes a named candidate exists. For gap probes whose
source taxonomy maps to none of the six Tier-1 candidates, it has no referent,
so a judge has to supply the defeater unaided - which is precisely the expert
prior the catalog exists to codify. This script asks whether they did.

METHOD. For each judgment on a gap_probe case, split the tokens available to
the judge into two pools:

  header pool   - everything in the prompt's metadata lines: case_id,
                  coverage_class, source_taxonomy, expected_target_rule,
                  rules_that_fired
  package pool  - tokens that appear in the package JSON-LD and NOT in the
                  header pool ("distinctive" tokens)

A judgment grounded in the artifact should reuse distinctive tokens: factor
names, validation-result names, quoted criteria. One resting on the frame will
reuse header tokens and generic verdict vocabulary only. We count distinctive
tokens echoed in the judge's reasoning, and report the distribution split by
whether the probe pointed at a named candidate.

Deliberately NOT a keyword regex. INV-17 recorded two traps from that approach:
a narrow pattern silently killing multi-word markers, and re.X eating spaces.
Token overlap has no pattern to get wrong, and every exclusion is logged.

BLINDING. This reads judge verdicts and reasoning. ADJUDICATION_INSTRUCTIONS.md
says those are for after the worksheet is finished. The --finished flag is a
speed bump, not a lock; do not pass it early.

    python studies/phase3_stage4/check_gap_probe_grounding.py --finished
"""

from __future__ import annotations

import argparse
import collections
import csv
import json
import re
import sys
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BUNDLE = ROOT / "dev/build/adversarial/phase2/2026-04-26/judge_ready_bundle.tgz"
JUDGMENTS = ROOT / "dev/build/adversarial/phase3/production/run-1"
OUT_DIR = ROOT / "dev/build/adversarial/phase3/adjudication"

# source_taxonomy prefix -> Tier-1 candidate, for the probes that point at one.
# Everything else is treated as unmapped, which is the population under test.
TAXONOMY_TO_CANDIDATE = {
    "gohar/contextual/configuration": "W-CX-01",
    "clarissa-machinery/workflow/eliminative-argumentation": "W-AR-06",
    "clarissa-machinery/workflow/residual-risk-justification": "W-AR-07",
    "gohar/evidence_validity/data-drift": "W-EV-01",
    "gohar/evidence_validity/inadequate-metrics": "W-EV-02",
    "gohar/requirements/ambiguous": "W-REQ-01",
    "gohar/requirements/inconsistent": "W-REQ-01",
    "gohar/requirements/stale": "W-EV-01",
}

TOKEN = re.compile(r"[A-Za-z][A-Za-z0-9_-]{4,}")
# Generic assurance vocabulary. Present in most packages and most reasoning,
# so it carries no evidence that the judge actually read this package.
STOPWORDS = {
    "package", "packages", "credibility", "assessment", "validation", "model",
    "models", "rules", "rule", "fired", "firing", "verdict", "catalog", "gap",
    "probe", "defeater", "weakener", "taxonomy", "expected", "target", "case",
    "coverage", "class", "level", "factor", "factors", "evidence", "results",
    "result", "context", "intended", "decision", "assurance", "structural",
    "synthetic", "instantiates", "instantiate", "instantiated", "present",
    "absent", "absence", "missing", "should", "would", "could", "which",
    "there", "their", "these", "those", "about", "because", "however",
}


def tokens(text: str) -> set[str]:
    return {t.lower() for t in TOKEN.findall(text or "")} - STOPWORDS


def load_bundle_index() -> tuple[dict, dict]:
    """case_id -> outcome record, and case_id -> package JSON text."""
    if not BUNDLE.exists():
        sys.exit(f"bundle not found: {BUNDLE}")
    outcomes, packages = {}, {}
    with tarfile.open(BUNDLE) as t:
        for m in t:
            if not m.name.startswith("judge_ready_bundle/packages/"):
                continue
            name = Path(m.name).name
            if name.endswith(".outcome.json"):
                cid = name[: -len(".outcome.json")]
                outcomes[cid] = json.loads(t.extractfile(m).read())
            elif name.endswith(".jsonld"):
                packages[cid_from(name)] = t.extractfile(m).read().decode("utf-8", "replace")
    return outcomes, packages


def cid_from(name: str) -> str:
    return name[: -len(".jsonld")]


def candidate_for(taxonomy: str) -> str | None:
    for prefix, cand in TAXONOMY_TO_CANDIDATE.items():
        if (taxonomy or "").startswith(prefix):
            return cand
    return None


def reasoning_text(rec: dict) -> str:
    parts = [rec.get("reasoning") or ""]
    steps = rec.get("reasoning_steps") or {}
    if isinstance(steps, dict):
        parts.extend(str(v) for v in steps.values())
    parts.append(str(rec.get("alternative_rule_analysis") or ""))
    return "\n".join(parts)


def instantiation_text(rec: dict) -> str:
    steps = rec.get("reasoning_steps") or {}
    return str(steps.get("instantiation_check") or "") if isinstance(steps, dict) else ""


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--finished", action="store_true",
                    help="confirm the Stage 4 worksheet is closed; this reads judge verdicts")
    ap.add_argument("--limit", type=int, default=0, help="stop after N judgments (0 = all)")
    ap.add_argument("--out", default=str(OUT_DIR / "gap_probe_grounding.csv"))
    args = ap.parse_args()

    if not args.finished:
        sys.exit(
            "Refusing to run: this reads judge verdicts and reasoning, which\n"
            "ADJUDICATION_INSTRUCTIONS.md reserves until the worksheet is finished.\n"
            "Re-run with --finished once author_verdict is complete on all 71 rows."
        )

    outcomes, packages = load_bundle_index()
    print(f"bundle: {len(outcomes)} outcome records, {len(packages)} packages")

    files = sorted(JUDGMENTS.glob("judgments_*.jsonl"))
    if not files:
        sys.exit(f"no judgments_*.jsonl under {JUDGMENTS}")

    rows = []
    skipped: collections.Counter = collections.Counter()
    dupes: collections.Counter = collections.Counter()
    seen_pairs: set = set()
    seen = 0
    for f in files:
        judge = f.stem.replace("judgments_", "")
        for line in f.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            seen += 1
            if args.limit and seen > args.limit:
                break
            rec = json.loads(line)
            cid = rec.get("case_id")
            oc = outcomes.get(cid)
            if oc is None:
                skipped["case_id not in bundle"] += 1
                continue
            if (oc.get("experimental_factors") or {}).get("coverage_intent") != "gap_probe":
                continue
            pkg = packages.get(cid)
            if pkg is None:
                skipped["package not in bundle"] += 1
                continue

            if (judge, cid) in seen_pairs:
                dupes[judge] += 1
                continue
            seen_pairs.add((judge, cid))

            taxonomy = oc.get("source_taxonomy") or ""
            header = " ".join([
                cid or "", oc.get("coverage_class") or "", taxonomy,
                str(oc.get("expected_rule") or ""), " ".join(oc.get("rules_fired") or []),
            ])
            distinctive = tokens(pkg) - tokens(header)
            reasoning = reasoning_text(rec)
            inst = instantiation_text(rec)
            echoed = distinctive & tokens(reasoning)
            echoed_inst = distinctive & tokens(inst)

            cand = candidate_for(taxonomy)
            rows.append({
                "case_id": cid,
                "judge": judge,
                "verdict": rec.get("verdict"),
                "confidence": rec.get("confidence"),
                "source_taxonomy": taxonomy,
                "tier1_candidate": cand or "NONE",
                "probe_points_at_candidate": bool(cand),
                "section_6_7_candidate_cited": rec.get("section_6_7_candidate") or "",
                "n_distinctive_tokens": len(distinctive),
                "n_echoed_in_reasoning": len(echoed),
                "n_echoed_in_instantiation_check": len(echoed_inst),
                "instantiation_check_len": len(inst),
                "sample_echoed": "; ".join(sorted(echoed)[:8]),
            })

    if not rows:
        sys.exit("no gap_probe judgments matched; nothing to report")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    # ---------------- report ----------------
    print(f"\ngap_probe judgments analysed: {len(rows)}")
    for reason, n in skipped.most_common():
        print(f"  SKIPPED {n}: {reason}")
    for judge, n in sorted(dupes.items()):
        print(f"  DEDUPED {n} repeat judgment(s) for judge {judge} "
              f"(first occurrence kept; retries/resumes leave duplicates)")
    if args.limit:
        print(f"  NOTE: --limit {args.limit} was set; this is not the full population")

    def block(title, subset):
        if not subset:
            print(f"\n{title}: none")
            return
        zero = [r for r in subset if r["n_echoed_in_instantiation_check"] == 0]
        med = sorted(r["n_echoed_in_instantiation_check"] for r in subset)[len(subset) // 2]
        print(f"\n{title}  (n={len(subset)})")
        print(f"  median distinctive tokens echoed in instantiation_check: {med}")
        print(f"  judgments echoing ZERO package-distinctive tokens: "
              f"{len(zero)} ({100*len(zero)/len(subset):.1f}%)")
        vc = collections.Counter(r["verdict"] for r in subset)
        print(f"  verdicts: {dict(vc.most_common())}")

    real = [r for r in rows if r["verdict"] == "REAL-GAP"]
    block("ALL gap_probe judgments", rows)
    block("REAL-GAP verdicts, probe points at a Tier-1 candidate",
          [r for r in real if r["probe_points_at_candidate"]])
    block("REAL-GAP verdicts, probe points at NO candidate",
          [r for r in real if not r["probe_points_at_candidate"]])

    print(f"\nwrote {out}")
    print("\nRead the last block first. A high zero-echo share there means those\n"
          "REAL-GAP verdicts were reachable from the prompt header alone, which\n"
          "bears on the Tier-1 claim rather than on any single case.")


if __name__ == "__main__":
    main()

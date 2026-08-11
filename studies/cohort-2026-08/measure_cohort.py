#!/usr/bin/env python
"""Measure what the raidex cohort furnishes, per Group-B property.

Pre-registered baseline for the deep study and the FAccT paper. Emits
`results.json` (the record of account) and prints a summary. Re-derivable by
construction: the dataset revision is pinned, so a later run reproduces these
numbers or tells you the cohort moved.

    python studies/cohort-2026-08/measure_cohort.py
    python studies/cohort-2026-08/measure_cohort.py --revision <sha> --out results.json
    python studies/cohort-2026-08/measure_cohort.py --local-dir <dir>   # offline

What it measures, for every published raidex record: which of the properties the
Group-B rules test are actually furnished, and therefore which weakeners fire.
The point is not that the numbers are bad. It is that the zero rows are a
*specification* -- exactly what a constituent would have to carry to clear the
bar -- and the non-zero rows show the assessment discriminating rather than
blanket-failing.

Nothing here judges a model. Coverage, uncertainty and exclusions are read off
the records; sufficiency is the pack's job, and this script does not run it.
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO / "src"))

from uofa_cli.furnishers import (  # noqa: E402
    GROUP_B_RESULT_PROPERTIES, CORE_RESULT_PROPERTIES_POPULATED,
)
from uofa_cli.furnishers import raidex  # noqa: E402

# The cohort as of this study. Pinning the revision is what makes the baseline a
# baseline: without it, "43 models" silently becomes whatever the dataset holds
# on the day someone re-reads the paper.
DATASET = "cloudronin/raidex-results"
REVISION = "d459f536b506dc5f82355891db19f599f374a92c"   # lastModified 2026-07-18
MEASURED = "2026-08-10"

# Properties whose furnishing rate this study reports, and the rule each feeds.
TRACKED = {
    "metricValue": "(the score itself)",
    "wasGeneratedBy": "W-EP-02 (core)",
    "hasUncertaintyQuantification": "W-AL-01 (core)",
    "samplingAccount": "W-EV-GEN-02",
    "harnessDeterminismStatement": "W-EV-DET-03",
    "nullBaselineStatement": "W-EV-NULL-04",
    "claimedCOU": "W-EV-COU-05",
    "confoundControlStatement": "W-EV-CAP-06",
    "generalizedClaim": "COMPOUND-EV-02",
}

_STDERR_RE = re.compile(r"standard error ([\d.]+)")


def _list_files(revision: str) -> list[str]:
    from huggingface_hub import list_repo_files
    return sorted(f for f in list_repo_files(DATASET, repo_type="dataset", revision=revision)
                  if f.endswith(".json"))


def _load(revision: str, filename: str) -> Path:
    from huggingface_hub import hf_hub_download
    return Path(hf_hub_download(DATASET, filename, repo_type="dataset", revision=revision))


def measure(paths: list[Path]) -> dict:
    per_model, exclusions, stderrs = [], [], []
    furnished = {k: 0 for k in TRACKED}
    total_results = 0
    unparsed = []

    for path in paths:
        fetched = raidex.fetch_record("", local_path=path)
        if not fetched.ok:
            unparsed.append({"file": path.name, "status": fetched.status,
                             "detail": fetched.detail[:200]})
            continue
        ev = raidex.furnish(fetched.record, "https://example.org/m", path.name)
        model_id = (fetched.record.get("config") or {}).get("model_id", path.stem)

        model_stderrs, with_uq = [], []
        for node in ev.nodes:
            total_results += 1
            key = node["id"].rsplit("-", 1)[-1]
            for prop in TRACKED:
                if prop in node:
                    furnished[prop] += 1
            if "hasUncertaintyQuantification" in node:
                with_uq.append(key)
                m = _STDERR_RE.search(node.get("uqMethod", ""))
                if m:
                    model_stderrs.append(float(m.group(1)))
        stderrs.extend(model_stderrs)

        for exc in ev.excluded:
            exclusions.append({"model_id": model_id, **exc})

        per_model.append({
            "file": path.name,
            "model_id": model_id,
            "coverage": ev.coverage,
            "coverage_pct": ev.coverage_pct,
            "backend_version": ev.backend_version,
            "eval_date": ev.eval_date,
            "n_validation_results": len(ev.nodes),
            "constituents_with_uncertainty": sorted(with_uq),
            "stderr_normalized": sorted(round(s, 4) for s in model_stderrs),
            "excluded": ev.excluded,
        })

    coverage_dist: dict[str, int] = {}
    for row in per_model:
        coverage_dist[row["coverage"]] = coverage_dist.get(row["coverage"], 0) + 1

    exclusion_reasons: dict[str, int] = {}
    for exc in exclusions:
        exclusion_reasons[exc["reason"]] = exclusion_reasons.get(exc["reason"], 0) + 1

    return {
        "study": "cohort-2026-08",
        "dataset": DATASET,
        "dataset_revision": REVISION,
        "measured": MEASURED,
        "n_models": len(per_model),
        "n_validation_results": total_results,
        "unparsed": unparsed,
        "coverage_distribution": coverage_dist,
        "exclusions": exclusions,
        "exclusion_reasons": exclusion_reasons,
        "furnished_counts": furnished,
        "furnished_rates": {
            k: (round(v / total_results, 4) if total_results else None)
            for k, v in furnished.items()
        },
        "tracked_property_rules": TRACKED,
        "stderr_normalized": {
            "n": len(stderrs),
            "min": round(min(stderrs), 4) if stderrs else None,
            "mean": round(statistics.mean(stderrs), 4) if stderrs else None,
            "max": round(max(stderrs), 4) if stderrs else None,
            "values": sorted(round(s, 4) for s in stderrs),
        },
        "declared_group_b_properties": sorted(
            GROUP_B_RESULT_PROPERTIES | CORE_RESULT_PROPERTIES_POPULATED),
        "per_model": per_model,
    }


def summarize(r: dict) -> str:
    n = r["n_validation_results"]
    lines = [
        f"cohort {r['study']}  dataset {r['dataset']}@{r['dataset_revision'][:12]}",
        f"measured {r['measured']}",
        f"{r['n_models']} models, {n} validation results",
        f"coverage: {r['coverage_distribution']}",
        f"exclusions: {r['exclusion_reasons'] or 'none'}",
        "",
        f"{'property':32s}{'rule':22s}furnished",
    ]
    for prop, rule in r["tracked_property_rules"].items():
        c = r["furnished_counts"][prop]
        pct = f"{100 * c / n:5.1f}%" if n else "  n/a"
        lines.append(f"{prop:32s}{rule:22s}{c:4d}/{n}  {pct}")
    s = r["stderr_normalized"]
    if s["n"]:
        lines += ["",
                  f"stderr (normalized 0-100), n={s['n']}: "
                  f"min={s['min']} mean={s['mean']} max={s['max']}",
                  f"DIV_TOLERANCE_NORMALIZED = 5.0 vs cohort max {s['max']}: "
                  f"{'HOLDS' if s['max'] < 5.0 else 'VIOLATED -- re-derive'}"]
    if r["unparsed"]:
        lines += ["", f"UNPARSED: {r['unparsed']}"]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--revision", default=REVISION, help="dataset revision to pin to")
    ap.add_argument("--local-dir", help="measure *.json in this directory instead of fetching")
    ap.add_argument("--out", default=str(Path(__file__).parent / "results.json"))
    args = ap.parse_args()

    if args.local_dir:
        paths = sorted(Path(args.local_dir).glob("*.json"))
    else:
        paths = [_load(args.revision, f) for f in _list_files(args.revision)]
    if not paths:
        print("no records found", file=sys.stderr)
        return 1

    result = measure(paths)
    result["dataset_revision"] = args.revision
    Path(args.out).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(summarize(result))
    print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

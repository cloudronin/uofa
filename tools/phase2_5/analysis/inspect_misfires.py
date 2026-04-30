"""Sample misfires for the propose step.

Per spec §4 step 1 ("inspect misfires"):
- 5 negative_control misfires (rule fired but should not have)
- 5 bystander misfires (rule fired on a confirm_existing variant
  whose target_weakener is something else)

For each sampled package, we dump the structural fields the rule's
predicate is keyed on so the propose step has concrete material to
narrow against. Output is JSON-on-stdout (or -o file) so propose can
ingest it programmatically.

CLI: ``python -m tools.phase2_5.inspect_misfires --rule W-EP-01``
"""

from __future__ import annotations

import argparse
import csv
import json
import random
from pathlib import Path

# Same fixed seed so two `inspect` runs hit the same sample
INSPECT_SEED = 20260427


def _read_outcomes(outcomes_csv: Path) -> list[dict]:
    with open(outcomes_csv) as f:
        return list(csv.DictReader(f))


def _resolve_package_path(row: dict, batch_dir: Path) -> Path | None:
    """Mirror of metrics._resolve_package_path; duplicated to avoid
    cross-module dep churn (this is a CLI inspector, not in the loop)."""
    spec_id = row["spec_id"]
    variant_num = int(row["variant_num"])
    intent = row.get("coverage_intent", "")
    category_map = {
        "confirm_existing": "confirm_existing",
        "gap_probe": "gap_probe",
        "negative_control": "negative_controls",
        "interaction": "interaction",
    }
    category = category_map.get(intent, intent)
    cell_dir = batch_dir / category / spec_id
    if cell_dir.exists():
        candidates = list(cell_dir.glob(f"*-v{variant_num:02d}.jsonld"))
        if candidates:
            return candidates[0]
    return None


def _summarize_package(pkg_path: Path) -> dict:
    """Pull the rule-relevant structural fields out of a JSON-LD package.

    We don't try to be exhaustive — just enough material that the propose
    step can spot why the rule mis-triggered.
    """
    try:
        data = json.loads(pkg_path.read_text())
    except Exception as e:
        return {"error": f"failed to parse: {e}"}

    # Walk the @graph for the interesting node types.
    graph = data.get("@graph", []) if isinstance(data, dict) else []
    summary: dict = {
        "package_path": str(pkg_path),
        "id": data.get("@id"),
        "factors": [],
        "decisions": [],
        "hashes": [],
        "shapes": [],
        "claims_about": [],
        "applicability": [],
        "validation_results": [],
        "qualifiers": [],
    }

    for n in graph:
        if not isinstance(n, dict):
            continue
        t = n.get("@type")
        types = t if isinstance(t, list) else ([t] if t else [])
        for ty in types:
            ty_short = str(ty).rsplit("#", 1)[-1].rsplit("/", 1)[-1].rsplit(":", 1)[-1]
            if "Factor" in ty_short:
                summary["factors"].append({
                    "id": n.get("@id"),
                    "value": n.get("hasValue") or n.get("value"),
                    "rationale": n.get("rationale"),
                })
            elif "Decision" in ty_short:
                summary["decisions"].append({
                    "id": n.get("@id"),
                    "outcome": n.get("hasOutcome") or n.get("outcome"),
                    "basis": n.get("hasBasis") or n.get("basis"),
                })
            elif "Hash" in ty_short or "Provenance" in ty_short:
                summary["hashes"].append({"id": n.get("@id"), "type": ty_short})
            elif "Shape" in ty_short or "Profile" in ty_short:
                summary["shapes"].append({"id": n.get("@id"), "type": ty_short})
            elif "Claim" in ty_short:
                summary["claims_about"].append({
                    "id": n.get("@id"),
                    "subject": n.get("hasSubject"),
                    "predicate": n.get("hasPredicate"),
                })
            elif "Applicability" in ty_short or "Scope" in ty_short:
                summary["applicability"].append({"id": n.get("@id"), "type": ty_short})
            elif "ValidationResult" in ty_short:
                summary["validation_results"].append({
                    "id": n.get("@id"),
                    "level": n.get("resultSeverity"),
                    "message": n.get("resultMessage"),
                })
            elif "Qualifier" in ty_short or "Quantitative" in ty_short:
                summary["qualifiers"].append({"id": n.get("@id"), "type": ty_short})
    return summary


def sample_misfires(
    rule_id: str,
    outcomes_csv: Path,
    batch_dir: Path,
    n_nc: int = 5,
    n_bystander: int = 5,
    seed: int = INSPECT_SEED,
) -> dict:
    """Return {nc_misfires: [...], bystander_misfires: [...]} samples
    where rule_id fired but the variant was not the rule's target.
    """
    rows = _read_outcomes(outcomes_csv)
    rng = random.Random(seed)

    nc_misfires: list[dict] = []
    by_misfires: list[dict] = []
    for r in rows:
        fired = {p.strip() for p in (r.get("rules_fired") or "").split(",") if p.strip()}
        if rule_id not in fired:
            continue
        intent = r.get("coverage_intent")
        if intent == "negative_control" and r.get("outcome_class") != "GEN-INVALID":
            nc_misfires.append(r)
        elif intent == "confirm_existing" and r.get("target_weakener") not in (rule_id, ""):
            by_misfires.append(r)

    rng.shuffle(nc_misfires)
    rng.shuffle(by_misfires)
    nc_sample = nc_misfires[:n_nc]
    by_sample = by_misfires[:n_bystander]

    def _hydrate(row: dict) -> dict:
        pkg_path = _resolve_package_path(row, batch_dir)
        return {
            "outcome_row": {
                "spec_id": row.get("spec_id"),
                "variant_num": row.get("variant_num"),
                "coverage_intent": row.get("coverage_intent"),
                "target_weakener": row.get("target_weakener"),
                "outcome_class": row.get("outcome_class"),
                "rules_fired": row.get("rules_fired"),
                "base_cou_key": row.get("base_cou_key"),
            },
            "package": _summarize_package(pkg_path) if pkg_path else {"error": "package not found"},
        }

    return {
        "rule_id": rule_id,
        "n_nc_total_misfires": len(nc_misfires),
        "n_bystander_total_misfires": len(by_misfires),
        "nc_misfires": [_hydrate(r) for r in nc_sample],
        "bystander_misfires": [_hydrate(r) for r in by_sample],
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--rule", required=True)
    p.add_argument(
        "--outcomes", type=Path,
        default=Path("out/adversarial/phase2/2026-04-26/coverage/outcomes.csv"),
    )
    p.add_argument(
        "--batch-dir", type=Path,
        default=Path("out/adversarial/phase2/2026-04-26"),
    )
    p.add_argument("--n-nc", type=int, default=5)
    p.add_argument("--n-bystander", type=int, default=5)
    p.add_argument("--seed", type=int, default=INSPECT_SEED)
    p.add_argument("-o", "--output", type=Path, default=None)
    args = p.parse_args(argv)

    sample = sample_misfires(
        rule_id=args.rule,
        outcomes_csv=args.outcomes,
        batch_dir=args.batch_dir,
        n_nc=args.n_nc,
        n_bystander=args.n_bystander,
        seed=args.seed,
    )
    text = json.dumps(sample, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text)
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

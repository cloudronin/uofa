"""PR-curve plotting (per-rule trajectory + catalog-wide milestones).

Per the user-added requirement (plan §"PR-curve infrastructure"): each
plot uses TWO labeled Y-series so the spec's specificity framing AND
the strict precision-recall framing both render side-by-side without
the lossy "1 − FPR is precision" conflation.

- Per-rule trajectory: one PNG per refined rule.
- Catalog-wide milestone scatter: a single PNG; one point per
  (catalog version, batch population) — M5 baseline → after rule 1
  locks → … → final.

CLI:
    ``python -m tools.phase2_5.plot_pr --rule W-EP-01``     # per-rule
    ``python -m tools.phase2_5.plot_pr --catalog``           # milestone scatter
    ``python -m tools.phase2_5.plot_pr --all``               # both, all rules
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path

# Matplotlib Agg backend works headless and is committed already in
# requirements (used by tests). Import lazily so unit tests that don't
# plot don't pull it in.


@dataclass
class IterPoint:
    iteration: int
    recall: float
    precision: float
    specificity: float
    nc_fpr: float
    decision: str           # accepted-auto | provisional | reverted | etc.
    target_zone_reached: bool = False


def _load_iterations(log_path: Path, rule_id: str) -> list[IterPoint]:
    """Read refinement_log.jsonl and pull iteration points for *rule_id*."""
    if not log_path.exists():
        return []
    points: list[IterPoint] = []
    with open(log_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            if rec.get("rule_id") != rule_id:
                continue
            train = rec.get("train_metrics") or {}
            if not train:
                continue
            points.append(IterPoint(
                iteration=rec["iteration"],
                recall=float(train.get("recall", 0.0)),
                precision=float(train.get("precision", 0.0)),
                specificity=float(train.get("specificity", 0.0)),
                nc_fpr=float(train.get("nc_fpr", 0.0)),
                decision=rec.get("review_decision", ""),
                target_zone_reached=bool(rec.get("target_zone_reached", False)),
            ))
    return points


def _color_for_iter(p: IterPoint) -> str:
    """Color a per-iter point per the metric-gate policy:

    - green (target zone): accepted-auto OR accepted-no-edit
    - yellow (provisional): cleared hard floors but not target zone
    - red (reverted): hard floor violation, sentinel loosening, or no-op
    - gray: stuck / rejected-baseline / unknown
    """
    d = p.decision
    if d in ("accepted-auto", "accepted-no-edit"):
        return "green"
    if d == "provisional":
        return "gold"
    if d in ("reverted", "rejected-noop"):
        return "red"
    return "gray"


def plot_rule_trajectory(
    rule_id: str,
    log_path: Path,
    baseline: dict | None,
    out_path: Path,
) -> Path:
    """Per-rule trajectory: solid = precision, dashed = specificity, both vs recall."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    pts = _load_iterations(log_path, rule_id)

    fig, ax = plt.subplots(figsize=(7, 5))
    if baseline:
        # Plot baseline as a black star at iteration 0
        ax.scatter([baseline["recall"]], [baseline["precision"]], marker="*",
                   color="black", s=120, label="baseline (precision)", zorder=5)
        ax.scatter([baseline["recall"]], [baseline["specificity"]], marker="*",
                   color="gray", s=120, label="baseline (specificity)", zorder=5)

    if pts:
        # Bucket points by decision color
        green = [p for p in pts if _color_for_iter(p) == "green"]
        yellow = [p for p in pts if _color_for_iter(p) == "gold"]
        red = [p for p in pts if _color_for_iter(p) == "red"]
        gray = [p for p in pts if _color_for_iter(p) == "gray"]

        # Solid line through GREEN (locked) iterations on precision axis
        if green:
            xs = [p.recall for p in green]
            ax.plot(xs, [p.precision for p in green], "-o",
                    color="green", label="precision (target zone)")
            ax.plot(xs, [p.specificity for p in green], "--s",
                    color="green", label="specificity (target zone)")
            for p in green:
                ax.annotate(f"#{p.iteration}",
                            (p.recall, p.precision),
                            textcoords="offset points", xytext=(5, 5), fontsize=8)
        # Yellow markers for provisional
        if yellow:
            ax.scatter([p.recall for p in yellow], [p.precision for p in yellow],
                       marker="o", color="gold", alpha=0.7,
                       label="precision (provisional)")
            ax.scatter([p.recall for p in yellow], [p.specificity for p in yellow],
                       marker="s", color="gold", alpha=0.7,
                       label="specificity (provisional)")
            for p in yellow:
                ax.annotate(f"#{p.iteration}",
                            (p.recall, p.precision),
                            textcoords="offset points", xytext=(5, 5),
                            fontsize=8, color="goldenrod")
        # Red markers for reverted
        if red:
            ax.scatter([p.recall for p in red], [p.precision for p in red],
                       marker="x", color="red", alpha=0.5,
                       label="precision (reverted)")
            ax.scatter([p.recall for p in red], [p.specificity for p in red],
                       marker="+", color="red", alpha=0.5,
                       label="specificity (reverted)")
        # Gray markers for stuck/rejected-baseline
        if gray:
            ax.scatter([p.recall for p in gray], [p.precision for p in gray],
                       marker="d", color="gray", alpha=0.5,
                       label="precision (stuck/rejected)")

    # Reference lines per the new policy
    ax.axvline(0.90, color="green", linestyle=":", alpha=0.4, label="recall ≥ 0.90 (target)")
    ax.axhline(0.90, color="green", linestyle=":", alpha=0.4, label="metric ≥ 0.90 (target)")
    # Hard floors
    ax.axvline(0.80, color="red", linestyle=":", alpha=0.3, label="recall hard floor 0.80")

    ax.set_xlim(0, 1.05)
    ax.set_ylim(0, 1.05)
    ax.set_xlabel("Recall (TP / target population)")
    ax.set_ylabel("Precision (solid) / Specificity (dashed)")
    ax.set_title(f"{rule_id} refinement trajectory")
    ax.legend(fontsize=7, loc="lower left")
    ax.grid(alpha=0.3)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(out_path, dpi=120)
    plt.close(fig)
    return out_path


def _catalog_metrics_from_outcomes(outcomes_csv: Path) -> dict:
    """Compute aggregate catalog precision + specificity + recall.

    - precision: TP / (TP + FP) where TP = confirm_existing rows where
      target_weakener ∈ rules_fired, FP = (negative_control + bystander)
      rows where ANY rule fired.
    - specificity: 1 − (NC fires / NC total).
    - recall: confirm_existing TP / confirm_existing total.
    """
    rows = list(csv.DictReader(open(outcomes_csv)))
    tp = fp = ce_total = nc_total = nc_fires = 0
    for r in rows:
        intent = r.get("coverage_intent", "")
        fired_set = {p.strip() for p in (r.get("rules_fired") or "").split(",") if p.strip()}
        if intent == "confirm_existing":
            ce_total += 1
            target = r.get("target_weakener", "")
            if target and target in fired_set:
                tp += 1
            else:
                # If something else fired on a confirm_existing variant,
                # we count it as bystander-FP at the catalog level
                if fired_set:
                    fp += 1
        elif intent == "negative_control" and r.get("outcome_class") != "GEN-INVALID":
            nc_total += 1
            if fired_set:
                fp += 1
                nc_fires += 1
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / ce_total if ce_total else 0.0
    specificity = (1.0 - nc_fires / nc_total) if nc_total else 0.0
    return {"precision": precision, "recall": recall, "specificity": specificity}


def plot_catalog_milestones(
    milestones_dir: Path, out_path: Path, label_map: dict[str, str] | None = None
) -> Path:
    """Catalog-wide milestone scatter from milestones/{label}.csv files."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(8, 5))
    points = []
    for csv_path in sorted(milestones_dir.glob("*.csv")):
        label = csv_path.stem
        m = _catalog_metrics_from_outcomes(csv_path)
        m["label"] = (label_map or {}).get(label, label)
        points.append(m)

    if points:
        xs = [p["recall"] for p in points]
        ax.plot(xs, [p["precision"] for p in points], "-o",
                color="C0", label="catalog precision")
        ax.plot(xs, [p["specificity"] for p in points], "--s",
                color="C1", label="catalog specificity")
        for p in points:
            ax.annotate(p["label"], (p["recall"], p["precision"]),
                        textcoords="offset points", xytext=(5, 5), fontsize=7)

    ax.set_xlim(0, 1.05)
    ax.set_ylim(0, 1.05)
    ax.set_xlabel("Catalog recall (TP / confirm_existing total)")
    ax.set_ylabel("Catalog precision / specificity")
    ax.set_title("Catalog-wide milestone trajectory (Phase 2.5)")
    ax.legend(fontsize=8, loc="best")
    ax.grid(alpha=0.3)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(out_path, dpi=120)
    plt.close(fig)
    return out_path


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--rule", default=None)
    p.add_argument("--all", action="store_true", help="all rules + catalog")
    p.add_argument("--catalog", action="store_true", help="catalog milestone scatter only")
    p.add_argument(
        "--log-path", type=Path,
        default=Path("out/phase2_5/shared/refinement_log.jsonl"),
    )
    p.add_argument(
        "--milestones-dir", type=Path,
        default=Path("out/phase2_5/shared/milestones"),
    )
    p.add_argument(
        "--plots-dir", type=Path,
        default=Path("out/phase2_5/shared/plots"),
    )
    p.add_argument(
        "--baseline-json", type=Path, default=None,
        help="optional JSON with baseline {recall, precision, specificity} for the rule",
    )
    args = p.parse_args(argv)

    from tools.phase2_5.refinement_loop.split import ALL_RULES

    rules: list[str] = []
    if args.rule:
        rules = [args.rule]
    elif args.all:
        rules = list(ALL_RULES)
    elif not args.catalog:
        p.error("provide --rule, --all, or --catalog")

    for r in rules:
        rule_slug = r.lower().replace("-", "_")
        out_path = args.plots_dir / f"{rule_slug}_trajectory.png"
        baseline = None
        if args.baseline_json and args.baseline_json.exists():
            baseline = json.loads(args.baseline_json.read_text())
        path = plot_rule_trajectory(r, args.log_path, baseline, out_path)
        print(f"{r} → {path}")

    if args.all or args.catalog:
        out_path = args.plots_dir / "catalog_milestones.png"
        path = plot_catalog_milestones(args.milestones_dir, out_path)
        print(f"catalog → {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

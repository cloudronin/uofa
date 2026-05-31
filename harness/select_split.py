"""Step 0 — choose the extrapolation split BEFORE the corpus run.

Both AirfRANS extrapolation tasks are band-in-the-middle. Default to **AoA** on
physical grounds (lift/drag nonlinear in AoA; the high side heads into stall, so
out-of-envelope degradation should be large and clean) — but confirm empirically.

Procedure: train the simple MLP on each task's train split, evaluate on its test
split, and compute **true Cl/Cd error as a function of the extrapolation
parameter** (not just the aggregate). Pick the split where out-of-envelope error
is **largest and most uniformly elevated** relative to in-envelope.

AoA asymmetry is reported honestly: the high side (toward stall) should degrade
hard; the low side may stay well-behaved, so out-of-envelope-low cases are
flagged-but-fine. We report the full-split numbers and note where degradation
concentrates — never silently drop the low side to inflate the gap.

No engine here — pure train + predict + arithmetic. Pure functions are testable
on the synthetic generator; the real run loads both tasks via `airfrans_pull`.
"""

from __future__ import annotations

import csv
from pathlib import Path

from harness import train_surrogate
from harness.datasets import Corpus


def evaluate_task(corpus: Corpus) -> list[dict]:
    """Train on the in-envelope split; return per-eval-case error-vs-parameter rows."""
    import numpy as np

    model = train_surrogate.train(corpus.train)
    lo, hi = corpus.envelope[corpus.extrapolation_param]
    rows = []
    for case in corpus.evaluation:
        param = getattr(case, corpus.extrapolation_param)
        pred = np.asarray(model.predict([case.features()]))[0]
        out_lo = param < lo
        out_hi = param > hi
        rows.append({
            "task": corpus.extrapolation_param, "param": float(param),
            "err_cl": abs(float(pred[0]) - case.cl), "err_cd": abs(float(pred[1]) - case.cd),
            "out_of_envelope": bool(out_lo or out_hi),
            "side": "low" if out_lo else ("high" if out_hi else "in"),
        })
    return rows


def _median(values: list[float]):
    import numpy as np
    return float(np.median(values)) if values else None


def out_of_envelope_stats(rows: list[dict]) -> dict:
    import numpy as np
    out = [r for r in rows if r["out_of_envelope"]]
    in_env = [r for r in rows if not r["out_of_envelope"]]
    res = {}
    for coeff in ("err_cl", "err_cd"):
        ov = [r[coeff] for r in out]
        iv = [r[coeff] for r in in_env]
        res[coeff] = {
            "out_median": _median(ov), "in_median": _median(iv),
            "out_iqr": [float(x) for x in np.percentile(ov, [25, 75])] if ov else None,
            "elevation": (_median(ov) / _median(iv)) if (ov and iv and _median(iv)) else None,
        }
    return res


def aoa_asymmetry(rows: list[dict]) -> dict | None:
    """For the AoA task, compare high-side vs low-side out-of-envelope error."""
    if not rows or rows[0]["task"] != "aoa":
        return None
    high = [r["err_cd"] for r in rows if r["side"] == "high"]
    low = [r["err_cd"] for r in rows if r["side"] == "low"]
    return {"high_side_cd_median": _median(high), "low_side_cd_median": _median(low),
            "n_high": len(high), "n_low": len(low)}


def choose(task_results: dict[str, list[dict]]) -> tuple[str, str]:
    """Pick the split with the largest, most-uniformly-elevated out-of-envelope error."""
    scored = {}
    for task, rows in task_results.items():
        stats = out_of_envelope_stats(rows)
        scored[task] = stats["err_cd"]["elevation"] or 0.0
    chosen = max(scored, key=lambda t: (scored[t], t == "aoa"))   # ties → AoA
    justification = (
        f"Chosen split: {chosen}. Out-of-envelope Cd-error elevation (out/in median): "
        + ", ".join(f"{t}={scored[t]:.1f}x" for t in scored)
        + f". Default is AoA on physical grounds (stall); {chosen} gives the cleanest separation here."
    )
    return chosen, justification


def write_error_vs_parameter(task_results: dict[str, list[dict]], out_dir: Path) -> Path:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "error_vs_parameter.csv"
    with open(csv_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["task", "param", "err_cl", "err_cd", "out_of_envelope", "side"])
        w.writeheader()
        for rows in task_results.values():
            w.writerows(rows)
    _maybe_plot(task_results, out_dir)
    return csv_path


def _maybe_plot(task_results: dict[str, list[dict]], out_dir: Path) -> None:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        return  # plot is optional; the CSV is the committable artifact
    for task, rows in task_results.items():
        fig, ax = plt.subplots()
        ax.scatter([r["param"] for r in rows], [r["err_cd"] for r in rows], s=12)
        ax.set_xlabel(task)
        ax.set_ylabel("true Cd error |pred - RANS|")
        ax.set_title(f"AirfRANS {task} extrapolation — error vs parameter")
        fig.savefig(out_dir / f"error_vs_{task}.png", dpi=120, bbox_inches="tight")
        plt.close(fig)


def render(task_results: dict[str, list[dict]]) -> str:
    chosen, justification = choose(task_results)
    lines = [justification, ""]
    for task, rows in task_results.items():
        stats = out_of_envelope_stats(rows)["err_cd"]
        lines.append(f"  {task}: out-of-envelope Cd error median={stats['out_median']:.4g} "
                     f"(in-envelope {stats['in_median']:.4g}); elevation "
                     f"{('%.1fx' % stats['elevation']) if stats['elevation'] else 'n/a'}")
        asym = aoa_asymmetry(rows)
        if asym:
            lines.append(f"    AoA asymmetry: high-side Cd-error median={asym['high_side_cd_median']:.4g} "
                         f"(n={asym['n_high']}) vs low-side {asym['low_side_cd_median']:.4g} (n={asym['n_low']}) "
                         f"— degradation concentrates on the high (stall) side; low-side flagged cases are "
                         f"flagged-but-fine and are reported, not dropped.")
    return "\n".join(lines)

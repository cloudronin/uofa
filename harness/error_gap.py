"""Experiment A's hard number: the true-error gap between fired and unfired cases.

Pure arithmetic over the per-case table (no model, no SIP, no LLM). Partition by
``w_surr_03_fired``; per group report the true-error distribution of Cl and Cd
(median + IQR + mean) as grounded measurements; the headline is the ratio of
flagged-group error to unflagged-group error per coefficient. Plus the
plausibility check: flagged predictions look physically reasonable while their
true error is large — the invisible-danger trap.

The report carries NO threshold / verdict / pass-fail language: it states what
the envelope weakener firing co-occurs with (large true error), and where that
co-occurrence concentrates. The engineer decides.
"""

from __future__ import annotations

import json
from pathlib import Path

# Believable physical ranges for an airfoil; used ONLY to show flagged
# predictions are not self-evidently broken (the trap), never as a verdict.
_PLAUSIBLE_CL = (-2.5, 2.5)
_PLAUSIBLE_CD = (0.0, 0.6)

SCOPING_SENTENCE = (
    "Scope: this measures out-of-envelope inadequacy specifically — a surrogate "
    "accurate in-envelope but silently wrong outside it. It does not measure "
    "in-envelope-but-still-bad surrogates, which is a different check."
)


def load_table(path: Path) -> list[dict]:
    path = Path(path)
    if path.suffix == ".jsonl":
        return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    import csv
    with open(path, newline="") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        for k in ("reynolds", "aoa", "pred_cl", "pred_cd", "ref_cl", "ref_cd", "err_cl", "err_cd"):
            r[k] = float(r[k])
        r["w_surr_03_fired"] = str(r["w_surr_03_fired"]).lower() in ("true", "1")
    return rows


def partition(rows: list[dict]) -> tuple[list[dict], list[dict]]:
    """Mechanical split by w_surr_03_fired — no thresholding."""
    fired = [r for r in rows if r["w_surr_03_fired"]]
    unfired = [r for r in rows if not r["w_surr_03_fired"]]
    return fired, unfired


def _distribution(rows: list[dict], key: str) -> dict:
    import numpy as np
    vals = np.array([r[key] for r in rows], dtype=float)
    if vals.size == 0:
        return {"count": 0, "median": None, "iqr": None, "mean": None}
    q1, med, q3 = np.percentile(vals, [25, 50, 75])
    return {"count": int(vals.size), "median": float(med),
            "iqr": [float(q1), float(q3)], "mean": float(vals.mean())}


def error_gap(rows: list[dict]) -> dict:
    fired, unfired = partition(rows)
    out: dict = {"n_fired": len(fired), "n_unfired": len(unfired), "coefficients": {}}
    for coeff, key in (("cl", "err_cl"), ("cd", "err_cd")):
        f_dist = _distribution(fired, key)
        u_dist = _distribution(unfired, key)
        ratio = None
        if f_dist["median"] is not None and u_dist["median"] not in (None, 0.0):
            ratio = f_dist["median"] / u_dist["median"]
        out["coefficients"][coeff] = {"fired": f_dist, "unfired": u_dist, "median_ratio": ratio}
    return out


def plausibility(rows: list[dict]) -> dict:
    """Show flagged predictions are plausible-looking yet wrong (the trap)."""
    fired, _ = partition(rows)
    lo_cl, hi_cl = _PLAUSIBLE_CL
    lo_cd, hi_cd = _PLAUSIBLE_CD
    import math

    def _finite_and_plausible(r) -> bool:
        return (
            all(math.isfinite(r[k]) for k in ("pred_cl", "pred_cd"))
            and lo_cl <= r["pred_cl"] <= hi_cl and lo_cd <= r["pred_cd"] <= hi_cd
        )

    plausible = [r for r in fired if _finite_and_plausible(r)]
    err = _distribution(plausible, "err_cd") if plausible else {"count": 0, "median": None}
    return {
        "n_fired": len(fired),
        "n_flagged_predictions_plausible_looking": len(plausible),
        "plausible_looking_cd_error": err,   # plausible-looking yet wrong
    }


def render_report(rows: list[dict], *, split_label: str = "extrapolation") -> str:
    gap = error_gap(rows)
    plaus = plausibility(rows)
    lines: list[str] = []
    lines.append(f"AirfRANS {split_label} — envelope-weakener error-gap (vs RANS ground truth)")
    lines.append(f"  group sizes: fired={gap['n_fired']}  not-fired={gap['n_unfired']}")
    lines.append("")
    lines.append("True-error distributions (|prediction − RANS reference|), grounded measurements:")
    lines.append(f"  {'coeff':<6}{'group':<11}{'count':>7}{'median':>12}{'mean':>12}{'IQR':>22}")
    for coeff in ("cl", "cd"):
        c = gap["coefficients"][coeff]
        for grp in ("fired", "unfired"):
            d = c[grp]
            iqr = f"[{d['iqr'][0]:.4g}, {d['iqr'][1]:.4g}]" if d.get("iqr") else "—"
            med = f"{d['median']:.4g}" if d["median"] is not None else "—"
            mean = f"{d['mean']:.4g}" if d.get("mean") is not None else "—"
            lines.append(f"  {coeff:<6}{grp:<11}{d['count']:>7}{med:>12}{mean:>12}{iqr:>22}")
    lines.append("")
    lines.append("Headline (median true-error ratio, fired ÷ not-fired):")
    for coeff in ("cl", "cd"):
        r = gap["coefficients"][coeff]["median_ratio"]
        lines.append(f"  {coeff.upper()}: {('%.1f×' % r) if r is not None else 'n/a'} "
                     f"(flagged-case error is {('%.1f×' % r) if r is not None else 'n/a'} the unflagged-case error)")
    lines.append("")
    lines.append("Plausibility of flagged predictions (the invisible-danger trap):")
    pe = plaus["plausible_looking_cd_error"]
    pe_med = f"{pe['median']:.4g}" if pe.get("median") is not None else "—"
    lines.append(f"  {plaus['n_flagged_predictions_plausible_looking']}/{plaus['n_fired']} flagged "
                 f"predictions are finite and in a believable Cl/Cd range,")
    lines.append(f"  yet their median Cd true error is {pe_med} — plausible-looking, measurably wrong.")
    lines.append("")
    lines.append(SCOPING_SENTENCE)
    return "\n".join(lines)

"""Slice out-of-envelope FIRED cases by side and by geometry (thickness).

Answers a specific question the AoA selection pass raised: when out-of-envelope
error concentrates on one side (here the low-AoA side), is the elevation **broad**
across those cases (a real finding that contradicts the stall assumption) or
**driven by a few extreme-geometry outliers** (the thickness confound resurfacing)?

Pure arithmetic over the per-case table (which now carries g1=camber, g2=max
thickness). Reports numbers only — thickness-tercile breakdown + a confound
diagnostic (does dropping the thickest third collapse the elevation? how strongly
does thickness rank-correlate with error?). No verdict; the engineer reads it.
"""

from __future__ import annotations


def _median(xs):
    import numpy as np
    return float(np.median(xs)) if len(xs) else None


def fired_by_side(rows: list[dict], envelope: dict, param: str) -> dict:
    """Split FIRED cases into those below / above the envelope on `param`."""
    lo, hi = envelope[param]
    fired = [r for r in rows if r["w_surr_03_fired"]]
    return {
        "lo": lo, "hi": hi,
        "low": [r for r in fired if float(r[param]) < lo],
        "high": [r for r in fired if float(r[param]) > hi],
    }


def thickness_terciles(cases: list[dict], *, geom_key: str = "g2", err_key: str = "err_cd") -> list[dict]:
    """Sort by geometry, split into 3 equal-count bands; per-band count + median error."""
    cases = sorted(cases, key=lambda c: float(c[geom_key]))
    n = len(cases)
    if n == 0:
        return []
    thirds = [cases[: n // 3], cases[n // 3: 2 * n // 3], cases[2 * n // 3:]]
    out = []
    for label, grp in zip(("low-thickness", "mid-thickness", "high-thickness"), thirds):
        out.append({
            "band": label, "n": len(grp),
            "thickness_range": (float(grp[0][geom_key]), float(grp[-1][geom_key])) if grp else None,
            "median_err_cd": _median([c[err_key] for c in grp]),
            "median_err_cl": _median([c["err_cl"] for c in grp]),
        })
    return out


def confound_diagnostic(cases: list[dict], *, geom_key: str = "g2", err_key: str = "err_cd") -> dict:
    """Is the elevation broad or thickness-driven? Report the numbers, not a verdict.

    - median error over ALL cases vs over cases EXCLUDING the thickest tercile:
      if dropping the thickest third barely moves the median → broad; if it
      collapses → thickness-driven.
    - Spearman (rank) correlation of thickness vs error: near 0 → broad; strongly
      positive → thickness-driven.
    """
    import numpy as np
    n = len(cases)
    if n < 6:
        return {"n": n, "note": "too few fired cases on this side to slice"}
    cs = sorted(cases, key=lambda c: float(c[geom_key]))
    excl_top = cs[: 2 * n // 3]                      # drop the thickest tercile
    g = np.array([float(c[geom_key]) for c in cases])
    e = np.array([float(c[err_key]) for c in cases])
    gr = g.argsort().argsort().astype(float)         # ranks → Spearman = Pearson of ranks
    er = e.argsort().argsort().astype(float)
    rho = float(np.corrcoef(gr, er)[0, 1]) if n > 2 else None
    return {
        "n": n,
        "median_err_cd_all": _median([c[err_key] for c in cases]),
        "median_err_cd_excl_thickest_third": _median([c[err_key] for c in excl_top]),
        "spearman_thickness_vs_err_cd": rho,
    }


def render(rows: list[dict], envelope: dict, *, param: str = "aoa") -> str:
    s = fired_by_side(rows, envelope, param)
    lines = [f"Asymmetry slice — FIRED cases by side of the {param} envelope "
             f"[{s['lo']:.4g}, {s['hi']:.4g}] (g2 = max thickness %)"]
    for side in ("low", "high"):
        grp = s[side]
        m_cd, m_cl = _median([c["err_cd"] for c in grp]), _median([c["err_cl"] for c in grp])
        lines.append(f"\n  {side}-{param} fired: n={len(grp)}  "
                     f"median err_cd={m_cd:.4g}" if m_cd is not None else
                     f"\n  {side}-{param} fired: n={len(grp)}  median err_cd=—")
        if m_cl is not None:
            lines[-1] += f"  median err_cl={m_cl:.4g}"
        for b in thickness_terciles(grp):
            rng = f"[{b['thickness_range'][0]:.3g}, {b['thickness_range'][1]:.3g}]" if b["thickness_range"] else "—"
            mcd = f"{b['median_err_cd']:.4g}" if b["median_err_cd"] is not None else "—"
            lines.append(f"      {b['band']:<15} n={b['n']:>3}  thickness {rng:<16} median err_cd={mcd}")
        d = confound_diagnostic(grp)
        if "note" in d:
            lines.append(f"      ({d['note']})")
        else:
            rho = d["spearman_thickness_vs_err_cd"]
            lines.append(f"      confound check: median err_cd all={d['median_err_cd_all']:.4g} "
                         f"vs excl-thickest-third={d['median_err_cd_excl_thickest_third']:.4g}; "
                         f"Spearman(thickness, err_cd)={rho:.2f}" if rho is not None else "")
    lines.append("\n  (broad elevation: dropping the thickest third barely moves the median and "
                 "Spearman≈0; thickness-driven: the median collapses and Spearman is strongly positive)")
    return "\n".join(lines)

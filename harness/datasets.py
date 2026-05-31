"""Corpus data sources for Experiment A.

Two sources behind one shape (a list of `Case` rows + the declared training
envelope = the train-split bounds):

- ``synthetic_task`` — a deterministic, offline AirfRANS-*like* generator used by
  the CI tests. It reproduces the experiment's structure on purpose: a narrow
  AoA train band, a nonlinear **stall** past the high AoA boundary (so a model
  trained only in-band extrapolates plausibly-but-wrong), and a **well-behaved
  low side** (so out-of-envelope-but-fine cases exist) — which exercises the
  AoA-asymmetry honesty the experiment must report. No `airfrans`, no network.

- ``harness.airfrans_pull`` — the real AirfRANS pull (gated, network, ODbL),
  emitting the same `Case` shape from the documented extrapolation tasks.

A `Case` carries the inputs (reynolds, aoa, geometry) and the **RANS reference**
Cl/Cd (the ground-truth arbiter). The surrogate's predicted Cl/Cd are added
later by the corpus runner; true error is |pred − ref|.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Feature order the surrogate/adapter consumes, and the predicted QoIs.
FEATURES = ("reynolds", "aoa", "g1", "g2")
TARGETS = ("cl", "cd")


@dataclass
class Case:
    reynolds: float
    aoa: float
    g1: float           # geometry param (e.g. NACA max-camber-like)
    g2: float           # geometry param (e.g. NACA thickness-like)
    cl: float           # RANS reference lift coefficient (ground truth)
    cd: float           # RANS reference drag coefficient (ground truth)
    case_id: str = ""

    def features(self) -> list[float]:
        return [self.reynolds, self.aoa, self.g1, self.g2]


@dataclass
class Corpus:
    """Train + evaluation cases plus the declared training envelope.

    The declared envelope is the *train-split* bounds over the extrapolation
    parameter(s). The eval set deliberately spans BOTH sides of that boundary so
    W-SURR-03 partitions it into a fired and an unfired group.
    """
    train: list[Case]
    evaluation: list[Case]
    envelope: dict[str, tuple[float, float]]   # e.g. {"reynolds": (3e6, 5e6), "aoa": (-2.5, 12.5)}
    extrapolation_param: str                   # "aoa" or "reynolds"
    provenance: dict[str, Any] = field(default_factory=dict)


# ── Honest synthetic physics (AoA-driven, with stall + asymmetry) ────────────
# Pre-stall: Cl ~ linear in AoA (thin-airfoil-like). Past the high-AoA stall
# angle, Cl drops sharply and Cd jumps (the drag bucket collapses) — a strong
# nonlinearity a model trained only pre-stall cannot see. The LOW side stays
# linear/well-behaved, so out-of-envelope-low cases are flagged-but-fine.

_STALL_ANGLE = 14.0  # deg; lies just OUTSIDE a [-2.5, 12.5] train band


def _true_cl(aoa: float, g1: float) -> float:
    slope = 0.10 + 0.01 * g1            # per-degree lift slope, mild geometry effect
    if aoa <= _STALL_ANGLE:
        return slope * aoa             # linear pre-stall (and on the low side)
    # Post-stall: lift collapses.
    peak = slope * _STALL_ANGLE
    return peak - 0.18 * (aoa - _STALL_ANGLE)


def _true_cd(aoa: float, g2: float) -> float:
    base = 0.009 + 0.0006 * g2
    bucket = 0.00025 * aoa * aoa       # drag bucket, symmetric-ish
    stall_jump = 0.06 * max(0.0, aoa - _STALL_ANGLE)  # sharp rise past stall
    return base + bucket + stall_jump


def synthetic_task(
    *,
    seed: int = 0,
    n_train: int = 120,
    n_eval_in: int = 30,
    n_eval_high: int = 30,
    n_eval_low: int = 20,
    aoa_band: tuple[float, float] = (-2.5, 12.5),
    re_band: tuple[float, float] = (3.0e6, 5.0e6),
) -> Corpus:
    """Deterministic AoA-extrapolation corpus (no airfrans, no network).

    Train cases live strictly inside ``aoa_band``. Eval cases mix in-band
    (held-out), high-AoA out-of-band (toward/through stall → large true error),
    and low-AoA out-of-band (well-behaved → small true error, the asymmetry).
    """
    import numpy as np

    rng = np.random.RandomState(seed)
    lo, hi = aoa_band
    re_lo, re_hi = re_band

    def _mk(aoa_vals, tag):
        out = []
        for i, aoa in enumerate(aoa_vals):
            reynolds = float(rng.uniform(re_lo, re_hi))
            g1 = float(rng.uniform(0.0, 4.0))
            g2 = float(rng.uniform(8.0, 18.0))
            out.append(Case(
                reynolds=reynolds, aoa=float(aoa), g1=g1, g2=g2,
                cl=_true_cl(float(aoa), g1), cd=_true_cd(float(aoa), g2),
                case_id=f"{tag}-{i}",
            ))
        return out

    train = _mk(rng.uniform(lo, hi, n_train), "train")
    eval_in = _mk(rng.uniform(lo, hi, n_eval_in), "eval-in")
    eval_high = _mk(rng.uniform(hi + 0.5, 20.0, n_eval_high), "eval-high")   # past stall
    eval_low = _mk(rng.uniform(-8.0, lo - 0.5, n_eval_low), "eval-low")      # well-behaved

    return Corpus(
        train=train,
        evaluation=eval_in + eval_high + eval_low,
        envelope={"reynolds": re_band, "aoa": aoa_band},
        extrapolation_param="aoa",
        provenance={"source": "synthetic", "stall_angle_deg": _STALL_ANGLE, "seed": seed},
    )

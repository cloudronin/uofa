"""Real AirfRANS pull (gated; network + ODbL; not committed).

Pulls the AirfRANS extrapolation tasks via the `airfrans` package and emits the
same `Corpus` shape the synthetic generator does, so the rest of the harness is
source-agnostic. Cite **arXiv:2212.07564** (not the NeurIPS version).

This module is **best-effort against the documented airfrans API and cannot be
exercised offline** — the data download is large and license-bound. The three
lines that touch the airfrans API are marked `# VERIFY:` — confirm them against
the installed `airfrans` version on first real run. Everything downstream (the
`Corpus` contract, training, corpus run, error-gap) is exercised by the
synthetic E2E test.

Splits are AirfRANS's own band-in-the-middle extrapolation tasks:
  - reynolds: train 3–5M, test outside (both sides)
  - aoa:      train −2.5°…12.5°, test outside (both sides)
Each is used as-is; the declared envelope = the train-split bounds.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

from harness.datasets import Case, Corpus

# AirfRANS uses air kinematic viscosity to convert inlet velocity → Reynolds
# (chord = 1 m). Documented in the dataset; VERIFY against the installed value.
_NU_AIR = 1.56e-5
TASKS = ("aoa", "reynolds")


def default_root() -> Path:
    return Path(os.environ.get("UOFA_AIRFRANS_DIR", "dev/build/airfrans"))


def _require_airfrans():
    try:
        import airfrans  # noqa: F401
    except ImportError as exc:  # pragma: no cover - real-run only
        raise RuntimeError(
            "airfrans is required for the real pull. Install with: "
            "pip install uofa[interrogate-corpus]  (then `make airfrans-pull`)."
        ) from exc
    import airfrans
    return airfrans


def _parse_name(name: str) -> tuple[float, float, float, float]:
    """Parse (reynolds, aoa, g1, g2) from an AirfRANS simulation name.

    Names look like `airFoil2D_SST_<inletVelocity>_<angleOfAttack>_<NACA...>`.
    VERIFY the field order/positions against the installed dataset.
    """
    parts = name.split("_")
    nums = [float(p) for p in parts if re.fullmatch(r"-?\d+(\.\d+)?", p)]
    inlet_velocity, aoa = nums[0], nums[1]
    reynolds = inlet_velocity / _NU_AIR              # chord = 1 m
    g1 = nums[2] if len(nums) > 2 else 0.0           # NACA params as geometry features
    g2 = nums[3] if len(nums) > 3 else 0.0
    return reynolds, aoa, g1, g2


def _cases(airfrans, root: Path, names) -> list[Case]:
    cases = []
    for name in names:
        reynolds, aoa, g1, g2 = _parse_name(name)
        sim = airfrans.Simulation(root=str(root), name=name)   # VERIFY: ctor signature
        cd, cl = sim.force_coefficient()                       # VERIFY: returns (C_D, C_L)
        cd_total = float(cd[0] + cd[1]) if hasattr(cd, "__len__") else float(cd)  # pressure+viscous
        cl_total = float(cl[0] + cl[1]) if hasattr(cl, "__len__") else float(cl)
        cases.append(Case(reynolds=reynolds, aoa=aoa, g1=g1, g2=g2,
                          cl=cl_total, cd=cd_total, case_id=name))
    return cases


def load_airfrans(task: str = "aoa", root: Path | None = None) -> Corpus:
    """Load one extrapolation task as a Corpus (train + eval + declared envelope).

    eval = held-out in-band (last 20% of train) ∪ the out-of-band test split, so
    W-SURR-03 partitions the corpus into a fired and an unfired group.
    """
    airfrans = _require_airfrans()
    root = Path(root or default_root())

    _, train_names = airfrans.dataset.load(root=str(root), task=task, train=True)   # VERIFY
    _, test_names = airfrans.dataset.load(root=str(root), task=task, train=False)    # VERIFY

    train_all = _cases(airfrans, root, train_names)
    test_cases = _cases(airfrans, root, test_names)             # out-of-band (extrapolation)

    cut = max(1, int(0.8 * len(train_all)))
    train_cases, held_out_in_band = train_all[:cut], train_all[cut:]

    reynolds = [c.reynolds for c in train_cases]
    aoa = [c.aoa for c in train_cases]
    envelope = {"reynolds": (min(reynolds), max(reynolds)), "aoa": (min(aoa), max(aoa))}

    return Corpus(
        train=train_cases,
        evaluation=held_out_in_band + test_cases,
        envelope=envelope,
        extrapolation_param=task,
        provenance={"source": "airfrans", "task": task, "cite": "arXiv:2212.07564",
                    "root": str(root)},
    )

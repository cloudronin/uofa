"""Real AirfRANS pull (gated; network + ODbL; not committed).

Pulls the AirfRANS extrapolation tasks via the `airfrans` package and emits the
same `Corpus` shape the synthetic generator does, so the rest of the harness is
source-agnostic. Cite **arXiv:2212.07564** (not the NeurIPS version).

AirfRANS API used (verified against airfrans 0.1.5.1):
  - `airfrans.dataset.download(root, file_name='Dataset', unzip=True,
    OpenFOAM=False)` fetches the cropped .vtu/.vtp dataset + `manifest.json`.
  - `manifest.json` carries the split name-lists keyed `"<task>_train"` /
    `"<task>_test"` — read directly (the package's `dataset.load` would build
    every full point cloud just to return names, which we don't need).
  - `airfrans.Simulation(root, name)` exposes `inlet_velocity`, `NU` (kinematic
    viscosity at T), `angle_of_attack` (radians), and `force_coefficient()`
    which returns `((cd, cdp, cdv), (cl, clp, clv))` — totals are the first
    element of each tuple. Reynolds = inlet_velocity / NU (chord = 1 m).
  - Geometry: the simulation name is
    `airFoil2D_SST_<U>_<alpha_deg>_<naca digits...>_<idx>`; airfrans itself
    parses the NACA params as `name.split('_')[4:-1]`. We mirror that slice and
    take the leading shape param + trailing thickness as g1/g2.

Per-simulation force-coefficient extraction reads a mesh per case, so the
scalar Cases are cached to `_uofa_case_cache.json` under the data root; select →
train → corpus then reuse the cache instead of re-reading meshes.

Splits are AirfRANS's own band-in-the-middle extrapolation tasks (train inside a
narrow band, test outside on both sides). The declared envelope = the in-band
train-split bounds; the eval set = a held-out in-band fold (W-SURR-03 silent) ∪
the out-of-band test split (W-SURR-03 fires), so the corpus partitions cleanly.
"""

from __future__ import annotations

import json
import math
import os
import random
from pathlib import Path

from harness.datasets import Case, Corpus

TASKS = ("aoa", "reynolds")
_HOLDOUT_FRACTION = 0.2          # in-band fold held out of fitting → the unfired group
_SHUFFLE_SEED = 0                # deterministic i.i.d. train/holdout split
_CACHE_NAME = "_uofa_case_cache.json"


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


def _find_data_root(root: Path) -> Path | None:
    """Locate the directory holding manifest.json (the zip may nest a subdir)."""
    if (root / "manifest.json").exists():
        return root
    for hit in root.rglob("manifest.json"):
        return hit.parent
    return None


def download(root: Path | None = None) -> Path:
    """Ensure the dataset is present locally; return the dir holding manifest.json."""
    airfrans = _require_airfrans()
    root = Path(root or default_root())
    root.mkdir(parents=True, exist_ok=True)
    data_root = _find_data_root(root)
    if data_root is None:
        airfrans.dataset.download(root=str(root), file_name="Dataset", unzip=True, OpenFOAM=False)
        data_root = _find_data_root(root)
    if data_root is None:  # pragma: no cover - real-run only
        raise RuntimeError(f"AirfRANS manifest.json not found under {root} after download.")
    return data_root


def _manifest_names(data_root: Path, task: str) -> tuple[list[str], list[str]]:
    manifest = json.loads((data_root / "manifest.json").read_text())
    try:
        return list(manifest[f"{task}_train"]), list(manifest[f"{task}_test"])
    except KeyError as exc:  # pragma: no cover - real-run only
        raise RuntimeError(
            f"manifest.json has no '{task}_train'/'{task}_test' keys; "
            f"available: {sorted(manifest)}"
        ) from exc


def _geometry_from_name(name: str) -> tuple[float, float]:
    """(g1, g2) from the NACA params encoded in the simulation name.

    The name is `airFoil2D_SST_<U>_<alpha_deg>_<NACA params...>`; the params are
    `split('_')[4:]` (3 for a 4-digit profile, 4 for a 5-digit one) with **max
    thickness last** (the 10–20% trailing field). We take g1 = leading camber
    param, g2 = trailing thickness — thickness is the dominant Cd driver, so it
    must be a feature for the surrogate to be accurate in-envelope. (airfrans'
    own `[4:-1]` slice drops the thickness; we deliberately keep it.)
    """
    params = [float(d) for d in name.split("_")[4:]] or [0.0, 0.0]
    return params[0], params[-1]


def _extract_case(airfrans, data_root: Path, name: str) -> Case:
    sim = airfrans.Simulation(root=str(data_root), name=name)
    (cd, _cdp, _cdv), (cl, _clp, _clv) = sim.force_coefficient()
    g1, g2 = _geometry_from_name(name)
    reynolds = float(sim.inlet_velocity) / float(sim.NU)          # chord = 1 m
    aoa_deg = math.degrees(float(sim.angle_of_attack))
    return Case(reynolds=reynolds, aoa=aoa_deg, g1=g1, g2=g2,
                cl=float(cl), cd=float(cd), case_id=name)


def _cases_cached(airfrans, data_root: Path, names: list[str]) -> list[Case]:
    """Extract Cases for `names`, caching scalar rows so meshes are read once."""
    cache_path = data_root / _CACHE_NAME
    cache = json.loads(cache_path.read_text()) if cache_path.exists() else {}
    missing = [n for n in names if n not in cache]
    for i, name in enumerate(missing):
        c = _extract_case(airfrans, data_root, name)
        cache[name] = [c.reynolds, c.aoa, c.g1, c.g2, c.cl, c.cd]
        if (i + 1) % 50 == 0 or i + 1 == len(missing):
            print(f"  extracted force coefficients: {i + 1}/{len(missing)} new sims", flush=True)
    if missing:
        cache_path.write_text(json.dumps(cache))
    out = []
    for name in names:
        re_, aoa, g1, g2, cl, cd = cache[name]
        out.append(Case(reynolds=re_, aoa=aoa, g1=g1, g2=g2, cl=cl, cd=cd, case_id=name))
    return out


def _bounds(cases: list[Case]) -> dict[str, tuple[float, float]]:
    reynolds = [c.reynolds for c in cases]
    aoa = [c.aoa for c in cases]
    return {"reynolds": (min(reynolds), max(reynolds)), "aoa": (min(aoa), max(aoa))}


def load_airfrans(task: str = "aoa", root: Path | None = None) -> Corpus:
    """Load one extrapolation task as a Corpus (train + eval + declared envelope).

    The in-band train split is shuffled i.i.d. and cut 80/20: the 80% is the
    fit set whose bounds become the declared envelope; the 20% held-out fold is
    in-band-but-unseen (the unfired group, honest generalization error). The
    out-of-band test split is the fired group.
    """
    airfrans = _require_airfrans()
    if task not in TASKS:
        raise ValueError(f"task must be one of {TASKS}, got {task!r}")
    data_root = download(root)

    train_names, test_names = _manifest_names(data_root, task)
    random.Random(_SHUFFLE_SEED).shuffle(train_names)            # i.i.d. fold (deterministic)
    cut = max(1, int((1.0 - _HOLDOUT_FRACTION) * len(train_names)))
    fit_names, holdout_names = train_names[:cut], train_names[cut:]

    fit_cases = _cases_cached(airfrans, data_root, fit_names)
    holdout_cases = _cases_cached(airfrans, data_root, holdout_names)
    test_cases = _cases_cached(airfrans, data_root, test_names)  # out-of-band (extrapolation)

    return Corpus(
        train=fit_cases,
        evaluation=holdout_cases + test_cases,
        envelope=_bounds(fit_cases),
        extrapolation_param=task,
        provenance={"source": "airfrans", "task": task, "cite": "arXiv:2212.07564",
                    "root": str(data_root), "n_fit": len(fit_cases),
                    "n_holdout": len(holdout_cases), "n_test": len(test_cases)},
    )

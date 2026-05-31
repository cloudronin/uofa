"""Train an HONEST surrogate for Experiment A.

A deliberately simple sklearn `MLPRegressor` (no torch/GPU; the surrogate need
not be SOTA) over (reynolds, aoa, g1, g2) → (cl, cd). Trained ONLY on the
in-envelope train split. We do NOT tune for low extrapolation error — competent
in-envelope and visibly degrading outside it is the whole point.

The declared training envelope is recorded as the **actual extent of the train
data** over each dimension (so it can never leak the test range), and becomes
the surrogate's declared envelope in every COU the corpus runner builds.
"""

from __future__ import annotations

import json
from pathlib import Path

from harness.datasets import FEATURES, TARGETS, Case, Corpus


def declared_envelope(train_cases: list[Case]) -> dict[str, tuple[float, float]]:
    """The declared envelope = the per-dimension [min, max] of the TRAIN cases.

    Derived from the training data itself, so no out-of-envelope (test) range
    can leak into the declared envelope.
    """
    reynolds = [c.reynolds for c in train_cases]
    aoa = [c.aoa for c in train_cases]
    return {"reynolds": (min(reynolds), max(reynolds)), "aoa": (min(aoa), max(aoa))}


def train(train_cases: list[Case], *, seed: int = 0):
    """Fit a StandardScaler→MLPRegressor pipeline on the in-envelope split."""
    import numpy as np
    from sklearn.neural_network import MLPRegressor
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    X = np.array([c.features() for c in train_cases], dtype=float)
    y = np.array([[c.cl, c.cd] for c in train_cases], dtype=float)
    model = make_pipeline(
        StandardScaler(),
        MLPRegressor(hidden_layer_sizes=(64, 64), max_iter=2000, random_state=seed),
    )
    model.fit(X, y)
    return model


def save_surrogate(model, envelope: dict[str, tuple[float, float]], out_dir: Path) -> tuple[Path, Path]:
    """Persist the model (joblib) + the declared-envelope bounds (JSON)."""
    import joblib

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    model_path = out_dir / "surrogate.joblib"
    bounds_path = out_dir / "declared_envelope.json"
    joblib.dump(model, model_path)
    bounds_path.write_text(json.dumps({
        "features": list(FEATURES),
        "targets": list(TARGETS),
        "envelope": {k: list(v) for k, v in envelope.items()},
    }, indent=2), encoding="utf-8")
    return model_path, bounds_path


def train_and_save(corpus: Corpus, out_dir: Path, *, seed: int = 0) -> dict:
    """Train on the corpus's in-envelope split and persist model + bounds."""
    model = train(corpus.train, seed=seed)
    envelope = declared_envelope(corpus.train)
    model_path, bounds_path = save_surrogate(model, envelope, out_dir)
    return {"model_path": model_path, "bounds_path": bounds_path, "envelope": envelope}

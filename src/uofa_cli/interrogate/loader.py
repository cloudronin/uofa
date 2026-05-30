"""Benchmark + reference loader (SIP §3 component 2).

Ingests the supplied benchmark inputs and reference outputs. SIP orchestrates
the comparison; it does NOT manufacture truth — the reference is supplied (a
parent-solver result or experiment).

v1 supports ``.npz`` (primary) and ``.json``. Conventions:

  benchmark file:
    inputs        — N x D array of evaluation points
    input_names   — length-D array of dimension names

  reference file:
    ref__<qoi>          — length-N reference values for a quantity of interest
    constraint__<id>    — residual field for a declared physics constraint (optional)
    lower__<qoi>, upper__<qoi> — prediction-interval bounds for UQ coverage (optional)

``numpy`` is imported lazily (ships in the ``[interrogate]`` extra).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Benchmark:
    inputs: Any
    input_names: list[str]


@dataclass
class Reference:
    reference: dict[str, Any]
    constraint_fields: dict[str, Any] = field(default_factory=dict)
    uq_intervals: dict[str, tuple[Any, Any]] = field(default_factory=dict)


def _load_mapping(path: Path) -> dict[str, Any]:
    """Load an npz or json file into a flat ``{key: array/list}`` mapping."""
    suffix = path.suffix.lower()
    if suffix == ".npz":
        import numpy as np
        with np.load(path, allow_pickle=False) as data:
            return {k: data[k] for k in data.files}
    if suffix == ".json":
        return json.loads(path.read_text(encoding="utf-8"))
    raise ValueError(
        f"Unsupported data format {suffix!r} for {path}. Use .npz or .json."
    )


def load_benchmark(path: Path) -> Benchmark:
    raw = _load_mapping(Path(path))
    if "inputs" not in raw:
        raise ValueError(f"Benchmark {path} is missing an 'inputs' array.")
    names = raw.get("input_names")
    input_names = [str(n) for n in names] if names is not None else []
    return Benchmark(inputs=raw["inputs"], input_names=input_names)


def load_reference(path: Path) -> Reference:
    raw = _load_mapping(Path(path))
    reference: dict[str, Any] = {}
    constraints: dict[str, Any] = {}
    lowers: dict[str, Any] = {}
    uppers: dict[str, Any] = {}
    for key, value in raw.items():
        if key.startswith("ref__"):
            reference[key[len("ref__"):]] = value
        elif key.startswith("constraint__"):
            constraints[key[len("constraint__"):]] = value
        elif key.startswith("lower__"):
            lowers[key[len("lower__"):]] = value
        elif key.startswith("upper__"):
            uppers[key[len("upper__"):]] = value
    intervals = {
        qoi: (lowers[qoi], uppers[qoi]) for qoi in lowers if qoi in uppers
    }
    if not reference:
        raise ValueError(
            f"Reference {path} declares no 'ref__<qoi>' arrays — nothing to "
            f"compute residuals against."
        )
    return Reference(reference=reference, constraint_fields=constraints, uq_intervals=intervals)

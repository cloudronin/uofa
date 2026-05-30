"""Model adapter — the single contract between a user's surrogate and SIP.

SIP has NO native support for any model framework. The user wraps their model
(ONNX, PyTorch, sklearn, custom, remote endpoint) in a ``ModelAdapter`` subclass
implementing one method: ``predict(inputs) -> outputs``. This is the sprawl
containment — SIP never imports torch/onnx/sklearn; the user's adapter does.

``predict`` receives the benchmark inputs (an ``N x D`` array of evaluation
points) and returns a mapping ``{quantity_of_interest: array_of_N_predictions}``
so SIP can compute per-QoI residuals against the reference set.
"""

from __future__ import annotations

import importlib
import importlib.util
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class ModelAdapter(ABC):
    """One contract: turn benchmark inputs into per-QoI surrogate outputs.

    Subclasses load their own model (in ``__init__`` or lazily) using whatever
    framework they like. SIP only ever calls ``predict``.
    """

    @abstractmethod
    def predict(self, inputs: Any) -> dict[str, Any]:
        """Return ``{qoi_name: predictions}`` for the given ``inputs``.

        ``inputs`` is an ``N x D`` array-like of evaluation points;
        ``predictions`` is a length-``N`` array-like per quantity of interest.
        """
        raise NotImplementedError


def load_adapter(ref: str) -> ModelAdapter:
    """Resolve and instantiate a ``ModelAdapter`` from a reference string.

    Accepted forms:
      - ``"package.module.ClassName"`` — imported via ``importlib``.
      - ``"/path/to/file.py:ClassName"`` — loaded from a source file.

    The class is instantiated with no arguments (the adapter loads its own
    model). Raises ``ValueError`` if the target is not a ``ModelAdapter``
    subclass, ``ModuleNotFoundError``/``AttributeError`` if it can't be found.
    """
    cls = _resolve_class(ref)
    if not (isinstance(cls, type) and issubclass(cls, ModelAdapter)):
        raise ValueError(
            f"{ref!r} does not resolve to a ModelAdapter subclass "
            f"(got {cls!r}). Subclass uofa_cli.interrogate.adapter.ModelAdapter."
        )
    return cls()


def _resolve_class(ref: str):
    if ":" in ref and (ref.endswith(".py") or "/" in ref.split(":", 1)[0]):
        file_part, _, class_name = ref.partition(":")
        path = Path(file_part).expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(f"Adapter file not found: {path}")
        spec = importlib.util.spec_from_file_location(path.stem, path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load adapter module from {path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return getattr(module, class_name)

    module_path, _, class_name = ref.rpartition(".")
    if not module_path:
        raise ValueError(
            f"Adapter ref {ref!r} must be 'pkg.module.ClassName' or "
            f"'/path/to/file.py:ClassName'."
        )
    module = importlib.import_module(module_path)
    return getattr(module, class_name)

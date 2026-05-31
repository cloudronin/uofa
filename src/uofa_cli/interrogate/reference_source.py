"""Reference source — the pluggable boundary for *truth* SIP measures against.

Pack-shaped architecture spec §3a. The reference/solver is the *thing that
varies* — precomputed AirfRANS data, experimental data, a cached solver result,
or (downstream) a live OpenFOAM run. It must live behind a contract, not be
hardcoded, exactly as the model under test lives behind ``ModelAdapter``. This is
that contract, defined as **one whole interface now** (serve + generate) so
nothing forks between Product A (serve) and Product B (generate): Product B
*exercises more of the same interface* rather than reconciling a second one.

Two capabilities, one interface:
  - **serve** — :meth:`ReferenceSource.reference` returns truth for inputs that
    *have* answers (precomputed datasets, experimental data, cached results).
    Directly analogous to ``ModelAdapter.predict`` — same shape, opposite source
    (truth vs. prediction). This is what Product A's evidence path exercises.
  - **generate** — :meth:`ReferenceSource.generate` produces truth for *novel*
    inputs with no answer yet (run the solver). The heavier capability Product
    B's mitigation loop exercises. The contract is fixed now; a working
    generating source (VTK/OpenFOAM parsing, field→QoI reduction, convergence)
    is the downstream solver-ingest build — a separate spec — not this one.

**Capability-detection, not a dead method** (§3a): a serve-only source declares
``supports_generate() → False`` and does not carry a live ``generate``; the
consumer asks before invoking. A whole interface with a declared *optional*
capability, never a present-but-dead method.

**Firewall placement — the same for both halves** (§3a, decided once for the
whole interface so the Product-B *generate* half can't later be bolted on with a
different stance): a reference source feeds *truth into the measurement
comparison*, whether looked-up (*serve*) or computed (*generate*). Both halves
sit on the **reference side** of the firewall — they provide what SIP measures
against; they never produce verdicts, decisions, or actions. (Distinct from the
action/decision region governed by the §4 two-scope signing.)

SIP has NO native solver/dataset support: a user (or a premium pack) wraps their
truth source in a ``ReferenceSource`` subclass, exactly as ``adapter.py`` wraps a
model. SIP never imports VTK/OpenFOAM/airfrans; the source does.
"""

from __future__ import annotations

import importlib
import importlib.util
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from uofa_cli.interrogate.loader import Reference, load_reference

_DATA_SUFFIXES = {".npz", ".json"}


class ReferenceSource(ABC):
    """One contract for truth: serve precomputed answers, optionally generate new ones.

    Subclasses implement :meth:`reference` (serve). They MAY additionally support
    generation by overriding :meth:`supports_generate` to return True and
    implementing :meth:`generate`; a serve-only source leaves both at their
    defaults (no dead method). Mirrors the ``ModelAdapter`` ABC style — a thin,
    single-responsibility interface a pack implements, resolved by reference.
    """

    @abstractmethod
    def reference(self, inputs: Any = None) -> dict[str, Any]:
        """Serve truth: ``{qoi_name: reference_values}`` for the evaluation points.

        The serve analog of ``ModelAdapter.predict`` — same ``{qoi: array}`` shape,
        opposite source. ``inputs`` is accepted to mirror ``predict`` and to let a
        generating source key off the points; a precomputed source already holds
        the answers and may ignore it.
        """
        raise NotImplementedError

    def constraint_fields(self) -> dict[str, Any]:
        """Residual fields for declared physics constraints (``{constraintId: field}``).

        Reference-side supporting data SIP compares against; empty when the source
        carries none. Not a measurement and not a verdict.
        """
        return {}

    def uq_intervals(self) -> dict[str, tuple[Any, Any]]:
        """Prediction-interval bounds per QoI (``{qoi: (lower, upper)}``) for UQ coverage."""
        return {}

    def supports_generate(self) -> bool:
        """Whether this source can *generate* truth for novel inputs (capability-detection).

        Defaults to False — a serve-only source. The consumer asks this before
        invoking :meth:`generate`, so a serve-only source carries no dead method.
        """
        return False

    def generate(self, inputs: Any) -> dict[str, Any]:
        """Generate truth for *novel* inputs (run the solver). Optional capability.

        Default raises — a serve-only source declares it does not support
        generation via :meth:`supports_generate`. A generating source overrides
        both. Output sits on the reference side of the firewall, identical to
        :meth:`reference` (truth, never a verdict). Building a working generating
        source (the solver internals) is the downstream solver-ingest spec.
        """
        raise NotImplementedError(
            f"{type(self).__name__} is serve-only and does not support generation. "
            f"Check supports_generate() before calling generate()."
        )


class FileReferenceSource(ReferenceSource):
    """Serve-only reference source backed by a precomputed ``.npz``/``.json`` file.

    The Product-A evidence path's source: it serves precomputed reference values,
    constraint residual fields, and UQ interval bounds (the conventions in
    ``loader``). It declares ``supports_generate() → False`` and carries no
    ``generate`` — capability-detection, not a no-op (§3a). Proves the interface
    end to end without any generating internals.
    """

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self._data: Reference = load_reference(self.path)

    def reference(self, inputs: Any = None) -> dict[str, Any]:
        return self._data.reference

    def constraint_fields(self) -> dict[str, Any]:
        return self._data.constraint_fields

    def uq_intervals(self) -> dict[str, tuple[Any, Any]]:
        return self._data.uq_intervals


def to_reference(source: ReferenceSource, inputs: Any = None) -> Reference:
    """Materialize the in-memory :class:`Reference` SIP's measurements consume.

    The boundary between the pluggable source and SIP's internals: serve the
    three kinds of truth through the interface, then hand SIP the data container
    it already reads. Keeps the measurement methods unchanged while routing truth
    through ``ReferenceSource``.
    """
    return Reference(
        reference=source.reference(inputs),
        constraint_fields=source.constraint_fields(),
        uq_intervals=source.uq_intervals(),
    )


def load_reference_source(ref: str | Path) -> ReferenceSource:
    """Resolve a ``ReferenceSource`` from a data-file path or a class reference.

    Accepted forms (mirrors ``adapter.load_adapter``, with a data-file shortcut):
      - ``"/path/to/reference.npz"`` / ``".json"`` → a :class:`FileReferenceSource`
        (the precomputed serve-only source).
      - ``"package.module:ClassName"`` / ``"/path/file.py:ClassName"`` → a custom
        (e.g. premium, possibly generating) source, imported and instantiated.

    Raises ``ValueError`` if a class reference does not resolve to a
    ``ReferenceSource`` subclass.
    """
    ref_str = str(ref)
    if Path(ref_str).suffix.lower() in _DATA_SUFFIXES:
        return FileReferenceSource(ref_str)

    cls = _resolve_class(ref_str)
    if not (isinstance(cls, type) and issubclass(cls, ReferenceSource)):
        raise ValueError(
            f"{ref!r} does not resolve to a ReferenceSource subclass (got {cls!r}). "
            f"Subclass uofa_cli.interrogate.reference_source.ReferenceSource."
        )
    return cls()


def _resolve_class(ref: str):
    if ":" in ref and (ref.endswith(".py") or "/" in ref.split(":", 1)[0]):
        file_part, _, class_name = ref.partition(":")
        path = Path(file_part).expanduser().resolve()
        if not path.is_file():
            raise FileNotFoundError(f"ReferenceSource file not found: {path}")
        spec = importlib.util.spec_from_file_location(path.stem, path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load ReferenceSource module from {path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return getattr(module, class_name)

    module_path, _, class_name = ref.rpartition(":") if ":" in ref else ref.rpartition(".")
    if not module_path:
        raise ValueError(
            f"ReferenceSource ref {ref!r} must be a .npz/.json path, "
            f"'pkg.module:ClassName', or '/path/file.py:ClassName'."
        )
    module = importlib.import_module(module_path)
    return getattr(module, class_name)

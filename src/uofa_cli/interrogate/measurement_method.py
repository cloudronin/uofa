"""The measurement-method interface — the pack-shaped boundary for SIP's measure leg.

Pack-shaped architecture spec §3: a measurement method is a capability a pack
can implement to replace or augment the open-core default measurements. Each
method declares its identity (``capability_id``), the measurement-block key it
emits (``output_key``), and its provenance id (``provenance_id``); it computes a
measurement-region value (``compute``), stamps its own measurement provenance
(``provenance``), and reports whether its output counts as a present field
(``is_present``). The orchestrator discovers methods through this interface and a
registry rather than by hardcoded attribute reference — so a premium measurement
(a second distance metric, a Wasserstein measurement) drops in as a pack with no
core change, and the four open-core functions become *the first pack* rather than
special-cased core.

**The firewall lives in the interface.** A ``MeasurementMethod`` emits into the
**measurement region** only — it computes, it never thresholds, and it must not
name a field with a forbidden verdict token (``forbidden.FORBIDDEN_TOKENS``).
The relaxed schema's measurement-region denylist + structural constraint enforce
this for any conforming method, so the firewall is inherited, not re-implemented
per pack. Decision/action content belongs in a signed action-region block, never
in a method's output (``AGENTS.md`` §12).

This module is stdlib + ``uofa_cli.paths`` only at import; it never imports
``measurements`` (the default-method payloads) at top level, so the two compose
without a cycle. Heavy deps stay lazy in the payloads.
"""

from __future__ import annotations

import importlib
import importlib.util
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class MeasurementContext:
    """Everything a measurement method needs, assembled once per interrogation run.

    The orchestrator builds this from the adapter's predictions and the loaded
    benchmark/reference + declared scope, plus the environment stamps each
    method records into its provenance (library versions, seed, run environment).
    A method reads what it needs and ignores the rest — the context is uniform
    across methods so the orchestrator never special-cases one.
    """

    predicted: dict[str, Any]
    benchmark: Any
    reference: Any
    scope: dict
    seed: int | None
    run_env: dict
    numpy_version: str
    sip_version: str


class MeasurementMethod(ABC):
    """One contract: turn a :class:`MeasurementContext` into a measurement-region block.

    Subclasses declare three identity fields and implement ``compute``/
    ``provenance``; ``is_present`` defaults to "present if it ran" and is
    overridden by methods whose output is conditionally meaningful (an empty
    physics list, a UQ block with no empirical coverage).

    Mirrors the ``ModelAdapter`` ABC style (``adapter.py``): a thin, single-
    responsibility interface a pack implements, discovered through a registry.
    """

    #: Stable capability identity, e.g. ``"measurement:reference-residuals"``.
    capability_id: str = ""
    #: The ``measurements`` block key this method emits, e.g. ``"referenceResiduals"``.
    output_key: str = ""
    #: The ``measurementProvenance.measurementId`` this method stamps, e.g. ``"m-residuals"``.
    provenance_id: str = ""

    @abstractmethod
    def compute(self, ctx: MeasurementContext) -> Any:
        """Return the value placed at ``measurements[output_key]`` (measurement-region only)."""
        raise NotImplementedError

    @abstractmethod
    def provenance(self, ctx: MeasurementContext) -> dict:
        """Return this method's ``measurementProvenance`` entry (library/version/config/seed/env)."""
        raise NotImplementedError

    def is_present(self, block: Any) -> bool:
        """Whether ``output_key`` is recorded in ``completeness.fieldsPresent``.

        Defaults to True (the method ran, so the field is present). Methods whose
        output is only meaningful under a condition override this.
        """
        return True


# ── Registry ────────────────────────────────────────────────
#
# Two registration paths feed the orchestrator's effective method list, which is
# recomputed FRESH per run (so deactivating a pack drops its methods — no
# cross-run leakage from the manifest path):
#   1. the open-core defaults (always first, canonical order) — code-registered
#      in ``measurements.default_methods()``;
#   2. manifest-declared measurement capabilities of the active packs —
#      ``pack_measurement_methods()``, re-derived per run;
#   3. methods added imperatively via ``register_measurement()`` — the small
#      persistent "extras" registry below (a premium pack registering at import,
#      or a test dropping in a stub). Persistent, so tests that add extras must
#      restore (snapshot/restore helpers provided). The active pack set, by
#      contrast, is no longer a process global — it is threaded explicitly via
#      ``args.active_packs`` / ``paths.resolve_active_packs`` (P2d-3); only this
#      imperative extras registry remains snapshot/restore territory.

_EXTRA_REGISTRY: dict[str, MeasurementMethod] = {}


def register_measurement(method: MeasurementMethod) -> None:
    """Register a measurement method so the orchestrator emits it — no core change.

    Keyed by ``capability_id`` (replace-in-place preserves order on re-register),
    so re-registering the same capability is idempotent. This is the "drop in a
    pack" surface (spec §3 acceptance): an alternative measurement method appears
    in the bundle through the interface with no orchestrator edit.
    """
    if not isinstance(method, MeasurementMethod):
        raise TypeError(
            f"register_measurement expects a MeasurementMethod, got {type(method).__name__}."
        )
    if not method.capability_id or not method.output_key or not method.provenance_id:
        raise ValueError(
            f"MeasurementMethod {type(method).__name__} must set non-empty "
            f"capability_id, output_key, and provenance_id."
        )
    _EXTRA_REGISTRY[method.capability_id] = method


def extra_measurements() -> list[MeasurementMethod]:
    """Methods added via :func:`register_measurement`, in registration order."""
    return list(_EXTRA_REGISTRY.values())


def unregister_measurement(capability_id: str) -> None:
    """Remove an imperatively-registered method (test teardown helper)."""
    _EXTRA_REGISTRY.pop(capability_id, None)


def snapshot_extra_measurements() -> dict[str, MeasurementMethod]:
    """Copy the extras registry so a test can restore it afterward."""
    return dict(_EXTRA_REGISTRY)


def restore_extra_measurements(snapshot: dict[str, MeasurementMethod]) -> None:
    """Restore the extras registry from a :func:`snapshot_extra_measurements`."""
    _EXTRA_REGISTRY.clear()
    _EXTRA_REGISTRY.update(snapshot)


# ── Manifest-driven registration ────────────────────────────


def _resolve_attr(ref: str):
    """Resolve a ``"module.path:attr"`` or ``"/path/file.py:attr"`` reference.

    Mirrors ``adapter.load_adapter``'s resolution but for the ``module:attr``
    form the manifest declares (``payload.impl``), where ``attr`` is a
    ``MeasurementMethod`` subclass or a factory callable.
    """
    if ":" in ref:
        mod_part, _, attr = ref.partition(":")
        if mod_part.endswith(".py") or "/" in mod_part:
            path = Path(mod_part).expanduser().resolve()
            if not path.is_file():
                raise FileNotFoundError(f"Measurement impl file not found: {path}")
            spec = importlib.util.spec_from_file_location(path.stem, path)
            if spec is None or spec.loader is None:
                raise ImportError(f"Could not load measurement module from {path}")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return getattr(module, attr)
        return getattr(importlib.import_module(mod_part), attr)
    module_path, _, attr = ref.rpartition(".")
    if not module_path:
        raise ValueError(
            f"Measurement impl {ref!r} must be 'pkg.module:Attr' or '/path/file.py:Attr'."
        )
    return getattr(importlib.import_module(module_path), attr)


def _impl_to_methods(impl_ref: str) -> list[MeasurementMethod]:
    """Resolve a ``payload.impl`` reference to one-or-more method instances.

    Dual-mode so a premium single-method capability and the multi-method
    open-core default both fit one ``impl`` field:
      - a ``MeasurementMethod`` subclass → instantiated (the per-capability case);
      - a callable → invoked; it returns a method or an iterable of methods (the
        open-core ``default_methods`` factory).
    """
    obj = _resolve_attr(impl_ref)
    if isinstance(obj, type) and issubclass(obj, MeasurementMethod):
        return [obj()]
    if callable(obj):
        result = obj()
        if isinstance(result, MeasurementMethod):
            return [result]
        return list(result)
    raise ValueError(
        f"Measurement impl {impl_ref!r} is neither a MeasurementMethod subclass "
        f"nor a callable returning method(s)."
    )


def pack_measurement_methods(pack_names: list[str] | None = None,
                             root: Path | None = None) -> list[MeasurementMethod]:
    """Methods declared by the active packs' ``measurement`` capabilities (payload.impl).

    The manifest-driven half of registration (spec §3/§7): the loader reads each
    pack's ``capabilities[]``, finds ``leg == "measurement"`` blocks, and imports
    + instantiates their ``payload.impl``. Re-derived per run from the CURRENT
    active set, so this never accumulates across runs.

    Robustness: if the repo root can't be resolved (no repo / odd cwd), returns
    ``[]`` — the code-registered open-core defaults still work. A pack whose
    manifest is missing is skipped, but a declared-but-broken ``impl`` raises
    loudly (a misconfigured active pack must fail, not silently degrade).
    """
    from uofa_cli import paths

    if pack_names is None:
        # The orchestrator has no args to thread; default to the open-core +
        # vv40 set. vv40 declares no measurement capability, so this is
        # behaviour-identical to the former ["core", *active] default while the
        # active-pack global is gone (P2d-3).
        pack_names = ["core", "vv40"]
    try:
        root = root or paths.find_repo_root()
    except FileNotFoundError:
        return []

    methods: list[MeasurementMethod] = []
    seen: set[str] = set()
    for name in pack_names:
        if name in seen:
            continue
        seen.add(name)
        try:
            manifest = paths.pack_manifest(name, root=root)
        except FileNotFoundError:
            continue
        for cap in manifest.get("capabilities", []):
            if cap.get("leg") != "measurement":
                continue
            impl_ref = (cap.get("payload") or {}).get("impl")
            if not impl_ref:
                continue
            methods.extend(_impl_to_methods(impl_ref))
    return methods

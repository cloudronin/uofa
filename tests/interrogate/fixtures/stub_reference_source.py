"""Fixture ReferenceSource subclasses for the §3a reference-interface tests.

Loaded by file:Class reference (the load_reference_source class-ref path),
mirroring how golden_adapter.py is loaded for the model-adapter tests.
"""

from __future__ import annotations

from typing import Any

from uofa_cli.interrogate.reference_source import ReferenceSource


class StubServeSource(ReferenceSource):
    """Serve-only — declares no generation (the Product-A precomputed shape)."""

    def reference(self, inputs: Any = None) -> dict[str, Any]:
        return {"cl": [0.5, 0.8]}


class StubGenSource(ReferenceSource):
    """Serve + generate — exercises the optional generate capability (Product-B shape)."""

    def reference(self, inputs: Any = None) -> dict[str, Any]:
        return {"cl": [0.5, 0.8]}

    def supports_generate(self) -> bool:
        return True

    def generate(self, inputs: Any) -> dict[str, Any]:
        # Stand-in for "run the solver on novel inputs" — truth, never a verdict.
        return {"cl": [round(0.1 * len(inputs), 3)]}


class NotASource:  # deliberately NOT a ReferenceSource — the rejection path
    pass

"""Deterministic fixture adapter for the byte-identical golden-bundle gate.

Returns fixed predictions for the 2-point golden benchmark, so the produced SIP
bundle is reproducible. Used only by tests/interrogate/test_bundle_golden.py.
"""

from __future__ import annotations

from typing import Any

from uofa_cli.interrogate.adapter import ModelAdapter


class GoldenAdapter(ModelAdapter):
    def predict(self, inputs: Any) -> dict[str, list[float]]:
        n = len(inputs)
        cl = [0.52, 0.78, 0.61, 0.44]
        cd = [0.021, 0.031, 0.025, 0.040]
        return {"cl": cl[:n], "cd": cd[:n]}

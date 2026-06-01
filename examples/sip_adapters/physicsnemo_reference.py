"""SIP ReferenceSource for a PhysicsNeMo-CFD signal source (serve-only).

Alongside its predictions, PhysicsNeMo emits the truth/UQ signals SIP measures
against: high-fidelity reference QoIs, physics-constraint residual fields, and
ensemble-variance prediction intervals. This serves them through the SIP
reference interface as a **thin HTTP client** (no torch, no checkpoints in the
appliance — the same boundary the adapter keeps).

It is **serve-only**: ``supports_generate()`` is ``False`` and it carries no live
``generate``, so the demo never crosses into the un-built generate (run-the-
solver) path. That heavier capability is the downstream solver-ingest spec; the
contract is fixed here, the capability is declared absent (pack-shaped §3a).

Resolve it on the SIP command line as:
    --reference examples/sip_adapters/physicsnemo_reference.py:PhysicsNeMoReference

Endpoint from ``PHYSICSNEMO_URL`` (default ``http://physicsnemo:8000``).
"""

from __future__ import annotations

import json
import os
import urllib.request
from typing import Any

import numpy as np

from uofa_cli.interrogate.reference_source import ReferenceSource

DEFAULT_URL = "http://physicsnemo:8000"


def _request_json(url: str, payload: dict | None = None, timeout: float = 60.0) -> dict:
    """GET ``url`` (or POST ``payload`` when given) and return the decoded JSON."""
    if payload is None:
        req = urllib.request.Request(url, method="GET")
    else:
        req = urllib.request.Request(
            url, data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}, method="POST",
        )
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 (in-enclave compose endpoint)
        return json.loads(resp.read().decode("utf-8"))


class PhysicsNeMoReference(ReferenceSource):
    """Serve PhysicsNeMo's reference QoIs, constraint residuals, and UQ bounds over HTTP."""

    def __init__(self, base_url: str | None = None):
        self.base_url = (base_url or os.environ.get("PHYSICSNEMO_URL", DEFAULT_URL)).rstrip("/")

    def reference(self, inputs: Any = None) -> dict[str, Any]:
        payload = None if inputs is None else {"inputs": np.asarray(inputs, dtype=float).tolist()}
        body = _request_json(f"{self.base_url}/reference", payload)
        ref = body.get("reference")
        if not isinstance(ref, dict):
            raise ValueError(
                "PhysicsNeMo /reference must return {'reference': {qoi: [...]}}, "
                f"got: {body!r}"
            )
        return {qoi: np.asarray(values, dtype=float) for qoi, values in ref.items()}

    def constraint_fields(self) -> dict[str, Any]:
        body = _request_json(f"{self.base_url}/constraint_fields")
        fields = body.get("constraint_fields", {})
        return {cid: np.asarray(values, dtype=float) for cid, values in fields.items()}

    def uq_intervals(self) -> dict[str, tuple[Any, Any]]:
        body = _request_json(f"{self.base_url}/uq_intervals")
        intervals = body.get("uq_intervals", {})
        out: dict[str, tuple[Any, Any]] = {}
        for qoi, bounds in intervals.items():
            lower, upper = bounds
            out[qoi] = (np.asarray(lower, dtype=float), np.asarray(upper, dtype=float))
        return out

    def supports_generate(self) -> bool:
        # Serve-only: the generate (solver-run) half is the downstream spec.
        return False

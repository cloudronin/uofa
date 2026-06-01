"""SIP ModelAdapter for a PhysicsNeMo-CFD signal source (the two-container demo).

The appliance ingests PhysicsNeMo's surrogate predictions through the SIP
measurement interface. This adapter is a **thin HTTP client**: PhysicsNeMo
(torch + checkpoints) runs in its *own* container; the appliance only speaks HTTP
to it, so no torch and no model weights ever enter the appliance image. That is
the moat boundary from the appliance spec — NVIDIA produces signals, UofA
produces credibility evidence, neither reimplements the other, and PhysicsNeMo's
model licenses stay in PhysicsNeMo's container.

Resolve it on the SIP command line as:
    --adapter examples/sip_adapters/physicsnemo_adapter.py:PhysicsNeMoAdapter

The PhysicsNeMo endpoint is read from the ``PHYSICSNEMO_URL`` environment
variable (default ``http://physicsnemo:8000`` — the compose service name).
"""

from __future__ import annotations

import json
import os
import urllib.request
from typing import Any

import numpy as np

from uofa_cli.interrogate.adapter import ModelAdapter

DEFAULT_URL = "http://physicsnemo:8000"


def _post_json(url: str, payload: dict, timeout: float = 60.0) -> dict:
    """POST ``payload`` as JSON and return the decoded JSON response."""
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}, method="POST"
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 (in-enclave compose endpoint)
        return json.loads(resp.read().decode("utf-8"))


class PhysicsNeMoAdapter(ModelAdapter):
    """Map benchmark inputs to PhysicsNeMo-CFD predictions over HTTP.

    SIP calls ``predict(inputs)``; this forwards the ``N x D`` evaluation points to
    the PhysicsNeMo container's ``/predict`` endpoint and returns
    ``{qoi: predictions}`` — exactly the contract SIP's ``referenceResiduals``
    measurement consumes. No model is loaded here; the surrogate lives in the
    PhysicsNeMo container.
    """

    def __init__(self, base_url: str | None = None):
        self.base_url = (base_url or os.environ.get("PHYSICSNEMO_URL", DEFAULT_URL)).rstrip("/")

    def predict(self, inputs: Any) -> dict[str, Any]:
        points = np.asarray(inputs, dtype=float).tolist()
        body = _post_json(f"{self.base_url}/predict", {"inputs": points})
        preds = body.get("predictions")
        if not isinstance(preds, dict):
            raise ValueError(
                "PhysicsNeMo /predict must return {'predictions': {qoi: [...]}}, "
                f"got: {body!r}"
            )
        return {qoi: np.asarray(values, dtype=float) for qoi, values in preds.items()}

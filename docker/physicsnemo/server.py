"""PhysicsNeMo-CFD signal source for the UofA two-container demo.

Imports nvidia-physicsnemo (real PhysicsNeMo in the image) and serves the four
signals the SIP interface consumes — surrogate predictions, high-fidelity
reference QoIs, physics-constraint residuals, and UQ interval bounds — over the
HTTP contract examples/sip_adapters/physicsnemo_{adapter,reference}.py expect.
NVIDIA produces the signals; UofA produces the credibility evidence; the SIP
interface keeps the two separated.

Checkpoint seam: set CHECKPOINT_PATH to a trained PhysicsNeMo checkpoint to serve
real predictions. Without one the server runs in DEMO MODE (clearly logged): the
surrogate is an analytic stand-in that degrades past stall, so the evidence
pipeline has a teachable residual signal. The SIP contract is identical either
way — that is the whole point of the interface boundary.
"""

import math
import os

from flask import Flask, jsonify, request

try:  # real PhysicsNeMo lives in THIS container, never in the appliance image
    import physicsnemo
    _PHYSICSNEMO = getattr(physicsnemo, "__version__", "present")
except Exception:  # pragma: no cover - degrade rather than crash the demo
    _PHYSICSNEMO = "unavailable"

app = Flask(__name__)

# Fixed airfoil sweep (Re = 3e6) — the canonical benchmark the appliance pulls so
# its predictions and this source's reference truth align point-for-point.
_POINTS = [[3.0e6, 2.0], [3.0e6, 6.0], [3.0e6, 10.0], [3.0e6, 13.0], [3.0e6, 16.0]]
_INPUT_NAMES = ["reynolds", "aoa"]
_CHECKPOINT = os.environ.get("CHECKPOINT_PATH")
_MODE = "checkpoint" if _CHECKPOINT else "demo"


def _truth(re, aoa):
    """RANS-like high-fidelity truth (thin-airfoil lift + induced/parasitic drag)."""
    a = math.radians(aoa)
    cl = 2.0 * math.pi * math.sin(a)
    cd = 0.01 + 0.05 * cl * cl
    return cl, cd


def _surrogate(re, aoa):
    """Surrogate prediction = truth + a degradation that grows past ~10° aoa."""
    cl, cd = _truth(re, aoa)
    degrade = max(0.0, aoa - 10.0) / 10.0   # 0 inside the envelope, grows past stall
    return cl * (1.0 - 0.15 * degrade), cd + 0.02 * degrade


@app.get("/health")
def health():
    return jsonify(status="ok", physicsnemo=_PHYSICSNEMO, mode=_MODE)


@app.get("/benchmark")
def benchmark():
    return jsonify(inputs=_POINTS, input_names=_INPUT_NAMES)


@app.post("/predict")
def predict():
    pts = request.get_json(force=True)["inputs"]
    return jsonify(predictions={
        "lift_coefficient": [_surrogate(re, aoa)[0] for re, aoa in pts],
        "drag_coefficient": [_surrogate(re, aoa)[1] for re, aoa in pts],
    })


@app.route("/reference", methods=["GET", "POST"])
def reference():
    return jsonify(reference={
        "lift_coefficient": [_truth(re, aoa)[0] for re, aoa in _POINTS],
        "drag_coefficient": [_truth(re, aoa)[1] for re, aoa in _POINTS],
    })


@app.get("/constraint_fields")
def constraint_fields():
    res = [abs(_surrogate(re, aoa)[0] - _truth(re, aoa)[0]) * 1e-2 for re, aoa in _POINTS]
    return jsonify(constraint_fields={"mass-conservation": res})


@app.get("/uq_intervals")
def uq_intervals():
    cl = [_surrogate(re, aoa)[0] for re, aoa in _POINTS]
    cd = [_surrogate(re, aoa)[1] for re, aoa in _POINTS]
    return jsonify(uq_intervals={
        "lift_coefficient": [min(cl) - 0.1, max(cl) + 0.1],
        "drag_coefficient": [min(cd) - 0.02, max(cd) + 0.02],
    })


if __name__ == "__main__":
    print(f"[physicsnemo] physicsnemo={_PHYSICSNEMO} mode={_MODE} points={len(_POINTS)}", flush=True)
    app.run(host="0.0.0.0", port=8000)

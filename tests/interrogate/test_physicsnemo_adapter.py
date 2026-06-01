"""The PhysicsNeMo SIP adapters (two-container demo) speak HTTP to a signal source.

These verify the appliance-side contract — that the adapter/reference correctly
map a PhysicsNeMo HTTP response into the SIP ``{qoi: array}`` frame — against a
mock HTTP server, so no torch / PhysicsNeMo / checkpoints are needed. That the
contract is testable with a 40-line mock IS the thin-client split working: the
appliance never imports the model framework.
"""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

np = pytest.importorskip("numpy")

from uofa_cli.interrogate.adapter import load_adapter
from uofa_cli.interrogate.reference_source import ReferenceSource, load_reference_source

REPO_ROOT = Path(__file__).resolve().parents[2]
ADAPTER_REF = f"{REPO_ROOT}/examples/sip_adapters/physicsnemo_adapter.py:PhysicsNeMoAdapter"
REFERENCE_REF = f"{REPO_ROOT}/examples/sip_adapters/physicsnemo_reference.py:PhysicsNeMoReference"

_CANNED = {
    "/predict": {"predictions": {"lift_coefficient": [0.31, 0.42], "drag_coefficient": [0.011, 0.013]}},
    "/reference": {"reference": {"lift_coefficient": [0.30, 0.40], "drag_coefficient": [0.010, 0.012]}},
    "/constraint_fields": {"constraint_fields": {"mass-conservation": [1e-4, 2e-4]}},
    "/uq_intervals": {"uq_intervals": {"lift_coefficient": [0.28, 0.34]}},
}


class _Handler(BaseHTTPRequestHandler):
    def _reply(self):
        body = _CANNED.get(self.path)
        payload = json.dumps(body if body is not None else {"error": "not found"}).encode()
        self.send_response(200 if body is not None else 404)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        self._reply()

    def do_POST(self):
        self._reply()

    def log_message(self, *_args):  # keep the test output quiet
        pass


@pytest.fixture()
def physicsnemo_url(monkeypatch):
    server = HTTPServer(("127.0.0.1", 0), _Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    monkeypatch.setenv("PHYSICSNEMO_URL", f"http://127.0.0.1:{server.server_address[1]}")
    try:
        yield
    finally:
        server.shutdown()


def test_adapter_maps_predictions_into_qoi_frame(physicsnemo_url):
    adapter = load_adapter(ADAPTER_REF)
    out = adapter.predict([[3.0e6, 5.0], [3.0e6, 6.0]])
    assert set(out) == {"lift_coefficient", "drag_coefficient"}
    np.testing.assert_allclose(out["lift_coefficient"], [0.31, 0.42])
    np.testing.assert_allclose(out["drag_coefficient"], [0.011, 0.013])


def test_reference_is_serve_only_and_maps_truth(physicsnemo_url):
    ref = load_reference_source(REFERENCE_REF)
    assert isinstance(ref, ReferenceSource)
    assert ref.supports_generate() is False  # never crosses into the generate path
    served = ref.reference([[3.0e6, 5.0]])
    np.testing.assert_allclose(served["drag_coefficient"], [0.010, 0.012])
    assert "mass-conservation" in ref.constraint_fields()
    lower, upper = ref.uq_intervals()["lift_coefficient"]
    assert float(lower) == pytest.approx(0.28) and float(upper) == pytest.approx(0.34)


def test_generate_raises_on_serve_only(physicsnemo_url):
    ref = load_reference_source(REFERENCE_REF)
    with pytest.raises(NotImplementedError):
        ref.generate([[1.0, 2.0]])

"""End-to-end proof of the appliance demo chain — WITHOUT Docker or PhysicsNeMo.

A mock signal server stands in for the PhysicsNeMo container; everything else is
the real demo path the appliance runs:

    mock signals → `uofa interrogate` (the real PhysicsNeMo SIP adapters)
      → signed, verdict-free bundle → read_sip_bundle → check(pack=surrogate)
      → **W-SURR-03 fires** (the declared evaluation point is out of the training
        envelope — the teachable flag docker/appliance/demo_scope.json is built
        around).

This pins the demo logic so the only thing the Docker images add is packaging.
"""

from __future__ import annotations

import argparse
import json
import math
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

np = pytest.importorskip("numpy")

from uofa_cli import integrity
from uofa_cli.interrogate import run_interrogation
from uofa_cli.readers.sip_bundle_reader import read_sip_bundle

REPO = Path(__file__).resolve().parents[2]
ADAPTER = f"{REPO}/examples/sip_adapters/physicsnemo_adapter.py:PhysicsNeMoAdapter"
REFERENCE = f"{REPO}/examples/sip_adapters/physicsnemo_reference.py:PhysicsNeMoReference"
SCOPE = REPO / "docker" / "appliance" / "demo_scope.json"

# The same fixed sweep + analytic signals the demo's PhysicsNeMo server serves.
_POINTS = [[3.0e6, 2.0], [3.0e6, 6.0], [3.0e6, 10.0], [3.0e6, 13.0], [3.0e6, 16.0]]


def _truth(re, aoa):
    a = math.radians(aoa)
    cl = 2.0 * math.pi * math.sin(a)
    return cl, 0.01 + 0.05 * cl * cl


def _surr(re, aoa):
    cl, cd = _truth(re, aoa)
    d = max(0.0, aoa - 10.0) / 10.0
    return cl * (1.0 - 0.15 * d), cd + 0.02 * d


_CANNED = {
    "/health": {"status": "ok"},
    "/benchmark": {"inputs": _POINTS, "input_names": ["reynolds", "aoa"]},
    "/predict": {"predictions": {
        "lift_coefficient": [_surr(*p)[0] for p in _POINTS],
        "drag_coefficient": [_surr(*p)[1] for p in _POINTS],
    }},
    "/reference": {"reference": {
        "lift_coefficient": [_truth(*p)[0] for p in _POINTS],
        "drag_coefficient": [_truth(*p)[1] for p in _POINTS],
    }},
    "/constraint_fields": {"constraint_fields": {
        "mass-conservation": [abs(_surr(*p)[0] - _truth(*p)[0]) * 1e-2 for p in _POINTS],
    }},
    "/uq_intervals": {"uq_intervals": {
        "lift_coefficient": [0.0, 7.0], "drag_coefficient": [0.0, 1.0],
    }},
}


class _Handler(BaseHTTPRequestHandler):
    def _reply(self):
        body = _CANNED.get(self.path)
        payload = json.dumps(body if body is not None else {"error": "nf"}).encode()
        self.send_response(200 if body is not None else 404)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    do_GET = do_POST = lambda self: self._reply()

    def log_message(self, *_):
        pass


@pytest.fixture()
def signal_server(monkeypatch):
    server = HTTPServer(("127.0.0.1", 0), _Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    monkeypatch.setenv("PHYSICSNEMO_URL", f"http://127.0.0.1:{server.server_address[1]}")
    try:
        yield
    finally:
        server.shutdown()


def test_demo_chain_fires_w_surr_03(signal_server, tmp_path):
    key = tmp_path / "sip.key"
    integrity.generate_keypair(key)
    pub = key.with_suffix(".pub")

    bench = tmp_path / "bench.npz"
    np.savez(bench, inputs=np.array(_POINTS, dtype=float),
             input_names=np.array(["reynolds", "aoa"]))
    scope = json.loads(SCOPE.read_text(encoding="utf-8"))

    result = run_interrogation(
        adapter_ref=ADAPTER, benchmark_path=bench, reference_path=REFERENCE,
        scope=scope, output_path=tmp_path / "bundle.json", key_path=key,
    )
    assert result["signed"]
    # The declared evaluation point (aoa=15) is outside the envelope (aoa_max=10).
    assert result["bundle"]["measurements"]["envelopeCoverage"]["evaluationPointInEnvelope"] is False

    doc = read_sip_bundle(tmp_path / "bundle.json", measurement_pubkey=pub)
    cou = tmp_path / "cou.jsonld"
    cou.write_text(json.dumps(doc), encoding="utf-8")

    from uofa_cli.commands.check import run_structured
    args = argparse.Namespace(
        file=cou, pubkey=None, context=None, rules=None, skip_rules=False, build=False,
        enable_oos=False, disable_oos=False, no_color=True, verbose=False, repo_root=None,
        pack=["surrogate"], active_packs=["surrogate"],
    )
    result = run_structured(args)
    assert result.rules is not None, getattr(result, "rules_error", "rules did not run")
    pids = {f["patternId"] for f in (result.rules.firings or [])}
    assert "W-SURR-03" in pids, f"expected W-SURR-03 (out-of-envelope); got {sorted(pids)}"

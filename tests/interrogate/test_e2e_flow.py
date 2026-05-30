"""Full end-to-end integration test of the surrogate flow (Addendum A14.4):

    interrogate init -> interrogate -> decision review -> decision sign
                     -> verify -> import (v2 native reader) -> check

Drives the real CLI via subprocess so the seams between stages are exercised:
init's generated adapter + scope feed interrogate; the emitted bundle feeds
decision/verify; the v2 reader maps the verified bundle to surrogate-pack
JSON-LD; check fires the W-SURR catalog on the imported COU.

A tiny sklearn model is generated so `init` produces a genuinely runnable
adapter (its smoke test must pass). Skipped if the Jena engine or sklearn is
unavailable.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

np = pytest.importorskip("numpy")
pytest.importorskip("sklearn")
pytest.importorskip("joblib")

from uofa_cli import integrity, paths  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]


def _engine_available() -> bool:
    try:
        paths.java_executable()
    except Exception:
        return False
    return paths.jar_path().exists()


pytestmark = pytest.mark.skipif(not _engine_available(), reason="Jena engine (Java + JAR) not available")


def _uofa(*args, stdin=None):
    return subprocess.run(
        [sys.executable, "-m", "uofa_cli", *args],
        cwd=str(REPO_ROOT), capture_output=True, text=True, input=stdin, timeout=300,
    )


@pytest.fixture(scope="module")
def workspace(tmp_path_factory):
    ws = tmp_path_factory.mktemp("sip_e2e")
    # A tiny, deterministic sklearn model: 2 inputs -> 1 output.
    import joblib
    from sklearn.linear_model import LinearRegression
    rng = np.random.RandomState(0)
    X = rng.rand(40, 2)
    y = X[:, 0] * 0.5 + X[:, 1] * 0.1
    model_path = ws / "model.pkl"
    joblib.dump(LinearRegression().fit(X, y), model_path)

    # Benchmark spans the declared envelope; reference is a supplied parent result.
    inputs = np.column_stack([np.linspace(2.0e6, 6.0e6, 40), np.linspace(-5.0, 15.0, 40)])
    np.savez(ws / "benchmark.npz", inputs=inputs, input_names=np.array(["reynolds", "aoa"]))
    np.savez(ws / "reference.npz", **{"ref__lift_coefficient": np.zeros(40)})

    # Keys: a SIP measurement key and the engineer's own decision key.
    integrity.generate_keypair(ws / "sip.key")
    integrity.generate_keypair(ws / "eng.key")
    return ws


def test_end_to_end_init_to_check(workspace):
    ws = workspace
    gen = ws / "gen"

    # 1) init — guided setup. Eval point Re=8e6 is OUTSIDE the [2e6,6e6] envelope
    #    (W-SURR-03); a physics constraint is declared but will go unmeasured
    #    (W-SURR-01). Answers piped on stdin (16 prompts).
    answers = "\n".join([
        "reynolds,aoa", "lift_coefficient",          # I/O names
        "2000000", "6000000", "-5", "15",            # envelope: reynolds, aoa bounds
        "8000000", "4",                              # evaluation point (Re extrapolation)
        "y", "mass-conservation", "div(u)=0", "conservation",  # one constraint
        "n",                                          # no more constraints
        "airfrans-echo", "1.0.0", "data-driven-emulator",      # subject
    ]) + "\n"
    r = _uofa("interrogate", "init", "--model", str(ws / "model.pkl"),
              "--benchmark", str(ws / "benchmark.npz"), "--out-dir", str(gen), stdin=answers)
    assert r.returncode == 0, r.stderr + r.stdout
    assert (gen / "sip_adapter.py").is_file()
    scope = json.loads((gen / "sip_scope.json").read_text())
    assert scope["scopeProvenance"]["trainingEnvelope.reynolds"] == "entered-by-engineer"
    assert "Adapter smoke test" in r.stdout  # A14.3 ran and passed

    # 2) interrogate — measure with init's generated adapter + scope; signed bundle.
    pkg = ws / "pkg.json"
    r = _uofa("interrogate",
              "--adapter", f"{gen / 'sip_adapter.py'}:GeneratedAdapter",
              "--benchmark", str(ws / "benchmark.npz"), "--reference", str(ws / "reference.npz"),
              "--scope", str(gen / "sip_scope.json"), "-o", str(pkg), "--key", str(ws / "sip.key"))
    assert r.returncode == 0, r.stderr + r.stdout
    bundle = json.loads(pkg.read_text())
    assert bundle.get("signature", "").startswith("ed25519:")
    assert "engineerDecision" not in bundle  # SIP authored no decision

    # 3) decision review — read-only facts.
    r = _uofa("decision", "review", str(pkg))
    assert r.returncode == 0

    # 4) decision sign — the engineer's own key.
    r = _uofa("decision", "sign", str(pkg), "--key", str(ws / "eng.key"),
              "--criterion", "Cl within 3% over the envelope", "--value", "accepted",
              "--rationale", "acceptable for this COU")
    assert r.returncode == 0, r.stderr + r.stdout
    assert json.loads(pkg.read_text())["engineerDecision"]["decisionValue"] == "Accepted"

    # 5) verify — both signatures independently.
    r = _uofa("verify", str(pkg), "--pubkey", str(ws / "sip.pub"), "--decision-pubkey", str(ws / "eng.pub"))
    assert r.returncode == 0, r.stderr + r.stdout
    assert "Measurement signature valid" in r.stdout
    assert "Engineer decision signature valid" in r.stdout

    # 6) import (v2 native reader) — verified bundle -> surrogate-pack JSON-LD.
    cou = ws / "cou.jsonld"
    r = _uofa("import", str(pkg), "--sip-pubkey", str(ws / "sip.pub"),
              "--decision-pubkey", str(ws / "eng.pub"), "-o", str(cou))
    assert r.returncode == 0, r.stderr + r.stdout
    imported = json.loads(cou.read_text())
    assert imported["decision"] == "Accepted"  # verified engineer decision carried in
    assert "https://uofa.net/vocab/surrogate#trainingEnvelope" in imported

    # 7) check — the surrogate pack fires on the imported COU, via the
    #    derivation-aware detection path (run_structured), which is what the
    #    pack tests, the interpretation pipeline, and `uofa diff` use.
    #    (The legacy `uofa check` CLI does NOT run the derivation pre-pass — a
    #    pre-existing repo behavior affecting every derived-flag pack — so
    #    W-SURR-03, which consumes a derived flag, surfaces here, not via the
    #    bare CLI. W-SURR-01 is pure-Jena and surfaces either way.)
    import argparse as _argparse
    from uofa_cli import paths as _paths
    from uofa_cli.commands.check import run_structured

    _paths.set_active_pack(["surrogate"])
    result = run_structured(_argparse.Namespace(
        file=cou, pubkey=None, context=None, rules=None, skip_rules=False, build=False,
        enable_oos=False, disable_oos=False, no_color=True, verbose=False,
        repo_root=None, pack=["surrogate"],
    ))
    pids = {f["patternId"] for f in (result.rules.firings or [])}
    assert "W-SURR-03" in pids, f"expected extrapolation weakener; got {pids}"
    assert "W-SURR-01" in pids, f"expected unchecked-constraint weakener; got {pids}"

    # And the CLI import+check path runs and surfaces the pure-Jena weakener.
    r = _uofa("import", str(pkg), "--sip-pubkey", str(ws / "sip.pub"),
              "--decision-pubkey", str(ws / "eng.pub"), "-o", str(ws / "cou2.jsonld"), "--check")
    assert "W-SURR-01" in (r.stdout + r.stderr)

"""Phase F: AirfRANS dual-COU case study (in-distribution vs extrapolation).

The two example packages are the SAME surrogate evaluated at an in-envelope
point (COU1) and a Reynolds-extrapolation point (COU2), held identical in every
other respect. The sole weakener divergence is W-SURR-03 — the surrogate
analogue of the NASA take-off-vs-cruise divergence, the value proposition `uofa
diff` renders in one figure. Skipped when the Jena engine is unavailable.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from uofa_cli import paths
from uofa_cli.commands.check import run_structured

REPO_ROOT = Path(__file__).resolve().parents[2]
COU1 = REPO_ROOT / "packs/surrogate/examples/airfrans/cou1/uofa-surrogate-airfrans-cou1.jsonld"
COU2 = REPO_ROOT / "packs/surrogate/examples/airfrans/cou2/uofa-surrogate-airfrans-cou2.jsonld"


def _engine_available() -> bool:
    try:
        paths.java_executable()
    except Exception:
        return False
    return paths.jar_path().exists()


pytestmark = pytest.mark.skipif(
    not _engine_available(), reason="Jena engine (Java + built JAR) not available"
)


def _pids(path: Path) -> set[str]:
    # active_packs threaded explicitly (P2d-3): check resolves the active set via
    # paths.resolve_active_packs(args), which reads args.active_packs.
    args = argparse.Namespace(
        file=path, pubkey=None, context=None, rules=None, skip_rules=False,
        build=False, enable_oos=False, disable_oos=False,
        no_color=True, verbose=False, repo_root=None, pack=["surrogate"],
        active_packs=["surrogate"],
    )
    result = run_structured(args)
    assert result.rules is not None and result.rules.returncode == 0
    return {f["patternId"] for f in (result.rules.firings or [])}


def test_example_packages_exist():
    assert COU1.is_file() and COU2.is_file()


def test_cou1_in_envelope_silent_on_w_surr_03():
    pids = _pids(COU1)
    assert "W-SURR-03" not in pids
    # In-distribution COU is clean on the new surrogate catalog.
    assert "W-SURR-01" not in pids  # constraint check evidence present
    assert "W-SURR-02" not in pids  # parent Accepted


def test_cou2_extrapolation_fires_w_surr_03():
    assert "W-SURR-03" in _pids(COU2)


def test_single_figure_divergence_is_w_surr_03():
    cou1_pids, cou2_pids = _pids(COU1), _pids(COU2)
    divergence = cou2_pids - cou1_pids  # what `uofa diff` renders as unique to COU2
    assert divergence == {"W-SURR-03"}, (
        f"expected the sole divergence to be W-SURR-03, got {divergence}"
    )

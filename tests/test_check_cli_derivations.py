"""Regression guard: the `uofa check` CLI runs the derivation pre-pass + OOS.

`check.run()` (the CLI shell) delegates to `run_structured`, so derived-flag
weakeners and OOS findings surface for users running `uofa check` directly —
not only via `run_structured`. For packs that declare neither (vv40), the
rendered output gains no derivation/OOS sections (byte-compat sentinel).

These call `check.run()` (the render path, capturing stdout), distinct from the
`run_structured` tests in test_derivation_prepass.py.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from uofa_cli import paths
from uofa_cli.commands import check

REPO_ROOT = Path(__file__).resolve().parents[1]
SURR_COU2 = REPO_ROOT / "packs/surrogate/examples/airfrans/cou2/uofa-surrogate-airfrans-cou2.jsonld"
MORRISON = REPO_ROOT / "packs/vv40/examples/morrison/cou1/uofa-morrison-cou1.jsonld"


def _engine_available() -> bool:
    try:
        paths.java_executable()
    except Exception:
        return False
    return paths.jar_path().exists()


pytestmark = pytest.mark.skipif(not _engine_available(), reason="Jena engine (Java + JAR) not available")


def _args(file_path: Path, pack: str) -> argparse.Namespace:
    # active_packs is threaded explicitly (P2d-3): check resolves the active set
    # via paths.resolve_active_packs(args), which reads args.active_packs.
    return argparse.Namespace(
        file=file_path, pubkey=None, context=None, rules=None, skip_rules=False, build=False,
        enable_oos=False, disable_oos=False, enable_derivations=False, disable_derivations=False,
        explain=False, no_color=True, verbose=False, repo_root=None, pack=[pack],
        active_packs=[pack],
    )


def test_uofa_check_cli_fires_derived_flag_weakener(capsys):
    # W-SURR-03 consumes the derived _evalOutsideEnvelope flag; it must surface
    # under the bare `uofa check` CLI (not only run_structured).
    check.run(_args(SURR_COU2, "surrogate"))
    out = capsys.readouterr().out
    assert "C2.5: Derivation pre-pass" in out
    assert "W-SURR-03" in out


def test_uofa_check_cli_renders_oos_section_for_oos_pack(capsys):
    check.run(_args(SURR_COU2, "surrogate"))
    out = capsys.readouterr().out
    assert "OOS: productive out-of-scope" in out


def test_uofa_check_cli_unchanged_for_pack_without_derivations_or_oos(capsys):
    # vv40 declares neither a derivation pre-pass nor OOS → no new sections.
    check.run(_args(MORRISON, "vv40"))
    out = capsys.readouterr().out
    assert "C2.5" not in out
    assert "OOS:" not in out
    # The classic three-gate summary is intact.
    assert "C2 SHACL" in out and "C1 Integrity" in out and "C3 Rules" in out

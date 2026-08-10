"""Golden-output contract for the report renderers.

The renderers have no template layer and three output formats, so a change to
one is easy to make and hard to see. These goldens are the contract: any diff in
rendered output shows up as a reviewable file change rather than as a behaviour
nobody noticed.

Regenerate deliberately, never as a side effect:

    python tests/test_report_goldens.py --update

and commit the regenerated goldens **in their own commit**, so the output diff is
reviewable separately from the logic that caused it. A golden updated silently
alongside a logic change proves nothing -- it just records whatever happened.

Cases span the paths that render differently: a card with no reported evaluation,
the same card with furnished evidence unassessed and assessed, and the vv40
morrison bundle (a pack with no evaluation layer at all, which must be unaffected
by anything Group B does).
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import pytest

from uofa_cli import card_bundle
from uofa_cli.commands import report as R
from uofa_cli.furnishers import raidex

REPO = Path(__file__).resolve().parents[1]
GOLDENS = REPO / "tests" / "fixtures" / "report_goldens"
_CARD = REPO / "packs" / "mrm-nist" / "examples" / "olmo2-13b-instruct" / "card.md"
_RAIDEX = REPO / "tests" / "fixtures" / "raidex" / "openai__gpt-5.6.json"
_MORRISON = REPO / "packs" / "vv40" / "examples" / "morrison" / "cou1" / "uofa-morrison-cou1.jsonld"


def _card_bundle() -> dict:
    bundle, _prov, _suff = card_bundle.card_to_bundle(
        _CARD.read_text(), "mrm-nist",
        model_id="allenai/OLMo-2-13B-Instruct", allow_llm=False)
    return bundle


def _cases() -> dict[str, tuple[dict, str]]:
    base = _card_bundle()
    fetched = raidex.fetch_record("", local_path=_RAIDEX)
    furnished = raidex.furnish(fetched.record, base["id"], _RAIDEX.name).nodes

    with_evidence = dict(base)
    with_evidence["hasValidationResult"] = furnished
    # The heuristic tier stamps this False. Without it the case defaults to
    # assessed and silently stops testing the declined path it exists for.
    with_evidence["_sufficiencyAssessed"] = False

    assessed = dict(with_evidence)
    assessed["_sufficiencyAssessed"] = True

    scoped = dict(assessed)
    scoped["decisionContextOfUse"] = "screening triage for X"
    scoped["decisionRiskLevel"] = 3

    return {
        "card_only": (base, "mrm-nist"),
        "card_evidence_declined": (with_evidence, "mrm-nist"),
        "card_evidence_assessed": (assessed, "mrm-nist"),
        "card_evidence_scoped": (scoped, "mrm-nist"),
        "morrison_vv40": (json.loads(_MORRISON.read_text()), "vv40"),
    }


def _state_for(bundle: dict, pack: str, name: str):
    if name == "morrison_vv40":
        path = _MORRISON                      # relative @context must resolve
    else:
        path = Path(tempfile.mkdtemp()) / "bundle.jsonld"
        path.write_text(json.dumps(bundle))
    # The SAME entry point `run` uses. Building the payload independently here
    # is how the goldens once recorded a code path the command does not take.
    return R.build_report_state(R.analysis_for(bundle, path, pack))


def _render_all() -> dict[str, str]:
    out = {}
    for name, (bundle, pack) in _cases().items():
        state = _state_for(bundle, pack, name)
        for fmt, fn in R._RENDERERS.items():
            out[f"{name}.{fmt}"] = fn(state)
    return out


@pytest.mark.parametrize("filename", sorted(
    p.name for p in GOLDENS.iterdir() if p.is_file()) if GOLDENS.exists() else [])
def test_rendered_output_matches_golden(filename):
    rendered = _render_all()
    assert filename in rendered, (
        f"golden {filename} has no matching case; delete it or restore the case")
    expected = (GOLDENS / filename).read_text()
    assert rendered[filename] == expected, (
        f"{filename} differs from its golden. If the change is intended, run\n"
        f"    python tests/test_report_goldens.py --update\n"
        f"and commit the regenerated goldens in their own commit."
    )


def test_every_case_has_a_golden():
    """A new case must ship its golden, or it is asserting nothing."""
    missing = sorted(set(_render_all()) - {p.name for p in GOLDENS.iterdir() if p.is_file()})
    assert not missing, f"cases with no golden on disk: {missing}"


def _update() -> int:
    GOLDENS.mkdir(parents=True, exist_ok=True)
    rendered = _render_all()
    for name in sorted(set(p.name for p in GOLDENS.iterdir() if p.is_file()) - set(rendered)):
        (GOLDENS / name).unlink()
        print(f"removed stale golden {name}")
    for name, text in sorted(rendered.items()):
        path = GOLDENS / name
        if not path.exists() or path.read_text() != text:
            path.write_text(text)
            print(f"updated {name}")
    print(f"{len(rendered)} goldens in {GOLDENS}")
    return 0


if __name__ == "__main__":
    if "--update" in sys.argv:
        raise SystemExit(_update())
    print(__doc__)

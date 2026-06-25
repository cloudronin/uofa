"""Worked-examples gallery: the committed MRM-NIST curated readouts render
consistently (the six invariants), the standalone HTML golden is reproducible, the
disclosed MRL assumption is shown, and the committed payloads still meet the R2
firing gate with the strong→holey→empty completeness contrast.

No rule engine here — these assert on the committed `state.json` / `reviewer.html`
artifacts, so they guard the demo's shipped output even where the JAR is absent.
Regenerate the artifacts with `python packs/mrm-nist/examples/_generate.py`.
"""

from __future__ import annotations

from space import curated, reviewer
from space.gloss import load_gloss
from space.reviewer_state import assert_reviewer_invariants, build_reviewer_state
from uofa_cli import paths

_EX = paths.pack_dir("mrm-nist") / "examples"


def test_load_curated_returns_three_in_display_order():
    assert [it["key"] for it in curated.load_curated()] == [
        "olmo2-13b-instruct", "twitter-roberta-sentiment", "chemberta-77m-mtr",
    ]


def test_each_curated_payload_satisfies_the_six_invariants():
    gloss = load_gloss()
    for it in curated.load_curated():
        assert_reviewer_invariants(build_reviewer_state(it["payload"], gloss))


def test_standalone_html_matches_committed_golden():
    # The committed reviewer.html must be reproducible from its payload — a stale
    # golden (renderer or payload changed without regenerating) fails here.
    gloss = load_gloss()
    for it in curated.load_curated():
        committed = (_EX / it["key"] / "reviewer.html").read_text(encoding="utf-8")
        assert curated.standalone_html(it["payload"], gloss) == committed, (
            f"{it['key']}/reviewer.html is stale — rerun packs/mrm-nist/examples/_generate.py"
        )


def test_mrl_assumption_is_disclosed_in_every_readout():
    gloss = load_gloss()
    for it in curated.load_curated():
        html = reviewer.render_reviewer_html(it["payload"], gloss)
        assert "Risk tier (assumed)" in html
        assert "MRL 3" in html


def test_completeness_contrast_and_committed_firing_gate():
    items = {it["key"]: it["payload"] for it in curated.load_curated()}
    n = {k: p["completeness"]["n_assessed"] for k, p in items.items()}
    # strong → popular-but-holey → ships-no-card
    assert n["olmo2-13b-instruct"] > n["twitter-roberta-sentiment"] > n["chemberta-77m-mtr"] == 0, n
    union: set[str] = set()
    for p in items.values():
        union |= {w["patternId"] for w in p["weakeners"]}
    assert len(union) >= 6, f"committed artifacts fire only {len(union)} distinct: {sorted(union)}"

"""The acceptance gate has to reject the corpus that caused the problem.

A gate calibrated on the real papers and tested only on the real papers is
circular -- it passes its own calibration set by construction. So the tests that
matter here run it against known-bad inputs: the old synthetic corpus, and
corpora built by duplication.
"""
from __future__ import annotations

import pathlib
import random
import sys

import pytest

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "dev" / "tools" / "scripts"))

pytest.importorskip("sklearn")

from corpus_profile import (  # noqa: E402
    BANDS, _DIVERSITY_CAP, _drift, _verdict, diversity,
)

# Shared genre vocabulary -- every credibility paper uses these.
_GENRE = ("model mesh solver boundary condition validation credibility "
          "sensitivity uncertainty calibration gradation factor evidence").split()
_GENRE_SHARE = 0.35  # tuned so distinct papers land near the real 0.14 mean


def _paper(seed: int, n: int = 4000) -> str:
    """A pseudo-paper: shared genre terms plus a vocabulary of its own.

    Drawing every paper from one small word list makes them all ~0.999 similar,
    which silently turns every duplication assertion below into a tautology --
    a corpus where everything is a near-duplicate cannot demonstrate that
    duplicates are detected. So each seed gets private terms, and
    `test_fixture_papers_are_actually_distinct` pins that this stays true.
    """
    rng = random.Random(seed)
    own = [f"term{seed}x{i}" for i in range(40)]
    return " ".join(rng.choice(_GENRE if rng.random() < _GENRE_SHARE else own)
                    for _ in range(n))


def test_fixture_papers_are_actually_distinct():
    """Guards every other test in this file.

    If distinct pseudo-papers drift towards each other, the duplication tests
    start passing because everything looks duplicated, and they stop testing
    anything. Pin the fixture near the real corpus's own 0.141.
    """
    d = diversity([_paper(i) for i in range(20)])
    assert d["diversity_mean"] < 0.35, (
        f"fixture papers are too alike ({d['diversity_mean']:.3f}); the "
        "duplication tests below would pass trivially")
    assert d["diversity_max"] < 0.60


def test_drift_is_monotone_and_anchored_at_five():
    """The size adjustment must be 1.0 where the real calibration was taken."""
    assert _drift(5, 0) == pytest.approx(1.0)
    assert _drift(5, 1) == pytest.approx(1.0)
    for which in (0, 1):
        vals = [_drift(n, which) for n in (5, 10, 20, 40, 87)]
        assert vals == sorted(vals), "drift must not decrease with n"
    assert _drift(3, 0) == pytest.approx(1.0)      # clamped below
    assert _drift(500, 0) == pytest.approx(1.707)  # clamped above


def test_duplication_is_caught_by_nn_and_missed_by_mean():
    """The reason three diversity numbers are reported instead of one.

    Twenty distinct papers, then each one duplicated. The mean barely moves --
    only 20 of 780 pairs are twins -- while every paper acquires a perfect
    nearest neighbour.
    """
    distinct = [_paper(i) for i in range(20)]
    twinned = distinct + distinct

    d0 = diversity(distinct)
    d1 = diversity(twinned)

    assert d1["diversity_nn"] > 0.99, "a duplicated corpus must show NN ~ 1.0"
    assert d1["diversity_max"] > 0.99
    # The mean is nearly blind to it, which is exactly why it cannot be the only
    # gate. Assert the blindness so a future "simplification" to one number fails.
    assert abs(d1["diversity_mean"] - d0["diversity_mean"]) < 0.05


def test_duplicated_corpus_fails_the_gate_at_full_size():
    """Size scaling must not open a hole big enough for duplication to pass.

    The thresholds grow with n so a large diverse corpus is not failed
    spuriously; this pins that the growth never reaches the duplicate case.
    """
    twinned = [_paper(i) for i in range(20)] * 2
    d = diversity(twinned)
    assert d["twins"] == 40
    for key in ("diversity_nn", "diversity_max", "twins"):
        ok, _ = _verdict(key, d[key], len(twinned))
        assert not ok, f"{key}={d[key]} passed on a corpus of exact twins"


def test_a_few_hidden_twins_are_caught():
    """The realistic failure: a generator that occasionally repeats itself.

    This is the case that broke the nearest-neighbour MEAN. Six duplicated papers
    among thirty lifted it by less than its own threshold, because a mean dilutes
    a minority -- the same flaw that disqualified mean-pairwise, one level up.
    The count does not dilute.
    """
    distinct = [_paper(i) for i in range(27)]
    sneaky = distinct + distinct[:3]
    d = diversity(sneaky)

    assert d["twins"] == 6, f"expected 6 twinned papers, counted {d['twins']}"
    ok, _ = _verdict("twins", d["twins"], len(sneaky))
    assert not ok, "three twins hidden in thirty papers slipped through"

    # Pin the dilution itself, so nobody restores the mean as the only gate.
    nn_ok, _ = _verdict("diversity_nn", d["diversity_nn"], len(sneaky))
    assert nn_ok, ("the NN mean now catches this; if so, re-derive whether the "
                   "count is still needed rather than deleting this assertion")


def test_diverse_corpus_at_forty_is_not_failed_spuriously():
    """The bug the drift table exists to prevent.

    Forty distinct papers must pass. Calibrated on five real papers with no size
    adjustment, max-pair alone would fail here purely from having more pairs to
    draw from -- and that failure would read as generator collapse.
    """
    d = diversity([_paper(i) for i in range(40)])
    for key in ("diversity_mean", "diversity_max", "diversity_nn", "twins"):
        ok, note = _verdict(key, d[key], 40)
        assert ok, f"{key}={d[key]} spuriously failed at n=40 ({note})"


def test_diversity_is_measured_on_a_capped_sample():
    """Length must not be mistaken for sameness.

    Uncapped, full-text cosine rated forty template papers as MORE varied than
    five real ones, because the real papers are 8x longer and long documents
    share more terms. Two papers that are identical for their first cap words
    must read as identical however much unique text follows.
    """
    head = _paper(1, _DIVERSITY_CAP)
    a = head + " " + _paper(2, 6000)
    b = head + " " + _paper(3, 6000)
    assert diversity([a, b])["diversity_max"] > 0.95


def test_bands_are_two_sided_where_tidiness_is_the_risk():
    """Agreement above its band is a failure, not a triumph.

    The seeded pilot scored 1.000 on factor selection against a real 0.920. A
    one-sided band would have called that the best result in the run.
    """
    lo, hi, _ = BANDS["agree_selection"]
    assert lo is not None and hi is not None
    assert not _verdict("agree_selection", 1.000)[0]
    assert _verdict("agree_selection", 0.920)[0]
    assert BANDS["na_rate"] == (0.0, 0.0, BANDS["na_rate"][2])

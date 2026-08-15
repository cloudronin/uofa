"""The shipped segmenter must not split inside a number.

There were two segmenters. Fifteen dev components imported the careful one from
`keyless_k2_extractive`; `keyless_extractor.py` -- the route users actually run
-- had its own:

    _SENT = re.compile(r"(?<=[.!?])\\s+(?=[A-Z(])")

which cuts "head rise is 0.72% of design" at the decimal point. K2 measured what
that costs when the fragment is then quoted as evidence: groundedness 0.000
instead of 1.000, because the entire value of quoting a span is the figures in
it.

So the shipped route quoted worse spans than every experiment that scored it,
and any span-based measurement standing on the naive splitter was partly
measuring the splitter rather than the method. One implementation now, in
`uofa_cli.segmentation`, re-exported by `keyless_k2_extractive` so its importers
are unchanged.

These tests pin the properties that made the careful version careful, and pin
that both call sites reach the same function.
"""

from __future__ import annotations

from uofa_cli.keyless_extractor import _sentences
from uofa_cli.segmentation import sentences


def test_a_decimal_does_not_end_a_sentence():
    """The case that named the bug."""
    text = "Measured head rise is 0.72% of design. The pump met its target."
    got = sentences(text)
    assert got == [
        "Measured head rise is 0.72% of design.",
        "The pump met its target.",
    ], f"split inside the decimal: {got}"
    assert any("0.72%" in s for s in got), (
        "the figure was destroyed by segmentation, which is the whole failure: "
        "a quoted span without its number is not evidence"
    )


def test_the_shipped_keyless_route_uses_it():
    """The point of the move.

    `uofa_cli.segmentation` being correct is worth nothing if the route that
    writes user-facing spans still calls a private copy. `_sentences` adds a
    minimum-length filter and must change nothing else.
    """
    text = "Measured head rise is 0.72% of design. The pump met its target."
    assert any("0.72%" in s for s in _sentences(text)), (
        "keyless_extractor._sentences lost the figure, so it is not using "
        "uofa_cli.segmentation"
    )


def test_dev_components_and_production_share_one_definition():
    """Re-export, not a second copy that drifts.

    Two segmenters is how this happened. If `keyless_k2_extractive.sentences`
    ever stops being the same object, the dev experiments and the shipped route
    can disagree again without anything failing.
    """
    import sys
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(root / "dev" / "tools" / "scripts"))
    from keyless_k2_extractive import sentences as dev_sentences

    assert dev_sentences is sentences, (
        "keyless_k2_extractive.sentences is no longer uofa_cli.segmentation."
        "sentences. Measurement and production can now diverge silently."
    )


def test_abbreviations_do_not_end_a_sentence():
    text = "See Fig. 4 for the mesh. Convergence follows."
    got = sentences(text)
    assert got == ["See Fig. 4 for the mesh.", "Convergence follows."], got


def test_a_markdown_row_stays_one_unit():
    """Table rows split into fragments that quote as nonsense."""
    text = "| Grid | GCI | Result |\n| fine | 1.2% | pass |"
    assert sentences(text) == ["| Grid | GCI | Result |", "| fine | 1.2% | pass |"]


def test_a_real_sentence_boundary_still_splits():
    """The guard rails must not cost the ordinary case.

    A segmenter that never splits passes every test above.
    """
    text = "The solver converged. Residuals fell below target. The case is closed."
    assert len(sentences(text)) == 3


def test_a_sentence_ending_in_a_number_does_not_split():
    """The known cost of the decimal guard, pinned rather than left to be found.

    `(?<!\\d\\.)` cannot tell "0.72% of design" from "below 1e-6. The case",
    so a sentence whose last character before the period is a digit runs into
    the next one. Measured here, not asserted as harmless.

    Kept as-is deliberately. The two failure directions are not symmetric: an
    over-split destroys the figure that makes a span worth quoting, and an
    under-split yields a longer span that still contains it. Any future fix must
    beat this on both, and `test_a_decimal_does_not_end_a_sentence` is the half
    that is not allowed to regress.
    """
    text = "Residuals fell below 1e-6. The case is closed."
    assert sentences(text) == ["Residuals fell below 1e-6. The case is closed."]

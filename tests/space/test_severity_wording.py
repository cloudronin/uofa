"""One weakener, one word, in every view that shows it.

`report_state` keeps a raw severity key and a reader-facing label, and says so:

    # lines, so the same item never reads "Medium" in one place and "Moderate"
    # in another. "Moderate" is the reader-facing word for the raw "Medium" key.
    _SEV_LABEL = {"Critical": "Critical", "High": "High",
                  "Medium": "Moderate", "Low": "Low"}

Two renderers ignored that and printed the raw key. Observed live on the
deployed Inspector, 2026-09-08, on a single run of the bundled sample:

    Reviewer view   "2 High, 1 Moderate"
    Author view     "3 weakeners fired (2 High, 1 Medium)"

Same three findings, two vocabularies, with a view toggle between them. A
reviewer comparing the two screens has to work out whether "Medium" and
"Moderate" are one severity or two.

The committed report goldens did **not** catch this. They render through
`report.py`, which already used the label helper, so they read "Moderate" and
stayed green while `_headline` printed "Medium" beside them. A golden that never
exercises the broken path cannot fail for it, which is why this file exists
rather than a new golden.
"""

from __future__ import annotations

import re

from uofa_cli.report_state import _headline, sev_label

RAW_KEYS = ("Critical", "High", "Medium", "Low")


def test_the_label_map_is_the_only_place_medium_is_renamed():
    """The mapping itself, pinned with its provenance."""
    assert sev_label("Medium") == "Moderate"
    assert sev_label("High") == "High"
    assert sev_label("Critical") == "Critical"
    assert sev_label("Low") == "Low"
    # An unknown severity passes through rather than vanishing: a severity we
    # cannot name must still be visible, not silently dropped.
    assert sev_label("Catastrophic") == "Catastrophic"
    assert sev_label(None) == ""


def test_the_headline_uses_reader_words_not_raw_keys():
    """The Author view's one-line summary, which is where this was found."""
    line = _headline(13, 13, 0, [{}, {}, {}], {"High": 2, "Medium": 1})

    assert "Moderate" in line, f"headline lost the reader-facing word: {line}"
    assert "Medium" not in line, (
        f"headline prints the raw severity key: {line!r}. The Reviewer view "
        "says 'Moderate' for the same finding."
    )


def test_no_view_can_reintroduce_a_raw_medium():
    """Every severity the headline can show must be a reader-facing word.

    Loops the raw keys rather than asserting one case, so a future severity
    added to the map cannot slip through with only its key rendered.
    """
    for raw in RAW_KEYS:
        line = _headline(1, 1, 0, [{}], {raw: 1})
        expected = sev_label(raw)
        assert expected in line, f"{raw!r}: expected {expected!r} in {line!r}"
        if expected != raw:
            assert not re.search(rf"\b{raw}\b", line), (
                f"{raw!r} leaked into the headline as a raw key: {line!r}"
            )

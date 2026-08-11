"""Section scoping for the prose path, and the contamination it exists to stop.

The binding Phase-4 constraint is that only content under an evaluation heading
may populate a Group-B property. It is enforced by **construction** -- the card
is sliced before an extractor sees it -- rather than by instructing a model to
ignore the rest. A prompt instruction is a request; text that is never sent
cannot be misread.

Why it matters, measured (`studies/card-eval-reporting-2026-08`, n=49): 45% of
cards mention a sampling setting and only 4% do so under an evaluation heading.
The other 41% is guidance for the reader. An extractor shown the whole card can
read "For thinking mode, use `Temperature=0.6`" as a statement about how the
reported scores were produced, and thereby silence W-EV-DET-03 on evidence about
something else entirely -- manufacturing the claim the rule tests for.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from uofa_cli.furnishers import card_eval

REPO = Path(__file__).resolve().parents[1]
_GEMMA = REPO / "tests" / "fixtures" / "model_cards" / "google__gemma-3-27b-it.md"

# A card shaped like the ones that motivated the constraint: usage guidance
# carrying sampling settings, and a separate section that reports evaluations.
_MIXED = """# Some Model

## Quickstart

Install and run:

```python
model.generate(**inputs, do_sample=True)
```

## Best Practices

> For thinking mode, use `Temperature=0.6`, `TopP=0.95`, `TopK=20`.
> For non-thinking mode, use `Temperature=0.7`.

## Evaluation

### Benchmark Results

| Benchmark | Metric  | Score |
| --------- | ------- | ----- |
| MMLU      | 5-shot  | 71.2  |
| GSM8K     | 8-shot  | 84.0  |

## Citation

Please cite as follows.
"""


def test_slicing_excludes_usage_guidance_settings():
    """The whole point: a temperature in "Best Practices" must not reach the extractor."""
    assert re.search(r"Temperature=0\.6", _MIXED), "fixture must contain the trap"
    scoped = card_eval.scoped_text(_MIXED)
    assert scoped, "the card does report an evaluation"
    assert "Temperature" not in scoped, (
        "usage guidance survived the slice - an extractor would read it as a "
        "determinism statement about the reported scores")
    assert "do_sample" not in scoped
    assert "MMLU" in scoped and "71.2" in scoped, "the actual evaluation content is kept"


def test_citation_and_quickstart_are_not_evaluation():
    headings = [s.heading for s in card_eval.eval_sections(_MIXED)]
    assert headings == ["Evaluation"]


def test_subsections_travel_with_their_parent():
    """gemma's results table sits under a subsection; a flat slice would lose it."""
    scoped = card_eval.scoped_text(_MIXED)
    assert "Benchmark Results" in scoped and "| MMLU" in scoped


def test_heading_match_is_whole_phrase_not_substring():
    """'Results of the training run' is not evaluation reporting."""
    card = "# M\n\n## Results of the training run\n\nWe trained for 3 epochs.\n"
    assert card_eval.eval_sections(card) == []


def test_no_eval_section_yields_empty_not_the_whole_card():
    """Returning the full card on no match would reintroduce the contamination,
    silently, on exactly the cards where slicing mattered most."""
    card = "# M\n\n## Quickstart\n\nUse `temperature=0.7`.\n"
    assert card_eval.scoped_text(card) == ""


def test_detector_asserts_nothing_about_quality():
    """A3: presence-only. It picks a sentence; it does not assess."""
    presence = card_eval.detect(_MIXED)
    assert presence.found and presence.has_eval_section and presence.has_results_table
    assert "mmlu" in presence.benchmarks_named
    assert not hasattr(presence, "sufficient")


def test_detector_reports_absence_when_a_card_truly_has_none():
    card = "# M\n\n## Quickstart\n\nInstall it.\n\n## License\n\nApache 2.0\n"
    presence = card_eval.detect(card)
    assert not presence.found
    assert presence.sections == ()


@pytest.mark.skipif(not _GEMMA.exists(), reason="gemma card fixture absent")
def test_real_card_slices_to_its_evaluation_sections():
    card = _GEMMA.read_text()
    presence = card_eval.detect(card)
    assert presence.found
    assert [s.heading for s in presence.sections] == [
        "Evaluation", "Evaluation Approach", "Evaluation Results"]

    scoped = card_eval.scoped_text(card)
    assert 0 < len(scoped) < len(card), "slicing must actually reduce the card"
    # The install snippet and usage docs are outside the evaluation sections.
    assert "pip install" not in scoped
    assert "do_sample" not in scoped
    # The benchmark table is inside them.
    assert "HellaSwag" in scoped


@pytest.mark.skipif(not _GEMMA.exists(), reason="gemma card fixture absent")
def test_patterns_live_in_pack_data_not_code():
    """A3 requires the pattern list to move without a release."""
    cfg = card_eval._detection_config("mrm-nist")
    assert "evaluation" in cfg["sectionHeadings"]
    assert "mmlu" in cfg["benchmarkNames"]

    # Behavioural, not a source grep. Grepping the module text cannot tell a
    # pattern from a docstring that mentions one, and would fail on exactly the
    # explanatory prose this codebase wants. Patch the config and see whether
    # behaviour follows it -- that is what "sourced from pack data" means.
    card = "# M\n\n## Wholly Invented Heading\n\n| B | S |\n| - | - |\n| X | 1 |\n"
    assert card_eval.eval_sections(card) == [], "control: not matched by default"

    card_eval._detection_config.cache_clear()
    try:
        patched = dict(cfg, sectionHeadings=cfg["sectionHeadings"] + ["wholly invented heading"])
        card_eval._detection_config.__wrapped__.__globals__  # noqa: B018  (exists check)
        import unittest.mock as _mock
        with _mock.patch.object(card_eval, "_detection_config", lambda pack="mrm-nist": patched):
            found = card_eval.eval_sections(card)
        assert [s.heading for s in found] == ["Wholly Invented Heading"], (
            "adding a heading to pack data did not change behaviour, so the "
            "patterns are not actually sourced from it")
    finally:
        card_eval._detection_config.cache_clear()

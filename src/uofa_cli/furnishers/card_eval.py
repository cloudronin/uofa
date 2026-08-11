"""Locate and slice a model card's own evaluation reporting.

Two consumers, one mechanism:

  * the **A3 presence-only detector** asks whether a card reports any evaluation
    at all, so the readout can pick the honest sentence: "no reported evaluation
    to assess" versus "reported evaluation present, sufficiency not assessed".
    It emits no nodes and asserts nothing about quality.

  * the **prose extractor** slices the card down to those sections before an LLM
    sees anything.

Slicing is the load-bearing decision, and it is enforced by construction rather
than by instruction. Across 49 cards, 45% mention a sampling setting and **4% do
so under an evaluation heading** (`studies/card-eval-reporting-2026-08`); the
remaining 41% is guidance for the reader, like Qwen3's "For thinking mode, use
`Temperature=0.6`". An extractor shown the whole card can read that as a
statement about how the reported scores were produced and thereby silence
W-EV-DET-03 using evidence about something else entirely.

A prompt instruction to ignore non-evaluation sections is a request. Text that is
never sent cannot be misread. So the constraint lives here, in a pure function
that is cheap to test, rather than in a paragraph an LLM may or may not honour.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from uofa_cli import paths

# `## Heading text` -> (level, text). Setext headings are not handled: they are
# rare in model cards and silently mis-slicing is worse than not slicing.
_HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.M)
_NON_WORD = re.compile(r"[^a-z0-9]+")


@dataclass(frozen=True)
class EvalSection:
    """One evaluation-reporting section of a card."""
    heading: str
    level: int
    text: str          # heading line + body, verbatim
    start: int         # character offset into the original card


@dataclass(frozen=True)
class EvalPresence:
    """What the presence-only detector found. Asserts nothing about quality."""
    has_eval_section: bool
    has_results_table: bool
    benchmarks_named: tuple[str, ...]
    sections: tuple[EvalSection, ...]

    @property
    def found(self) -> bool:
        """Any positive signal at all.

        A section heading is the primary signal; a named benchmark or a results
        table corroborates. Absence of all three is the only state that licenses
        "no reported evaluation to assess", and that sentence is a claim about
        the card, so it should not rest on one pattern.
        """
        return self.has_eval_section or self.has_results_table or bool(self.benchmarks_named)


@lru_cache(maxsize=4)
def _detection_config(pack: str = "mrm-nist") -> dict:
    """Heading and benchmark patterns, from pack data rather than code (A3)."""
    path = paths.pack_dir(pack) / "data" / "eval_detection.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _normalise(text: str) -> str:
    return _NON_WORD.sub(" ", text.lower()).strip()


def _is_eval_heading(heading: str, patterns: list[str]) -> bool:
    """Whole-phrase match, never substring.

    Exact match, or a suffix match on a whole phrase -- never a prefix match. A
    prefix rule was tried first and matched "Results of the training run" against
    "results", which is not evaluation reporting and would have fed training prose
    to the extractor. Exact-only was tried next and cost 24 points of section
    detection (71% -> 47%), missing "Distilled Model Evaluation" and
    "4. Evaluation Results".

    Suffix matching recovers those without reopening the hole, because English
    heading style puts qualifiers BEFORE the noun: the tail carries the subject.
    "Training results" still matches "results" by suffix and is admitted -- an
    accepted false positive, since a training-results section that reaches the
    extractor yields no Group-B properties rather than wrong ones.

    The asymmetry justifies the strictness: a MISS costs a stated N/A, which is
    honest; a FALSE HIT costs contamination, which is the failure this module
    exists to prevent. Multi-word variants belong in the pack data list, where
    they can be added without a release.
    """
    norm = _normalise(heading)
    pats = {_normalise(x) for x in patterns}
    if norm in pats:
        return True
    # Suffix match, but never prefix. "Distilled Model Evaluation" and
    # "4. Evaluation Results" are evaluation reporting; "Results of the training
    # run" is not, and it is a PREFIX match ("results ...") rather than a suffix
    # one. That asymmetry is the whole rule: qualifiers precede the noun in
    # English heading style, so the tail carries the subject.
    return any(norm.endswith(" " + pat) for pat in pats)


def eval_sections(card_text: str, pack: str = "mrm-nist") -> list[EvalSection]:
    """Sections of the card that report its own evaluation, in document order.

    A section runs from its heading to the next heading of the same or shallower
    level, so subsections stay with their parent -- gemma's "Benchmark Results"
    table sits under "## Evaluation" and would be lost by a flat slice.
    """
    if not card_text:
        return []
    patterns = _detection_config(pack)["sectionHeadings"]
    heads = [(m.start(), len(m.group(1)), m.group(2), m.end())
             for m in _HEADING.finditer(card_text)]

    out: list[EvalSection] = []
    for i, (start, level, text, _end) in enumerate(heads):
        if not _is_eval_heading(text, patterns):
            continue
        stop = len(card_text)
        for later_start, later_level, _t, _e in heads[i + 1:]:
            if later_level <= level:
                stop = later_start
                break
        out.append(EvalSection(heading=text, level=level,
                               text=card_text[start:stop].rstrip(), start=start))

    # Drop sections wholly contained in an earlier one, so a parent and its
    # subsection are not both sent (duplicated text inflates nothing but cost,
    # and duplicated tables invite duplicate ValidationResult nodes).
    kept: list[EvalSection] = []
    for sec in out:
        if any(s.start <= sec.start and sec.start < s.start + len(s.text) for s in kept):
            continue
        kept.append(sec)
    return kept


def detect(card_text: str, pack: str = "mrm-nist") -> EvalPresence:
    """Presence-only detection (addendum v0.1 A3).

    Never emits ValidationResult nodes and never asserts sufficiency. It decides
    only which honest sentence the readout prints, so it cannot upgrade a
    heuristic run into an assessed one.
    """
    cfg = _detection_config(pack)
    sections = tuple(eval_sections(card_text, pack))
    low = (card_text or "").lower()
    named = tuple(sorted(
        b for b in cfg["benchmarkNames"]
        if re.search(rf"(?<![a-z0-9]){re.escape(b)}(?![a-z0-9])", low)))
    has_table = bool(re.search(r"^\|.*\|\s*$", card_text or "", re.M)) and "---" in (card_text or "")
    return EvalPresence(has_eval_section=bool(sections), has_results_table=has_table,
                        benchmarks_named=named, sections=sections)


def scoped_text(card_text: str, pack: str = "mrm-nist") -> str:
    """The card reduced to its evaluation sections, for the prose extractor.

    Returns "" when nothing matches, which the caller must treat as "no reported
    evaluation" rather than falling back to the full card. Falling back would
    reintroduce exactly the contamination this function exists to prevent, and it
    would do so silently on the cards where slicing mattered most.
    """
    return "\n\n".join(s.text for s in eval_sections(card_text, pack))

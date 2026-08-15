"""One sentence segmenter, shipped, so measurement and production agree.

There were two. `dev/tools/scripts/keyless_k2_extractive.py` had the careful one
and fifteen dev components import it; `keyless_extractor.py` -- the shipped
keyless route, the one users actually run -- had its own:

    _SENT = re.compile(r"(?<=[.!?])\\s+(?=[A-Z(])")

That splits inside a decimal. "Measured head rise is 0.72% of design" becomes
"...head rise is 0." and the figure is gone. K2 measured the cost of exactly
this: groundedness 0.000 instead of 1.000, because the whole value of quoting a
span is the numbers in it, and a truncated span carries none.

So the shipped route quoted worse spans than every dev experiment that scored
it, and any span-based measurement built on the naive splitter was partly
measuring the splitter. This module is the K2 implementation, moved to where
production can import it; `keyless_k2_extractive` now re-exports from here so
its fifteen importers are unchanged and there is one definition to fix.

Pure stdlib on purpose. The pipeline's segmentation, furniture filter and
component registry are the parts a reader might expect spaCy for, and spaCy's
POS tagger and NER were measured insufficient here (K3 -> K3c).
"""
from __future__ import annotations

import re

# A sentence ends at .!? + whitespace + capital/quote/bullet. The lookbehind
# excludes a digit, so "0.72%" never splits, and excludes the common
# abbreviations that otherwise fragment engineering prose.
_ABBREV = r"(?<!\bapprox)(?<!\bFig)(?<!\bEq)(?<!\bNo)(?<!\bvs)(?<!\bcf)(?<!\bi\.e)(?<!\be\.g)"
_SENTENCE = re.compile(rf"(?<=[.!?]){_ABBREV}(?<!\d\.)\s+(?=[A-Z\"“(\-•])")


def sentences(text: str) -> list[str]:
    """Split into sentences without breaking decimals or abbreviations."""
    out: list[str] = []
    for block in text.split("\n"):
        block = block.strip()
        if not block:
            continue
        # Markdown table rows and bullets are single units; splitting them on
        # punctuation produces fragments that quote as nonsense.
        if block.startswith(("|", "-", "*", "#")):
            out.append(block)
            continue
        out.extend(s.strip() for s in _SENTENCE.split(block) if s.strip())
    return out

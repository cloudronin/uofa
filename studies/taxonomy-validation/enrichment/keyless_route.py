"""The keyless table route for P2 uncertainty, frozen for the holdout gate.

## ROUTE VERSION 1 — IMMUTABLE. Gated 2026-08-12.

**A gated route version is frozen permanently.** Its measured properties, good
and bad, are what the qualification row asserts, and editing it would silently
change what that row means.

**Published defects of v1** (found by the holdout, deliberately NOT repaired):

1. **Compound dispersion headers are not read.** `HEADER` is anchored, so
   `reward_std` / `reward_mean` do not match. Cost: 2 of 27 holdout false-fires.
2. **A standalone `SE` metric column is misread as standard error.** Measured on
   `UE|PoE|PlE|SE|EE`, where the route returned `93.75`. Cost: 1 of 33 holdout
   false-clears (3.0%).

   **Production consequence, stated on the qualification row:** this false-clear
   mode credits a card with an uncertainty it does not state, which **silences
   W-AL-01 on that card**, at a measured 3%.

   The obvious fix — "93.75 is too large to be a standard error" — is refused on
   doctrine, not on difficulty. The moment the route reasons about magnitude it
   stops being a field read and becomes inference, which is the backend's job
   under D2. A deterministic reader that guesses is neither.

**Any improvement is route v2**, and v2 qualifies against a **new holdout draw** —
never against rows 2, 29 or 41, which caught v1. Repairing against the cases that
found a defect is the in-sample loop the gate exists to break.

**This is the route exactly as developed in-sample.** It is committed here,
unchanged, BEFORE being scored against the holdout labels, so the gate scores a
fixed artifact rather than one that could be adjusted after seeing which cases it
fails. Any change after this commit is a NEW route needing its own gate.

Two branches, both field reads:

  inline    a dispersion token bound to a number inside one cell -- "0.5409 ± 0.0222"
  columnar  a header cell naming a dispersion, then a NUMBER in that column in a
            later row. lm-eval-harness emits exactly this, and the word and the
            value are rows apart, so the inline branch cannot see it. This is the
            branch that was REPAIRED in-sample after eight misses, which is why
            the holdout draw over-samples it.

**Branch redundancy is MEASURED SERENDIPITY, not designed coverage.** On the
holdout's two `_`-separator rows -- where a pipeline mangled `±` into `_` -- the
inline branch failed and the columnar branch caught both, because it keys on the
header and never needed the glyph. That was not designed and must not be relied
on: a future format that defeats both branches has no third to fall back to.

Reading a value out of a `Stderr` column infers nothing, which is what makes this
legitimate under D2 ("structured input reads deterministically; prose requires a
backend"). A markdown eval table is structured input.

Returns the stated dispersion, or None. None is a real answer: the `_blank`
contract from `keyless_extractor.py` applies -- a route with no reading leaves
the field empty rather than satisfying a minCount with a plausible value.
"""

from __future__ import annotations

import re

# A dispersion token bound to a number, inside one cell.
INLINE = re.compile(r"(?:±|\+/-|\+-)\s*\d+(?:\.\d+)?", re.I)

# A header cell that names a dispersion, and nothing else. Anchored on both ends
# on purpose: `SE` alone is a dispersion header, but `SE` inside `SEQ_LEN` or a
# task named `se` is not, and an unanchored match would read a metric name as a
# column of uncertainties.
HEADER = re.compile(
    r"^\s*(?:stderr|std\.?\s*err|std(?:ev)?|se|95%\s*ci|error)\s*$", re.I)

# A cell holding a bare number. An EMPTY cell does not match, which is the
# behaviour the empty-header tables depend on: a header with no values under it
# is an absence, and a route that fired on the header alone would invent one.
NUMBER = re.compile(r"^\s*[<>±+\-]?\s*\d+(?:\.\d+)?\s*$")

_PIPE = re.compile(r"(?<!\\)\|")


def _cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def _table_lines(text: str) -> list[str]:
    return [ln for ln in text.splitlines() if len(_PIPE.findall(ln)) >= 2]


def read_uncertainty(eval_sections: str) -> str | None:
    """The stated uncertainty from a table, or None if none is stated."""
    lines = _table_lines(eval_sections)

    for line in lines:                                   # inline
        m = INLINE.search(line)
        if m:
            return m.group(0).strip()

    for i, line in enumerate(lines):                     # columnar
        idx = [j for j, c in enumerate(_cells(line)) if HEADER.match(c)]
        if not idx:
            continue
        for row in lines[i + 1:]:
            rc = _cells(row)
            for j in idx:
                if j < len(rc) and NUMBER.match(rc[j]):
                    return rc[j].strip()
    return None

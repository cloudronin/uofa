#!/usr/bin/env python3
"""Recover the predeclared credibility levels from Table 3 of NTRS 20200002832.

Why this exists
---------------
Johnson (2020) states the achieved credibility levels in prose on p.25, but the
*predeclared* levels — the requirement the achieved levels are measured against —
exist only as green cell fill on Table 3, p.7. There is no text to read. Every
text-based extractor, LLM or otherwise, returns nothing for those eight values,
because there is nothing there to return.

They are still recoverable, from the page's vector geometry rather than its text.
This script does that, and exists so the recovery is reproducible and checkable
rather than asserted.

What it does NOT do
-------------------
It is not an extraction method and its output is not extractor provenance. Under
the pilot's rule the recovered values enter the workbook as author-side
corrections during the review pass, with the method named in the citation anchor.
See TABLE3_RECOVERY.md.

Run:  python dev/build/pilot-johnson/table3_recover.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import pdfplumber

PDF = Path(__file__).parent / "source" / "NTRS-20200002832-Johnson-2020.pdf"
TABLE3_PAGE = 6  # zero-indexed; p.7 of the PDF
SHADE = (0.761, 0.839, 0.608)  # the green Johnson uses for "predeclared"

# 7009A Appendix E Table 3 column order, left to right after the Level column.
FACTORS = [
    "Data Pedigree",
    "Verification",
    "Validation",
    "Input Pedigree",
    "Uncertainty Characterization",
    "Results Robustness",
    "M&S History",
    "M&S Process / Product Management",
]


def _mid(a: float, b: float) -> float:
    return (a + b) / 2.0


def recover(pdf_path: Path = PDF) -> dict[str, int]:
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[TABLE3_PAGE]
        rects = page.rects
        words = page.extract_words()

        # Column bands from the table's own vertical rules. A rule is a filled
        # rect that is tall and hairline-thin; deriving the bands from the drawn
        # grid rather than from hardcoded x values is what makes this checkable.
        rules = sorted({round(r["x0"], 1) for r in rects
                        if (r["x1"] - r["x0"]) < 1.5 and (r["bottom"] - r["top"]) > 5})
        if len(rules) != len(FACTORS) + 2:
            sys.exit(f"expected {len(FACTORS) + 2} column rules, found {len(rules)}: {rules}")
        # rules[0]..rules[1] is the Level column; the factor columns follow.
        bands = list(zip(rules[1:-1], rules[2:]))

        # Row bands from the level digits in the Level column, which sit between
        # the first two rules. Each digit's band runs to the next digit up.
        digits = [w for w in words
                  if w["text"] in {"0", "1", "2", "3", "4"}
                  and rules[0] <= w["x0"] and w["x1"] <= rules[1]]
        digits.sort(key=lambda w: w["top"])
        if [w["text"] for w in digits] != ["4", "3", "2", "1"]:
            sys.exit(f"unexpected level digits: {[(w['text'], w['top']) for w in digits]}")
        centres = {w["text"]: _mid(w["top"], w["bottom"]) for w in digits}

        shaded = [r for r in rects if r.get("non_stroking_color") == SHADE]
        if not shaded:
            sys.exit("no shaded cells found — the fill colour or the file changed")

        out: dict[str, int] = {}
        for factor, (x0, x1) in zip(FACTORS, bands):
            cells = [r for r in shaded if x0 <= _mid(r["x0"], r["x1"]) <= x1]
            if not cells:
                sys.exit(f"no shaded cell in the {factor} column")
            # The shading is drawn as a stack of thin bands covering one row; take
            # the whole extent and pick the level digit that sits inside it.
            top = min(r["top"] for r in cells)
            bottom = max(r["bottom"] for r in cells)
            hits = [lvl for lvl, c in centres.items() if top <= c <= bottom]
            if len(hits) != 1:
                sys.exit(f"{factor}: shading spans {hits or 'no'} level rows "
                         f"(top={top:.1f} bottom={bottom:.1f})")
            out[factor] = int(hits[0])
        return out


def anchor(factor: str, pdf_path: Path = PDF) -> str:
    """The citation anchor for a recovered value, method included."""
    return (f"p.7 Table 3, {factor} column, cell fill rgb{SHADE} "
            f"(geometric recovery — see TABLE3_RECOVERY.md)")


if __name__ == "__main__":
    levels = recover()
    width = max(len(f) for f in levels)
    print(f"{'7009A factor':<{width}}  predeclared")
    for factor, level in levels.items():
        print(f"{factor:<{width}}  {level}")

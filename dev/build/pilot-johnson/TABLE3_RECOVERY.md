# Table 3 recovery — the predeclared levels, and why they are author-side

State: DRAFT. Values below are candidates for the author's review pass.

## The problem

Johnson (2020) states the **achieved** credibility levels in prose on p.25, under
"THE FINAL CREDIBILITY ASSESSMENT". It states the **predeclared** levels — the
requirement those achieved levels are measured against, and half of the credibility
claim — nowhere in text. They exist only as green cell shading on the reproduced
7009A Table 3, p.7, introduced by one sentence: "Credibility requirements as
predeclared are shown below on a copy of Table 3 in 7009A Appendix E by green
shading."

A text-reading extractor returns nothing for those eight values. Not a wrong value,
not a low-confidence value: nothing, because there is no text to read. This is the
protocol outline's §2c case ("a value the source located somewhere non-obvious") in
a harder form than the outline's prompt anticipates, and it is the reason this file
exists as its own artifact rather than a line in the ambiguity log.

## The recovery

`table3_recover.py`, run against `source/NTRS-20200002832-Johnson-2020.pdf` with
pdfplumber (already a dependency of `uofa[extract]`, so no new tooling).

Method, in three steps:

1. **Column bands from the table's own drawn grid.** The vertical rules are filled
   rectangles under 1.5pt wide and over 5pt tall. There are ten, giving the Level
   column plus eight factor columns. The script asserts that count rather than
   trusting hardcoded x values, so a different file fails loudly instead of
   returning a plausible wrong answer.
2. **Row bands from the level digits.** The digits `4 3 2 1` sit in the Level
   column; the script reads their vertical centres from the text layer. It asserts
   the digits come out in that order.
3. **Cell fill.** Shaded cells are rectangles with non-stroking colour
   `(0.761, 0.839, 0.608)`. For each factor column the script takes the full
   vertical extent of its shading and requires **exactly one** level digit centre
   to fall inside it.

Every step asserts. The script exits non-zero rather than guessing if the file, the
grid, or the fill colour changes.

## Result

| 7009A factor (Table 3, p.7) | Predeclared (recovered) | Achieved (p.25, prose) | Met? |
|---|---|---|---|
| Data Pedigree | 3 | 3 | = |
| Verification | 3 | 4 | + |
| Validation | 1 | 1 | = |
| Input Pedigree | 3 | 3 | = |
| Uncertainty Characterization | 4 | 4 | = |
| Results Robustness | 4 | 4 | = |
| M&S History | 3 | 3 | = |
| M&S Process / Product Management | 2 | 4 | + |

## Corroboration

The recovery is checked three ways against the paper's own text, none of which was
used to produce it:

1. **The radar plot, p.9.** Its legend is `Required` / `Achieved` and its title is
   "Credibility Meets or Exceeds Requirements". The recovered table has achieved ≥
   predeclared on all eight factors, with no exceptions and two exceedances. A
   recovery that placed any shaded cell one row wrong would contradict that title.
2. **M&S History, p.7-8.** The paper narrates this one factor's predeclaration in
   prose because it was negotiated: "Given what happened was what was planned, the
   results would rate a Level 3." Recovered predeclared M&S History = 3.
3. **Validation, p.6.** "Validation will not be performed. Real world data was not
   available and funding and time constraints precluded running confirmation
   tests." Recovered predeclared Validation = 1, the lowest row, and achieved is
   also 1.

An earlier independent pass over the raw PDF content stream — parsing `re`
operators and `scn` fill colours by hand, without pdfplumber — produced the same
eight values. Two parsers, one answer.

## The rule this hands the protocol

**The values are author-side, not extractor output.** The pilot runs the LLM
extract first and records verbatim what it returns for these cells. The recovered
values then enter the workbook during the review pass as author corrections. They
are counted on the human side of the provenance reconciliation in `RUN_LOG.md`,
never as `extracted`.

This is not bookkeeping fussiness. The provenance counts are the package's answer
to "how much of this was actually read from the document", and that answer is the
thing Ch3's Human Adjudication Role section rests on. A value that a human
recovered by parsing page geometry is a human contribution however it was
mechanised, and crediting it to the extractor would overstate the extractor and
understate the human in the one place the manuscript quotes.

**The citation anchor carries the method, not just the location.** For these cells
the anchor reads:

    p.7 Table 3, <factor> column, cell fill rgb(0.761, 0.839, 0.608)
    (geometric recovery — see TABLE3_RECOVERY.md)

so a reviewer who goes to p.7 and finds no text is told why, and what to do
instead.

Proposed protocol rule, filed under §2 as RULE-NEEDED:

> Where a reviewed value is recoverable only by non-textual means, the citation
> anchor names the recovery method as well as the location, the recovered value is
> recorded as an author-side correction rather than extractor output, and the
> method is reproducible from the encoding package.

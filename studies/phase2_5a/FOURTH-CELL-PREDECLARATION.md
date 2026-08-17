# Pre-declaration — the fourth cell of the NC trajectory table

Committed **2026-08-17, before `run_fourth_cell.py` exists and before any number is
produced.** Same discipline as `M5-REBASELINE-PREDECLARATION.md`: the interpretation
is fixed in writing first, so it cannot be fitted to the result afterwards.

## The one sentence

**This cell measures the regenerated negative-control corpus against the old
catalog, so that the trajectory table has no unmeasured cell and INV-16's bounded
inference becomes a measurement rather than an argument.**

## What is being run

[INV-16](../../docs/investigations/INV-16-nc-trajectory-decomposition.md) closed with
one cell empty:

| | M5 corpus, unpatched | regenerated corpus |
|---|---|---|
| **v0.5.7** | 0/176 = 0.0% (committed) | **← this run** |
| **v0.5.15.1** | 8/176 = 4.5% (measured) | 166/171 = 97.1% (committed) |

Four classifications, all at zero LLM cost, all re-classifications of committed
packages:

| | corpus | catalog | why |
|---|---|---|---|
| **B** | `holdout-2026-04-29-v0515` NC | **v0.5.7** | **the ruled cell** |
| A | `2026-04-26` (M5) NC | **v0.5.7** | reproduction check against the committed 0/176 |
| C | `2026-04-29-v0512` hybrid NC | **v0.5.7** | tests INV-16's bounded inference |
| D | `holdout-2026-04-29-v0515` NC | v0.5.15.1 | reproduction check against the committed 166/171 |

## Design, and the confound it is built to expose

The catalog version is varied by passing the rules file from tag `v0.5.7`
(`79f87997`, 2026-04-27) through the engine's existing `--rules` override. **The code
is current in every cell.** Both versions carry the same 21 rule ids, so the variable
is predicate refinement alone — no rule was added or removed.

That leaves one confound, and it is declared rather than discovered: **the two
committed figures were produced by 2026-04 code, and these cells use 2026-08 code.**
Cells A and D exist to test exactly that. If A reproduces 0/176 and D reproduces
166/171, the code-version difference is immaterial and all four cells are
comparable. **If either fails to reproduce, that is a finding about the trajectory
table, and it gets recorded as one rather than explained away** — including the
possibility that it invalidates the comparison this run was meant to complete.

## The prediction being put on the line

INV-16 argued, without measuring, that corpus regeneration alone cannot lift the
clean rate because W-EP-01 and W-AL-02 each fired on 100% of M5 NCs at v0.5.7 and
neither had a regeneration tool.

**Declared prediction for cell C: at or near 0%.** If the hybrid corpus scores
materially above zero at v0.5.7, my inference in INV-16 was wrong and that section
gets corrected, not softened.

**No prediction is declared for cell B**, the ruled cell. INV-16 states the fresh
2026-04-29 holdout came from a later pipeline and what v0.5.7 scores on it is
genuinely unknown. Declaring an expectation here would be inventing one.

## What this does not decide

- **It does not reopen the adjudication.** The ruling that M5's W-ON-02 firings are
  correct detections of real uninjected absences, not false positives, rests on what
  the packages contain. No number from this run bears on it.
- **It does not decide P2-A.** Re-baselining Phase 2 at v0.5.15.1 remains a separate
  authored call.
- **It does not revise the 97.1%**, which stands as the specificity figure with its
  scope attached.

What it can do is change the *attribution* sentence in INV-16 — how much of the
trajectory is corpus and how much is rules — and that is the only claim it is
licensed to move.

## Failure condition

If anything in this file needs amending once the numbers are known, **that is a
finding about this file and gets recorded as one, not edited away.**

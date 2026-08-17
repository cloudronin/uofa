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

---

# RESULT — 2026-08-17

## The closed table

| | M5 unpatched | v0.5.12 hybrid | v0515 holdout |
|---|---|---|---|
| **v0.5.7** | **0/176 = 0.0%** (A) | **0/148 = 0.0%** (C) | **0/171 = 0.0%** (B) |
| **v0.5.15.1** | 8/176 = 4.5% | — | **166/171 = 97.1%** (D) |

No cell is unmeasured. **The ruled cell, B, is 0.0%.**

## Both reproduction checks reproduce exactly

| | committed | measured now | |
|---|---|---|---|
| A | 0/176 | **0/176** | headline and denominator |
| D | 166/171 | **166/171** | headline and denominator |

The code-version confound declared above is **eliminated, not argued away**. All
four cells are comparable.

Cell A goes further than the headline: it reproduces **every per-rule value** in
`v0512_summary.md:23-35`'s M5 baseline column, to the decimal — W-AL-02 100.0%,
W-EP-01 100.0%, W-ON-02 89.8%, COMPOUND-01 89.8%, COMPOUND-03 79.5%, W-AR-02 23.9%,
W-CON-01 19.9%. Ten of ten. A 2026-04 measurement reproduced in 2026-08 by current
code against the tagged catalog, with no value disagreeing.

## The declared prediction held

Cell C was predicted "at or near 0%" and came in at **0/148 = 0.0%**. INV-16's
bounded inference — that corpus regeneration cannot lift the rate while W-EP-01 and
W-AL-02 fire on everything — is now measured rather than argued. Both fire on
**100%** of cell C.

## The finding: the gain is interactive, not additive

**Neither axis alone produces any material gain.**

- **Corpus regeneration alone: 0.0 points.** The regenerated holdout scores exactly
  zero against the old catalog. Not "less than expected" — zero.
- **Rule refinement alone: 4.5 points**, the M5 column.
- **Together: 97.1%.**

The mechanism is visible in the per-rule data, and it is symmetric: **each axis is
blocked by a rule that only the other axis fixes.**

| Axis | Blocked by | Firing | Why that axis cannot clear it |
|---|---|---|---|
| Catalog (regenerate the corpus, keep v0.5.7) | **W-EP-01** | **171/171 = 100%** on the regenerated holdout | no regeneration tool ever targeted it; it needed the v0.5.8 predicate guard |
| Corpus (refine the rules, keep M5) | **W-ON-02** | 158/176 = 89.8% on M5 | it was never rule-fixed; it was closed by inserting the field |

W-EP-01 gates the catalog axis and W-ON-02 gates the corpus axis, so a package is
clean only where both were addressed — and they were addressed by different means.
That is why the 97.1% exists in exactly one cell of four.

## What needs correcting, recorded as a finding

**The declaration above needed no amendment.** It declared no expectation for cell B
and its one prediction held.

**INV-16 does.** Its summary sentence — *"The remaining 92.6 points travel with the
corpus"* — is **falsified**. The 92.6 points travel with neither factor; they exist
only in the joint cell. INV-16's *other* formulation, *"both were necessary; neither
alone exceeds 4.5%,"* was exactly right and is now measured rather than inferred, as
was its explicit warning that the parts *"do not sum to 97.1 because they are not
independent."*

So the correction is to one sentence that reached for an additive split the same
document elsewhere disclaimed. Corrected in place at INV-16 §Result with the
falsification stated, not edited away.

## Measurement notes

- **Cell C's denominator is 148, not 176.** The hybrid's inserted
  `hasSensitivityAnalysis` stubs are the inline-object form that current SHACL
  rejects — the D2 boolean mismatch — so 31 packages read non-conformant under the
  2026-08 schema. It does not affect the 0.0% result, which holds on every evaluable
  row, but the hybrid corpus is **not** schema-valid today and no figure should be
  quoted from it without that note.
- **Cell B's denominator, 171, matches the committed "171 validated"** independently.
- Cell D's five residual firings are W-ON-01 (3), W-AL-01 (2), W-EP-02 (2), W-AR-05
  (2), COMPOUND-03 (1) across 5 packages — the documented 5/171 = 2.9%.
- Re-derive: `PYTHONPATH=src python studies/phase2_5a/run_fourth_cell.py`; rows in
  `fourth_cell_results.json`.

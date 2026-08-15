# evidence_span: killed, and it stays killed

Ruled 2026-08-15, closing the deferral. Written so the idea cannot be
re-proposed without the number attached — the same protection the anchor
dictionary has.

## The ruling

**Killed stays killed.** Two declared revisions against a 0.70 verbatim floor
landed at **0.258** and **0.369**. Phase 3 reached length-invariance without the
field: the shotgun null fell from 0.7527 to 0.0505 on rationales alone, and the
candidate now separates from its worst null by 9.0×.

Reviving `evidence_span` now would be a search for a passing configuration on a
feature that has already lost twice, and
`docs/decisions/2026-08-14-h2-replacement-thresholds.md` forbids that shape by
name: *"A failure is a result, not a prompt to look for a third metric."* The
same reasoning that bars a third metric bars a third arm.

## The number that has to travel with any re-proposal

**The failure mode is silent elision of parentheticals.** The model does not
invent spans. It copies the document's own words in the document's own order and
quietly drops bracketed material and trailing qualifiers:

- dropped `(lid-driven cavity Re=1000, backward-facing step, and rotating channel flow)`
- dropped `(scaled residuals)`
- dropped `from the aerodynamics methods group (Dr. …)`

Similarity to the nearest source sentence runs 0.75–0.86. The span reads
correctly and **cannot be found by exact search**, which is the one thing the
field was specified to provide. A reviewer told to search the document for the
span gets no result 63% of the time.

Arm 2 addressed exactly this — *keep every parenthetical, the span must survive
exact search* — and moved verbatim from 0.258 to 0.369. Real movement, less than
half the distance to the floor.

**Any future proposal must state 0.369 and the elision mechanism**, or it is
proposing something already measured without saying so.

## What was true about it, and is not a reason to revive it

The field localises to a source sentence **0.711** of the time against the
rationale's **0.263** — 2.7× better as a Phase 3 input. That is real and it is
recorded.

It is not a reason to revive the field, for two reasons. Phase 3 cleared its
length-invariance target without it, so the gain is unclaimed rather than
needed. And the deferral was resolved on Phase 3's actual numbers, which is the
condition under which the deferral was granted — the decision was taken with the
evidence, not despite it.

If a future workstream needs a localisable span, this measurement is the
starting point and the elision failure is the first problem to solve. That is a
different proposal from reviving this one.

## What the field cost, and what it bought

**Cost:** two extraction arms, a prompt change to two packs, and one regression
— inserting the field's note pushed the absence rule 16 lines from the `status:`
field it governs and broke `test_absence_rule_sits_with_the_field_it_governs` on
both prompts. That guard exists because the rule was already present and ignored
at 14 lines' distance, during the shopping-list failure. Reordered; caught by
the suite, not by review.

**Bought:** the demonstration. The plan of record calls `evidence_span` "the
highest-value change in the plan". It was given kill criteria before it was
built, measured against them twice, failed both, and did not ship — while Phase
3 shipped in the same week at a published cost of 0.6068 → 0.4524. The two
decisions were independent, which is the point.

A kill criterion that has never killed anything describes intent. One that
killed the change its own author called highest-value describes practice.

## Status of the prompt text

The `evidence_span` field remains in the vv40 and nasa-7009b prompts, because
Phase 3 reports span figures beside rationale figures per the standing ruling on
`studies/evidence-span/FINDINGS.md`. It is **not** a workbook column, it is
**not** described anywhere as a span a reviewer can search for, and no shipped
behaviour depends on it.

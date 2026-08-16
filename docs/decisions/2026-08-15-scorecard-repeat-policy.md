# Standing scorecard law: repeats, spreads, and "unstable at the bar"

**Date:** 2026-08-15
**Status:** standing rule — applies to every qualification scorecard, not just
the study that produced it
**Origin:** `studies/model-selection/`, where the study failed this rule before
it existed

## Why this is a rule and not a study quirk

The model-selection study produced **13 blank rationales in one run and zero in
the next, at the same pin**. A separate regeneration of the synthetic baseline,
also at a pinned config, moved claim density **0.199 → 0.115** — a 42% relative
swing on the incumbent.

Both are `W-EV-DET-03`: *"no determinism / repeat-run policy stated for the
evaluation"*, severity **High** in the model-credibility pack — the weakener
this project fires at vendors.

**The study qualifying extractors failed its own determinism floor, and the
taxonomy caught it because we applied it to ourselves.** The baseline failed it
too, one level down, and had been failing it silently for longer.

## The rule

1. **Minimum three runs for any hosted arm.** One run is a sample, not a row.
2. **Report per-clause spread beside every point value.** Min–max across runs,
   for each clause of the conjunction, not just the aggregate.
3. **An arm whose spread straddles a threshold is `UNSTABLE AT THE BAR`** —
   a first-class verdict alongside pass and fail, and not reducible to either.
4. **Local arms may cite determinism in lieu of repeating.** Fixed weights on
   fixed hardware: demonstrate run-to-run identity once and that is the stronger
   claim.
5. **Pins on quantities measured this way are bands, not points**, wide enough
   to hold the observed runs, with those runs recorded so the width is justified
   rather than arbitrary.

## Why the third clause is the load-bearing one

Pass and fail both assert that the measurement *decided something*. When a
spread crosses the threshold, the run decided it — not the candidate. Reporting
whichever run landed on the convenient side is not a rounding error, it is the
whole failure mode, and it is invisible in any single-run table.

**`UNSTABLE AT THE BAR` names what single-run evaluations structurally cannot
see.** That is most of what the adversarial catalogue flags vendors for, and
until now this project had no vocabulary for it in its own results.

## Corroboration that bands beat points

`acceptance_criteria_distinct` was banded (300–420) under an earlier ruling. It
survived a full corpus regeneration at 314 **without edit**. The point pins
beside it — claim density at ±0.01, rows-below-required as an integer — did not
survive the same regeneration and had to be rewritten.

One banded pin and two point pins met the same event; the band was the one that
held.

## Excluded rows are named, never absorbed

A document that fails on some arms and not others is excluded from **per-arm
denominators with the exclusion stated on the scorecard**. Five-paper arms with
a named exclusion beat six-paper arms with a hidden hole.

`elemance` is the current instance: it failed twice, differently — a timeout on
`family-72b`, a `ValueError` on `frontier`. **Two distinct failure modes on one
document is a fixture question, not noise**, and both tracebacks are filed rather
than averaged away. It is the largest paper in the set at 1,319 sentences.

## Re-entry, so a failed scorecard does not become a standing invitation

When no candidate clears, the study closes with a **declared re-entry
condition** rather than an open search: *a candidate must clear the conjunction
on the real corpus under this repeat policy.*

That is the difference between future work and gate-shopping. Without it, "no
candidate cleared" quietly licenses trying models indefinitely until one does,
which is the same shape as trying metrics until one passes.

# Amendment 02: the §5a micro-ground was drawn by a broken sampler

**Raised and signed 2026-08-11.** Amends `ENRICHMENT-PROTOCOL.md` §5a and §7.

`ENRICHMENT-PROTOCOL.md` is signed and is **not modified by this file**. The
signed text stands; this amendment travels with it so the change is visible as a
change.

---

## The defect

§5a specifies an unfiltered control: 20–30 cards drawn at random with **no**
keyword filter, from the richest ground, labeled identically to the enriched
stratum. Its purpose is to bound the keyword filter's selection bias — the
filtered stratum finds positives by their characteristic language, so its
specificity is an upper bound, and the micro-ground is the only measurement
bearing on the gap.

**The reservoir sampler in `search.py` deduplicates the enriched pool by
eval-text hash but does not deduplicate the micro-ground reservoir.**

Measured on the committed draw:

| Stratum | Rows | Distinct eval texts |
|---|---:|---:|
| enriched | 117 | **117** |
| micro-ground | 30 | **4** |

**27 of the 30 micro-ground rows are the same byte-identical empty template
stub.** Auto-generated stub cards dominate the corpus, so a proportional random
draw landed on 27 copies of one card. The sampler did what it was written to do;
what it was written to do was wrong for a control.

## What this invalidates

**§7's zero-yield inference is withdrawn until the redraw.** The protocol says:

> **Zero yield** is evidence the filter's coverage is adequate, which converts
> the upper bound into something closer to an estimate.

That reading was never available on this draw. Zero yield from 30 rows carrying
4 distinct texts — 27 of them an empty stub that can state no property at all —
is evidence that the draw was degenerate, not that the filter is good. Reporting
it as filter adequacy would have converted a sampler bug into a methodological
claim in the paper's favour.

**The keyword-selection bias therefore remains an unbounded upper bound.**
Everywhere specificity is reported, §7's limitation stands undiminished: cards
phrasing a property unusually are under-represented, and no measurement currently
bounds that gap.

Nothing else is affected. The **enriched** stratum deduplicated correctly (117
rows, 117 distinct texts) and every rate computed on it stands.

## The remedy

1. **Dedupe the micro-ground reservoir by eval-text hash**, matching the enriched
   pool's discipline. A control that samples the same text 27 times measures one
   card 27 times.
2. **Re-run the search** and redraw the micro-ground. Same seed, same declared
   grounds (§4), same target of 20–30 — only the duplicate-suppression changes.
3. **Label the redrawn micro-ground** under the unchanged instructions.
4. **Only then** does §7's filter-coverage inference become available, and it is
   reported with this amendment cited so a reader knows which draw produced it.

## Why this is an amendment and not a bug fix

It touches a protocol-declared artifact whose properties a reader is entitled to
rely on. Fixing the sampler silently would leave the record saying a control was
drawn as specified when it was not, and the corrected draw would be
indistinguishable from the original in the committed history.

There is no shame in the record. A protocol that can say "the sampler was broken,
here is the fixed draw, and here is what the broken one could not support" is
working. One that quietly re-runs and reports the better number is not.

## Status

**Remedy not yet executed.** The defect is recorded now so that no figure
depending on §5a is published in the interim, and so the redraw is a scheduled
step rather than a discovery someone makes later.

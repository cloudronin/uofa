# Addendum v0.6: A17 — the field study (prevalence), one page

**Applies to:** model-credibility-pack-spec.md + addenda v0.1–v0.5
**Status:** one-pager. Scope only; the frame, thresholds and pre-registration
come after the A16 catalog settles, per A16.8's "validation before prevalence".

---

## A17.1 What it is

A16 asks *does the instrument measure what it claims*. A17 asks *what does the
field actually publish*. One study, two outputs, in that order — a prevalence
figure from an unvalidated instrument measures the instrument.

Output: per-property publishing rates across the model-card population, which is
the FAccT paper's empirical contribution and the field-scale form of the claim
already supported at two-source convergence (`studies/cohort-2026-08`,
`studies/card-eval-reporting-2026-08`): **scores are published routinely, the
properties that make scores interpretable are published at 0–4%.**

## A17.2 The field arm: `modelbiome/ai_ecosystem_withmodelcards`

**Candidate, pending the two checks in A17.3.**

| | |
|---|---|
| Rows | 1,860,411 |
| Non-empty cards (200k sample) | 49.4% → **~920k assessable** |
| Card dates | 2022-03 → **2025-07** |
| Eval-bearing (A3 detector) | 48.4% of non-empty |
| Extras | likes, downloads, tags, licenses, arxiv_papers, and model **lineage** (parent / finetune / quantized / adapter / merge) |

**Why it is the field arm rather than A16's corpus.** Liang is a published
paper's dataset with task categories and citable provenance — the right choice
for validating an instrument against adjudicated labels, and it stays frozen in
that role. Prevalence needs scale and recency instead, and this corpus is 29×
larger on assessable cards and nearly two years fresher.

**The lineage columns matter for the frame.** A population containing many
quantizations and merges of one parent will inflate any prevalence figure with
near-duplicate cards. Stratification must account for family, not just task and
size, or the study reports how often a popular card was forked.

## A17.3 Two diligence checks, both outstanding

Neither is a formality; either can disqualify the corpus.

1. **Pinning adequacy.** A CSV in a HF dataset repo with **no dataset card** and
   128 downloads. A content hash pins the file, but A9.1's artifact-pin claim
   requires the source be re-fetchable at a stated revision. Whether the repo's
   history is stable enough to cite is unverified.
2. **Redistribution terms.** Unstated in the repo. Whether card text may be
   quoted in a paper, or shipped as a test fixture, is unknown. The underlying
   cards carry their own model licences, which is a second layer.

**A corpus that cannot be cited or quoted is not a venue for a published study**,
however rich. If either check fails, Liang remains the only pinned corpus and
A17's scope shrinks to what 32,111 cards support.

## A17.4 Consequence for W-EV-DIV-07

DIV-07's opportunity rate is 0.25% here against 0.07% in Liang — ~4,700
opportunities versus 24. If the checks clear, DIV-07's Mode 2 could be
adjudicated on this arm rather than deferred.

That is **not** decided here. It is drafted as
`studies/taxonomy-validation/AMENDMENT-01-div07-venue.md`, unsigned, and the
A16 freeze is untouched. The amendment is not recommended for signature until
A17.3 clears.

## A17.5 Sequencing

Unchanged, and this addendum moves nothing forward of it: **the gold-set
labeling sessions remain the critical path.** A17 cannot start until the A16
catalog settles, and the catalog cannot settle without adjudicated labels.
Identifying a better field corpus early is worth recording; it is not progress
toward settling.

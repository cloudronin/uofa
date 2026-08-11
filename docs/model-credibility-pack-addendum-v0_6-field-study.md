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

## A17.3 Diligence checks — RUN 2026-08-11, both clear

Two claims in the first draft of this section were wrong, and the checks
corrected them. Recorded rather than quietly edited.

**Check 2, redistribution terms: PASSES.** The dataset is **CC-BY-4.0**, declared
in a dataset card that **does exist** (`README.md` frontmatter), and the corpus
has an accompanying paper (`arXiv:2508.06811`). The first draft said "no dataset
card" and implied unattributed provenance — that came from one API response
returning a null `cardData`, which I read as absence rather than re-checking the
raw README. It is a published research artifact with an attribution-only licence,
so quoting card text in a paper and shipping fixtures are both permitted with
attribution.

**Check 1, pinning adequacy: PASSES at corpus level, with one stated limit.**

| | |
|---|---|
| Repo revision | `4cb5d8739a8fce7c03826994dd756c244b4126bf` |
| File | content-hashable, single CSV |
| Snapshot dates | models 2025-07-13; card scrape completed 2025-07-21, both stated in the card |
| **Per-row card revision** | **absent** — no `sha` / `revision` / fetch-date column |

`createdAt` is the *model's* creation date, not the card's fetch date, and there
is nothing recording which HF revision each card body came from.

**Why it still clears.** The corpus file is the artifact, and it is pinned: repo
sha plus content hash plus stated snapshot dates satisfy A9.1's non-HF artifact
pin. Every row's text is re-derivable *from the pinned corpus* by content hash,
which is exactly how the A16.3 gold set already pins its rows.

**The limit, stated so it is not discovered later:** you cannot verify an
individual card against live HF at the version scraped, because that version was
not recorded. Claims are attributable to the snapshot, not to HF's history. That
is the same position Liang leaves us in and is acceptable for a study whose
population *is* the snapshot — but it forecloses any check of the form "was this
card altered after scraping".

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

# The anchor dictionary fails a third time, on the easiest data in the repo

Phase 0, 2026-08-14. `dev/tools/scripts/published_rationale_ceiling.py`.

`tests/fixtures/extract_corpus_vv40/bundle_bologna_bcthip/ground_truth.json`
carries 23 `published_rationale` strings, each with a `pack_factor` mapping. The
labels are the **paper authors'**, not an annotator's. No Python in the repo read
them until now.

## Result

| method | correct | rate |
|---|---|---|
| name-only null | 12 / 23 | 0.522 |
| prompt anchors (`Look for:`) | 12 / 23 | **0.522** |

**Delta +0.000.** The pack prompts' anchor phrases recover nothing that matching
the factor's own name and acronym did not already recover.

The null here is deliberately hostile to the asset: it looks for the factor's
name and acronym in the rationale and nothing else. It scores 0.522 because
domain experts writing about Software Quality Assurance write "SQA". That is not
attribution; it is the author restating the heading.

## Why this is the strongest form of the negative result

These rationales are the friendliest input a lexical method will ever get:

- short expert clauses, median **8 words**, no filler
- written in V&V 40 vocabulary, beside a V&V 40 gradation, for a V&V 40 factor
- written by the people who did the work, with no reason to obscure anything

If the anchors were going to beat a name-match anywhere, it would be here. They
do not beat it at all.

**8 of the 11 misses are the anchors declining to fire** — no `Look for:` phrase
matched the rationale at all, so the method returned nothing. The prompt's
anchors do not appear in prose that domain experts write about the very factors
those anchors describe.

The other three errors land exactly on the confusable cluster the corpus already
names: `Model form` → `Model inputs`, `Output comparison` → `Numerical code
verification` (twice), and both relevance factors → `Use error`.

## Third strike, three different tasks

| task | anchors | control | verdict |
|---|---|---|---|
| routing | P 0.973 / R 0.235 / F1 0.367 | 0.960 | fails |
| post-hoc re-attribution | 0.059 | — | fails |
| **author-rationale recovery** | **0.522** | **0.522 name-only** | **fails, delta 0.000** |

The plan of record already rules: *do not build the anchor dictionary*, and
*reject any "score the rationale against the prompt's Look-for terms" proposal
with the re-attribution number*. This adds a third refusal on a third task,
against the most favourable data available, and closes the remaining objection
that the earlier two numbers came from hard cases.

## Limits, stated

One document, one standard, 23 factors, one annotator-of-record (the paper's
authors). This is an upper bound on an easy case, not a corpus measurement, and
it is not evidence about the extractor — nothing here ran an extractor. It is
evidence about what can be recovered from rationale text by lexical means when
the rationale was written by an expert and not by a model trying to justify a
filing.

What it does **not** show: that rationale text carries no signal. A trained,
label-masked classifier is a different mechanism and is measured separately at
flag precision 0.605 against a 0.378 base. This rules out one specific
mechanism, on a third task.

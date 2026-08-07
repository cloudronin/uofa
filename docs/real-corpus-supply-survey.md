# How much real data is actually out there?

Written after the synthetic/real router inversion, which showed that synthetic
evaluation ranks K6 above K4 while real documents rank them the other way round.
That makes real documents the evaluation substrate rather than a validation
sample, and raises a question nobody had asked: **how many real credibility
assessments exist to evaluate on?**

Surveyed 2026-08-06 against the NTRS API.

## What we have

| | distinct documents | usable prose |
|---|---|---|
| in the corpus today | 4 | **2** |
| in `MANIFEST.json`, never turned into bundles | 2 | 0 |

The 13 Tier 1 bundles draw on only 4 documents — one report backs 8 of them,
because a single paper assesses several (model × mechanism) units. That is
leverage for the disambiguation task and **not** for transfer, where only
distinct documents count.

Of the 4, only elemance and opensim are extractable prose. ARED is a poster and
IMM is a 32-slide deck at 43 words a slide.

The two unused manifest entries are both IWS2023 posters
(`20230000585` Fall-from-Heights, `20230000583` Boot/Ankle). Two further
manifest entries turned out to be alternate versions of papers already used —
`20240000233` and `20240011014` — and were correctly excluded.

## What the survey found

Three NTRS queries: `"credibility assessment" "NASA-STD-7009"`,
`"credibility assessment scale"`, and `"credibility factor" score verification
validation "input pedigree"`. All candidates are `PUBLIC` distribution with
`PUBLIC_USE_PERMITTED` or `GOV_PUBLIC_USE_PERMITTED` rights.

**Likely to carry a filled assessment of a specific model:**

| citation | type | note |
|---|---|---|
| **20140003849** | **Conference Paper** | **ARED — the prose twin of the poster we already have.** The one clear new prose document. |
| 20170005224 | Presentation | MPCV exercise operational volume, same DAP family |
| 20140013389 | Presentation | Renal stone module, same IMM family as `20150021308` |

**Methodology, not application** — these describe the scale rather than score a
model, so they are not bundles: `20140017305`, `20200002832`, `20120006603`,
`20090005963`, `20080015742`, `20100031270`.

## The finding: NTRS is thin for prose

Realistic NTRS ceiling is roughly **7 distinct documents**, of which about
**3 are journal prose** — the two we have plus the ARED conference paper.
Everything else is posters, slide decks, or papers about the standard.

That is not enough to make real-document evaluation primary. It is enough to
roughly double the prose sample, from 2 to 3.

## Where the larger pool is

**ASME V&V 40 medical-device case studies**, not NASA 7009. Three reasons:

1. They are peer-reviewed journal articles — the genre that is scarce here, and
   the one where routing actually has to work.
2. They map onto the **vv40 pack directly**. Every 7009A document needs
   `cas_mapping.roll_up` to be scoreable at all; a V&V 40 case study does not.
3. **We already have one.** Morrison et al. 2019 is in the repo as
   `tests/fixtures/extract/ground_truth/morrison-cou{1,2}.json`, with per-factor
   goals transcribed and its gradation letters recorded. It has never been used
   as a routing document.

Published examples exist beyond Morrison — the Bologna Biomechanical CT
assessment is one — but the size of that pool was not measured here and should
be before committing to it.

The caveat that applies to the whole pool: V&V 40 papers are written to
*demonstrate* the framework, so they spell everything out. Morrison is the
ceiling for how well specified a bundle can be, not the norm — measured on the
synthetic corpus, model risk is stated in 2% of documents and model influence in
0%.

## Recommendation

1. **Fetch `20140003849`** — one prose document, and directly comparable to the
   ARED poster already annotated, which makes it a clean genre-controlled pair:
   same assessment, same factors, poster vs paper.
2. **Promote the two unused manifest posters** to bundles. Cheap, already
   sourced, and the ARED result suggests posters with labelled rationale blocks
   are close to self-annotating.
3. **Size the V&V 40 pool before committing to NTRS beyond that.** If it yields
   ten prose documents, it is the better investment by a wide margin, and it
   needs no rollup layer.

Do not read step 2 as progress on the transfer question. Posters are the easy
genre — ARED routes at 0.86 recall@5 against 0.33 for journal prose, because its
evidence lines begin with the factor name. Adding posters raises the aggregate
and answers nothing.

## Sources

- [NTRS citation 20140003849 — ARED conference paper](https://ntrs.nasa.gov/citations/20140003849)
- [NTRS citation 20230000585 — IWS2023 Fall-from-Heights poster](https://ntrs.nasa.gov/citations/20230000585)
- [NTRS citation 20230000583 — IWS2023 Boot/Ankle poster](https://ntrs.nasa.gov/citations/20230000583)
- [ASME V&V 40-2018 standard](https://www.asme.org/codes-standards/find-codes-standards/assessing-credibility-of-computational-modeling-through-verification-and-validation-application-to-medical-devices)
- [Credibility assessment per ASME V&V40: Bologna Biomechanical CT](https://www.sciencedirect.com/science/article/pii/S0169260723003930)
- [FDA — Assessing the Credibility of Computational Modeling](https://www.fda.gov/media/154985/download)

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

## What the three recommendations actually yielded

All three were carried out. **Net effect on the transfer question: nothing.**

| step | outcome |
|---|---|
| Fetch `20140003849` | **Rejected.** NTRS types it "Conference Paper"; the artifact is a one-page 700-word extended abstract with no CAS table, and its text extracts with doubled characters (`VALLIDATION ANND CREDIBIILITY`) from a font-encoding fault. |
| Promote `20230000585` | **Rejected.** Zero per-factor scores in the text layer -- they exist only in radar plots, the same problem as the elemance thresholds. Not transcribable at published granularity. |
| Promote `20230000583` | **Accepted**, with a limit. Prints a fully explicit table inline, so levels transcribe cleanly. But **zero sentences name any factor** -- it lists scores and otherwise discusses ankles and EVA. Transcribable for levels, *not annotatable for routing.* |
| Size the V&V 40 pool | 92 PMC hits, of which most describe the standard. Four clear applications found. |

So the corpus gained one bundle and the routing evaluation gained nothing. Both
rejections were only visible on inspection -- NTRS metadata called one a
conference paper and the other a poster with credibility scores, and both
descriptions were true and useless.

### A variant was added, by the rule that anticipated it

`20230000583` prints Code Verification and Solution Verification as separate
factors. `cas_mapping.py` had removed exactly those two keys with the note *"add
a key when a transcribed table prints it, not before"*. A table now prints them,
so `decomposed_8_7009a` was added as a **new** variant rather than by widening
`decomposed_7009a` -- widening would give every existing decomposed bundle a key
its own table never printed, and an unused key is a denominator.

### The V&V 40 pool, sized

| paper | year | access |
|---|---|---|
| Morrison et al., hemolysis in centrifugal blood pumps | 2019 | PMC open — **already a repo fixture** |
| Catalano et al., TAVI patient-specific modelling I | 2025 | APL Bioeng |
| Scuoppo et al., TAVI patient-specific modelling II | 2025 | APL Bioeng |
| Bologna Biomechanical CT | 2023 | Elsevier |

Larger than NTRS's prose supply and in the right genre, but the licensing model
is different: these are commercial-journal articles, not `PUBLIC_USE_PERMITTED`
NASA works. The fetch-manifest-plus-SHA-256 discipline that makes the NTRS
corpus redistributable does not obviously transfer, and each paper needs
checking individually.

## The three V&V 40 papers, assessed

All three were obtained and read with the pipeline's own reader.

### A third PDF pathology: lost spaces

| paper | alpha tokens >20 chars | verdict |
|---|---|---|
| tavi1 | **10.36%** | unusable |
| tavi2 | **11.25%** | unusable |
| **bologna** | **0.06%** | clean |
| elemance / opensim | 0.01% / 0.08% | known-good baseline |

Both TAVI papers lose word spacing on extraction —
`thisworkseekstoperformapopulation-basedvalidation`,
`DepartmentofEngineering`. Real English words are almost never over 20
characters; ~10% of theirs are. That is a third extraction pathology after
column interleaving and line wrapping, and it destroys every downstream
sentence operation. No reader fix was attempted.

Independently of the text quality, neither TAVI paper publishes a per-factor
credibility table. They follow the V&V 40 *process* — QoI, CoU, model risk — and
Part I says so directly: *"the ASME also recommends an applicability assessment
to complete the credibility assessment. This was, however, not carried out in
this study."*

They are still interesting for one thing the corpus almost entirely lacks:
**Part I states model risk as 5 on a 1–5 scale, with both inputs given.** Across
the synthetic corpus, risk level is stated in 2% of documents and model
influence in 0%.

### Bologna is the best real document found

`10.1016/j.cmpb.2023.107727` — Aldieri et al., *Comput. Methods Programs
Biomed.* 240:107727 (2023). CC BY-NC-ND.

* **Clean extraction** — 0.06% run-together, 11,018 words, 40% sentence-like.
* **Full V&V 40 assessment** — CoU, QoI, and model risk derived from decision
  consequence × *regulatory impact*, which the authors substitute for model
  influence and explain at length. A realistic deviation, not a defect.
* **Table 1 gives per-factor: available range, selected rigour, achieved
  credibility, and a written rationale.**

```
SQA (5.1.1.1)              a-c   b: SQA procedures from the vendors are referenced.   Medium
NCV (5.1.1.2)              a-d   b: multiple benchmark test cases are used...         Medium
Discretisation (5.1.2.1)   a-c   c: conservation equation balances checked...         High
Numerical solver (5.1.2.2) a-c   c: problem-specific sensitivity study on solver...   High
```

* **Maps to the vv40 pack directly** — no `roll_up` layer, unlike every 7009A
  document in the corpus.
* **The per-factor rationale is annotatable evidence**, which is precisely what
  the two accepted posters lacked.

It also settles an open question. The Morrison transcription recorded that
gradation counts differ per factor — SQA a–c, NCV a–d — and flagged that the
letter→level convention was unrecoverable. Bologna independently prints **the
same ranges**, so the differing counts are a property of the standard rather
than of Morrison.

One caveat: Bologna uses V&V 40's finer decomposition (5.2.2.1.1 "Quantity of
test samples", 5.2.2.1.2 "Range of characteristic test samples", …) — roughly 20
sub-factors against the pack's 13. Transcribing at published granularity means
a fourth variant, the same call already made for `decomposed_8_7009a`.

**Recommendation: Bologna becomes the next bundle, and the first V&V 40 one.**
It is a journal-prose document with annotatable per-factor evidence, which is
the exact gap nothing else in this survey filled.

## Original recommendation, kept for the record## Original recommendation, kept for the record

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

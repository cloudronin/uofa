# Bologna encoding — INVESTIGATION, not a packet

> **CLOSED 2026-08-22 by R-B** (`docs/UofA_Decision_Record_2026-08-16_Addenda.md`).
> The usage trace (`BOLOGNA_TRACE.md`, `cada14ac`) resolved this investigation: Bologna is
> disqualified from A3 and barred from any new assignment, and Decision 8's conditional is
> closed. The three open items in "What the author must supply or decide" below are moot —
> **no source document is to be supplied and no encoding is to be run.** The section is
> retained as the record of what was open when. The A3 slot is refilled from
> `A3_CANDIDATES.md` under R-A3-SCREEN.

~~**AWAITING-AUTHOR.**~~ W5 of `UofA_Protocol_Draft_and_Encoding_Prep_Spec_v1_0.md` instructs
that if the Bologna source materials are not assembled in the repo, the item is an
investigation reporting what exists and what is missing rather than a substitution. They
are not, and there is a second reason not to run the pipeline that matters more than the
first.

Bologna is Aldieri A, Curreli C, Szyszko JA, La Mattina AA, Viceconti M, "Credibility
assessment of computational models according to ASME V&V40: Application to the Bologna
Biomechanical Computed Tomography solution," Comput Methods Programs Biomed 2023;240:107727,
DOI `10.1016/j.cmpb.2023.107727`, licence CC BY-NC-ND.

## The blocking issue is not the missing PDF

Encoding Bologna under the draft protocol would put a document that is already load-bearing
in the H2 evaluation chain through the extract path, and §1 of the draft protocol excludes
exactly that:

> Evaluation references for H2 are outside this protocol. They are built under the
> annotation protocol and never regenerated through the extract path, because H2 measures
> agreement with a corrected self and an extractor-derived reference would make the
> extractor a party to its own evaluation.

Bologna is one of the six annotated documents in `studies/real-document-rescore/FINDINGS.md`
(row `bologna | vv40 | 0/13 | 895`), and its ground truth is the declared substrate for both
`studies/attribution-agreement/PREREGISTRATION.md` and
`studies/published-rationale-ceiling/FINDINGS.md`.

INV-5 is **ESCALATED and open** on precisely this, and names the conflict as three-way:

| Claimant | Basis |
|---|---|
| A3 external negative control | the role W5 assigns it |
| Scorecard pool | v2.0 §A10, "Bologna (Aldieri 2023) is the next bundle" |
| H2 evaluation corpus | already realised, not a plan |

INV-5's own words: "A3's 'external' negative would be a document the H2 arm already measures
on." Running W5's pipeline now would decide that escalation by executing it, which is the
opposite of how the summary records the question ("Which claim wins"). The relief route INV-5
names, screening Ahn and de Weck for the scorecard pool first, has not been reported as run.

## What exists in the repo

Substantial transcribed material, none of it the source document.

| Artifact | Content |
|---|---|
| `tests/fixtures/extract_corpus_vv40/bundle_bologna_bcthip/ground_truth.json` | 23 `expected_factors` transcribed from the paper's Table 1, each with published available range, selected gradation, achieved credibility, and printed rationale. Also the COU, and the model-risk derivation |
| `.../metadata.json` | standard vv40, tier 1, quality real, `published_granularity: vv40_subfactors` |
| `docs/v1/annot_bologna.json` | 13 evidence-span annotations covering 11 of 13 pack factors, under a selection rule fixed before annotating |
| `docs/v1/valresults_bologna.json` | transcribed validation results |

Two things recorded there are worth the author's attention because they bear on the encoding
rather than on the escalation.

**The paper carries no numeric levels.** Its ground truth states this explicitly: the paper
publishes a letter gradation (a to d) for the goal and Low, Medium, or High for what was
achieved, and neither is a NASA CAS score. Converting them "would invent two conventions the
document does not state." That is the same refusal the Johnson pilot made under A-06 and the
draft protocol's declination rule, arrived at independently by whoever transcribed this
bundle. It is corroboration for the rule rather than a new problem.

**The paper deviates from V&V 40 and says so.** The authors substitute regulatory impact for
model influence in the model-risk derivation and argue for it explicitly. The transcription
records it as printed, noting the substitution is theirs and "a real deviation from V&V 40
rather than an error to normalise away." An encoding would need an ambiguity-log entry for
it under §5 of the draft protocol.

## What is missing

The source document itself. No PDF, no extracted text, nothing beyond the DOI. The corpus
bundle holds ground truth and metadata only.

The repo's own supply survey explains why rather than treating it as an oversight:
commercial-journal articles are not `PUBLIC_USE_PERMITTED` NASA works, "the
fetch-manifest-plus-SHA-256 discipline that makes the NTRS corpus redistributable does not
obviously transfer, and each paper needs checking individually"
(`docs/real-corpus-supply-survey.md`). Bologna extracts cleanly, at a 0.06% pathology rate
against 10% for the two TAVI papers, so the obstacle is licensing rather than quality.

CC BY-NC-ND permits redistribution of the unmodified work with attribution for
non-commercial use, which on its face allows committing the PDF. That reading is not mine to
apply on the author's behalf.

## What the author must supply or decide

1. **Rule INV-5 before any encoding runs.** Which of the three claims wins, or whether the
   Ahn and de Weck screen runs first to relieve the scorecard pool. Encoding Bologna decides
   this by default, and by executing rather than by ruling.
2. **If A3 wins, resolve the H2 boundary.** Either the draft protocol's §1 separation gets an
   exception with its rationale, or A3's negative control moves to a document the H2 arm does
   not measure on. The second keeps the separation clean.
3. **Supply the source document** and confirm the licence reading permits committing it under
   `dev/build/` alongside the encoding.

Until 1 and 2 are settled, no pipeline is run and no packet exists. That is the whole of W5's
output, per its own instruction.

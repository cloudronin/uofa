# Phase 2, arm 2: declared before running

Arm 1 result, `evidence_span` as first specified, 8 bundles / 152 factor rows,
`meta-llama/Llama-3.3-70B-Instruct-Turbo`:

| criterion | floor | measured | |
|---|---|---|---|
| span filled | ≥ 0.70 | **0.993** (151/152) | PASS |
| span verbatim in corpus | ≥ 0.70 | **0.258** (39/151) | **KILL** |
| stitched (interior sentence boundary) | — | 5/151 | |

## What the failure actually is, which is not what the number suggests

The non-verbatim spans are **not invented**. Every one inspected is the
document's own words, in the document's own order, with parenthetical or
trailing material silently removed:

- *"…three vendor verification cases confirmed…"* — dropped
  `(lid-driven cavity Re=1000, backward-facing step, and rotating channel flow)`
- *"…driven below 1 × 10⁻⁵ before solutions were accepted."* — dropped
  `(scaled residuals)`
- *"…conducted by a senior engineer."* — dropped
  `from the aerodynamics methods group (Dr. …)`

Similarity to the nearest source sentence runs 0.75–0.86. The model is tidying
the sentence, not inventing one.

That distinction is load-bearing and must not be flattened in any writeup. "The
model invents evidence spans" would be false, and it is a worse error than the
one being measured. The true statement is: **the model elides without marking
the elision**, so the span cannot be found by exact search — which defeats the
one thing the field was for.

## Two questions, and arm 1 only answers one

**Q-product — can a reviewer find the span in the document?** No. 0.258. The
field as specified fails.

**Q-metric — can Phase 3 localise the span to the right source sentence?**
Unknown. Elided parentheticals do not obviously break token-overlap
localisation, and Phase 3 needs sentence indices, not exact strings. Arm 1 did
not measure this, so nothing is known about it either way.

## Arm 2, declared now

**One revision, not iteration to a pass.** Repeatedly editing a prompt until it
clears a kill criterion is the criterion doing no work. This is the single
revision arm 1's diagnosis warrants — the failure has an identified and specific
cause, and the instruction never addressed it. If arm 2 fails, `evidence_span`
is killed as specified and Phase 3 proceeds on rationales alone.

**The change:** state the elision failure at the point of use — keep
parentheticals and trailing qualifiers, and the span must be findable by exact
search. This is the same fix shape as the absence rule: the constraint restated
in terms of the specific observed violation, adjacent to the field it governs.

**Criteria, unchanged from arm 1** — the floors do not move because the arm did:

    KILL if evidence_span is filled on < 70% of factor rows
    KILL if < 70% of filled spans are verbatim substrings of the corpus
    KILL if mean_overall_f1 moves more than 0.004

**Added measurement, reported for both arms:** the fraction of filled spans that
localise to a source sentence whose token overlap with the span is ≥ 0.60. This
answers Q-metric and is **reported, not gating** — it is a new measurement and
giving it a threshold today, after seeing arm 1, would be the retroactive
thresholding this project has already been burned by.

## What no arm-2 result licenses

A pass does not make `evidence_span` a workbook column. The Credibility Factors
sheet has eight fixed columns indexed positionally by the writer,
`parse_extracted_xlsx`, the import path and the goldens. That change ships only
if the field is going to be used, and it is a separate decision from whether the
model can produce the field.

A pass also says nothing about whether the span is the *right* sentence for the
factor. That is attribution, it is what Phase 3 measures, and it is not
measured by either arm here.

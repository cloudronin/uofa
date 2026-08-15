# H2 replacement gate: thresholds, declared before the real-document re-score

**Date:** 2026-08-14
**Status:** DECLARED, NOT YET MEASURED against the real corpus
**Amends:** [`2026-08-14-h2-gate-amendment.md`](2026-08-14-h2-gate-amendment.md)
**Consumed by:** the Ch4 H2 section and the R6/U8 metrics spec, which are
written *after* the re-score, not before it

The amendment moved H2 off detection F1 and onto the attribution/groundedness
conjunction. It deliberately left the conjunction unnumbered, because numbering
it in the same breath as reporting 0.9637 would have been the retroactive
thresholding the amendment exists to avoid.

This file numbers it. **The real-document re-score has not been run.** Every
figure below is either a synthetic-corpus measurement or a pre-existing
real-document figure, and each is labelled as such. Nothing here is fitted to a
result that does not yet exist.

## The six conditions, with numbers

### 1. Beat the run's own permutation null by a stated margin

**Threshold: margin ≥ 0.25, and ≥ 3 sd above the permutation mean.**

Synthetic reference, Phase 3 sentence-index rule, 515 scored rows, 4400
permutation iterations:

    candidate         0.4524
    permutation null  0.0526  (sd 0.1027)
    margin           +0.3999   -> 3.9 sd

The margin is set at 0.25 because the synthetic margin is 0.40 and real
documents are expected to be harder; a threshold at the synthetic value would
be a threshold no real result could clear. The sd condition is the binding one
at low margins — a large gap over a null with a large spread is not a gap.

The permutation null is computed on **the run's own rationales with labels
shuffled**, so it inherits their length and vocabulary. A null written
independently would differ in length as well as attribution, and length is the
confound this whole workstream removed.

### 2. No null in the battery exceeds the figure, at any rationale length

**Threshold: absolute. Any null reaching the candidate fails the gate,
regardless of the other five conditions.**

Synthetic reference: worst null is shotgun k=20 at 0.0505 against 0.4524, a
9.0× separation, with the sweep nearly flat in k (0.0388 / 0.0466 / 0.0505 at
k = 5, 12, 20).

No tolerance. This is the condition detection F1 failed — its worst null
*exceeded* the candidate — and a gate that tolerates near-misses on it would
not have caught that.

### 3. Stated against the real-document agreement ceiling

**Threshold: the reported figure must be stated beside 0.714, and a threshold
above 0.714 is not set, because it is unreachable by a perfect extractor.**

**0.714 is the REAL-document same-sentence inter-annotator agreement**, and it
is the right ceiling here. It is *not* the 0.913 measured in
`studies/attribution-agreement/`, which is the **synthetic** corpus.

That substitution is a named trap in this repo. `d1_annotator_agreement.py`
opens with it: *"The only reliability figure this project has is 89.3%
inter-annotator agreement — measured on the synthetic corpus, which
subsequently turned out to invert method rankings. Checking the reliability of
the data you are no longer using is not a check."* Using 0.913 as a
real-document ceiling would repeat exactly that.

The established band is [0.60, 0.85] with real at 0.714
(`corpus_profile.py:80`, `seeded_agreement.py:5`).

#### What condition 3 is actually for, stated generally

**A score above the human agreement ceiling is not excellence. It is evidence of
leakage.** A perfect instrument cannot exceed the agreement of the humans whose
judgments define the truth it is scored against — if annotators agree with each
other 71.4% of the time, then 71.4% is the most an instrument can score while
still being measured against them. Anything higher means the candidate and the
reference are not independent.

This was drafted against a hypothetical and **caught an actual on first
contact**. The first real-document run scored 0.8545 with three of six papers at
exactly 1.000, because it scored the annotation's own evidence text against gold
sentence sets derived from that same text. Three papers at exactly 1.000 is
circularity's signature: a measurement comparing something to itself does not
merely score well, it scores *perfectly*, and perfection on a noisy human
reference is impossible by construction.

Condition 3 is therefore a **leakage detector**, not a quality threshold. It has
no floor and it never passes anything. It only ever fires.

### 4. Measured on the real corpus, not the generator

**Threshold: the real-document figure is the reported result. The synthetic
figure appears beside it and never alone.**

Per the plan's standing rule, and per the denominator rule graduated in
`studies/misfile-signal/`: paired synthetic and real measurements are
inseparable in every citation, and where they disagree the real number is the
result.

Instrument: `dev/tools/scripts/real_attribution_reference.py`, six
hand-annotated papers, 56 of 58 annotated factors located, 69 of 72 spans.

### 5. FP/FN rates from the disagreement adjudication published beside it

**Threshold: published, not bounded. There is no number to clear — the
requirement is that the figures exist and are reported.**

Synthetic reference already published in
`studies/attribution-sentence-index/`: 209 disagreement rows, of which at least
91 of 176 old-right/new-wrong are gold-set errors rather than rule errors, and
the localiser's own error rate is **at most 11.7%** of scored rows.

The real-document run must produce the equivalent. A rule whose disagreements
have not been looked at is a rule whose error profile is unknown.

### 6. Groundedness as the triple, never a lone number

**Threshold: coverage, claim_density and groundedness are reported together, in
that order, in every table. A lone groundedness figure fails this condition
however high it is.**

The reason is now measured rather than argued. The C3 migration took
claim_density from 0.565 to 0.199 — checkable claims 864 → 200 — while coverage
*rose* to 1.000 and groundedness held at 0.990. Two of the three moved the
reassuring way while three quarters of the verifiable content disappeared.
Reported alone, either would have described that as an improvement.

See `studies/hosted-model-specificity/`, Q3, for the Goodhart framing that must
accompany the triple wherever it appears.

## What fails the gate

Any one of: margin under 0.25, or under 3 sd; any null reaching the candidate at
any length; the real-document figure absent or reported without the synthetic
one; the disagreement adjudication not run; a lone groundedness number.

**A failure is a result, not a prompt to look for a third metric.** If the
conjunction does not clear on real documents, the finding is that H2 cannot
currently be supported on attribution, and that is what gets written. The
sequence detection-F1 → attribution → *something else* would be gate-shopping
with extra steps, and the whole point of numbering these before the run is that
there is nowhere to move to afterwards.

## Known limits carried into the re-score

These are properties of the instrument and do not change with the result:

- **A +0.13 residual quoting advantage** (verbatim rationales 0.5714,
  paraphrased 0.4399, n=49 on the quoted side). Partly structural. Any
  extractive-versus-generative comparison must report both.
- **The gold sentence sets needed furniture filtering** to be usable — 783 raw
  gold sentences were headings, table rows or bullets. Filtered improves the
  candidate and *lowers* every null, so it removed noise, but it drops 212 of
  727 rows. Both denominators reported.
- **The reference is one annotator's**, bounded by 0.714 on real documents.
- **`evidence_span` is excluded** from the primary figures by a written
  consequence rather than by evidence. It localises 2.7× better than the
  rationale (0.711 vs 0.263). That decision is live and was deferred to
  Phase 3's actual numbers, which now exist.

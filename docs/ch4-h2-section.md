# Chapter 4 §4.3.1 — Extract Quality Against the Synthetic and Real Corpora

Draft for the praxis text. Manuscript register, no repo jargon in the prose; file
paths appear only in footnote-style pointers. Consumes
[`2026-08-15-h2-narrowed-conclusion.md`](decisions/2026-08-15-h2-narrowed-conclusion.md).

---

## 4.3.1 Extract Quality

H2 held that a frozen extraction prompt produces high-fidelity credibility-factor
extractions, and specified four conditions: mean F1 above the protocol
threshold, per-factor F1 across the nineteen factors, reproduction on the
Morrison and aerospace regression cases, and a zero crash rate.

**All four are met. So is a function that reads nothing.**

### Detection at ceiling, and a null that reaches it

| split | bundles | mean F1 | null control | per-factor F1 | crashes |
|---|---|---|---|---|---|
| development | 30 | 0.9637 | **0.9637** | 1.000, all 19 | 0 |
| held-out test | 20 | 0.9544 | **0.9544** | 1.000, all 19 | 0 |

The null is the pack's fixed checklist of factor names, emitted without reading
the input. It ties the extractor to four decimal places on both splits, and its
per-factor score is also 1.000 across all nineteen — necessarily, since naming
every factor detects every factor.

Two features of the original criterion explain how a gate could be met without
discriminating. First, **its threshold was never numbered**: the protocol
requires F1 to exceed "the protocol threshold" without stating one, and a
condition of that form cannot fail. Second, the metric's only variance was a
defect. A prompt-routing error meant that every NASA-STD-7009B extraction was
run against the ASME V&V 40 prompt, so six of nineteen factors were never
requested and scored zero while the remaining thirteen scored one. Repairing the
extraction path removed the last source of variation the measure could observe.

The measure is therefore reported throughout this chapter beside its null, and
it gates nothing.[^detection]

### A replacement criterion, declared and not cleared

Detection having been shown non-discriminating, H2's support criterion was moved
to a conjunction over attribution — whether a rationale cites evidence belonging
to the factor it was filed under — and the groundedness triple. Six conditions
were given numeric thresholds, and those thresholds were committed to the record
before the measurement was performed.

Measured against six hand-annotated engineering papers:

| condition | required | observed | |
|---|---|---|---|
| margin over the run's own permutation null | ≥ 0.25, ≥ 3 sd | +0.044, 0.5 sd | **not met** |
| no null model reaches the candidate | absolute | 0.000 | met |
| below the inter-annotator agreement ceiling | 0.714 | 0.054 | met |
| measured on real documents | — | 6 papers, n = 56 | met |
| error profile published | — | published | met |
| groundedness reported as a triple | — | 1.000 / 0.000 / 0.000 | met |

**The conjunction is not satisfied.** The thresholds it failed against were
fixed in advance and were not revised afterwards — not when an initial
measurement was found to be circular, not when a defect in the scoring code was
corrected, and not when the sample was completed from three papers to six.

### Capability beneath the criterion

The attribution rule discriminates. Against the permutation null computed on
each run's own output, it achieves 8.6× chance on the synthetic corpus and 5.5×
on real documents, and no null model reaches it at any rationale length. What it
does not achieve is the margin the criterion required.

Both statements hold simultaneously, and the criterion's verdict governs.

### What the rationales contain

The most consequential single observation in this evaluation is not an accuracy
figure. Across the six real papers, every credibility factor received a
rationale — coverage 1.000 — and **not one of the ninety-six rationales contains
a checkable quantity**. Claim density is 0.000.

A representative rationale reads: *"The grid convergence study showed that the
discretization error was small."* The document in question reports the grid
convergence index numerically.

This is the reason groundedness is reported as three numbers. Coverage alone
describes complete success; groundedness alone, on an empty claim set, describes
total fabrication. Neither is what occurred. What occurred is that the extractor
produced a well-formed and unverifiable account of every factor.

### The limit on inference

Fifty-six factor-document pairs, six papers, three correct attributions, and a
single annotator whose same-sentence agreement with an independent second reader
is 0.714.

At this sample size, no result on the real corpus separates a mechanism from
noise. One paper contributed all three correct attributions; a second paper's
rate moved between two runs of the same extractor. The error-profile
adjudication rests on six disagreements.

**No modification to the extraction system addresses this.** The constraint is
the reference corpus, and it is relieved by two things only: additional
annotated documents, and a second annotator. The latter is the same work
requested independently as an encoder-independence check; one person following
the annotation protocol satisfies both.

The attribution result is accordingly reported as a characterization of
capability and not as a verdict on it.

### Summary of the H2 determination

H2 is **supported in a narrowed form**. The extractor identifies which
credibility factors a document addresses, at ceiling, on a measure a constant
also reaches — reported with that null throughout. The replacement criterion,
specified numerically in advance and measured on real documents, is **not
cleared**. Attribution capability is characterized at 5.5× chance on real
documents and bounded above by a sample too small to support a stronger claim.

[^detection]: Detection F1, its null controls, the routing defect and its
    correction are recorded in the evaluation harness under
    `studies/nasa-prompt-routing/`.

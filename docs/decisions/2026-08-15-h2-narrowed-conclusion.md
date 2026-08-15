# H2, concluded: what the evidence carries

**Date:** 2026-08-15
**Status:** the H2 conclusion, for Chapter 4
**Depends on:** [the amendment](2026-08-14-h2-gate-amendment.md),
[the replacement thresholds](2026-08-14-h2-replacement-thresholds.md),
[`studies/real-document-rescore/`](../../studies/real-document-rescore/FINDINGS.md)

---

## H2 as pre-registered

> A frozen extraction prompt produces high-fidelity credibility-factor
> extractions from documented CM&S evidence. H2 is supported if mean F1 across
> the stratified synthetic corpus exceeds the protocol threshold, per-factor F1
> holds across the 19 V&V 40 and NASA-STD-7009B credibility factors, results
> reproduce on the Morrison and aerospace regression cases, and the bundle-level
> crash rate is zero.

## The conclusion

**H2 is supported in a narrower form than it was written, and the narrowing is
what the evidence carries.**

Three claims, each with its instrument's limit attached:

### 1. Factor detection is at ceiling, on a measure that does not discriminate

Mean F1 **0.9637** development, **0.9544** held-out test. Per-factor F1
**1.000** for all nineteen factors on both splits. Zero crashes in 50 bundles.
All four regression cases clear.

**And `control_constant_list` — a function that emits the pack's fixed checklist
having read no input at all — scores identically. Delta +0.0000, to four decimal
places, on both splits.** Its per-factor F1 is also 1.000 across all nineteen,
by construction: it names every factor, so it detects every factor.

The pre-registered gate is therefore met and cannot discriminate. Two facts make
that concrete rather than rhetorical. The gate's mean-F1 condition **never
carried a number** — Chapter 3 and §3.6 both require F1 to "exceed the protocol
threshold" and neither states one, so a condition of that form cannot fail. And
the only variance the metric ever had was a defect: until a routing bug was
fixed, six of nineteen NASA factors were never asked about, scoring per-factor
F1 exactly 0.000 while the other thirteen scored exactly 1.000. Repairing the
extractor removed the last thing detection F1 could see.

**Claimed:** the extractor identifies which credibility factors a document
addresses, at ceiling, on this corpus.
**Not claimed:** that this demonstrates extraction quality. It does not, and the
null is reported beside it everywhere for that reason.

### 2. The replacement gate was declared with numbers, measured on real documents, and not cleared

Detection F1 having been shown non-discriminating, H2's support criterion moved
to an attribution/groundedness conjunction. Its six conditions were given
numeric thresholds and committed to disk **before** the measurement ran.

Measured on six hand-annotated real engineering papers:

| condition | threshold | measured | |
|---|---|---|---|
| margin over the run's own permutation null | ≥ 0.25 **and** ≥ 3 sd | **+0.044 / 0.5 sd** | **FAIL** |
| no null reaches the candidate, at any length | absolute | 0.0000 | pass |
| below the 0.714 real-document agreement ceiling | leakage check | 0.054 | pass |
| measured on the real corpus | — | six papers, n=56 | pass |
| FP/FN from the disagreement adjudication published | published | 6 rows, 2 of 3 gold-set gaps | pass, thin |
| groundedness as the triple, never alone | reported together | 1.000 / **0.000** / 0.000 | pass |

**H2 is not supported on attribution.** The conjunction failed on its first
condition, and the thresholds it failed against were on disk before it ran and
were not moved afterwards — not when a circular measurement was found, not when
a scorer bug was fixed, not when the sample was completed from three papers to
six.

### 3. Attribution capability exists, characterized, below the bar

| | candidate | permutation null | lift |
|---|---|---|---|
| synthetic | 0.4524 | 0.0526 | **8.6×** |
| real | 0.0536 | 0.0098 | **5.5×** |

The rule discriminates on real prose — 5.5× its own chance level, with no null
reaching it at any rationale length — and does not discriminate enough to rest a
hypothesis on. Both are true, and the gate's verdict is the operative one.

**Reported second, deliberately.** Leading with 5.5× would read as a rescue of a
failed gate.

### The finding underneath all three

On real documents, **claim density is 0.000**. Ninety-six rationales across six
papers, and not one contains a checkable number:

> *"The grid convergence study showed that the discretization error was small."*

Every factor received a rationale; none of them can be verified against the
document. That is a sufficient explanation for much of what is above, and it is
only visible because groundedness is reported as a triple — `coverage 1.000`
alone reads as complete success and `groundedness 0.000` alone reads as total
fabrication.

## The limit on inference, stated as a limit

**Fifty-six factor-document pairs. Six papers. Three correct attributions. One
annotator, whose same-sentence agreement with an independent second reader is
0.714.**

At that size, nothing on the real corpus distinguishes a mechanism from noise.
The disagreement adjudication is six rows. A single paper contributed all three
hits, and one paper's rate moved 1/12 to 0/12 between two runs of the same
extractor.

**No change to the tool moves this wall.** Not a better localiser, not a
different encoder, not a larger model. Only two things move it, and both are
corpus work rather than modelling: **more annotated documents**, and **a second
annotator**.

The second annotator is worth naming precisely, because it is the same work the
committee already asked for under a different heading. Encoder-independence and
annotation-agreement are one task: a second person following the protocol
resolves both.

**This is why the attribution result is a characterization and not a verdict.**
The gate's failure is a fact about the measurement as specified; the underlying
capability is estimated from a sample too small to bound.

## Why this shape is the defensible one

Every number in the conclusion survived an attempt to kill it.

- The **detection gate** survived a null that ties it — and is reported as
  non-discriminating *because* of that, not despite it.
- The **attribution rule** survived a shotgun of random sentences that used to
  beat the metric it replaced, 0.7527 against 0.6068, now 0.0505 against 0.4524.
- The **real-document figure** survived a circular first measurement that scored
  0.8545 — caught by its own leakage condition, which fired because a score
  above the human agreement ceiling is impossible for an honest instrument — and
  a scorer bug that silenced three of six papers.
- The **thresholds** did not move at any point in that sequence.

A cleared gate on that trail would have been a weaker artifact than this failure
is, because a gate that has never rejected anything is a description of intent.
This one rejected the hypothesis it was written to test, on the corpus that
matters, having first rejected two of its own measurements.

## What H2 does not claim

- Generalization to standards, domains or formats beyond the stratified corpus.
  Chapter 3 disclaimed this and it stands.
- That extraction quality is good or poor. Detection cannot say, and attribution
  says only that capability exceeds chance by a factor the sample cannot bound.
- That the replacement conjunction is the right criterion. It is *a* criterion,
  declared before measurement and failed. A third metric is not available: the
  sequence detection → attribution → something-else would be gate-shopping, and
  numbering the conjunction in advance was precisely so there is nowhere to move
  now.

# Decision Log: H2 support criterion — amended after the gate was passed

**Date:** 2026-08-14
**Author:** Vishnu Vettrivel
**Scope:** RQ2 / H2 only. H1 and H3 unaffected.
**Evidence:** [`studies/nasa-prompt-routing/FINDINGS.md`](../../studies/nasa-prompt-routing/FINDINGS.md),
[`studies/hosted-model-specificity/FINDINGS.md`](../../studies/hosted-model-specificity/FINDINGS.md),
[`studies/prompt-absence/FINDINGS.md`](../../studies/prompt-absence/FINDINGS.md)
**Run tag:** `routing-fix-v1-llama33-70b`, `meta-llama/Llama-3.3-70B-Instruct-Turbo`

## H2 as pre-registered

Quoted from the draft, Chapter 3:

> Hypothesis 2 (H2): A frozen extraction prompt produces high-fidelity
> credibility-factor extractions from documented CM&S evidence. H2 is supported
> if mean F1 across the stratified synthetic corpus exceeds the protocol
> threshold, per-factor F1 holds across the 19 V&V 40 and NASA-STD-7009B
> credibility factors, results reproduce on the Morrison and aerospace
> regression cases, and the bundle-level crash rate is zero.

## The result: the gate is passed, and so is the null

| condition | result | verdict |
|---|---|---|
| mean F1 exceeds the protocol threshold | dev **0.9637**, test **0.9544** | see the note below |
| per-factor F1 holds across the 19 factors | **1.000 for all nineteen**, both splits | PASS |
| reproduces on the Morrison and aerospace regression cases | Morrison COU1 **1.000**, COU2 **0.700**; aerospace COU1 **0.973** — all clear the harness's 0.70 | PASS |
| bundle-level crash rate is zero | **0** of 50 | PASS |

And the same table for `control_constant_list`, a function that emits the pack's
fixed checklist of factor names having read no input at all:

| | extractor | null control | delta |
|---|---|---|---|
| dev split | 0.9637 | 0.9637 | **+0.0000** |
| held-out test split | 0.9544 | 0.9544 | **+0.0000** |
| aerospace COU1 | 0.973 | 0.973 | **+0.000** |
| aerospace COU2 | 0.848 | 0.848 | **+0.000** |

**The null passes every condition the extractor passes, to four decimal places.**
Per-factor F1 is 1.000 across all nineteen for the constant too, by
construction: it names every factor in the pack, so it detects every factor in
the pack. Its crash rate is zero because it does not read anything. It
reproduces on the regression cases for the same reason it reproduces anywhere.

Discrimination is zero. Not small — zero.

## The amendment

**H2 is not rested on detection F1.** The support criterion moves to the
attribution / groundedness conjunction recorded in the plan of record, with
groundedness always stated as the triple `coverage / claim_density /
groundedness` and never as a lone number.

The posture matters and should not be softened in the write-up:

> We passed the pre-registered gate. We report the pass. We decline to rest H2
> on it, because a criterion that a null model also passes at ceiling is not
> measuring extraction.

This is not a gate retired under failure. Every condition was met, on the
held-out split, with a zero crash rate — the outcome the criterion was written
to detect was in hand. There is no gate-shopping reading available, because the
shopped-for result was already obtained and refused. What is being declined is
an empty win.

Both sets of numbers stay in every table, permanently: the original-gate figures
and the null beside them. The pairing is the disclosure. A reader who sees only
0.9544 has been told less than one who sees `0.9544 / 0.9544`.

## Three things that must be disclosed with it

### 1. "The protocol threshold" has no number

Chapter 3 says mean F1 must exceed "the protocol threshold". §3.6 says "F1 above
the protocol threshold" and "the required F1 thresholds". **No number is stated
in either place.** The §4.5 criterion table's H2 row carries a different set
entirely — completeness +30% / weakener density −40% / coverage +25% / semantic
coherence ≥0.9 — which are the §4.3.2 manual-versus-AI automation-lift
thresholds, not the corpus F1 threshold.

So of the four conditions, three are pre-registered with checkable criteria and
one is a dangling reference. The harness has always applied `F1 >= 0.70`, and
0.9637 / 0.9544 exceed any threshold anyone would plausibly have written.

**We are not going to write that number now.** Choosing it today, having seen
0.9637, is exactly the move the rest of this amendment exists to avoid, and it
would be indefensible in a way the amendment itself is not. It is recorded as a
pre-registration defect, disclosed, and left unnumbered. The replacement
conjunction carries its thresholds declared on disk *before* its measurement
runs, which is the correction.

### 2. The regression case that started this is not an H2 condition

The draft names "Morrison COU 1 and COU 2" and "the aerospace COU 1 case".
Aerospace **COU2** — the 0.593 gate failure that triggered the whole
investigation — is a harness case, not an H2 regression case. The harness was
stricter than the protocol. That is fine and it is how the routing bug was
found, but the "H2 regression case failing" framing was ours, never H2's.

For completeness: aerospace COU2 also passes post-fix, at 0.848, identical to
its control.

### 3. Morrison COU2 clears by zero margin

1.000, 0.700, 0.973 — and 0.700 against a 0.70 gate. It passes on the boundary,
single run, no seed control. Reported as passing, and reported as passing by
nothing.

## Why the original gate could not have shown this before now

Until 2026-08-14 the detection metric had one source of variance, and it was a
bug. `paths.extract_prompt()` took no pack name, so every NASA extraction was
run on the V&V 40 prompt and six of nineteen factors were never asked about.
Those six scored per-factor F1 exactly 0.000; the other thirteen scored exactly
1.000. Nothing else in the metric moved.

Fixing it removed the last thing detection F1 could see. Pre-fix the extractor
scored *below* its null (0.9035 vs 0.9637; 0.8909 vs 0.9544), which reads as a
weak extractor. Post-fix it scores exactly the null, which reads as what it is:
a metric with no discriminative content on this corpus.

The stronger evidence only became available by fixing the defect that was
depressing the score. That sequence is worth stating plainly, because the
alternative reading — that we went looking for a reason to abandon a metric we
were failing — is available only to someone who does not have the dates.

## What the amendment does not touch

- **H1 and H3.** Unchanged.
- **The absence-rule prompt change.** Its before/after comparison stands; both
  arms ran on the same (V&V 40) prompt, so nothing between them is confounded.
  Its denominator is corrected in `studies/prompt-absence/FINDINGS.md`.
- **The claim that extraction works.** Nothing here says the extractor is bad.
  It says detection F1 cannot tell us either way, and that the corpus is
  saturated: every factor is present in every bundle, so a metric asking "which
  factors are present" has nothing to measure. The remaining failures in the
  corpus are all `level_mismatch` — the extractor names the right factor and
  gets its level wrong — which is where any residual signal in this scorer
  lives.

## Open, carried forward

The replacement conjunction is **declared, not yet measured**. Its thresholds go
on disk before the real-document re-score, and until that run completes H2's
status is: original gate passed and disclosed as non-discriminating, replacement
criterion pre-registered and pending. A declared gate with a pending measurement
is a pre-registration in progress, and should be presented as one.

Separately, `studies/hosted-model-specificity/` records that the C3 hosted-model
migration cut checkable claims per corpus from 864 to 200 while coverage rose to
1.000 and groundedness held at 0.99 — the exact failure the groundedness-triple
rule exists to prevent, now with a measured before and after.

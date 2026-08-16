# Asking for figures produced fewer figures

Q2, run 2026-08-15 against the threshold committed in `DECLARATION.md` before
the arm ran. One declared revision, no second arm.

## Result

| | before | after | delta |
|---|---|---|---|
| **claim_density** | 0.1875 | **0.0854** | **−0.1021** |
| claims, total | 112 | **55** | −57 |
| rationales carrying a claim | 90 | 41 | −49 |
| groundedness | 0.9821 | **1.0000** | +0.0179 |
| ungrounded triage set | 1 | **0** | −1 |
| coverage | 1.0000 | 1.0000 | 0.0000 |
| distinctness | 0.8125 | 0.7708 | −0.0417 |
| mean_overall_f1 | 0.9637 | 0.9637 | 0.0000 |

Synthetic corpus, 30 dev bundles, 480 factor rows.

| threshold (declared, unmoved) | required | measured | |
|---|---|---|---|
| claim_density | ≥ 0.40 | **0.0854** | **FAIL** |
| groundedness | ≥ 0.98 | 1.0000 | pass |
| ungrounded triage set | ≤ 4 | 0 | pass |

**Real corpus: 0.000 before, 0.000 after.** Unmoved.

The arm's own kill criteria are all clean — `mean_overall_f1` did not move at
all, coverage held at 1.000, the triage set fell. It is not disqualified. It
simply failed, and failed in the wrong direction: **the intervention halved the
quantity it was written to raise.**

## The shape of the failure is the finding

**Groundedness rose to a perfect 1.000 and the ungrounded set went to zero,
while the claim pool halved.**

Quoted as a lone number, this arm reads as an unambiguous win: *groundedness
1.000, zero ungrounded claims, F1 unchanged.* It is the opposite of a win. Both
surviving numbers are ratios whose denominator was cut in half, and there is
nothing left to be wrong about because there is half as much being claimed.

This is the Goodhart pattern documented in `docs/metrics-spec-r6-u8.md` — written
the day before, from the hosted-model migration where coverage rose to 1.000 and
groundedness held at 0.990 while checkable claims fell 864 to 200. It reappeared
within twenty-four hours, on an intervention designed by the person who wrote
that warning, and the triple caught it exactly as specified.

## What the rationales actually did

The instruction reached the model and changed its behaviour. It did not produce
figures.

Before:

> *"The grid convergence study showed that the discretization error was small."*

After:

> *"A grid convergence study was performed to estimate the discretization error.
> The results showed that the velocity and hemolysis index predictions changed
> by less than 1% as the mesh size was refined."*

Longer, more specific, naming solvers (`ANSYS CFX v.15.0`), methods (Richardson
extrapolation) and references (Hariharan et al.). On the real corpus, still only
**2 of 96 rationales contain any number at all**.

## Hypothesis, marked as one and not tested

The instruction carried an anti-fabrication clause — *"where the document
genuinely reports no quantity for this factor, say what it does report and do
not invent one"* — and the model may have taken that as the safer branch. The
guard would then have suppressed more than the request elicited.

**Untested, and it stays untested.** Per the declaration and `evidence_span`'s
precedent: iterating a prompt until it clears a criterion is the criterion doing
no work. A second arm that removed the anti-fabrication clause would also be
removing the guard that makes a density gain trustworthy, which is a bad trade
even if it worked.

## The intervention, verbatim, so it is not re-proposed without its result

Replacing `rationale: <brief evidence summary, may span multiple lines>` in the
vv40 and nasa-7009b prompts:

```
rationale: <brief evidence summary, and it must carry the FIGURE. Where the
  document reports a quantity for this factor -- a GCI, a percentage, a residual,
  a sample count, a tolerance, a level -- state that quantity with its units.
  "The grid convergence study showed the discretization error was small" is
  incomplete: the study reports a number and the rationale must give it. Where
  the document genuinely reports no quantity for this factor, say what it does
  report and do not invent one. May span multiple lines.>
```

Anyone proposing to ask the extractor for figures must state that this was
tried and **halved claim density**, 0.1875 to 0.0854, on 480 factor rows.

## What this does to the surrounding questions

**The upstream-lever argument was sound and the lever did not move.** Condition
6 showed there is nothing in the rationales for a detector to detect, and fixing
the input before polishing detectors is dependency order rather than preference.
That reasoning stands. What has changed is that the input is not fixable by
instruction, so the detector work behind it is no longer queued behind an
incoming fix — it is queued behind a problem now measured as harder than it
looked.

**Q1's remaining discriminator gains weight.** The acceptance-criteria collapse
was already refuted as a prompt effect by the pack split — both packs collapsed
and only one carried the `"or implied"` clause. Claim density has now survived a
prompt change aimed directly at it. **Model or temperature is the standing
explanation, with two independent prompt-side refutations behind it**, and the
open discriminator is qwen against Llama on identical prompts at a fixed
temperature.

## Measurement note, and what it will look like when the fix lands

A defect was found and measured during this work, then filed rather than fixed:
`checkable_claims` discards `{0,1,2,3,4,5}` so a bare count cannot ground
against any document, and the same rule discards `"less than 1%"`, `"within
2%"`, `"below 5%"`. Impact is ~1% on both corpora — 8 of 800 synthetic rows, 1
of 96 real. It would move claim_density 0.1988 to 0.2087 and changes no
conclusion here. Not fixed under pressure: admitting more claims changes the
groundedness denominator too, so it needs its own before/after with the triage
set re-run.

**The connection to this study, recorded now so it is inherited rather than
rediscovered as a contradiction.** The intervention *did* elicit language the
metric structurally cannot see — *"changed by less than 1% as the mesh size was
refined"* is a real quantitative claim about the document, and the trivial-integer
rule discards it. So Q2's real-corpus rows are the clearest case the eventual
fix touches, and they are in that fix's scope.

**Expect 0.000 to become roughly 0.01, not roughly 0.40.** The ceiling on that
re-read is fixed by the fact that **94 of 96 rationales contain no number of any
kind**: only two rows can move, whatever the filter does. A re-read landing near
0.01 confirms this study's verdict rather than showing the fix underperforming,
and **Q2's verdict does not move** either way.

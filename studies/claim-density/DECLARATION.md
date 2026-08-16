# Q2: can claim density be recovered, and at what cost to groundedness?

Declared 2026-08-15, **before the intervention arm runs**. Same discipline as
`studies/evidence-span/`: one arm, declared, measured against a threshold that
was fixed beforehand and does not move.

## The problem

| | claim density |
|---|---|
| qwen3.5:4b, synthetic | 0.565 |
| Llama-3.3-70B, synthetic | 0.188 |
| **Llama-3.3-70B, six real papers** | **0.000** |

Ninety-six rationales across six engineering papers and not one checkable
number, in documents full of them. Every downstream mechanism — attribution,
the misfile signal, any localiser — is a detector, and a detector pointed at
prose with no document-specific content has nothing to key on. This is the
upstream lever.

## The threshold, as filed, unchanged

> An intervention counts as a fix only if claim_density reaches **≥ 0.40** with
> groundedness **≥ 0.98** and the ungrounded triage set staying at or below
> **4** items.

**The failure mode this guards is lifting density by fabricating figures.** A
rationale with more numbers has more that can be wrong; the triage set is what
catches an intervention that buys density with invention.

## One ambiguity in my own declaration, resolved before the run

The filed threshold does not say **which corpus** it applies to. That is a gap
in the original declaration, and resolving it after seeing a result would be
exactly the retroactive move this project has spent a month building discipline
against. Resolving it now, in advance:

**The threshold applies to the synthetic corpus**, because its third clause —
the ungrounded triage set at or below 4 — is a synthetic-corpus quantity (4
under qwen, 1 under Llama). A threshold cannot be evaluated on a corpus where
one of its clauses is undefined.

**And the real-corpus figures are reported beside it in every citation, with
the real number as the result where they disagree**, per the standing
denominator rule. Concretely: an intervention that reaches 0.40 on synthetic
while leaving real at 0.000 has **not** solved the problem this question was
asked about, and the write-up must say so in those words rather than reporting
a threshold pass.

## The intervention arm

A prompt change, so it gets `evidence_span`'s treatment: **one declared
revision, no iterating to a pass.**

The current prompts ask for `rationale: <brief evidence summary>`. The revision
asks, at the point of use, for the figure the rationale is about — a quantity,
with its units, copied from the document — and states that a rationale
describing a measurement without its value is incomplete.

Explicitly **not** doing: asking for "more detail", raising a temperature, or
adding examples of good rationales. The first is unmeasurable, the second is a
different experiment (Q1's remaining discriminator), and the third risks the
model reproducing the example's figures.

## Kill criteria for the arm itself

Beyond the threshold above, the arm is killed if:

1. `mean_overall_f1` moves more than **0.004**, the movement the absence-rule
   change produced and this corpus's demonstrated noise floor.
2. The ungrounded triage set exceeds **4**. This is the fabrication guard and it
   is the one that matters — density bought with invented figures is worse than
   no density, because an unverifiable rationale is at least honest about
   having nothing to check.
3. Coverage falls below **0.95**. An intervention that raises density by making
   the model decline to write rationales it cannot support has traded one
   failure for another, and coverage is what sees it.

## What no result licenses

A pass does not make this a general finding about extraction. It would establish
that the field is recoverable by instruction on this corpus with this model —
which is worth knowing, and is not the same as the field being fixed.

A failure does **not** license a second arm. Per `evidence_span`'s precedent and
the replacement-thresholds doc: iterating a prompt until it clears a criterion is
the criterion doing no work.

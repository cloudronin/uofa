# The misfile signal is too weak to ship, on the labels that exist today

> ## Governing rule: no rate without its denominator
>
> Graduated to a standing rule 2026-08-14, on its third appearance — after
> opportunities-versus-cards, after the two shotgun probes that disagreed
> (0.740 vs 0.9284, because one scored 447 rows and the other 376), and now
> after 0.247 against 0.605.
>
> **No rate is quoted without its measurement context: corpus, base rate, n.**
>
> **Paired synthetic and real measurements are inseparable in every citation**,
> and where they disagree the real number is the result, per the plan's standing
> rule.
>
> This governs every figure in this file and every figure derived from it. A
> rate detached from its denominator has repeatedly meant something different
> from what it appeared to mean, and each time the cost was paid downstream by
> someone reading it in good faith.

Phase 4, 2026-08-14. `dev/tools/scripts/misfile_signal.py`. Bundle-level 2-fold,
515 scored factor rows across 44 bundles, misfile base rate **0.175**.

## Result

| second opinion | precision | recall | fired |
|---|---|---|---|
| base rate (fire always) | 0.175 | 1.000 | 515 |
| prompt anchors | 0.194 | 0.533 | 247 |
| K6 trained, unmasked | 0.247 | 0.211 | 77 |
| **K6 trained, masked** | **0.247** | 0.200 | 73 |
| K6 masked + extra features | 0.274 | 0.222 | 73 |

**Nothing here is worth shipping.** At 0.247 precision the signal is wrong three
times in four. The plan's rule was that this ships as a confidence demotion
rather than a warning banner, because a red MISFILED label at two false alarms
in five is reviewer-hostile. At three in four it is not a demotion either — it
is noise attached to a number a reviewer is asked to trust.

The extra feature block moved precision **+0.027** against a **+0.05** floor
declared before it was measured. **Dropped**, as declared.

## Masking made no difference, and the mask works

The plan's central mechanism claim is that the second opinion must be denied the
label vocabulary, because the rationale is written in its filed factor's terms
and a reader given it as written confirms the filing 94% of the time. Masked and
unmasked score **identically here: 0.247 and 0.247**.

The mask is not a no-op. It rewrites 156 of 200 rationales and leaves a mean of
**0.01** factor-vocabulary tokens surviving:

    before:  Test conditions were controlled and the test samples met the
             discretization error target.
    after:     were controlled and the   met the   target.

So on this label set the vocabulary leak is not the binding constraint. That is
a finding about this measurement, not a refutation of the 94% result, which was
measured on a different question — what a second reader *names* the factor,
rather than whether a classifier can flag a misfile.

## This does not reproduce the plan's numbers, and it is not meant to

| | plan | here |
|---|---|---|
| base rate | 0.378 | **0.175** |
| prompt anchors | 0.412 | 0.194 |
| K6 unmasked | 0.581 | 0.247 |
| K6 masked | 0.605 | 0.247 |

**The base rates differ by more than two to one, so these are not the same
labelled set.** The plan's figures came from a pre-Phase-3 definition of
"misfiled" over ~545 labelled sentences. These come from the Phase 3
sentence-index rule: a row is misfiled when its rationale localises to a
sentence carrying another factor's evidence — the best definition available now
that Phase 3 exists, and the one the shipped signal would have to use.

So this neither reproduces nor refutes the plan's table. It measures the
mechanism the plan specifies, against labels the plan's numbers predate, and
finds it weak. Anyone citing 0.605 should know it does not survive the move to
Phase 3 labels; anyone citing 0.247 should know it was measured on a different
label definition than the 0.605.

## Ruling

**The misfile signal does not ship.** Not as a `Concern` — that needs 0.85 on
real documents and this is 0.247 on synthetic ones. Not as a confidence
demotion — 0.247 precision attached to a confidence figure would make the
confidence worse, and `keyless_extractor` establishes the house rule that the
confidence written is the measured figure for that route.

What was built stays: the comparison harness, the vocabulary mask, the
bundle-level folds, the optional-sklearn `available()` guard returning a precise
reason rather than degrading silently. The measurement is cheap to re-run when
the labels improve.

## What would change the answer

1. **Real documents.** Everything here is the synthetic corpus. The six
   hand-annotated papers are wired up (`real_attribution_reference.py`) and the
   misfile question has never been asked of them.
2. **A better misfile label.** The Phase 3 definition inherits Phase 3's
   limits — including a gold sentence set that needed furniture filtering, and a
   +0.13 residual quoting advantage. A label built on a noisy reference caps
   whatever is trained against it.
3. **`evidence_span`.** The signal reads the rationale, which is the text
   contaminated by its own label. The span localises 2.7× better (0.711 vs
   0.263) and is currently excluded from Phase 3 by a written consequence
   rather than by evidence. A second opinion reading spans instead of rationales
   is the obvious next mechanism and has not been tried.

## What stands, unchanged

**Do not build the anchor dictionary.** Fourth refusal, fourth task: 0.194
precision against a 0.175 base rate here, joining routing (0.367 against a 0.960
control), post-hoc re-attribution (0.059), and author-rationale recovery (0.522
against a 0.522 name-only null).

The signal must never become a weakener rule. Weakeners are semantic rules over
the package; this is an extraction-time signal about text that no longer exists
in it.

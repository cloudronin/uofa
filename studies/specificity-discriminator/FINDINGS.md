# INTERACTION

Run 2026-08-15 against `DECLARATION.md`, committed before the script existed.
Four arms, 30 dev bundles, identical committed prompts, the Q2 intervention
reverted and excluded.

## Verdict

**INTERACTION.** Neither model-attributed nor temperature-attributed by the rule
declared in advance.

| arm | distinct/filled | coverage | claim density | groundedness |
|---|---|---|---|---|
| **A qwen3.5:4b, default** | **1.0000** | 0.902 | **0.420** | 0.899 |
| B qwen3.5:4b, temp 0 | 0.8179 | 1.000 | 0.329 | 0.996 |
| C Llama-3.3-70B, default | 0.5623 | 1.000 | **0.044** | 1.000 |
| D Llama-3.3-70B, temp 0 | 0.4444 | 1.000 | 0.046 | 1.000 |

```
MODEL gap   |A−C| = 0.4377    separation needs ≥ 0.20   ✓
TEMP  qwen  |A−B| = 0.1821    close needs < 0.10        ✗
TEMP  llama |C−D| = 0.1179    close needs < 0.10        ✗
```

Model-attribution required the model gap ≥ 0.20 **and both** temperature gaps
< 0.10. The model gap clears comfortably; neither temperature gap falls inside
"close". Temperature-attribution required the reverse and is nowhere near.

**The verdict enters the record as the rule returned it.** The data
superficially resembles the clean model result, and reporting the awkward
verdict when it does is the entire reason verdicts are pre-declared. The
interaction outcome was named in `DECLARATION.md` before the run specifically so
it could not be reported as one of the clean two.

## Characterization, beneath the verdict

**The model effect is 2.4× the larger temperature effect** — 0.4377 against
0.1821 — and dwarfs both temperature gaps.

**Temperature moves the same direction in both models**: qwen −0.1821, llama
−0.1179. Temperature 0 *degrades* distinctness. Mechanically unsurprising —
lower temperature is more deterministic, so phrasing repeats.

**Temperature is therefore closed as a recovery path.** Lowering it hurts, and
raising it was never in the declared arms and is not licensed by them.

## The unasked finding: a measured tradeoff frontier

**The C3 migration traded checkable specificity for grounding and coverage.**
Qwen produces ten times the checkable content and one in ten of its claims does
not ground; llama grounds everything and produces almost nothing checkable.
**Neither model clears the conjunction.** This is a measured tradeoff frontier
with no current point on the right side of it — not a cheap win on a shelf.

Against Q2's bar, which is a conjunction — density ≥ 0.40 **and** groundedness
≥ 0.98 **and** triage ≤ 4:

| | density | groundedness | verdict |
|---|---|---|---|
| qwen default | **0.420** ✓ | **0.899** ✗ | fails, wide margin on grounding |
| llama default | 0.044 ✗ | 1.000 ✓ | fails, an order of magnitude on density |

Qwen's coverage is also 0.902 against llama's 1.000 — a further 10% cost.

### A correction, recorded because it is the standing example

The first report of this run said qwen *"already clears"* Q2's threshold, on the
strength of density 0.420 against a ≥0.40 bar. **That is false, and it is the
quote-one-clause error the triple exists to prevent** — made in the same message
that praised the triple for catching the same error elsewhere.

The bar is a conjunction. Reading one clause of it and calling the result a pass
is precisely what `coverage 1.000` alone or `groundedness 1.000` alone does. It
is now the worked example: the person most primed to avoid this error made it
within an hour of writing it up.

## Notes on the arms

- **Qwen's coverage is 0.902 at default and 1.000 at temp 0**, and its
  groundedness moves 0.899 → 0.996 in the same direction. Temperature 0 makes
  qwen safer and blander on every axis at once — fewer distinct criteria, fewer
  claims, but the claims it makes are almost all grounded.
- **Llama is flat across temperature on the triple** (density 0.044 → 0.046,
  groundedness 1.000 → 1.000). Only distinctness moves. Whatever produces its
  generic prose is not sampling.
- **Cost**: qwen 11,209 s and 6,405 s for the two local arms; llama 357 s and
  573 s hosted. Roughly 20× wall-clock for the local model, which is a real
  operational fact and not part of any threshold here.

## What this does not establish

- **Which model to use.** Neither clears the bar; see
  `studies/model-selection/` for the declared study that asks that question
  properly, across a wider candidate set and on both corpora.
- **That raising temperature would help.** Untested and not licensed. The arms
  were default and 0.
- **Anything about real documents.** All four arms are the synthetic dev split.
  Qwen's 0.420 density is synthetic-only and its real-document figure is
  unmeasured.

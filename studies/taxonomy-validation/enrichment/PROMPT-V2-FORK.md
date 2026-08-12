# Prompt v2: the fork, declared before the run

**Written 2026-08-11, before any v2 invocation.** Authorized after the corrected
v1 ground was reviewed.

The point of writing this first is that v2 has two genuinely different outcomes
and they imply opposite next moves. A fork chosen after seeing the numbers is not
a fork; it is a rationalization with a timestamp.

## What changed, and what did not

v2's prompt renders the property definitions **verbatim from the same source the
labeling sheet renders from** (`packs/mrm-nist/properties/P*.json`, enforced by
`tests/test_property_definitions_are_one_source.py`). Concretely it now asks for:

- **P7** — "ablations offered as controls" and "an explicit limitation statement
  doing this work". v1 named neither.
- **P6** — the sheet's section-level tie to an intended-use statement.
- **P2** — "variance across runs/seeds".

Plus three worked negatives closing the over-generous labels.

**Everything else is held constant**: same 116 cases, same corrected labels, same
temperature 0, same seed, same `max_tokens`, same two configs. Only
`prompt_sha256` moves, so a v1→v2 difference is attributable to the prompt alone.

## v1 baseline on corrected ground

| | P2 ff | P5 ff | P6 ff | P7 ff | P2 fc | P5 fc |
|---|---:|---:|---:|---:|---:|---:|
| `Llama-3.3-70B` | 18% | 75% | **100%** | **100%** | 11% | 33% |
| `DeepSeek-V4-Pro` | 58% | 95% | 71% | **100%** | 11% | 0% |

Bar: false-fire ≤10%, false-clear ≤5%, per property, no averaging.

## The expected signature, if drift was the cause

1. **P6 and P7 false-fire collapse.** These are the two properties whose forms
   the prompt never named. If drift explains them, asking for the right forms
   should move them by multiples, not margins.
2. **P2 recovers the `stefan-it` cluster.** The five-run mean±std family is the
   largest P2 positive cluster and v1's prompt omitted variance-across-seeds.
   P2 false-fire should fall materially on both configs.
3. **P5 barely moves.** Its drift was minor ("chance level shown in table"), so
   P5 is the near-control: a large P5 improvement would suggest something other
   than the declared change is driving the result, and would need explaining.
4. **False-clear does not blow up.** The worked negatives should hold it flat or
   improve it. A rise means the richer prompt is inviting invention, which trades
   one failure for the worse one.

## The branches

Read on **P6 and P7 false-fire**, both configs.

### Branch A — drift explained it. Both P6 and P7 fall below **25%**.

At least a 4× improvement from ~100%. The residual gap to the 10% bar is
ordinary prompt tuning, and it is authorized as such: iterate the combined
prompt, each iteration its own pinned row.

### Branch B — these properties resist one-shot extraction. Either stays at or above **50%**.

The prompt now carries the sheet's own text verbatim, so a persistent ~100% miss
is no longer a drift story. The finding is that P6 and P7 cannot be read
reliably by a single call extracting seven properties at once from a raw section
slice.

**The design answer is then NOT more prompt surgery on the combined prompt.**
It is one of:

- **per-property calls** — one focused invocation per property, which tests the
  instruction-overload hypothesis directly; or
- **judge-panel-only routing** — P6 and P7 never reach a rule via automated
  extraction, and their findings are produced by the A16.4 panel from the card
  text. This costs coverage and is honest about why.

Which of those two is a separate decision, taken after Branch B is reached.

### Between 25% and 50% — partial.

Drift was a real contributor and not sufficient. **One** per-property variant is
authorized as the discriminating test, pinned as its own row. If per-property
clears the bar, the finding is instruction overload. If it does not, Branch B.

## What falsifies the P2 sub-hypothesis

If P2 false-fire does **not** improve on either config, the variance-across-seeds
drift was not what was costing P2, and that specific claim in `CONSTRUCT-DRIFT.md`
is withdrawn regardless of what P6/P7 do. The three drifts were argued
independently and they fail independently.

## What this run cannot settle

v2's rates are still computed against **machine-drafted** labels and still
qualify an extractor rather than settle a rule. A16.4 finding validity,
adjudicated on fired findings, remains the settle authority. A v2 that clears
the bar unblocks the panel; it does not substitute for it.


---

# RESULT — Branch B, decisively (run 2026-08-12)

v2 ran on both configs. Prompt `faacd0f9cea62dfa` (v1 was `aecc9a6f32545163`);
same 116 cases, same corrected labels, same temperature, seed, `max_tokens`.
0 errors on both.

## False-fire, v1 → v2

| | P2 | P5 | P6 | P7 |
|---|---|---|---|---|
| `Llama-3.3-70B` | 18% → **18%** | 75% → 80% | 100% → 86% | 100% → **100%** |
| `DeepSeek-V4-Pro` | 58% → 55% | 95% → 95% | 71% → **86%** | 100% → 71% |

**Branch A required both P6 and P7 below 25%. The maximum is 100%.**
**Branch B required either at or above 50%. Every one of the four is.**

## The prompt carried the sheet's own text, and it did not help

This is the finding, and it is a negative one:

- **P7 did not move on Llama at all** — 100% before and after asking, in the
  sheet's own words, for ablations offered as controls and limitation statements
  doing this work. DeepSeek improved to 71%, still 7× the bar.
- **P6 got WORSE on DeepSeek** (71% → 86%) while improving on Llama
  (100% → 86%). Both land at 86%. A change that moves two families in opposite
  directions to the same place is not a fix.
- **P5 barely moved** (75→80, 95→95), exactly as predicted for the near-control.
  That the control behaved as declared is what licenses reading the rest.
- **False-clear stayed flat** (11%/11%, 33%/33%, 0%/0%). The richer prompt did
  not invite invention, so nothing was traded.

## The P2 sub-hypothesis is FALSIFIED

Declared in advance: *"If P2 false-fire does not improve on either config, the
variance-across-seeds drift was not what was costing P2, and that specific claim
in `CONSTRUCT-DRIFT.md` is withdrawn regardless of what P6/P7 do."*

P2 went 18% → 18% and 58% → 55%. **Withdrawn.** The prompt now explicitly asks
for "variance across runs/seeds" and the `stefan-it` five-run cluster is still
being missed at the same rate, so whatever costs P2, it is not that omission.

## What survives from the drift finding

The drift was **real and documented** — the two artifacts did define three
properties differently, and that remains true and worth having fixed. What is
now withdrawn is the *causal* claim: fixing the drift did not fix the extraction.

Drift was a confound that made the v1 numbers uninterpretable. It was not the
mechanism. Both things can be true, and the honest record says so rather than
retiring one finding to protect the other.

## Consequence, per the declared branch

**No further prompt surgery on the combined prompt.** The design answer is one of:

- **per-property calls** — one focused invocation per property, testing the
  instruction-overload hypothesis directly; or
- **judge-panel-only routing** — P6 and P7 never reach a rule through automated
  extraction, and their findings come from the A16.4 panel reading card text.
  This costs coverage and is honest about why.

That choice is a separate decision and is **not** taken here.

One observation bearing on it: P6 and P7 are the two properties whose definitions
are *relational* — a claimed COU requires a stated connection between an
evaluation and a use; a confound control requires a comparison doing work. P2 and
P5 are lexical by comparison: a ± or a chance value is present or it is not. If
one-shot extraction is what fails, the failure tracks relational reading rather
than instruction count, and per-property calls would help less than the
instruction-overload framing predicts. That is a hypothesis, not a finding, and
the per-property variant is what would test it.

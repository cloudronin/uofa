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

---

# Per-property variant: the fork, declared 2026-08-12 before any call

All four properties, both configs, one focused invocation per property. P2 and P5
are included as **lexical controls**, not as targets: if per-property calls fix
everything, the mechanism was instruction overload; if the lexical pair clears
while the relational pair stays high, that is a measured boundary of single-pass
extraction rather than a failure.

## Revised by the structure split (`STRUCTURE-SPLIT.md`), which ran first

Three things changed before this fork was written, and it is built around them:

1. **P2 table-borne already clears on Llama (8%, n=24).** Aggregate P2 is
   therefore not a usable signal — a variant could "improve P2" by moving a cell
   that already passes. **P2 is read on its PROSE cell only** (n=9).
2. **P5 is not interpretable.** 13 of its 15 prose positives are one house
   sentence stating no baseline value, arguably failing the sheet's own Present
   bar. P5 is **reported but excluded from branch selection** until its labels
   are reviewed.
3. **P6/P7 are prose-only (0 table positives).** "Relational" and "prose-borne"
   are perfectly confounded for them and this variant cannot separate the two.
   Both branches below are worded so neither claims to.

## Baseline to beat (v2 prompt, one call for all seven properties)

| | P2 prose | P6 | P7 |
|---|---:|---:|---:|
| `Llama-3.3-70B` | 44% | 86% | 100% |
| `DeepSeek-V4-Pro` | 67% | 86% | 71% |

Bar unchanged: false-fire ≤10%, false-clear ≤5%, per property.

## Branches, read on P2-prose against P6/P7

### Branch C — instruction overload. P2-prose clears (≤10%) AND P6/P7 both fall below 25%.

Focus was the constraint. The combined prompt was asking for too much at once,
and the fix is architectural: per-property extraction becomes the shipped path,
costing 4–7× the calls. Its economics get their own decision.

### Branch D — a boundary of single-pass extraction. P2-prose improves materially (≥15 points) while P6/P7 stay at or above 50%.

**This is the FAccT-grade outcome if it holds.** Focus helps where the evidence
is lexical — a `±` or a chance value is present in the sentence or it is not —
and does not help where the property is a *relation* the reader must construct:
a claimed COU needs a stated connection between an evaluation and a use; a
confound control needs a comparison doing work.

Stated as the finding it would be: **lexical evidence properties are extractable
by single-pass reading; relational ones require adjudication-grade reading.**

With the confound named in the same breath: P6/P7 are also the only prose-only
properties, so "relational" and "prose-borne" cannot be separated on this
stratum, and the claim must be written to say so.

### Branch E — focus changes nothing. P2-prose does not improve materially and P6/P7 stay high.

Neither overload nor relation-versus-lexical. The remaining candidates are prose
reading itself, or the labels. **The next step would be a label review of the
P2-prose and P6/P7 positives** on the footing the P6/P7 seven already had — not
another extraction variant.

### Mixed — P2-prose clears but one of P6/P7 lands 25–50%.

Report as partial. No further variant is authorized without a new fork.

## Pre-committed consequence (also written into A16.4)

**If the per-property run fails the relational pair — Branch D or E — then P6 and
P7 findings on the prose path become panel-confirmed-only.** Extraction may
propose; no `W-EV-COU-05` or `W-EV-CAP-06` finding renders on any card without
A16.4 panel confirmation.

Written before the result exists so it cannot be invented to fit the number. It
is also the conservative design regardless: false-fire on these two is the
maximum-reputation-damage direction — a public accusation that a publisher
omitted something they stated — so panel-gating them is right even if the variant
partially recovers.

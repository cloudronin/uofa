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

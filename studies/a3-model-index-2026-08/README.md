# A3: does HF `model-index` cover enough to be the primary eval detector?

**Answer: no. 4 of 100. It is a fallback, not the primary path.**

Addendum v0.1 §A3 asks the detector to distinguish "no reported evaluation" from
"evaluation present but not analysed", and carries an investigation item: the HF
`model-index` metadata block is structured and free, so check its coverage before
investing in a markdown-pattern tier — the regex path *may* be the fallback.

Measured before writing any detector code, because the plan's expectation and the
answer point in opposite directions.

| | |
|---|---|
| Population | most-downloaded text-generation models on the HF hub |
| Sample | 100 |
| Measured | 2026-08-10 |
| `model-index` present | **4 (4.0%)** |
| …carrying `results[]` | 4 |

Re-derive: `python studies/a3-model-index-2026-08/measure_model_index.py`

## What this settles

**The structured path cannot be the primary detector.** At 4% coverage, keying
the "is there reported evaluation here?" question on `model-index` would answer
"no evaluation reported" for 96% of models, most of which do report benchmark
results — in prose, in a markdown table, in a section the metadata never saw.
That is not a cheap detector, it is a detector that is wrong almost always, and
wrong in the direction that matters: a confident **N/A over evidence that
exists** is exactly the failure A3 was written to prevent.

The 74 distinct metric types the sample does carry reinforce it. They are
dominated by retrieval metrics (`map_at_1`, `map_at_10`, …, 51 occurrences each)
from a single embedding model — not the benchmark-eval reporting the Group-B
layer assesses. So even the 4% is not 4% of the *relevant* signal.

## The detector decision this justifies

1. **Markdown/section scanning is the primary tier**, not the fallback. The
   pattern list lives in pack data, not code (A3), so it moves without a release.
2. **`model-index` is a corroborating tier**, checked first because it is free
   and structured: when present it is a positive signal with no parsing risk.
   Absence proves nothing and must never be read as "no evaluation reported".
3. **The detector stays presence-only.** It picks which honest sentence the
   readout prints and emits no `ValidationResult` nodes. It cannot upgrade a
   heuristic run into an assessed one, and no measurement here changes that.

## What would change the answer

Coverage is a property of hub conventions, not of this code. If HF begins
populating `model-index` broadly, re-run this and promote the structured tier.
Record a new dated study rather than editing this one — a changed result is a
finding about the hub, not a number to overwrite.

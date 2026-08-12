# Table-borne vs prose-borne evidence — recomputed, no new runs

**Run 2026-08-12**, before authorizing the per-property variant, from the
existing per-case results. `split_by_structure.py`.

A case is table-borne when the line carrying its lure is a markdown table row
(≥2 unescaped pipes) — a mechanical test on the line the evidence sits on.

## Positive-class structure (the miss denominator)

| Property | table | prose |
|---|---:|---:|
| P2 uncertainty | **24** | 9 |
| P5 null baseline | 5 | 15 |
| P6 claimed COU | **0** | 7 |
| P7 confound control | **0** | 7 |

## Miss rate by structure (v2 prompt)

| | P2 table | P2 prose | P5 table | P5 prose | P6 prose | P7 prose |
|---|---:|---:|---:|---:|---:|---:|
| `Llama-3.3-70B` | **8%** | 44% | 20% | 100% | 86% | 100% |
| `DeepSeek-V4-Pro` | 50% | 67% | 80% | 100% | 86% | 71% |

## The one cell that clears the bar

**Llama on table-borne P2: 2/24 = 8%, under the 10% false-fire bar.** On n=24,
the largest single structure×property cell in the stratum.

That is the first thing all session to clear anything, and it is the opposite of
the hypothesis this analysis was written to test. Tables were suspected as the
hard case, because P2's largest positive family (`stefan-it`, five run columns
plus `mean ± std`) is table-structured. Tables are the **easy** case. A
`0.5409 ± 0.0222` in a cell is read reliably; the same claim in a sentence is not.

**So the table-preprocessing fix is not indicated.** The structure that was
suspected of needing special handling is the structure that already works.

## What this does NOT establish, and cannot

**P6 and P7 have zero table-borne positives.** All 14 of their positives are
prose. So for exactly the two properties in question, "relational" and
"prose-borne" are **perfectly confounded**, and no re-analysis of observational
data can separate them — there is no table-borne claimed-COU to compare against,
here or plausibly anywhere. A context of use is never a table cell.

The relational hypothesis therefore survives this test without being supported by
it. The per-property variant is still the discriminating measurement, and it
should be read knowing that a P6/P7 result confounds two mechanisms.

## A label-quality finding that arrived instead

**P5's 100% prose miss is not clean evidence about prose reading.** 13 of its 15
prose positives are one organization's house sentence:

> "The scores for each task is normalised to account for **baseline performance
> due to random chance**."

That names chance and **states no baseline value**. The sheet's Present examples
all carry one (`random baseline: 25%`, `majority-class: 51%`), and its Absent
clause treats *"significantly above chance"* with no stated value as `unclear` at
best. `rmtariq` is the same shape: *"vs Random Baseline: +66% improvement"* — a
relative delta, no baseline.

So P5's positive class is 20, of which 13 are a sentence that arguably fails the
sheet's own Present bar, and the extractor's blank on them is defensible. This is
the same pattern as the seven adjudicated flips, in a property nobody had
re-read.

**Recommended, not done here:** a P5 label review on the same footing as the P6/P7
one — the 13 SEA-LION-family rows plus `rmtariq`, adjudicated against the sheet's
value requirement. Until then P5's rates should be read as provisional in a way
P2's are not. Doing it now would mean flipping labels to fit a hypothesis mid-run,
which is the move this study exists to avoid.

## What the per-property fork must account for

1. **P2 table already clears on Llama.** The variant cannot be judged on
   aggregate P2 — it must be judged on the cells that do not clear.
2. **P5 is not interpretable** until its labels are reviewed; its numbers should
   be reported but not used to select a branch.
3. **P6/P7 carry a confound the variant cannot remove.** A per-property call that
   fails on them is consistent with both "relational reading is hard" and "prose
   reading is hard", and the fork must not claim to distinguish them.

The honest summary: the free analysis dissolved the table hypothesis, could not
separate the relational one, and turned up a label-quality problem in a third
property. Two of those three were not what it was looking for.

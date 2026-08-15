# The hosted model writes the same acceptance criteria in every document

Found 2026-08-14 while re-running the corpus for
`studies/nasa-prompt-routing/`. Not caused by that fix, and not caused by the
absence-rule prompt change. It arrived with the C3 migration from the local
`ollama/qwen3.5:4b` to `meta-llama/Llama-3.3-70B-Instruct-Turbo` via Together,
and nothing noticed for a week.

## The number

`acceptance_criteria`, distinct values as a fraction of filled values, over the
full 50-bundle corpus (30 dev + 20 held-out test):

| run | model | rows | filled | distinct | distinct/filled |
|---|---|---|---|---|---|
| frozen 2026-08-07 | qwen3.5:4b (local) | 800 | 788 | 738 | **0.937** |
| absence-rule-v1, 2026-08-14 | Llama-3.3-70B (hosted) | 650 | 636 | 246 | **0.387** |
| routing-fix-v1, 2026-08-14 | Llama-3.3-70B (hosted) | 800 | 774 | 343 | **0.443** |

Restricted to the thirteen V&V 40 factors, which all three runs share, so the
missing NASA block cannot account for it: 0.939, 0.387, 0.433.

The routing fix moved this *up* slightly. The drop is the model.

## What it is, precisely

It is **not** within-document repetition. Every run, every model, every bundle:
distinct criteria as a fraction of filled criteria **within a single bundle is
1.000**. No model ever writes the same criterion twice in one assessment.

It is repetition **across** documents. Llama writes a generic criterion for
"Discretization error" and writes approximately that same criterion in every
assessment it produces, where qwen wrote one keyed to the document in front of
it. Roughly three of every five criteria in the corpus are now a duplicate of a
criterion in some other bundle.

That distinction matters because the per-factor-fields report checks the wrong
one. It prints

    acceptance_criteria: 13/13 (100%)  13 distinct, mean 87 chars

for a single bundle, and that line is true and will stay true. Within-bundle
distinctness cannot see this failure. The corpus-wide count is what sees it, and
the only assertion checking it is
`test_per_factor_fields.py::test_the_synthetic_corpus_shortfall_rate`, whose
`acceptance_criteria_distinct > 700` would now fail at 343 if it read the live
run. It reads the committed baseline instead, so it passes.

Its own comment says what the number means, and it was right:

> Not boilerplate: if this collapses, the column stopped being extracted and
> started being echoed from the template.

## Why it matters beyond a metric

`acceptance_criteria` is the field a reviewer reads to know *what would have to
be true* for a factor to pass at its level. A criterion copied across every
assessment is not a finding about this model and this context of use — it is the
template talking. It also drives `W-AR-01`, which fires per factor on an
unpopulated criterion; a populated-but-generic criterion satisfies that rule
while carrying no more information than a blank one would.

## What was NOT done, deliberately

**The committed baseline was not regenerated.** `tests/fixtures/extract_corpus/extracted_rows.json`
still holds the qwen-era rows from `00e70177` (2026-08-07). Regenerating it from
the current run would make
`test_the_committed_rows_still_match_the_extraction_output` pass and would
delete the only on-disk record of what this extraction looked like before the
model swap. The failing test is the correct signal, not the problem.

Consequence to be aware of: with today's `extracted.xlsx` on disk, that drift
test fails locally. It skips in CI, where the xlsx are gitignored and absent.
The drift arrived with the morning `absence-rule-v1` run, before any change in
this workstream.

## Open

1. **Cause unknown.** Prompt wording, model, or temperature. The extract prompts
   ask for "the explicit level-passing criterion stated or implied in the
   narrative", and "or implied" may be enough licence for a generic answer from
   a model that is happy to give one.
2. **Not scored against gold.** This measures self-similarity across bundles,
   not correctness. A criterion can be generic and still right. What is
   established is that the field stopped varying with the document, which is a
   fact about the field regardless of how it is graded.
3. **`docs/credibility-inspector.md` §7** says extraction quality is
   "model-dependent, and the dependence is sharp". This is the concrete instance
   and the page does not yet name it.

# The hosted model writes fluent prose where the local model wrote checkable prose

Found 2026-08-14 while re-running the corpus for
`studies/nasa-prompt-routing/`. Not caused by that fix, and not caused by the
absence-rule prompt change. It arrived with the C3 migration from the local
`ollama/qwen3.5:4b` to `meta-llama/Llama-3.3-70B-Instruct-Turbo` via Together,
a week earlier, and nothing noticed.

Both row sets are committed here so the comparison survives any later
regeneration of the working baseline:

- `extracted_rows_2026-08-07_qwen35-4b.json` — the pre-swap corpus, 50 bundles,
  800 rows, as frozen in `00e70177`
- `extracted_rows_2026-08-14_llama33-70b.json` — the same corpus after the swap
  and after the extract-prompt routing fix

`tests/fixtures/extract_corpus/extracted_rows.json` is the *working* baseline
and tracks the current pipeline. It is regenerated when the pipeline changes, so
the drift check keeps working. Nothing here depends on it.

## Two measurements, one behaviour

### Rationales carry a quarter as many checkable claims

| | qwen3.5:4b | Llama-3.3-70B |
|---|---|---|
| factors with a rationale | 779 / 800 | **800 / 800** |
| rationales containing a checkable claim | 440 | **159** |
| checkable claims, total | 864 | **200** |
| claims grounded | 859 | 198 |
| **coverage** | 0.974 | **1.000** |
| **claim_density** | 0.565 | **0.199** |
| **groundedness** | 0.994 | **0.990** |

**Read the triple, and the reason for the rule is on the page.** Coverage went
*up* to a perfect 1.000. Groundedness barely moved, 0.994 to 0.990. Reported
alone, either one says the migration was a clean improvement. It was not: the
number of verifiable claims in the corpus fell by 77%, from 864 to 200. Every
factor now gets a rationale and four in five of those rationales contain nothing
a checker can test.

This is the concrete before/after for the amended gate's requirement that
groundedness is stated as coverage / claim_density / groundedness and never as a
lone number. A lone 0.990 here is not merely uninformative — it is actively
misleading about the direction of the change.

### Acceptance criteria stopped varying with the document

`acceptance_criteria`, distinct values as a fraction of filled values, across
the whole 50-bundle corpus:

| run | model | rows | filled | distinct | distinct/filled |
|---|---|---|---|---|---|
| 2026-08-07 | qwen3.5:4b (local) | 800 | 788 | 738 | **0.937** |
| absence-rule-v1 | Llama-3.3-70B (hosted) | 650 | 636 | 246 | **0.387** |
| routing-fix-v1 | Llama-3.3-70B (hosted) | 800 | 774 | 343 | **0.443** |

Restricted to the thirteen V&V 40 factors, which all three runs share, so the
missing NASA block cannot account for it: 0.939, 0.387, 0.433. The routing fix
moved this slightly *up*. The drop is the model.

It is **not** within-document repetition. Every run, every model, every bundle:
distinct criteria as a fraction of filled criteria **within a single bundle is
1.000**. No model writes the same criterion twice in one assessment. It is
repetition *across* documents — a generic criterion for "Discretization error"
reused in every assessment, where qwen wrote one keyed to the document in front
of it.

That distinction matters because the per-factor-fields report checks the wrong
one. It prints `acceptance_criteria: 13/13 (100%) 13 distinct, mean 87 chars`
per bundle, and that line is true and will stay true. Only the corpus-wide count
sees this.

## The single behaviour underneath

Both measurements say the same thing from different angles: **the hosted model
writes fluent, generic prose where the local model wrote specific, checkable
prose.** Rationales lost their numbers; criteria lost their document.

That is a plausible consequence of a larger instruction-following model asked
for "the explicit level-passing criterion stated or implied in the narrative" —
"or implied" is licence to produce a well-formed general answer, and a stronger
model takes it more consistently. Plausible is not measured. See the open
questions.

## Declared questions and thresholds

Recorded before the investigation, so the answer is not fitted to it.

**Q1 — Is the criteria collapse the prompt, the model, or the temperature?**
Arms: shipped prompt vs. one that strikes "or implied" and requires the
criterion to quote or paraphrase a stated threshold; Llama vs. qwen on identical
prompts; temperature 0 vs. current.
*Threshold:* the prompt arm is the cause if striking "or implied" recovers
corpus-wide distinct/filled to **>= 0.70** on the 13 shared factors. Below that,
the cause is the model and the fix is not a prompt edit.

**Q2 — Is claim_density recoverable, and at what cost to groundedness?**
A rationale with more numbers has more that can be wrong. Any change that lifts
claim_density must report groundedness beside it.
*Threshold:* an intervention counts as a fix only if claim_density reaches
**>= 0.40** with groundedness **>= 0.98** and the ungrounded triage set staying
at or below **4** items. Lifting density by fabricating figures is the failure
mode, and the triage set is what catches it.

**Q3 — Is the coverage/groundedness improvement Goodhart-shaped?**
Coverage rose to 1.000 and groundedness held at 0.990 **while the population
being measured fell from 864 checkable claims to 200**. Both surviving numbers
are ratios whose denominator shrank by three quarters. The metrics may have
improved *because* the population shrank — fewer claims means fewer chances to
be ungrounded, and every factor getting a rationale is easier when the
rationales assert less.
*Threshold:* none — this is a framing that must be stated wherever the triple is
reported, not a quantity to clear. Declared here so it is read in the record
rather than discovered by a reviewer, which is the difference between a
disclosure and a finding against us. The ungrounded triage set is the concrete
instance: it fell 4 to 1, which reads as improvement until divided — 4/864 is
0.46%, 1/200 is 0.50%, and the artefact rate did not move at all.

**Q4 — Are generic criteria actually wrong?**
Both measurements are self-similarity and countability, not correctness. A
criterion can be generic and still right; a rationale can be claim-free and
still true. Neither is scored against gold here.
*Threshold:* none declared. This needs a gold set for acceptance criteria that
does not exist yet, and inventing one to close the question would be the
mistake. Stated as unmeasured, per AGENTS.md §13.

## What this does not license

None of this reopens detection F1. That metric is disqualified separately and
for a different reason — the extractor and a constant that reads nothing score
identically on it. See `studies/nasa-prompt-routing/FINDINGS.md`.

Nor is it an argument to revert to qwen. qwen was measured worse on other axes
and the migration bought hosted availability, which was C3's purpose. What is
established is that the swap had a cost on two axes nobody was watching, and
that the numbers being watched — coverage, groundedness, within-bundle
distinctness — all moved the reassuring way while it happened.

## Related

- `docs/credibility-inspector.md` §7 says extraction quality is
  "model-dependent, and the dependence is sharp". This is the concrete instance.
- `tests/test_groundedness.py::test_llm_baseline_on_the_shipped_corpus` and
  `tests/test_per_factor_fields.py::test_the_synthetic_corpus_shortfall_rate`
  pin the current values, with the qwen figures recorded beside them.

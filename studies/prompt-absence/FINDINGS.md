# Scoring the absence-rule prompt change

Run 2026-08-14. Corpus `tests/fixtures/extract_corpus/dev` (30 bundles, 480
factors), extractor `meta-llama/Llama-3.3-70B-Instruct-Turbo` via Together.
Both arms scored with `dev/tools/scripts/score_extraction_batch.py`; the only
difference between them is the three extract prompts, restored from
`3f32bbf5^` for the BEFORE arm.

Raw results: `dev-before.json`, `dev-after.json`.

## What this corpus can and cannot test

**It cannot test the change.** The absence rule governs `not-assessed`: the
status a factor should carry when the corpus contains no evidence for it. This
corpus has no `not-assessed` ground truth. Its statuses are `assessed` (447)
and `not_applicable` (33), and those are different claims -- *does not apply to
this context of use* is not *no evidence was found*.

The direct evidence for the fix remains the hand-built probe in the C3 spike: a
shopping list as the evidence corpus, which returned 13/13 `assessed` before and
13/13 `not-assessed` after. That is four cases, and it stays the only thing that
exercises the rule.

**It can test two things worth knowing**, which is why it was run: whether the
new rule degrades extraction where evidence IS present, and whether it bleeds
into genuinely not-applicable factors.

## Result

Headline metric unchanged:

| | mean overall F1 | groundedness | claims grounded |
|---|---|---|---|
| before | 0.9035 | 0.989 | 91/92 |
| after | 0.9035 | 1.000 | 107/107 |

Status confusion, all 480 factors:

| expected -> extracted | before | after |
|---|---|---|
| `assessed` -> `assessed` | 376 | 374 |
| `assessed` -> *(none)* | 71 | 71 |
| `not_applicable` -> *(none)* | 19 | 19 |
| `not_applicable` -> `assessed` | **14** | **12** |
| `assessed` -> `not-assessed` | 0 | **2** |
| `not_applicable` -> `not-assessed` | 0 | **2** |

**Before the change the model never emitted `not-assessed` once** in 480
factors. That is the clearest signal the fix did what it was for: it made the
status reachable at all, rather than nudging a distribution.

Raw status accuracy falls 376/480 to 374/480 (-0.4pp), because the scorer counts
both new mismatch classes as wrong -- correctly. The error *profile* moved the
safer way for a credibility tool:

- over-claiming fell: `not_applicable -> assessed` 14 -> 12. Those are factors
  that do not apply being reported as evidenced.
- under-claiming appeared: 2 genuinely assessed factors marked `not-assessed`.

Trading two over-claims for two under-claims is the right direction here. A tool
whose purpose is to report gaps should fail toward naming a gap that is not
there, not toward hiding one that is.

## Caveats

- **n=1 per arm, 4 factors of difference.** Not statistically meaningful.
  Directionally consistent with the probe; not a substitute for it.
- Single temperature-0 run; no seed control across arms.
- Dev split only. The test split is sentinel-locked (`.test_set_lock`,
  `--allow-test`) and was deliberately not touched.

## Separate finding, pre-existing — ANSWERED, see studies/nasa-prompt-routing/

**71 of 480 factors (15%) come back with no status at all**, identically in both
arms, plus 19 more among the not-applicable ones. 90 of 480 factors carry no
status. This predates the change and is unaffected by it, but it is a real gap
in the extract path: the status column is the field the completeness math and
the headline are computed from. Worth its own investigation.

**Investigated 2026-08-14.** Those 90 are the six NASA-STD-7009B factors across
the 15 nasa bundles — six times fifteen, splitting 71 `assessed` / 19
`not_applicable`, which is this table's two numbers exactly. They carried no
status because they had no row: `paths.extract_prompt()` took no pack name and
returned the V&V 40 prompt for every pack, so every NASA extraction was asked
about 13 factors and never about the other six. Fixed; the row count goes 390 to
480 with none missing.

**What that does to this study.** The before/after comparison stands — both arms
ran on the V&V 40 prompt, so nothing between them is confounded by the routing
bug. But the denominator is not what it says. The 480 is 390 rows the extractor
was actually asked to produce plus 90 it was never asked about, so every rate
quoted here over 480 is diluted by a fifth, and "the model never emitted
`not-assessed` once in 480 factors" is properly "in 390 factors". The headline
mean F1 of 0.9035 is likewise a mixed figure: unchanged across the arms, but on
the nasa half it was measuring the missing block rather than extraction quality
(nasa 0.8385 before the routing fix, 0.9588 after; vv40 0.9686 either way).

## Cost and time

30 bundles per arm. Before 14.0 min (28.0 s/bundle), after 10.5 min
(21.0 s/bundle). Roughly $0.20 per arm at the measured per-run estimate.

## Reproducing

`run_extraction` previously spoke only the legacy `--model` flag, which cannot
reach a hosted provider: the legacy resolver splits on `/` and looks the prefix
up in `ALLOWED_BACKENDS`, so `together_ai/...` silently falls back to Ollama and
`openai/...` would go to OpenAI, there being nowhere to put a base_url. It now
also accepts `backend@base_url|model`:

```bash
TOGETHER_API_KEY=... UOFA_OPENAI_COMPATIBLE_API_KEY=... PYTHONPATH=src \
python dev/tools/scripts/score_extraction_batch.py \
  --corpus tests/fixtures/extract_corpus/dev \
  --model 'openai-compatible@https://api.together.xyz/v1|meta-llama/Llama-3.3-70B-Instruct-Turbo' \
  --prompt-version absence-rule-after \
  --output /tmp/after.json
```

The legacy form (`--model ollama/qwen3.5:4b`) is unchanged.

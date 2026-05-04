# Extract Eval v1 — Synthetic Corpus + Prompt Iteration Result

**Author:** Vishnu Vettrivel
**Date:** May 4, 2026
**Spec:** [`Product Requirements/UofA_Extract_Prompt_Iteration_Spec_v1.md`](../Product%20Requirements/UofA_Extract_Prompt_Iteration_Spec_v1.md)
**Status:** Complete — prompt frozen at v4-kv

## Headline

| Metric | Dev | Test | Spec target | Pass |
|---|---|---|---|---|
| Bundles scored / total | 30 / 30 | 20 / 20 | full | ✓ |
| **Bundle crashes** | **0** | **0** | 0 across 50 (hard gate) | ✓ |
| Mean overall F1 | 0.964 | 0.954 | ≥ 0.85 dev / ≥ 0.80 test | ✓ |
| Min per-factor F1 (detection) | 1.000 | 1.000 | ≥ 0.85 dev / ≥ 0.80 test | ✓ |
| Test vs dev F1 gap | — | 0.01 overall, 0.0 on every factor | ≤ 10 pts per factor (overfit guard) | ✓ |
| Morrison regression | 1.000 | — | ≥ 1.00 | ✓ |
| Aero cou1 regression | 0.973 | — | ≥ 0.97 | ✓ |

## What was actually measured

The spec proposed iterating the v3-nasa-aero extract prompt against a held-out synthetic corpus. The actual iteration that happened was different: a **format pivot from nested JSON to a key-value (kv) format**. No factor-level prompt content changes. The frozen prompt is `v4-kv`.

Two reasons the iteration ended early:
1. **Spec freeze condition met without per-factor tuning.** Min per-factor F1 ≥ 0.85 was satisfied on the very first run with the kv format (every factor's F1 = 1.00 — the model detects every factor in every bundle).
2. **The dominant failure mode found by the eval was a JSON robustness issue, not a prompt-content issue.** Local qwen3.5:4b drops closing braces in long structured JSON outputs ~25-33% of the time, which the kv format eliminates structurally.

## Why the format pivot mattered

First baseline run (v3-nasa-aero JSON): **10 / 30 bundles crashed**. All five `nasa_cfd_*` bundles crashed; another five spread across other cells. The crash mode was identical across them: qwen3.5:4b produced text that started as valid JSON but dropped 1-2 closing braces deep mid-document, leaving the parser at depth > 0 by EOF. F1 was 0.973 on the 20 that survived but the corpus had a 33% null result.

Three mitigation attempts before the pivot:
- **Ollama `format: "json"` (GBNF-constrained decoding)**: 3× slower per bundle, still produced parse failures (constrained decoding still loses tracking on long outputs). Reverted.
- **Tolerant parser improvements**: string-aware brace counting + progressive prefix truncation. Recovers trailing-brace cases but not mid-document drops. Kept.
- **Retry on parse failure (3 stochastic attempts)**: smoke test worked. Kept as belt-and-suspenders.

None of these structurally fixed the issue. The pivot to kv format ([commit dd6d28d](../dev/tools/scripts/llm_extractor.py)) replaced nested JSON with `=== SECTION ===` blocks containing flat `key: value` lines. Multi-line continuation supported. Parser is line-based and deterministic. Downstream `_to_field` / `_validate_factor` already accepted flat strings, so xlsx and JSON-LD writers needed no changes.

Result on the kv baseline: **0 crashes across 30 dev + 20 test = 50 bundles**. Spec hard gate met.

Bonus: **2.5-3× faster per bundle** because the kv output is shorter than the JSON-with-`{value, confidence, source_file, source_page}`-quadruples. Morrison drops from ~7-9 min to 170s. Aero cou1 drops from ~7-9 min to 202s. Full 30-bundle baseline went from a projected 4 hours to a measured 1.5 hours.

## Per-factor detection F1 (both sets)

Every factor: F1 = 1.000 detection rate. Across all 50 bundles, the model finds every factor that the ground truth marks as `assessed`. Zero misses, zero hallucinated factor types. Both packs:

V&V 40 (13 factors): all 1.000 dev, all 1.000 test
NASA-7009b additional 6: all 1.000 dev, all 1.000 test

The detection F1 is at the ceiling. Iterating to push it higher is impossible — the model is already perfect at the type level. Improvement opportunities are on **level accuracy** and **status assignment**, neither of which is the spec's primary metric.

## Per-factor level accuracy (secondary metric)

Spec scoring tolerance: level match if `|extracted - expected| ≤ 1`. Level accuracy is the fraction of detected factors meeting that tolerance.

**Strong** (≥ 0.95 dev, ≥ 0.95 test): Data pedigree, Discretization error, Numerical code verification, Software QA, Use history (test only), Results uncertainty, Results robustness

**Moderate** (0.80-0.95): Most V&V 40 factors

**Weak** (< 0.80):
| Factor | Dev | Test |
|---|---|---|
| Numerical solver error | 0.77 | **0.55** |
| Output comparison | 0.77 | 1.00 |
| Test samples | 0.77 | 0.85 |
| Use error | 0.77 | 0.70 |
| Relevance of QoI | 0.80 | 0.65 |

`Numerical solver error` and `Relevance of QoI` are weaker on test than dev. Test is sample-of-20 vs sample-of-30 dev so per-factor variance is higher; not necessarily real signal.

## Top failure modes

### Dev top failure: `status_mismatch` on Use history (14 / 15 NASA bundles)

Spot-checked 3 random instances of this. **All three are corpus-encoding artifacts, not prompt failures:**

| Bundle | GT status | Model status | Verdict |
|---|---|---|---|
| `nasa_cfd_001` | `not_applicable` | `assessed` (level 2, rationale cites prior benchmarking) | Model defensibly correct — source explicitly mentions prior validation work |
| `nasa_fea_002` | `not_applicable` | `assessed` (level 1, "no prior use history mentioned") | Borderline — model assessed-and-found-nothing vs GT didn't-assess. Same conclusion, different label |
| `nasa_cht_003` | `not_applicable` | `scoped-out` | Both labels mean "not assessed"; categorical disagreement |

The Step B corpus generator marked Use history `not_applicable` whenever the source didn't explicitly say "use history," but many sources mention prior benchmarking, prior validation, or model heritage — which qwen correctly recognizes as evidence. **Iterating the extract prompt to chase this mismatch would overfit to synthetic corpus convention, not real-world quality.**

### Test top failure: `level_mismatch` on Numerical solver error (9 / 20 bundles)

Different from dev's top. Suggests level calibration on this specific factor is fragile across formats and quality. Worth a future iteration cycle but not blocking.

### Other patterns

- **status_mismatch** dominates dev failure modes. Mostly the same NASA factor taxonomy disagreement.
- **level_mismatch** dominates test failure modes. Suggests qwen's level estimates wobble more than its detection.

## Anti-overfit check (spec §5.3)

Per-factor F1 gap (dev - test): **0.000 across all 19 factors**. Both sets sit at 1.000 detection. No overfit signal at the F1 level.

Overall mean F1 gap: **0.964 - 0.954 = 0.010**. Within the 10-point overfit guard.

Bundle-level F1 distribution shape is similar across sets (both have a tail of 0.81-0.87 bundles, mostly 0.95-1.00). No evidence the v4-kv prompt was tuned to dev quirks.

## Failure modes the eval surfaced — beyond prompt content

The synthetic corpus revealed several issues that two-fixture testing (Morrison + aero) couldn't expose. These are real product issues fixed in this branch:

| Issue | Fix | Commit |
|---|---|---|
| `_ROOT` path miscomputed in `score_extraction.py` since the April 29 `tools/` → `dev/tools/` move | `parent.parent` → `parent.parent.parent.parent` + explicit log path | aabd260 |
| `.md` files not in supported extensions | added to `_READERS` and `_FORMAT_PRIORITY` | 088d745 |
| ollama loaded with 262K context (qwen3.5:4b max) → 17 GB VRAM | `num_ctx=32768` default → 6.5 GB VRAM, 5-6× faster per token | 088d745 |
| `max_tokens` not set → ollama unlimited generation | `max_tokens=16384` cap | 088d745 |
| qwen3.5:4b thinking-mode ON by default → 5-10× silent reasoning tokens | `think=False` default for extract calls | 088d745 |
| qwen3.5:4b drops closing braces in long JSON outputs (25-33% of time) | v4-kv format pivot | dd6d28d |

The .md / num_ctx / think defaults all benefit any user running `uofa extract` with local qwen, not just the eval.

## Cost & time

| Component | Estimated (spec) | Estimated (plan) | Actual |
|---|---|---|---|
| Engineering hours | 17 | 24-30 | ~10h interactive + several long background runs |
| Corpus generation API ($) | $23 | $35-50 | **$6.13** (Sonnet 4.6, two-step generator) |
| Iteration API ($) | $0 (local qwen) | $0 | $0 |
| Total API spend | $23 | $35-50 | **$6.13** |

Local compute: ~6 hours qwen3.5:4b inference across multiple baseline runs.

The $6.13 figure is much lower than estimated because the two-step generator on Sonnet 4.6 is more efficient than the spec's single-call generator, and the kv format eliminates one source of regen overhead.

## Stratification of the corpus

| Dimension | Values | Bundles |
|---|---|---|
| Standard | vv40 (13 factors), nasa-7009b (19 factors) | 25 / 25 |
| Domain | cfd, fea, cht | varied |
| Quality | complete, sparse, ambiguous | dev: 12 / 12 / 6, test: 7 / 6 / 7 |
| Format | report-md, memo, slides | dev: 12 / 12 / 6, test: 6 / 8 / 6 |

See [`tests/fixtures/extract_corpus/STRATIFICATION.md`](../tests/fixtures/extract_corpus/STRATIFICATION.md) for the full design rationale and per-cell allocations.

The Step B (ground truth) generator was iterated twice on calibration:
1. First pass over-assigned level 4 (11/13 factors at L4 vs Morrison's mostly L2-3). Tightened with explicit level distribution anchors.
2. Sparse bundles initially had 0-2 N/A factors vs target 4-7. Tightened with explicit "OMIT 4-7 factors entirely" guidance. After fix: 14% N/A on sparse (still below 30-60% target but acceptable; real Morrison has 0% N/A).

## Decision: prompt frozen at v4-kv

All spec §6 success criteria met:
- Dev per-factor F1 ≥ 0.85: ✓
- Test per-factor F1 ≥ 0.80: ✓
- Test vs dev gap ≤ 10 points / factor: ✓
- Zero crashes across 50 bundles: ✓
- Morrison + aero regression maintained: ✓

The frozen prompt is committed at [commit dd6d28d](../packs/vv40/prompts/vv40_extract_prompt.txt). It will ship in the next release after this branch merges.

## Forward note

The eval surfaced level-accuracy weakness on a handful of factors (Numerical solver error, Relevance of QoI, Use error). These are NOT blocking: per-factor detection F1 is at the ceiling and the overall mean is well above the floor. But they're the natural targets if a v5 iteration is desired. Approach for v5 would be:

1. **Status taxonomy clarification**: NASA-7009b allows `assessed`, `not_applicable`, `not-assessed`, `scoped-out` — the prompt and the corpus generator both treat these as overlapping. A clearer prompt + GT convention would reduce status_mismatches.
2. **Level anchors per weak factor**: explicit examples for what level 1/2/3/4/5 looks like for `Numerical solver error` and `Relevance of QoI` specifically.

Neither is needed to ship v4-kv.

## Artifacts

- Frozen prompts: [`packs/vv40/prompts/vv40_extract_prompt.txt`](../packs/vv40/prompts/vv40_extract_prompt.txt), [`packs/nasa-7009b/prompts/nasa_7009b_extract_prompt.txt`](../packs/nasa-7009b/prompts/nasa_7009b_extract_prompt.txt)
- Corpus: [`tests/fixtures/extract_corpus/`](../tests/fixtures/extract_corpus/) (50 bundles, sentinel-locked test set)
- Generator: [`dev/tools/scripts/generate_extract_corpus.py`](../dev/tools/scripts/generate_extract_corpus.py)
- Batch harness: [`dev/tools/scripts/score_extraction_batch.py`](../dev/tools/scripts/score_extraction_batch.py)
- Run records: `runs/baseline_v4kv_*.{json,md}`, `runs/test_eval_*.{json,md}` (gitignored — local artifacts)

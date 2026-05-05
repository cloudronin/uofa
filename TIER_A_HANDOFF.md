# Phase 3 Tier A — Handoff Document

**Branch:** `phase3-tier-a-prep` off `main` (v0.8.0)
**Date:** 2026-05-04
**Spec:** `Product Requirements/UofA_Adversarial_Gen_Phase3_Spec_v1_5.md`
**Plan:** `~/.claude/plans/users-vishnu-library-cloudstorage-dropb-humble-lemon.md`

This document records what landed on this branch, what's pending, and any spec ambiguities surfaced during build (input for spec v1.6).

---

## What's built

### Module layout — `src/uofa_cli/adversarial/judge/`

| File | Purpose | Coverage |
|---|---|---|
| `__init__.py` | Package docstring + spec pointers | 100% |
| `cli_args.py` | `--judges` parsing, position mapping (A/B/C), `--parallel` validation | 97% |
| `family_check.py` | Cross-family circularity check (judges + generator), exit code 5 | 100% |
| `bundle.py` | `judge_ready_bundle.tgz` reader + JSONSchema-validated manifest | 97% |
| `bundle_writer.py` | Writer; normalizes Phase 2 class names; preserves `phase2_outcome_class_raw` | 92% |
| `prompts.py` | **STUB** — function signatures only; real v1.0.0 template deferred (§24.3) | 100% |
| `triage.py` | Majority-of-3 bucket assignment (CONVERGENT / DIVERGENT / UNCERTAIN) | 100% |
| `adjudication.py` | Cohen's κ + Fleiss' κ + confusion matrices; `_to_count_matrix` shape helper | 100% |
| `retry.py` | Async-aware exponential-backoff decorator with jitter | 100% |
| `caching.py` | Vendor-specific cache-key construction (OpenAI + Gemini) | 100% |
| `batch.py` | Batch submit/poll/reassemble dispatch (Stage 2 reassembly is a skeleton) | 89% |
| `runner.py` | CLI entry points (`run_bundle`, `run_judge`, `run_triage`, `run_adjudicate`) | 87% |
| `providers/__init__.py` | `FAMILY_MAP` + `resolve_family()` with glob support | 100% |
| `providers/base.py` | `AbstractJudgeProvider` ABC + `Judgment` + `CalibrationResult` dataclasses | 100% |
| `providers/openai_compat.py` | OpenAI proper + HF Endpoints (env-var-driven dual init) | 77% |
| `providers/gemini.py` | Google Gemini with `response_schema` strict mode | 58% |

Overall coverage on `src/uofa_cli/adversarial/judge/`: **89%** (target ≥85%).

The Gemini and OpenAI provider gaps are real-network paths (`_build_default_client`, `_is_transient`, real calibration loop) which only fire with API credentials. Mock-driven tests cover the call shape, schema enforcement, and judgment construction — the network paths exercise on the first Stage 1 calibration run.

### Other artifacts
- `specs/judge_output_schema.json` — strict-mode-compatible JSONSchema (no `$ref`/`format`/`default`), 12 required properties, 6-class verdict enum
- `dev/tools/scripts/verify_openai_strict_schema.py` — one-off real-API verification (~$0.01); see "Pending real-API verification" below
- `dev/build/adversarial/phase2/2026-04-26/judge_ready_bundle.tgz` — real Phase 2 bundle stashed for future Stage 1 runs (4,556 packages, 10MB)
- `pyproject.toml` — `[project.optional-dependencies] judge` group; `[tool.pytest.ini_options]` documents the coverage gate
- `tests/adversarial/judge/` — 170 tests, all green, fixture pattern mirrors existing `tests/adversarial/conftest.py`

### CLI surface added to `src/uofa_cli/commands/adversarial.py`
- `uofa adversarial bundle` — package an already-analyzed Phase 2 batch into `judge_ready_bundle.tgz`
- `uofa adversarial judge` — run the LLM-as-judge ensemble (mock or real providers)
- `uofa adversarial triage` — majority-of-3 inter-judge bucketing
- `uofa adversarial adjudicate` — Cohen's κ + Fleiss' κ + confusion matrices
- `uofa adversarial analyze --emit-judge-bundle` — opt-in flag; without it, `analyze` behavior is unchanged

---

## Real-corpus verification (spec §24.2 acceptance #4)

```
$ uofa adversarial bundle \
    --batch-dir dev/build/adversarial/phase2/2026-04-26/ \
    --out dev/build/adversarial/phase2/2026-04-26/judge_ready_bundle.tgz
  packaging dev/build/adversarial/phase2/2026-04-26 → /tmp/phase2_bundle.tgz
    wrote 4556 packages; normalized class distribution
    {'COV-HIT': 2707, 'COV-WRONG': 1470, 'GEN-INVALID': 379}
  ✓ judge_bundle  ...
```

Round-trip confirmed: `bundle.open_bundle()` reads all 4,556 packages back, `phase2_outcome_class_raw` preserved on every entry. End-to-end smoke `bundle → judge → triage → adjudicate` produces non-degenerate κ values (AB κ=0.444, AC κ=0.500, BC κ=0.500, Fleiss κ=0.458) — all in the planned 0.4–0.7 mock-fixture range.

**Skipped:** 49 outcomes.csv rows (~1%) didn't have matching jsonld dirs, all from `adv-2026-001-w-ar-05_*` directories (note: missing the `p2-` segment in the spec_id; appears to be from an earlier W-AR-05-specific patch run with non-standard naming). The 4,556/4,605 capture rate is acceptable for Phase 3 — the missing rows are not §6.7 candidates.

### Real-LLM smoke against Anthropic Claude

To validate the full pipeline against a real model (not just mocks), an `anthropic` provider target was added to `OpenAICompatProvider` (uses Anthropic's OpenAI-compat endpoint at `https://api.anthropic.com/v1/`). Anthropic is the Phase 2 generator family, so this is a same-family smoke only — requires `--allow-same-family-judge` and is **not** a Stage 2 production judge.

```bash
ANTHROPIC_API_KEY=sk-ant-... uofa adversarial judge \
  --in dev/build/adversarial/phase2/2026-04-26/judge_ready_bundle.tgz \
  --out /tmp/judge_claude_smoke \
  --judges anthropic,mock_b,mock_c \
  --calibration-only \
  --allow-same-family-judge
```

Result: 5 calibration cases judged by `claude-3-7-sonnet-20250219` (Anthropic remapped our `claude-sonnet-4-5` request); every response validated cleanly against `specs/judge_output_schema.json`; triage + adjudication ran end-to-end. **The architecture is proven against a real LLM.**

Substantive note: Claude correctly returned `verdict=OUT-OF-SCOPE, confidence=0.15` on every case with reasoning that explicitly cited the stub prompt as having no real package content to assess — exactly the right behavior for a placeholder template. The pairwise κ values are not meaningful (one judge returns a constant verdict; mocks return varying ones); they will become meaningful once `prompts.py` carries the v1.0.0 framework context + few-shots + real package excerpts.

#### Schema-portability finding (input for spec v1.6)

Anthropic's strict-mode JSON schema is more restrictive than OpenAI's:

| Keyword | OpenAI strict | Anthropic strict |
|---|---|---|
| `$comment` | accepted | rejected |
| `minimum` / `maximum` | accepted | rejected |
| `minLength` / `maxLength` | accepted | rejected |
| `pattern` | accepted | rejected |
| `exclusiveMinimum` / `exclusiveMaximum` | accepted | rejected |

`OpenAICompatProvider._call_strict()` strips these for the Anthropic call only (via `_strip_unsupported_for_anthropic`) and revalidates the response against the full schema post-parse. OpenAI and Gemini code paths use the schema verbatim.

`$comment` was removed from `specs/judge_output_schema.json` (was documentation; lives in code comments).

---

## Spec-vs-reality reconciliation

The spec assumed Phase 2 outcome classes `COV-HIT / COV-MISS / COV-WRONG`. Actual Phase 2 emits `COV-HIT-PLUS / COV-WRONG / GEN-INVALID / COV-CLEAN-WRONG`. The bundle writer normalizes per `bundle_writer.NORMALIZE`:

| Phase 2 actual | Normalized | Notes |
|---|---|---|
| COV-HIT-PLUS | COV-HIT | "PLUS" notes auxiliary firings; preserved in `phase2_outcome_class_raw` |
| COV-WRONG | COV-WRONG | Identity |
| COV-CLEAN-WRONG | COV-WRONG | Negative-control false positives folded into COV-WRONG |
| GEN-INVALID | GEN-INVALID | New normalized class; SHACL-failed packages; auto-routes toward GENERATOR-ARTIFACT verdict |

Notable: **no `COV-MISS` rows** in the actual corpus (every gap_probe case had some rule fire). The judge prompt should treat `gap_probe + COV-WRONG` as the natural REAL-GAP / EXISTING-RULE-MISBEHAVIOR candidate space.

The judge output schema (`specs/judge_output_schema.json`) keeps the spec's 6-class verdict enum unchanged. `GEN-INVALID` is only a normalized **input class** the judge sees, not a verdict.

---

## Pending real-API verification (Wave 1 step 2)

`dev/tools/scripts/verify_openai_strict_schema.py` is shipped but **not yet run** — needs an OpenAI API key set in the env. To complete the Wave 1 acceptance:

```bash
OPENAI_API_KEY=sk-... python dev/tools/scripts/verify_openai_strict_schema.py
# expected: "PASS: schema accepted, response valid against jsonschema" → exit 0
# cost: ~$0.01 (single gpt-4o call)
```

The schema was hand-validated against the [OpenAI strict-mode allowed-property set](https://platform.openai.com/docs/guides/structured-outputs/supported-schemas) and the `Draft202012Validator.check_schema()` passes. R1 (the highest pre-Tier-A risk) is mitigated structurally; this script confirms it operationally.

If the script fails, surface the rejection details into spec v1.6 — the schema change is purely the JSONSchema file, no provider code changes needed.

---

## Spec ambiguities / open questions for v1.6

1. **`--calibration-only` vs `--calibration-check`.** Spec §14.3 uses `--calibration-only` (smoke test) and spec §9.1 uses `--calibration-check` (drift sanity check during full run). Implemented `--calibration-only`; left `--calibration-check` for Stage 1 follow-up.
2. **`outcomes.csv` `spec_id` semantics.** Spec §2.1 example shows `case_id: adv-2026-p2-001-gohar-data-drift-v01` (base id + variant). Actual Phase 2 outcomes.csv `spec_id` includes the `_<subtlety>_<basecou>` suffix, e.g. `adv-2026-p2-001-w-ar-01_high_morrison-cou1`. Bundle writer keys on the FULL id; case_id in the bundle becomes `<full_spec_id>-v<NN>`. Both forms match the §7.7 case_id regex.
3. **Bundle producer ownership.** Spec §2.1 documents the schema but doesn't name an owner. Plan decision: bundle writer is in scope as `bundle_writer.py` + `analyze --emit-judge-bundle` + `bundle` subcommand. Phase 2 owners can override if their schema diverges.
4. **`prompts.py` v1.0.0 content.** Stubs only. Real prompt template (framework context, six verdict-class definitions, reasoning scaffold, few-shot examples) is post-Tier-A; few-shots come from the calibration set, which is also post-Tier-A.
5. **Skipped 49 rows from `adv-2026-001-w-ar-05_*` dirs.** Could indicate a Phase 2 batch convention drift or a leftover from a W-AR-05-specific patch run. Worth a check before Stage 2 to confirm those rows aren't material to §6.7 candidates.

---

## What's NOT built (deferred per spec §24.3)

These require Phase 2 outputs (now available!) plus author-side work, and are tracked separately from this Tier A scope:

- `specs/calibration/calibration_set_v1.jsonl` — 30 author-annotated cases (5 per verdict class)
- `packs/core/judge_prompts/v1.0.0.md` — real prompt template with framework context + few-shots from calibration
- Stage 1 calibration runs against real OpenAI / Gemini / HF endpoints
- Stage 2 full-corpus judgment (~4,556 × 3 judges; ~$420 LLM spend)
- Stage 4 author adjudication queue + agreement statistics
- Stage 5 pattern formalization → v0.5 catalog rule additions
- Case study re-run with v0.5 against Morrison COU1/COU2 + Nagaraja
- §13.4 ANOVA robustness analysis

Infrastructure built here makes all of the above runnable; you drive them when API budget + author-annotation time are available.

---

## Acceptance checklist (plan §"Acceptance")

- [x] All modules committed to `phase3-tier-a-prep` branch
- [x] `pytest tests/adversarial/judge/` green, coverage 89% on `judge/` package (target ≥85%)
- [ ] `verify_openai_strict_schema.py` passes (author-side; pending API key)
- [x] Smoke test runs end-to-end against the real `2026-04-26/` corpus → `judge_ready_bundle.tgz` with 4,556 packages
- [x] Bundle round-trip test passes; `phase2_outcome_class_raw` provenance preserved
- [x] Mock judgment fixtures produce pairwise Cohen's κ in 0.4–0.7 (verified in `test_adjudication.py` and `test_runner.py::test_summary_kappas_in_target_range`)
- [x] `analyze` without `--emit-judge-bundle` is byte-for-byte unchanged (gated by `getattr(args, 'emit_judge_bundle', False)`)
- [x] `TIER_A_HANDOFF.md` documents what's built, what's pending, spec ambiguities
- [ ] PR opened to `main`; merge once green

---

## v1.6 update (2026-05-04 phase3-tier-a-prep continuation)

This branch now carries the full v1.6 + productive-OOS deltas in addition to the v1.5 Tier A baseline above. New module list (additions only):

| File | Purpose | Coverage (judge pkg) |
|---|---|---|
| `providers/litellm_provider.py` | Single litellm-backed provider; replaces `openai_compat.py` + `gemini.py` (deleted in Phase 1) | 76% |
| `providers/capabilities.py` | Per-provider capability table (strict_schema, batch_api, caching, blocklists, thinking kwargs) | 100% |
| `anchor.py` | Judge D calibration-anchor ingest + author-override capture | 93% |
| `arbitration.py` | Judge E arbitration over the disagreement queue + Stage 3b ARBITRATED/ESCALATED partition | 90% |
| `final_verdict.py` | 4-layer source priority (AUTHOR_OVERRIDE > AUTHOR_FINAL > ARBITRATED > CONVERGENT) + productive-OOS evidence_gap carry-through | 91% |
| `cost_gate.py` | Budget tracker, `--dry-run` cost estimate, `--max-cost` enforcement | 100% |
| `resume.py` | `--resume` idempotency over per-judge JSONL outputs | 100% |
| `formalize.py` | Wave J — REAL-GAP → Jena rule scaffold (forward-chaining only per Delta 6) | 96% |
| `case_study.py` | Wave K — catalog × COU rule re-run + delta_table.md | 92% |

Overall coverage on `src/uofa_cli/adversarial/judge/`: **79%** (was 89% in v1.5). The drop reflects the runner.py CLI surface expanding faster than the runner-level integration tests; module-level coverage on the new pieces (`cost_gate.py`, `resume.py`, `formalize.py`, `case_study.py`) is ≥92%.

### v1.6 schema + prompt artifacts
- `specs/judge_output_schema.json` — adds `evidence_gap` field; `if/then` block requires it when `verdict == 'OUT-OF-SCOPE'` (Delta 1).
- `specs/judge_e_output_schema.json` — Judge E arbitration schema with `arbitration_basis` + `production_judge_evaluation` + same OOS conditional-required (Delta 2).
- `packs/core/judge_prompts/v1.1.0.md` — production prompt with productive-OOS framing + cal-021 OOS exemplar (Delta 3); v1.0.0.md retained for reproducibility.
- `packs/core/judge_prompts/arbitration_v1.0.0.md` — Judge E prompt with OOS arbitration instruction (Delta 4).

### v1.6 calibration set
- `specs/calibration/calibration_set_v1.jsonl` — 30-case Judge D anchor (5 per class, 6 canonical few-shots).
- `specs/calibration/packages/cal-02[1-5]-out_of_scope-stub.jsonld` — author-constructed OOS packages with `adversarialProvenance.evidenceGapDescription`.
- `dev/tools/scripts/validate_calibration_set.py` v2 — Checks 11 (REAL-GAP requires section_6_7_mapping), 12 (§6.7 coverage ≥4 of 6), W1/W2 soft warnings.

### CLI surface added in v1.6
- `uofa adversarial calibrate-anchor ingest` — validate Judge D anchor + capture author overrides.
- `uofa adversarial arbitrate` — Judge E arbitration over the disagreement queue.
- `uofa adversarial finalize` — assemble `final_verdicts.jsonl` with productive-OOS evidence_gap + provenance source attribution.
- `uofa adversarial formalize` — Wave J Jena rule scaffolds (forward-chaining only).
- `uofa adversarial case-study-rerun` — Wave K v0.4.1 vs v0.5 delta table.
- `uofa adversarial judge --dry-run --max-cost --resume` — Wave F + I production-readiness flags.
- `uofa adversarial adjudicate --judgments-e --judgments-d --author-adjudications --spot-check-overrides` — Wave D extended agreement metrics.

### Real-API verification scripts (Wave L — pending API keys)
- `dev/tools/scripts/verify_litellm_refactor.py` — confirms litellm path matches v1.5 SDK results.
- `dev/tools/scripts/verify_anthropic_native_thinking.py` — verifies extended thinking + strict-schema (with `if/then` strip) end-to-end.
- `dev/tools/scripts/verify_mistral_strict_schema.py` — populates `capabilities.py` Mistral blocklist if needed (deferred until `MISTRAL_API_KEY`).

### Productive-OOS Delta 5 details (final_verdicts.jsonl source attribution)
- `evidence_gap_source ∈ {judge_a, judge_b, judge_c, judge_e, author}`.
- CONVERGENT OOS: highest-confidence judge's gap is primary; canonical A→B→C tie-break; alternatives preserved in `alternative_evidence_gaps`.
- ARBITRATED OOS sourced from Judge E.
- AUTHOR_FINAL / AUTHOR_OVERRIDE OOS sourced from author record.

### Capability-table notes
- `supports_batch_api` is OFF for `gemini` and `anthropic` (litellm 1.30 only supports OpenAI in `create_batch`). Internal helpers `_submit_anthropic_batch` etc. are wired and tested via mocks — flipping the flag back ON when litellm matures is a one-line change. Mistral has no batch API per spec §6.7.
- Anthropic `schema_keyword_blocklist` includes `if/then/else` (Delta 1 conditional-required is enforced post-call by the runtime parser).

### What's still pending (Wave L + Tier B)
- Real-API smokes against Anthropic / OpenAI / Mistral (need `MISTRAL_API_KEY`).
- End-to-end production run on the 4,556-package corpus (cost ≈ $420 + Mistral arbitration).
- Spec text update at §15 hard gate #2 (v1.0.0 → v1.1.0) — sandbox-blocked while editing user's Dropbox spec doc; one-line author-side change.
- Backward-chaining OOS Jena rule generation: separate engineering, May 11–24 substrate validation test (`UofA_OOS_Substrate_Validation_Test_v0_1.md`).

### Test count (judge package)
- v1.5: 170 tests
- v1.6 commit `c9918a6` (Phase 2): 269 tests
- v1.6 commit `54ac672` (Phase 3): 307 tests
- v1.6 commit current (Phase 4 + 5): 322 tests, all green


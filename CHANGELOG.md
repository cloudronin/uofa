# Changelog — Unit of Assurance (UoFA) Specification

All notable changes to this project are documented here.

## [0.8.0] — 2026-05-04

### Added — Extract eval v1 (synthetic corpus + held-out test)

50-bundle synthetic eval corpus stratified across (standard × domain × quality × format) at [`tests/fixtures/extract_corpus/`](tests/fixtures/extract_corpus/), with sentinel-locked held-out test set and a 2-step Claude-driven generator at [`dev/tools/scripts/generate_extract_corpus.py`](dev/tools/scripts/generate_extract_corpus.py).

Frozen v4-kv prompt achieves on dev/test:
- Mean F1: 0.964 / 0.954
- Per-factor F1: 1.000 across all 19 factors (V&V 40 + NASA-7009b)
- Bundle-level crash rate: 0 / 50
- Morrison regression: F1 = 1.000
- Aero cou1 regression: F1 = 0.973

Writeup at [`docs/extract_eval_v1.md`](docs/extract_eval_v1.md). Batch eval harness at [`dev/tools/scripts/score_extraction_batch.py`](dev/tools/scripts/score_extraction_batch.py) with confusion analysis, per-factor stats, and held-out-set guards (refuses to score `test/` unless `--allow-test` is passed AND prompt-version contains neither `iter` nor `dev`).

### Changed — Extract prompts: nested JSON → key-value blocks

`packs/vv40/prompts/vv40_extract_prompt.txt` and `packs/nasa-7009b/prompts/nasa_7009b_extract_prompt.txt` rewritten to emit `=== SECTION ===` blocks containing flat `key: value` lines instead of nested `{value, confidence, source_file, source_page}` JSON objects.

Local qwen3.5:4b dropped 1-2 closing braces ~25-33% of the time on the previous JSON format, causing irrecoverable parse failures (10/30 dev bundles crashed in the last JSON baseline). The kv format eliminates the nested-structure failure class and runs ~2.5-3× faster (less verbose output).

Downstream `_to_field` and `_validate_factor` already accepted flat strings, so xlsx and JSON-LD writers needed no changes. Backwards-compatible with the JSON format via fallback in `_parse_response`.

### Fixed — `uofa extract` performance and reliability

- **`.md` files now supported** as evidence input ([`document_reader.py`](src/uofa_cli/document_reader.py)). Uses the existing text reader. Markdown is a common engineering doc format; previously `extract` exited "No supported files found" on a folder of `.md`.
- **Adaptive `num_ctx` for ollama** ([`litellm_backend.py`](src/uofa_cli/llm/litellm_backend.py)). Previously the daemon defaulted to the model's max (262K for qwen3.5 = 17 GB VRAM, 5-6× slower per token). Now sized to the actual prompt + output budget, bucketed to 8K/16K/32K/49K/65K to avoid model reloads on consecutive similar calls. Bounds VRAM at ~8 GB. Override via `options.extra["num_ctx"]`.
- **`max_tokens` cap of 16384** for extract calls. Without this cap, ollama defaulted to unlimited generation; verbose models could ramble past a complete response.
- **`think=False` default for ollama extract calls**. qwen3.5 (and other Qwen3-family) models have thinking-mode ON by default at the daemon level, generating 5-10× silent reasoning tokens. Letting that through caused ~22 min/bundle wall time on local extract; explicit `think=False` brought it to ~7 min/bundle for the same output.
- **Tolerant JSON parser** in `_parse_response` for the JSON-format fallback path. Adds string-aware brace counting + progressive prefix truncation, recovering when output occasionally drops trailing braces.
- **Retry on parse failure** (3 stochastic attempts) wraps the LLM call. Belt-and-suspenders with the kv format and tolerant parser.
- **`_ROOT` path bug** in `dev/tools/scripts/score_extraction.py` introduced by the April 29 `tools/` → `dev/tools/` reorganization, which made the script resolve fixtures to `dev/tools/tests/fixtures/...` (doesn't exist).

### Cost vs. spec

Synthetic corpus generated for **$6.13** (Sonnet 4.6) vs. spec's $23 estimate. Iteration ran on local qwen3.5:4b — $0 inference cost.

## [0.5.0] — 2026-04-21

### Added — v0.5 JSON-LD context

- **New optional vocabulary** (`spec/context/v0.5.jsonld`): 12 additions backing the expanded weakener catalog. All backward-compatible — every v0.4 property is preserved; new properties are optional at the SHACL level.
  - Data vintage / model revision: `dataVintage`, `modelRevisionDate`
  - Evidence timestamps: `evidenceTimestamp`, `signatureTimestamp`
  - Provenance marking: `isFoundationalEvidence`
  - Model versioning: `modelVersion` (on ModelConfiguration)
  - Sensitivity + activities: `hasSensitivityAnalysis`, `hasVerificationActivity`
  - Identifier resolution: `referencesIdentifier`
  - Staged CLARISSA vocabulary for v0.6 W-AR-06/W-AR-07: `residualRiskJustification`, `consideredAlternative`, `knownLimitation`

### Added — Weakener catalog expansion (12 → 23 patterns)

Eleven new weakener patterns join the `packs/core` catalog. All validated via unit-test fixtures under `tests/fixtures/weakeners/` (27 tests pass) plus inline Morrison regression (see `docs/v0.5-morrison-deltas.md`).

- **W-ON-02** (High) — Unbounded Applicability: COU lacks both `hasApplicabilityConstraint` and `hasOperatingEnvelope`.
- **W-AR-03** (High) — Inference Method Mismatch: requirement's `requiredVerificationMethod` differs from generating activity's `activityType`.
- **W-AR-04** (High) — Model Version Drift: `ModelConfiguration.modelVersion` ≠ UofA's `currentModelVersion`.
- **W-AL-02** (Medium) — Sensitivity Gap: UQ declared but no `hasSensitivityAnalysis` linked.
- **W-EP-03** (High) — Stale Input Data: dataset `dataVintage` predates UofA `modelRevisionDate`.
- **W-CON-01** (High) — Factor-Decision Consistency: `Accepted` decision with credibility factors lacking both `requiredLevel` and `achievedLevel`.
- **W-CON-03** (High) — Future-dated Evidence: `evidenceTimestamp` > UofA `signatureTimestamp`.
- **W-CON-04** (Medium) — Profile-Structure Consistency: Complete profile with no `hasSensitivityAnalysis` (single-branch v0.5; broader enumeration deferred to v0.6).
- **W-CON-02** (Medium, **Python**) — Identifier Resolution: `referencesIdentifier` target neither resolves locally nor has an external-fetch hint.
- **W-CON-05** (High, **Python**) — Activity-Evidence Consistency: `hasVerificationActivity` declared with no evidence linked via `prov:wasGeneratedBy`.
- **W-PROV-01** (Critical, **Python**) — Provenance Chain Incomplete: BFS upstream from `bindsClaim` — emit at nodes without upstream edges that are not marked `uofa:isFoundationalEvidence=true`.

### Added — CLI

- **`uofa catalog`** — enumerates all weakener patterns across active packs. `--format json` for machine-readable output. Covers Jena rules and Python-implemented rules. Satisfies the "catalog CLI" deliverable.

### Changed — Morrison regression deltas

| | v0.4.0-nafems (baseline) | v0.5.0-pre-phase2 | Delta |
|---|---|---|---|
| Morrison COU1 | 14 | 24 | +10 (W-ON-02 + W-CON-01×6 + W-CON-04 + COMPOUND-01×2 cascades) |
| Morrison COU2 | 6 | 16 | +10 (W-ON-02 + W-AL-02 + W-CON-04 + W-PROV-01×7) |

Per-rule attribution in `docs/v0.5-morrison-deltas.md`.

### Release-branch discipline

- **Frozen reference tag** `v0.4.0-nafems` (on commit `e11b2b4`) preserves the exact state used for NAFEMS demo slide screenshots. All screenshots regenerated from v0.5 will show different counts; the demo runs from the frozen tag regardless.
- **v0.5.0-pre-phase2** tag lands on `main` as the Phase 2 experimental baseline.

### Known limitations

- Python post-pass rules (W-PROV-01, W-CON-02, W-CON-05) do not feed back into the Jena `COMPOUND-01` cascade. Python-generated Critical weakeners are reported but not paired with Jena-detected High weakeners via the existing compound rule. Compound cascade across engines is deferred to v0.6.
- W-CON-04 ships one branch (Complete profile missing SensitivityAnalysis). Broader ProfileComplete structural enumeration is deferred to v0.6 once distinct semantics beyond SHACL enforcement are settled.
- W-CON-02 limits identifier resolution to the local graph plus HTTP(S) URL self-documentation; no HTTP fetch attempts in v0.5.
- COMPOUND-02 (Factor Credibility Erosion) remains deferred (commented out in `packs/core/rules/uofa_weakener.rules`). `uofa catalog` filters it out.

## [0.4.1] — 2026-04-04
### Added
- **`uofa import` command:** Imports practitioner-filled Excel workbooks into signed, validated JSON-LD UofA artifacts. Supports VV40 (13 factors) and NASA-STD-7009B (19 factors) packs, v2 evidence types (`ReviewActivity`, `ProcessAttestation`, `DeploymentRecord`, `InputPedigreeLink`), automatic URI generation, `assessmentPhase` assignment, and `ImportActivity` provenance tracking. Optional `--sign` and `--check` flags for one-command import-sign-validate workflow.
- **`uofa schema --emit python`:** Generates `excel_constants.py` from SHACL shapes (factor names, level ranges, dropdown enums, evidence types). Keeps import validation in sync with SHACL — no manual constant maintenance.
- **Excel import pipeline modules:** `excel_reader.py` (parse + validate workbooks), `excel_mapper.py` (intermediate dict → JSON-LD), `excel_constants.py` (generated from SHACL).
- **`openpyxl` optional dependency:** `pip install uofa-cli[excel]` for Excel import support.
- **Test corpus:** 15 programmatic Excel test fixtures with manifest-driven parametrized test runner (106 tests covering happy paths, error cases, NASA factors, and URI generation).

## [0.4] — 2026-04-02
### Added
- **NASA-STD-7009B support:** New `packs/nasa-7009b/` domain pack with 19 credibility factors (13 shared with V&V 40 + 6 NASA-only), 6 NASA-specific weakener rules (W-NASA-01 through W-NASA-06), and SHACL shapes enforcing CAS level range 0-4 and assessment phase requirement.
- **Multi-pack CLI support:** `--pack` flag now accepts multiple values (`--pack vv40 --pack nasa-7009b`). SHACL shapes and Jena rules from all specified packs are loaded as a union.
- **`uofa migrate` command:** Upgrades v0.3 JSON-LD files to v0.4 (updates context URL, adds `factorStandard` to each CredibilityFactor). Supports `--dry-run`.
- **v0.4 JSON-LD context** (`spec/context/v0.4.jsonld`): 3 new properties (`factorStandard`, `assessmentPhase`, `hasEvidence`) and 4 new evidence classes (`ReviewActivity`, `ProcessAttestation`, `DeploymentRecord`, `InputPedigreeLink`) with supporting properties.
- **V&V 40 domain pack** (`packs/vv40/`): Extracted V&V 40 factor taxonomy (13 factors, level range 1-5) from core into its own pack.
- **Aerospace example** (`examples/aerospace/uofa-aero-nasa7009b.jsonld`): Demonstrates multi-standard assessment with all 19 factors, evidence classes, and multi-pack validation.
- **Evidence class SHACL shapes:** ReviewActivityShape, ProcessAttestationShape, DeploymentRecordShape, InputPedigreeLinkShape added to core shapes.
- **W-NASA pattern IDs:** WeakenerAnnotation patternId regex updated to accept `W-NASA-NN` format.

### Changed
- **Core pack is now standards-agnostic:** `packs/core/pack.json` no longer lists specific standards or constrains factorType to V&V 40 values. Factor taxonomy enforcement is delegated to domain packs.
- **Default pack is `vv40`:** When no `--pack` flag is specified, the CLI defaults to `--pack vv40` for backward compatibility with v0.3 behavior.
- **Morrison examples upgraded to v0.4:** Context URL updated, `factorStandard: "ASME-VV40-2018"` added to all CredibilityFactor entries.
- **All skeleton templates and starters updated** to v0.4 context and factorStandard.

## [0.3] — 2026-04-01
### Added
- **13-factor expansion:** Morrison COUs now encode all 13 V&V 40 credibility factors (7 assessed + 6 not-assessed), up from the original 7.
- **W-EP-04 weakener pattern:** Detects unassessed credibility factors at elevated model risk (MRL > 2). Fires 6 times on COU2 (MRL 5) but not on COU1 (MRL 2) — the core risk-driven divergence demonstration.
- **`uofa diff` command:** Compares weakener profiles across two COUs with identity block, divergence table (core + compound patterns separated), severity summary, and divergence explanations from the rule engine.
- **Domain packs system:** SHACL shapes, Jena rules, templates, and prompts organized into modular packs under `packs/`. Core pack ships with 13 factors and 13 weakener patterns.
- **`uofa init` command:** Scaffolds new UofA projects with template JSON-LD, signing keys, and `.gitignore`.
- **`uofa packs` command:** Lists and inspects installed domain packs.
- **Starter examples:** Real-world starter templates under `examples/starters/`.

### Changed
- **`uofa diff` now runs Jena rules dynamically** instead of reading static `hasWeakener` arrays from JSON-LD files.
- **Morrison COU1 weakener profile:** 14 weakeners across 6 patterns (4 Critical, 10 High). Compound patterns (COMPOUND-01, COMPOUND-03) fire via chained forward-chaining inference.
- **Morrison COU2 weakener profile:** 6 weakeners, all W-EP-04 (High) — fires on 6 unassessed factors at MRL 5.
- **COU divergence:** 7 divergent patterns between COU1 and COU2 (5 core + 2 compound), all divergent (no shared patterns).
- SHACL shapes and Jena rules moved from `spec/` to `packs/core/` with symlinks for backward compatibility.
- JSON-LD context updated to v0.3 (`spec/context/v0.3.jsonld`).

### Fixed
- Removed `@type: @id` from `acceptanceCriteria` context definition (was silently dropping strings).

## [0.1] — 2025-11-01
### Added
- Initial **UoFA** specification published at https://uofa.net (single-page canonical spec).
- Namespace established: `https://uofa.net/vocab#` with prefix `uofa`.
- JSON-LD Context released: `context/v0.1.jsonld`.
- JSON-LD Frame (skeleton) released: `schema/v0.1.jsonld`.
- Repository bootstrap: README, licensing (CC BY 4.0), example snippet.

### Notes
- This is a **draft** intended for early adopters and pilot implementations.
- Formal validation to be provided via **SHACL shapes** and/or a JSON Schema profile in a subsequent release.

[0.1]: https://uofa.net

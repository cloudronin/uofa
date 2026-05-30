# Changelog — Unit of Assurance (UoFA) Specification

All notable changes to this project are documented here.

## [Unreleased]

### Added — Surrogate pack + Surrogate Interrogation Probe (SIP)

Surrogate-model credibility, in two separable workstreams joined only by a frozen evidence contract.

- **SIP evidence contract (G3 freeze)** ([`specs/sip_evidence_bundle_schema.json`](specs/sip_evidence_bundle_schema.json)): frozen JSON Schema for the SIP→pack integration boundary. **The firewall** (signature-scoped, Addendum A) — SIP measures, never judges — is enforced here: `additionalProperties:false` at every level, with the `FORBIDDEN_TOKENS` denylist ([`forbidden.py`](src/uofa_cli/interrogate/forbidden.py)) scoped to the *measurement region*. Decision content is valid only inside a signed `engineerDecision` block; anywhere else it is a breach. Exact-property-name matching, so `parentModelSnapshot.parentDecision` (inherited provenance) is legitimate.
- **SIP component** (`uofa interrogate`, behind the `[interrogate]` extra): thin model adapter (single `predict` contract — no native framework support), benchmark/reference loader, numpy-backed measurement orchestrator (residuals, envelope coverage, physics-constraint residuals, UQ calibration) with per-measurement provenance, and a packager that validates-then-signs (reusing ed25519/RDFC-1.0 signing) and attaches PROV-DM (no orphan entities → core `W-PROV-01` stays silent). The command emits the bundle, prints an at-a-glance surrogate-vs-reference comparison, and renders **no verdict**; there is deliberately no `--check`/`--decision`/threshold flag.
- **`packs/surrogate`** (pack 0.1.0, independent of CLI version): `uofa-surr:` vocabulary (additive/optional, `ProfileMinimal`-compatible). Weakener catalog reuses W-EP-03/W-AR-04/W-AL-02/W-ON-02 from core unchanged and adds **W-SURR-01** (physics-constraint evidence missing, High), **W-SURR-02** (unvalidated parent — severity split: Not Accepted → Critical, unrecorded → High), **W-SURR-03** (extrapolation beyond envelope, High; containment via an `_evalOutsideEnvelope` SPARQL pre-pass CONSTRUCT). W-SURR-04 + residuals-unlinked stay method-first CANDIDATES, not pre-implemented.
- **Productive-OOS** (`rules/oos/oos_v0.1.rules`, 2 rules: calibration-provenance, model-comparison), **coverage matrix** against the Jakeman-derived proto-taxonomy (`docs/UofA_Surrogate_ProtoTaxonomy_v0_1.md`) reported as fraction-detected with the emerging-reference caveat — **no Cohen's-κ claim**, and `cal-surr-01..05` calibration packages (W-SURR-02 exercises both severity arms).
- **AirfRANS dual-COU case study** ([`packs/surrogate/examples/airfrans/`](packs/surrogate/examples/airfrans/)): same surrogate in-distribution (COU1) vs Reynolds-extrapolation (COU2); sole weakener divergence is W-SURR-03, legible in one `uofa diff`. PDEBench breadth check gated behind a per-file CC-BY license precondition.
- **Firewall enforcement**: `dev/tools/scripts/firewall_guard.py` (imports the one token list, scoped to the measurement region) wired into `make all`; `AGENTS.md` §12 (signature-scoped + vendor conformance); `specs/` force-included into the wheel so the schema layer runs for pip-installed users (empirically gated by a wheel-content test). v1 staged ingestion renders a human-review view with `pass_fail`/Decision left for the reviewer and the canonical signed bundle linked.
- **Signed engineer decision + accuracy reporting (Addendum A)**: the firewall moved from a flat token denylist to a **signature-scoped** rule. New `uofa decision review` (read-only comparison, terminal silence) and `uofa decision sign --key <engineer-key>` write an `engineerDecision` block signed over the decision **plus the measurements it references** (`signing.py` two-scope signatures: measurement signature excludes the block so it survives a later decision; decision signature binds the recomputed measurement hash → tamper-evident); stale-bundle refusal, no default/headless decider identity (A8). `uofa verify` gained dual-signature verification (`--decision-pubkey`), reporting both signatures independently and treating an unverifiable decision as "no engineer decision," never package failure. New `uofa interrogate init` guided wizard (model detect → physical-I/O Q&A → adapter/scope/load-stub codegen → adapter smoke test; never silent-defaults scope, never fabricates reference; scope-provenance tags ride into the bundle). Vendor conformance is a checkable artifact property — the decision signature must be the deciding human's key — not a certification.
- **v2 native ingestion + end-to-end**: `src/uofa_cli/readers/sip_bundle_reader.py` verifies a SIP bundle's measurement (and, when a key is supplied, decision) signatures, then maps SIP §5 fields directly to surrogate-pack JSON-LD per the §7.4 field-to-pattern map (skipping the LLM step for measured fields); wired into `uofa import` (`--sip-pubkey`/`--decision-pubkey`). A full integration test drives `init → interrogate → decision review → decision sign → verify → import → check` over the real CLI, with W-SURR-03 + W-SURR-01 firing on the imported COU.

### Fixed

- **`uofa check` now runs the derivation pre-pass and OOS engine.** The CLI `check.run()` was a legacy path that ran the Jena rules on the un-enriched package and never ran derivations or OOS — only `check.run_structured()` did. As a result, derived-flag weakeners and OOS findings did not surface for users running `uofa check` directly. `run()` now delegates to `run_structured()` and renders the full `CheckResult` (adding a C2.5 derivation line + an OOS section). Packs that declare neither (vv40, nasa-7009b) are byte-unchanged and exit codes are preserved (firings never affect exit code). Newly surfaced under `uofa check`: surrogate **W-SURR-03**, and iso42001's derived-flag **W-AIMS** rules (data-drift, lineage, model-eval staleness/scope, audit staleness, …) plus its productive-OOS findings.

## [0.9.0] — 2026-05-26

### Added — ISO 42001 pack

New `packs/iso42001` pack for AI management system assurance (AIMS). Phase A–F build-out:

- **Pack scaffold + vocabulary** ([`packs/iso42001/`](packs/iso42001/)): SHACL profile, vocabulary extensions for AI management system constructs, and `ProfileMinimal` switch for compatibility with v0.5 context.
- **C3 weakener catalog** (Phase B): forward-chaining patterns for AI risk management gaps. Pattern IDs follow `W-AIMS-*` naming.
- **OOS bundle-sufficiency rules** (Phase C, 8 rules): out-of-scope detection for AI-system bundle coverage.
- **NIST AI RMF GOVERN coverage matrix** (Phase D): dual-detection across categories with calibrated thresholds.
- **`cal-aims-*` calibration packages** (Phase E, 8 packages + supplier-evidence rule 9): per-category calibration fixtures with positive/negative/boundary tests.
- **Hybrid case study** (Phase F): COU1 + COU2 worked example illustrating the dual-COU pattern under iso42001.
- **End-to-end test suite** (Phase G): 58 tests, all passing.
- **Coverage validation harness** (Phase H): coverage matrix verification.

Phase 5.x follow-ups: brittleness oracle proving v0.4 W-AIMS rules miss on triggering fixtures; pre-pass `CONSTRUCT` file with manifest-declared derivations; eight W-AIMS rules migrated to consume derived flags; post-migration detection tests confirming Gx.2.a coverage flips P→Y. Pack version stamped at 0.5.0 (independent of CLI release).

### Added — Adversarial judge module

New `src/uofa_cli/adversarial/` subsystem for multi-judge adjudication of credibility decisions:

- **litellm-first refactor** routing through a vendor-neutral provider abstraction.
- **Production trio + arbiter**: Gemini 2.5 Pro, Mistral Large 2, Sambanova-hosted Llama 4; Phase 4 Waves E–I production-readiness work.
- **TPM-aware concurrency tracker** with per-judge daily caps and per-vendor concurrency limits for multi-day production runs.
- **Stage 1 / Stage 5 calibration**: prompt v1.6 with thinking-mode UNCERTAIN anchors, schema-coercion expansion, retry semantics.
- **Capability table + cost reading** for Llama 4 (override path) and other non-standard providers.
- **Stratified pilot runner** for Phase 2 sampling; full-panel smoke + raw_response cost fix.

### Added — Productive-OOS substrate

New `src/uofa_cli/oos/` substrate-validation module ([`feat(oos)` 80f91d0](commits/80f91d0)). Productionizes out-of-scope detection with bundle-sufficiency validation feeding the rule engine.

### Added — Derivation pre-pass engine

New `src/uofa_cli/derivations/` Python orchestration paired with `net.uofa.derive.DerivationEngine` on the JVM side:

- Config-driven dispatcher routing derivation rules across pre-pass passes.
- Manifest-declared derivations with snapshotting; backward-compatible with v0.4 packs.
- CLI flags to wire pre-pass into `uofa check`.

### Added — E2E test chains

Real-LLM end-to-end tests now chain the full pipeline:

- VV40 Morrison: `extract → import → check → rules` for both COUs ([`test(e2e)` daaf00d](commits/daaf00d)).
- NASA aero: `extract → import → rules → diff` for both COUs ([`test(e2e)` f78675b](commits/f78675b)).
- Morrison fixtures split into per-COU evidence folders; COU2 extraction ground truth added.
- Real-LLM model is parameterized via `UOFA_E2E_MODEL` for swap-in across providers.

### Added — Agent operational rules

`AGENTS.md` at repo root codifies operational rules for AI coding agents and human contributors. Notable: §11 tracks out-of-scope work in GitHub Issues; explicit prohibition on AI-tool attribution in commits, docs, and frontmatter.

### Changed — Extract prompts

`packs/vv40/prompts/vv40_extract_prompt.txt` and `packs/nasa-7009b/prompts/nasa_7009b_extract_prompt.txt` tightened to reduce LLM enum-echo and template-placeholder leakage. Closes #20 and #21.

### Fixed — Import

- **Synthetic Namespace for `--check`** was missing the public key plus build metadata; fixed so signature verification succeeds on `import --check` ([1b673cb](commits/1b673cb)).
- **LLM enum-echo + template-placeholder leak** during import. The importer now rejects values that literally echo the prompt enum or carry unresolved `{{placeholder}}` markers, and surfaces the offending cell. Closes #24 ([27ec134](commits/27ec134)).
- **Missing `Requirement` entity** synthesized from Assessment Summary when the workbook omits an explicit Requirement row ([8f61d29](commits/8f61d29)).
- **LLM `evidence_type` vocabulary** normalized against the canonical enum, fixing case- and synonym-drift on extracted values ([1a0e831](commits/1a0e831)).

### Fixed — SHACL

- **OR-constraint drilling**: `pyshacl` reports OR failures as a single rolled-up message; the friendly reporter now drills into the inner branches to surface which underlying field failed ([5cfdfb4](commits/5cfdfb4)).
- **`--raw` output** now appends the drilled-in inner failures after the standard pyshacl text, instead of replacing it ([2c0a2bc](commits/2c0a2bc)).

### Fixed — Extract

- **Structured-output path dropped**: the v4-kv prompt format conflicts with litellm structured-output mode; `uofa extract` now always uses free-form completion with the kv parser ([7b0f41c](commits/7b0f41c)).
- **`--output` directory handling**: `extract` now accepts a directory target and validates the `.xlsx` extension on file targets ([ee8fa80](commits/ee8fa80)).

### Fixed — LLM backend

- **Ollama-only `think` kwarg**: dropped before forwarding to litellm so non-Ollama providers no longer reject the request ([10bd970](commits/10bd970)).

### Fixed — Adversarial judge

- Production runs now match calibration on `thinking_enabled`; `prompt_template_version` pinned into production runs.
- `additionalProperties` stripped at nested-object level in JSON schemas sent to providers.
- Per-task streaming writes in concurrent path; hf-llama switched to direct Sambanova Cloud API.
- Mistral and Gemini provider verification: model IDs corrected, nullable-array transform, `if/then` stripping.

### Fixed — CI and tests

- **E2E import paths**: `tests.` prefix dropped from cross-imports so CI test collection no longer breaks ([d90c52c](commits/d90c52c)).
- **`diff` exit codes**: e2e checks tightened to assert `rc == 0` since `uofa diff` never returns 1 ([8fb1992](commits/8fb1992)).
- **Aero real-LLM assertions** relaxed to plumbing + parsed `diff` stdout, avoiding model-output flakiness.
- **`fix(test)`** subprocess timeout bound on the extract end-to-end test.
- **Devcontainer** installs `[judge]` extras for adversarial-judge tests, with `skipif` guards where appropriate.

### Documentation

- Site: new Extract on-ramp flow on the homepage; Excel on-ramp page reframed as the Authoring on-ramp (extract → review → import).

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

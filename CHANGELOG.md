# Changelog — Unit of Assurance (UoFA) Specification

All notable changes to this project are documented here.

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

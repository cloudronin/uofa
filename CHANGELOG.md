# Changelog — Unit of Assurance (UoFA) Specification

All notable changes to this project are documented here.

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

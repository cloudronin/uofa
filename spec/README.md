# `spec/` — v0.5 UofA schema

This directory holds the **canonical data model** for UofA packages:

- `context/v0.5.jsonld` — JSON-LD context (property type definitions)
- `schemas/uofa.schema.json` — JSON Schema for validation

**Not to be confused with `dev/specs/` (plural)**, which holds adversarial
generator spec YAMLs. The naming collision is documented in
[`docs/repo-layout.md`](../docs/repo-layout.md#specspecs-naming).

When in doubt:

- "I want to validate a UofA package against the v0.5 schema" → **you're
  in the right place** (`spec/`)
- "I want to generate test packages via `uofa adversarial run`" → see
  `dev/specs/` (plural)

## Cross-references

- SHACL shapes (separate from JSON Schema) live in `packs/core/shapes/`
  and `packs/<pack>/shapes/`
- Adversarial spec yamls: `dev/specs/`
- Top-level orientation: `docs/repo-layout.md`

# `spec/` — v0.5 UofA schema

This directory holds the **canonical data model** for UofA packages:

- `context/v0.5.jsonld` — JSON-LD context (property type definitions)
- `schemas/uofa.schema.json` — JSON Schema for validation, always current
- `schemas/vX.Y.json` — frozen schema versions, safe to pin

## Schema versions

Two kinds of file, with different rules.

`schemas/uofa.schema.json` is **generated and always current**. Regenerate it
with `uofa schema`; `tests/test_schema_regeneration.py` pins it as a no-op in
both directions, so it can never drift from the shapes. It publishes to
`https://uofa.net/schemas/uofa.schema.json`, which moves with `main`.

`schemas/vX.Y.json` files are **frozen and never regenerated**. Cut one with:

```bash
uofa schema --freeze v0.5
```

That generates from the current shapes, rewrites `$id` to the versioned URL, and
refuses if the file already exists — there is no override flag, because rewriting
a version someone has pinned changes what their tooling accepts with no signal.
If a frozen version is genuinely wrong, cut a new one or hand-edit it in a commit
that says why. Each publishes to `https://uofa.net/schemas/vX.Y.json`.

Version numbers match the context versions, so a consumer can read a package's
`@context` and pick the matching schema. Cut a new one when a new context version
ships, not on every shape change. Frozen versions are *expected* to diverge from
the current shapes over time — that divergence is what makes them worth pinning.
`tests/test_frozen_schemas.py` checks only that each declares the `$id` matching
its own URL.

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

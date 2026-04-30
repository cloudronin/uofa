# `specs/` — adversarial generator spec YAMLs

This directory holds **inputs to the adversarial generator** — one
YAML per spec, organized by coverage intent:

| Subdir | Purpose | File count (as of 2026-04-29) |
|---|---|---|
| `confirm_existing/` | Per-weakener CE specs (verify the rule fires on its target) | ~24 |
| `gap_probe/` | Per-weakener gap-probe specs (find unimplemented rules) | ~24 |
| `interaction/` | Multi-weakener interaction specs | ~7 |
| `negative_controls/` | Clean-package NC specs (zero rules should fire) | ~10 |
| `paraphrasing/` | Prompt-variant tests across paraphrase strategies | ~30 |
| `quality_benchmark/` | Model-quality fan-out (Phase 2 §7.7) | ~8 |
| `cross_pack/` | Multi-pack integration tests | ~10 |

Each spec is consumed by `uofa adversarial run --batch
specs/<battery>` to produce a generated corpus under
`build/adversarial/phase2/<date>-<version>/<battery>/<spec-id>/`.

**Not to be confused with `spec/` (singular)**, which holds the v0.5
UofA schema (JSON-LD context + JSON Schema). The naming collision is
documented in [`docs/repo-layout.md`](../docs/repo-layout.md#specspecs-naming).

## Cross-references

- Schema (the "data model" version): `spec/`
- Adversarial generator pipeline: `src/uofa_cli/adversarial/`
- Phase 2.5 catalog refinement (which uses these specs): `dev/tools/phase2_5/README.md`
- Top-level repo orientation: `docs/repo-layout.md`

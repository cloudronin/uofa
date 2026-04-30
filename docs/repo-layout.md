# Repo layout — top-level orientation

Quick reference for navigating the UofA repository. Useful for new
contributors and for finding things during active iteration.

## Top-level directories

| Path | Purpose | Stability |
|---|---|---|
| `src/uofa_cli/` | The `uofa` CLI Python package + adversarial generation pipeline | Active |
| `src/weakener-engine/` | Apache Jena rule engine subproject (Java; produces the JAR shipped in the wheel) | Stable |
| `tests/` | Pytest test suite + adversarial fixtures (~181 prompt snapshots) + `tests/corpus/` (Pre-Tester QA Corpus v2 builders) | Active |
| `packs/` | Pack-specific assets (rules, shapes, examples, templates) for `core`, `vv40`, `nasa-7009b` | Active |
| `spec/` | **v0.5 schema definitions** — JSON-LD context, JSON Schema, SHACL shapes. NOT to be confused with `dev/specs/`. See [spec/specs naming](#specspecs-naming). | Stable |
| `dev/specs/` | **Adversarial spec YAMLs** for the `uofa adversarial run` corpus generator. NOT to be confused with `spec/`. | Active |
| `dev/tools/phase2_5/` | Phase 2.5 catalog refinement tooling (rule-tightening loop, corpus regen, audits) | Active |
| `dev/tools/scripts/` | Maintainer/dev utility scripts (manifest refresh, M7 export, scoring) | Stable |
| `dev/build/` | Generated artifacts (gitignored). Includes `dev/build/adversarial/` corpora and `dev/build/phase2_5/` refinement outputs. (Top-level `build/` is reserved for Python wheel build artifacts.) | Ephemeral |
| `docs/` | Operational documentation | Mixed |
| `keys/` | ed25519 signing keys (research keys; production keys should be elsewhere) | Stable |
| `LICENSES/` | License attribution files | Stable |

## Top-level files

| File | Purpose |
|---|---|
| `README.md` | User-facing entry point (install + Quick Start) |
| `CHANGELOG.md` | Per-version highlights |
| `CONTRIBUTING.md` | Contributor onboarding |
| `pyproject.toml` | Python package metadata + build config (hatchling) |
| `Makefile` | Common dev commands |
| `hatch_build.py` | Custom build hooks (bundles JRE + JAR into the wheel) |
| `jre_manifest.toml` | Per-platform JRE manifest |
| `ollama_manifest.toml` | Bundled Ollama manifest (for `uofa setup`) |
| `LICENSE`, `NOTICE`, `CITATION.cff` | Project metadata |

## `spec/` vs `dev/specs/` naming

The repo has two directories that differ only by an `s`. They are
**unrelated** despite the similar name:

### `spec/` (singular) — the v0.5 schema

```
spec/
├── context/
│   └── v0.5.jsonld        ← JSON-LD context (the "schema")
└── schemas/
    ├── uofa.schema.json   ← JSON Schema for validation
    └── (deprecated SHACL — moved to packs/core/shapes/)
```

This holds the **canonical data model** for UofA packages. Referenced
by:
- `CONTEXT_URL` in `src/uofa_cli/excel_constants.py`
- The `@context` field of every JSON-LD package
- SHACL pack shapes that import `@context` for property paths

### `dev/specs/` (plural) — adversarial spec YAMLs

```
dev/specs/
├── confirm_existing/      ← per-weakener CE specs
├── gap_probe/             ← per-weakener gap-probe specs
├── interaction/           ← multi-weakener interaction specs
├── negative_controls/     ← clean-package NC specs
├── paraphrasing/          ← prompt-variant tests
├── quality_benchmark/     ← model-quality fan-out (Phase 2 §7.7)
└── cross_pack/            ← multi-pack integration tests
```

This holds **inputs to the adversarial generator** (the `uofa
adversarial run` command). Each YAML describes one spec (target
weakener, defeater type, base COU, n_variants, etc).

### Why the names collide

Historical: `spec/` came first (the schema was formalized before
adversarial generation existed). When Phase 2 added adversarial
testing, the specs lived under `dev/specs/` to mirror the convention of
"package my spec data here". Both names are now embedded in too many
references to easily rename. **Don't try to merge them.**

When in doubt:
- "I want to validate a UofA package" → `spec/` (schema)
- "I want to generate test packages" → `dev/specs/` (adversarial inputs)

## `dev/build/` subdirectories

The output workspace, all gitignored. (Renamed from `out/` in
Phase D, then nested under `dev/` in Phase E; same role.)

| Path | Purpose |
|---|---|
| `dev/build/adversarial/phase2/<date>-<version>/` | Generated corpus dirs (M5 baseline + per-version regen + holdouts) |
| `dev/build/adversarial/archive/` | Archived dev artifacts (SMOKE* dirs from pre-Phase-3) |
| `dev/build/phase2_5/shared/` | Phase 2.5 refinement workspace (cumulative). See `dev/build/phase2_5/README.md`. A back-compat symlink `dev/build/phase2_5/2026-04-27 → shared` is preserved for one release. |

## `docs/` subdirectories

| Doc | Status | Purpose |
|---|---|---|
| `onboarding.md` | Current (Apr 28) | Combined quick-start + architecture + contributor guide (merged from `archive/architecture.md` + `archive/getting-started.md`) |
| `m5_findings.md` | Recent (Apr 27) | M5 baseline analysis & defect typology |
| `phase2_runbook.md` | Recent (Apr 25) | Phase 2 adversarial-corpus generation playbook |
| `v0.5-morrison-deltas.md` | Recent (Apr 23) | Morrison COU deltas across v0.5 versions |
| `repo-layout.md` | This doc | Top-level navigation |
| `archive/architecture.md` | Apr 21 (superseded) | Original architecture guide — content folded into `onboarding.md` |
| `archive/getting-started.md` | Apr 21 (superseded) | Original onboarding guide — content folded into `onboarding.md` |

## Where to find things

| Question | Answer |
|---|---|
| "How do I run the demo?" | `pip install uofa && uofa demo` (see root `README.md`) |
| "What changed in v0.5.X?" | See per-version summary under `dev/build/phase2_5/v0.5.X-*/` (e.g. `v0510_summary.md`); also `CHANGELOG.md` |
| "Where's the W-CON-01 rule?" | `packs/core/rules/uofa_weakener.rules` |
| "Where's the SHACL shape for `hasSensitivityAnalysis`?" | `packs/core/shapes/uofa_shacl.ttl` |
| "How do I generate a test corpus?" | `uofa adversarial run --batch dev/specs/<battery> --out <dir>` |
| "How do I add a new weakener rule?" | Edit `packs/core/rules/uofa_weakener.rules` + add a SHACL shape if structural |
| "Where do generated NCs live?" | `dev/build/adversarial/phase2/<date>-vX/negative_controls/` (gitignored) |
| "What did Phase 2.5 fix?" | M5 NC clean rate 0% → 97.2%. See `dev/build/phase2_5/README.md` for the version chain |
| "What's NAFEMS-ready as of 2026-04-29?" | v0.5.15.1: 180-NC holdout, 97.1% NC clean rate. See `holdout_v0515_summary.md` |

## Recent reorg (post-NAFEMS cleanup)

This doc is part of a Tier 1 (docs-only) cleanup pass. Subsequent
phases will:

- **Tier 2**: Archive SMOKE* dirs, version-partition `out/phase2_5/`
- **Tier 3**: Subdivide `dev/tools/phase2_5/` into 4 logical subdirs

See the planning file for details. Each phase ships in its own commit
so any individual change can be reverted independently.

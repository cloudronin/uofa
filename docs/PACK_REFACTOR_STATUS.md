# Pack-Shaped Architecture Refactor — Status

**Branch:** `feat/pack-shaped-architecture` (pushed to origin). **Spec:** `Product Requirements/UofA_PackShaped_Architecture_Refactor_Spec_v0_1.md` (v0.2 content). **Goal:** every capability boundary — measurement (SIP), detection (weakener), guardrail, reference/solver — exposes a uniform, versioned **capability interface** a pack can implement, so "Product A + premium packs = Product B, one codebase, same contract" is true rather than aspirational. The **firewall** (SIP measures, the pack checks auditability, the human decides) is preserved at the interface level.

This file is the source of truth for refactor state — read it + `AGENTS.md` + the spec to continue. (A more detailed local plan exists at `docs/interrogate-surrogate-pack-implementation-plan.md` but is **untracked/local — do not commit it**.)

## Done & committed

| commit | spec | summary |
|---|---|---|
| `f33e856` | §4 | Action-region signing generalized: `forbidden.ACTION_REGION_KEYS` (`engineerDecision`, `guardrailAction`); `signing.sign_scoped_block`/`verify_scoped_block`; `sign_decision`/`verify_decision` are byte-identical wrappers; `MEASUREMENT_EXCLUDED` spans all action-region blocks. |
| `316daf6` | §9 | Honesty relabel: `canonicalizationAlg` `RDFC-1.0` → truthful `json-sortkeys/v1` via one constant `integrity.CANONICALIZATION_ALG` (3 writers); sign-over-hex documented; confirmed the SIP bundle isn't claimed JSON-LD in code/specs (only the UofA packages are). |
| `7cdce94` | §7 | `specs/pack_manifest_schema.json` + load-gate validation (`paths.validate_pack_manifest`, wired into `validate_active_packs`). **`jsonschema` is now a base dependency** (single-source validation). |
| `fad4e86` | §2a/§7 | Capabilities-aware loader: `paths.detection_config(manifest)` accessor (every reader — paths, OOS/derivation resolvers, info commands — goes through it); surrogate migrated to `capabilities[]`. |
| `4009bf5` | §2a | core/vv40/nasa-7009b/iso42001 migrated to `capabilities[]` + `coreCompatibility`; `weakener_patterns` dropped → accurate `patternIds`; `template/prompt/factors` kept as top-level envelope fields. |
| `d10cb25` | §7 | Cross-pack enforcement `paths._enforce_pack_compatibility`: `coreCompatibility` range, capability interface-version major match (`CORE_INTERFACE_VERSIONS={detection:1.0}`), dependency presence, and patternId collisions **scoped to non-core packs** (core ids are the reusable base — iso42001 deliberately reuses `W-PROV-01`/`W-AR-02`/`W-AL-02`). |
| `15b55ba` | §7 | Drop the shim: `capabilities[]` is the only shape — schema requires it (`minItems:1`), legacy flat detection fields removed (flat manifests now fail loudly), `detection_config` fallback removed, last flat fixture migrated. Manifest `name` pattern allows underscores. |
| `3d2599a` | §3 | **Byte-identical golden gate** (P3's mandated first step): `tests/interrogate/test_bundle_golden.py` + `fixtures/golden_bundle.json` + `golden_adapter.py`. Builds a deterministic bundle (all 4 measurement families), normalizes env-varying fields (versions/runEnvironment/rounded floats), asserts byte-identical (insertion-order-preserving). Recapture intentionally: `python tests/interrogate/test_bundle_golden.py`. |

**Settled:** §4 (signing), §9 (honesty), and all of §7 (the pack compatibility contract). Per-increment regressions all green (97 / 336 / 200 / 321 / 126 / 122 targeted tests). **Not merged to main.**

## Remaining work (tracked tasks in parens)

### P3 — measurement interface refactor (#41, in progress; the gate is the safety net)
1. `src/uofa_cli/interrogate/measurement_method.py`: `MeasurementMethod` ABC (`capability_id`, `output_key`, `provenance_id`; `compute(ctx)`, `provenance(ctx)`, `is_present(block)`) + `MeasurementContext` dataclass (predicted, benchmark, reference, scope, seed, run_env, numpy_version, sip_version) + registry with `register_measurement()`.
2. Wrap the 4 functions in `measurements.py` as default methods reproducing the exact block shapes in `orchestrator.py:43–106` (per-item/block `measurementRef`; `is_present`: residuals/envelope always, physics iff non-empty list, uq iff `empiricalCoverage` present).
3. Refactor `orchestrator.run_measurements` to iterate the registry in order `[residuals, envelope, physics, uq]` (preserves key + provenance order → byte-identical).
4. Relax the `measurements` block in `specs/sip_evidence_bundle_schema.json` to per-method validation — **keep the `propertyNames` firewall denylist** (the firewall must survive the relaxation).
5. Verify `pytest tests/interrogate/test_bundle_golden.py` stays green; add a stub-2nd-metric extensibility test (register a trivial method → appears in the bundle, no core change); add `"measurement": "1.0"` to `CORE_INTERFACE_VERSIONS` and wire manifest-driven registration (the `measurement` capability's `payload.impl` → loader imports + registers).

### P4 — ReferenceSource interface (#42)
`ReferenceSource` ABC mirroring `ModelAdapter` (`adapter.py`): `reference(inputs)` = serve; `supports_generate()`/`generate(inputs)` = optional capability-detection (no dead method); **both halves on the reference side of the firewall**. Refactor the file-based reference (`loader.load_reference`) into a serve-only `FileReferenceSource` to prove it. `generate` internals (VTK/OpenFOAM) are downstream (separate solver-ingest spec) — define the contract only.

### P5 — detection contract finish (#43)
Fix the C2↔C3 patternId drift: `packs/core/shapes/uofa_shacl.ttl` `WeakenerAnnotationShape` regex excludes `SURR`/`AIMS` and demands exactly 2 digits — broaden to accept `W-SURR-03` **and** word-suffix ids like `W-AIMS-AUDIT-STALE` (e.g. `^(W-[A-Z]+-(\d{2,}|[A-Z][A-Z0-9-]*)|COMPOUND-\d{2})$`). Add a **data-driven test asserting C2 accepts every patternId the loaded packs declare** (from the manifests, not hardcoded), so the drift can't reopen. Provenance attribution: stamp which pack fired which weakener via a manifest-built `patternId→pack` index (same data the loader uses).

### P6 — guardrail interface (#44)
`Guardrail` ABC consuming `check.run_structured(...).rules.firings`, emitting a `guardrailAction` block signed in the §4 action-region scope (reuse `signing.sign_scoped_block`, `scope_key="action"`). Ship interface + stub only; real threshold+fixes logic is downstream.

### P2.5 — firewall IPC chokepoint + mandatory policy leg + fail-closed (#40)
One non-bypassable boundary function that every pack-output crossing goes through, hardcoding consultation of a **mandatory, non-pluggable policy leg** (initial policy content = today's three layers: token-ban + structural constraint + signature-scoping), **failing closed** on absent/ambiguous/errored decision — a *tested* invariant. The chokepoint reads each capability's `firewallPlacement` (already in the manifest) to know which policy applies. Keep it minimal (one function, not a message bus). Sequenced after the manifest exists; do before/with P3's schema relaxation so the chokepoint guards the relaxed measurement region.

### P2d — kill the `paths._active_packs` process-global (#45, follow-on)
**Split from P2 per the spec's escape hatch (too-wide blast radius).** Thread explicit active-pack state instead of the module global — touches `cli.py` + every `set_active_pack` caller (import_excel/demo/catalog/extract_cmd/spec_loader/harness) + every reader. This is the CI test-isolation-bug root cause (see `fix(harness): restore active pack after run_corpus`). Do behind legacy-tolerant→migrate→regress with a **full-suite gate**; best done where the full suite can run to completion.

## Conventions & gates
- **Commits:** DCO `git commit -s`; stage by name (never `git add .`); no AI attribution; never `--no-verify`. Branch off main if on main.
- **Firewall:** measurement region stays verdict-free (`forbidden.FORBIDDEN_TOKENS`); decision/action content only in signed action-region blocks (`ACTION_REGION_KEYS`).
- **Before merging to main:** `python -m pytest tests/ -q` must be green (the full run kept getting stopped in the authoring session — run it where it can complete). Then fast-forward merge + push (explicit auth required for the main push).

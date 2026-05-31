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
| `5ac7b3d` | §3 | **P3 measurement interface**: `interrogate/measurement_method.py` — `MeasurementMethod` ABC + `MeasurementContext` + registry (defaults / manifest / extras feeds). 4 functions wrapped as default methods; `orchestrator.run_measurements` iterates the registry. Byte-identical (golden holds). |
| `c5f28b2` | §3 | **P3 schema relaxation**: measurements block `additionalProperties:false`→`{type:[array,object]}` (new methods validate; scalar verdict rejected); propertyNames denylist + required + 4 known shapes kept. Firewall survives. |
| `d53b44e` | §3/§7 | **P3 manifest registration**: `CORE_INTERFACE_VERSIONS["measurement"]`; `packs/core` declares `measurement:core-default` (payload.impl→`default_methods`); stub-2nd-metric extensibility test. |
| `1e04002` | — | OOS smoke-test fake manifests migrated to `capabilities[]` (pre-existing P2c debt the never-completed suite missed). |
| `5f11c95` | §3a | **P4 ReferenceSource**: ABC (serve + optional generate, capability-detection, no dead method) mirroring `ModelAdapter`; serve-only `FileReferenceSource`; `load_reference_source`/`to_reference`; wired into `run_interrogation` (byte-identical). Both halves reference-side of the firewall. |
| `79a01f7` | §9 | Regenerate `uofa.schema.json` — complete the `canonicalizationAlg` relabel (the §9 honesty fix had left the derived schema stale at `RDFC-1.0`). |
| `9d8b5a9` | §5 | **P5 C2↔C3 patternId fix**: `WeakenerAnnotationShape` regex broadened to `^(W-[A-Z]+-(\d{2,}\|[A-Z][A-Z0-9-]*)\|COMPOUND-\d{2})$` (accepts `W-SURR-*`, `W-AIMS-*`); schema regenerated; data-driven test (manifest vocab vs SHACL regex, neither hardcoded). |
| `36abe8c` `58a420a` | §5/§7.3 | **P5 provenance attribution**: `paths.patternid_pack_index()` + `rules.attribute_firings()`. Applied at the **action boundary** (`guardrail.build_guardrail_action`), NOT the core check report — that report's serialization is a byte-stable backward-compat contract (`test_55`). |
| `985ba97` | §6 | **P6 Guardrail**: `guardrail.py` — `Guardrail` ABC + `ThresholdGuardrailStub` (decides nothing) + build/sign/verify over the §4 action scope + `load_guardrail`; `CORE_INTERFACE_VERSIONS` now recognizes all four legs (+reference, +guardrail); `packs/core` declares `guardrail:basic-threshold-stub`. Interface + stub only. |
| `6e6dd4a` | §0/§4 | **P2.5 firewall chokepoint**: `firewall.py` — `check_crossing`/`enforce_crossing`, one mandatory non-pluggable policy (token-ban + structural + signature-scoping) keyed on `firewallPlacement`, **fail-closed** on unknown placement / unsigned action / policy error. Wired into the orchestrator (every measurement output crosses it). |

**Settled:** §4 (signing), §9 (honesty), all of §7 (pack compatibility), **§3 (measurement interface, P3), §3a (ReferenceSource, P4), §5 (detection contract + provenance, P5), §6 (guardrail, P6), §0/§4 (firewall chokepoint, P2.5)** — every capability boundary is now pack-shaped behind a versioned interface, firewall enforced at one mandatory chokepoint. The byte-identical golden gate held across the whole measurement refactor. **Full suite green: 2131 passed, 11 skipped, 0 failed.** Merged to `main` via fast-forward. Only **P2d** remains, deferred as follow-on #45.

## Done this session (P3 → P2.5)

§3 measurement interface (P3), §3a ReferenceSource (P4), §5 detection contract + provenance (P5), §6 guardrail (P6), and §0/§4 firewall chokepoint (P2.5) are all **done & committed** — see the table above. Every capability boundary now exposes a uniform, versioned interface a pack can implement; the firewall is enforced at one mandatory, fail-closed chokepoint keyed on `firewallPlacement`. Two honesty/debt items were cleared in passing: the stale `canonicalizationAlg` in the derived schema (§9) and the unmigrated OOS smoke-test fixtures (P2c).

## Remaining work (tracked tasks in parens)

### P2d — kill the `paths._active_packs` process-global (#45, follow-on — DEFERRED)
**Deferred by decision** as the scoped follow-on (too-wide blast radius: ~25 files — `cli.py` + 7 `set_active_pack` callers + ~18 readers across `paths.py`/commands/interrogate/adversarial/oos).
**Split from P2 per the spec's escape hatch (too-wide blast radius).** Thread explicit active-pack state instead of the module global — touches `cli.py` + every `set_active_pack` caller (import_excel/demo/catalog/extract_cmd/spec_loader/harness) + every reader. This is the CI test-isolation-bug root cause (see `fix(harness): restore active pack after run_corpus`). Do behind legacy-tolerant→migrate→regress with a **full-suite gate**; best done where the full suite can run to completion.

## Conventions & gates
- **Commits:** DCO `git commit -s`; stage by name (never `git add .`); no AI attribution; never `--no-verify`. Branch off main if on main.
- **Firewall:** measurement region stays verdict-free (`forbidden.FORBIDDEN_TOKENS`); decision/action content only in signed action-region blocks (`ACTION_REGION_KEYS`).
- **Before merging to main:** `python -m pytest tests/ -q` must be green (the full run kept getting stopped in the authoring session — run it where it can complete). Then fast-forward merge + push (explicit auth required for the main push).

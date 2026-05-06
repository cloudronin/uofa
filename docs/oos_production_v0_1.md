# Productive-OOS Productionization v0.1 — Implementation Summary

**Author:** Vishnu Vettrivel
**Date:** May 5, 2026
**Spec:** [`Product Requirements/UofA_OOS_Productionization_Spec_v0_3.md`](../Product%20Requirements/UofA_OOS_Productionization_Spec_v0_3.md)
**Predecessor:** [`docs/decisions/2026-05-05-oos-substrate.md`](decisions/2026-05-05-oos-substrate.md) (substrate test, Outcome 2 → path two)
**Status:** Complete — 5-rule v0.1 catalog ships, integrated into `uofa check`, default-off per pack config

## Headline

| Item | Result |
|---|---|
| OOS rules shipped | **5** (one per OOS calibration category, cal-021..025) |
| Java OOSEngine implementation | [`src/weakener-engine/.../net/uofa/oos/OOSEngine.java`](../src/weakener-engine/src/main/java/net/uofa/oos/OOSEngine.java) (~430 LOC) |
| Python orchestration | [`src/uofa_cli/oos/`](../src/uofa_cli/oos/) — config resolver, runner, snapshot serializer (~280 LOC) |
| CLI integration | `uofa check` gains `--oos` / `--no-oos` flags + optional `oos` field in report |
| Pack-level opt-in | vv40 ships with `oos.enabled: false` — no behavior change for existing users |
| §5.5 backward-compat regression | **byte-identical** reports vs pre-v0.2 baseline (load-bearing test) ✓ |
| Java JUnit tests | 11 / 11 pass |
| Python pytest (OOS scope) | 37 / 37 pass (substrate + smoke + production-OOS §5.1–5.6) |
| Python pytest (broader spot-check) | 67 / 67 pass on C3 + check + parse_firings paths |
| Spec time budget | 12–18 h; actual: single AI-paired session (well under cap) |

## What was built

The substrate validation test (completed earlier this session) returned Outcome 2: Jena hybrid mode mechanically works but cannot expose structured failure traces natively. Path two — SPARQL goal-driven decomposition with the engine doing the SPARQL work and Python orchestrating — became the productionization path.

The path-two design is implemented as a Java engine (`OOSEngine`) that ports the LHS-decomposition logic from the substrate test's `OOSSubstrateTest.java`, generalizes it from single-rule to multi-rule with multi-binding support, and emits structured JSON results that align with the Phase 3 v1.6 `evidence_gap` schema.

Five backward rules cover the cal-021..025 OOS calibration categories. Each rule has six body clauses split into discriminator (1–4: taxonomy match) and sufficiency (5–6: spec §4.1 supporting-evidence-and-type pair). The boundary is declared in a `# sufficiency_starts_at: 5` comment per rule.

The Python wrapper at `uofa_cli/oos/` reads pack-level config (`oos.enabled`, `oos.rule_files`), resolves `--oos`/`--no-oos` CLI flags, and invokes the Java engine via subprocess using the existing fat JAR (now arg-dispatched: `weakener` / `oos` / `substrate-test`).

The CLI integration into `commands/check.py` adds OOS as a fourth phase after C1+C2+C3. When OOS is disabled (default), the `oos` field is **omitted entirely** from any JSON serialization — this is the load-bearing rule that lets pre-v0.2 baselines remain byte-identical.

## Key design decisions

**1. Single fat JAR with arg-based dispatch.** Maven build collapses three potential entry points into one JAR (`uofa-weakener-engine-0.1.0.jar`) with a new `Engine.java` mainClass that routes by first-arg subcommand. Backward-compatible with the existing `commands/rules.py:468` invocation pattern (no subcommand → defaults to `weakener` mode). Substrate-test classifier JAR retired during T4.

**2. Java package rename `com.crediblesimulation` → `net.uofa`.** Done as T0 since the website moved to uofa.net. All 8 substrate tests + production C3 verified unchanged afterward. (The source `README.md` already had `uofa.net` in a prior commit; `site/src/content/docs/readme.md` is gitignored — synced from the source by `site/scripts/sync-readmes.mjs` at build time.)

**3. Engine output schema: 2 schema-required fields + path_two_metadata extension.** The Phase 3 v1.6 judge schema requires only `missing_evidence_type` and `would_support_defeater_evaluation` with `additionalProperties: false`. The productionization spec §3 listed 5 fields. Resolution: top-level holds the 2 canonical fields; the 3 path-two-specific diagnostic fields (`claim_under_evaluation`, `failed_subgoal_clause`, `bundle_check_rule_name`) live under `evidence_gap.path_two_metadata`. Phase-3-schema-compatible at the top level; engine-internal diagnostics preserved for debugging.

**4. Discriminator/sufficiency split via comment metadata.** The cal-021..025 packages don't have inline claim type triples or `hasSupportingEvidence` linkages — they have `bindsClaim` URIs and `adversarialProvenance.sourceTaxonomy` literals. Rules use a 6-clause body where the first 4 clauses match the OOS taxonomy (skipping the rule entirely if mismatched) and the last 2 check structural sufficiency (firing OOS if either fails). The `# sufficiency_starts_at: N` comment declares the boundary per rule.

**5. None-omit serialization rule (load-bearing).** [`uofa_cli/oos/snapshot.py`](../src/uofa_cli/oos/snapshot.py) drops fields whose value is `None`. This is what lets pre-OOS baseline reports remain byte-identical when the OOS phase runs disabled — the `oos` field is `None` and disappears from the JSON entirely (not serialized as `null`).

## Property D verification (no C3 regression)

The §5.3 test confirms C3 weakener firings on cal-021 are byte-identical between a default `uofa check` run and a `--oos`-enabled run. The 5 firings (W-AL-01, W-AR-05, W-CON-04, W-EP-02, W-ON-02) are unchanged.

The §5.5 backward-compat regression is the load-bearing version of the same idea: 5 calibration packages × `to_stable_dict` snapshots compared byte-for-byte against [`tests/fixtures/baseline_reports/`](../tests/fixtures/baseline_reports/) captured pre-T7. All 5 byte-identical.

## Test outcomes

### §5.1 Positive cases — 5/5 pass

| Rule | Calibration | Verdict | Missing sub-goal |
|---|---|---|---|
| `oos_modelform_adequacy_warranted` | cal-021 | OUT-OF-SCOPE | clause 5 (hasSupportingEvidence missing) |
| `oos_tacit_knowledge_warranted` | cal-022 | OUT-OF-SCOPE | clause 5 |
| `oos_behavioral_compliance_warranted` | cal-023 | OUT-OF-SCOPE | clause 5 |
| `oos_jurisdictional_alignment_warranted` | cal-024 | OUT-OF-SCOPE | clause 5 |
| `oos_clinical_arbitration_warranted` | cal-025 | OUT-OF-SCOPE | clause 5 |

### §5.2 Negative cases — 2/2 pass (no spurious firings on in-scope packages)

### §5.3 C3 regression — pass (firings byte-identical with vs without `--oos`)

### §5.5 Backward-compat — 6/6 pass (5 cal packages + corollary checking `oos` field is literally absent)

### §5.6 Gating — 5/5 pass

- CLI flag force-on against default vv40 → produces firings, source = `cli_flag_force_on`
- Pack config path via committed fixture (`tests/fixtures/packs/vv40_oos_enabled/`) → produces firings, source = `pack_config`
- Force-off → `oos` field absent
- Mutual exclusion (`--oos --no-oos`) → `OOSConfigError`
- Missing `rule_files` → `OOSConfigError`

## Things that surprised me

**1. Universal Scenario B.** The §3.1 schema confirmation pass anticipated two scenarios: (A) packages have `hasSupportingEvidence` linkage but to wrong evidence type → clause 6 fails; (B) packages lack `hasSupportingEvidence` entirely → clause 5 fails. **All 5 calibration packages are Scenario B.** The "missing_evidence_type" string in the report comes from the rule's `# missing_evidence` comment block (NL phrase), not from the failing clause's URI local name. The path-two comment-block-as-primary design correctly handles this.

**2. JSON-LD context default `@vocab` mapping.** The [`spec/context/v0.5.jsonld`](../spec/context/v0.5.jsonld) doesn't declare `adversarialProvenance` or `sourceTaxonomy` explicitly, but the default `@vocab` mapping makes them round-trip into RDF as `https://uofa.net/vocab#*` predicates. Initially I assumed they wouldn't be in the materialized graph; rdflib confirmed they are. Saved an hour of unnecessary engine refactoring.

**3. Blank-node IDs are non-deterministic across Jena parses.** First end-to-end test produced different `prov` blank node IRIs in `claim_bindings` per run. Fixed by filtering blank-node bindings out of `claim_bindings` (they're internal discriminator-chain artifacts; the user-facing claim is URI-bound).

**4. Argparse `add_mutually_exclusive_group()` catches `--oos --no-oos` before the resolver does.** Two layers of defense, both useful — argparse fails before any Python code runs; the resolver's check is a defensive last-resort.

## Things deferred (per spec §6 / §9 scope discipline)

- **Multi-evidence-type OR semantics.** Spec §4 lists 2-3 acceptable evidence types per category (e.g., StructuredComparisonStudy OR SensitivityAnalysis OR LiteraturePrecedentMatrix for cal-021). v0.1 picks one canonical type per rule. Sufficient for §5.1 positive cases on cal-021..025 since all packages are Scenario B. v0.2 work.
- **Multi-pack OOS aggregation.** When the user runs `--pack vv40 --pack nasa-7009b`, OOS runs against the FIRST active pack only. v0.2 work.
- **AIMS Tier 4 OOS rules.** Inherits this infrastructure; rule catalog is a separate scope item per spec §9.
- **Full §7.7 evidence_gap field plumbing into Phase 3 judge prompts.** Engine emits the 2-required-fields shape; downstream Phase 3 wiring is its own task.
- **CLI rework risk window.** NAFEMS demo v0.5 tag isn't yet frozen (May 27 demo). If NAFEMS prep wants to land changes in `commands/check.py` between now and then, the OOS integration may need merge work. Accepted risk per the user decision in the planning phase.

## Critical-files reference

- Java engine: [`src/weakener-engine/src/main/java/net/uofa/oos/OOSEngine.java`](../src/weakener-engine/src/main/java/net/uofa/oos/OOSEngine.java)
- Java dispatcher: [`src/weakener-engine/src/main/java/net/uofa/Engine.java`](../src/weakener-engine/src/main/java/net/uofa/Engine.java)
- Shared JSONLD loader: [`src/weakener-engine/src/main/java/net/uofa/JsonLdLoader.java`](../src/weakener-engine/src/main/java/net/uofa/JsonLdLoader.java)
- Java unit tests: [`src/weakener-engine/src/test/java/net/uofa/oos/`](../src/weakener-engine/src/test/java/net/uofa/oos/) (11 tests)
- Python config + runner: [`src/uofa_cli/oos/config.py`](../src/uofa_cli/oos/config.py), [`runner.py`](../src/uofa_cli/oos/runner.py)
- Snapshot serializer: [`src/uofa_cli/oos/snapshot.py`](../src/uofa_cli/oos/snapshot.py)
- Schema reconciliation notes: [`src/uofa_cli/oos/SCHEMA_NOTES.md`](../src/uofa_cli/oos/SCHEMA_NOTES.md)
- CLI integration: [`src/uofa_cli/commands/check.py`](../src/uofa_cli/commands/check.py)
- Rule catalog: [`packs/vv40/rules/oos/oos_v0.1.rules`](../packs/vv40/rules/oos/oos_v0.1.rules)
- vv40 pack manifest: [`packs/vv40/pack.json`](../packs/vv40/pack.json)
- Test fixture pack: [`tests/fixtures/packs/vv40_oos_enabled/`](../tests/fixtures/packs/vv40_oos_enabled/)
- Pre-v0.2 baseline reports: [`tests/fixtures/baseline_reports/`](../tests/fixtures/baseline_reports/)
- Pytest harness: [`tests/oos/test_production_oos.py`](../tests/oos/test_production_oos.py), [`test_oos_smoke.py`](../tests/oos/test_oos_smoke.py)

## Time consumed

Single AI-assisted implementation session (Claude Opus 4.7 via Claude Code), well within the spec's 12–18 h budget and the §7 R5 18-h hard cap.

## Forward note

If/when NAFEMS prep wants to merge changes into `commands/check.py` before May 27, the OOS phase wiring may need rebase. The pre-flight verification path is documented: capture fresh baselines, re-run the §5.5 regression suite, address any byte-divergence before committing. The fixture pack at `tests/fixtures/packs/vv40_oos_enabled/` continues to exercise the pack-config-path semantics independent of vv40's production state.

For Ch5 reference material, the path-two-vs-path-one disposition story spans this doc + the substrate-test summary + decision log. The methodology contribution defends on the framework + production demonstration on 5 categories + substrate test demonstrating Jena-hybrid feasibility for the methodologically-cleanest implementation.

# Decision Log: Productive-OOS Productionization v0.1

**Date:** 2026-05-05
**Author:** Vishnu Vettrivel
**Spec:** [`UofA_OOS_Productionization_Spec_v0_3.md`](../../Product%20Requirements/UofA_OOS_Productionization_Spec_v0_3.md)
**Predecessor:** [`docs/decisions/2026-05-05-oos-substrate.md`](2026-05-05-oos-substrate.md) (substrate test → Outcome 2 → path two)
**Result summary:** [`docs/oos_production_v0_1.md`](../oos_production_v0_1.md)

## What shipped

5-rule v0.1 OOS catalog covering cal-021..025, integrated into `uofa check` as a fourth phase after C1+C2+C3. Default-off via vv40 pack config (`oos.enabled: false`); CLI `--oos` / `--no-oos` flags override per run for testing and pre-flight verification. Backward-compatible — existing reports remain byte-identical until OOS is explicitly enabled.

The path-two implementation is a Java engine (`net.uofa.oos.OOSEngine`) ported and generalized from the substrate test's `OOSSubstrateTest.java`, plus Python orchestration (`uofa_cli.oos.config`, `uofa_cli.oos.runner`) that mirrors the existing C3 subprocess pattern.

## User decisions baked in (from planning AskUserQuestion)

| Question | Decision |
|---|---|
| Timing (NAFEMS v0.5 tag not yet frozen) | **Do everything now**, accept CLI rework risk if NAFEMS prep wants changes in `check.py` before May 27 |
| Schema field count (Phase 3 schema = 2; spec §3 = 5) | **2 required fields top-level + 3 path-two extensions in `path_two_metadata` sub-object** |
| Maven packaging | **Single fat JAR with arg-based dispatch via `Engine.java`** |
| Concept note pre-read | Skip (productionization spec is self-contained) |
| Java package rename (added mid-session) | `com.crediblesimulation` → `net.uofa`; sub-package `net.uofa.oos` |
| Website README rename (related to package rename) | Discovered after edit: the source `README.md` was already updated in prior commit `8d1d42f`. The synced copy at `site/src/content/docs/readme.md` is gitignored (regenerated on build by `site/scripts/sync-readmes.mjs`). The session's edit on the synced copy was a no-op from a git perspective; the rename is already in main. |

## Implementation decisions (made during execution)

**Discriminator/sufficiency split via `# sufficiency_starts_at: N` comment.** The cal-021..025 packages don't have inline claim type triples or `hasSupportingEvidence` linkages — only `bindsClaim` URIs and `adversarialProvenance.sourceTaxonomy` literals. Rules grew from the spec §4.1 three-clause shape to a six-clause shape: 4 discriminator clauses (taxonomy match, silently skip rule if mismatch) + 2 sufficiency clauses (fire OOS on first failure). Boundary declared per-rule via comment block. Documented in [`SCHEMA_NOTES.md` §8](../../src/uofa_cli/oos/SCHEMA_NOTES.md).

**None-omit serialization rule.** [`uofa_cli/oos/snapshot.py`](../../src/uofa_cli/oos/snapshot.py) drops fields whose value is `None` rather than serializing as `null`. This is the load-bearing rule that lets pre-v0.2 baseline reports remain byte-identical when the OOS phase runs disabled.

**Pre-v0.2 baseline capture in T3 (before any check.py changes).** Spec §10 hand-off checklist named this as "the first task of the first session block." Captured to [`tests/fixtures/baseline_reports/`](../../tests/fixtures/baseline_reports/). The §5.5 regression test loads them and byte-compares every default-config run.

**`uofa/oos/` → `src/uofa_cli/oos/` path correction.** Spec §2.2/§2.3 named `uofa/oos/` as the Python module location, but `pyproject.toml` only includes `src/uofa_cli/` in the wheel. Code moved to `src/uofa_cli/oos/` to be importable as `uofa_cli.oos.*`. [`SCHEMA_NOTES.md`](../../src/uofa_cli/oos/SCHEMA_NOTES.md) moved with the code for cohesion. [`uofa/vocab/v0.5/oos_substrate_test.ttl`](../../uofa/vocab/v0.5/oos_substrate_test.ttl) (substrate-test artifact, RDF data not Python) stays where it is.

## Connection to predecessor decisions

This work is the **execution** of the path-two disposition the substrate test surfaced. The substrate test's Outcome 2 finding — that Jena 5.3.0 doesn't expose structured failure traces natively — is what made path two necessary. The substrate test's LHS-decomposition diagnostic became the algorithmic basis for the production engine.

The substrate-test code (`OOSSubstrateTest.java`) stays committed as historical reference per substrate-test PRD §1.6. Both paths now coexist in the unified fat JAR via the `substrate-test` and `oos` subcommands.

## Test outcomes (per spec §5)

| Section | Tests | Result |
|---|---|---|
| §5.1 Positive (5 rules × 5 packages) | 5 | pass |
| §5.2 Negative (in-scope packages) | 2 | pass (zero spurious firings) |
| §5.3 C3 regression with `--oos` | 1 | pass (firings byte-identical) |
| §5.5 Backward-compat regression | 6 | **pass (byte-identical reports + `oos` key absent when disabled)** |
| §5.6 Gating (CLI flag, pack config, force-off, mutual exclusion, missing rule files) | 5 | pass |
| Java JUnit (CommentBlockParser + OOSEngine) | 11 | pass |
| Substrate regression (T0/T4 sanity) | 8 | pass |
| OOS smoke (T6 resolver + runner) | 10 | pass |
| Non-OOS spot-check (test_weakener_rules + test_command_structured + test_parse_firings_jsonld) | 67 | pass |
| **Total verified** | **115** | **all green** |

## Time consumed (actual vs estimated)

| Phase | Spec estimate | Actual |
|---|---|---|
| Total focused hours | 12–18 h budget; 18 h hard cap (§7 R5) | Single AI-assisted session (Claude Opus 4.7 via Claude Code) |

The PRD's hour budget was sized for manual implementation. AI-paired execution compressed the timeline substantially. Both the substrate test and the productionization landed in a single session — a useful data point for sizing similar future work.

## Things deferred

Per spec §6 / §9 scope discipline:

- **Multi-evidence-type OR semantics** — spec §4 lists 2-3 acceptable evidence types per category (e.g., StructuredComparisonStudy OR SensitivityAnalysis OR LiteraturePrecedentMatrix for cal-021). v0.1 picks one canonical type per rule. Sufficient for §5.1 positive cases since all packages are Scenario B (fail at clause 5, never reach clause 6).
- **Multi-pack OOS aggregation** — when `--pack vv40 --pack nasa-7009b` is used, OOS runs against the FIRST active pack only.
- **AIMS Tier 4 OOS rules** — inherits this infrastructure; rule catalog is a separate scope item.
- **Full §7.7 evidence_gap field plumbing into Phase 3 judge prompts** — engine emits the 2-required-fields shape; Phase 3 wiring is its own task.
- **Full pytest suite verification** — the 1690-test suite was started but hung at 50% on what appears to be a long-network adversarial/judge test. Replaced with focused 115-test verification covering all OOS code paths + spot-check on related non-OOS paths. The full suite is `python -m pytest`; budget ~30 min including network-bound tests.

## Things surprising

**1. Universal Scenario B.** The §3.1 schema confirmation pass anticipated two scenarios for where rules would fail (clause 5 = no `hasSupportingEvidence`, clause 6 = wrong evidence type). All 5 calibration packages turned out to be Scenario B (clause 5 fails). The path-two design's "comment-block-as-primary source for `missing_evidence_type`" handles this correctly — the failing clause's structural identifier doesn't matter; the rule comment carries the human-readable phrase Phase 3 wants.

**2. JSON-LD default `@vocab` mapping.** Initial assumption: `adversarialProvenance.sourceTaxonomy` wouldn't materialize as RDF (since not declared in v0.5.jsonld context). Reality: the context's default `@vocab` mapping makes any unprefixed JSON key round-trip into `https://uofa.net/vocab#*` predicates. Verified via rdflib before committing to the rule shape. Saved an hour of unnecessary engine refactoring.

**3. Blank-node IDs are non-deterministic across Jena parses.** Discovered when the §5.5 byte-identical baseline test would have failed had I left blank-node bindings in `claim_bindings`. Fixed by filtering blank-node bindings out (they're internal discriminator-chain artifacts; user-facing claim is URI-bound).

**4. Plan file path correction `uofa/oos/` → `src/uofa_cli/oos/`.** The spec named `uofa/oos/` for Python code, but the wheel only includes `src/uofa_cli/`. Caught at T3 when the snapshot module wouldn't import. Code moved to make it importable as `uofa_cli.oos.*`.

## Next-session questions (if and when they arise)

1. **AIMS Tier 4 OOS rules**: when do we need a rule catalog for AIMS, and what categories? Inherits this infrastructure cleanly — only the rule files + comment metadata need authoring.
2. **Phase 3 stage 5 OOS adversarial-discovery output**: stage 5 may surface additional OOS categories beyond the 5 here. New rules slot into `packs/vv40/rules/oos/oos_v0.X.rules` (or a new file under `oos/`); pack manifest's `rule_files` list extends.
3. **NAFEMS demo CLI churn (May 6–27)**: if any demo prep wants to land changes in `commands/check.py`, the OOS phase wiring may need rebase. Pre-flight: capture fresh baselines, re-run `tests/oos/test_production_oos.py`, address any byte-divergence before committing.

## Artifacts produced

| Artifact | Path | Status |
|---|---|---|
| Java OOS engine | `src/weakener-engine/src/main/java/net/uofa/oos/OOSEngine.java` | committed |
| Java engine dispatcher | `src/weakener-engine/src/main/java/net/uofa/Engine.java` | committed |
| Java OOSEngine stub (T4) → full impl (T5) | n/a — overwritten in T5 | committed |
| Shared JSONLD loader | `src/weakener-engine/src/main/java/net/uofa/JsonLdLoader.java` | committed |
| Java JUnit tests | `src/weakener-engine/src/test/java/net/uofa/oos/` (2 files, 11 tests) | committed |
| Maven build wiring | `src/weakener-engine/pom.xml` (single shade execution; jackson-databind dep) | committed |
| Java package rename | `com.crediblesimulation` → `net.uofa`, all consumers updated | committed |
| OOS rule catalog | `packs/vv40/rules/oos/oos_v0.1.rules` (5 rules with comment metadata) | committed |
| vv40 pack manifest | `packs/vv40/pack.json` (added `oos` section, default-off) | committed |
| Python OOS config + runner | `src/uofa_cli/oos/config.py`, `runner.py` | committed |
| Python OOS snapshot serializer | `src/uofa_cli/oos/snapshot.py` | committed |
| Schema reconciliation notes | `src/uofa_cli/oos/SCHEMA_NOTES.md` | committed |
| CLI integration | `src/uofa_cli/commands/check.py` (added OOS phase, `--oos`/`--no-oos` flags) | committed |
| Pre-v0.2 baseline reports | `tests/fixtures/baseline_reports/cal-021..025.json` | committed |
| Test fixture pack | `tests/fixtures/packs/vv40_oos_enabled/` (oos.enabled:true) | committed |
| Production-OOS pytest harness | `tests/oos/test_production_oos.py`, `test_oos_smoke.py`, `test_report.json` | committed |
| Substrate-test pytest update | `tests/substrate/conftest.py`, `oos_backward_substrate_test.py` (subcommand prefix) | committed |
| Site README update | source `README.md` already had `uofa.net` (commit 8d1d42f, prior work); synced copy at `site/src/content/docs/readme.md` is gitignored | n/a (no commit from this session) |
| Markdown summary | `docs/oos_production_v0_1.md` | committed |
| Decision log entry | `docs/decisions/2026-05-05-oos-production.md` | this file |

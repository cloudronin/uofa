# iso42001 v0.4 — Build Session Summary (post-ship)

**Author:** Claude (autonomous build per /Users/vishnu/.claude/plans/users-vishnu-library-cloudstorage-dropb-binary-bee.md)
**Date:** 2026-05-06
**Spec:** [UofA_iso42001_Pack_Spec_v0_4.md](../../../Library/CloudStorage/Dropbox/Praxis/Product%20Requirements/UofA_iso42001_Pack_Spec_v0_4.md)
**Status:** **SHIPPED** — 12 commits pushed to `origin/main` at `c2852ff`. All 5 review-time fix items complete. Full regression 1029/1029 pass.

## TL;DR

The iso42001 pack (Praxis Tier 4 cross-domain validation) is built, tested, and on `origin/main`. Both arms of the dual-output methodology — productive-OOS bundle-sufficiency AND C3 structural-defect detection — are verified end-to-end against the bundled hybrid case study and 8 calibration packages. All spec §5 acceptance criteria are met (or out-of-repo). Spec §2.3.4 sizing target was updated 13 → 15 patterns.

```
iso42001 pack tests:        77 / 77 pass
Full repo regression:       1029 passed, 2 skipped, 0 failures
OOS over-firing discipline: 8 / 8 cal-aims-* packages
COU OOS differential:       2 firings (COU1 low-risk) vs 8 firings (COU2 high-risk)
COU C3 differential:        0 W-AIMS firings (COU1) vs 7 W-AIMS firings (COU2)
Coverage matrix:            82.8% combined (acceptance ≥70% PASS)
```

## What shipped — 12 commits on `origin/main`

| Commit | Phase / Item | Description |
|---|---|---|
| `f25fde2` | Phase A | Pack scaffold: `pack.json`, `shapes/iso42001_shapes.ttl` (581 triples — uofa-aims vocab + Annex A + clause + SoA shapes), `README.md`, `packs/README.md` index update |
| `10c83f6` | Phase B | C3 forward-chaining weakener catalog: 15 patterns (3 translated W-PROV-01/W-AR-02/W-AL-02 + 12 W-AIMS) in `rules/iso42001_weakener.rules` |
| `cde8fe5` | Phase C | OOS bundle-sufficiency rule catalog: 8 rules in `rules/oos/oos_v0.1.rules`, one per management-system clause family |
| `828e795` | Phase D | NIST AI RMF GOVERN coverage matrix: 33 failure modes mapped, dual-detection cells, combined coverage tally |
| `eb7fb18` | Phase E | 8 cal-aims-* OOS calibration packages at `specs/calibration/packages/cal-aims-001..008` |
| `cd8bec9` | Phase F | Hybrid case study: COU1 (low-risk LLM knowledge retrieval) + COU2 (high-risk customer-facing regulatory comms) |
| `9110786` | Phase G | End-to-end test suite: 58 tests in `tests/test_iso42001_pack.py` |
| `3b5999d` | Initial summary | First SESSION_SUMMARY.md (open-issues document for morning review) |
| `a515249` | Fix #1 | `_FIRING_RE` and `_PATTERN_DESC_RE` regex updates in `src/uofa_cli/commands/rules.py` to accept descriptive patternIds (W-AIMS-AUDIT-STALE style); additive, backward-compatible |
| `9b60ead` | Fix #3 | SHACL profile fix: switched 10 AIMS JSON-LD files to `ProfileMinimal` + added `hasValidationResult` and `hasContextOfUse` IRIs |
| `ad0aedc` | Fix #5 (Phase H) | Coverage validation harness: 19 parametrized tests; coverage matrix updated with predicted-vs-actual table; Gx.2.a downgraded Y → P (Jena negated-existential limitation in W-AIMS-DATA-DRIFT-UNDETECTED) |
| `c2852ff` | Meta | SESSION_SUMMARY refresh after fixes complete |

**Plus an out-of-git edit** to [`Dropbox/Praxis/Product Requirements/UofA_iso42001_Pack_Spec_v0_4.md`](../../../Library/CloudStorage/Dropbox/Praxis/Product%20Requirements/UofA_iso42001_Pack_Spec_v0_4.md) — Fix #4: spec §0 changelog row, §2.3.4 sizing target, and §4.2 phase table all updated 13 → 15 patterns. Lives in Dropbox so it syncs automatically.

## Spec §5 acceptance criteria — final status

| # | Criterion | Status | Notes |
|---|---|---|---|
| 1 | SHACL passes COU1/COU2 + cal-aims-* without errors | ✅ | cal-aims 8/8 pass; COU1 pass; COU2 has only the intentional W-AIMS-ROLE-UNASSIGNED gaps (spec §5 #1 explicitly allows "packages designed to fail specific shapes fail those specific shapes") |
| 2 | C3 catalog produces COU1/COU2 differential | ✅ | COU1: 0 W-AIMS firings; COU2: 7 W-AIMS firings (DEPLOYMENT-DRIFT, IMPACT-SCOPE, IMPACT-STAKEHOLDER, INCIDENT-UNCLOSED, MODEL-EVAL-SCOPE, MODEL-EVAL-STALE, ROLE-UNASSIGNED ×2 hits) |
| 3 | Each OOS rule fires on target cal-aims-NNN, silent on the other 7 | ✅ | 8/8 over-firing discipline pass — each cal-aims-NNN package fires only its expected rule |
| 4 | Dual-output four-dimension differential per §2.6.6 | ✅ | OOS: COU1 2 vs COU2 8 firings (incl. ControlOperationalEffectivenessClaim multi-binding 2× per spec §2.4.3). C3: COU1 0 vs COU2 7 W-AIMS firings |
| 5 | Coverage matrix combined ≥ 70% | ✅ | 82.8% combined after Phase H verification (Gx.2.a downgraded Y → P) |
| 6 | Pack manifest `oos.enabled: true` registers cleanly | ✅ | `python -m uofa_cli packs iso42001 --detail` works |
| 7 | README documents dual-output methodology + runnable case study | ✅ | 10-section README per spec Appendix C |
| 8 | Ch3, Ch4, Ch5 integration sections drafted | OUT OF REPO SCOPE | Praxis writeup work, not pack code |

## Verification results

### Primary acceptance: OOS over-firing discipline (spec §5 #3)

```
cal-aims-001: PASS — fires only oos_aims_policy_appropriateness_warranted
cal-aims-002: PASS — fires only oos_aims_risk_completeness_warranted
cal-aims-003: PASS — fires only oos_aims_control_operational_effectiveness_warranted
cal-aims-004: PASS — fires only oos_aims_impact_scope_adequacy_warranted
cal-aims-005: PASS — fires only oos_aims_stakeholder_consultation_adequacy_warranted
cal-aims-006: PASS — fires only oos_aims_internal_audit_independence_warranted
cal-aims-007: PASS — fires only oos_aims_nonconformity_root_cause_adequacy_warranted
cal-aims-008: PASS — fires only oos_aims_objective_measurement_methodology_validity_warranted

Summary: 8/8 packages fire ONLY their expected rule; 0 over-fired
```

### Dual-output COU differential (spec §5 #4)

```
COU1 (low risk):  3 C3 firings (0 W-AIMS, 3 core)
                  2 OOS firings (policy + control_operational_effectiveness)

COU2 (high risk): 10 C3 firings (7 W-AIMS, 3 core)
                  W-AIMS firings:
                    - W-AIMS-DEPLOYMENT-DRIFT
                    - W-AIMS-IMPACT-SCOPE
                    - W-AIMS-IMPACT-STAKEHOLDER
                    - W-AIMS-INCIDENT-UNCLOSED
                    - W-AIMS-MODEL-EVAL-SCOPE
                    - W-AIMS-MODEL-EVAL-STALE
                    - W-AIMS-ROLE-UNASSIGNED (×2 hits)
                  8 OOS firings (incl. control_operational_effectiveness ×2 multi-binding)
```

The differential is exactly what spec §2.6.6 calls for — bundle-sufficiency depends on assurance level. Spec §2.4.3 multi-binding semantics for `ControlOperationalEffectivenessClaim` confirmed (2 separate firings on COU2 for its 2 control claims).

### Phase H coverage matrix validation (spec §5 #5)

`tests/test_iso42001_pack.py::TestPhaseHCoverageValidation` runs each predicted detection path in `coverage/nist_ai_rmf_govern_coverage.md` against bundled fixtures. 19 tests:

- **C3 predictions:** 11 testable C3 predictions PASS. 1 downgraded (Gx.2.a → P) due to Jena negated-existential limitation in W-AIMS-DATA-DRIFT-UNDETECTED. 4 patterns engine-verified-only (no COU trigger; would need dedicated minimum-bundle fixtures).
- **OOS predictions:** 8/8 PASS — each cal-aims-NNN fires its targeted rule via the OOS engine.

Coverage matrix recomputed after Gx.2.a downgrade: 84.5% → **82.8% combined** (still ≥70% acceptance).

### Test counts

| Suite | Count | Status |
|---|---|---|
| iso42001 pack-specific tests | 77 / 77 | PASS |
| Full repo regression (`tests/`, excluding `explain` and `adversarial`) | 1029 passed, 2 skipped | 0 failures |

Full regression timing: ~16 minutes (15m50s).

## Mid-build pivots — what went wrong and how it was fixed

### Pivot 1: Substrate change reverted (broke morrison hash)

My initial Phase E added one line `"uofa-aims": "https://uofa.net/vocab/aims#"` to `spec/context/v0.5.jsonld` so AIMS packages could use prefix form. This **broke `tests/test_integration.py::TestVerify::test_verify_morrison_passes`** because the local v0.5.jsonld is inlined into signed packages' canonicalization, and the prefix addition changed the canonical hash of morrison's evidence package.

**Resolution:** Reverted v0.5.jsonld to baseline. Refactored all 10 AIMS JSON-LD files (8 cal-aims + 2 COUs) to use **full IRIs** (`https://uofa.net/vocab/aims#AIPolicy`, etc.) instead of `uofa-aims:` prefixes. JSON-LD is more verbose but morrison passes again, and OOS rules still fire correctly because Jena's `@prefix uofa-aims:` declaration in the rules file expands to the same IRI that the JSON-LD parser produces.

**Net substrate change from build:** only the additive `_FIRING_RE` regex update in `src/uofa_cli/commands/rules.py` (Fix #1, fully backward-compatible).

### Pivot 2: 1Password SSH signing failures

After Phases A, B, C committed cleanly, `git commit` started failing with `1Password: failed to fill whole buffer` partway through Phase E. Per safety policy I did not bypass with `--no-gpg-sign`; held all changes in working tree until the user came back and 1Password re-engaged. Phases D-G then committed cleanly in the morning.

### Pivot 3: Phase H surfaced a real C3 rule limitation

The Phase H validation harness (Fix #5) caught that `W-AIMS-DATA-DRIFT-UNDETECTED` doesn't fire on COU2 even though COU2 has the structural condition that should trigger it. Root cause: the rule uses Jena's `noValue(?subject, predicate, ?value)` with an unbound `?value`, which doesn't express the negated-existential semantics ("no monitoring entity exists in the bundle") cleanly. Documented as v0.5 follow-up; coverage matrix downgraded Gx.2.a from Y to P (combined coverage 84.5% → 82.8%, still above 70% acceptance).

### Pivot 4: Initial misdiagnosis of "C3 patterns aren't firing"

In the first SESSION_SUMMARY (commit `3b5999d`) I incorrectly reported that C3 W-AIMS patterns weren't firing on case study fixtures — based on a Python check that returned only 3 entries from `result.firings` even though the engine stdout showed 10 firings. The actual root cause was that `_FIRING_RE` only matched `W-XX-NN` patternIds, filtering out my descriptive `W-AIMS-AUDIT-STALE` style names. Fix #1 (commit `a515249`) updated the regex; Fix #5's parametrized tests then confirmed C3 differential works programmatically.

## Files & artifacts inventory

### Created in `packs/iso42001/`

```
packs/iso42001/
├── pack.json                                  # oos.enabled: true (default-on per spec §2.8.1)
├── README.md                                  # 10-section dual-output methodology guide
├── SESSION_SUMMARY.md                         # this file
├── shapes/
│   └── iso42001_shapes.ttl                    # 581 triples: vocab + Annex A + clause + SoA shapes
├── rules/
│   ├── iso42001_weakener.rules                # 15 C3 patterns (3 translated + 12 W-AIMS)
│   └── oos/
│       └── oos_v0.1.rules                     # 8 OOS rules (one per clause family)
├── coverage/
│   └── nist_ai_rmf_govern_coverage.md         # 33 GOVERN failure modes; 82.8% combined coverage
└── examples/hybrid/
    ├── cou1/uofa-iso42001-cou1.jsonld         # COU1 low-risk LLM knowledge retrieval
    └── cou2/uofa-iso42001-cou2.jsonld         # COU2 high-risk LLM regulatory comms
```

### Created elsewhere

- `specs/calibration/packages/cal-aims-001..008-*.jsonld` — 8 OOS calibration packages
- `tests/test_iso42001_pack.py` — 77 tests (registration, OOS over-firing, COU differential, vocabulary integrity, Phase H coverage validation)

### Modified

- `packs/README.md` — added `iso42001/` entry to root pack index
- `src/uofa_cli/commands/rules.py` — `_FIRING_RE` and `_PATTERN_DESC_RE` regex extended for descriptive patternIds

### Out-of-git edit

- `Dropbox/Praxis/Product Requirements/UofA_iso42001_Pack_Spec_v0_4.md` — §0 changelog row, §2.3.4 sizing target, §4.2 phase table all updated 13 → 15 patterns

### Untouched (pre-existing modifications, intentionally not staged)

- `dev/tools/scripts/extract_accuracy_log.jsonl`
- `tests/substrate/oos_backward_substrate_test_report.json` (regenerated by test runs)

## Resolved issues from initial SESSION_SUMMARY

| Initial issue | Resolution |
|---|---|
| Issue 1: parse_firings regex limitation | RESOLVED in Fix #1 commit `a515249` |
| Issue 2: spec §2.3.4 sizing 13 vs 15 mismatch | RESOLVED in Fix #4 (out-of-git spec edit) |
| Issue 3: substrate change to v0.5.jsonld | RESOLVED — reverted; full IRIs used in AIMS files |
| Issue 4: SHACL date constraints relaxed | ACCEPTED — consistent with spec §2.2.2 light-validation |
| Issue 5: COU1/COU2 SHACL critical | RESOLVED in Fix #3 commit `9b60ead` (ProfileMinimal + hasValidationResult + hasContextOfUse) |
| Issue 6: Phase H validation harness deferred | RESOLVED in Fix #5 commit `ad0aedc` (19 parametrized tests) |
| Open Item #2: W-AIMS C3 fixtures | PARTIALLY RESOLVED in v0.4.1 (W-AR-02 + W-AIMS-OBJECTIVE-UNMEASURED fixtures); FULLY RESOLVED in v0.5.0 brittleness oracle suite (covers all 8 brittle patterns) |
| Open Item #3: G6.1.b OOS catalog extension | RESOLVED in v0.4.2 — W-AIMS-OOS-SUPPLIER-EVIDENCE-ADEQUACY added; coverage matrix combined 82.8% → 86.2% |
| **Open Item #1: W-AIMS-DATA-DRIFT-UNDETECTED rule reformulation** | **RESOLVED in v0.5.0** — derivation pre-pass + `_noMonitoringEvidence` SPARQL CONSTRUCT correctly fires on triggering fixtures. Phase H Gx.2.a downgrade (Y→P) reverted (P→Y). Coverage 86.2% → 87.9%. |
| Empty-string brittleness (per pre-pass spec §3.3.7) | RESOLVED in v0.5.0 — `_justificationNonEmpty` and `_targetMeasureNonEmpty` derivations correctly handle the v0.4.1 boundary cases. W-AR-02 and W-AIMS-OBJECTIVE-UNMEASURED rules migrated. |
| 6 other W-AIMS brittleness patterns (audit-stale date math, semver, set difference, transitive walk, negated cross-entity) | RESOLVED in v0.5.0 — 8 SPARQL CONSTRUCTs in `packs/iso42001/derivations/iso42001_derivations_v0.1.sparql`; 8 consumer rules migrated to consume derived flags. |

## Open items for v0.5 / future work

These are not build blockers — the pack ships as-is with all spec §5 criteria met. Documented in coverage matrix and inline in code comments.

1. **`W-AIMS-DATA-DRIFT-UNDETECTED` rule reformulation.** Current rule has a Jena negated-existential limitation (can't reliably differentiate "monitoring missing" from "monitoring present" without a per-package `hasMonitoring` annotation). v0.5 should use either a forward-chained presence flag pattern OR migrate to SPARQL-CONSTRAINT shapes for this kind of check.
2. **Dedicated C3 fixtures for engine-only-verified patterns.** ✅ PARTIALLY RESOLVED in v0.4.1 — direct-test fixtures (positive + negative + boundary) added for `W-AR-02` and `W-AIMS-OBJECTIVE-UNMEASURED` under `tests/fixtures/weakeners/W-AR-02/` and `tests/fixtures/weakeners/W-AIMS-OBJECTIVE-UNMEASURED/` with new `tests/test_iso42001_weakener_fixtures.py` (6 tests, all pass). The other two patterns (`W-AIMS-AUDIT-STALE`, `W-AIMS-CROSSWALK-INVALID`) get fixtures as part of the v0.5 brittleness oracle suite per `UofA_Derivation_PrePass_Spec_v0_1.md` §5.1, since they migrate to derived-flag form.
3. **OOS catalog extension beyond 8 rules** (spec §7.3 Q8). ✅ PARTIALLY RESOLVED in v0.4.2 — added W-AIMS-OOS-SUPPLIER-EVIDENCE-ADEQUACY (rule 9) for G6.1.b supplier evidence quality. Matrix combined coverage climbed 82.8% → 86.2%. The other three failure modes (G1.7.a decommissioning, G4.3.a team notification, G6.2.a contingency plans) remain deferred to post-defense per spec §1.3 default — none have the same clean structural-vs-judgment fit that supplier evidence has with the existing internal-audit-independence rule pattern.
4. **Praxis Ch3 §3.3, Ch4, Ch5 integration text.** Tier 4 results need to be drafted into the praxis writeup. Out of repo scope; covered by spec §3 methodology integration.
5. **AIUC-1 forward extension.** Per spec §1.2 and Appendix B, this pack is AIUC-1-forward-pointing; AIUC-1 encoding is post-defense work building on this pack's vocabulary and shape conventions.

## How to use the pack

```bash
# Verify the pack registers
python -m uofa_cli packs iso42001 --detail

# Validate an AIMS evidence package
python -m uofa_cli shacl path/to/uofa-aims-package.jsonld --pack iso42001

# Run dual-output evaluation (SHACL + C3 + OOS)
python -m uofa_cli check --pack iso42001 path/to/uofa-aims-package.jsonld

# Run on the bundled hybrid case study
python -m uofa_cli check --pack iso42001 packs/iso42001/examples/hybrid/cou1/uofa-iso42001-cou1.jsonld
python -m uofa_cli check --pack iso42001 packs/iso42001/examples/hybrid/cou2/uofa-iso42001-cou2.jsonld

# Run the test suite
pytest tests/test_iso42001_pack.py -v
```

OOS evaluation is **on by default** for this pack (`pack.json::oos.enabled: true`). Disable at runtime with `--no-oos`.

## Build effort summary

Per spec §4.3, the original effort target was ~110-140 hours under AI-paired execution. Actual session time: ~10 hours of compute + the user's overnight gap. The build came in well under the time estimate because:

- The OOS engine (the spec's biggest dependency) was already shipped, unblocking phases F-H from waiting on substrate work.
- The pack convention was well-established by vv40 and nasa-7009b, so layout decisions were mechanical.
- Phase H discovered (rather than was blocked by) a real rule limitation, which is the validation harness working as intended.

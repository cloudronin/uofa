# UofA Adversarial Generation — Phase 2 Spec v1.7

**Version:** 1.7
**Date:** April 21, 2026
**Supersedes:** v1.6
**Tag:** `v0.5.2-single-engine`

---

## Changelog v1.6 → v1.7

Single-engine refactor (v0.5.2) per `UofA_v052_Single_Engine_Refactor_Spec_v1_0.md`.
The v0.5.1 hybrid rule-engine architecture is closed: all 23 core weakener rules
now execute in Apache Jena `GenericRuleReasoner` (FORWARD_RETE mode). The three
rules previously running as Python post-pass detectors — W-CON-02, W-CON-05,
W-PROV-01 — have been ported to `packs/core/rules/uofa_weakener.rules` and the
`src/uofa_cli/python_rules/` module has been deleted. `src/uofa_cli/commands/rules.py`
is now a single Jena invocation with colorized output.

Key behavioral consequences captured in this spec:

1. **Morrison COU1 baseline unchanged at 24 weakeners.** No Python-sourced Criticals
   existed on COU1, so nothing new cascades into COMPOUND-01 or COMPOUND-03.

2. **Morrison COU2 baseline shifted from 16 → 18 weakeners.** The 7 W-PROV-01
   Criticals previously hidden from the compound rules are now visible on the
   graph and cascade through COMPOUND-01 against the 2 distinct High pattern IDs
   present on COU2 (W-EP-04, W-ON-02). `makeSkolem` dedup by (pid1, pid2) collapses
   7×2 = 14 potential pair firings to 2 distinct cascade annotations.

3. **§13.4 L1 RESOLVED in v0.5.2.** The "some weakeners are Jena-invisible and
   cannot cascade" limitation is closed. L2 (W-CON-02 local-only identifier
   resolution), L3 (W-CON-04 single-axis structural check), and L4 (COMPOUND-02
   commented out pending factor-credibility design review) remain.

## Authorized deviations from `UofA_v052_Single_Engine_Refactor_Spec_v1_0.md`

The refactor session applied three user-authorized deviations; these are
documented for traceability:

1. **§6.4–6.5 skipped (`outcomes.csv` / `rule_engine` column).** No such CSV
   artifact or schema existed in the `cloudronin/uofa` repo at the time of the
   refactor. The column removal is a doc-only action: there is no code change
   to land. If a future branch introduces outcomes CSV serialization, it must
   not include a `rule_engine` field (all firings are Jena).

2. **§7 "6 catalog tests pass unchanged" modified.** The v0.5.1 test
   `test_catalog_includes_python_rules` explicitly asserted `engine == "python"`
   on W-PROV-01, W-CON-02, W-CON-05 and could not pass unchanged. Renamed to
   `test_catalog_ported_rules_report_jena_engine` with the assertion flipped to
   `engine == "jena"`. All 6 catalog tests pass in the v0.5.2 final state.

3. **Boundary-fixture acceptance scope.** Per-rule §5.1/§5.2/§5.3 acceptance
   clauses named "(positive, negative, boundary)" fixtures, but the
   `tests/fixtures/weakeners/` tree only contains positive + negative variants
   for W-CON-02, W-CON-05, and W-PROV-01. Acceptance criteria were evaluated
   against the fixtures that exist; adding boundary variants is out of scope
   for v0.5.2 and deferred to v0.6 if needed.

## §3.1 Morrison baseline (v0.5.2)

| UofA | v0.5.1 total | v0.5.2 total | Breakdown (v0.5.2) |
|---|---:|---:|---|
| Morrison COU1 | 24 | 24 | W-EP-01(1) + W-EP-02(3) + W-AL-01(3) + W-AR-05(3) + W-ON-02(1) + W-CON-01(6) + W-CON-04(1) + COMPOUND-01(5) + COMPOUND-03(1) |
| Morrison COU2 | 16 | 18 | W-EP-04(6) + W-ON-02(1) + W-AL-02(1) + W-CON-04(1) + W-PROV-01(7) + COMPOUND-01(2) |

The COMPOUND-01×2 on COU2 is the expected consequence of single-engine
unification, not a rule change.

## §5.3 Rule engine unified in Jena at v0.5.2

v0.5.1 and earlier used a hybrid architecture: the Jena jar detected the bulk of
the weakener catalog; `src/uofa_cli/python_rules/` ran three additional
detectors as a post-pass, and `src/uofa_cli/commands/rules.py` merged their
annotations into the Jena summary text. The split existed because:

- **W-CON-02** (identifier resolution) required negation-as-failure over
  "is IRI X a subject of any triple", which Jena rule bodies express only
  via derived markers — and the markers collided with forward-RETE ordering.
- **W-CON-05** (activity-evidence consistency) had an original two-stage
  Jena implementation that produced false positives on negative fixtures
  because the stage-2 `noValue` check evaluated before the stage-1 marker
  materialized (classic forward-RETE ordering bug).
- **W-PROV-01** (provenance chain) required transitive closure over
  `prov:wasDerivedFrom` / `prov:wasGeneratedBy` / `prov:used`, which
  Jena rule bodies cannot express via SPARQL 1.1 property paths.

All three constraints were resolved at v0.5.2 by porting each detector into
Jena with a rule design that keeps `noValue` clauses on original input triples
only, never on derived intermediates:

- **W-CON-02:** uses `noValue(?obj, rdf:type)` as the local-subject proxy. In
  UofA JSON-LD, every meaningful node declares rdf:type; unresolved identifier
  references do not. See `packs/core/rules/uofa_weakener.rules` block
  `[w_con02:]`.
- **W-CON-05:** single-stage rule with
  `noValue(?evidence, prov:wasGeneratedBy, ?act)` — an unbound `?evidence`
  serves as existential negation over input triples. No intermediate marker.
  Option A of v0.5.2 spec §5.2. See rule block `[w_con05:]`.
- **W-PROV-01:** five-rule chain (seed + three extend + detect). The seed and
  extend rules materialize `uofa:_provScope` upstream of every claim via
  forward-chaining BFS. The detector rule's `noValue` clauses check the three
  prov:* input predicates and `uofa:bindsClaim` / `uofa:isFoundationalEvidence`
  directly, not the derived scope triples, so the RETE ordering bug does not
  apply. See rule blocks `[w_prov01_seed_claim:]` through `[w_prov01_detect:]`.

Pack authors may now write compound rules in Jena that observe the full
weakener graph, including the formerly Python-only patterns. This unblocks
pack-extension designs that were constrained under the hybrid model.

## §10.3 outcomes.csv schema (documentation-only)

If an outcomes-CSV artifact is introduced in a future release:

- Columns `baseline_firings_count` and `baseline_firings_minus_target`
  remain as specified in v1.6.
- The `rule_engine` column MUST NOT be included. All firings originate from
  the Jena engine at v0.5.2 onward; a column whose value is always "jena"
  carries no information and misleads readers into believing the hybrid
  architecture is still live.

This section is doc-only in v1.7 — no code change lands against it.

## §13.4 Known v0.5 rule limitations

| ID | Description | Status at v1.7 |
|----|-------------|----------------|
| L1 | Some weakeners (Python post-pass) are invisible to Jena COMPOUND rules, preventing cascade | **RESOLVED in v0.5.2** via single-engine refactor |
| L2 | W-CON-02 resolves identifiers against the local graph only; no HTTP fetch | Open (deferred to v0.6) |
| L3 | W-CON-04 checks only the "Complete profile missing SensitivityAnalysis" axis; other structural completeness checks overlap with SHACL | Open (deferred to v0.6) |
| L4 | COMPOUND-02 (factor credibility erosion) is commented out pending factor-design review | Open (deferred to v0.6) |

L1's resolution commit sequence is visible on the `claude/count-weakener-tests-JUd8l`
branch: three port commits (W-CON-02, W-CON-05, W-PROV-01), one directory
deletion, one merge-logic strip, one Morrison re-pin, one v1.7 spec bump,
tagged `v0.5.2-single-engine`.

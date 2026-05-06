# OOS Engine — Schema Reconciliation Notes

**Purpose:** Document the `evidence_gap` schema resolution between three sources (Phase 3 v1.6 judge schema, productionization spec §3, substrate-test diagnostic output) and define the structure the production OOSEngine emits.

**Spec reference:** `UofA_OOS_Productionization_Spec_v0_3.md` §3.1 (this document is the deliverable §3.1 calls for).

---

## 1. Sources of truth

| Source | Path | Role |
|---|---|---|
| Phase 3 v1.6 judge output schema | [`specs/judge_output_schema.json`](../../specs/judge_output_schema.json) | Authoritative for **judge-emitted** `evidence_gap`. Two required fields, `additionalProperties: false`. |
| Phase 3 v1.6 productive-OOS delta | `Product Requirements/Phase3_Plan_Productive_OOS_Delta.md` | Same two fields, same constraint. Defines the field semantics in prose. |
| Productionization spec | `Product Requirements/UofA_OOS_Productionization_Spec_v0_3.md` §3 | Lists **five** fields mapped from path-two engine internals. |
| Substrate test diagnostic output | [`tests/substrate/oos_backward_substrate_test_report.json`](../../tests/substrate/oos_backward_substrate_test_report.json) under `property_c.lhs_decomposition_diagnostic` | Concrete shape the production engine extends. Has `clauses[]`, `missing_subgoal_index`, `missing_subgoal`, `missing_subgoal_resolved`, `details`. |

---

## 2. Resolved structure

Per the user's decision in this session: **two schema-required fields at top level + three path-two-specific fields under `path_two_metadata`.** This keeps the canonical Phase 3 contract intact and isolates implementation diagnostics where consumers can ignore them.

```json
{
  "rule_name": "oos_modelform_adequacy_warranted",
  "verdict": "OUT-OF-SCOPE",
  "claim_bindings": {
    "claim": "https://uofa.net/calibration/oos-021/claim"
  },
  "missing_subgoal": "(?evidence rdf:type uofa:StructuredComparisonStudy)",
  "evidence_gap": {
    "missing_evidence_type":
      "structured model-form comparison studies for turbulence model selection",
    "would_support_defeater_evaluation":
      "subjective model-form adequacy — bundle does not contain evidence sufficient to evaluate model-form choice against COU",
    "path_two_metadata": {
      "claim_under_evaluation":
        "https://uofa.net/calibration/oos-021/claim",
      "failed_subgoal_clause":
        "(?evidence <https://uofa.net/vocab#> rdf:type <https://uofa.net/vocab#StructuredComparisonStudy>)",
      "bundle_check_rule_name":
        "oos_modelform_adequacy_warranted"
    }
  }
}
```

The outer object (`rule_name`, `verdict`, `claim_bindings`, `missing_subgoal`, `evidence_gap`) is the per-result element of the `oos_results` array per spec §2.4. The `evidence_gap` sub-object is the part that aligns with the Phase 3 schema.

---

## 3. Field-source mapping

| Output field | Source | Notes |
|---|---|---|
| `rule_name` | `Rule.getName()` | Jena rule parser API |
| `verdict` | Constant `"OUT-OF-SCOPE"` | The engine only emits results when bundle-sufficiency fails. Successful proofs (rare in practice; see §6) produce no result for that binding. |
| `claim_bindings` | SPARQL SELECT bindings for the rule head's variables | For the v0.1 rule shape (one variable, `?claim`), this is a single-key map. Generalizable. |
| `missing_subgoal` | Failing clause's textual form, with bindings substituted | Renders the `TriplePattern` with bound subject/object → human-readable triple. Substrate test produced equivalent output as `missing_subgoal_resolved`. |
| `evidence_gap.missing_evidence_type` | **Primary:** rule's `# COMMENT` block, key `missing_evidence:` <br> **Fallback:** failing clause's object URI local name | The Phase 3 schema example uses NL phrases ("structured rationale documents for model-form selection"), so the comment block is the better source. URI fallback ensures the field is always populated even if a rule lacks the comment. |
| `evidence_gap.would_support_defeater_evaluation` | Rule's `# COMMENT` block, key `defeater_type:` | Phase 3 schema example: "W-AR-06 eliminative argumentation absent". Rule-author writes this. |
| `evidence_gap.path_two_metadata.claim_under_evaluation` | Bound subject from rule head | Same value as `claim_bindings["claim"]` for the v0.1 rule shape; redundant on purpose so consumers reading only `evidence_gap` have the binding. |
| `evidence_gap.path_two_metadata.failed_subgoal_clause` | Same as outer `missing_subgoal` | Redundant on purpose for the same reason. |
| `evidence_gap.path_two_metadata.bundle_check_rule_name` | Same as outer `rule_name` | Redundant on purpose for the same reason. |

The three `path_two_metadata` fields are deliberate redundancy with outer-object fields — the `evidence_gap` block is meant to be self-contained for downstream consumers that only read it (e.g., a future judge agreement-statistics tool comparing engine output to LLM judge output side-by-side).

---

## 4. Worked example — cal-021

From the substrate test output (`tests/substrate/oos_backward_substrate_test_report.json`), the LHS-decomposition diagnostic on cal-021 reported:

```json
"missing_subgoal": "?claim @hasSupportingEvidence ?evidence",
"missing_subgoal_resolved":
  "(?claim=https://uofa.net/calibration/oos-021/claim <https://uofa.net/vocab#hasSupportingEvidence> ?evidence)"
```

Note: cal-021 fails at **clause 1** (`hasSupportingEvidence`) in the substrate test setup — the substrate harness only added `ModelFormAdequacyClaim` typing in-memory and not the `hasSupportingEvidence` triple. Production behavior depends on what cal-021..025 actually contain (T2 vocabulary reconciliation will resolve this).

Two production scenarios:

**Scenario A — clause 3 fails (the "ideal" case per spec §4.1):** Package has `ModelFormAdequacyClaim` typing AND `hasSupportingEvidence` linkage to *some* evidence node, but that evidence node lacks the `StructuredComparisonStudy` type. The engine reports clause 3's URI as `failed_subgoal_clause`, and `missing_evidence_type` comes from the rule comment block (NL phrase) rather than the URI local name.

**Scenario B — clause 1 or 2 fails (current substrate test reality):** Package has `ModelFormAdequacyClaim` typing but lacks `hasSupportingEvidence`. Engine still reports a meaningful `missing_evidence_type` from the rule comment block (which describes what the rule is checking for), regardless of which clause specifically failed. The `failed_subgoal_clause` field carries the exact diagnostic so the auditor can see *which* link is missing.

The comment-block-as-primary design makes both scenarios produce a useful Phase-3-compatible `missing_evidence_type`. The `path_two_metadata.failed_subgoal_clause` carries the engine-internal diagnostic for finer-grained inspection.

---

## 5. Reconciliation with `judge_output_schema.json` — open question

The judge output schema enforces `additionalProperties: false` on `evidence_gap` ([`specs/judge_output_schema.json`](../../specs/judge_output_schema.json) line 158, fragment around line 140). **If the OOS engine output is fed through this validator, `path_two_metadata` will be rejected.**

This is an architecturally distinct concern: the engine output is **not** judge output. They share the field name `evidence_gap` but live in separate report sections (`oos_results[].evidence_gap` for engine output vs `judge_verdicts[].evidence_gap` for judge output). The Phase 3 pipeline validates judges' output via the judge schema; the engine has its own output path.

**Open question to resolve in T7 (CLI integration):**
- When `uofa check` emits the unified report, does the OOS engine result pass through any validator that uses `judge_output_schema.json`?
- If yes → either (a) drop `path_two_metadata` from the engine output (loses diagnostic value), or (b) split the `evidence_gap` schema into a base + extension and apply only the base to engine output. Strongly prefer (b).
- If no → no action needed; the engine output uses its own schema.

**Resolution rule (per spec §7 R6):** If T7 surfaces actual schema-validation rejection, raise as a blocker before improvising. Do not silently drop `path_two_metadata` — its absence loses the failed-subgoal diagnostic that motivated path two in the first place.

---

## 6. Reconciliation with substrate test output

Substrate test diagnostic structure (under `property_c.lhs_decomposition_diagnostic`):

```
clauses: [...]                   ← per-clause evaluation results
passed: bool                     ← whether decomposition found a missing sub-goal
missing_subgoal_index: int       ← which clause failed first
missing_subgoal: string          ← failing clause's text
missing_subgoal_resolved: string ← failing clause with bindings substituted
details: string                  ← human-readable summary
```

Production engine output keeps the substrate test's diagnostic value but reorganizes:

| Substrate field | Production field | Note |
|---|---|---|
| `missing_subgoal` | (not exposed) | The text-form clause is replaced by `missing_subgoal_resolved` semantics |
| `missing_subgoal_resolved` | `missing_subgoal` (top-level) AND `evidence_gap.path_two_metadata.failed_subgoal_clause` | Renamed to drop the `_resolved` suffix; the engine always substitutes bindings |
| `missing_subgoal_index` | (not exposed in output; available in JUnit assertions) | Diagnostic-only |
| `clauses[]` array | (not exposed by default) | Available via `--verbose` flag for debugging; not part of standard output |
| `passed` (rule-level) | Implicit: a result element is emitted only when the rule fails | A "passed" rule (full proof) emits no `oos_results` element for that binding |
| `details` | (not exposed) | Replaced by structured fields |

Substrate test code stays committed at [`OOSSubstrateTest.java`](../../src/weakener-engine/src/main/java/net/uofa/OOSSubstrateTest.java) per spec §1.6 (historical reference); production code is a new class.

---

## 7. Open items for T2/T5/T7

- **T2 vocabulary reconciliation** (per spec §4.2): inspect cal-021..025 to determine whether each package has `hasSupportingEvidence` linkage (Scenario A → clause 3 fails) or not (Scenario B → clause 1/2 fails). If Scenario B is the universal case, every rule's failure point will be clause 1 or 2, and the `# COMMENT` block becomes load-bearing for `missing_evidence_type`. Document any per-package divergence here in a §8 addendum.

- **T5 OOSEngine implementation**:
  - Define the `# COMMENT` block syntax for rule files. Proposal:
    ```
    # bundle_check_rule_name: oos_modelform_adequacy_warranted
    # calibration_target: cal-021
    # defeater_type: subjective model-form adequacy — bundle does not contain ...
    # missing_evidence: structured model-form comparison studies for ...
    ```
    The parser reads `# key: value` lines immediately preceding each `[rule_name: ...]` block.
  - Decide whether to support multiple candidate evidence types per rule (cal-021 lists three: StructuredComparisonStudy, SensitivityAnalysis, LiteraturePrecedentMatrix per spec §4 table). v0.1 will support an OR over evidence types via multiple rules with the same name suffix, OR a single rule that uses `noValue` over a UNION of evidence types. Decision deferred to T5.

- **T7 CLI integration**: resolve the §5 open question (does the report assembly path validate engine output through judge_output_schema?). Add a unit test that constructs an engine output with `path_two_metadata` and verifies it survives the report-emit path.

- **T9 docs**: if any open items above resolve in unexpected ways, capture in `docs/oos_production_v0_1.md` for posterity.

---

## 8. T2 vocabulary reconciliation outcome (May 5, 2026)

Per-package inspection of cal-021..025 vs the spec §4 expected vocabulary:

| Cal | Spec §4 claim type | Actual claim typing in package | Spec §4 evidence type | Used in rule |
|---|---|---|---|---|
| cal-021 | `uofa:ModelFormAdequacyClaim` | None (claim is bare URI bound via `bindsClaim`) | StructuredComparisonStudy | `uofa:StructuredComparisonStudy` |
| cal-022 | `uofa:TacitKnowledgeTransferClaim` | None | DocumentedSOP | `uofa:DocumentedSOP` |
| cal-023 | `uofa:BehavioralComplianceClaim` | None | BehavioralAuditRecord | `uofa:BehavioralAuditRecord` |
| cal-024 | `uofa:RegulatoryJurisdictionClaim` | None | JurisdictionalAlignmentDocument | `uofa:JurisdictionalAlignmentDocument` |
| cal-025 | `uofa:ClinicalJudgmentArbitrationClaim` | None | ArbitrationRecord | `uofa:ArbitrationRecord` |

**Universal Scenario B confirmed.** No package has inline claim type triples or `hasSupportingEvidence` linkage. The packages DO contain structured `adversarialProvenance.sourceTaxonomy` literals identifying the OOS category (verified: this field round-trips through JSON-LD into RDF as `uofa:sourceTaxonomy`, materialized via the v0.5 context's default `@vocab` mapping).

**Resolution:** Per spec §4.2 (rules update to match packages), the v0.1 rule shape is six body clauses instead of the §4.1 three-clause shape. The first four are **discriminator clauses** (taxonomy match — establish that the rule applies to this UofA); the last two are **sufficiency clauses** (the spec §4.1 supporting-evidence-and-type pair). The boundary is declared in each rule's `# sufficiency_starts_at: 5` comment.

**Engine semantics for v0.1** (per `packs/vv40/rules/oos/oos_v0.1.rules` header comment):

- For each rule, walk body clauses in declared order with binding propagation
- For each binding, evaluate clauses sequentially via SPARQL SELECT (clause N) → propagate any new bindings to clause N+1
- If any clause in `[1 .. sufficiency_starts_at - 1]` fails for ALL candidate bindings → **silently skip the rule** (it doesn't apply to this package)
- If any clause in `[sufficiency_starts_at .. end]` fails → **fire OOS** with that clause as `missing_subgoal`
- If all clauses succeed for some binding → no firing for that binding (proof complete = bundle is sufficient for that claim)

**Comment block format** (consumed by OOSEngine during rule parsing):

```
# bundle_check_rule_name: <identifier — same as the rule's [name:] anchor>
# calibration_target: <cal-XXX reference, informational>
# defeater_type: <NL phrase → evidence_gap.would_support_defeater_evaluation>
# missing_evidence: <NL phrase → evidence_gap.missing_evidence_type>
# sufficiency_starts_at: <integer, 1-based index of first sufficiency clause>
```

The parser reads `# key: value` lines immediately preceding each `[rule_name: ...]` block. Lines outside that immediate-preceding window are treated as file-level comments.

**Vocabulary divergence from spec §4 table:** None for v0.1. All five rules use the spec-listed evidence type. Each rule's `# missing_evidence:` comment carries a richer NL phrase that better matches the per-package gap (e.g., cal-022's actual gap is calibration studies for tolerance, even though the rule's structural type is `DocumentedSOP`). The Phase-3-compatible `missing_evidence_type` field gets the NL phrase per §3 mapping (primary source = comment, fallback = URI local name).

**Multi-evidence-type support deferred to v0.2.** Spec §4 lists multiple acceptable evidence types per category (e.g., cal-021 accepts StructuredComparisonStudy OR SensitivityAnalysis OR LiteraturePrecedentMatrix). v0.1 picks one canonical type per rule. Extending to OR-semantics requires either (a) duplicating rules with different evidence types in the third clause, or (b) a `noValue` Jena builtin over a UNION. Either is a small change but unnecessary for v0.1 since the calibration positive cases require only one evidence type per rule to fail.

**Verification of rule file parsing:** All 5 rules parse cleanly via `Rule.rulesFromURL()` (the substrate-test JAR's `--mode a1-parse-only` reports `passed: true, rules_parsed: 5`).

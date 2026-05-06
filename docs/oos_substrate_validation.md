# OOS Backward-Chaining Substrate Validation — Result Summary

**Author:** Vishnu Vettrivel
**Date:** May 5, 2026
**Spec:** [`Product Requirements/UofA_OOS_Substrate_Validation_Test_v0_1.md`](../Product%20Requirements/UofA_OOS_Substrate_Validation_Test_v0_1.md)
**Status:** Complete — substrate test produced one bit of decision-relevant information (PRD §6)

## Headline

| Property | Result | Note |
|---|---|---|
| A.1 — OOS rule parses standalone | **PASS** | 1 rule, name `oos_modelform_adequacy_warranted` |
| A — Hybrid mode reasoner loads cleanly | **PASS** | 29 C3 forward + 1 OOS backward, `prepare()` succeeded |
| B — Backward rule fires on goal query | **PASS** | `inf.listStatements(claim, bundleSufficient, *)` drove the backward chain; `proof_outcome: failure` (expected — cal-021 lacks the StructuredComparisonStudy) |
| C native — Structured failure trace from Jena | **FAIL** | `getDerivation()` returns nothing for failed backward proofs in Jena 5.3.0; the LP engine's failure trace is SLF4J/stderr strings only |
| C diagnostic — LHS-decomposition fallback | **PASS** | Correctly identifies `?claim hasSupportingEvidence ?evidence` (clause index 1) as the structurally missing sub-goal |
| D — Forward C3 firings unchanged with OOS rule loaded | **PASS** | 5 firings identical (W-AL-01, W-AR-05, W-CON-04, W-EP-02, W-ON-02), zero symmetric difference |
| **Overall outcome (PRD §5)** | **Outcome 2** | Hybrid mechanically works but native structured failure attribution is unavailable. Disposition: fall back to path two for praxis-window OOS implementation. |

## What was actually tested

The test ran the four PRD §2 properties against cal-021 (subjective model-form adequacy OOS calibration package) using a single Java entry point (`net.uofa.OOSSubstrateTest`) compiled into a sibling fat JAR alongside the production weakener engine. Both the forward-only baseline run and the hybrid-mode run executed in one JVM to eliminate classpath drift as a confound for Property D.

The OOS backward rule (`packs/vv40/rules/oos_backward_v0.1.rules`) declares the body-to-head dependency in Jena's backward syntax (`[name: head <- body]`); the PRD §3.2 displayed the rule with `->` for readability but the on-disk artifact uses `<-` so the rule actually executes as backward in HYBRID mode. Standalone parse via `Rule.rulesFromURL` was added as Property A.1 to isolate rule-syntax bugs from reasoner-mode bugs.

cal-021 was not modified on disk. The `uofa:ModelFormAdequacyClaim` typing required for the backward rule's first clause was added to the in-memory Jena `Model` after JSONLD load, honoring PRD §3.4's directive to keep the canonical calibration package unchanged.

## The Property C finding (load-bearing)

Property C is the result that drives the disposition decision.

Jena 5.3.0's `GenericRuleReasoner` exposes `setDerivationLogging(true)` and `inf.getDerivation(stmt)`, but `RuleDerivation` is emitted only for *successfully derived* triples. A failed backward proof returns an empty `StmtIterator` — same shape as "no such triple exists" — and `getDerivation` on a non-existent statement returns nothing. The LP backward engine's failure trace is reachable only via `setTraceOn(true)` which prints SLF4J/stderr strings, exactly the failure mode PRD §7 R4 named.

This means the productive-OOS schema's `evidence_gap` field cannot be populated from a structured Jena API path. Hand-coded fallback is required.

The LHS-decomposition diagnostic was added precisely to make this disposition decision better-informed. It walks the OOS rule's body via `Rule.getBody()`, queries each `TriplePattern` against the data graph (propagating bindings forward as it goes), and reports the first clause that returns empty as the structurally missing sub-goal. On cal-021 it correctly identifies clause 1 (`?claim hasSupportingEvidence ?evidence`) — exactly the structurally absent triple.

The diagnostic working confirms that **path two (SPARQL goal-driven queries in Python) is implementable for the praxis-window OOS work**. Methodologically, LHS decomposition is essentially path two by another name: it bypasses the backward chain and reconstructs failure attribution by hand. The substrate test surfaces this honestly rather than papering over it as a Property C pass.

## Property D verification (no forward regression)

Both runs produced the same 5 weakener firings on cal-021:

| Pattern ID | Affected node | Owner |
|---|---|---|
| W-AL-01 | `oos-021/validation/experimental` | `cal-021-out_of_scope-stub` |
| W-AR-05 | `oos-021/validation/experimental` | `cal-021-out_of_scope-stub` |
| W-CON-04 | `cal-021-out_of_scope-stub` | `cal-021-out_of_scope-stub` |
| W-EP-02 | `oos-021/validation/experimental` | `cal-021-out_of_scope-stub` |
| W-ON-02 | `oos-021/cou` | `cal-021-out_of_scope-stub` |

Cross-checked against the production `python -m uofa_cli rules specs/calibration/packages/cal-021-out_of_scope-stub.jsonld` output — identical pattern IDs, identical affected-node short forms. The new substrate-test JAR is not drifting from production behavior.

Determinism check: 3 sequential runs produced byte-identical firing lists in both arrays. Canonical sort by `(patternId, affectedNode, owner)` plus deduplication of hybrid-mode duplicate solutions prevents the skolem-IRI churn the Plan-phase analysis flagged.

## Disposition implication

Path one (Jena hybrid mode) is **engineering-feasible at the mechanical level** — the reasoner loads, the backward rule executes when queried, forward firings don't regress. But the productive-OOS framing's `evidence_gap` requirement (structured failure attribution accessible from Python) is **not satisfied by native Jena**. Bridging the gap requires hand-coding the LHS-decomposition logic in Java, which is essentially reimplementing path two inside path one.

**Praxis-window decision: implement OOS via path two (SPARQL goal-driven queries in Python).** The LHS-decomposition diagnostic in this test demonstrates the path-two pattern works on cal-021 and produces a structured `missing_subgoal` output that maps directly to the productive-OOS `evidence_gap` schema field.

What this does *not* commit to:

- Whether to build the full OOS catalog or a subset in the praxis window — the substrate test produces one bit, not the full disposition (PRD §9). That sizing decision belongs in a separate session.
- Whether C4 reactivation is supported by the same substrate — the C4 question per PRD §10 stays deferred to a focused strategic-review session, with this test result as one input.

## Time consumed

Single AI-assisted implementation session (Claude Opus 4.7 via Claude Code). Well inside the PRD §7 R6 hard cap of 22 focused hours. The 16–22h human-baseline estimate in the PRD assumed manual work; the actual compressed timeline reflects AI-paired execution and does not invalidate the estimate as a planning anchor for similar future work.

## Artifacts

- Substrate test JAR source: [`src/weakener-engine/src/main/java/net/uofa/OOSSubstrateTest.java`](../src/weakener-engine/src/main/java/net/uofa/OOSSubstrateTest.java)
- Build wiring: [`src/weakener-engine/pom.xml`](../src/weakener-engine/pom.xml) (second shade execution producing `uofa-weakener-engine-0.1.0-substrate-test.jar`, plus `jackson-databind` dep for JSON output)
- OOS backward rule: [`packs/vv40/rules/oos_backward_v0.1.rules`](../packs/vv40/rules/oos_backward_v0.1.rules) (committed regardless of test outcome per PRD §8)
- Schema additions: [`uofa/vocab/v0.5/oos_substrate_test.ttl`](../uofa/vocab/v0.5/oos_substrate_test.ttl) (substrate-test scope only; production use deferred)
- Python harness: [`tests/substrate/oos_backward_substrate_test.py`](../tests/substrate/oos_backward_substrate_test.py) + [`conftest.py`](../tests/substrate/conftest.py) (8 pytest cases including 3-run determinism check)
- Structured test report: [`tests/substrate/oos_backward_substrate_test_report.json`](../tests/substrate/oos_backward_substrate_test_report.json) (the decision-relevant artifact)
- Decision log entry: [`docs/decisions/2026-05-05-oos-substrate.md`](decisions/2026-05-05-oos-substrate.md)

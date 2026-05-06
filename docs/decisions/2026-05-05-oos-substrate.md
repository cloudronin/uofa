# Decision Log: OOS Backward-Chaining Substrate Validation

**Date:** 2026-05-05
**Author:** Vishnu Vettrivel
**Spec:** [`UofA_OOS_Substrate_Validation_Test_v0_1.md`](../../Product%20Requirements/UofA_OOS_Substrate_Validation_Test_v0_1.md)
**Result summary:** [`docs/oos_substrate_validation.md`](../oos_substrate_validation.md)
**Test report:** [`tests/substrate/oos_backward_substrate_test_report.json`](../../tests/substrate/oos_backward_substrate_test_report.json)

## Test outcome

**Outcome 2 (PRD §5).** Properties A.1, A, B, D pass. Property C native fails because Jena 5.3.0's `GenericRuleReasoner` does not expose a structured failure trace for failed backward proofs (`getDerivation()` returns nothing for non-derived statements; the LP engine's failure trace is SLF4J/stderr strings only). The LHS-decomposition diagnostic added to the test correctly identifies the structurally missing sub-goal (`?claim hasSupportingEvidence ?evidence`) by walking the rule body and querying each clause directly.

## Disposition implication

**Praxis-window OOS implementation falls back to path two: SPARQL goal-driven queries in Python.**

The substrate question "does Jena hybrid mode support productive-OOS as specified" resolves to: hybrid mode mechanically works (forward C3 + backward OOS coexist without regression on cal-021), but the productive-OOS framing's `evidence_gap` requirement (PRD §0) cannot be satisfied via native Jena APIs. Bridging the gap requires hand-coding clause-by-clause sub-goal evaluation, which is path two in path one's clothing.

The LHS-decomposition diagnostic working on cal-021 confirms path two is implementable — the same decomposition pattern produces a structured `missing_subgoal` output that maps directly to the productive-OOS `evidence_gap` schema field.

## Next-session question

What is the praxis-window OOS scope decision? Now that path two is the implementation path, the open scoping questions are:

1. Build the full OOS catalog in the praxis window, build a subset, or ship the methodology specification with one demonstration rule (PRD §5 Outcome 1 deferred decision, now applies to path two).
2. Where does the path-two OOS code live in the codebase — alongside the C3 SHACL/Jena stack, or as a separate Python module? The LHS-decomposition diagnostic in `OOSSubstrateTest.java` is a Java prototype; production path two will be Python.
3. Does the productive-OOS schema (`evidence_gap` field per PRD §0) need any updates given the implementation will be path two rather than path one? Probably not — the schema was written substrate-agnostic — but worth a confirmation pass.

These are sized as a focused strategic-review session, not part of the substrate test itself (PRD §6 scope discipline).

## Connection to C4

PRD §10 raised the C4 reactivation question. The substrate test result feeds it as follows: the same Jena-substrate limitation that blocks productive-OOS as a fully native backward-chaining feature would also affect C4 if C4's argumentation needed structured failure attribution. Forward-chaining ASPIC+ argumentation (C4 as specified) does not have this issue — it's a forward-only graph materialization — so the substrate result is **not** an obstacle to a future C4 reactivation. The C4 strategic-review session per the May 4 conclusion can proceed independently of this disposition.

## Artifacts produced

| Artifact | Path | Status |
|---|---|---|
| OOS backward rule file | `packs/vv40/rules/oos_backward_v0.1.rules` | committed (per PRD §8 — regardless of outcome) |
| Schema vocab additions | `uofa/vocab/v0.5/oos_substrate_test.ttl` | committed (substrate-test scope only; production use deferred) |
| Java entry point | `src/weakener-engine/src/main/java/net/uofa/OOSSubstrateTest.java` | committed |
| Maven build config | `src/weakener-engine/pom.xml` (second shade execution + `jackson-databind` dep) | committed |
| Python pytest harness | `tests/substrate/oos_backward_substrate_test.py`, `conftest.py` | committed |
| Structured test report (JSON) | `tests/substrate/oos_backward_substrate_test_report.json` | committed (decision-relevant artifact) |
| Markdown summary | `docs/oos_substrate_validation.md` | committed |
| Decision log entry | `docs/decisions/2026-05-05-oos-substrate.md` | this file |

## Time consumed (actual vs. estimated)

| Phase | PRD estimate | Actual |
|---|---|---|
| Total focused hours | 12–18 (best case), 16–22 (with buffer), 22 hard cap | Single AI-assisted implementation session (Claude Opus 4.7 via Claude Code) |

The PRD's hour budget was sized for manual implementation. AI-paired execution compressed the timeline substantially; the budget remains a useful planning anchor for similar future substrate experiments performed manually.

## Things that surprised me

The Property C result was *expected to fail* per the Plan-phase analysis (Jena's known LP engine limitations on failure traces), so the surprise was not the outcome itself. Two things were surprising in execution:

1. **The PRD's rule syntax in §3.2 used `->` (forward direction), not `<-`.** Caught during T2 implementation; the on-disk rule file uses `<-` so it actually executes as backward in HYBRID mode. The PRD likely meant the `->` as informal "implies" notation rather than Jena syntax. Worth flagging in any future substrate spec to use Jena's exact syntax in spec snippets.
2. **The plan initially proposed updating `packs/vv40/pack.json` to point at the OOS rules file.** Caught and reverted during T2: `vv40` is the default active pack (`paths.py:13`), so wiring the OOS backward rule into `pack.json` would have caused the production `uofa rules` engine to load the rule on every call — either failing to parse `<-` syntax in FORWARD_RETE mode or otherwise polluting production behavior. The substrate test stays self-contained: the OOS rule is loaded only via the substrate-test JAR's explicit `--oos-rule-path` flag.

## Things deferred (per PRD §6 / §9 scope discipline)

- Multi-rule substrate testing (rule interaction)
- Multi-package generalization (rule correctness across calibration set)
- Full §7.7 evidence_gap field plumbing in the productive-OOS schema
- Praxis-window OOS catalog scope (subset / full / single-demo decision)
- C4 reactivation question (handled in its own strategic-review session)

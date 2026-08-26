# UofA Spec — The Attestation Boundary: Signing Model v1.0

Date: 2026-09-08
Status: RULED, build-ready. Consolidates the §12 constitutional rulings, the vocabulary unification, the decision-sign build order, the launch-gate yield, and the documentation pass into one spec. Supersedes all partial messages on this thread. Execution: Claude Code, in the order of §5.
Origin: run 26's first launch was stopped at $12.49 when the pre-registered pass line ("signed package") turned out unreachable — the sign route was a dead control. The repair plan then surfaced a constitutional gap: `assert_issuable` guarded a decision block by one spelling (`engineerDecision`) while the product emits the concept under another (`hasDecisionRecord`), so the issuer key would have signed over a human judgment — the exact thing AGENTS.md §12 exists to forbid. Caught by reading, before any signature existed.

## 1. The principle: attestation scope follows attestor kind

UofA has formalized the boundary between machine work and human judgment at every layer it touches:

| altitude | mechanism | the contract enforced |
|---|---|---|
| act | escalation table + cage | machines execute mechanics; judgment acts are unrepresentable without escalation |
| record | dual attribution (`performed_by` / `authored_by`) | which mind did what, per act, atomic with the act |
| claim | provenance tokens (`defaulted` / `affirmed` / `corrected`) | which kind of mind settled each value |
| presentation | DRAFT chips, machine work non-terminal | machine output proposes; it never concludes |
| **seal** | **this spec: scoped signatures, kind-matched keys** | **infrastructure keys attest what machines can know; only a person's key signs a judgment** |

The signing model is the boundary's terminal enforcement — the same law the cage applies at act time, applied at sealing time. Two questions, two scopes, two key classes:

- **The issuer seal** (infrastructure key): *"this package is authentically from this producer, was structurally sound when it left, and is exactly as it left."* Origin, integrity since sealing, well-formedness at sealing time, declared provenance (the run log's pins inside the sealed scope). Everything machine-checkable; nothing judged. Holder: the producing infrastructure — the Space's deployment secret today; a customer deployment's own key in the enterprise tier.
- **The decision signature** (person-class key): *"I, the named reviewer, stand behind this judgment."* Scoped to the decision block (`hasDecisionRecord`): outcome, rationale, actor, timestamp. Holder: the reviewing engineer — a demo reviewer identity in the instrument, the customer's own engineer in production.
- **One signature may never span both.** An issuer seal covering a judgment would be infrastructure vouching for a human commitment — a machine signing a human judgment. The format refuses it (§3), so the confusion is unrepresentable, not discouraged.

What the issuer seal deliberately does NOT certify: that the evidence is true, that the judgments are sound, that the model is credible, or that the producing organization approves anything. The seal is the tamper-evident bag and the instrument-calibration sticker; the decision signature is the analyst's name on the report. The format now guarantees nobody can mistake the bag for the finding.

## 2. Constitutional rulings (final)

**R1 — `hasDecisionRecord` IS a decision block under §12.** The reading is concept, not spelling: any node carrying a human judgment (outcome + actor/role + rationale + timestamp) is what §12 forbids issuer signatures from spanning, whatever the property is named. Consequence: a complete governed-review package (A-12 requires the outcome) can never be issuer-signed. The remedy is the one the policy itself names: `uofa decision sign`, the reviewer's key, scoped to the block.

**R2 — `engineerDecision` is removed entirely; `hasDecisionRecord` is the sole canonical term.** No alias, no deprecation window — contingent on the §5 step-0 sweep confirming no real artifact carries the old term. The split was two tracks of one program (PhysMAP-era signing policy vs. the v0.7 context) coining separate words for one concept; PhysMAP-side specs migrate later on the author's own queue. The `uofa decision sign` mechanism (two-scope signature) is untouched — only its target's spelling changes.

**R3 — the `assert_issuable` gap is urgent in the public repo independent of Credenza.** Any third party emitting `hasDecisionRecord` can currently obtain an issuer signature over a human judgment. Ships with this work, ahead of the ProfileMinimal repair in the queue.

**R4 — §12 is rewritten in principle form during the unification.** The clause states the law — *attestation scope follows attestor kind: infrastructure keys may sign only machine-checkable claims; judgment-class blocks require a person-class key* — with the decision block as its current instance, so any future judgment-class block (e.g., signed affirmations, if the policy ever extends there) inherits the rule automatically rather than needing its own clause.

## 3. Design

### 3a. The concept guard
`assert_issuable` refuses issuer-signing any package carrying: (a) the `hasDecisionRecord` property or a `DecisionRecord`-typed node; (b) the semantic backstop — any node bearing outcome + actor + rationale semantics per the context — so a third coinage can never reopen the gap. Refusal message names the block found and the lawful path (`uofa decision sign`).

### 3b. Keys — two, structurally separated
- **Demo issuer keypair** (exists; Space secret): seals decision-free artifacts and (pending §4's answer) evidence regions.
- **Demo reviewer keypair** (NEW; second Space secret, same custody profile per deploy/DEPLOY.md): signs decision blocks. Distinct secret names (`DEMO_ISSUER_*`, `DEMO_REVIEWER_*`).
- A test asserts the decision-sign route CANNOT be invoked with the issuer key — wrong-key refusal seen red. Scope separation structural, not conventional.
- No per-user custody, trust-anchor UI, or revocation story this session. Enterprise custody is the customer's, later, on the established tier design.

### 3c. The demo identity is a labeled fixture
The signer name/role in the decision signature block reads unambiguously as a demo identity ("Demo Reviewing Engineer" per policy naming). The ceremony is what gets tested; the identity is what gets swapped: an instrument run's package must tell any reader truthfully which KIND of signer signed. The record never permits the demo signature to be mistaken for a liability claim — in production the same route carries the customer engineer's own key, and only then is the signature a commitment.

### 3d. The product surface
The button that lives: **"Sign the decision (demo reviewer)"** via `uofa decision sign`. The button that dies: issuer-signing of review packages. Dead-control law: nothing renders whose route doesn't answer; server-side refusal proven by direct POST, never by button absence. The sample signs only when its gates honestly clear (A-3/A-4 earned by real extraction, lineage pinned) — no special-case block; the demo path and the certification path stay the same path.

## 4. INVESTIGATION ITEM (before any terminal assertion is written)

Does the uofa policy prescribe **dual signature** (issuer over the evidence region + reviewer over the decision block) or **decision-signature-only** for review packages? Read the spec's answer — never invent one. `write_signed`'s re-verification (`uofa verify --pubkey`), both walks' terminal assertions, and the export flow follow whichever it says.

## 5. Build order

0. **The removal gate.** Sweep for `engineerDecision` and report counts per location before deleting anything: every exported package in the archive (donetest workspaces, run 24/25 packages, capture zips, sample projects, `spec/examples/`, shipped fixtures); the praxis-adjacent encodings (Morrison, Nagaraja, HPT, Zenodo/demo artifacts, anything RESULTS.md or the manuscript cites); the uofa repo, distinguishing code/guard definitions (expected — being removed) from DATA carrying the term as content; Credenza's emission paths and fixtures. **Zero data hits → proceed. Any data hit → stop and report** — a term a real finding depends on gets a migration, not an erasure.
1. **Vocabulary unification.** Every `engineerDecision` reference in code, policy, docs, AGENTS.md §12, and fixtures moves to `hasDecisionRecord`. §12 rewritten in principle form (R4). `uofa decision sign` keeps name and mechanism.
2. **The concept guard** (§3a), fixtures seen red: a `hasDecisionRecord` package refuses issuer signing; a novel-spelling decision-shaped node also refuses.
3. **Grep-clean assertion**: `engineerDecision` appears nowhere in `src/`, `spec/`, or shipped policy (changelog entry is the sole permitted mention).
4. **CHANGELOG + wheel release**: the contract change stated — the refusal trigger, the previously-live gap, its closure. Third parties script against exit codes.
5. **The decision-sign route** per §3b–3d, with the §4 answer read first.
6. **The launch-check yield stands**: the pre-launch gate asserts every pre-registered criterion is satisfiable by the product, against the deployed target for deployed runs. A criterion no affordance can discharge is a hope wearing a measurement's clothes — refuse at launch, not at $12.49.
7. **Both walks extended through the true pass line**: decision signed per §4's answer, package verified by the published wheel, Credenza-free. Fails-first: revert the sign route; the walk must wall there.
8. **Docs pass (§6) lands with the build, same session** — the public story must not lag the enforced one.
9. **Flash re-probe** (~$0.50, PROBE flag, railed): the sealed-and-signed package as a scored item — the first model-produced package to pass the CLI end to end carrying the signature the constitution permits. Journal-scored; unmeasured is void; any product miss = fix, redeploy, re-probe.
10. **Run 26 re-pre-registers and relaunches only behind a clean probe.** Opus, solo, unsteered, instrument profile, `--journal --capture`, full lineage, standard ceiling, deploy-check + deployed smoke current. Amendment boundary 25→26 declared: affirm act, levels legibility, v0.8 contract, vocabulary unification, decision-sign route. The pre-registration names the signature honestly: pass line = "decision signed via the demo reviewer identity and verified by the published wheel." The unsigned escape is not done. **Stop after the record is written — the reading is the author's.**

## 6. Documentation pass (public story = enforced story)

- **README**: the signing paragraph gains the two-question model in three sentences: UofA formalizes the boundary between machine work and human judgment, and the signing model enforces it — infrastructure keys seal what machines can attest (origin, integrity, well-formedness); only a person's key signs a judgment (the decision block); one signature may never span both, and the CLI refuses the confusion.
- **architecture.md**: C1's row splits honestly — integrity verification unchanged, plus the decision-scope signature and `assert_issuable`'s refusal as the enforcement mechanism.
- **getting-started**: the signing step forks — decision-free packages follow the existing flow; decision-carrying packages use `uofa decision sign`; the refusal message is shown and explained as law, not error.
- **uofa.net**: the site's signing/verification copy gets the same three-sentence model; check the live wording during the pass — it may lag the repo.
- **Book note**: one line lands in §1a's second takeaway — the dotted line reached the cell with `affirmed`, and now reaches the seal: the human/AI contract enforced at act, record, claim, and signature.

## 7. Verification

- Every refusal seen red before believed: issuer-key-on-decision-package, wrong-key-on-sign-route, novel-spelling decision node, dead-route POST.
- The walks wall when the sign route is reverted (fails-first), then terminate at the §4-prescribed verification through the published wheel.
- Step-0 sweep report filed before any deletion.
- Grep-clean test green after unification.
- The probe's checklist includes: signature block carries the demo reviewer identity label; the wheel verifies the signed package unaided.

## 8. Out of scope

Per-user key custody, trust anchors, revocation (enterprise-tier design, later). PhysMAP-side spec migration (author's queue). The ProfileMinimal SHACL repair (queued behind R3's release). Any numbered run beyond run 26's relaunch. The pass-line question after run 26 — the reading is the author's.

## 9. One paragraph for the record

Run 26's first launch was stopped by its own gates twelve dollars in, and the repair uncovered the last place the human/AI boundary was informal: the seal. The constitution had the law (§12), the policy had the mechanism (`uofa decision sign`), and the guard knew the wrong word. One reading session closed the gap before any signature existed to regret: the vocabulary unified to one term, the guard rewritten to refuse the concept, the keys split by attestor kind, and the demo identity labeled as the fixture it is. The boundary is now enforced at act, record, claim, and seal — and the signing story the docs tell is the one the format enforces. Assurance by construction, at the edge of the artifact.

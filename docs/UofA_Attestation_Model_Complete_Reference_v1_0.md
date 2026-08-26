# UofA — The Attestation Model: Complete Reference v1.0

Date: 2026-09-09
Status: REFERENCE. The consolidated statement of everything ruled across the attestation-boundary sessions. This document is for consultation — the head does not need to hold it; that is the point. Companion specs (build-authoritative): UofA_Spec_Attestation_Boundary_Signing_v1_0.md, UofA_Spec_Unified_Signing_Surface_v1_0.md, the updated implementation plan (attestation-boundary, decision model, run 26). If this reference and a spec disagree, the spec wins and this document gets corrected.

## 0. The whole thing in five sentences

Every claim in a UofA package is chained to an answerable party. Machines are attributed; identities sign; infrastructure seals; absent authors are cited, never impersonated. One signature may never span both machine-attestable facts and human judgment — attestation scope follows attestor kind. The chain terminates at keys, keys at custody, custody at a person the legal system can reach. Signatures all the way down, with a human at the bottom.

## 1. The stack, bottom to top

| layer | mechanism | what it binds | who answers |
|---|---|---|---|
| passage | sha (content addressing) | the evidence text to its identity | the source document |
| anchor | sha-pinned reference | a claim to the passage supporting it | the encoder who placed it |
| level judgment | `affirmed`/`corrected` provenance + attributed activity (v0.8) | a sufficiency judgment to its judge | the affirming reviewer |
| decision record | actor + timestamp, required always (ownerless verdicts unrepresentable) | a verdict to its owner | the decider named in it |
| decision signature | envelope binding the record + the recomputed measurementHash | the verdict to a key AND to the exact evidence state it judged | the key's holder, in the named role |
| issuer seal | measurement signature over everything except the decision layer | the evidence state to the environment that produced it | the deployment's operator |
| verify | walks the tower back down | reports each layer's verdict, role, and key identity | the reader's own run of the wheel |

Tamper anywhere and the chain says where: alter evidence → measurement hash changes → issuer seal fails AND every decision signature's embedded hash mismatches (the decision provably judged different evidence). Alter a decision → its signature fails. Strip an anchor → the shape refuses. Ownerless verdict → unrepresentable.

## 2. The two questions, two scopes, two key classes

- **Issuer seal** (infrastructure key): "this package is authentically from this producer, was structurally sound when it left, and is exactly as it left." Origin, integrity, well-formedness, lineage pins. Everything machine-checkable; nothing judged. Holder: whoever operates the producing environment — the Space's secret on the hosted tier, the customer's own deployment key in the enterprise tier, the lone engineer on a laptop.
- **Decision signature** (person-class key): "I, the named party, stand behind this judgment (or this transcription of one)." Scoped to the decision layer; binds the recomputed measurement hash so the judgment is chained to the evidence it judged.
- **The law (§12, principle form)**: attestation scope follows attestor kind. An infrastructure key may never sign over a judgment; the format refuses the confusion (`assert_issuable`, name-strict plus semantic backstop), so it is unrepresentable, not discouraged.
- What the issuer seal deliberately does NOT certify: that the evidence is true, the judgments sound, the model credible, or the organization approving. The seal is the tamper-evident bag; the decision signature is the analyst's name on the report.

## 3. The decision model

**Records**: `hasDecisionRecord`, repeatable, append-only — decisions stack (source acceptance, independent concurrence, program approval), never overwrite. Every record: actor + timestamp required (shape-enforced), `decisionScope` from the closed set, and the fork:

- **`asserted`** — the decider is a participant in this package's production. Decision signature REQUIRED. (Run 26's reviewer; a future concurring engineer.)
- **`extracted`** — the decider is the source's (Morrison's team, 2019). Anchor REQUIRED — the sha-pinned passage stating the decision. No signature from the source ever exists or is expected: the paper is their attestation; the anchor cites it. **Signatures attach to acts, not actors.**

**Roles** (`signatureRole`, closed set, required on every decision signature):
- `deciding-engineer` — I made this judgment.
- `concurring-reviewer` — I reviewed this work/decision and concur (or do not).
- `encoder-of-record` — I attest faithful transcription of a third party's decision. Covers the decision LAYER as an act of transcription; whether it is required is a protocol-completeness question, never a per-record shape constraint on extracted entries.

**Machine assessments are not decisions.** Automated output emits `hasAssessmentResult` / `AutomatedAssessment` with status facts (`documentation-incomplete`) — never verdict vocabulary. "Accepted / Not accepted" is reserved for owned decisions. A machine emitting a verdict was the Space's own live defect; the strict name-guard is what caught it.

**The boundary of the format's ambition**: it records the decision ledger; it never orchestrates it. Who must concur, in what order, with what authority — the customer's QMS and the standards' business.

## 4. The two canonical cases (reference — the example wins over any implementation choice)

**Case 1 — Morrison (the source already decided).** Sonnet extracts evidence, anchors, and Morrison's acceptance as an `extracted` decision record (actor = Morrison's team, source's date, anchor to the accepting passage). The stranger signs the decision layer as `encoder-of-record` — faithful transcription. The Space seals the measurement view. Verify reports: intact and authentic; anchors resolve; transcription attested by the named encoder; the decision belongs to Morrison per the cited passage. Nobody signed anything they didn't do.

**Case 2 — Johnson (the reviewer decides).** No acceptance exists in the source. The stranger renders the judgment itself: an `asserted` record (actor = the reviewer, demo identity labeled, now), decision signature with `signatureRole: deciding-engineer`. Same issuer seal. Run 26's pass-line artifact is a Case-2 package.

## 5. Keys, custody, independence

- **Key-per-party, role-per-signature.** A key answers "who is this party?"; scope + role answer "what are they claiming?" §12 lives on the second axis only.
- **The solo case is legitimate and honestly reported**: one human, one key, two roles — issuer as operator of the environment, decision role as judge or encoder. Verify derives independence from **key identity, never key count**: same key across scopes → "single-party configuration" reported as fact; different keys → independent attestation. Independence is a custody fact the format reveals, never a ceremony it fakes.
- **The demo models two parties** and therefore keeps two keys: production issuer key (the pipeline/wizard), demo reviewer key (the labeled fixture identity — "the ceremony is what gets tested; the identity is what gets swapped"). Wrong-key refusals hold both directions.
- **The identity grammar is one definition in code** (`sign_roles.classify_identity`), read by the actor-hygiene guard and by the relation derivation alike, and transcribed here from that guard's own fixture. Identity is the substrate every derived relation stands on: two parties normalising onto one path would not raise an error, it would make verify report a confident falsehood. So comparison is whole-string (case-folded for scheme and host, never shortened to a handle), and an unclassifiable form refuses rather than defaults.

<!-- BEGIN identity-grammar (generated from tests/test_sign_roles.py) -->

| identity | class | what it names |
|---|---|---|
| `https://uofa.net/org/demo-reviewer` | person | a party who can decide; may match a signer |
| `https://acme.example/org/j-smith` | person | a party who can decide; may match a signer |
| `urn:uofa:space:deployment` | infrastructure | a tool, deployment, or key; may match a signer |
| `aa:bb:cc:dd:ee:ff:00:11:22:33` | infrastructure | a tool, deployment, or key; may match a signer |
| `ledger://review-2026/entry-14` | act-reference | an **act**, not a party — never matches a signer |

Refused, each naming its own form rather than defaulting:

- `file:///Users/vishnu/packages/V.%20Vettrivel`
- `path://team/reviewer`
- `J. Smith`
- the empty string
- whitespace only
- a non-string (`None`)
- a non-string (`42`)

<!-- END identity-grammar -->

- **The recursion's bottom**: keys terminate at custody, custody at a person the legal system can reach. Whether a key genuinely belongs to a real, authorized person is the custody layer's promise (enterprise tier, QMS, key ceremony) — priced separately, out of the schema's scope, and honestly labeled as such.

## 6. The CLI surface

**`uofa sign --key K --as <roles> pkg`** — the one signing entry point (`uofa decision sign` is removed; callers migrated).
- Decision-free package, bare `sign`: byte-identical to historical behavior (the whole document IS the measurement view). Regression-pinned.
- Decision-carrying package, bare `sign`: refuses, naming `--as` and the missing role.
- `--as issuer`: seals the measurement view. Permitted over extracted-only decisions (anchors are their warrant); refuses if an asserted record exists unsigned — the seal never silently wraps an unowned verdict.
- `--as <decision role>`: signs the decision layer; requires a verifying measurement seal first (stale-bundle refusal).
- Composed (`--as issuer,deciding-engineer`): one atomic act — both signatures or neither touches disk. Composed ≡ sequential, fixture-asserted.

**`uofa verify`** — the read side.
- No silent default trust anchor (the `research.pub` default is gone); bare verify names which wheel-shipped anchor matched.
- `--decision-pubkey` general and repeatable; unmatched signatures report "present, no key provided" — distinct from invalid.
- Context follows the document; `--context` is the override; fallbacks are named.
- Report is role- and fork-aware: per signature — scope, role, key identity, verdict; per decision record — asserted (signature checked) or extracted (anchor resolved); plus the concentration line.

## 7. Where each rule is enforced

| rule | enforcement layer |
|---|---|
| ownerless verdicts unrepresentable | SHACL (actor + timestamp on every decision record) |
| anchor iff extracted, signature iff asserted | SHACL (per-record) |
| encoder attestation required for a transcription package | protocol-completeness check (per-layer) — distinguishable refusal from the shape's |
| issuer never signs over a judgment | `assert_issuable` (name-strict + semantic backstop) AND the sign surface's refusals AND the SHACL person-class constraint |
| machine output never wears verdict vocabulary | the emitter's contract + the strict name guard |
| judgment tokens carry attributed activities | v0.8 shapes (affirmations), v0.9 shapes (decision signatures) |
| the anchor physically travels | the `decisionAnchor` emission path; verify resolves it (unresolvable = failed, not absent) |
| version honesty | the document's own `@context` wins everywhere; fallbacks named; contexts append-only and digest-pinned |

## 8. Version story

- **v0.7**: `hasDecisionRecord` exists as a bare structure; single whole-document signature vocabulary.
- **v0.8 (shipped, 0.13.0, digest-pinned, byte-frozen)**: level-judgment provenance (`affirmed` etc.) with attributed activities; the two-scope signing mechanism existed in code (A6/A10) but undeclared.
- **v0.9 (this build, additive, +18 terms)**: the decision fork (`decisionProvenance`, `decisionScope`), `decisionAnchor`, the declared `DecisionSignature` envelope (`signatureRole`, `signerKind`, `measurementHash`), the machine-assessment vocabulary. v0.8 packages keep verifying forever under their own context.
- Praxis scope: all of this is post-freeze framework evolution — the manuscript's §5.4 dated sentence and the five tagged placements, nothing more. The v0.9 world belongs to run 26, the paper, and the book.

## 9. The rulings ledger (one line each, for the record)

1. A decision block is a concept, not a spelling; the guard refuses on meaning with a semantic backstop.
2. `engineerDecision` removed entirely; `hasDecisionRecord` canonical; sweep gated the removal and passed.
3. The `assert_issuable` gap was live in our own Space (machine "Not accepted" under an issuer seal) — closed, urgent, shipped.
4. §12 rewritten as principle: attestation scope follows attestor kind.
5. Machines never emit verdict vocabulary; assessments get their own terms and status facts.
6. Every decision has an owner (actor + timestamp, shape-enforced).
7. Signatures attach to acts, not actors; the asserted/extracted fork carries it.
8. Decisions stack append-only with scopes and roles; the format records, never orchestrates.
9. Key-per-party, role-per-signature; independence derived from key identity; the solo case honest.
10. Key model: new production issuer key; demo key rebadged as the labeled reviewer fixture; wrong-key refusals both directions.
11. research.key was remediated in March (rotated, revoked-pub retained) — the escalation's object didn't exist; the silent default-anchor still dies on its own merit.
12. v0.9, not v0.8 — the append-only pin caught its own author's addendum.
13. SHACL reconciliation: per-record warrants (anchor/signature by fork) vs per-layer completeness (encoder attestation) — two layers, two refusals, distinguishable.
14. `decisionAnchor` needed an emission path, not a rename — the anchor now physically travels and verify resolves it.
15. One command: `uofa sign --as <roles>`, atomic composition, `decision sign` retired; verify made role- and fork-aware with no silent trust.
16. Wheel releases at step 7 exactly — one version carrying all three contract changes; the Space consumes only what's shipped.

## 10. One paragraph for the book

The seal was the last place the human/machine boundary ran on convention. Formalizing it forced every ambiguity beneath it to surface exactly once: what a decision is, who owns it, who may sign it, what a machine may say, where independence comes from, and what the anchor of an absent author's word is worth. The answers compose into a single recursive rule — every claim chained to its answerable party, all the way down to a key in a human hand — and the artifact now enforces what the constitution could previously only state. Assurance by construction, at the edge of the artifact, with a person at the bottom.

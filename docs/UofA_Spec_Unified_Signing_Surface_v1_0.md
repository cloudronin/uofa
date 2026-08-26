# UofA Spec — Unified Signing Surface v1.0

Date: 2026-09-09
Status: RULED, build-ready. Amends UofA_Spec_Attestation_Boundary_Signing_v1_0.md (§3, §5 step 5) and supersedes the composed-flag addendum and all partial messages on the signing surface. Covers both sides: §1 the sign surface, §1a the verify counterpart. Execution: Claude Code, inside the attestation-boundary build order — this spec replaces the signing-surface portion of step 5; every other step stands.
Origin: the two-scope model (issuer seal / decision signature) initially shipped as two commands. The party analysis ruled key-per-party, role-per-signature: one human legitimately signs both scopes in one act, and act count should follow party count, not scope count. Two commands for one party manufactures ceremony and a half-signed seam. Ruling: one verb; `uofa decision sign` retires.

## 1. The surface

`uofa sign --key K --as <roles> [package]` is the single signing entry point.

| invocation | behavior |
|---|---|
| `uofa sign --key K pkg` (decision-free package) | byte-identical to current behavior — the whole document is the measurement view, so this IS the issuer seal. Regression-pinned. |
| `uofa sign --key K pkg` (decision-carrying package) | **refuses** per the concept guard; refusal names `--as` and the missing decision role — refuse-and-teach. |
| `uofa sign --key K --as issuer pkg` | issuer seal over the measurement view (document minus integrity fields minus the decision layer). Refuses on a decision-carrying package only if an `asserted` decision record exists with no decision role in `--as` (see §3). |
| `uofa sign --key K --as deciding-engineer pkg` | decision signature over `{measurementHash (recomputed), decision}` — requires an existing, verifying measurement seal (stale-bundle refusal preserved from the A6 design). |
| `uofa sign --key K --as issuer,deciding-engineer pkg` | the composed solo act: measurement seal first, then decision signature binding the recomputed hash. **Atomic**: both land or neither touches disk (temp-file-and-rename; no half-attested artifact ever exists). |
| `uofa sign --key K --as issuer,encoder-of-record pkg` | the Morrison solo form: seal plus transcription attestation. |

Role vocabulary is the closed set from the decision model: `issuer`, `deciding-engineer`, `concurring-reviewer`, `encoder-of-record`. An unknown role is a refusal, not a warning. Multi-party flows use separate invocations with separate keys — the demo Space runs `--as issuer` with its key; the reviewer runs their role with theirs. The composition is for one party wearing multiple hats; it is sugar over the same two signing paths, never a third mechanism.

## 1a. The verify counterpart

`uofa verify` is the read side of the consolidated surface. Current shape (`--pubkey` defaulting to `keys/research.pub`; `--decision-pubkey` scoped to "a SIP hasDecisionRecord signature"; `--context` as an ordinary flag) carries three misalignments, one urgent:

1. **The compromised default dies.** `--pubkey`'s default of `keys/research.pub` is removed **in the same commit that deletes the key** (the research.key escalation). New behavior: no silent default trust anchor. Bare `verify` with no `--pubkey` uses the wheel-shipped anchors and **names which anchor matched in the output** ("verified against: demo issuer anchor (fixture)") — a fallback is always named, never silent. The production issuer anchor is never the no-flag default, per the key-model ruling.
2. **`--decision-pubkey` generalizes and repeats.** Help text and behavior: verifies decision signatures on any decision-carrying package (the SIP scoping retires with `is_sip_bundle`, step 8). The flag is repeatable — stacked decisions (source acceptance + concurrence + encoder attestation) may carry signatures from multiple parties; each provided key matches by key identity, and unmatched decision signatures report as "signature present, no key provided to verify it" — distinct from invalid, per the unreadable-is-not-empty rule.
3. **Context resolution follows the document.** Bare verify reads the package's declared `@context`; `--context` becomes the explicit override; an undeclared-context package gets the named fallback line (the document's-own-context rule, applied to verify).
4. **The report is role-aware and fork-aware.** Per signature: scope, role (`issuer` / `deciding-engineer` / `encoder-of-record` / `concurring-reviewer`), signer key identity, verdict. Per decision record: the provenance fork (`asserted` → signature required and checked; `extracted` → anchor required and resolved). Plus the concentration line: same key across scopes reported as fact ("issuer and decision scopes signed by the same key — single-party configuration"); different keys report as independent attestation. Independence is derived from key identity, never key count.
5. **Report/refusal semantics seen red**: tampered measurement view fails both scopes (the A10 chain); tampered decision fails its signature; an asserted record with no signature reports incomplete; an extracted record with an unresolvable anchor reports failed, not absent. Exit codes documented in the CHANGELOG beside the sign-side contract change — third parties script against verify's codes above all.

Sign writes roles; verify reads them back and tells the truth about custody.

## 2. The removal

`uofa decision sign` is deleted — not aliased, not deprecated-with-warning — same rule as `engineerDecision`, contingent on the same class of gate:

**Step 0 (gates the removal): sweep for invocations** in scripts, docs, walks (`dev/walks/`), CI, deploy tooling, probe rails, and the PhysMAP-era specs. The Repair Stage spec names `uofa decision sign` as the prescribed path: that spec migrates on the author's queue like its siblings — note it in the sweep report, do not edit it. Any live caller migrates in the same commit as the removal. Decision rule: report the sweep before deleting; a caller that cannot migrate in-commit stops the removal and escalates.

CHANGELOG states the removal and the mapping (`uofa decision sign --key K` → `uofa sign --key K --as <role>`). Wheel version-bumps per release discipline. This is the second exit-code-contract change of the release (the concept guard was the first); the changelog says so plainly — third parties script against both.

## 3. Refusals (all seen red before believed)

1. Bare `sign` on a decision-carrying package → refuse, naming `--as` and the lawful roles.
2. `--as issuer` alone where an `asserted` decision record exists unsigned → refuse ("this package carries an asserted decision; add a decision role or have its decider sign separately") — never silently seal around an unsigned verdict.
3. `--as issuer` alone where the only decision records are `extracted` (Morrison-shaped, anchored, no live decider) → **permitted**: the seal excludes the decision layer, the extracted record's warrant is its anchor, and the encoder's attestation arrives via `encoder-of-record` when the encoding party signs. (The protocol check, not the signer, owns whether an encoder attestation is required for completeness.)
4. Wrong key class per the key-model rules → refuse both directions (issuer key on a decision role; reviewer key on the issuer role where the deployment's key policy binds classes — the demo's two-key separation test survives the consolidation).
5. Unknown role in `--as` → refuse, closed vocabulary named.
6. Decision role invoked with no verifying measurement seal present → refuse (stale-bundle rule, A6 preserved).
7. `signatureRole` absent from a decision signature → unrepresentable (the role is written by the signer from `--as`; there is no path that omits it).

## 4. Invariants, asserted by fixture

- **Equivalence**: composed `--as issuer,deciding-engineer` output is byte-identical in attestation structure to sequential (`--as issuer` then `--as deciding-engineer`) invocation. One fixture asserts it, always.
- **Atomicity**: kill the process between the two composed signatures (fault-injection fixture) — the package on disk is either fully pre-sign or fully signed; never intermediate.
- **Regression pin**: bare `sign` on the decision-free corpus (existing fixtures, sample packs) produces byte-identical output to the pre-consolidation wheel.
- **Verify unchanged**: `uofa verify` output is untouched by this spec — two scopes reported independently, roles on the record, same-key concentration across scopes reported as a fact (the solo configuration), different keys reported as independent attestation. Independence is derived from key identity, never key count or command shape.
- Every §3 refusal seen red first; every fixture from the decision-model amendment (Morrison two-entry, synthetic three-entry, ownerless-decision SHACL refusal, asserted-unsigned refusal, extracted-unanchored refusal) passes unchanged under the consolidated surface.

## 5. Docs (rides the §6 pass, same session)

- getting-started: one signing step, one command, roles explained in two sentences (issuer = the environment's custody claim; decision roles = a person's claim, named); the decision-free path shown first and unchanged. The verify step updated: no default anchor, the named-anchor line shown, `--decision-pubkey`'s general form.
- README: the two-question model's three sentences updated to the single-command form; verify's role-aware report shown once.
- The walks, deployed smoke, and probe rails update to the new invocations, both sides.
- CHANGELOG per §2, carrying both contract changes: sign's surface and verify's default-anchor removal and exit codes.

## 6. Out of scope

Per-user custody, trust anchors, revocation (enterprise tier, unchanged). The PhysMAP-era specs' prescriptions (author's queue). Any change to verify's semantics. Any numbered run — run 26 relaunches per the standing gate stack, its rails and pre-registration updated to the consolidated invocation.

## 7. One line for the record

Scopes are the format's business; commands are the party's. One party, one act, one command — two claims, each exactly its own size — and the signing surface now has the same shape as everything else in the system: roles as vocabulary, scopes as mechanics, refusals as the teacher.

## 8. ADDENDUM (2026-09-10) — the two-role surface: roles collapse to the boundary

Supersedes §1's four-role vocabulary and every partial message on roles. Ruled after the four-role set was built and five refusals were live; the collapse is a simplification of a working surface, not a redesign.

### 8.1 The ruling

**The role vocabulary is `issuer | reviewer` — two roles because two kinds of mind.** The four-role set declared facts the artifact already carries: deciding-engineer, concurring-reviewer, and encoder-of-record are all derivable by actor-match against the decision records and their provenance fork, and a declaration that can only agree with the record or lie is the two-sources-of-truth disease — with a live misdeclaration channel (sign your own verdict as encoder-of-record and ownership is softened in the permanent record, uncatchably, because the flag was the truth-source). The collapse closes that channel by construction.

- `--as issuer` — infrastructure key; seals the measurement view. The machine side of the boundary: custody, integrity, well-formedness — what machines can know.
- `--as reviewer` — person-class key; signs the decision layer. The human side: a named person stands behind judgment.
- Composed solo act: `--as issuer,reviewer`, atomic per §1. Morrison and Johnson are the same command; the difference lives in the records, where it always did.

**The relation is derived, never declared** (derive-never-declare-twice, applied to the signature layer):
- signer matches an `asserted` record's actor → **decider** ("decided by the signer")
- reviewer signature over extracted-only records → **transcription attestation** ("transcription attested; decision belongs to [source actor] per the cited passage")
- a second party signing their own stacked asserted record → **concurrence** (scoped to the prior record per `decisionScope`)
- verify computes and reports these as derived labels; they exist nowhere as stored claims. The words "encoder" and "concurrence" survive in verify's output only.

**Multiple reviewers are native**: records are repeatable and append-only; signatures are per-signer envelopes each binding the measurement hash; `--decision-pubkey` repeats; each signature covers its own claim (a later signer can never absorb or amend an earlier judgment); the concentration line generalizes — distinct keys report as independent parties, shared keys as single-party. The format records the stack; it never orchestrates it (who must sign, in what order, with what authority = the customer's QMS).

### 8.2 The thesis identity (why two, permanently)

The role axis now IS the machine/human boundary — the same single axis every layer enforces: escalation table at act, dual attribution at record, provenance tokens at claim, roles at seal. Consequences, all cheap because v0.9 is unreleased:
- **One axis, not two**: `signerKind` becomes the derived shadow of the role (or retires, with the role term carrying `infrastructure | person` semantics in its context definition). Never two fields that could disagree about which kind signed.
- **§12's principle form names the identity**: "attestation scope follows attestor kind — and the signing surface has exactly one role per kind." A future role proposal must argue against the boundary itself, not request a flag. A relation that genuinely isn't derivable (e.g., delegated signature under written authority) extends the model by a **record type**, never a role.
- **The docs' three-sentence model becomes the thesis verbatim**: machines seal evidence; only a person signs a judgment; the command has one word for each.

### 8.3 Build deltas

1. **v0.9 edits before it ships** (unreleased — an edit, not a version bump): `signatureRole`'s four-value vocabulary retires; the envelope carries the two-role axis with `infrastructure | person` semantics defined in the context; derived relations are verify-output only.
2. **Refusals re-pinned under the two-role set, all seen red again**: wrong key class both directions (unchanged); unknown role refuses naming `issuer, reviewer`; §3.2/§3.3 (refuse sealing around unsigned asserted; permit sealing over extracted-only) unchanged — they never depended on role names.
3. **The derivation function is constitutional surface**: it is the only place decider/encoder/concurrence exist, so it is fixture-pinned against both canonical cases plus the three-entry stack — which now carries **two distinct reviewer keys** so derivation and independence reporting are both exercised before any real second party exists.
4. **Actor-representation hygiene is load-bearing**: actor-match requires disciplined identity strings/IRIs (the `file://`-path bug class would corrupt derivation) — one fixture asserts the match survives the canonical identity forms and refuses on malformed ones.
5. **Regression and equivalence pins re-assert** under the new flags; the canonical cases re-pin (same acts, same records, simpler flags); getting-started teaches two words.

### 8.4 One line

The signature layer ends with as many roles as the thesis has kinds — two — and that is the strongest form of the match: not aligned with the boundary, made of it.

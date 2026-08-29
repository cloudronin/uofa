# Changelog — Unit of Assurance (UoFA) Specification

All notable changes to this project are documented here.

## [Unreleased]

## [0.16.0] — 2026-08-28

### Added

- **`Prompt hash`, scoped to the instructions.** `ExtractionResult` now carries
  `prompt_sha256`, and `uofa extract` prints it. The digest is over the prompt's
  **instruction half only, excluding the corpus** — `prompt_instructions()` is
  defined as `build_prompt("")` so it cannot drift from the assembly it digests.

  The scoping is the design. A digest over the assembled prompt moves with the
  source document: two runs given identical instructions on two papers report
  different prompts, and the only pair that could ever match is two runs on the
  same paper — the one comparison a prompt identity is not needed for. Scoped to
  the instructions, the field answers what it is named for: were these two
  extractions told to do the same thing?

  It is printed rather than exposed only on the result object because a consumer
  reads run-log facts from this output and must not recompute them. Writing what
  we asked for when we cannot tell what answered is the defect A-3 exists to
  prevent, and it applies to the prompt exactly as it applies to the model. The
  keyless path prints nothing: it sends no prompt, and a hash there would
  describe instructions that do not exist.

  Recorded because it was not. Every package emitted to date carries
  `Prompt hash: _not recorded_`, so no two runs could be compared on "same
  prompt" and a comparability check could only answer UNANSWERABLE. Found
  independently from the other side by an unsteered stranger session, which read
  its own run log after extraction and filed the gap as an escalation.

## [0.15.0] — 2026-08-28

### Changed

- **A recorded absence is not a missing judgment.** Both level checks —
  `required levels were reviewed` (workbook) and `required levels were judged`
  (package) — counted a DISPOSED requirement as an unjudged one. A reviewer who
  recorded that a document does not state a requirement was told they had not
  weighed it, so the only lawful exit from "there is no level here to weigh" was
  refused at the next gate.

  Two rules, and the second is what stops the first becoming the defect it
  replaced. A disposition leaves the **denominator** — exclusion is not judgment
  credit, and nothing is counted as weighed that was not weighed. And every
  message **names** what it excluded, how many, and under which term: a
  denominator that quietly shrinks is exactly the vacuity this checker exists to
  refuse. A package that disposed of everything renders as an advisory saying so,
  never as a green tick over nothing judged.

  `source-absent` has been in v0.8's vocabulary since it shipped and was always
  read as a silence; that half is a straight bug fix on published v0.8.

  **Breaking**: `protocol-check` outcomes change for packages carrying
  disposition tokens, and third parties script against these exit codes.

- **`CONTEXT_URL` is now a function of the workbook's declaration.** `uofa
  import` transcribes a sheet; nothing it writes is newer than what the sheet
  held, so stamping the current vocabulary on an older workbook claims
  conformance to rules that content was never authored against — and would
  subject it to five decision-model shapes introduced at v0.9 that it never
  claimed to satisfy. This is the jurisdiction doctrine `_apply_jurisdiction`
  already enforces, read from the emitter's side. A workbook declaring nothing
  gets the oldest supported context, not the newest.

- **`WORKBOOK_PROFILE_VERSION` v0.8 → v0.9.** The sheet's contract changed: the
  provenance column can now carry `not-recoverable`.

### Added

- **`not-recoverable`, at v0.9.** The source DOES state this requirement, and
  the admitted text cannot carry it — a different fact about the document than
  `source-absent`, which asserts the source never stated it. Recording one as the
  other is a false claim about the evidence, not a rounding. Three reviewers met
  exactly this and each invented a different unsatisfactory route, because the
  honest act had no form to take.

- **`uofa:retiredIn` — the jurisdiction bound that did not exist.**
  `introducedIn` can only widen a rule forward, so the day a CLOSED set grows,
  the shape enumerating it has exactly the two options `_apply_jurisdiction`'s
  own docstring rejects: widen the published list, and v0.8 documents start
  accepting a term v0.8 cannot mean; or leave it, and v0.9 documents are refused
  for using v0.9's own vocabulary. A retired shape is superseded rather than
  deleted — it keeps judging the documents it had jurisdiction over and stops at
  the rule that replaced it. `RequiredLevelProvenanceShape` is retired in v0.9
  and `RequiredLevelProvenanceV09Shape` takes over; not one byte of v0.8's
  conformance story changes.

- **The vocabulary is closed at the DECLARED version, at both ends.** A v0.8
  sheet writing `not-recoverable` has its token dropped rather than laundered
  into a package whose context makes the term legal, and the levels check names
  the disagreement instead of reporting the honest reviewer as negligent.

  The out-of-vocabulary refusal is deliberately narrow — terms this vocabulary
  knows that the declaration predates, not everything unrecognised. `confirmed`
  is the specimen: the encoding tool's location act, excluded from every version
  on purpose. A workbook full of it is run 25 with seventeen levels anchored and
  none weighed, and that package must be refused as UNJUDGED by the message that
  sends the reviewer to weigh them.

- **Every context the emitter can write is pinned**, not only the default. Which
  context a package is signed against is now a function of its source, so
  guarding one name would leave the others editable with nothing noticing —
  the single failure `test_context_pin` exists to prevent.

## [0.14.2] — 2026-08-26

### Added

- **`package_policy.sign_package_scoped`** — the two-scope act for a service.
  `sign_package` produces one signature over the whole document and
  `assert_issuable` refuses it for anything carrying a judgment, so a hosted
  product emitting decision records had **no path through the policy layer at
  all**: the only signer a UI is supposed to call could not sign what the UI
  makes. This seals the measurement view, signs each asserted record with the
  reviewer key, and is atomic — a package sealed with its verdict unsigned states
  something nobody meant. A reviewer key is optional; without one the package is
  sealed and honestly owed, which is the lawful multi-party interim.

  It routes on what the package carries, exactly as verify does. An earlier draft
  used the measurement-view hash unconditionally, so decision-**free** packages
  were sealed under a scope no verifier checks them against: correctly signed,
  reported broken.

- **In-memory keys throughout.** `fingerprint_from_private_key` and
  `sign_decision_records` accept PEM bytes: a hosted deployment receives its key
  as a secret and must never write it to the filesystem it serves downloads from,
  so a path-only accessor forced exactly the write it was avoiding.

### Fixed

- **A release could only be published by a tag push, and nothing else.**
  `release-wheels.yml` already accepted `workflow_dispatch`, but its publish and
  validate jobs required `github.event_name == 'push'` — so a manual re-run
  built every wheel, ran every smoke test, and then skipped the upload. The
  manual path existed and could not finish the job.

  That went unnoticed until `v0.14.1`'s tag push produced **no workflow run at
  all** (cause still unexplained; `v0.14.0`'s identical push had fired
  normally). With no dispatch path to publish and a public tag that must not be
  mutated, the release had nowhere to go.

  Both jobs now gate on the **ref** rather than the trigger: only a tag ships,
  but a tag ships however the run was started. `v0.14.1` is therefore skipped on
  PyPI — the version exists as a signed git tag and nothing else.


## [0.14.1] — 2026-08-26

### Changed

- **Release tags are signed, and the checklist enforces it.** v0.14.0 was tagged
  with `git tag -a`, which annotates without signing. Every commit underneath was
  SSH-signed, but the release marker itself carried no attestation — in the
  release that formalized *attestation scope follows attestor kind*. A program
  whose thesis is scoped attestation should not ship unattested release markers.

  v0.14.0 stands as published: a mutated public marker is precisely the
  tamper-shape this format exists to refuse, so the signature arrives as **this**
  tag rather than by replacing one PyPI has already seen. `v0.12.0` was signed
  and set the better precedent; the discipline drifted because nothing enforced
  it, so `release_check.py` gains a **tag signing** check — it verifies the repo
  *can* sign before you tag, and that an existing tag *did*.

  No functional change to the CLI. 0.14.0 remains valid and installable.


## [0.14.0] — 2026-08-25

### Added

- **`spec/context/v0.9.jsonld`** (160 terms) — the decision model. Built additively
  from v0.8: nothing existing was changed or removed, so v0.8 pins stay valid and
  every package signed against them still verifies.

- **`uofa decision record`** — authoring a decision as its own act: criterion,
  value, actor, timestamp, provenance `asserted`, no key and no signature. Records
  are append-only at the CLI: a bundle already carrying one is refused unless
  `--append` says the second entry is deliberate.

- **`uofa verify` rebuilt as the read side of the two-scope model.** Per decision
  record it reports the fork and whether the warrant that fork owes is present and
  good; `--decision-pubkey` is repeatable, since stacked decisions carry signatures
  from several parties. The distinctions are kept apart deliberately: *no key
  provided* ≠ *none of the provided keys matched* ≠ *invalid*, and an asserted
  record with no signature reports **incomplete, not invalid**. A closing line
  states custody as fact — same key across scopes is a "single-party
  configuration", different keys are "independent attestation" — derived from key
  identity, never key count.

- **The identity grammar** (`sign_roles.classify_identity`) — one definition read
  by the actor-hygiene guard and the relation derivation alike, and transcribed
  into the Attestation Model reference *from the guard's own fixture*, with a test
  that fails if the two drift. Comparison is whole-string: two reviewers sharing a
  handle under different authorities are different parties, and a normaliser that
  fused them would produce no error at all — just a confident, wrong relation.

### Changed — breaking

- **No silent default trust anchor** (the second exit-code contract change of this
  release). `--pubkey` had defaulted to `keys/research.pub`, so "verified" was a
  claim whose subject the reader could not recover. There is no default now: with
  `--pubkey` the caller named the key, and without one the shipped anchors are
  tried and **the match is named in the output**. A fallback is always named,
  never silent.


- **`uofa decision sign` is removed. Authoring and attesting are two commands.**
  The old command did both in one act: it took `--criterion`/`--value`, built the
  decision record, and signed it. The replacement is the honest pair — the
  migration is **two commands, not a renamed flag**:

  ```
  # before
  uofa decision sign PKG --key K --criterion C --value accepted --rationale R

  # after
  uofa decision record PKG --criterion C --value accepted --rationale R \
      --actor https://your.org/org/<handle>
  uofa sign PKG --key K --as reviewer
  ```

  `decision record` takes no key and writes no signature; `sign --as reviewer`
  signs records that already exist. Scripts that expected one invocation must add
  the second, and must now supply `--actor`: who decided is a fact about the
  judgment, and the old command could only infer it from whoever held the key.

- **A decision record now carries `actor` and `decisionProvenance`; the SIP
  bundle schema requires them and no longer requires a signature.** The signature
  left the *shape* contract because authoring legitimately precedes attestation;
  completeness moved to the package gate, which refuses to seal around an
  asserted record nobody has signed (exit 2). `decisionProvenance` is the fork
  naming which warrant is owed: `asserted` requires a decision signature,
  `extracted` requires a sha-pinned anchor and the source never signs.

- **`uofa sign` refuses a decision-carrying package without `--as`** (exit 2). An
  unscoped signature would span a human judgment, which AGENTS.md §12 forbids:
  attestation scope follows attestor kind. Roles are `issuer` and `reviewer`.

- **The two-party signing order was unreachable.** `--as issuer` refused while an
  asserted record was unsigned, and a decision role refused while no seal
  existed — so the issuer could not seal until the reviewer signed, and the
  reviewer could not sign until a seal existed. Both parties refused in both
  orders, and since excel packages emit asserted records, this was the ordinary
  flow. The refusal's rationale did not survive the architecture: the issuer
  seal covers the measurement view and **excludes the decision layer by
  construction**, so it never wraps the verdict and survives one arriving later.
  `uofa sign --as issuer` now seals with a named warning (*"sealing with N
  unsigned asserted decision record(s); decision signature owed"*), and
  completeness moved to where it belongs — `uofa check` reports **C1b Decision
  layer complete** and refuses the package until its decider signs. The
  stale-bundle rule (a decision signature binds the measurement hash, so a seal
  must exist first) is unchanged.

- **Shapes now declare their jurisdiction.** A shape carries `uofa:introducedIn`
  and never judges a document that declares an older context. Retroactive shapes
  made every published conformance claim expire silently whenever the model grew,
  and created pressure to edit shipped artifacts to satisfy rules that did not
  exist when they were written. A document whose declared version cannot be
  parsed gets **every** shape: ambiguity must not become an exemption. Applied on
  all three validation paths, `--raw` included.

- **A placeholder seal no longer reads as a seal.** `uofa import` writes
  zero-filled `hash`/`signature`, and the seal checks tested presence — so an
  all-zeros package passed as sealed. One shared definition now answers "has this
  been sealed", read by both the signer and `decision record`.

- **`uofa verify` now resolves decision anchors instead of asserting they resolve.**
  It checked that a locator and a digest were both present and reported
  `✓ anchor resolves` — which stayed green on a package whose pin had been
  replaced with garbage, because nothing ever opened the file. Resolve now means
  **open, hash, compare, report**, with three outcomes kept distinct: match →
  resolved (naming the file opened); mismatch → **failed**, naming the record and
  both hashes, and the package fails (a false transcription claim is exactly what
  the anchor exists to catch); source unavailable → **unresolvable**, which is
  neither green nor red — a stranger holding the package without its archive must
  not be told either "verified" or "tampered".

- **A synthetic adversarial sample is refused before any scope reasoning.** The
  decision-layer guard ran first, so the synthetic refusal was unreachable for
  any sample carrying a decision record — and the message told the operator to
  add `--as`, which reads as "you are one flag away from signing this". They are
  not: a synthetic sample is unsignable in every scope.

- **The scope routing and the concept guard disagreed about what a decision layer
  is.** `decision_records()` reads dicts; a package referencing its decision by
  IRI has none, while the guard saw the property plainly. Such a package sealed
  under the measurement-view scope and then verified under the whole-document
  scope — sealed cleanly, failed its own verification. Both now read
  `has_decision_layer()`.

### The finding list

Every defect this release closes belongs to one family: **a check correct on the
ordinary case and silent, vacuous, or wrong on the important one.** They are
listed together because the pattern is the point — each was found by reading a
check against the case it was supposed to catch, not by a failing test.

| where | what it did on the important case |
|---|---|
| `assert_issuable` | guarded the decision block by one spelling; the product emitted another, so the issuer key could sign over a human judgment |
| `unsigned_asserted` | compared against `"asserted"`, so a record declaring **nothing** passed the gate a declared one failed — and the excel path emitted forkless records by default |
| `assert_measurement_seal_present` | tested presence, so an all-zeros placeholder read as a seal |
| `verify_decision` | read only the legacy signature field, so correctly-signed packages reported as unsigned |
| `_resolve_anchor` | checked the pin was *present*, never opened the source — a check that could not fail, under the sentence Case 1 rests on |
| `check` C1 / `verify` C1 | two implementations of one question, drifting apart |
| `decision_records` vs the concept guard | disagreed on IRI-referenced decisions, so a package sealed under one scope and verified under the other |
| the synthetic refusal | ordered after the decision guard, so it was unreachable for decision-carrying samples |
| the context resolver | substituted a newer context for integrity, so intact packages read as tampered |
| SHACL shapes | judged documents written before the shapes existed |
| `test_decision_block_requires_signature` | deleted the signature and went red on a missing `actor` — a false pass proving something other than its name |
| `test_the_factor_shape_is_unreachable…` | a failure message claiming more than its assertion measured, which put a false "uofa#109 closed" into a status report |
| `check_workflow_paths` | audited `.github/workflows` paths and not `pyproject.toml`'s — the anchor rename broke every wheel build after the suite went green, because nothing local builds a wheel |
| the `morrison-v09` siblings | copied wholesale, so they claimed the frozen originals' IRIs: two documents at one identifier, pointing the praxis record's own citation at the wrong bytes. Invisible to SHACL (validates each file alone) and to the byte-freeze (watches the originals) |
| the `sh:or` profile dispatcher | its drill-in reports a branch's message, not necessarily the failing branch's — it named `CompleteBody` while the document was on `Minimal` |

Three of those landed **in this release**, found by guards outside the test
suite: hatchling's hard error on a missing include, and the site generator's
refusal to publish a package count or a namespace it was not told to expect.
Each demanded the change be *acknowledged* rather than absorbed. A 3365-test
suite proves the code does what it says; it does not prove the corpus, the
packaging manifest, or the IRI space still hold together, because no test owns
those.

**Also open, and now documented rather than accidental:** every profile —
including `ProfileMinimal` — requires `hasDecisionRecord` with `minCount 1`.
There is no profile under which a UofA package may lack a verdict. That is a
coherent position, but it means the shipped templates can never validate as
packages (they ship decision-free, since a template carrying a placeholder
verdict is an ownerless judgment). Belongs with [#109](https://github.com/cloudronin/uofa/issues/109)
in a profile-system session.

**Still open:** [uofa#109](https://github.com/cloudronin/uofa/issues/109) — the
CredibilityFactor shape remains unreachable for ProfileMinimal packages. It was
briefly and wrongly reported closed; it is not, and it does not close with this
release.

### Changed — shipped artifacts

- **Morrison's shipped examples are byte-frozen** and pinned by
  `tests/test_frozen_artifacts.py`. The praxis record's counts and its
  cross-version-verify claim are claims about *those bytes*. A new
  **`packs/vv40/examples/morrison-v09/`** sibling carries the same content under
  v0.9 — `decisionProvenance: "extracted"` plus an anchor whose sha256 is
  computed from the shipped `decision_rationale_cou{1,2}.pdf` — and is sealed in
  CI with throwaway fixture keys. No signature from Morrison's team exists or
  ever will; the anchor is their attestation.
- **Nagaraja ships no decision record.** No pinnable source states its decision,
  and anchoring to a paper's title would claim a passage says something it does
  not. A decision record is not owed by every package.
- **Templates ship decision-free.** A template carrying a placeholder verdict is
  an ownerless judgment by construction; the decision row is empty until a human
  fills it. `uofa decision record` is how a project fills it.

### Fixed
- **The seal gate was defeated by omitting the decision fork.** `unsigned_asserted`
  compared `decisionProvenance` against `"asserted"`, so a record that *declared*
  its fork was refused and a record that declared **nothing** passed — and
  `uofa import` emitted forkless records by default whenever the workbook had no
  anchor column, so omission was the ordinary path, not an edge case. An issuer
  seal would close over a human judgment nobody signed, which is precisely what
  the guard exists to prevent. Two changes close it: an anchorless workbook
  decision now emits `decisionProvenance: "asserted"` (a decision citing no source
  is one a live person entered), and `uofa sign --as issuer` refuses any record
  whose fork is absent or unrecognised, naming the form rather than exempting it.
  **Consequence:** excel-authored packages carrying a decision now require a
  decision signature before they can be sealed.


- **`uofa verify` reported correctly-signed packages as unsigned.** It read the
  legacy in-block `decisionSignature` string and did not understand the canonical
  `hasDecisionSignature` node the signing surface emits, so a package signed by
  `--as reviewer` verified as carrying no decision. It now reads both, checks the
  signature's embedded measurement hash against the recomputed one (the binding
  was otherwise decorative), and handles a repeatable `hasDecisionRecord` list
  instead of reporting "no block present" over several signed judgments.

- **The stale-bundle refusal (A-11) survived the command split.** `decision sign`
  recomputed the measurement hash and refused a bundle whose content had drifted
  from its seal; the unified surface at first checked only that a seal *existed*.
  Both `decision record` and `sign --as reviewer` now recompute — authoring
  refuses too, because a refusal that arrived only at signing time would leave
  the drifted package already carrying the verdict.

## [0.13.0] — 2026-08-24

### Changed — CONTRACT: `--protocol-check` can now fail a package that passed under 0.12

Third parties script against these exit codes, so the change is stated plainly
rather than left to be discovered.

- **New check, `required levels were judged`**, in `check_package`. A package
  whose declared `@context` is v0.8 or later is refused when any factor with a
  required level carries no judgment token (`affirmed`, `corrected`, `waived`)
  and no waiver is recorded. The message names the cells and the discharge path.
- **A package declaring an older context is ADVISED, never refused** on this
  check. Its vocabulary cannot state whether the judgment happened, and refusing
  it would punish age rather than negligence. The fork keys on the declared
  `@context`, not on `conformsToProfile` — that term carries the profile
  (Minimal/Complete/Disposition) and encodes no context version at all.
- **`check_workbook`'s levels check no longer infers from column shape.** It
  forks on the workbook's `Encoding Profile Version` declaration. A workbook
  declaring v0.8 with no provenance column is now refused as self-contradictory;
  previously it was indistinguishable from a legacy workbook and inherited the
  legacy excuse. A workbook carrying the column but declaring nothing is advised,
  and the advisory says the column was seen and why it went unread.
- **Equal required/achieved values are no longer evidence either way.** The old
  rule refused a package whose required level equalled its achieved level on
  every factor. Agreement writes nothing, so that reading refused a reviewer who
  read every level and agreed with all of them, and caught nothing else.

### Added

- **`spec/context/v0.8.jsonld`** — additive over v0.7 (143 terms, +4, nothing
  changed or removed): `requiredLevelProvenance` (flat token from a closed set),
  `LevelAffirmation` (activity class), `hasLevelAffirmation`, `affirmedAt`.
  `confirmed` is deliberately **not** in the vocabulary: it is an encoding
  tool's location act, and exporting it as a judgment claim is the ambiguity
  this version exists to remove.
- **`CONTEXT_URL` now names v0.8.** It had been pinned at v0.5 while the
  repository shipped v0.7, so every emitted package declared a context two
  versions behind what it was written against. v0.5.jsonld is untouched and
  still hashes to its pinned digest; packages signed against it keep verifying.
- **SHACL shapes for the v0.8 vocabulary** (`packs/core/shapes/uofa_shacl.ttl`):
  the closed token set, and a judgment token requiring a `hasLevelAffirmation`
  with `actor` and `affirmedAt`. Targeted on `uofa:CredibilityFactor` directly
  rather than through `CredibilityFactorShape`, which only ProfileComplete
  packages reach. No `sh:minCount` on the token — these shapes are
  version-agnostic and every pre-v0.8 package would fail one.
- **Workbook columns `Affirmed By` and `Affirmed At`**, read by the importer and
  emitted as the affirmation activity. A judgment claim carries its agent
  regardless of which carrier it travels in.

### Fixed

- **`rules`, `diff` and `mutation` validated against the toolchain's default
  context rather than the document's own.** That default was pinned at v0.5, so
  a v0.8 package was expanded against a vocabulary that does not define the
  terms being validated, and a v0.5 package validated against anything newer
  silently lost the fourteen terms v0.7 removed. Each now resolves the context
  the document declares; where none can be resolved, the fallback is the newest
  context shipped in the checkout and is **named in the output**, never silent.
  `--context` remains a deliberate override and still wins.
- **`uofa:actor` received a person's name where an IRI was required.** The term
  is declared `"@type": "@id"`, so JSON-LD resolved the string as a relative IRI
  against the document's location. `actor` now carries a minted IRI and `role`
  the readable name — the split `hasDecisionRecord` already used.
- **An out-of-vocabulary provenance token was emitted verbatim** rather than
  being rejected, so the closed set was not closed.


## [0.12.0] — 2026-08-20

### Added — the encoding protocol, and the mechanical half of it as a gate

- **`docs/Encoding_Protocol_v0_1.md`**: the procedure that turns one published
  source document into a signed-ready package that is evidence rather than
  opinion. Part A is thirteen executable steps, each ending in a check; Part B
  disposes the weakener firings Part A's last step produces, with a verdict rule
  per pattern family and an explicit mechanical-versus-judgment class; Part C is
  rationale, cited to the Johnson pilot by finding number. Part B's rules are
  calibrated against 71 recorded author adjudications, and the Calibration column
  says of each rule what it was derived from and which are not yet calibrated.
  An encoding records the protocol version that governed it, so a package encoded
  under v0.1 stays readable when v0.2 changes a rule.
- **`uofa extract --protocol-check` and `uofa import --protocol-check`**: the
  scriptable subset of that document, so no workbook reaches an author's review
  pass while it still fails something a machine could have caught. A flag rather
  than a command, because the checks have no state and nothing to orchestrate.
  The two commands behave differently on purpose: every check describes a
  *reviewed* workbook, and a freshly extracted one has no citation anchors
  because anchors are what review produces — so `extract` prints the table and
  leaves the exit code alone, while `import` treats the same checks as gates.
  Checks cover the anchor column and its per-row population, template
  placeholders left in data rows, required-equals-achieved on every factor
  without a waiver, the ambiguity log, the run log's lineage fields, and the
  minted namespace.
- **The namespace check names a domain family, not a string.** The importer's own
  warning fires on its `example.org` default, so an encoder can satisfy the
  warning and still miss the rule — a reserved example domain under a plausible
  subdomain reads like a real namespace and is one nobody controls. The whole
  RFC 2606 / RFC 6761 reserved family is refused. It reads the package's minted
  `id`, which sits inside the canonicalised content the signature covers, so the
  mistake is permanent rather than cosmetic.

### Added — evidence sealing for solver artifacts, without the solver

- **`uofa evidence inventory|seal`**: classify, digest and account for every file
  in an evidence folder and every member inside an Ansys Workbench `.wbpz`, with
  no vendor software, no licence, no network and no model. Establishes integrity,
  provenance and completeness *before* any extractor runs, which is the half of
  the claim that never needed a language model. Built against the three archives
  behind Nagaraja et al., *Methods* 225 (2024) 74-88 (<https://osf.io/n4pjz/>).
- **Content decides the kind; the suffix only breaks ties.** Not a preference:
  `document_reader._READERS` maps `.dat` to the plain-text reader, and a real
  Workbench project carries `dp0/act.dat`, which is HDF5 — under suffix routing
  that binary is decoded with `errors="replace"` and handed to an extractor as
  mojibake. Same for `.scdoc` (a zip that is really CAD geometry), `.wbdp` (XML
  sharing the project file's marker) and the saved result figures (PNG). Across
  a real 405 MB archive all 93 files are identified and none falls through to
  "unrecognised".
- **Everything streams.** That archive inventories in **6.7 s at a peak of
  50.5 MiB RSS, writing zero bytes to disk**. Members are hashed in chunks and
  read from the zip in place; nothing is unpacked. Three guards treat an evidence
  archive as untrusted input — path traversal, member count, and expansion
  checked both against the declared total and a running budget, because a zip's
  central directory is a claim rather than a fact.
- **An artifact with no reader is sealed and reported unread *with a reason*,
  never skipped.** The honest-blank contract from `keyless_extractor` applied to
  bytes: a manifest listing only what we understood would misrepresent a folder
  of proprietary archives as a small one.
- **Operator identity is redacted before anything else sees it.** A Workbench
  project file is a diary — the real ones carry usernames, machine names and the
  analyst's directory tree, matching contributors credited in the paper. Two
  one-way exits follow without this: the extraction corpus goes to a model, and
  the package gets signed and published. **Basenames survive on purpose**, because
  the strongest completeness evidence in the folder is the archive's own record
  naming `ds.dat`, `file.rst` and `solve.out` as stripped; redacting filenames
  would protect the operator by deleting the finding.
- **The stored messages are the solver log.** These archives were written without
  solution files, so `solve.out` does not exist — but the `.wbpj` carries 78
  stored messages in each small archive and 241 in the large one (154 errors, 85
  warnings), including weak springs added to reach a solution and a matrix
  coefficient ratio above 1e8. They are **solver-reported cautions**, never
  weakeners: that word names a catalog rule with an id, and this work mints none.
  A test greps the rendered corpus for catalog vocabulary and fails if any leaks.
- **Materials read with their declared units, never converted.** One library
  genuinely mixes them, and where two systems disagree both readings are shown.
  Material facts bind at `LIBRARY_ENTRY`, not certainty: the value is certainly in
  the file; that the published run *used* it is a claim the file does not make,
  and this library holds three mutually inconsistent titanium definitions.
- **`uofa evidence --claims` corroborates prose against the artifacts.** Against
  the paper's Table 5 it confirms Young's modulus 108,222 MPa, Poisson's ratio
  0.33, yield 967.5 MPa and tangent modulus 4,647 MPa, and reports two
  divergences. Comparisons happen only through the conversion table declared in
  `packs/vv40/pack.json`; an undeclared unit makes a pair `not-comparable` rather
  than coerced, because a silent conversion that is wrong produces an answer that
  validates. Divergences are reported, never adjudicated.
- **`uofa import --evidence` folds the seal in before the package is hashed**, so
  the manifest and pins sit inside the signature rather than beside it. Asserted
  the only way that means anything: edit one digest inside the sealed manifest and
  verification must fail. No term is added to `spec/context/v0.5.jsonld` —
  `@vocab` already expands these, and that file is inlined into the hash preimage.
- **One read-only panel in the Space**, calling the same `uofa_cli` code and
  attached after signing, so no rendering change can move a package hash.

### Changed

- `discover_files(max_depth=)` raised from 3 to 6. A Workbench tree puts its
  materials library four levels down at `proj_files/dp0/SYS-15/ENGD/`, so the old
  ceiling stopped one short of the evidence.
- Unreadable simulation formats are **named in a warning instead of dropped in
  silence**. Pointed at the real evidence folder, `uofa extract` previously exited
  1 with "No supported files found" — `.wbpz` was in neither `_READERS` nor
  `_DEFERRED_SUFFIXES`, so it fell through the unsupported-suffix `continue`
  without a word, which is the failure an operator is least able to diagnose.

### Fixed

- **`uofa extract --keyless` no longer demands `uofa setup`.** Its own contract is
  "no network call, no API key, no token spend", but the setup guard ran before
  the keyless branch, so the offline route was unreachable on a machine that had
  never downloaded a runtime — exactly the machine it exists for.
- **`text_reader` sniffs a BOM before trying UTF-8.** A UTF-16LE file does not
  raise under a UTF-8 read; it decodes to interleaved replacement characters, so
  the failure is silent and the mojibake travels on. Real solver evidence contains
  such a file.
- **The Nagaraja fixture recorded the wrong DOI.** `ground_truth.json` and
  `metadata.json` both carried `10.1016/j.jmbbm.2024.106640`, which resolves to an
  unrelated hip-prosthesis alloy FEA paper by different authors; the package's
  `10.1016/j.ymeth.2024.03.003` is correct. The `source_sha256` beside the wrong
  DOI was computed against that wrong document and is removed rather than left
  looking authoritative.

### Not added, on evidence — a result-file reader

`ansys-mapdl-reader` (MIT, no Ansys install, no licence) would have read `.rst`
binaries, and an `[ansys]` extra was planned for it. Inventorying all three
archives settled it: **none contains a solver result file, a solver log or an APDL
deck**, and every `MECH/` directory in all three is empty (8, 9 and 19 of them).
The 405 MB is almost entirely Mechanical databases — six `.mechdb` files of 121,
121, 86, 86, 86 and 50 MB, binary with no open-source reader. The extra would have
had nothing to open, so it is dropped rather than carried as an unused optional
dependency with a devcontainer and release-check cost. What it would have read is
sealed by digest and reported unread.

### Fixed — W-EP-01 guarded on a class the vocabulary does not declare

- **The `(?claim rdf:type uofa:Claim)` guard is removed. Disclosed post-freeze
  correction, ruled 2026-08-19 (R1a, `docs/UofA_Ch4_Numbers_and_Repairs_Spec_v1_0.md` §0).**

  **Window:** the guard landed **2026-04-27** (`205cc90e`, *"refine W-EP-01 to
  recall=1.0, nc_fpr=0.0"*) and stood until now.

  **Cause:** `uofa:Claim` is declared nowhere — not in `packs/core/shapes/uofa_shacl.ttl`,
  not in any context version. It reaches the `uofa:` namespace only through
  `@vocab`. The class the vocabulary *does* declare, and which the canonical
  examples use, is `uofa:AssuranceClaim`. These are different IRIs, so a
  correctly typed claim could never satisfy the guard.

  **Effect:** W-EP-01 stopped matching the 2026-04-26 adversarial corpus one day
  after that corpus was generated. **63 of 65 comparable packages diverged** from
  their recorded `rules_fired`, cascading into COMPOUND-01 (39 packages) and
  COMPOUND-03 (31), since both chain off another weakener having fired. Measured
  in [INV-21](docs/investigations/INV-21-claim-node-conventions.md).

  **Machine verification, pinned pre-fix:**
  `studies/phase3_stage4/w-ep-01-contrast/` — two fixtures identical but for the
  claim's type. The `Claim`-typed one fires W-EP-01; the `AssuranceClaim`-typed
  one is **silent**. The silence is the defect.

  **Why the guard was dropped rather than retargeted to `uofa:AssuranceClaim`:**
  the generator emits `type: Claim` *because* the guard required it. Only 2 of
  the 71 corpus packages define a claim node at all, both typed `Claim`, and both
  are the queue's W-EP-01 targets. Retargeting without regenerating the corpus
  would silence W-EP-01 on all 71 rather than fix it.

  **Measurements that precede this fix and are NOT re-run** (R1c): P25-A at
  v0.5.15.1 (`studies/phase2_5a/REPORT.md`), and the Phase 3 Stage 4 adjudication,
  which per R1b was adjudicated against recorded generation-time `rules_fired`
  and stands as ruled (`studies/phase3_stage4/REPORT.md`).

  **Behaviour delta**, measured across the seven canonical examples: W-EP-01
  newly fires on iso42001 cou1/cou2, morrison-cou1 and nagaraja-cou1, cascading
  into COMPOUND-01 and COMPOUND-03. morrison-cou2 and both surrogate examples are
  unchanged — their claims carry `prov:wasDerivedFrom`, so `noValue` correctly
  fails. **No rule outside W-EP-01, COMPOUND-01 and COMPOUND-03 changed.**

  **Baselines re-pinned:** the five `tests/fixtures/baseline_reports/cal-02*.json`
  §5.5 fixtures were regenerated. Every delta is confined to those same three
  patterns; the rest of each report, including the rules metadata, is
  byte-identical, so the serialization behaviour that test exists to guard is
  untouched. Pre-fix baselines are at ref `b23622af`.


### Fixed — the published weakener catalog under-reported two packs, and said nothing

- **`uofa catalog` reported 35 patterns across 4 packs. The correct answer is 57
  across 5.**

  **Window:** iso42001's `W-AIMS-*` rules landed **2026-05-06**
  (`10c83f6a`) and were under-reported from that day, through **0.9.0** and
  **0.11.0** — roughly three months and two releases. The model-credibility
  pack's 10 patterns were absent from the moment they were added.

  **Cause:** the catalog's pattern-id grammar was `W-[A-Z]+-\d{2}`, which cannot
  express either id shape the two packs use:

  | shape | example | pack |
  |---|---|---|
  | word-suffixed | `W-AIMS-AUDIT-STALE` | iso42001 — **12 of its 15 rules** |
  | three-segment | `W-EV-GEN-02` | model-credibility — all 10 |

  A box-drawing decorated header (`# ── W-EV-COU-05: …`) cost one more. Neither
  the rules nor the manifests were wrong; only the reader was.

  **Effect:** the catalog is the public list of what each pack detects, published
  to uofa.net and regenerated on every site build. Anyone consulting it to see
  what the ISO/IEC 42001 pack looks for saw **3 rules instead of 15**. The rules
  themselves always fired correctly — this was a reporting defect, not an engine
  one, so no assessment was ever wrong. What was wrong is what a reader was told
  the tool checks.

  **Why it went unnoticed for three months:** it failed *silently*.
  `_parse_rules_for_pack` returned `[]` for an unreadable pack and the pack
  simply did not appear in the output. There was no error, no warning, and no
  count to reconcile against — absence of a parse rendered as absence of rules.

  **Fix:** the grammar now spans both shapes and decorated headers, and the
  parser **reconciles against the manifest**: a pack that declares patternIds the
  parser could not find now raises rather than shipping a silently under-read
  catalog. Verified parsed == declared for all seven packs.


### Fixed — the shipped JSON Schema still demanded a field core had removed for causing fabrication

- **`spec/schemas/uofa.schema.json` required `hasContextOfUse` at the Minimal
  profile after core had stopped requiring it.**

  **Window:** the requirement was removed from core on **2026-08-08** and that
  removal shipped in **0.11.0 (2026-08-09)** — see "core is now
  standards-agnostic" below. The *derived* JSON Schema was never regenerated, so
  it kept the requirement for the whole of 0.11.0 until this release.

  **Effect:** anyone validating a package against the published schema — editor
  autocomplete, a CI step, any tool consuming `uofa.schema.json` — was still told
  that `hasContextOfUse` is mandatory at the Minimal profile. That is precisely
  the requirement core dropped because it meant no NASA-STD-7009A document could
  produce a valid package except by inventing the field, and two that did
  validated on a context of use a model had made up. The fix propagated to the
  SHACL and to core's behaviour; it did not propagate to the artifact that
  restates it, so the incentive to fabricate survived in the schema. Packages
  validated with `uofa check` were never affected — SHACL was correct throughout.
  Only the standalone JSON Schema was wrong.

  **Fix:** `uofa schema --emit json` now resolves active packs (it read core
  shapes only, while the committed artifact had been generated with `vv40`
  active, so regenerating it *also* silently deleted the `hasContextOfUse`
  definition and downgraded the `deviceClass` enum to a bare string —
  regeneration was lossy in one direction and stale in the other). The artifact
  is regenerated, `deviceClass` regains vv40's `"N/A"` value, and
  `tests/test_schema_regeneration.py` pins regeneration as a no-op so a derived
  artifact cannot drift from its source again.

## [0.11.0] — 2026-08-09

### Added — keyless extraction, and packages that say what they are

- **`uofa extract --keyless`**: extraction with no API key, no network and no model. Fills only fields with a route measured to beat a null model that reads nothing, and leaves the rest blank rather than guessing — every blank named in the run output. Ships its labelled training data (9,740 sentences, 0.55 MB) rather than a fitted estimator, so the classifier survives scikit-learn upgrades and can be read by anyone asking what it was taught. Validation results recall@5 **0.438** against a 0.125 control; decision outcome **0.917** balanced accuracy catching 5 of 6 rejections against a constant's 0. Per-factor levels are deliberately **not** emitted: the best keyless route reaches 0.100 end to end, and a wrong level validates exactly as well as a right one.
- **Field provenance on every package** (`uofa import` prints it always): each field records whether it was `extracted`, `run-context`, `defaulted` or `derived`. A conforming package can be mostly about the run that produced it, and this is the only place that shows.
- **Derived profile**: a package declares the highest profile its content satisfies rather than the one the extractor asserted. Every prior extraction declared `ProfileComplete` because the writer emitted "Complete". A package satisfying none now fails naming the missing fields instead of declaring a lower one it also does not meet.
- **Recorded pack set** (`validatedWithPacks`): a package carries the packs it was built under, so it validates the same way for everyone. Without `--pack`, `uofa shacl` uses the record and warns when it must assume.

### Changed — core is now standards-agnostic (**core pack 0.5.0 → 0.6.0**)

- `uofa:hasContextOfUse` **moved out of core** into `packs/vv40`. Core described itself as "Standards-agnostic" while every `UnitOfAssurance` profile required an ASME V&V 40 concept — so **no NASA-STD-7009A document could produce a valid package at any profile** except by inventing the field. Core now requires only what every standard shares. Behaviour for V&V 40 packages is unchanged, since `vv40` is the default active pack.
- **`packs/vv40` declares `coreCompatibility >=0.6.0`.** New core with an old vv40 would drop the context-of-use requirement entirely; this refuses that pairing.
- `prov:wasAttributedTo` is supplied by the run (operator identity), never from an extracted assessor name. A document that states who performed the assessment is still read, as `statedAssessor`.
- A missing Project Name defaults to the workbook stem with a warning instead of refusing the import.

### Fixed

- **The entity Identifier column kept the template's help text**, so `bindsRequirement` came out as `"Stable URI or local ID"` and satisfied its `minCount`. The same defect previously satisfied `wasDerivedFrom` for 27 of 27 packages with `"DOI, report number, or URI"`.
- `_merge_json_results` guarded a bare value when merging `credibility_factors` but not `assessment_summary` or `decision`; one un-wrapped field lost an entire chunked document.
- Two colliding `conftest` modules made `from conftest import ...` resolve to whichever imported first, failing two tests in any full run.
- The corpus dry-run crashed where no `pdflatex` exists instead of reporting that the render path went unchecked.

### Documentation

- README restructured to lead with the demo, then the on-ramp (extract → **review** → import → check), with relative links made absolute so they resolve on PyPI.
- **Extraction claims corrected.** The README reported `F1 = 1.000` / `0.964` figures that measure *detection* — and `control_constant_list`, which prints the standard's checklist and reads nothing, scores **1.000** on that. Replaced with measurements against annotated gold, each beside its control.

## Previously unreleased

### Added — Surrogate pack + Surrogate Interrogation Probe (SIP)

Surrogate-model credibility, in two separable workstreams joined only by a frozen evidence contract.

- **SIP evidence contract (G3 freeze)** ([`specs/sip_evidence_bundle_schema.json`](specs/sip_evidence_bundle_schema.json)): frozen JSON Schema for the SIP→pack integration boundary. **The firewall** (signature-scoped, Addendum A) — SIP measures, never judges — is enforced here: `additionalProperties:false` at every level, with the `FORBIDDEN_TOKENS` denylist ([`forbidden.py`](src/uofa_cli/interrogate/forbidden.py)) scoped to the *measurement region*. Decision content is valid only inside a signed `engineerDecision` block; anywhere else it is a breach. Exact-property-name matching, so `parentModelSnapshot.parentDecision` (inherited provenance) is legitimate.
- **SIP component** (`uofa interrogate`, behind the `[interrogate]` extra): thin model adapter (single `predict` contract — no native framework support), benchmark/reference loader, numpy-backed measurement orchestrator (residuals, envelope coverage, physics-constraint residuals, UQ calibration) with per-measurement provenance, and a packager that validates-then-signs (reusing ed25519/RDFC-1.0 signing) and attaches PROV-DM (no orphan entities → core `W-PROV-01` stays silent). The command emits the bundle, prints an at-a-glance surrogate-vs-reference comparison, and renders **no verdict**; there is deliberately no `--check`/`--decision`/threshold flag.
- **`packs/surrogate`** (pack 0.1.0, independent of CLI version): `uofa-surr:` vocabulary (additive/optional, `ProfileMinimal`-compatible). Weakener catalog reuses W-EP-03/W-AR-04/W-AL-02/W-ON-02 from core unchanged and adds **W-SURR-01** (physics-constraint evidence missing, High), **W-SURR-02** (unvalidated parent — severity split: Not Accepted → Critical, unrecorded → High), **W-SURR-03** (extrapolation beyond envelope, High; containment via an `_evalOutsideEnvelope` SPARQL pre-pass CONSTRUCT). W-SURR-04 + residuals-unlinked stay method-first CANDIDATES, not pre-implemented.
- **Productive-OOS** (`rules/oos/oos_v0.1.rules`, 2 rules: calibration-provenance, model-comparison), **coverage matrix** against the Jakeman-derived proto-taxonomy (`docs/UofA_Surrogate_ProtoTaxonomy_v0_1.md`) reported as fraction-detected with the emerging-reference caveat — **no Cohen's-κ claim**, and `cal-surr-01..05` calibration packages (W-SURR-02 exercises both severity arms).
- **AirfRANS dual-COU case study** ([`packs/surrogate/examples/airfrans/`](packs/surrogate/examples/airfrans/)): same surrogate in-distribution (COU1) vs Reynolds-extrapolation (COU2); sole weakener divergence is W-SURR-03, legible in one `uofa diff`. PDEBench breadth check gated behind a per-file CC-BY license precondition.
- **Firewall enforcement**: `dev/tools/scripts/firewall_guard.py` (imports the one token list, scoped to the measurement region) wired into `make all`; `AGENTS.md` §12 (signature-scoped + vendor conformance); `specs/` force-included into the wheel so the schema layer runs for pip-installed users (empirically gated by a wheel-content test). v1 staged ingestion renders a human-review view with `pass_fail`/Decision left for the reviewer and the canonical signed bundle linked.
- **Signed engineer decision + accuracy reporting (Addendum A)**: the firewall moved from a flat token denylist to a **signature-scoped** rule. New `uofa decision review` (read-only comparison, terminal silence) and `uofa decision sign --key <engineer-key>` write an `engineerDecision` block signed over the decision **plus the measurements it references** (`signing.py` two-scope signatures: measurement signature excludes the block so it survives a later decision; decision signature binds the recomputed measurement hash → tamper-evident); stale-bundle refusal, no default/headless decider identity (A8). `uofa verify` gained dual-signature verification (`--decision-pubkey`), reporting both signatures independently and treating an unverifiable decision as "no engineer decision," never package failure. New `uofa interrogate init` guided wizard (model detect → physical-I/O Q&A → adapter/scope/load-stub codegen → adapter smoke test; never silent-defaults scope, never fabricates reference; scope-provenance tags ride into the bundle). Vendor conformance is a checkable artifact property — the decision signature must be the deciding human's key — not a certification.
- **v2 native ingestion + end-to-end**: `src/uofa_cli/readers/sip_bundle_reader.py` verifies a SIP bundle's measurement (and, when a key is supplied, decision) signatures, then maps SIP §5 fields directly to surrogate-pack JSON-LD per the §7.4 field-to-pattern map (skipping the LLM step for measured fields); wired into `uofa import` (`--sip-pubkey`/`--decision-pubkey`). A full integration test drives `init → interrogate → decision review → decision sign → verify → import → check` over the real CLI, with W-SURR-03 + W-SURR-01 firing on the imported COU.

### Added — AirfRANS corpus harness (Experiment A)

A top-level `harness/` package (product/conference track, **not** wired into the CLI or praxis tiers) that turns the structural pack into a **measured result**: train an honest surrogate, drive SIP + `uofa check` over a corpus, and compute the true-error gap between cases where the envelope weakener **W-SURR-03 fired** and cases where it did not. Reuses W-SURR-03, SIP's orchestrator, the signed-bundle flow, and `interrogate init`'s template adapter — no reimplementation.

- **Honest surrogate + corpus** ([`harness/train_surrogate.py`](harness/train_surrogate.py), [`harness/datasets.py`](harness/datasets.py)): a plain sklearn `MLPRegressor` (no torch/GPU, not tuned for extrapolation — the degradation *is* the experiment) trained only on the in-envelope split; the declared envelope is the train-split bounds exactly (no test-range leakage, asserted). A synthetic generator with honest physics (linear pre-stall, collapse past stall, well-behaved low side) exercises the whole machinery offline; [`harness/airfrans_pull.py`](harness/airfrans_pull.py) pulls the real ODbL data (gated, never committed; cite arXiv:2212.07564).
- **Split selection (Step 0)** ([`harness/select_split.py`](harness/select_split.py), `make airfrans-select`): trains on each extrapolation task and reports true Cl/Cd error vs the extrapolation parameter; picks the split with the largest, most-uniformly-elevated out-of-envelope error (default AoA on physical grounds, confirmed empirically). **AoA asymmetry is reported honestly** — the high (stall) side degrades hard, the low side stays flagged-but-fine; the full-split number is reported and the low side is never silently dropped to inflate the gap.
- **Corpus run + error gap** ([`harness/run_corpus.py`](harness/run_corpus.py), [`harness/error_gap.py`](harness/error_gap.py)): per case, build a COU → `run_interrogation` → signed bundle → read **W-SURR-03 fired?** from the real `check.run_structured(...).rules.firings` (never recomputed) → record pred/ref/true-error rows to a committable CSV+JSONL table. The gap is a mechanical partition + pure arithmetic (median/IQR/mean per group, fired÷unfired ratio per coefficient) plus a plausibility check showing flagged predictions look physically believable while their true error is large — the invisible-danger trap. The report carries **no threshold/verdict/pass-fail token** (reuses `FORBIDDEN_TOKENS`) and states its scope: out-of-envelope inadequacy only.
- **CLI + make targets** (`python -m harness <pull|select|train|corpus|gap>`; `make airfrans-pull|airfrans-select|airfrans-train|airfrans-corpus|airfrans-gap`), `[interrogate-corpus]` extra extended with scikit-learn/joblib/matplotlib. Tests cover the mechanical partition, pure-arithmetic gap, no-LLM-in-harness guard, no-verdict report, no-envelope-leakage, and one engine-gated synthetic E2E through the full `interrogate → import → check → gap` path.
- **First real measured result** ([`harness/results/reynolds_extrapolation/`](harness/results/reynolds_extrapolation/)): ran the full pipeline on the real AirfRANS dataset (`airfrans` 0.1.5.1, ODbL). Step 0 chose the **Reynolds** split empirically (out-of-envelope Cd-error elevation 2.2× vs AoA's 1.6×) over the AoA default. Over 597 evaluation cases (498 fired W-SURR-03, 99 not), flagged-case median true error is **2.0× (Cl) / 2.2× (Cd)** the unflagged-case error, with 165 flagged predictions plausible-looking yet measurably wrong (the invisible-danger trap). Honest aside: on the AoA task the degradation concentrated on the **low**-AoA side, not the high/stall side — reported as the data shows. The derived per-case table is committed with ODbL attribution; raw AirfRANS is not.

### Fixed

- **`uofa check` now runs the derivation pre-pass and OOS engine.** The CLI `check.run()` was a legacy path that ran the Jena rules on the un-enriched package and never ran derivations or OOS — only `check.run_structured()` did. As a result, derived-flag weakeners and OOS findings did not surface for users running `uofa check` directly. `run()` now delegates to `run_structured()` and renders the full `CheckResult` (adding a C2.5 derivation line + an OOS section). Packs that declare neither (vv40, nasa-7009b) are byte-unchanged and exit codes are preserved (firings never affect exit code). Newly surfaced under `uofa check`: surrogate **W-SURR-03**, and iso42001's derived-flag **W-AIMS** rules (data-drift, lineage, model-eval staleness/scope, audit staleness, …) plus its productive-OOS findings.

## [0.9.0] — 2026-05-26

### Added — ISO 42001 pack

New `packs/iso42001` pack for AI management system assurance (AIMS). Phase A–F build-out:

- **Pack scaffold + vocabulary** ([`packs/iso42001/`](packs/iso42001/)): SHACL profile, vocabulary extensions for AI management system constructs, and `ProfileMinimal` switch for compatibility with v0.5 context.
- **C3 weakener catalog** (Phase B): forward-chaining patterns for AI risk management gaps. Pattern IDs follow `W-AIMS-*` naming.
- **OOS bundle-sufficiency rules** (Phase C, 8 rules): out-of-scope detection for AI-system bundle coverage.
- **NIST AI RMF GOVERN coverage matrix** (Phase D): dual-detection across categories with calibrated thresholds.
- **`cal-aims-*` calibration packages** (Phase E, 8 packages + supplier-evidence rule 9): per-category calibration fixtures with positive/negative/boundary tests.
- **Hybrid case study** (Phase F): COU1 + COU2 worked example illustrating the dual-COU pattern under iso42001.
- **End-to-end test suite** (Phase G): 58 tests, all passing.
- **Coverage validation harness** (Phase H): coverage matrix verification.

Phase 5.x follow-ups: brittleness oracle proving v0.4 W-AIMS rules miss on triggering fixtures; pre-pass `CONSTRUCT` file with manifest-declared derivations; eight W-AIMS rules migrated to consume derived flags; post-migration detection tests confirming Gx.2.a coverage flips P→Y. Pack version stamped at 0.5.0 (independent of CLI release).

### Added — Adversarial judge module

New `src/uofa_cli/adversarial/` subsystem for multi-judge adjudication of credibility decisions:

- **litellm-first refactor** routing through a vendor-neutral provider abstraction.
- **Production trio + arbiter**: Gemini 2.5 Pro, Mistral Large 2, Sambanova-hosted Llama 4; Phase 4 Waves E–I production-readiness work.
- **TPM-aware concurrency tracker** with per-judge daily caps and per-vendor concurrency limits for multi-day production runs.
- **Stage 1 / Stage 5 calibration**: prompt v1.6 with thinking-mode UNCERTAIN anchors, schema-coercion expansion, retry semantics.
- **Capability table + cost reading** for Llama 4 (override path) and other non-standard providers.
- **Stratified pilot runner** for Phase 2 sampling; full-panel smoke + raw_response cost fix.

### Added — Productive-OOS substrate

New `src/uofa_cli/oos/` substrate-validation module ([`feat(oos)` 80f91d0](commits/80f91d0)). Productionizes out-of-scope detection with bundle-sufficiency validation feeding the rule engine.

### Added — Derivation pre-pass engine

New `src/uofa_cli/derivations/` Python orchestration paired with `net.uofa.derive.DerivationEngine` on the JVM side:

- Config-driven dispatcher routing derivation rules across pre-pass passes.
- Manifest-declared derivations with snapshotting; backward-compatible with v0.4 packs.
- CLI flags to wire pre-pass into `uofa check`.

### Added — E2E test chains

Real-LLM end-to-end tests now chain the full pipeline:

- VV40 Morrison: `extract → import → check → rules` for both COUs ([`test(e2e)` daaf00d](commits/daaf00d)).
- NASA aero: `extract → import → rules → diff` for both COUs ([`test(e2e)` f78675b](commits/f78675b)).
- Morrison fixtures split into per-COU evidence folders; COU2 extraction ground truth added.
- Real-LLM model is parameterized via `UOFA_E2E_MODEL` for swap-in across providers.

### Added — Agent operational rules

`AGENTS.md` at repo root codifies operational rules for AI coding agents and human contributors. Notable: §11 tracks out-of-scope work in GitHub Issues; explicit prohibition on AI-tool attribution in commits, docs, and frontmatter.

### Changed — Extract prompts

`packs/vv40/prompts/vv40_extract_prompt.txt` and `packs/nasa-7009b/prompts/nasa_7009b_extract_prompt.txt` tightened to reduce LLM enum-echo and template-placeholder leakage. Closes #20 and #21.

### Fixed — Import

- **Synthetic Namespace for `--check`** was missing the public key plus build metadata; fixed so signature verification succeeds on `import --check` ([1b673cb](commits/1b673cb)).
- **LLM enum-echo + template-placeholder leak** during import. The importer now rejects values that literally echo the prompt enum or carry unresolved `{{placeholder}}` markers, and surfaces the offending cell. Closes #24 ([27ec134](commits/27ec134)).
- **Missing `Requirement` entity** synthesized from Assessment Summary when the workbook omits an explicit Requirement row ([8f61d29](commits/8f61d29)).
- **LLM `evidence_type` vocabulary** normalized against the canonical enum, fixing case- and synonym-drift on extracted values ([1a0e831](commits/1a0e831)).

### Fixed — SHACL

- **OR-constraint drilling**: `pyshacl` reports OR failures as a single rolled-up message; the friendly reporter now drills into the inner branches to surface which underlying field failed ([5cfdfb4](commits/5cfdfb4)).
- **`--raw` output** now appends the drilled-in inner failures after the standard pyshacl text, instead of replacing it ([2c0a2bc](commits/2c0a2bc)).

### Fixed — Extract

- **Structured-output path dropped**: the v4-kv prompt format conflicts with litellm structured-output mode; `uofa extract` now always uses free-form completion with the kv parser ([7b0f41c](commits/7b0f41c)).
- **`--output` directory handling**: `extract` now accepts a directory target and validates the `.xlsx` extension on file targets ([ee8fa80](commits/ee8fa80)).

### Fixed — LLM backend

- **Ollama-only `think` kwarg**: dropped before forwarding to litellm so non-Ollama providers no longer reject the request ([10bd970](commits/10bd970)).

### Fixed — Adversarial judge

- Production runs now match calibration on `thinking_enabled`; `prompt_template_version` pinned into production runs.
- `additionalProperties` stripped at nested-object level in JSON schemas sent to providers.
- Per-task streaming writes in concurrent path; hf-llama switched to direct Sambanova Cloud API.
- Mistral and Gemini provider verification: model IDs corrected, nullable-array transform, `if/then` stripping.

### Fixed — CI and tests

- **E2E import paths**: `tests.` prefix dropped from cross-imports so CI test collection no longer breaks ([d90c52c](commits/d90c52c)).
- **`diff` exit codes**: e2e checks tightened to assert `rc == 0` since `uofa diff` never returns 1 ([8fb1992](commits/8fb1992)).
- **Aero real-LLM assertions** relaxed to plumbing + parsed `diff` stdout, avoiding model-output flakiness.
- **`fix(test)`** subprocess timeout bound on the extract end-to-end test.
- **Devcontainer** installs `[judge]` extras for adversarial-judge tests, with `skipif` guards where appropriate.

### Documentation

- Site: new Extract on-ramp flow on the homepage; Excel on-ramp page reframed as the Authoring on-ramp (extract → review → import).

## [0.8.0] — 2026-05-04

### Added — Extract eval v1 (synthetic corpus + held-out test)

50-bundle synthetic eval corpus stratified across (standard × domain × quality × format) at [`tests/fixtures/extract_corpus/`](tests/fixtures/extract_corpus/), with sentinel-locked held-out test set and a 2-step Claude-driven generator at [`dev/tools/scripts/generate_extract_corpus.py`](dev/tools/scripts/generate_extract_corpus.py).

Frozen v4-kv prompt achieves on dev/test:
- Mean F1: 0.964 / 0.954
- Per-factor F1: 1.000 across all 19 factors (V&V 40 + NASA-7009b)
- Bundle-level crash rate: 0 / 50
- Morrison regression: F1 = 1.000
- Aero cou1 regression: F1 = 0.973

Writeup at [`docs/extract_eval_v1.md`](docs/extract_eval_v1.md). Batch eval harness at [`dev/tools/scripts/score_extraction_batch.py`](dev/tools/scripts/score_extraction_batch.py) with confusion analysis, per-factor stats, and held-out-set guards (refuses to score `test/` unless `--allow-test` is passed AND prompt-version contains neither `iter` nor `dev`).

### Changed — Extract prompts: nested JSON → key-value blocks

`packs/vv40/prompts/vv40_extract_prompt.txt` and `packs/nasa-7009b/prompts/nasa_7009b_extract_prompt.txt` rewritten to emit `=== SECTION ===` blocks containing flat `key: value` lines instead of nested `{value, confidence, source_file, source_page}` JSON objects.

Local qwen3.5:4b dropped 1-2 closing braces ~25-33% of the time on the previous JSON format, causing irrecoverable parse failures (10/30 dev bundles crashed in the last JSON baseline). The kv format eliminates the nested-structure failure class and runs ~2.5-3× faster (less verbose output).

Downstream `_to_field` and `_validate_factor` already accepted flat strings, so xlsx and JSON-LD writers needed no changes. Backwards-compatible with the JSON format via fallback in `_parse_response`.

### Fixed — `uofa extract` performance and reliability

- **`.md` files now supported** as evidence input ([`document_reader.py`](src/uofa_cli/document_reader.py)). Uses the existing text reader. Markdown is a common engineering doc format; previously `extract` exited "No supported files found" on a folder of `.md`.
- **Adaptive `num_ctx` for ollama** ([`litellm_backend.py`](src/uofa_cli/llm/litellm_backend.py)). Previously the daemon defaulted to the model's max (262K for qwen3.5 = 17 GB VRAM, 5-6× slower per token). Now sized to the actual prompt + output budget, bucketed to 8K/16K/32K/49K/65K to avoid model reloads on consecutive similar calls. Bounds VRAM at ~8 GB. Override via `options.extra["num_ctx"]`.
- **`max_tokens` cap of 16384** for extract calls. Without this cap, ollama defaulted to unlimited generation; verbose models could ramble past a complete response.
- **`think=False` default for ollama extract calls**. qwen3.5 (and other Qwen3-family) models have thinking-mode ON by default at the daemon level, generating 5-10× silent reasoning tokens. Letting that through caused ~22 min/bundle wall time on local extract; explicit `think=False` brought it to ~7 min/bundle for the same output.
- **Tolerant JSON parser** in `_parse_response` for the JSON-format fallback path. Adds string-aware brace counting + progressive prefix truncation, recovering when output occasionally drops trailing braces.
- **Retry on parse failure** (3 stochastic attempts) wraps the LLM call. Belt-and-suspenders with the kv format and tolerant parser.
- **`_ROOT` path bug** in `dev/tools/scripts/score_extraction.py` introduced by the April 29 `tools/` → `dev/tools/` reorganization, which made the script resolve fixtures to `dev/tools/tests/fixtures/...` (doesn't exist).

### Cost vs. spec

Synthetic corpus generated for **$6.13** (Sonnet 4.6) vs. spec's $23 estimate. Iteration ran on local qwen3.5:4b — $0 inference cost.

## [0.5.0] — 2026-04-21

### Added — v0.5 JSON-LD context

- **New optional vocabulary** (`spec/context/v0.5.jsonld`): 12 additions backing the expanded weakener catalog. All backward-compatible — every v0.4 property is preserved; new properties are optional at the SHACL level.
  - Data vintage / model revision: `dataVintage`, `modelRevisionDate`
  - Evidence timestamps: `evidenceTimestamp`, `signatureTimestamp`
  - Provenance marking: `isFoundationalEvidence`
  - Model versioning: `modelVersion` (on ModelConfiguration)
  - Sensitivity + activities: `hasSensitivityAnalysis`, `hasVerificationActivity`
  - Identifier resolution: `referencesIdentifier`
  - Staged CLARISSA vocabulary for v0.6 W-AR-06/W-AR-07: `residualRiskJustification`, `consideredAlternative`, `knownLimitation`

### Added — Weakener catalog expansion (12 → 23 patterns)

Eleven new weakener patterns join the `packs/core` catalog. All validated via unit-test fixtures under `tests/fixtures/weakeners/` (27 tests pass) plus inline Morrison regression (see `docs/v0.5-morrison-deltas.md`).

- **W-ON-02** (High) — Unbounded Applicability: COU lacks both `hasApplicabilityConstraint` and `hasOperatingEnvelope`.
- **W-AR-03** (High) — Inference Method Mismatch: requirement's `requiredVerificationMethod` differs from generating activity's `activityType`.
- **W-AR-04** (High) — Model Version Drift: `ModelConfiguration.modelVersion` ≠ UofA's `currentModelVersion`.
- **W-AL-02** (Medium) — Sensitivity Gap: UQ declared but no `hasSensitivityAnalysis` linked.
- **W-EP-03** (High) — Stale Input Data: dataset `dataVintage` predates UofA `modelRevisionDate`.
- **W-CON-01** (High) — Factor-Decision Consistency: `Accepted` decision with credibility factors lacking both `requiredLevel` and `achievedLevel`.
- **W-CON-03** (High) — Future-dated Evidence: `evidenceTimestamp` > UofA `signatureTimestamp`.
- **W-CON-04** (Medium) — Profile-Structure Consistency: Complete profile with no `hasSensitivityAnalysis` (single-branch v0.5; broader enumeration deferred to v0.6).
- **W-CON-02** (Medium, **Python**) — Identifier Resolution: `referencesIdentifier` target neither resolves locally nor has an external-fetch hint.
- **W-CON-05** (High, **Python**) — Activity-Evidence Consistency: `hasVerificationActivity` declared with no evidence linked via `prov:wasGeneratedBy`.
- **W-PROV-01** (Critical, **Python**) — Provenance Chain Incomplete: BFS upstream from `bindsClaim` — emit at nodes without upstream edges that are not marked `uofa:isFoundationalEvidence=true`.

### Added — CLI

- **`uofa catalog`** — enumerates all weakener patterns across active packs. `--format json` for machine-readable output. Covers Jena rules and Python-implemented rules. Satisfies the "catalog CLI" deliverable.

### Changed — Morrison regression deltas

| | v0.4.0-nafems (baseline) | v0.5.0-pre-phase2 | Delta |
|---|---|---|---|
| Morrison COU1 | 14 | 24 | +10 (W-ON-02 + W-CON-01×6 + W-CON-04 + COMPOUND-01×2 cascades) |
| Morrison COU2 | 6 | 16 | +10 (W-ON-02 + W-AL-02 + W-CON-04 + W-PROV-01×7) |

Per-rule attribution in `docs/v0.5-morrison-deltas.md`.

### Release-branch discipline

- **Frozen reference tag** `v0.4.0-nafems` (on commit `e11b2b4`) preserves the exact state used for NAFEMS demo slide screenshots. All screenshots regenerated from v0.5 will show different counts; the demo runs from the frozen tag regardless.
- **v0.5.0-pre-phase2** tag lands on `main` as the Phase 2 experimental baseline.

### Known limitations

- Python post-pass rules (W-PROV-01, W-CON-02, W-CON-05) do not feed back into the Jena `COMPOUND-01` cascade. Python-generated Critical weakeners are reported but not paired with Jena-detected High weakeners via the existing compound rule. Compound cascade across engines is deferred to v0.6.
- W-CON-04 ships one branch (Complete profile missing SensitivityAnalysis). Broader ProfileComplete structural enumeration is deferred to v0.6 once distinct semantics beyond SHACL enforcement are settled.
- W-CON-02 limits identifier resolution to the local graph plus HTTP(S) URL self-documentation; no HTTP fetch attempts in v0.5.
- COMPOUND-02 (Factor Credibility Erosion) remains deferred (commented out in `packs/core/rules/uofa_weakener.rules`). `uofa catalog` filters it out.

## [0.4.1] — 2026-04-04
### Added
- **`uofa import` command:** Imports practitioner-filled Excel workbooks into signed, validated JSON-LD UofA artifacts. Supports VV40 (13 factors) and NASA-STD-7009B (19 factors) packs, v2 evidence types (`ReviewActivity`, `ProcessAttestation`, `DeploymentRecord`, `InputPedigreeLink`), automatic URI generation, `assessmentPhase` assignment, and `ImportActivity` provenance tracking. Optional `--sign` and `--check` flags for one-command import-sign-validate workflow.
- **`uofa schema --emit python`:** Generates `excel_constants.py` from SHACL shapes (factor names, level ranges, dropdown enums, evidence types). Keeps import validation in sync with SHACL — no manual constant maintenance.
- **Excel import pipeline modules:** `excel_reader.py` (parse + validate workbooks), `excel_mapper.py` (intermediate dict → JSON-LD), `excel_constants.py` (generated from SHACL).
- **`openpyxl` optional dependency:** `pip install uofa-cli[excel]` for Excel import support.
- **Test corpus:** 15 programmatic Excel test fixtures with manifest-driven parametrized test runner (106 tests covering happy paths, error cases, NASA factors, and URI generation).

## [0.4] — 2026-04-02
### Added
- **NASA-STD-7009B support:** New `packs/nasa-7009b/` domain pack with 19 credibility factors (13 shared with V&V 40 + 6 NASA-only), 6 NASA-specific weakener rules (W-NASA-01 through W-NASA-06), and SHACL shapes enforcing CAS level range 0-4 and assessment phase requirement.
- **Multi-pack CLI support:** `--pack` flag now accepts multiple values (`--pack vv40 --pack nasa-7009b`). SHACL shapes and Jena rules from all specified packs are loaded as a union.
- **`uofa migrate` command:** Upgrades v0.3 JSON-LD files to v0.4 (updates context URL, adds `factorStandard` to each CredibilityFactor). Supports `--dry-run`.
- **v0.4 JSON-LD context** (`spec/context/v0.4.jsonld`): 3 new properties (`factorStandard`, `assessmentPhase`, `hasEvidence`) and 4 new evidence classes (`ReviewActivity`, `ProcessAttestation`, `DeploymentRecord`, `InputPedigreeLink`) with supporting properties.
- **V&V 40 domain pack** (`packs/vv40/`): Extracted V&V 40 factor taxonomy (13 factors, level range 1-5) from core into its own pack.
- **Aerospace example** (`examples/aerospace/uofa-aero-nasa7009b.jsonld`): Demonstrates multi-standard assessment with all 19 factors, evidence classes, and multi-pack validation.
- **Evidence class SHACL shapes:** ReviewActivityShape, ProcessAttestationShape, DeploymentRecordShape, InputPedigreeLinkShape added to core shapes.
- **W-NASA pattern IDs:** WeakenerAnnotation patternId regex updated to accept `W-NASA-NN` format.

### Changed
- **Core pack is now standards-agnostic:** `packs/core/pack.json` no longer lists specific standards or constrains factorType to V&V 40 values. Factor taxonomy enforcement is delegated to domain packs.
- **Default pack is `vv40`:** When no `--pack` flag is specified, the CLI defaults to `--pack vv40` for backward compatibility with v0.3 behavior.
- **Morrison examples upgraded to v0.4:** Context URL updated, `factorStandard: "ASME-VV40-2018"` added to all CredibilityFactor entries.
- **All skeleton templates and starters updated** to v0.4 context and factorStandard.

## [0.3] — 2026-04-01
### Added
- **13-factor expansion:** Morrison COUs now encode all 13 V&V 40 credibility factors (7 assessed + 6 not-assessed), up from the original 7.
- **W-EP-04 weakener pattern:** Detects unassessed credibility factors at elevated model risk (MRL > 2). Fires 6 times on COU2 (MRL 5) but not on COU1 (MRL 2) — the core risk-driven divergence demonstration.
- **`uofa diff` command:** Compares weakener profiles across two COUs with identity block, divergence table (core + compound patterns separated), severity summary, and divergence explanations from the rule engine.
- **Domain packs system:** SHACL shapes, Jena rules, templates, and prompts organized into modular packs under `packs/`. Core pack ships with 13 factors and 13 weakener patterns.
- **`uofa init` command:** Scaffolds new UofA projects with template JSON-LD, signing keys, and `.gitignore`.
- **`uofa packs` command:** Lists and inspects installed domain packs.
- **Starter examples:** Real-world starter templates under `examples/starters/`.

### Changed
- **`uofa diff` now runs Jena rules dynamically** instead of reading static `hasWeakener` arrays from JSON-LD files.
- **Morrison COU1 weakener profile:** 14 weakeners across 6 patterns (4 Critical, 10 High). Compound patterns (COMPOUND-01, COMPOUND-03) fire via chained forward-chaining inference.
- **Morrison COU2 weakener profile:** 6 weakeners, all W-EP-04 (High) — fires on 6 unassessed factors at MRL 5.
- **COU divergence:** 7 divergent patterns between COU1 and COU2 (5 core + 2 compound), all divergent (no shared patterns).
- SHACL shapes and Jena rules moved from `spec/` to `packs/core/` with symlinks for backward compatibility.
- JSON-LD context updated to v0.3 (`spec/context/v0.3.jsonld`).

### Fixed
- Removed `@type: @id` from `acceptanceCriteria` context definition (was silently dropping strings).

## [0.1] — 2025-11-01
### Added
- Initial **UoFA** specification published at https://uofa.net (single-page canonical spec).
- Namespace established: `https://uofa.net/vocab#` with prefix `uofa`.
- JSON-LD Context released: `context/v0.1.jsonld`.
- JSON-LD Frame (skeleton) released: `schema/v0.1.jsonld`.
- Repository bootstrap: README, licensing (CC BY 4.0), example snippet.

### Notes
- This is a **draft** intended for early adopters and pilot implementations.
- Formal validation to be provided via **SHACL shapes** and/or a JSON Schema profile in a subsequent release.

[0.1]: https://uofa.net

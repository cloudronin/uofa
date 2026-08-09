# Making both extractors produce a valid package

**Status:** specification, not yet implemented. Revised 2026-08-08 after review;
the first draft's acceptance criteria were unreachable and its headline was
wrong. Every number here was measured against the five real papers.

---

## Finding 1 — core is not standards-agnostic, and says it is

`packs/core/pack.json` describes itself as **"Core credibility assessment rules.
Standards-agnostic."** Its shape file is not.

**Every `UnitOfAssurance` profile in core requires `uofa:hasContextOfUse`:**

| profile | required | requires `hasContextOfUse` |
|---|---|---|
| `MinimalBody` | 7 | **yes** |
| `CompleteBody` | 13 | **yes** |
| `DispositionBody` | 14 | **yes** |

Context of use is an ASME V&V 40 concept. **NASA-STD-7009A defines no such
thing** — measured, not assumed: the definitional route correctly returns nothing
on 9 of 10 and 4 of 4 seeded 7009A documents, and the two real 7009A papers carry
0 and 1 mentions of the term against 39, 33 and 50 for the three V&V 40 papers.

So **no 7009A document can produce a valid package at any profile**, and the two
that validated in the head-to-head did so on a context of use the model invented.
Two of the five real papers are 7009A.

### The fix is subtraction, not addition

The first draft of this spec proposed adding a fourth profile,
`ProfileNasaMinimal`, to core. That was implemented, proven to work, and
**reverted** — because it treats the symptom. Core would then carry *two*
standards' assumptions instead of one, and a core that enumerates standards is
not core.

The pack system already models this correctly everywhere else: `packs/vv40` and
`packs/nasa-7009b` each constrain `CredibilityFactor` in their own shape file.
Nothing standard-specific about `UnitOfAssurance` was ever done that way, which
is how a V&V 40 concept ended up in the core profiles.

### R0 — core carries no standard's vocabulary — **DONE**

`hasContextOfUse` removed from core's `MinimalBody` and `CompleteBody`
(`DispositionBody` follows by `sh:node`), and added to
`packs/vv40/shapes/vv40_shapes.ttl` as `VV40ContextOfUseShape`.

Minimal now requires **six**, none of them a single standard's vocabulary:

    bindsRequirement, hasValidationResult, hasDecisionRecord,
    generatedAtTime, hash, signature

Complete still requires **twelve** — it lost only the context of use.

**Zero regressions across all 64 packages** — 59 conforming before and after, the
same 5 failing.

**Why it is behaviour-preserving.** Shapes load as core + the *active* packs
(`paths.all_shacl_schemas`), and the default active set is `["vv40"]`. So a
default invocation loads the vv40 shape exactly where the core constraint used to
sit. Nothing about a V&V 40 package changes; what changes is that
`--pack nasa-7009b` no longer imports a V&V 40 assumption.

**A false premise that blocked this for a while, worth recording.** An earlier
draft called the targeting an open question, reasoning that "validation loads
several packs at once" so a vv40 shape would hit 7009A packages too. That was
never true of the tool — it was true of *my regression harness*, which loaded all
seven shape files. I inferred the system's behaviour from my own instrument's,
which is the same error as reading a stale measurement as a live one, and it also
meant the first baseline (55/64) was over-strict by four packages. The corrected
harness validates each package under core + its own pack, and reports **59/64**.

### R0b — a package must say which standard it is under **(new, and R0 is half a fix without it)**

**A package records nothing about its standard.** No `criteriaSet`, no standards
reference, nothing. Validation is therefore relative to a flag the operator
remembers to pass, and the default is `vv40`.

So after R0, a 7009A package validated as `uofa shacl pkg.jsonld` — no `--pack` —
**still gets the V&V 40 context-of-use requirement and still fails.** The
assumption left core; the default still applies it. R0's benefit currently
reaches only operators who know to type `--pack nasa-7009b`.

`uofa import` stamps the pack it built under into the package, and `uofa shacl` /
`uofa check` read it as the active set when no `--pack` is given, with an explicit
flag still overriding. A package then validates the same way for everyone,
including someone who received it and knows nothing about how it was made.

**Migration, and it decides how much R0b is worth.** All 64 existing packages
predate the stamp. `uofa shacl` on an unstamped package falls back to the `vv40`
default — the current behaviour — which means **every existing artefact keeps the
V&V 40 assumption R0 removed**, and R0b's guarantee holds only for packages built
after it. That is not acceptable for the two 7009A example packages in
`packs/nasa-7009b/examples/`, which are shipped artefacts demonstrating the
standard.

So: the fallback is `vv40` and it emits a warning naming the assumption it just
made, and **the 7009A example packages are restamped as part of this work**. The
remaining unstamped packages are V&V 40 anyway, so the fallback is correct for
them and the warning is the only change they see.

*Fails if:* the same package validates differently depending on who runs the
command, with no flag given — or if an unstamped package is validated under an
assumed standard without saying so.

### R0b-1 — move the pack default out of the parser — **DONE**

**Why the warning cannot fire.** `cli.py:132` reads

    args.active_packs = _pre_args.pack or args.pack or ["vv40"]

so the default is applied at *parse* time. By the time a command runs, an
explicit `--pack vv40` and a defaulted one are the same value, and "was a flag
given?" is no longer answerable. The warning that tells a user "no pack recorded,
I assumed vv40" is therefore unreachable — and until it fires, an unstamped 7009A
package still silently validates as V&V 40, which is the defect R0b exists to
close.

**The fix is one line, and it puts the default where the resolution already is:**

    args.active_packs = _pre_args.pack or args.pack or None

`paths.resolve_active_packs` already falls back correctly on `None` — explicit,
then the package's stamp, then `vv40`. The parser stops making a decision that
belongs to the resolver, and `None` becomes the honest signal for "not asked
for".

**What to check before doing it:** anything reading `args.active_packs` directly
rather than through `resolve_active_packs` will now see `None` where it expected
a list. Grep for it; there were three call sites at the time of writing.

*Fails if:* `uofa shacl` on an unstamped package prints no warning, or
`--pack vv40` prints one.

### R0b-2 — stamp the one shipped 7009A package — **DONE**

The three packages under `packs/nasa-7009b/examples/` are the artefacts that
demonstrate the standard, and they are exactly the ones the fallback gets wrong:
unstamped, they validate as V&V 40.

**The complication:** they carry `hash` and `signature`. Adding
`validatedWithPacks` changes the content, so both must be recomputed —
restamping is a re-signing, not an edit. `keys/research.key` is in the repo and
is what the test suite signs with.

    1. add "validatedWithPacks": ["nasa-7009b"] to each
    2. uofa sign <file> --key keys/research.key
    3. re-run profile_baseline.py --diff — expect NO verdict change, since
       nasa-7009b was already the correct pack for them
    4. grep the tests for a pinned hash of any of the three

Step 3 is the point. If a package's verdict *changes*, the stamp disagreed with
how it was actually being validated, and that is worth knowing before the file is
re-signed rather than after.

**Done.** `uofa-aero-fatigue-minimal.jsonld` carries
`validatedWithPacks: ["nasa-7009b"]` and is re-signed. All three checks pass —
**C1 integrity, C2 SHACL, and C3 rules at 42 inferred triples** — and it now
resolves to its own pack with no `--pack` flag. Zero regressions across 64
packages.

C3 is named deliberately. The first attempt passed C1 and C2 on a file whose
graph the rule engine read as one triple, and the acceptance criteria as written
never mentioned C3 — so every check that had been specified was green on a broken
artefact. It is the third of the three checks `uofa check` runs and the one
nobody thought to name.

**Correction, 2026-08-08.** This was closed on the reasoning that the three files
are not packages. That was over-general, and it came from the same detection bug
twice: a scan checking only `@type` while these files use compacted `type`.

**Two of the three are overlays; one is a real package.** `uofa-aero-cou1` and
`uofa-aero-cou2` carry no `UnitOfAssurance` node — which is why `uofa shacl`
passes them vacuously — but **`uofa-aero-fatigue-minimal` is a genuine package
and does need the stamp.** So R0b-2 is not closed; it is one file instead of
three. `tests/test_pack_stamp.py` pins which is which so the next attempt repeats
neither error.

The paragraph below is kept because its reasoning holds for the two overlays.

**On the two overlays.** They are **not packages**. They contain no
`uofa:UnitOfAssurance` node — they are weakener-annotation overlays referencing a
package IRI that lives elsewhere, which is why `uofa shacl` reports them
conforming (vacuously, finding nothing to check) and why there was nothing to
attach a pack stamp to. Restamping them is not a smaller version of this task;
it is a task about the wrong artefacts.

What remains true is the requirement behind it: **a 7009A package must carry its
pack stamp.** No such package currently exists in the repo to stamp. The stamp is
written by `excel_mapper` for every package built from now on, so this closes as
soon as a real 7009A package is produced — and the head-to-head's own gpt-5 and
keyless outputs are the first candidates.

**What happened on the first attempt, and why it was reverted.** The stamp went
in, the three files re-signed, hash and signature verified, and
`profile_baseline --diff` reported **no verdict change** — every check that had
been specified passed. Two tests outside that set then failed:
`TestWeakenerPins::test_aero_cou1_accept_fires_w_ar_02` and its cou2 pair, with
`uofa rules` reporting **"Inferred 0 new triples (1 total)"**. The rule engine
was seeing an empty graph.

The cause is in the stamping script, not in the idea. It looked for a node typed
`uofa:UnitOfAssurance` to attach the stamp to; **these packages contain no such
node at graph level**, so it fell through to a `target = d` default and stamped
the top-level document beside `hash` and `signature`. Re-signing over that
structure produced a file that verifies and validates and that the rule engine
cannot read.

**Three things this says for the retry:**

1. **Find out where the stamp actually belongs in these files first.** They are
   not shaped like the packages `excel_mapper` emits — no `@context`, full IRIs,
   18 graph nodes, no `UnitOfAssurance` node found by type. That difference is
   worth understanding before writing to them.
2. **A fall-through default in a script that edits signed artefacts is the bug.**
   `target = d` silently did something plausible instead of failing. It should
   raise.
3. **The specified checks were insufficient and passing them proved nothing.**
   Hash, signature, and the 64-package validation diff were all green on a file
   that had been broken. C2 and C1 do not exercise C3, and the acceptance for
   this item must include `uofa rules` — which is the third of the three checks
   `uofa check` runs, and the one nobody thought to name.

*Fails if:* a shipped example validates differently with and without `--pack
nasa-7009b` — or if C1 and C2 pass on it while C3 sees an empty graph.

### R0c — the version bump — **DONE, and it is not the version I first wrote**

An earlier draft said "core schema 0.7 → 0.8, touching `spec/context/v0.8.jsonld`".
That conflated three separate version series:

| artefact | series | did R0 change it? |
|---|---|---|
| `spec/context/vX.jsonld` | the JSON-LD **context** — term to IRI mappings | **no** |
| `packs/core/pack.json` | the **pack** shipping the shapes, at 0.5.0 | **yes** |
| `CONTEXT_URL` in `excel_constants` | what gets stamped into a package | no |

**R0 changed the shapes, not the vocabulary.** `hasContextOfUse` still exists as
a term with the same IRI; what moved is which shape requires it. A
`v0.8.jsonld` would have been byte-identical to `v0.7.jsonld`, which is
versioning that signals nothing.

So the bump is **`packs/core/pack.json` 0.5.0 → 0.6.0** — a minor version, because
core *removed* a requirement.

**And `packs/vv40/pack.json` declares `coreCompatibility: ">=0.6.0"`**, which is
the part that actually matters. The dangerous pairing is **new core with old
vv40**: core has given up the context-of-use requirement and an old vv40 does not
yet carry it, so every V&V 40 package silently stops being asked for one. That
combination is exactly what `coreCompatibility` exists to refuse, and without the
bump nothing would have refused it.

*(The reverse pairing — old core, new vv40 — applies the constraint twice, which
is harmless.)*

**Unrelated drift, found while doing this and not fixed here:** `CONTEXT_URL`
points at `spec/context/v0.5.jsonld` while the context series has reached v0.7.
Every package emitted since v0.6 has been stamped with a two-versions-stale
context. That predates this work and is out of its scope, but it should not go
unrecorded.

### The regression instrument

`dev/tools/scripts/profile_baseline.py` validates every package under **core plus
its own pack**, mirroring `all_shacl_schemas`, and diffs two runs. It exits
non-zero on any package that stops conforming, and also reports packages that
*start* conforming — silently making validation easier is how a shape stops
meaning anything.

Baseline: **64 packages, 59 conforming, 5 not — and of the 59, two pass
vacuously.**

A shape targeting `uofa:UnitOfAssurance` conforms on a file containing no such
node: it finds nothing to check and reports success. Three of the shipped
`nasa-7009b` "examples" are weakener-annotation overlays referencing a package
IRI that lives elsewhere, and `uofa shacl` calls them conforming. Without the
column, a pass on an empty file and a pass on a full package read identically —
`control_constant_list` scoring 1.000 in a new place.

**57 of 64 are real packages that met their profile**, and that is the number the
R0 regression result rests on.

---

## Finding 2 — a package validates when the extractor guesses

All five gpt-5 packages declare `ProfileComplete`. The two that pass C2 are
exactly the two where the model invented an **Assessor Name**:

| | profile | assessor | project | COU | SHACL |
|---|---|---|---|---|---|
| opensim | Complete | **yes** | yes | yes | **PASS** |
| bologna | Complete | — | yes | yes | fail |
| nagaraja | Complete | — | yes | yes | fail |
| elemance | Complete | **yes** | yes | yes | **PASS** |
| morrison | Complete | — | yes | yes | fail |

`excel_mapper.py:150` emits `prov:wasAttributedTo` only from `assessor_name`;
Complete requires it. Keyless fails earlier: `excel_reader.py:268` requires
Project Name even for Minimal, and keyless leaves it blank by design.

Neither is an extraction failure. Both are one category error: **fields
describing the assessment are demanded of a component that reads the document**,
and an extractor can satisfy them only by making them up.

*(The two 7009A packages passing here is not a contradiction of Finding 1: they
pass because their extractions happen to carry a `cou_name` string the model
produced. Under R4 that string should not exist, and when it stops existing
those two will fail until R0 lands. **The validity rate is expected to get worse
before it gets better**, and an implementation that does not show that dip has
probably kept the fabrication.)*

---

## The principle: three classes of field

| class | who knows it | rule |
|---|---|---|
| **document-derived** | the paper | extract, or leave blank with a reason |
| **run-context** | the invocation | supply from the run |
| **author-decision** | a person | prompt, or refuse; never infer |

| field | class |
|---|---|
| `hasContextOfUse`, `hasCredibilityFactor`, `hasValidationResult`, `hasDecisionRecord`, `bindsModel`, `bindsDataset`, `modelRiskLevel` | document-derived |
| `wasDerivedFrom`, `generatedAtTime`, `hash`, `signature`, `wasAttributedTo` | run-context |
| `project_name`, `bindsRequirement`, `conformsToProfile` | author-decision |

---

## Requirements

### R1 — operator identity is run-context; a stated assessor is evidence

`prov:wasAttributedTo` is supplied by `uofa import` from, in order: `--assessor`,
the `[assessment] assessor` config key, `git config user.name`, `$USER`. **An
extracted assessor name may never satisfy it** — that field is who ran the tool,
and an extractor cannot know it.

But a document *may state who performed the assessment*, and NTRS credibility
reports often do. That is a real document-derived fact and reading it is not the
error; using it as the operator's identity is. Extractors record it as
`statedAssessor`, an extracted fact, distinct from `wasAttributedTo`. R5 keeps
the two distinguishable in the output.

*Fails if:* any package validates on an assessor the extractor produced.

### R2 — `project_name` defaults to something true

Default to the source document's filename stem, recorded as `defaulted`, not as
a reading. A user renaming it is doing the intended thing; a user never seeing a
package because it lacked a name is not.

*Fails if:* import refuses a package whose only defect is an unnamed project.

### R3 — the declared profile is derived, with a floor

Import computes the highest profile the content actually satisfies and declares
that. **Order: Disposition, Complete, Minimal.**

**Profile derivation is pack-aware.** After R0 the required set depends on the
active packs — a V&V 40 package must carry a context of use and a 7009A package
must not be asked for one — so "the highest profile the content satisfies" is
only answerable against a declared pack set. This is why R0b is a prerequisite
rather than a convenience: without a recorded pack, derivation would compute a
different profile depending on who ran it.

There is no NASA-specific profile: R0 removes the V&V 40 concept from core rather than adding a second profile beside it, so 7009A packages reach the same Minimal every other standard reaches.

*Why Disposition ranks highest:* it is `CompleteBody` plus `hasDisposition`
(`sh:node` inheritance, verified), so it is strictly the most demanding. Zero
packages currently adopt it — which is a fact about adoption, not about rank, and
ranking by what a shape demands rather than by what is popular is what keeps the
order stable as adoption changes.

**The floor:** a package satisfying no profile **fails loudly**, naming the
closest profile and the fields it lacks. It must never declare nothing, and never
declare a profile it does not meet. Until R0 lands this is the common case for
7009A, so the message is the primary user-facing output for those documents, not
an edge case.

*Fails if:* any package declares a profile whose required fields it lacks, or a
non-conformant package exits without naming what is missing.

### R4b — the synthesized Requirement carries the template's placeholder **(open, diagnosed)**

A keyless package now imports and reports C1, C2 and C3 green — and the C2 pass
is not real:

    bindsRequirement    "Stable URI or local ID"

**That is the template's own help text satisfying a minCount**, and it is the
identical defect already on this project's record: `wasDerivedFrom` was satisfied
for 27 of 27 packages by *"DOI, report number, or URI"*. Same failure, different
field, alive today.

**The synthesis itself is legitimate and should stay.** It dates to May 2026: an
LLM dropped the Requirement entity, the importer hard-failed, and the fix was to
synthesize one from `cou_name` + `cou_description` with a warning. The COU is
real document content, so a Requirement built from it is derived, not invented.
The synthesized row reads:

    Requirement | "<the COU text>" | "Stable URI or local ID" | "Auto-synthesized from COU"

Name and description are genuine. **Only the Identifier/URI column is wrong** — it
carries the template placeholder, and `bindsRequirement` maps from that column.

**The fix is narrow:** the synthesized row must leave the identifier blank, or
mint one from the COU slug the way every other entity URI is minted. A blank
identifier fails validation naming `bindsRequirement`, which is the honest
outcome and the one the boundary table already predicts.

**What it means for the boundary table.** That table lists keyless at 5 of
Minimal's 6, blocked on `bindsRequirement`. That is what SHOULD be true and is
not what happens: the field is filled with placeholder text and the package
passes. Until R4b lands, **every validity figure in this document rests on a
shape a help string can satisfy** — including the gpt-5 2-of-5.

*Fails if:* any emitted identifier appears in the template's help row, or a
package validates on a `bindsRequirement` no one supplied.

### R4 — no blank is filled to satisfy a count

R1–R3 supply what the tool genuinely knows. Nothing authorises filling a
document-derived field with a plausible value. Keyless factor levels stay blank:
the best keyless route reaches **0.100 end to end**, and a wrong level that
validates is worse than a blank one that does not.

*Fails if:* a validation rate rises by emitting a value no route was measured to
produce.

### R5 — every field records its class, and the counts are mandatory output

Each emitted field carries `method`: `extracted`, `run-context`, `defaulted`,
`author-supplied`, or `absent`. `uofa import --check` prints the per-class counts
**always**, not under a verbose flag.

A package validating on 6 run-context fields and 2 extracted ones is a different
artefact from one validating on 8 extracted fields, and today they are
indistinguishable. This is what stops R1–R3 from becoming a way to make the
numbers look better.

*Fails if:* a validating package cannot be asked how much of it was read.

### R6 — the null control, and what the batch harness supplies

**The null control.** An extractor that reads nothing and emits nothing, run
through R1–R3, scores **0 of 5** — Minimal needs three document-derived fields
that no run-context default can supply. This must be *measured and printed*
beside the two extractors, not asserted. Every other metric in this project
carries a null model, and the one that was skipped here is the one that would
have caught the first draft's impossible acceptance table.

**The harness.** R1, R2 and `bindsRequirement` are interactive or run-context,
and nobody answers a prompt in a batch run. `keyless_vs_model.py` declares exactly
what it supplies — `--assessor "batch-harness"`, project name from the filename —
and prints R5's per-class counts. Without that the head-to-head measures the
harness defaults rather than the extractors.

**`bindsRequirement` stays absent, and the harness must not paper over it.** An
earlier draft left it absent AND set "at Minimal" acceptance targets, so every
batch package failed Minimal and every target was 0 before anything ran. The
resolution is not to have the harness invent a requirement to make the number
move — that is R4's exact prohibition — but to report the boundary instead of a
rate. Acceptance now does. The harness prints `bindsRequirement: absent
(author-decision)` on every row, so the one field standing between a keyless
package and Minimal is visible rather than buried in a failure count.

*Fails if:* the null control is absent from the comparison, or the harness's
contributions are not separable from the extractors'.

---

## Acceptance — the boundary, not a pass rate

The first two drafts set pass-rate targets. Both were unreachable, for different
reasons, and the second was unreachable **by construction of the harness this
same spec specifies**: R6 leaves `bindsRequirement` absent, Minimal requires it,
so every batch-run package fails Minimal and every "at Minimal" row was 0 before
anyone ran anything. That is the third time in this document's history that two of
its own requirements have contradicted, and the pattern is now clear enough to
name: **a target expressed as a rate invites engineering the rate.**

So acceptance is the boundary. Per path, which of Minimal's six fields it
produces and what blocks the rest.

| Minimal requires | class | gpt-5 | keyless |
|---|---|---|---|
| `generatedAtTime` | run-context | ✅ | ✅ |
| `hash` | run-context | ✅ | ✅ |
| `signature` | run-context | ✅ | ✅ |
| `hasValidationResult` | document-derived | ✅ | ✅ trained, recall@5 **0.438** vs 0.125 |
| `hasDecisionRecord` | document-derived | ✅ | ✅ trained, **0.917** balanced, 5 of 6 rejections |
| `bindsRequirement` | **author-decision** | ✅ | ❌ **by design** |
| | | **6 of 6** | **5 of 6** |

**Keyless reaches five of six, and the sixth is a decision rather than a
failure.** `bindsRequirement` names the engineering requirement the model is
trusted to help satisfy; only 30% of papers cite a standard at all, and it was
settled as author-supplied on 2026-08-08. An extractor that emitted it would be
inventing it.

That is the boundary this investigation has been circling, and it is a more
useful result than a 5/5 that had to be engineered: **a keyless package is one
human-entered field away from Minimal, and that field is one no document
contains.**

**Invariants — these are still rates, because each has a null answer that is
correct:**

| | now | target |
|---|---|---|
| packages validating on an invented assessor | 2/5 | **0** |
| keyless factor levels emitted | 0/65 | **0/65 — unchanged** |
| null control (an extractor that reads nothing) | unmeasured | **0 of 6, printed** |
| packages whose verdict depends on who ran the command | unknown | **0** |

The null control is the check that would have caught both unreachable acceptance
tables, and it is the one this spec twice failed to specify.

## What this investigation learned about its own instruments

Six defects were found in the *measuring* apparatus during the work that produced
this spec — not in the extractors, in the things watching them. They are recorded
because they are why R5 and R6 exist, and because five of the six were mine.

| what was measured | what it actually measured | how it surfaced |
|---|---|---|
| K7 at 15/20 on train | a corpus regenerated **three times** since | re-ran it before quoting it |
| the shape's "open targeting question" | my harness loading all 7 shape files, which no invocation does | asked the user, who knew |
| baseline 55 of 64 conforming | the same over-strict harness — the truth is **59** | corrected the harness |
| keyless factor `status` "valid" | a test asserting the same underscore the code emitted | `uofa import` rejected all 12 rows |
| "keyless degrades without scikit-learn" | nothing — the blocker used `find_module`, dead in 3.12 | checked that the block worked |
| model rationale groundedness 0/0 | a dict shape the scorer silently skips | 0/0 was implausible on 13 rationales |

**Three of these produced a confident number that was wrong**, and none of them
raised an error. That is the shape of the risk this spec is written against: not
an extractor that fails loudly, but an instrument that reports success.

### What it implies for the requirements

**R5 (every field records its class) is not bookkeeping.** Two of the six above
were quantities that looked like extraction and were not — a stale corpus, a
harness default. Once packages are validating, "how much of this was read?" stops
being answerable by inspection, and the only defence is that each value says where
it came from at the time it was produced.

**R6 (the null control) is the one that keeps catching things.** It would have
caught both unreachable acceptance tables — a rate that is 0 by construction is
obvious the moment an empty extractor is scored beside a real one. This project
puts a null model against every other metric and skipped it here twice.

**And the discipline that found four of the six: run the check with the thing
removed.** The CI failures this session — a gitignored fixture, two colliding
`conftest` modules, a missing `pdflatex` — were all cases where the local
environment was a *superset* of the target's, so the cheap local check could not
reproduce the failure. A check whose environment is richer than the target's
cannot falsify anything about the target.

**One more, and it is the one that generalises furthest:** the keyless extractor
was tested as far as producing a spreadsheet and never through `uofa import` to a
package — the only artefact anyone wants. Every test passed while every workbook
was unimportable. **Test the pipeline, not the step**, and prefer the check that
can fail.

## Risks

- **R3 makes validation easier to pass.** Mitigated by R5: profile and per-class
  counts print together, so a package that dropped to Minimal is visibly one that
  dropped to Minimal.
- **R1 puts the operator's name in every package**, which may be shared. It must
  be overridable and visible in the output, never silently stamped.
- **R0 changes a shipped shape, and it MOVES a constraint rather than adding a
  branch.** The "an `sh:or` branch only adds ways to pass" argument belonged to
  the reverted fourth-profile approach and does not apply here. What makes R0 safe
  is narrower and worth stating exactly: **the default active pack set is
  `["vv40"]`, and the constraint landed in vv40** — so a default invocation loads
  it precisely where core's sat. Verified, not argued: 64 packages, 59 conforming
  before and after, no package changing verdict.
- **A valid package is still not a correct one.** This spec fixes where fields
  come from; it does not improve extraction. Groundedness of 0.988 measures
  whether numbers in a rationale appear in the source, not whether a level is
  right — and this project once reported `mean F1 0.964 — PASS` while 37 of 45
  packages failed the shape. Validity and correctness stay two numbers.

## Out of scope

Improving what either extractor reads. Keyless factor levels stay at 0.100 and
stay unemitted; `bindsRequirement` stays author-supplied. This spec makes the
pipeline produce a truthful package from what the extractors already manage, and
is not an argument that they manage enough.

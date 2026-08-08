# Making both extractors produce a valid package

**Status:** specification, not yet implemented. Every number here was measured on
2026-08-08 against the five real papers.

## The measurement this exists to fix

Both extraction paths were run over the five real documents and imported with
`uofa import --sign --check`.

| | packages that pass C2 SHACL |
|---|---|
| gpt-5 | **2 of 5** |
| keyless | **0 of 5** — refused at import |

## The diagnosis, and it is one sentence

**A package validates when the extractor invents a field the document does not
contain, and fails when it does not.**

All five gpt-5 packages declare `ProfileComplete`. The two that pass are exactly
the two where the model wrote something into **Assessor Name**:

| | profile | assessor | project | COU | SHACL |
|---|---|---|---|---|---|
| opensim | Complete | **yes** | yes | yes | **PASS** |
| bologna | Complete | — | yes | yes | fail |
| nagaraja | Complete | — | yes | yes | fail |
| elemance | Complete | **yes** | yes | yes | **PASS** |
| morrison | Complete | — | yes | yes | fail |

`excel_mapper.py:150` emits `prov:wasAttributedTo` **only** when `assessor_name`
is present. `ProfileComplete` requires it at `minCount 1`. So the failing three
fail on one field, and that field asks *who performed this assessment* — which is
not stated in a journal paper and cannot be read out of one.

Keyless fails earlier and for the same underlying reason: `excel_reader.py:268`
requires **Project Name** for even the Minimal profile, keyless leaves it blank
by design, and import refuses.

**Neither failure is an extraction failure.** Both are the same category error:
fields that describe *the assessment* are being demanded of a component that
reads *the document*.

## The principle: three classes of field, and they must not be mixed

| class | who knows it | rule |
|---|---|---|
| **document-derived** | the paper | extract it, or leave it blank with a reason |
| **run-context** | the invocation | **supply it from the run** — the tool knows this |
| **author-decision** | a person | prompt, or refuse; **never** infer |

The current design has no such distinction, so run-context and author-decision
fields fall to the extractor, and the only way for an extractor to satisfy them
is to make them up. That is precisely the incentive that produced 14
turbomachinery models labelled "Class II" that validated while packages honestly
writing "Turbomachinery (Centrifugal Pump)" failed.

### Where each required field belongs

| field | class | source |
|---|---|---|
| `hasContextOfUse`, `hasCredibilityFactor`, `hasValidationResult`, `hasDecisionRecord`, `bindsModel`, `bindsDataset`, `modelRiskLevel` | document-derived | the extractors, as now |
| `prov:wasDerivedFrom` | **run-context** | the input filenames — already fixed once |
| `prov:generatedAtTime` | **run-context** | the clock at signing |
| `uofa:hash`, `uofa:signature` | **run-context** | the signing key |
| `prov:wasAttributedTo` | **run-context** | **who is running the tool** |
| `project_name` | author-decision | prompt; default to the source document's title |
| `conformsToProfile` | author-decision | **derived, see R3** |
| `bindsRequirement` | author-decision | prompt; settled 2026-08-08 |

`wasAttributedTo` is the load-bearing move. It is the identity of the operator,
which the tool has and the paper does not — and treating it as document-derived
is what makes validity depend on a guess.

---

## Requirements

### R1 — `wasAttributedTo` comes from the run, never from the document

`uofa import` supplies it from, in order: `--assessor`, the `[assessment]
assessor` config key, `git config user.name`, `$USER`. It is recorded with
`method: "run-context"` so a reader can tell it was not read from the paper.

**The extractors stop emitting Assessor Name entirely.** gpt-5 currently invents
one on 2 of 5 papers, and those inventions are the only reason those two
validate — a fabricated attribution is worse than a missing one, because it
names someone.

*Fails if:* a package still validates on an assessor the model invented.

### R2 — `project_name` defaults to something true

Blank is the honest answer for a keyless extractor, and it stops the pipeline
dead. Default to the source document's filename stem, marked as a default rather
than a reading. A user renaming it is doing the intended thing; a user never
seeing the package because a name was missing is not.

*Fails if:* import still refuses a package whose only defect is an unnamed
project.

### R3 — the declared profile is DERIVED from what is present, not asserted

This is the requirement that does the most work.

All five gpt-5 packages declared `Complete` because the extractor writes
`Complete` — not because they contained the complete field set. The declaration
is an aspiration and the shape then measures it as a claim.

`uofa import` must compute the highest profile the content actually satisfies —
Disposition, then Complete, then Minimal — and declare that. A package with
Minimal's fields declares `ProfileMinimal` and **passes**, honestly, at the level
it earned.

*Fails if:* any package declares a profile whose required fields it does not
carry.

**This alone takes keyless from 0 of 5 to a passing Minimal package**, given R1
and R2, because keyless supplies Minimal's extractor-facing fields and the rest
are run-context.

### R4 — a blank field must never be filled to satisfy a count

R1–R3 supply things the tool genuinely knows. Nothing here authorises filling a
document-derived field with a plausible value. `hasCredibilityFactor` levels stay
blank in the keyless path — the best keyless route reaches **0.100 end to end**,
and a wrong level that validates is worse than a blank one that does not.

*Fails if:* any change here raises a validation rate by emitting a value no route
was measured to produce.

### R5 — the run reports which class each field came from

Every emitted field carries `method`: `extracted`, `run-context`, `defaulted`, or
`author-supplied`. `uofa import --check` prints the counts.

A package that validates on 6 run-context fields and 2 extracted ones is a
different artefact from one that validates on 8 extracted fields, and **today
those are indistinguishable.** This is the requirement that keeps R1–R3 from
becoming a way to make numbers look better.

*Fails if:* a validating package cannot be asked how much of it was read.

### R6 — validity is measured on both paths, every time

`dev/tools/scripts/keyless_vs_model.py` gains a validity column: of N documents,
how many produce a package passing C2, and on how many extracted fields.

*Fails if:* the head-to-head reports extraction quality without validity. They
were measured separately once, and the result was a model that scored ahead on
every gold dimension while producing a valid package **less than half the time**.

---

## Acceptance

| | now | target |
|---|---|---|
| gpt-5 packages passing C2 | 2/5 | **5/5** |
| keyless packages passing C2 | 0/5 | **5/5, at ProfileMinimal** |
| packages validating on an invented assessor | 2/5 | **0** |
| keyless factor levels emitted | 0/65 | **0/65 — unchanged** |

The last row is the one that makes the others meaningful. Any implementation
that reaches 5/5 by loosening R4 has defeated the purpose.

## Risks

- **R3 makes validation easier to pass, and that is the point** — but it must not
  become a way to claim less and look better. Mitigated by R5: the profile and
  the per-class counts are printed together, so a package that dropped to Minimal
  is visibly a package that dropped to Minimal.
- **R1 puts an identity in every package.** The operator's name is now in an
  artefact that may be shared. It must be overridable and it must be visible in
  the output, not silently stamped.
- **A valid package is still not a correct one.** These requirements fix a
  category error in *where fields come from*. They do not improve extraction. The
  0.988 groundedness figure measures whether numbers in a rationale appear in the
  source, not whether a level is right — and this project once reported
  `mean F1 0.964 — PASS` while 37 of 45 packages failed the shape. Validity and
  correctness must keep being reported as two numbers.

## Out of scope

Improving what either extractor reads. The keyless factor-level route stays at
0.100 and stays unemitted; `bindsRequirement` stays author-supplied. This spec
makes the pipeline produce a truthful package from what the extractors already
manage — nothing here is an argument that they manage enough.

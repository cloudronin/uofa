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

### R0 — core carries no standard's vocabulary

Remove `hasContextOfUse` from core's `MinimalBody` and `CompleteBody`.
`DispositionBody` follows by `sh:node` inheritance. Core then requires only what
every standard shares:

    bindsRequirement, hasValidationResult, hasDecisionRecord,
    generatedAtTime, hash, signature

Move the requirement to `packs/vv40/shapes/vv40_shapes.ttl`, where a V&V 40
package is required to declare a context of use exactly as it is today.

This is a **core schema version bump: 0.7 → 0.8** (`spec/context/v0.8.jsonld`,
`packs/core/pack.json`), because it changes what core demands rather than adding
to it.

**Open question, and it must be settled before implementing.** The vv40 shape has
to apply to V&V 40 packages *only*. Validation loads several packs at once — the
regression harness loads all 7 shape files together — so a shape targeting
`uofa:UnitOfAssurance` unconditionally would impose the COU requirement on 7009A
packages again, reproducing the bug in a new location. The discriminator a V&V 40
package carries has not yet been identified, and **guessing at it is how this
change goes wrong quietly**: the packages would still validate, and the
requirement would silently apply to the wrong set.

### The regression instrument

`dev/tools/scripts/profile_baseline.py` validates every package in the repo and
diffs two runs. Baseline before any change: **64 packages, 55 conforming, 9 not.**

A schema edit claiming to be additive, or to only move a constraint, is a claim
about 64 packages, and the only way to hold it is to validate all of them twice.
The script exits non-zero on any package that stops conforming, and it also
reports packages that *start* conforming — because silently making validation
easier is how a shape stops meaning anything.

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
and nobody answers a prompt in a batch run. `keyless_vs_model.py` must therefore
declare exactly what it supplies — `--assessor "batch-harness"`, project name
from the filename, `bindsRequirement` left absent — and print R5's per-class
counts in its output. Without that the head-to-head measures the harness defaults
rather than the extractors.

*Fails if:* the null control is absent from the comparison, or the harness's
contributions are not separable from the extractors'.

---

## Acceptance

Per profile and per standard, because a single figure hides Finding 1.

**Before R0** — the two 7009A papers are expected non-conformant:

| | now | target |
|---|---|---|
| gpt-5, V&V 40 (3 papers) | 0/3 | **3/3 at Complete or below** |
| keyless, V&V 40 (3 papers) | 0/3 | **3/3 at Minimal** |
| gpt-5, 7009A (2 papers) | 2/2 | **0/2, failing loudly** — the current passes rest on invented COU strings |
| keyless, 7009A (2 papers) | 0/2 | **0/2, failing loudly** |

**After R0:**

| | target |
|---|---|
| gpt-5, 7009A | **2/2 at Minimal or above** |
| keyless, 7009A | **2/2 at Minimal** |

**Invariant across both:**

| | now | target |
|---|---|---|
| packages validating on an invented assessor | 2/5 | **0** |
| keyless factor levels emitted | 0/65 | **0/65 — unchanged** |
| null control | unmeasured | **0/5, printed** |

The last three rows are what make the others mean anything. Any implementation
reaching its targets by loosening R4 has defeated the purpose.

---

## Risks

- **R3 makes validation easier to pass.** Mitigated by R5: profile and per-class
  counts print together, so a package that dropped to Minimal is visibly one that
  dropped to Minimal.
- **R1 puts the operator's name in every package**, which may be shared. It must
  be overridable and visible in the output, never silently stamped.
- **R0 changes a shipped shape.** A new `sh:or` branch cannot invalidate an
  existing package — `sh:or` only ever adds ways to pass — but the profile
  *reported* for a package may change, and every fixture asserting a profile
  string needs re-running.
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

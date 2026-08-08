# Making both extractors produce a valid package

**Status:** specification, not yet implemented. Revised 2026-08-08 after review;
the first draft's acceptance criteria were unreachable and its headline was
wrong. Every number here was measured against the five real papers.

---

## Finding 1 — the profiles make NASA-STD-7009A unvalidatable

**Every profile requires `uofa:hasContextOfUse`:**

| profile | required properties | requires `hasContextOfUse` |
|---|---|---|
| `MinimalBody` | 7 | **yes** |
| `CompleteBody` | 13 | **yes** |
| `DispositionBody` | 14 | **yes** |

And **NASA-STD-7009A defines no context of use.** That is this project's own
measured finding, not an assumption: K7 correctly returns *nothing* on 9 of 10
and 4 of 4 seeded 7009A documents, and the real papers carry 0 mentions
(opensim) and 1 (elemance) against 39/33/50 for the three V&V 40 papers.

So **no 7009A document can produce a valid package at any profile**, and the only
way to make one is to invent the field. Two of the five real papers are 7009A.

**This is not an extractor defect and not a packaging defect.** The profile
definitions encode ASME V&V 40's conceptual model as universal, and the shape
then measures 7009A documents against a concept their standard does not contain.
Every downstream number — extraction accuracy, validity rate, the head-to-head —
is affected, and no amount of work on the extractors touches it.

It is also the reason the first draft of this spec was wrong. It set "keyless 5/5
at ProfileMinimal" as acceptance, which is reachable **only by fabricating
`hasContextOfUse` on the two 7009A papers** — forbidden by this spec's own R4.
Two requirements of mine contradicting each other, for the third time in this
project.

### R0 — a profile a 7009A document can satisfy

Add `UnitOfAssurance_NasaMinimalBody`: Minimal's seven, minus `hasContextOfUse`,
plus `bindsModel` (which 7009A does require and every real 7009A document
states). Register it as a fourth branch of the `sh:or`, and add its URI to the
`conformsToProfile` `sh:in` list — which `PROFILE_URIS` already derives from,
so nothing drifts.

*Fails if:* a 7009A document can only validate by carrying a context of use.

**R0 is a prerequisite for everything below.** Until it lands, 7009A papers are
**expected non-conformant** and must be reported that way rather than counted as
extractor failures.

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
that. **Order: Disposition, Complete, NasaMinimal, Minimal.**

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
| gpt-5, 7009A | **2/2 at NasaMinimal or above** |
| keyless, 7009A | **2/2 at NasaMinimal** |

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

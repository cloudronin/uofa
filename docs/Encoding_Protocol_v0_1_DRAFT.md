# Encoding Protocol v0.1 (DRAFT)

**AWAITING-AUTHOR.** A machine-produced draft. It governs nothing until the author has
corrected it and committed the result as `Encoding_Protocol_v0_1.md`. Each `[AUTHOR-CONFIRM]`
marker names a point the draft is not confident reproduces the author's practice.

This document tells you how to turn one published source document into a signed-ready UofA
package that is evidence rather than opinion. **Part A** is the procedure, executable top to
bottom. **Part B** is how to disposition the weakener firings Part A's last step produces.
**Part C** is why, and you can skip it.

A **reference encoding** is a UofA package built by hand from a named published source, under
this procedure. A hand encoding produced by judgment alone is an opinion about the source, and
a second encoder following that judgment cannot tell whether they reproduced it or merely
agreed with it. The procedure is what turns the second encoder's agreement into a check.

You need the source document, the `uofa` CLI, and an extraction model. Background on UofA
packages, contexts of use, credibility factors and weakeners is at `uofa.net/concepts`.

---

# Part A — The procedure

Work in a single directory. It ends holding a scoping note, a workbook, an unsigned package,
a run log, an ambiguity log, a review ledger, and a dispositions table.

### A-1. Scope the source and write the scoping note

Write `SOURCE_SCOPING.md` before you read the document closely enough to encode from it. State
the context of use, the model or system being assessed, and an inventory of every part of the
source that carries evidentiary weight, each with a page, section, table, or figure reference.

Then draw the **evidence boundary**: list what you admit and what you exclude. A single source
can interleave evidence about the model with tutorial about the standard being applied to it,
in one voice and paragraph by paragraph, and a rule admitting "the published document" admits
both. Admissible material is the published document and the supplementary material published
with it; secondary summaries and recollection are not. Synthetic evidence bundles are
admissible, and the package states its source class.

Create `AMBIGUITY_LOG.md` now, empty. A-9 states what goes in it, and entries begin arriving
during this step.

**Check:** the note lists admitted and excluded material separately, and `AMBIGUITY_LOG.md`
exists. Nothing you encode later may cite an **excluded passage**. A page may be partly
admitted: bibliographic front matter such as a title, a byline or a reference list is
admissible even on a page whose argument you excluded, so the boundary is drawn over passages
and the anchor names the passage.

### A-2. Choose the minting namespace

Set `base_uri` to a namespace you control, and record it. The identifier it produces is covered
by the signature and cannot be corrected after signing.

**Check:** at A-11, `--protocol-check` reports the minted namespace is not a reserved example
domain. The whole RFC 2606 and RFC 6761 reserved family is refused — `example.com`,
`example.net`, `example.org`, `example.*` generally, and anything under `.test`, `.invalid` or
`.localhost` — not only the placeholder the importer defaults to. A reserved domain is one
nobody controls, so it fails this step's rule however plausible the subdomain in front of it.

### A-3. Open the run log

Write `RUN_LOG.md` recording the extraction model string, the backend, the prompt hash, the
documentation-site commit current on the day you run, your repository or tool version, and the
`base_uri` from A-2.

Name your extractor by exact model string and version, and state what it is **not** the same
as. Lineage is declared per encoding and never inherited from a document that describes a
different run.

**Check:** `--protocol-check` verifies the log carries model, backend, site commit, version,
and `base_uri`.

### A-4. Extract

```
uofa extract <source-dir> --pack <pack> -o <workbook>.xlsx
```

Keep the extractor's untouched output. Copy the workbook to `raw-extract/` before you edit a
cell, so the difference between what the extractor produced and what you reviewed stays
measurable.

Extraction is a starting point and it may return very little, including no credibility factors
at all. That is not a failure state and it does not change what follows: build the workbook
from the source under A-6, where every cell needs a source location anyway. Record what the
extractor returned in the run log, because a thin extraction and a thorough one produce
packages that look alike and are not.

**Check:** a copy of the extractor's output exists and is not the file you are about to edit.

### A-5. Give the workbook a home for citations

Every sheet needs a trailing `Source Anchor` column. Add it if the template lacks one, at the
right of the existing headers.

**Check:** `--protocol-check` reports the anchor column present on every data sheet.

### A-6. Review every cell against the source

For each populated cell, do one of four things and record which in `REVIEW_LEDGER.md`:
**confirm** it against the source, **correct** it against the source, **mark it source-absent**
and empty it, or **add** a row the source plainly supports.

Review against the source location that should carry the value, never against the extractor's
output or its rationale. A value the extractor synthesized arrives with a plausible rationale
attached, and a confidence score does not separate it from one that was read.

Anchor every populated row. The anchor cites a page, section, table, or figure, at row level in
the workbook and at cell level in the ledger wherever a row's cells come from different places.

**Check:** `--protocol-check` reports every populated row anchored, and no template placeholder
text left in a data row.

### A-7. Confirm required and achieved levels separately

These are two different claims and they live in two different places in a source document.
Confirm each against its own location. **Required equal to achieved on every factor is treated
as unreviewed** until you have found where the source states its requirement, because
extraction tooling commonly defaults one to the other.

**Check:** `--protocol-check` fails when required equals achieved on every factor and no waiver
is recorded.

### A-8. Anchor non-textual values by their recovery method

Where a value is recoverable only by non-textual means, such as cell shading in a table or a
position in a figure, the anchor names the recovery method as well as the location. Record the
value as your own work rather than extractor output, and ship the method with the encoding so
someone else can repeat it.

**Check:** the anchor names a method, and the method is reproducible from the files you commit.

### A-9. Keep the ambiguity log as you go

The log was created in A-1 and you have been adding to it since. Add an entry whenever the
source **underdetermines** a field, whenever a **cross-standard mapping is not mechanical**, or
whenever the source **over-determines** a field by answering the same question two ways.

An entry states the ambiguity, the resolution you chose, and the rule you applied choosing it.

Where the source contradicts itself, record the reading you chose and enter the contradiction
with an anchor for each reading. Never harmonize silently. Where one reading is an answer and
the other a declination to answer, the answer outranks the declination and the declination is
kept as context.

Where the source discloses its own distortion, such as an example the authors describe as
disguised, encode what the source states and say that you did.

Mark an entry **ESCALATION** where you meet a gap the schema cannot express and that you must
not work around. An escalation is not a resolution. It is amended rather than replaced if one
arrives later, so the record shows the gap was met before it was closed.

**Check:** `--protocol-check` reports the log present and non-empty.

### A-10. Decline rather than invent

Where the source's scale or vocabulary cannot map mechanically onto the pack's, **do not
populate**. Disclose the declination and its consequence in the encoding, and record the
mapping gap as an ESCALATION entry.

Declining has a visible cost: derived metrics computed from levels will read zero for factors
you declined, against a source that asserts otherwise. State that in the encoding. Understating
a source is a smaller failure than overstating it and it is not a free one.

Declining is the default, and it has a limit. Where declining would suppress a value the source
explicitly foregrounds — a headline result, a stated exceedance, a figure the source exists to
demonstrate — you may not decline silently. Either carry the value as a recorded judgment act,
named as your judgment rather than as the source's arithmetic, or decline. In **both** cases
write an ambiguity-log entry setting the two readings side by side, each with its own anchor, so
a reader can see what the reading you did not take would have produced.

**Check:** the declination and its consequence appear in a committed file, not in a covering
note. Where the declination touches a value the source foregrounds, the ambiguity log carries
both readings, each anchored.

### A-11. Import without signing

```
uofa import <workbook>.xlsx --pack <pack> --base-uri <your-namespace> --protocol-check
```

Do not pass a signing flag. Read the resulting profile from the package rather than from the
console.

Record the provenance counts the import reports, and treat a surprise in them as something to
investigate rather than as a result. The counts classify summary-level fields only and cannot
see a cell-by-cell review, so the auditable record of what you contributed is the anchored
workbook and the review ledger, not the counts.

**Check:** `--protocol-check` exits zero. The package's signature field is still a placeholder.

### A-12. Run the rules and draft the dispositions

```
uofa rules <package>.jsonld
```

Write `DISPOSITIONS_DRAFT.md` using Part B. The table covers **every factor the pack expects**,
not only the factors the engine raised a firing against. A factor with no firing and no level
gets an explicit disposition, ordinarily source-absent or declined-mapping.

**Check:** the table has a row per expected factor. A table containing only engine-raised rows
is incomplete.

### A-13. Completion

The encoding is complete when import passes with every mandatory field either populated or
explicitly marked source-absent, the declared profile is earned rather than asserted, the
anchor column and ambiguity log are populated, and the dispositions table covers every expected
factor.

Completion does not certify that the package represents its source well. Import success and
schema conformance are both satisfiable by a package that understates its source. Derived
metrics are not completeness evidence.

Record the protocol version that governed the encoding. Record the pack version and the
standard version as separate facts; they are not the same statement. Record any departure from
this procedure in the ambiguity log with its rationale.

**A machine-drafted review is preparation, not review.** If a tool or an assistant prepared the
candidate values, the review in A-6 has not happened until a named person performs it. The run
log must never leave ambiguous which of the two occurred or who did it.

---

# Part B — Disposition rules

A **weakener firing** is the rule engine reporting that a package exhibits a catalogued
pattern of weakness. A **disposition** is your verdict on one firing, with the source anchor
and the rule you applied. **Dispositions adjudicate the package, not the source**: a firing is
a statement about the artifact a reviewer receives, so a firing that is true of the package and
false of the source is still Accepted, and the difference between them goes in the ambiguity
log. The three verdicts are **Accepted**, meaning the package exhibits the gap the pattern
describes; **Not Accepted**, meaning the pattern fired but the package does not exhibit it;
and **Not Applicable**, meaning the pattern's precondition is not meaningful for a package of
this class.

Two classes of rule appear below. A **mechanical** rule is one whose verdict a script could
check from the package's own content. A **judgment** rule is one whose verdict requires a human
decision about whether the claim holds, and is recorded as author judgment under this protocol.
Class is a property of the pattern and is not the encoder's to reassign.

Adjudicating against the package makes every mechanical firing on a correctly encoded artifact
Accepted, so the verdict carries most of its information on the other two values.
[AUTHOR-CONFIRM: this follows from the package-basis rule rather than being separately stated,
and it changes what the dispositions table is for.]

| Family | Patterns | Class | Verdict rule | Not Applicable when |
|---|---|---|---|---|
| Provenance and epistemic | `W-PROV-01`, `W-EP-01`…`W-EP-03` | mechanical | Accepted when the package does not carry the derivation edge. Not Accepted only where the edge is present and the rule failed to traverse it. [AUTHOR-CONFIRM] | the package class has no derivation chain to carry |
| Epistemic, risk-conditioned | `W-EP-04` | judgment | Author judgment on whether an unassessed factor at elevated model risk undermines the claim, which depends on what the context of use needs from that factor. [AUTHOR-CONFIRM] | — |
| Alignment | `W-AL-01`, `W-AL-02` | mechanical | Accepted when the node is absent from the package. The source's possession of the underlying work is an ambiguity-log entry and never a reason to disposition otherwise. [AUTHOR-CONFIRM] | the package class carries no such analysis by definition |
| Ontology | `W-ON-01`, `W-ON-02` | mechanical | Accepted when the context of use carries neither an applicability constraint nor an operating envelope. [AUTHOR-CONFIRM] | — |
| Argumentation, structural | `W-AR-04`, `W-AR-05` | mechanical | Accepted when the link is absent, including where the comparator is real but is not the kind of thing an identifier names. [AUTHOR-CONFIRM] | the node class has no comparator by nature, such as a review activity or a process attestation |
| Argumentation, reasoning | `W-AR-01`, `W-AR-02` | judgment | Author judgment. A required level without acceptance criteria, and an acceptance standing above a shortfall, are both claims about whether the reasoning holds, and no test of package content settles either. [AUTHOR-CONFIRM] | — |
| Argumentation, unresolved | `W-AR-03` | unresolved | Record the firing and its class as unresolved. Do not assign it to either class. | — |
| Consistency, structural | `W-CON-02`…`W-CON-05` | mechanical | Accepted when the package does not carry the referenced element. [AUTHOR-CONFIRM] | — |
| Consistency, factor-decision | `W-CON-01` | judgment | Author judgment. A factor carrying evidence and no level under an accepted decision is what A-10 produces on purpose, so this pattern is the one most sensitive to a declination. [AUTHOR-CONFIRM] | — |
| Structural integrity | `W-SI-01`, `W-SI-02` | mechanical | Accepted when the element is absent. Note that `W-SI-01` does **not** fire on an unsigned package, because import writes a placeholder signature and the pattern tests absence rather than validity, so its silence never means the package is signed. [AUTHOR-CONFIRM] | — |
| Compound patterns | `COMPOUND-*` | excluded | Not dispositioned individually. They report coexistence of firings already dispositioned above. | — |
| Pack-specific patterns | any `W-<PACK>-nn` | as the core family it resembles | A pack ships patterns of its own, and each takes the rule of the core family it resembles rather than a rule per pack. A pattern testing for a factor asserted without its linked evidence is a consistency pattern. [AUTHOR-CONFIRM] | as the family it resembles |

[AUTHOR-CONFIRM: the Not Applicable conditions above are derived from the pattern bodies. The
distinction between Not Applicable and Not Accepted needs a worked case from a package whose
decision outcome was Not Accepted, and no such record is committed.]

[AUTHOR-CONFIRM: one full worked disposition, from source citation to verdict, belongs here.
The strongest candidate is a validation activity waived by a documented authority decision,
which reads correctly whether adjudicated against source or package. It cannot be cited until
a governed review pass has dispositioned it.]

The **verdict** and the **action class** are different vocabularies and neither derives from
the other. The verdict states the credibility judgment. The action class states the remediation
posture, drawn from a controlled set running from restricting the context of use through
accepting residual risk. An action class is never inferred from a verdict.

---

# Part C — Rationale notes

Skippable. Each note is numbered to the step or row it explains and cites
`dev/build/pilot-johnson/PROTOCOL_FINDINGS.md` by finding number rather than restating it.

**A-1, the evidence boundary.** The rule exists because the Johnson pilot's source was half
evidence about a model and half tutorial about NASA-STD-7009, written in one voice, so an
intake rule naming "the published paper" admitted both (F-2a). Drawing the boundary afterward
is a different act, because by then the encoder has read the tutorial and cannot unread it.

**A-2, the namespace.** The on-ramp page never mentions `base_uri`, import warns about the
placeholder domain, and the identifier cannot be corrected after signing (F-1b). The on-ramp
page needs the same sentence, which is a tooling item rather than a protocol one. The check was
widened from the importer's one placeholder string to the whole reserved family after an encoder
following this step chose a reserved example domain under a plausible subdomain: the narrow
check passed, and the rule — a namespace you control — was missed in substance.

**A-3, the pin and the lineage.** No example site commit appears in Part A because the outline's
own example had drifted before the first encoding under it began, and a pin that goes stale
inside a governing document is worse than no pin (F-1a). The lineage rule exists because the
pilot's governing spec asserted its extractor was the model an evaluation had used, when that
evaluation ran on a local four-billion-parameter model and the frontier arm belonged to a
different study (F-1c).

**A-6, reviewing against the source location.** The pilot's extractor returned 141 of 142 cells
as review-suggested rather than high-confidence, which is honest reporting and exactly why it
does not help: a synthesized value and a read value carry the same signal (F-3a).

**A-6, the fourth verb.** Confirm, correct and mark-source-absent all act on a cell that already
exists. The pilot met a firing clearable only by adding a row the source plainly supported, and
declined, which was right for a run made before this document existed (F-3c).

**A-7, the level rule.** An extraction prompt in common use sets required equal to achieved
unless the narrative names a gap. The pilot's source wrote its required levels as table shading
rather than prose, so the default fired on all seventeen factors carrying levels and produced a
column that was complete, plausible, schema-valid, and from nowhere. It erased both of the
exceedances the source exists to demonstrate (F-3b).

**A-8, non-textual recovery.** The pilot's predeclared credibility levels existed only as green
cell fill in one table, with no text for any extractor to read. They were recovered from the
page's fill geometry and corroborated against three statements the recovery had not used
(F-2d). Crediting that work to the extractor would overstate it where the provenance argument
depends on it.

**A-9, the contradiction rule.** The pilot's source answered the same question two ways three
times, most sharply where one response both described an approved waiver and denied any waiver
was required (F-4b). The answer-outranks-declination rule settles one of the three; the other
two remain author judgment, which is the honest limit of the rule.

**A-10, declining.** The pilot declined to rewrite a nought-to-four credibility level onto a
one-to-five factor, and every derived metric in the resulting package read zero against a
source asserting otherwise (F-5a, F-6a). Two standing examples of the escalation class: a
factor the source predeclares and achieves that the pack has no field for, and a level-zero
convention inexpressible on thirteen of nineteen factors.

**A-11, the provenance counts.** They classify eleven summary-level fields and no credibility
factor, validation result, or decision record, so a package reviewed cell by cell and one
imported straight from the extractor report identical counts (F-7a). One class is missing
rather than coarse: author-side recovery of the kind A-8 requires is human work no existing
class describes (F-7b), which is why the review ledger is mandatory (F-7c).

**A-11, reading the profile from the package.** Import currently prints the declared profile
while writing the derived one (F-3e). Template hint text also survives into data rows wherever
the model wrote nothing, which is why A-6's check names it (F-3d).

**A-12, the silence rule.** Eleven of the pilot's factors carried no level and a non-assessed
status and drew no weakener at all, because the relevant pattern excludes those statuses by
design. The encoding's largest gap was the one the engine said least about (F-4e).

**A-13, pack version against standard version.** The pilot's package was pack `nasa-7009b`
0.5.0 encoding an assessment written against NASA-STD-7009A. The version-agnostic alias for
that standard resolves to the B identifier, so an assessment entered the natural way is
silently graded against a standard it does not claim (F-8b).

**B, the package basis.** Nine of the pilot's twelve firings were true of the package and false
of the source behind it (F-4a). Dispositioning them against the source would suppress warnings
that are correct about the artifact under review. Adjudicating against the package also keeps
disposition semantics identical whether the source is real or synthetic.

**B, the class definitions.** The mechanical-versus-judgment split reproduces a partition ruled
elsewhere in this project, restated here in terms a reader of this document alone can apply.
The per-family rules are derived from the pattern bodies in the core rules file together with
the twelve dispositioned rows of the Johnson pilot, which is the only per-firing disposition
record committed anywhere. The outline this draft was written from specifies a different
source that is not committed, which is why every family row carries a marker.

**B, argumentation Not Applicable.** A review activity and a process attestation have no
comparator by nature, yet both ride the same predicate as validation results, so the
comparator-absence pattern reports an absence that could never be a presence. Established by
adding a process attestation and watching it draw the firing immediately.

**B, structural integrity.** An unsigned package carries a zero-filled placeholder rather than
no signature, so the missing-signature pattern never fires on one. Integrity checking catches
it and the weakener report does not (F-6d).

**The principle behind A-10, A-12 and A-13.** The system may decline to decide, but it may never
decline invisibly. A-12's silence rule, A-13's refusal to let import success stand as
completeness evidence, and A-10's declination disclosure are three faces of one design
principle; the A-10 case is what forced it into words, when a conservative encoder following the
rule as first written could drop the value a source exists to demonstrate and leave nothing in
the record to say it had.

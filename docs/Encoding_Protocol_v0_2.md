# Encoding Protocol v0.2

**Version 0.2 · 2026-08-29.** Adopted in a single event on the C-series report, under the
adoption condition stated in `docs/Protocol_v0_2_Amendments_Draft.md`. v0.1 governed until that
event; this document supersedes it and v0.1 stays readable for packages encoded under it.

**What changed, in one line each.** Batch A landed as drafted (operator identity declared not
inherited; the D-06 worked disposition; the COU1/COU2 Not-Applicable-versus-Overruled pair;
sign-off verified against the published wheel at whatever version is then current). Batch B's
four stranger-series amendments landed validated against the C-series. **Part D records each
item with its validation status and the evidence that carried it**, and the Validation Record
appendix carries the measured completion rate.

**Version 0.1 · 2026-08-20.** Finalized under the work order dated 2026-08-21, which took the
remaining protocol rulings and authorized this commit.

An encoding records the protocol version that governed it. Cite this document by version, not by
path: a package encoded under v0.1 states v0.1, and stays readable when v0.2 changes a rule.

Part B's verdict rules are calibrated against 71 recorded author adjudications of packages against
the weakener catalog; each row's
**Calibration** column says what it was derived from and which rules are not yet calibrated.
Part C records why each rule exists and cites `dev/build/pilot-johnson/PROTOCOL_FINDINGS.md` by
finding number.

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
Confirm each against its own location.

**Two questions, two acts.** They were one token until run 25, and the conflation cost a
release:

- **Was the required level LOCATED?** Anchoring answers it. Its residue is the anchor.
- **Was the required level JUDGED?** Only a sufficiency judgment answers it — weighing the
  required level against the achieved one. Its residue is an *affirmation*: the provenance
  token `affirmed` or `corrected`, and an activity naming who judged and when.

Anchoring a required cell routes `set-anchor → confirm`, so a reviewer who located every level
and weighed none produced a workbook reading `confirmed` throughout. Anchoring's residue was
being offered as evidence of judgment, and a check built to read it passed a package nobody had
judged.

**Why this needed an act at all.** Agreement writes nothing. A reviewer who reads seventeen
required levels and agrees with every one produces a file byte-identical to one nobody opened.
The old rule inferred from shape — *required equals achieved everywhere, so nobody looked* —
which refuses the diligent reviewer and misses nothing else. Run 25 is the case that made it
worth fixing rather than tolerating: the defaults really were untouched, so the refusal was
correct, and the identical reading would have refused a reviewer who had done the work.

**A judgment claim carries its agent.** A token saying someone weighed this level, with nothing
saying who or when, is an assertion nobody stands behind — and it satisfies any check that
merely asks whether an activity exists. So `affirmed`, `corrected` and `waived` each require an
attributed affirmation, in the workbook (`Affirmed By`, `Affirmed At`) and in the package
(`hasLevelAffirmation`) alike. The requirement does not vary by carrier.

**Check:** `--protocol-check` asks a package that can answer whether each required level was
judged, and refuses it when any carries no judgment and no waiver is recorded. A package whose
declared context predates the vocabulary cannot answer, and is advised rather than refused.
Equal values are no longer evidence either way.

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

**Declare the operator identity; do not inherit it.** *(v0.2, A1)*

```
UOFA_ASSESSOR="<operator>" uofa import <workbook>.xlsx --pack <pack> \
  --base-uri <your-namespace> --protocol-check
```

Left unset, the importer falls back to `git config user.name` and then to `$USER`, and writes
whichever it finds into `wasAttributedTo`. Those are properties of the shell the import happened
to run in, not decisions about the encoding, and the field is covered by the signature like any
other. An encoding run in a container inherits the container's identity; the same workbook
imported on a laptop inherits the laptop's. **Neither is a claim anyone made.**

`wasAttributedTo` is **who ran the tool** and is not the assessor. Where the source names who
performed the assessment, that is read into `statedAssessor` and the two stay distinguishable. A
machine-run import declaring a machine operator is correct and is not a defect to hide: it is the
same distinction A-13 draws between machine-drafted preparation and a named person's work.

**Check:** `--protocol-check` exits zero, and fails when the operator identity was not explicitly
declared. The package's signature field is still a placeholder.

### A-12. Run the rules and draft the dispositions

```
uofa rules <package>.jsonld
```

Write `DISPOSITIONS_DRAFT.md` using Part B. The table covers **every factor the pack expects**,
not only the factors the engine raised a firing against. A factor with no firing and no level
gets an explicit disposition, ordinarily source-absent or declined-mapping.

**The verdict is authored after the judgments it rests on.** *(v0.2, P2-2)* A decision recorded
while the levels it depends on stand unaffirmed is a verdict in search of its grounds. Judgment
comes first in time, not merely first in the document.

**Check:** the table has a row per expected factor. A table containing only engine-raised rows
is incomplete. Every judgment act predates the decision act in the review ledger.

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

**Gates clearing establishes readiness, not completion.** *(v0.2, P2-4)* No checker state
substitutes for the accountable party's signature, and no interface may present one as the
other. A checker reporting that nothing is owed has said something about the package's readiness
and nothing about whether anyone has attested to it. **Attestation is a separate act.**

**An encoding is complete when no gates are owed AND the decision has been signed.** *(v0.2,
P2-1)* Taking away an unsigned export is a legitimate act, and the package says honestly what it
owes; it is not completion. An engagement letter given to any reviewer should name the signed
deliverable, because a reviewer scored against a criterion its instructions never named has been
measured on someone else's expectation.

**Sign-off verifies against the published wheel, at whatever version is then current.** *(v0.2,
A4)* In a clean environment, with the package outside the repository. **The version gap is the
test.** The rule cannot be *"verify under the pinned version"* — that is the version the encoder
already has, and the gap between the signing tool and the current published tool is the only part
of the check an outside verifier cannot fake for you.

```
python3 -m venv venv && ./venv/bin/pip install "uofa==<current published>"
./venv/bin/uofa verify <package>.jsonld --pack <pack> \
  --pubkey keys/<issuer>.pub --decision-pubkey keys/<reviewer>.pub
```

Verify **from the anchors the package itself ships**, not from keys named on the verifier's own
machine: a signature checked against a key the reader already trusted proves nothing the packaged
anchor exists to answer.

---

# Part B — Disposition rules

A **weakener firing** is the rule engine reporting that a package exhibits a catalogd
pattern of weakness. A **disposition** is your verdict on one firing, with the source anchor
and the rule you applied. **Dispositions adjudicate the package, not the source**: a firing is
a statement about the artifact a reviewer receives, so a firing that is true of the package and
false of the source is still Confirmed, and the difference between them goes in the ambiguity
log. The three verdicts are **Confirmed**, meaning the package exhibits the gap the pattern
describes; **Overruled**, meaning the engine's finding does not hold against the package as it
actually stands, typically because the package carries the element the firing reports missing;
and **Not Applicable**, meaning the pattern's precondition is not meaningful for a package of
this class. There are three, and the table below adds no fourth.

**"Confirmed" here is a verdict on a firing.** A-6's confirm, correct and mark-source-absent are
per-cell review actions on a workbook. The two vocabularies are unrelated and never interact.

Two classes of rule appear below. A **mechanical** rule is one whose verdict a script could
check from the package's own content. A **judgment** rule is one whose verdict requires a human
decision about whether the claim holds, and is recorded as author judgment under this protocol.
Class is a property of the pattern and is not the encoder's to reassign.

Adjudicating against the package makes most mechanical firings on an honest package Confirmed,
so the verdict column's information concentrates in Overruled and Not Applicable. That is
intended design rather than a weakness in the vocabulary: the substantive content of a Confirmed
row is its ambiguity-log context, and the table records what was examined as much as what was
decided.

The **Calibration** column states what each rule was derived from. *Firing rulings* are cases
where the pattern fired and the disposition was recorded on that firing. *Silence rulings* are
cases where the pattern stayed silent; they calibrate by contrapositive, establishing the package
condition under which a firing would be right or wrong rather than dispositioning a firing
directly. Both are legitimate calibration and the distinction is recorded because it is the same
distinction A-12's silence rule draws. *Uncalibrated* means the rule comes from the pattern body
alone, is not yet checked against an author disposition record, and is revisited in v0.2 after
the governed review passes.

| Family | Patterns | Class | Verdict rule | Not Applicable when | Calibration |
|---|---|---|---|---|---|
| Provenance chain | `W-PROV-01` | mechanical | Confirmed when the package carries no upstream derivation, generation or use edge for the node and does not mark it foundational. **Overruled where that edge is present and the rule did not traverse it**: the pattern's scope starts at bound claims, so a node outside every claim's derivation subtree is out of its reach. | the package class has no derivation chain to carry | 2 silence rulings |
| Epistemic | `W-EP-01`…`W-EP-03` | mechanical | Confirmed when the package does not carry the link the pattern names. Overruled where the link is present and the firing reports it missing. | the package class has no such link to carry | 3 firing + 1 silence ruling |
| Epistemic, risk-conditioned | `W-EP-04` | judgment | Author judgment on whether an unassessed factor at elevated model risk undermines the claim, which depends on what the context of use needs from that factor. | — | uncalibrated |
| Alignment | `W-AL-01`, `W-AL-02` | mechanical | Confirmed when the node is absent from the package. The source's possession of the underlying work is an ambiguity-log entry and never a reason to disposition otherwise. | the package class carries no such analysis by definition | 1 firing + 1 silence ruling |
| Ontology, bounds | `W-ON-02` | mechanical | Confirmed when the context of use carries neither an applicability constraint nor an operating envelope. Either one present, even as an empty stub, and the pattern is correctly silent; the hollowness is an ambiguity-log entry, not a disposition. | — | 4 firing rulings |
| Ontology, mandatory | `W-ON-01` | mechanical | Not Applicable on any package that validates: the context of use is a mandatory field, so the flaw cannot exist in a schema-valid package. A firing means the package failed structural validation and is not yet an artifact to disposition. | always, on a package that validates | 2 silence rulings |
| Argumentation, structural | `W-AR-04`, `W-AR-05` | mechanical | Confirmed when the link is absent, including where the comparator is real but is not the kind of thing an identifier names. Overruled where both fields are present and the firing misreads them. | the node class has no comparator by nature, such as a review activity or a process attestation | `W-AR-04` 4 silence rulings; `W-AR-05` uncalibrated |
| Argumentation, method | `W-AR-03` | mechanical | Confirmed when the requirement names a verification method and the supporting activity records a different activity type. | neither field is populated, which is a property of the generator rather than of the package | 1 firing ruling |
| Argumentation, reasoning | `W-AR-01`, `W-AR-02` | judgment | Author judgment on whether the reasoning holds; no test of package content settles either. Confirmed when the firing stands on a package genuinely carrying a required level without acceptance criteria, or an acceptance standing above a recorded shortfall. | — | `W-AR-02` 2 firing rulings; `W-AR-01` 6 silence rulings |
| Consistency, structural | `W-CON-02`, `W-CON-04`, `W-CON-05` | mechanical | Confirmed when the package does not carry the referenced element. | — | `W-CON-02`, `W-CON-05` 6 firing rulings; `W-CON-04` uncalibrated |
| Consistency, ordering | `W-CON-03` | mechanical | Confirmed when the package carries both a signature timestamp and a later evidence timestamp. Overruled where that ordering holds in the package and the firing misreports it. | the package carries only one of the two timestamps | 2 silence rulings |
| Consistency, factor-decision | `W-CON-01` | judgment | Author judgment. A factor carrying evidence and no level under an accepted decision is what A-10 produces on purpose, so this pattern is the one most sensitive to a declination. | — | 1 firing ruling |
| Structural integrity, binding | `W-SI-02` | mechanical | Confirmed when the named binding is genuinely absent from the package. The pattern ships as two rule blocks under one identifier, one for the requirement binding and one for the validation-result binding, so a disposition names which of the two fired. | — | 4 silence rulings |
| Structural integrity, signature | `W-SI-01` | mechanical | Not Applicable on any package that validates: the signature is a mandatory field, so a package genuinely missing it is non-conformant rather than weak. Note also that the pattern does **not** fire on an unsigned package, because import writes a placeholder signature and the pattern tests absence rather than validity, so its silence never means the package is signed. | always, on a package that validates | 4 silence rulings |
| Compound patterns | `COMPOUND-*` | excluded | Not dispositioned individually. They report coexistence of firings already dispositioned above. | — | 3 firing rulings confirm they report coexistence correctly |
| Pack-specific patterns | any `W-<PACK>-nn` | as the core family it resembles | A pack ships patterns of its own, and each takes the rule of the core family it resembles rather than a rule per pack. A pattern testing for a factor asserted without its linked evidence is a consistency pattern. | as the family it resembles | uncalibrated |

**Both worked examples landed in v0.2.** *(A2, A3)* The full worked disposition — one row from
source citation to verdict — is **D-06**, and the Not-Applicable-versus-Overruled distinction is
carried by the **COU1/COU2 pair**, whose Not-accepted decision changes which firings are *about*
the decision rather than incidental to it. Both are set out in full, with their evidence, in
`docs/Protocol_v0_2_Amendments_Draft.md` §A2 and §A3, adopted with this version.

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

**B, where the verdict rules come from.** Part B was first written from the pattern bodies alone.
Its rules are now derived from 71 author adjudications of packages against the catalog. Setting
aside 21 ruled out of scope leaves 50, of which 47 name a target pattern and feed the table; the
remaining three record no target pattern and feed no rule. The mapping is ruled:
a correct detection yields Confirmed, an existing-rule misbehavior yields Overruled, and a
generator artifact yields either Not Applicable or Confirmed depending on the condition below.

**B, calibrating a verdict on a firing from a ruling about a silence.** A verdict dispositions a
firing, yet of the 47 rulings behind the table only 21 are firings; the other 26 are cases where
the pattern stayed silent. Those calibrate by contrapositive rather than directly: a silence with the property present establishes the
condition under which a firing would be wrong, which is Overruled; a silence with the
precondition genuinely absent establishes that the pattern fires only when the flaw is real,
which is Confirmed. This is the same distinction A-12's silence rule draws, and the Calibration
column keeps firing rulings and silence rulings apart so that no rule appears better evidenced
than it is.

**B, the generator-artifact split.** Those rulings divide on one condition rather than on which
pattern was targeted. Where the package failed structural validation, the pattern's precondition
is not meaningful and the verdict is Not Applicable; `W-ON-01` and `W-SI-01` test mandatory
fields, so their flaw cannot exist in a package that validates at all. Where the package is
valid and the flaw simply is not present, the pattern's silence is correct and a firing on such
a package would be Confirmed. The condition is stated rather than the pattern list, because a
list would fix each pattern to whichever half its sample happened to fall in.

**B, what the calibration corpus is and is not.** The adjudicated packages were generated before
a catalog refinement that moved the negative-control clean rate from near nothing to almost
all, and one ruling records that its evidence predates a rule rewrite. The 71 are also a
deliberately enriched sample, combining every case where a judging ensemble failed to agree with
a stratified draw from the cases it did agree on, so they are harder than a random package and
the rules derived from them are tuned on hard cases. Three patterns whose rulings are all
silences, `W-EP-03`, `W-AR-04` and `W-CON-03`, are among the four the decision record calls
enrichment-required: proven unable to fire on evidence this protocol itself produces. That is the
same finding as `docs/SCHEMA_FINDINGS.md` SF-3 records for `W-EP-02`, and it is why a silent
pattern is never read as clearance.

**B, `W-AR-03`.** Its class is ruled MECHANICAL by the 2026-08-16 decision record, Addendum A,
on the re-derivability criterion: the comparison runs on declared package fields, so a script
re-derives the label. The absence of a controlled vocabulary for verification methods makes the
rule weaker, not human-dependent, and the hardening was deferred rather than the classification
left open. The draft carried the pattern as unresolved; that is now closed.

**B, the verdict names.** Earlier planning documents name the three verdicts Accepted, Not
Accepted and Not Applicable. This document renames the first two to Confirmed and Overruled,
because `Accepted` is already the decision-outcome vocabulary a package carries and a reviewer
reading both in one artifact cannot tell which is meant. Records written before this version keep
the old names.

**B, structural integrity.** An unsigned package carries a zero-filled placeholder rather than
no signature, so the missing-signature pattern never fires on one. Integrity checking catches
it and the weakener report does not (F-6d).

**The principle behind A-10, A-12 and A-13.** The system may decline to decide, but it may never
decline invisibly. A-12's silence rule, A-13's refusal to let import success stand as
completeness evidence, and A-10's declination disclosure are three faces of one design
principle; the A-10 case is what forced it into words, when a conservative encoder following the
rule as first written could drop the value a source exists to demonstrate and leave nothing in
the record to say it had.

---

# Part D — v0.2 amendments, and what validated each

Adopted in a single event on 2026-08-29, when the C-series reported. Each item below is marked
against the evidence, not against having been drafted: `docs/Protocol_v0_2_Amendments_Draft.md`
carries the full text and citations for every row.

## Batch A — v0.1-era, evidence complete before the stranger series

| item | rule, in one line | validated by |
|---|---|---|
| **A1** | Operator identity is declared, not inherited; `wasAttributedTo` is who ran the tool | the Johnson package signed carrying an identity nobody chose (`protocol-v0_2-notes.md`) |
| **A2** | D-06 as the worked disposition, source citation to verdict | committed adjudication record |
| **A3** | The COU1/COU2 pair as the Not-Applicable-versus-Overruled example | the Not-accepted decision record, committed |
| **A4** | Sign-off verifies against the published wheel at whatever version is then current | both NASA substrates signed under 0.11.0, verifying under published 0.12.0 in a clean venv outside the repo (`studies/ch4_numbers/LEDGER.md` §4.5) |
| **A5** | The vacuous-green check finding, landing with its batch | the check written to catch F-3d passing on F-3d's own case |

### P2-3 rule 1 — instruction rows are never evidence and are never anchored

**Reclassified into Batch A on adoption, by evidence lineage rather than drafting history.**

*Validated by v0.1-era evidence (`docs/donetest/FIVE_SEATS_ONE_TRAP.md`: five unsteered
sessions meeting one documented fabrication affordance, zero surviving fabrications). The
C-series could not exercise it because the trap was remediated before the batch. Reclassified to
Batch A by that lineage.*

Batch A is defined as evidence-complete and committed, which this is; it sat in Batch B only
because it was drafted alongside the stranger amendments. The adoption condition's clause — *an
item that evidence cannot validate does not land on the strength of having been drafted* — cuts
both ways: it forbids waving items through, and equally forbids marking an item unvalidated when
its validation exists, is committed, and merely predates a series structurally unable to re-reach
it. A rule left pending on evidence that cannot exist would be the UNANSWERABLE state misfiled as
a refusal.

The rule stays because the *next* trap's encoder needs a lawful move, not because this one
recurred. Its adjacent behaviour is evidenced at scale by rule 2 below.

## Batch B — stranger-series amendments, validated against the C-series

| item | rule, in one line | C-series evidence |
|---|---|---|
| **P2-1** | Complete = no gates owed **and** the decision signed | **10/10** reached signature under a prompt naming the deliverable; the boundary is operable, not merely correct |
| **P2-2** | The verdict is authored after the judgments it rests on | **10/10 by measurement** — every decision act postdates every judgment act in the ledger; narrowest margin 52 seconds |
| **P2-3 rule 2** | An obligation that cannot be lawfully discharged is recorded as a finding, never fabricated past | **9/10** recorded escalation or schema-finding entries; **10/10** recorded dispositions rather than fabricating past them |
| **P2-4** | Gates clearing establishes readiness, not completion; attestation is a separate act | **10/10** reached `READY TO SIGN` and then performed a distinct sign act |

**P2-2 was validated by measurement rather than recollection**, and the distinction is the point:
a protocol whose rules are hoped-followed is not the same artifact as one whose rules are
timestamped. Ten ledgers were read; ten orderings held.

---

# Appendix — Validation record

**The measured completion rate, entering as v0.1's stranger test entered before it.**

> In **10 of 10** pre-registered trials, an unsteered frontier-model reviewer, given the task
> statement and a browser as its sole working surface — eleven browser tools, no other tool
> touched, enforced by transcript audit with any violation voiding the run — completed this
> protocol through signature: producing a package that verifies under the published `uofa` wheel
> (measurement hash, measurement signature, decision signature under independent keys).

    counted runs        10        endings: 10 signed-export
    verification        30 checks, 0 failures, each from a fresh environment
    condition pins      10/10 read `same` — a trial of the frozen condition
    voids               1 (tool-surface breach), replaced; ledgered in the report

Pre-registered before the first counted run in
`credenza/docs/donetest/C_SERIES_PREREGISTRATION.md`; reported in
`credenza/docs/donetest/C_SERIES_REPORT.md` with the composition table, the void ledger and the
verification transcripts.

**What the rate does and does not say.** The signatures attest completion of the governed review
**with dispositions recorded where evidence was unrecoverable** — nine of ten packages explicitly
declined to claim judgment, their covers reading *"No required level was judged … this package
does not claim otherwise."* They are **not** assertions that achieved levels meet requirements.

Out of scope, as pre-registered: soundness of the extraction (predeclared levels in the test
source are legible only as cell shading, so a text-fed extractor sees a gap and fills it);
assessment quality of the source paper; and **human-reviewer executability**, which is carried by
the earlier stranger evidence and not by this series. This is a model-reviewer claim.

**The void is the record's load-bearing entry.** One run signed, then touched a non-browser tool
after the signature for a purpose unrelated to the encoding, and was voided by the harness's own
audit. The claim says *no other tool touched*, not *no other tool touched in a way someone judged
material*. The numerator contains no run that reached for anything.

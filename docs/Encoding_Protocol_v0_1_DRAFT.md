# Encoding Protocol v0.1 (DRAFT)

**AWAITING-AUTHOR.** A machine-produced first draft written from
`Encoding_Protocol_Outline_v3.md`. It governs nothing until the author has corrected it and
committed the result as `Encoding_Protocol_v0_1.md`. Each `[AUTHOR-CONFIRM]` marker names a
sentence the draft is not confident reproduces the author's practice. Evidence base is the
Johnson pilot at `dev/build/pilot-johnson/`, cited by finding number.

---

## 1. Purpose and scope

A reference encoding is a UofA package built by hand from a named published source, under
written procedure, as evidence about what the schema can and cannot carry. A hand encoding
produced by authorial judgment alone is an opinion about the source, and a second encoder
following that judgment cannot tell whether they reproduced it or merely agreed with it. The
protocol is what makes hand encodings evidence rather than opinion.

Evaluation references for H2 are outside this protocol. They are built under the annotation
protocol and never regenerated through the extract path, because H2 measures agreement with a
corrected self and an extractor-derived reference would make the extractor a party to its own
evaluation.

Encoding follows the published on-ramp at `uofa.net/start/from-excel`, and the run log pins
the site commit current on the day it ran. No example commit appears in this protocol. The v1
outline's example had drifted before the first encoding under it began, and a pin that goes
stale inside a governing document is worse than no pin.

Machine-drafted candidate review is preparation, not review. The protocol's review pass has not
occurred until the author performs section 3 in person, and a run log must never leave ambiguous
which of the two happened or who did it.

An encoding names its extractor by exact model string and version, and states what that
extractor is not the same as. Lineage is declared per encoding, never inherited from a spec
sentence. The Johnson pilot's governing spec asserted its extractor was the model the extraction
eval had used, when that eval ran on a local four-billion-parameter model and the frontier arm
belonged to a different study (F-1c).

Set `base_uri` to a namespace you control before extraction begins. The on-ramp never mentions
it, import warns that identifiers are minting under a placeholder domain, and the identifier is
covered by the signature and cannot be corrected afterward (F-1b).

## 2. Source-evidence intake

Admissible source material is the published document and the supplementary material published
with it. Secondary summaries and recollection of talks are not. Synthetic evidence bundles are
admissible, because this protocol governs process rather than source authenticity, and the
package states its source class so no reader has to infer it. [AUTHOR-CONFIRM: the Morrison
recall belongs here, specifically which supplementary material was used and what was
deliberately excluded.]

Admissibility also runs within a document. A single source can interleave evidence about the
model with tutorial about the standard, in one voice, and an intake rule admitting "the
published paper" admits both (F-2a). The encoder draws the evidence boundary in the
source-scoping note before extraction. Drawing it afterward is a different act, because by
then the encoder has read the tutorial and cannot unread it.

Every reviewed value carries a citation to a page, section, table, or figure. The anchor lives
at row level in the workbook's trailing Source Anchor column, the spreadsheet's natural unit,
and at cell level in the review ledger wherever a row's cells diverge in origin (F-2c). The
column is mandatory and protocol-check validates it. The anchor does not survive import into the
JSON-LD, a disclosed limitation carrying a schema note for the post-defense increment (F-2b), so
a reviewer holding the package holds less than one holding the workbook and both are
committed.

Where a value is recoverable only by non-textual means, the citation anchor names the recovery
method as well as the location, the value is recorded as author-side work rather than extractor
output, and the method ships with the encoding. Johnson's predeclared credibility levels exist
only as green cell fill in one table, with no text for any extractor to read, and were recovered
from the page's fill geometry then corroborated against three statements the recovery had not
used (F-2d).

When a source discloses its own distortion, the encoding is faithful to the source and
knowingly unfaithful to the world, and says so. Johnson's worked example describes itself as a
heavily disguised real application, so the encoded real-world system is what the paper states
(F-2e).

A source can over-determine a field as well as underdetermine it. Johnson does this three
times, most sharply where one response both describes a Technical Authority approved waiver and
denies any waiver was required (F-4b). The encoding records the reading it chose, enters the
contradiction in the ambiguity log with an anchor for each reading, and never harmonizes
silently. Where one reading is an answer and the other a declination to answer, the answer
outranks the declination and the declination is kept as context. That settles one of Johnson's
three; the other two remain author judgment, which is the honest limit of the rule.

## 3. The extract, review, and import procedure

Scope the source and write the scoping note with its evidence boundary. Set `base_uri`.
Extract with the pack named. Open the workbook and add the Source Anchor column if the template
lacks one. Review in factor order, levels first. Import with the completeness check and without
signing. Run the rule engine and draft dispositions. The run log records the model string, the
backend, the prompt hash, the site commit, the repository HEAD, and the `base_uri`, because an
encoding that cannot be reconstructed is not evidence about a procedure. [AUTHOR-CONFIRM: the
on-ramp reviews sheet by sheet and this reviews in factor order; confirm that is your practice
and that levels-first is why.]

Every cell is confirmed against the source, corrected against the source, or marked
source-absent, and no cell passes on extractor confidence. That base rule is necessary and not
sufficient, in two ways the pilot found.

Review runs against the source location that should carry the value, not against the
extractor's output or rationale. A synthesized value arrives with a plausible rationale
attached, and the confidence signal does not separate it from a read one. The pilot's extractor
returned 141 of 142 cells as review-suggested rather than high-confidence, which is honest
reporting and exactly why it does not help.

Defaulted fields are not extracted fields. The extract prompt carries a documented default
setting each factor's required level equal to its achieved level unless the narrative names a
gap. Johnson writes his required levels as table shading rather than prose, so the default fired
on all seventeen factors carrying levels, and the resulting column was complete, plausible,
schema-valid, and from nowhere (F-3b). It erased both exceedances the paper exists to
demonstrate. Required and achieved are therefore reviewed against different source locations and
confirmed separately, and required equal to achieved on every factor is treated as unreviewed
until the predeclaration has been located. Until the workbook distinguishes extractor-asserted
from extractor-defaulted cells, the reviewer consults the extract prompt's default list.

Adding an evidence row is a review act. The verbs above operate on a cell that already
exists, and the pilot met a firing clearable only by adding a row the source plainly supports
(F-3c). Adding a row is permitted when a source anchor supports it and is recorded in the
review ledger as a correction is.

Record the import provenance counts and treat a surprise in them as something to investigate
rather than as a result. They classify eleven summary-level fields and see no factor-level
review, so a pass of ninety-seven decisions across a hundred and fifty-five cells reported four
extracted fields (F-7a).

Where the source's scale or vocabulary cannot map mechanically onto the pack's, decline to
populate. Disclose the declination together with its consequence, and file the mapping gap as a
schema finding. Inventing a value is never the resolution, and the consequence has to be stated
because it is real. Johnson's encoding declines to rewrite a nought-to-four credibility level
onto a one-to-five factor, and every derived metric in the resulting package reads zero
against a source asserting otherwise (F-5a, F-3e). Understating a source is a smaller failure
than overstating it and it is not a free one. The standing examples are Johnson's two
escalations, an input-pedigree factor the pack cannot hold and a Level 0 convention thirteen
of nineteen factors cannot express.

## 4. Disposition procedure

**Dispositions adjudicate against the package.** Every other rule here depends on it. A
weakener firing is a statement about the artifact a reviewer receives, and nine of the pilot's
twelve firings were true of the package and false of the paper behind it (F-4a). Those nine
state what the encoding failed to carry, and dispositioning them against the source would
suppress warnings correct about the thing under review. The delta between what the source
holds and what the package carries lives in the ambiguity log and routes to the
schema-findings channel, never in a suppressed warning. This also keeps disposition semantics
identical whether the source is real or synthetic.

The consequence is worth stating. Adjudicating against the package makes every mechanical
firing on a correctly encoded artifact Accepted, and all twelve pilot candidates resolve that
way, so the verdict carries little information on the mechanical patterns and all of it on the
other two values. [AUTHOR-CONFIRM: the draft's inference from the adjudication rule rather than
something you stated, and it changes what the dispositions table is for.]

**Accepted** means the package exhibits the gap the pattern describes. **Not Accepted** means
the pattern fired but the package does not exhibit it, a false positive against package content
rather than a disagreement with the source. **Not Applicable** means the pattern's precondition
is not meaningful for a package of this class. A criterion is testable when it references what
the source says as carried by the package; where none can be written the pattern is JUDGMENT
class.

Class assignment is not the encoder's to make. The A1 partition rules sixteen patterns
MECHANICAL and four JUDGMENT, leaves W-AR-03 unresolved, and excludes the compound patterns.
This protocol adopts it rather than re-deriving it, and W-AR-03 is recorded unresolved wherever
it fires.

### Per-family rules

Derived from the pattern bodies in `packs/core/rules/uofa_weakener.rules` and the twelve
dispositioned rows of the Johnson pilot. The outline specifies Morrison COU1 dispositions as the
source and those are not committed anywhere, so every rule below carries a marker.

**Provenance and epistemic.** W-PROV-01 and W-EP-01 through W-EP-03 fire on a missing or
terminating derivation edge. Accepted when the package does not carry it; Not Accepted only
where the edge is present and the rule failed to traverse it. W-EP-04 is JUDGMENT, because
whether an unassessed factor at elevated model risk undermines the claim depends on what the
context of use needs from it. [AUTHOR-CONFIRM]

**Alignment.** W-AL-01 and W-AL-02 fire on evidence the package does not carry. Accepted when
the node is absent; the source's possession of the underlying work is an ambiguity-log entry and
never a reason to disposition otherwise. Johnson documents his sensitivities and rates a factor
on them, and the package still carries none because the on-ramp has no route to one.
[AUTHOR-CONFIRM]

**Ontology.** W-ON-01 and W-ON-02 fire on a context of use that is absent or unbounded.
Accepted when the package carries neither an applicability constraint nor an operating envelope.
Johnson states his envelope four ways and the workbook holds none of them. W-ON-02 is a known
observation across the queue rather than a property of any one encoding. [AUTHOR-CONFIRM]

**Argumentation.** W-AR-04 and W-AR-05 are mechanical, testing a version mismatch and a
missing comparator link. Accepted when the link is absent, including when the comparator is
real but not the kind of thing a URI names, which is how five of Johnson's firings arose.
W-AR-01 and W-AR-02 are JUDGMENT, because a required level without acceptance criteria and an
acceptance standing above a shortfall are claims about whether the reasoning holds, and no
test of package content settles either. [AUTHOR-CONFIRM]

**Consistency.** W-CON-02 through W-CON-05 are mechanical. W-CON-01 is JUDGMENT and is the
pattern most sensitive to the declination rule, because a factor carrying evidence and no level
under an accepted decision is what section 3 produces on purpose. Three of Johnson's firings are
this case, and they exist because the encoding refused to invent levels rather than despite it.
[AUTHOR-CONFIRM]

**Structural integrity.** W-SI-01 and W-SI-02 are mechanical. W-SI-01 does not fire on an
unsigned package, because import writes a zero-filled signature placeholder and the pattern
tests absence rather than validity. Integrity checking catches this and the weakener report does
not, so an unsigned package is never dispositioned as though that silence meant anything.
[AUTHOR-CONFIRM]

**Pack-specific patterns.** A domain pack may ship patterns of its own, and they take the rule
of the core family they resemble rather than a rule per pack. The NASA patterns that test for a
factor asserted without its linked evidence are consistency patterns and are Accepted when the
link is absent, which is how two of Johnson's firings resolve. [AUTHOR-CONFIRM]

[AUTHOR-CONFIRM: the Not Applicable rule belongs here and needs a Morrison COU2 case, where the
distinction between Not Applicable and Not Accepted actually bit. No committed record exists.]

The disposition pass covers every factor the pack expects rather than every firing the engine
raised. Eleven of Johnson's factors carried no level and a non-assessed status and drew no
weakener, because W-CON-01 excludes those statuses by design, so the encoding's largest gap is
the one the engine says least about (F-4e). Those factors receive an explicit disposition,
ordinarily source-absent or declined-mapping. A dispositions table containing only engine-raised
rows is incomplete and fails section 6.

The verdict and the action class are different vocabularies and neither derives from the
other. The verdict states the credibility judgment; the action class states the remediation
posture, drawn from the controlled set running from restricting the context of use through
accepting residual risk. An action class is never inferred from a verdict (F-4c).

[AUTHOR-CONFIRM: the worked example. The strongest candidate is the Technical Authority
waived validation, the one pilot firing that reads correctly whether adjudicated against
source or package. It cannot be cited as dispositioned until the governed review pass runs.]

## 5. The ambiguity log

An entry is mandatory whenever the source underdetermines a field, whenever a cross-standard
mapping is not mechanical, and whenever the source over-determines a field inconsistently in
the sense of section 2. The pilot opened twenty-five entries, nineteen before extraction ran.
A rename across standards carrying a level unchanged is recorded even though nothing about it
is difficult, because the record of an easy decision is what lets a second encoder check it. A
factor the source predeclares and achieves, which the pack has no field for, is recorded as
something the encoding could not do rather than something it decided. [AUTHOR-CONFIRM: one
Morrison ambiguity belongs here as a third example.]

An entry states the ambiguity, the resolution chosen, and the rule applied in choosing it. The
log is a committed file beside the package rather than a workbook sheet, because entries
carrying quoted source text do not fit a spreadsheet column and escalations have to survive
independently of the package they were raised against (F-5b). The workbook may carry a pointer,
and protocol-check tests that the file exists and is non-empty.

Some entries are explicitly not resolutions. Where the encoder meets a schema gap that must
not be worked around, the entry is marked ESCALATION, routes to the schema-findings channel,
and the encoding proceeds under the declination rule (F-5a). An escalation that later
acquires a resolution is amended rather than replaced, so the record shows the gap was met
before it was closed.

## 6. Completion and the stopping rule

An encoding is complete when import passes with every mandatory field either populated or
explicitly marked source-absent, when the declared profile is earned rather than asserted, when
the citation column and ambiguity log are populated per sections 2 and 5, and when the
dispositions table covers every factor the pack expects. The profile machinery already works;
the pilot declared Complete in its workbook and earned Minimal, which is correct.

Completion does not certify that the package represents its source well. Import success and
schema conformance are both satisfiable by a package that understates its source, and the pilot
passed both with all four derived credibility metrics reading zero under the declinations of
section 3 (F-6a). Derived metrics are not completeness evidence, and the declination disclosure
is the only place an understatement is made legible. Completion is checked against the package
rather than the console because import currently prints the declared profile while writing the
derived one (F-3e).

Most rules above are verifiable by script, and that set is the protocol-check specification
implemented as a flag on extract and import. The per-family rules of section 4, the evidence
boundary of section 2, the reviewer-identity boundary of section 1, and every JUDGMENT-class
disposition are not.

## 7. Provenance and the human contribution

The import provenance counts cannot see the review pass. They classify eleven summary-level
fields and no credibility factor, validation result, or decision record, so a package reviewed
cell by cell and one imported straight from the extractor report identical counts (F-7a). The
auditable record of the human contribution is therefore the review artifact rather than the
count, meaning the anchored workbook and the review ledger committed beside the package. The
ledger is mandatory for a reference encoding until the tooling can see what it records.

One provenance class is missing rather than coarse. Author-side recovery, of the kind section 2
requires for a non-textual value, is human work no existing class describes (F-7b). Until one
exists, the review ledger carries the distinction.

## 8. Versioning and deviation

This is protocol version 0.1, and every encoding records the protocol version that governed
it. Any departure is recorded in the ambiguity log with its rationale, which the pilot
exercised three times before this document existed. Runs executed before the protocol existed
are labeled as such and superseded by governed passes rather than retrofitted into
compliance.

Pack version and standard version are separate facts, recorded separately. The pilot's package
is pack `nasa-7009b` version 0.5.0 encoding an assessment written against NASA-STD-7009A, and
those are not the same statement. The version-agnostic alias for that standard resolves to the B
identifier, so an assessment entered the natural way is silently graded against a standard it
does not claim (F-8b).

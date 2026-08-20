# Encoding_Protocol_v0_1.md — Outline and Writing Prompts, v3

Target: 4-6 pages. Praxis appendix + committed to repo at docs/. Voice: yours. The prompts
tell you what each section must establish and what question it protects; the words are
yours to write. Where a prompt asks for Morrison/Nagaraja recall, that recall IS the
content.

v3 change: fully reconciled against the pilot's expanded PROTOCOL_FINDINGS.md
(dev/build/pilot-johnson/, branch claude/uofa-encoding-pilot-plan-rwe9tu). Every F-number
below is that memo's. v2's [PILOT] folds are kept; v3 adds the findings v2 missed (F-1b,
F-1c, F-2a, F-2c granularity, F-3c, F-3d, F-4b ordering rule, F-4e, F-5a escalation class,
F-5b, F-6a, F-7b, F-7c, F-8b) and corrects one premise (F-1c: the extractor lineage
claim).

Writing constraints: no em dashes, no tripartite lists, no colon chains, prose over
bullets in the final text.

---

## §1. Purpose and scope (half page)

**Must establish:** what this protocol governs and what it does not. Reference encodings
and the human review pass are in; H2 evaluation references are out (annotation protocol,
extractor-independent by design).

**Prompt 1a:** The one-paragraph statement of what a reference encoding is and why written
procedure rather than authorial judgment. Close to "the protocol is what makes hand
encodings evidence rather than opinion."

**Prompt 1b:** The separation sentence for H2 references. Two sentences, no more.

**Prompt 1c:** Workflow inheritance, with the pin rule generalized: encoding follows the
published on-ramp, and the encoding's run log pins the site commit current on its day. Do
not hardcode an example commit in the protocol; the v1 outline's example (01c7372) had
already drifted (31cb466) before the first pilot ran, which is the demonstration that the
pin belongs in the run log. [F-1a]

**Prompt 1d:** The reviewer-identity boundary: machine-drafted candidate review is
preparation; the protocol's review pass has not occurred until the author performs §3b. A
run log reading "review complete" must never be ambiguous about who reviewed. [pilot
session boundary]

**Prompt 1e (new):** The extractor-lineage rule. An encoding names its extractor by exact
model string and version, and states what it is not the same as. The pilot's own spec
inherited a false lineage claim ("the same frontier model the extraction eval used") when
the extraction eval ran on local qwen3.5:4b and the frontier arm belonged to a different
study (the model-selection scorecard). Lineage is declared per encoding, never inherited
from a spec sentence. [F-1c]

**Prompt 1f (new):** The namespace rule. Before extraction, set base_uri to a namespace
you control; the on-ramp never mentions it, import warns that identifiers mint under the
example.org placeholder, and the id is covered by the signature so it cannot change after
signing. One sentence in the protocol; TOOLING note that the on-ramp page needs the same
sentence. [F-1b]

## §2. Source-evidence intake (three-quarters page)

**Must establish:** what counts as source, within-document admissibility, the anchoring
rule and its granularity, and the two source pathologies.

**Prompt 2a:** Admissible source material, Morrison recall, plus two additions. Synthetic
bundles are admissible; the protocol governs process, not source authenticity, and the
package states its source class. And the within-document rule the Johnson paper forced: a
single source can interleave evidence about the model with tutorial about the standard in
one voice, and the encoder draws the evidence boundary in the source-scoping note before
extraction, listing what is admitted and what is excluded. [F-2a]

**Prompt 2b:** The anchoring rule with its granularity decided. Every reviewed value
carries a citation to page, section, table, or figure. Granularity: row-level anchor in the
workbook's trailing Source Anchor column (the natural spreadsheet unit; one row often
cites several pages), cell-level anchors in the review ledger where a row's cells diverge.
Both halves of the survival problem stated: the column is mandatory in the workbook
(protocol-check validates presence), and the anchor's absence from the JSON-LD is a
disclosed limitation with a schema note for the post-defense increment. [F-2b, F-2c]

**Prompt 2c:** The non-textual recovery worked example and rule. Johnson's predeclared
levels exist only as green cell fill in Table 3, recovered from page geometry,
corroborated three ways against text the recovery did not use. Rule: where a value is
recoverable only by non-textual means, the citation anchor names the recovery method as
well as the location, the value is recorded as author-side work rather than extractor
output, and the method ships with the encoding. [F-2d]

**Prompt 2d:** The self-declared-disguise rule: when a source discloses its own
distortion, the encoding is faithful to the paper, knowingly not to the world, and says
so. Not a defect; must not be silent. [F-2e]

**Prompt 2e (new):** The self-contradicting source rule, now with its ordering principle.
Johnson is over-determined and inconsistent three times; §5's underdetermination trigger
does not cover this, so it is a §2/§4 rule: the encoding records the reading chosen, the
contradiction enters the ambiguity log with both anchors, no silent harmonization, and
where one reading is an answer and the other a declination, the answer outranks the
declination with the declination kept as context. That ordering rule covers one of
Johnson's three; the other two stay author judgment, which is the honest limit of the
rule. [F-4b]

## §3. The extract-review-import procedure (one page)

**Must establish:** the ordered procedure, where human judgment enters, the defaulted-field
hazard, and the fourth review verb.

**Prompt 3a:** The procedure as you run it, numbered. Run-log discipline per the pilot:
model string, backend, prompt sha, site commit, repo HEAD, base_uri. Where practice
differs from the on-ramp page, say so and why.

**Prompt 3b:** The review rule, upgraded twice by the pilot. Base rule: every cell
confirmed against the source, corrected against the source, or marked source-absent. First
upgrade: review is against the source location that should carry the value, not against
the extractor's output or rationale, because a synthesized value arrives with a plausible
rationale attached and honest confidence (141 of 142 cells yellow) does not make it
sourced. Second upgrade: defaulted fields are not extracted fields. The prompt's
required=achieved default converted an unreadable source field into a confident,
schema-valid column that erased the paper's headline. Required and achieved levels are
reviewed against different source locations and confirmed separately; required equal to
achieved on every factor is treated as unreviewed until the predeclaration is located.
TEMPLATE-CHANGE: the workbook distinguishes extractor-asserted from extractor-defaulted;
until it does, the reviewer consults the extract prompt's default list. TOOLING:
protocol-check flags all-factors required==achieved. [F-3a, F-3b]

**Prompt 3c (new):** The fourth review verb. Confirm, correct, and mark-source-absent all
act on an existing cell; the pilot hit a firing clearable only by adding an evidence row
the source plainly supports, which no verb covers. Rule: adding a row is a review act,
permitted when the source anchor supports it, recorded in the review ledger like any
correction. The pilot declined and escalated, which was right for a pilot; the protocol
makes it a governed act. [F-3c]

**Prompt 3d:** The provenance self-audit, rewritten. The counts classify eleven summary
fields and see no factor-level review (97 decisions, 155 cells, reported as 4 extracted).
Record the counts, but the auditable record of the human contribution is the anchored
workbook plus the review ledger; a surprise in the counts is investigated, never trusted
in either direction. [F-7a, feeds §7]

**Prompt 3e:** The decline-versus-synthesize rule. Where the source's scale or vocabulary
cannot map mechanically onto the pack's, decline to populate, disclose the declination and
its consequence (derived metrics reading 0.00 against a source asserting otherwise), and
file the mapping gap as a schema finding. Invent-and-overstate is never the resolution.
Johnson's two escalations (Input pedigree homeless, Level 0 inexpressible on 1-5 factors)
are the standing examples. [F-5a, headline finding 3]

**Prompt 3f (tooling note, not prose):** Two import defects the protocol works around
until fixed: template hint text survives into data rows where the model wrote nothing
(reviewer clears them; protocol-check candidate), and import prints the declared profile
while writing the derived one (completion checks the package, not the console). [F-3d,
F-3e]

## §4. Disposition procedure (one and a half pages, the core section)

**Must establish:** the adjudication basis, the testable criteria per weakener class, the
silence rule, and the vocabulary relation.

**Prompt 4a-0 (write first):** The adjudication-basis rule, ruled during the pilot:
dispositions adjudicate against the package. Nine of twelve pilot firings were true of the
package and false of the paper; they are true statements about what the encoding failed to
carry. The package-versus-source delta lives in the ambiguity log and the schema-findings
channel, never in suppressed warnings. This keeps disposition semantics identical across
real and synthetic sources. [F-4a]

**Prompt 4a:** The testability principle: a criterion is testable when it references what
the source says as carried by the package. Where it cannot be made testable, the pattern
is JUDGMENT class and the disposition is recorded as author judgment under this protocol.

**Prompt 4b:** Per-family decision rules from your Morrison COU1 dispositions, two or three
per family, reverse-engineered. Still half the writing time. Test each written rule against
the pilot's twelve DRAFT rows; where your rule and the pilot's candidate diverge, the
divergence is the content.

**Prompt 4c:** The Not Applicable rule from a COU2 case. Unchanged.

**Prompt 4d:** The worked example. Candidates, all harder than Morrison's: the TA-waived
validation (D-06, the one firing right on both readings), the negotiated M&S History
predeclaration, the incomplete randomization judged inconsequential by SMEs (whose judgment
does the encoding record?), the retained outlier. Any Johnson case used must wait for your
governed review pass to be citable as dispositioned. [F-4d]

**Prompt 4e (new):** The silence rule. Eleven factors carrying no level and a non-assessed
status drew no weakener, because W-CON-01 excludes those statuses by design; the encoding's
largest gap is the one the engine says least about. Rule: the disposition pass covers every
factor the pack expects, not every firing the engine raised; factors with no firing and no
level get an explicit disposition (typically source-absent or declined-mapping with the
§3e disclosure). A dispositions table with only engine-raised rows is incomplete. [F-4e]

**Prompt 4f:** The vocabulary relation, two or three sentences: the verdict (Accepted / Not
Accepted / Not Applicable) is the credibility judgment; actionClass (restrict-cou,
acquire-validation, characterize-region, accept-residual-risk, change-cou) is the
remediation posture; one does not derive from the other. [F-4c]

## §5. The ambiguity log (half page)

**Prompt 5a:** The trigger, extended: an entry is mandatory whenever the source
underdetermines a field, whenever a cross-standard mapping is not mechanical, and whenever
the source over-determines inconsistently (§2e). Point at the pilot's 25 entries and pull
two examples, plus one Morrison recall. [F-5c]

**Prompt 5b:** Entry shape and home, revised: the ambiguity, the resolution chosen, the
rule applied. Home is a committed log file beside the package, not a workbook sheet; 25
entries with quoted source text do not fit a column, and escalations must survive
independently of the package. The workbook may carry a pointer. protocol-check tests the
file's existence and non-emptiness. [F-5b]

**Prompt 5c (new):** The escalation entry class. Some entries are explicitly not
resolutions: schema gaps the encoder must not work around (Input pedigree homeless in the
pack; Level 0 inexpressible on 13 of 19 factors). The log marks these ESCALATION, they
route to the schema-findings channel, and the encoding proceeds with the §3e declination.
[F-5a]

## §6. Completion and the stopping rule (third of a page)

**Prompt 6a:** The completion rule: import passes with every mandatory field populated or
explicitly source-absent, the profile earned not asserted (the machinery works; the pilot
earned Minimal against a declared Complete), citation column and ambiguity log populated
per §§2 and 5, and the dispositions table covering every expected factor per §4e. Checked
against the package, not the console, until F-3e's fix lands. [F-6b, F-3e]

**Prompt 6b (new):** What completion does not certify. Import success is satisfiable by a
package that understates its source: the pilot passed import and SHACL with all four
derived metrics at 0.00 under §3e declinations. State explicitly that derived metrics are
not completeness evidence, and that the §3e disclosure is where understatement is made
legible. [F-6a]

**Prompt 6c (tooling note, not prose):** The protocol-check spec, pre-seeded by the pilot:
citation column present and non-empty per populated row; ambiguity log file exists and
non-empty; no --sign in a pilot run log; required != achieved on at least one factor or an
explicit waiver recorded; no template placeholder strings in data rows; W-SI-01's
placeholder blindness noted for the catalog (zero-filled signature is a value, so the
missing-signature weakener never fires on unsigned packages; C1 catches it, the C3 report
a reviewer reads stays silent). [F-6c, F-6d]

## §7. Provenance and the human contribution (quarter page)

**Prompt 7a:** Rewritten from the pilot's proof. The counts cannot see the review pass, so
the paragraph v1 asked for is false as tooled. Write what is true: the auditable record of
the human contribution is the review artifact, the anchored workbook and the review ledger
committed beside the package, with provenance counts as partial summary-field lineage
pending tooling. The review ledger is mandatory for reference encodings until the tooling
catches up. Note the missing provenance class while you are there: author-side recovery
(the Table 3 cells) is human work counted nowhere; extracted, run-context, and defaulted
are all wrong for it. Feeds Ch3's Human Adjudication Role section honestly. [F-7a, F-7b,
F-7c]

## §8. Versioning and deviation (quarter page)

**Prompt 8a:** Protocol version, encodings record the governing protocol version,
deviations recorded in the ambiguity log with rationale. The pilot exercised this and it
worked (three recorded deviations with rationale). Add the pilot-labeling sentence: runs
executed before this protocol existed are labeled as such and superseded by governed
passes. [F-8a]

**Prompt 8b (new):** Pack version and standard version are separate facts, recorded
separately. The pilot's package is nasa-7009b 0.5.0 encoding a NASA-STD-7009A assessment,
and the version-agnostic alias folds onto the B identifier, so a 7009A assessment entered
the natural way is silently graded as 7009B. The encoding declares both, and the alias
fold is a TOOLING flag. [F-8b]

---

## Cross-cutting note for the writing pass, not protocol prose

Eight of twelve pilot firings trace to things the workbook cannot carry (SensitivityAnalysis
exists in the ontology and appears nowhere in the on-ramp toolchain; COU applicability
constraints; non-URI comparators dropped at import; the two escalated factors). These are
schema and toolchain findings feeding the post-defense increment and INV-20's chapter
material, not protocol rules. The protocol's job is §3e and §5c: decline, disclose,
escalate. Do not let §4's prose try to solve them.

## After drafting: three checks before you tag it

1. Checkable-first pass: mark each rule scriptable or not; the marked set extends the §6c
   pre-seeded protocol-check spec.
2. Read §4 against your Morrison COU1 dispositions AND the pilot's twelve DRAFT rows:
   would the written rules alone reproduce your verdicts and adjudicate the candidates?
   Include the §4e silence sweep: does your rule set disposition the eleven factors nothing
   fired on?
3. The adjudication sentence check: judgment enters at the review pass and the disposition
   procedure, governed by §§3-4, performed by a named author (§1d). If the Human
   Adjudication Role section can now say that, this document is done.

Estimated split: §4 is half the work. §§1-3 and 5-8 are substantially pre-answered by pilot
artifacts; 4b's per-family rules remain the fresh-attention block.

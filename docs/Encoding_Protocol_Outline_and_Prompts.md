# Encoding_Protocol_v0_1.md — Outline and Writing Prompts

Target: 4-6 pages. Praxis appendix + committed to repo at docs/.
Voice: yours. The prompts below tell you what each section must establish and what
question it protects; the words are yours to write. Where a prompt asks you to
recall a specific decision you made during the Morrison/Nagaraja/NASA encodings,
that recall IS the content — this document is you writing down what you already do.

Writing constraints you already hold: no em dashes, no tripartite lists, no colon
chains, prose over bullets in the final text (the outline's bullets are scaffolding,
not the format).

---

## §1. Purpose and scope (half page)

**Must establish:** what this protocol governs and what it deliberately does not.
Reference encodings and the human review pass are in; the H2 evaluation references
are out (governed by the annotation protocol, extractor-independent by design).

**Prompt 1a:** Write the one-paragraph statement of what a "reference encoding" is
in this praxis and why it must be governed by written procedure rather than
authorial judgment. You have said versions of this sentence in conversation for
months; the one you want is close to "the protocol is what makes hand encodings
evidence rather than opinion."

**Prompt 1b:** Write the separation sentence: evaluation references for H2 are
constructed under the annotation protocol and never regenerated through the
extract path, and why (agreement-with-corrected-self). Two sentences, no more.

**Prompt 1c:** State the workflow inheritance: encoding follows the published
authoring on-ramp (cite uofa.net/start/from-excel, pin the site commit that built
it — today's is 01c7372), and this protocol adds the requirements below for
praxis-grade encodings. One sentence.

## §2. Source-evidence intake (half page)

**Must establish:** what counts as source, and the citation-anchoring rule.

**Prompt 2a:** Define admissible source material for a reference encoding. Think
about what you actually used for Morrison: the published paper, which tables, which
supplementary material? What did you deliberately NOT use (emails, memory of talks,
secondary summaries)? Write the rule you actually followed.

**Prompt 2b:** Write the anchoring rule: every reviewed value carries a citation
to page, section, table, or figure of the source. State where the citation lives
in the workbook (a citation column per sheet? cell comment? decide now — this
becomes a template change if the workbook doesn't have a home for it, and
protocol-check will validate its presence).

**Prompt 2c:** Recall one concrete case where the source located a value somewhere
non-obvious (a number that lived in a figure caption, or supplementary table).
Write it as the worked example for the rule. One paragraph.

## §3. The extract-review-import procedure (one page)

**Must establish:** the ordered procedure, and where human judgment enters.

**Prompt 3a:** Write the procedure as you run it: extract against the source
folder with the pack named; open the workbook; review order (do you go sheet by
sheet in factor order? levels first, per the on-ramp's own advice?); fill blanks
from the PDF; import with sign and check. Number the steps. Where your actual
practice differs from the on-ramp page, say so and say why.

**Prompt 3b:** Write the review rule that answers "what does 'reviewed' mean":
every cell either confirmed against the source, corrected against the source, or
marked source-absent. No cell passes on extractor confidence alone. You wrote the
on-ramp's warning about confident-wrong levels; this is its procedural form.

**Prompt 3c:** State what the provenance line must show for a reference encoding
and what you do if it surprises you (e.g. extracted count higher than the number
of cells you remember confirming). This is the self-audit step.

## §4. Disposition procedure (one to one and a half pages — the core section)

**Must establish:** the testable criteria for Accepted / Not Accepted / Not
Applicable per weakener class. This is the section must-have 5 actually needs,
and the only section that exists nowhere else in any form.

**Prompt 4a:** Before writing criteria, write the principle in your own words:
a disposition criterion is testable when it references what the source text says,
not what the encoder believes. Where a criterion cannot be made testable, the
pattern is JUDGMENT class and the disposition is recorded as author judgment
under this protocol. (This sentence is the bridge to the label-class partition;
get it right and A9 writes itself.)

**Prompt 4b:** For each weakener family you dispositioned in the case studies
(epistemic, alignment, ontology, structural integrity, consistency, provenance,
argumentation), write the decision rule you actually applied. Method: open your
Morrison COU1 dispositions, take two or three, and reverse-engineer the rule you
used. Ask of each: what in the source text made this Accepted rather than Not
Accepted? If you cannot answer from the source text, that is a JUDGMENT pattern
and the honest rule is "author judgment applying [the consideration you used]."
Expect this prompt to take half your writing time. It should.

**Prompt 4c:** Write the Not Applicable rule separately: when is a weakener
pattern NA for a context of use rather than Accepted? Recall a COU2 case if one
exists (the Not Accepted package is where NA vs Not Accepted actually bit).

**Prompt 4d:** Worked example: one full disposition, source citation to verdict,
written out. Pick the one you found hardest in Morrison; the hard case
demonstrates the protocol better than an easy one.

## §5. The ambiguity log (half page)

**Must establish:** when an entry is mandatory and what it records.

**Prompt 5a:** Define the trigger: an entry is mandatory whenever the source
underdetermines a field (two plausible readings, a value implied but not stated,
a unit ambiguity). Recall two real ambiguities from the case studies and write
them as the examples. If you cannot recall any, that is itself worth a sentence
of honest reflection, because it likely means they went unrecorded, and this
protocol exists to stop that.

**Prompt 5b:** Define the entry shape: the ambiguity, the resolution chosen, the
rule applied. Decide where it lives (a log sheet in the workbook is the natural
home; naming it here makes it a template requirement protocol-check can test).

## §6. Completion and the stopping rule (quarter page)

**Must establish:** when an encoding is done.

**Prompt 6a:** Write the rule around the machinery that already enforces it:
encoding is complete when import passes with every mandatory field populated or
explicitly marked source-absent, the declared profile is earned not asserted
(the import already derives it), and the citation column and ambiguity log are
populated per §§2 and 5. State which parts import checks today and which parts
await protocol-check.

## §7. Provenance and the human contribution (quarter page)

**Must establish:** the package records which assertions came from extraction and
which from author correction, and why that matters for a praxis reader.

**Prompt 7a:** Write the paragraph connecting the import provenance counts to the
adjudication disclosure: the counts are the auditable record of how much of the
package the human shaped. One paragraph, and note it feeds Ch3's Human
Adjudication Role section nearly verbatim.

## §8. Versioning and deviation (quarter page)

**Prompt 8a:** State the protocol version, that encodings record which protocol
version governed them, and the deviation rule: any departure from this protocol
during an encoding is recorded in the ambiguity log with rationale. Two or three
sentences. This is what lets a future multi-encoder study execute the same
document, which is the future-work claim the manuscript makes.

---

## After drafting: three checks before you tag it

1. Checkable-first pass: for each rule, ask whether a script could verify
   compliance (field present, citation cell non-empty, log sheet exists). Mark
   the ones that can't be scripted; those markings are the protocol-check spec.
2. Read §4 against your actual Morrison COU1 dispositions: would following only
   the written rules reproduce your verdicts? Where it wouldn't, the rule is
   incomplete, not the verdict wrong.
3. The A9 sentence check: can the Human Adjudication Role section now say
   "judgment enters at the review pass and the disposition procedure, governed by
   §§3-4 of the published protocol"? If yes, this document is done.

Estimated split: §4 is half the work. If tonight's window covers only §§1-3, that
is a fine stopping point; §4 deserves the weekend block's fresh attention.

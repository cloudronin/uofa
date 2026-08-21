# Schema and tooling findings

The channel that encoding escalations route to. An encoding that meets a gap it must not work
around records an `ESCALATION` entry in its own ambiguity log and files the gap here, where it
survives independently of the package that found it.

Entries are numbered `SF-n` in the order they are filed. Each carries the same five fields:

- **Finding** — what cannot be expressed or cannot happen, in one sentence.
- **Cause** — the schema, pack or tooling property responsible.
- **Evidence** — the committed artifact that establishes it.
- **Consequence** — what an encoding loses, and whether it is blocked.
- **Status** — open until an author acts. Filing is not a proposal to change anything.

**This file is new, and the channel predates it.** `docs/Encoding_Protocol_Outline_v3.md` §5c and
`dev/build/encoding-prep/REVIEW_PACKET_JOHNSON.md` both route escalations here without a file
existing to route them to. SF-1 and SF-2 are the two gaps §5c names; both are entered from the
ambiguity-log rows that raised them, so the entries are transcriptions rather than new findings.

**A labelling collision, recorded rather than resolved.** `docs/Ruling_WAR05_Schema_Findings.md`
and `dev/build/pilot-johnson/Johnson_Author_Verdict_Record.md` both refer to the evidence-typing
gap as "SF-1" and the comparator-identity gap as "SF-2". Those labels are the ruling document's
own, and they collide with SF-1 and SF-2 as already filed here. This file's stated rule is that
entries are numbered in the order they are filed, so the two gaps are entered below as **SF-4**
and **SF-5**. **Ruled 2026-08-21: the order-of-filing rule wins and SF-4/SF-5/SF-6 stand.**
Where a conversational or ruling document says "SF-1" or "SF-2" for the evidence-typing or
comparator-identity gap, it means **SF-4** and **SF-5** as filed here; SF-1 and SF-2 in this
channel are `Input pedigree` and Level 0, and are cited under those numbers from
`docs/Encoding_Protocol_v0_1.md` Part C.

**The list is partial by construction.** It holds what has been explicitly filed, not a census of
every known gap. Two channel-eligible items from the same encoding are deliberately not entered
here: the version-agnostic `NASA-STD-7009` alias resolving to the 7009B identifier, and the two
import defects (template hint text surviving into data rows, import printing the declared profile
while writing the derived one). They are recorded in their own artifacts and are not filed here
because no directive has asked for them yet. Absence from this file is not evidence of absence.

---

## SF-1 — `Input pedigree` has no factor in the pack

**Finding.** A source can predeclare and achieve a credibility factor the pack has no field for.

**Cause.** Pack `nasa-7009b` carries no `Input pedigree` factor. The nearest name, `Model inputs`,
is a V&V 40 validation factor asking whether input data is accurate and well characterised — a
different question, on a different scale.

**Evidence.** `dev/build/pilot-johnson/AMBIGUITY_LOG.md`, entry A-07 (ESCALATION). The source
predeclares the factor at 3, achieves 3, and carries a rationale for it.

**Consequence.** The value is not carried. It is not forced into `Model inputs`, because a value
entered under a factor that asks a different question is worse than a value absent. The encoding
proceeds under the declination rule with the loss disclosed.

**Status.** Open. No pack change proposed here.

---

## SF-2 — Level 0 is inexpressible on 13 of 19 factors

**Finding.** The NASA-STD-7009 "level 0" convention — insufficient evidence to make a
determination — cannot be recorded on any V&V 40 factor.

**Cause.** Level 0 exists on the 6 NASA factors and on none of the 13 V&V 40 factors, whose scale
runs 1–5. There is no value in the pack meaning *not determinable* as distinct from *not assessed*.

**Evidence.** `dev/build/pilot-johnson/AMBIGUITY_LOG.md`, entry A-08 (ESCALATION), quoting the
source's own definition at p.7.

**Consequence.** Not blocking for the encoding that raised it, because that source uses no level 0
anywhere. Blocking for any 7009A assessment that does: it could not be encoded at all on the
affected factors, and the nearest available move — recording a 1 — asserts a determination the
source explicitly declines to make.

**Status.** Open. Filed before a real encoding hits it, which is why the encoding that raised it
was not blocked.

---

## SF-3 — `W-EP-02` cannot fire on an imported package, by construction

**Finding.** The broken-provenance pattern `W-EP-02` — a validation result with no generation
activity — can never fire on a package produced by `uofa import`. Its silence in a weakener report
carries no information about the source.

**Cause.** Importer auto-generation. `src/uofa_cli/excel_mapper.py:443` stamps a `wasGeneratedBy`
activity onto every validation result it writes, with an in-code comment stating that the stamp
exists so `W-EP-02` does not fire on every imported result. Every node the importer places under
`hasValidationResult` goes through that one mapper (`excel_mapper.py:296`), so the stamp is
unconditional. The rule's premise is `noValue(?result, prov:wasGeneratedBy)`
(`packs/core/rules/uofa_weakener.rules:63`), which the stamp makes unsatisfiable rather than
merely usually-false. The template carries no column for a generation activity, so an encoder can
neither supply a real one nor suppress the synthetic one.

**Evidence.** The silence table of the second done-test run —
`dev/build/encoding-prep/donetest/RESULTS.md`, run 2's third disposition table, patterns that did
not fire and why silence is not clearance. That table separates "correctly silent" from "silence
is the tool's, not the source's", and places `W-EP-02` in the second class.

**Prior partial record, and how this widens it.** `packs/model-credibility/README.md:197` already
lists `W-EP-02` under patterns suppressed by construction, with the parenthetical "generation
activity auto-stamped". It scopes the suppression to the **card level**, as a property of what a
model card lacks. The importer code shows the suppression is not card-specific: it applies to
every Excel-imported package on every pack, including full V&V assurance packages that carry the
structure the card was said to lack.

**Consequence.** A weakener report cannot distinguish a source with real generation provenance
from one with none. Any count of firings across imported packages excludes `W-EP-02` silently, and
a disposition pass that treats non-firing as clearance will read the auto-stamp as evidence.

**Status.** Open. **No rule edit; the catalog is frozen.** Recorded so the silence is documented
rather than inferred, and so a future catalog revision has the case already stated.

---

## SF-4 — non-comparison evidence has no predicate of its own

*Referred to as "SF-1" in `docs/Ruling_WAR05_Schema_Findings.md` and in the Johnson verdict
record. Filed here under the next number in order; see the labelling note above.*

**Finding.** Evidence that is not a comparison — a review activity, a process attestation, a
deployment record — rides the same predicate as validation results, so a pattern scoped to
comparisons tests node classes it was never about.

**Cause.** The ontology already types the node classes. The graph loses the distinction because
the Excel mapper funnels every evidence type through `hasValidationResult`. `W-AR-05` then tests
every node under that predicate for a comparator.

**Evidence.** Five `W-AR-05` firings on `dev/build/pilot-johnson/johnson-pilot.jsonld`, of which
three survive as dispositions D-03, D-04 and D-05, ruled **Not Applicable** by the author on
2026-08-21 (`dev/build/pilot-johnson/DISPOSITIONS_DRAFT.md`). Established by controlled
experiment: a `ProcessAttestation` added under the fourth-verb rule drew the firing immediately,
on a node whose whole purpose is to attest a process rather than compare against a referent.
`dev/build/pilot-johnson/AMBIGUITY_LOG.md`, entry A-28.

**Consequence.** The pattern reports an absence that could never be a presence for these node
classes. A disposition pass must rule three of five firings Not Applicable, and a reader counting
firings across packages counts the mis-scoping as weakness.

**Proposed shape, recorded as a proposal and not a design.** A predicate for non-comparison
evidence — `hasReviewEvidence`, or a general `hasSupportingEvidence`; the mapper routes by
evidence type; `W-AR-05` then scopes itself by walking only the validation predicate, with no
type guard required. Note the INV-21 lesson explicitly: if a type guard is ever considered
instead, the class it guards on must be declared in the ontology first.

**Status.** Open. **No rule edit; the catalog is frozen post-R1a.** The fix rides the schema
increment. Carries the boundary-section tag with SF-5: judgment-borne and prose-borne evidence is
where the schema stops.

---

## SF-5 — real comparators are not always URI-shaped

*Referred to as "SF-2" in `docs/Ruling_WAR05_Schema_Findings.md` and in the Johnson verdict
record. Filed here under the next number in order; see the labelling note above.*

**Finding.** A source can state a comparator that is not the kind of thing an identifier names,
and the package cannot carry it.

**Cause.** `comparedAgainst` is an `@type: @id` term, so prose values — "SME engineering
judgment", "RWS data (not available)" — are dropped at import as non-well-formed subjects.
`W-AR-05` then fires on an absence import itself created.

**Evidence.** `dev/build/pilot-johnson/AMBIGUITY_LOG.md`, entry A-21, and dispositions D-02 and
D-06, both ruled **Confirmed** by the author on 2026-08-21. The same `@type: @id` expansion
behaviour was established separately by the relative-IRI experiment recorded as A-26.

**Consequence.** The source stated a comparator and the package reports none. The firing is
correct about the artifact and wrong about the work, which is exactly the split the disposition
rules make the encoder carry in the ambiguity log.

**Proposed shape, again a proposal.** A comparator-description node, or a small controlled
vocabulary of referent classes — expert judgment, test data as referent, published benchmark,
predicate reference to a cited artifact.

**Status.** Open. Morrison and Nagaraja never surfaced this, because their comparators were bench
data with citable identities. Johnson surfaces it because judgment-borne referents are normal in
this document class.

---

## SF-6 — a context of use has no cell for its operating envelope

**Finding.** The workbook carries no cell for a COU applicability constraint or operating
envelope, so a source that states one repeatedly produces a package that states none.

**Cause.** `hasApplicabilityConstraint` and `hasOperatingEnvelope` exist on the context of use,
and the Excel on-ramp has no column feeding either. `W-ON-02` is Confirmed on any package built
through that on-ramp, whatever the source says.

**Evidence.** Disposition D-11, ruled **Confirmed** by the author on 2026-08-21, with the ruling
**no per-package repair**: the gap is a workbook/template finding and belongs to the schema
increment rather than to this encoding. The source states the envelope at p.18, at p.19 twice,
and at p.23. Cross-reference `packs/vv40/examples/morrison/cou1`, which fires the same pattern,
and the Ch4 spec's observation of it on 65 of 71 queue packages.

**Consequence.** The pattern cannot distinguish a source with no operating envelope from a source
with four statements of one. As with SF-4, a firing count treats a template gap as a package
weakness.

**Status.** Open. **Template change, not a rule edit.** Filed beside SF-4 and SF-5 for the same
schema increment, per the author's D-11 ruling.

**Sibling gap, same class, recorded here rather than filed separately.** A validation-result
firing dispositioned Confirmed *with an offset rationale* has no on-ramp route either:
`uofa:OffsetRationale` and `hasOffsetRationale` exist in the v0.5 context and
`packs/vv40/examples/nagaraja/cou1` carries one, but the mapper has no offset handling and the
template has no column — and Nagaraja's `refersToFactor` points at a factor, where D-06's firing
is on a validation result. Ruled 2026-08-21 the same way as the envelope gap: the disposition
record carries the rationale, the package is not hand-edited, and the missing route is a template
finding. Recorded in `dev/build/pilot-johnson/PROTOCOL_FINDINGS.md`, cross-cutting table. Promote
to **SF-7** if the increment wants it as its own entry.

---

## SF-7 — the placeholder check is blind at the row where placeholders survive

**Finding.** `--protocol-check` reports `no template placeholder text in data rows: clean` on a
workbook whose first data row contains the template's own hint text, and the leaked value reaches
the package as a node identifier.

**Cause.** Two independent gaps, one at each layer.

*Workbook side.* `protocol_check.check_workbook` scans from `head + data_offset`. For
`Validation Results` that is row 2 + 2 = row 4. The pack template reserves row 3 for hint text
and expects data from row 4, but the extractor writes its **first data row into row 3**. So the
one row where hint text most plausibly survives — the row a writer fills partially, since
`excel_writer` clears hints only in the columns the model wrote — is the one row the scan never
examines. The hint string is present in the check's own hint set; the row is populated with real
data; the check simply never looks at it. It does not report *skipped*. It reports **clean**.

*Package side.* Nothing refuses a node whose identifier is hint text. `excel_mapper` minted
`ValidationResult` nodes with `id` equal to the literal string `Stable URI or local ID` in two
separate packages, and both passed import, SHACL and the rule engine.

**Evidence.** `dev/build/encoding-prep/aero-cou1` and `aero-cou2`, both carrying that node id
before the 2026-08-21 cell walk blanked `Validation Results` C3; both ledgers record the
correction. The prep session's review packet reports protocol-check green on all applicable
checks, which it was.

**Consequence.** A check written specifically to catch Johnson finding F-3d passes on F-3d's own
case, and passes with an affirmative green rather than a skip. Any encoder trusting the check
would ship a package identified by template boilerplate. This is a **vacuous green with an
affirmative face** — the failure shape the instrument-lessons thread documents — occurring in the
tool that exists because of the previous instance.

**Proposed fix, at both layers.** Scan from `head + 1`, since a populated hint row is by
definition a leak. **And** have the importer, or protocol-check's package-side pass, refuse any
node whose id matches the hint set — the workbook-side scan can be correct and a future writer
bug could still mint one. Cheap second guard, same finding.

**How it was found, which is the part worth recording.** Not by a check passing or failing, and
not by the delta tables, which were green throughout. By a session reading a node name
skeptically while enumerating evidence types for an unrelated disposition question. The
human-in-the-loop slot earned itself again, and the thing it caught was the instrument.

**Status.** Open. Tooling fix, no rule or schema change. Both affected packages are corrected;
the check is not.

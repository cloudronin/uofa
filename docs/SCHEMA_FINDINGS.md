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

---

## SF-8 — no on-ramp package can bind the claim its evidence supports

**Finding.** `uofa:bindsClaim` — *"links the package to the proposition its evidence is offered
in support of"* — is unreachable through the Excel on-ramp. Every package built from a workbook
lacks it, and always will until the template can carry a claim.

**Cause.** The `Model & Data` sheet offers exactly three entity types: **Requirement, Model, or
Dataset**. There is no Claim. `excel_mapper.py` contains no occurrence of `bindsClaim` at all, so
no code path could emit one even if a row existed. The property is declared in the ontology
(`packs/core/shapes/uofa_shacl.ttl`, domain `UnitOfAssurance`, range `AssuranceClaim`) and in the
v0.5 context, but it carries no SHACL cardinality constraint — which is why packages missing it
pass C1, C2 and C3 cleanly and the absence is invisible to every gate.

**Evidence.** `studies/ch4_numbers/derive_h1_tier_table.py`, repointed at the two signed aero
encodings, reports `missing mandatory ['bindsClaim']` for both while every other check passes:

    NASA take-off  flat  Accepted      3  NO  pass  pass  pass
    NASA cruise    flat  Not accepted  4  NO  pass  pass  pass

`dev/build/pilot-johnson/johnson-pilot.jsonld` lacks it too. `packs/vv40/examples/morrison/*`
and `packs/vv40/examples/nagaraja/cou1` carry it, and both were hand-authored.

**The boundary arrived here by a fourth independent route, and that is the point of this
entry.** The schema audit found the empty claim interior — `AssuranceClaim` is one of INV-20's
four classes with zero populated properties, and INV-21 counted seven incompatible `bindsClaim`
conventions. The Stage 4 adjudication relocated all twelve REAL-GAP spot-check rows to the schema
boundary. The override analysis confirmed the relocation. Now the H1 **derivation script** — the
tier table itself, an instrument built for something else entirely — has measured the same
boundary from the tooling side: the assessment layer is carried, the assurance-case layer is not,
and no governed encoding can supply the proposition its evidence is offered for. Four routes,
four methods, one boundary.

**Consequence.** The H1 per-substrate table cannot reach five-of-five on completeness with
protocol-encoded packages. This is recorded in `studies/ch4_numbers/LEDGER.md` as measured rather
than resolved: the two NASA rows read `NO — blocked on SF-8` beside three passing gates.

**Explicitly not done: the ledger's definition of `complete` was not amended.** Changing
`MANDATORY` so the column measures what a package can currently carry would tune the gate to the
tooling — the retroactive-threshold move in a new costume — and it is rejected on the record. The
definition stands; the packages report against it truthfully.

**What this reframes.** The two packages produced under the governed pipeline are precisely the
ones that expose the claim gap, because hand-authoring had been silently supplying it. The
governed process did not fall short of the hand-crafted packages. It revealed what the
hand-crafting had been providing without anyone recording that it was needed.

**Status.** Open. Template change plus mapper support. No rule or schema change; the property
already exists and is already declared.


---

## SF-9 — a source written against 7009A can only be encoded against 7009B

**Filed by an encoding, through the channel, exactly as designed.** T-8 — an unsteered stranger
session with no access to this file or to any of the reasoning in it — met the gap, recorded a
`SCHEMA FINDING` entry in its own ambiguity log, and named it in its closing report. This is the
first entry the escalation route produced from outside the authoring context.

**Finding.** The only NASA pack `uofa` ships is `nasa-7009b`. A source document written entirely
against **NASA-STD-7009A** must therefore be encoded against a standard it never mentions, and
five of the pack's nineteen factors have no counterpart term in such a source at all — they can
be filled only by inferring that a differently-named concept is the same concept.

**Cause.** Pack identity is versionless at the point where it matters. `packs/` carries
`nasa-7009b` and no `nasa-7009a`, and nothing in the import path asks whether the pack's standard
is the standard the source was written to. The mismatch is invisible to every gate: A-5 wants an
anchor, A-6 wants a review, A-7 wants required and achieved separately — none of them asks
*which standard the anchored passage is written against*, so a factor matched across a version
boundary anchors and confirms exactly like one matched by name.

**Evidence.** `NTRS-20200002832-Johnson-2020.pdf`, the source T-8 encoded, measured directly:

    7009A          50 occurrences
    7009B           0 occurrences
    bare "7009"     2 occurrences

The abstract's first sentence is "NASA-STD-7009A, Standard for Models and Simulations, contains a
worthy and insightfully-crafted credibility assessment…", and the paper defines its own shorthand:
"NASA-STD-7009A Standard for Models and Simulations (to be called here the Standard or 7009A)".

T-8's signed, verifying package — `~/stranger-runs/T-8/downloads/credenza-your-evidence-signed.zip`,
whose measurement and decision signatures both check against the anchors it ships — carries
`pack: NASA-STD-7009B` over that source, with every gate reading pass.

**Consequence.** An encoding of a 7009A source is silently a cross-version mapping, and the
package says nothing about it. The five unmatched factors are the visible part; the invisible part
is that *every* matched factor is matched by inferred meaning rather than by name, and a reader of
the package cannot tell which ones. Nothing is blocked — T-8 completed and signed — which is the
problem: the artifact makes a versioned claim its source does not support, and it makes it
cleanly.

**Not the same as SF-5 or SF-6.** Those are gaps in what a cell can express. This is a gap in what
the *pack selection* records: the encoding is well-formed and the standard it names is the wrong
one. The nearest neighbour is the version-agnostic `NASA-STD-7009` alias noted as
deliberately-unfiled in this file's preamble; that alias resolving to the 7009B identifier is the
same boundary approached from the identifier side, and it should now be read alongside this entry.

**Status.** Open. Filing is not a proposal to add a `nasa-7009a` pack; the minimum an author might
act on is that a package record the standard its **source** declares beside the standard its
**pack** asserts, so a cross-version encoding is legible as one. No rule or schema change is
proposed here.

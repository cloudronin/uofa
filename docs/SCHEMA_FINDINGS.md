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

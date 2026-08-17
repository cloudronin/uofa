# M5 re-analysis at v0.5.15.1 — scope declared before the number exists

**Date:** 2026-08-17
**Status:** DECLARED, NOT YET MEASURED
**Consumed by:** the Phase 2.5a report, A4, and any manuscript sentence quoting an
M5 recall figure

This file is committed **alone and before** `run_arm_m5.py` is executed. Its whole
purpose is that the interpretation of the number is fixed while the number is still
unknown. Writing it afterwards would be the retroactive framing that GATE-H2's own
rationale condemns, and the same defect as retroactive thresholding arriving by a
different door.

## What is about to be measured

The M5 corpus (`dev/build/adversarial/phase2/2026-04-26`, 381 specs, ~4,601
packages) re-classified at catalog **v0.5.15.1**. No regeneration: adversarial
packages are catalog-version-independent, so this is a re-run of the rule engine
over committed packages at **zero LLM spend**. The `$386 / 14h` figure in
`PHASE2_STATUS_REPORT.md:55` is for regenerating the corpus and does not apply.

## The four things this figure is, declared now

1. **It is a training-corpus measurement.** M5 is the corpus Phase 2.5's refinement
   loop tuned against. Recall measured on it at v0.5.15.1 is therefore optimistic in
   a way the v0.5.13 holdout figure is not, and every quotation of it must say so.
   The holdout figure (**287/378 = 75.9%**, `studies/phase2_5a/REPORT.md`) remains
   the one to cite when an unbiased estimate is wanted.

2. **It is reported for like-for-like continuity, not as a replacement.** The
   manuscript carries **73.4%** for M5 at v0.5.7. The value of re-running the same
   corpus at v0.5.15.1 is that it isolates the catalog delta with the corpus held
   fixed. That comparison is its only purpose.

3. **It carries the evaluable-rows convention**, matching the manuscript's own
   "73.4% (evaluable rows)". GEN-INVALID packages are excluded from the denominator,
   determined by measured SHACL conformance rather than by file existence. Two
   denominators are already in circulation for the holdout — 288/420 = 68.6% and
   288/378 = 76.2%, the same measurement — so the convention is named wherever the
   number appears.

4. **It does not decide re-baselining.** P2-A (`PHASE2_STATUS_REPORT.md:54`) —
   whether to re-baseline Phase 2 on the v0.5.15.1 catalog — **remains an open,
   separate, authored decision**, whichever way this number lands. A measurement is
   not a ruling. This file exists so that producing the figure cannot be read as
   having settled the question by fait accompli.

## Why take a measurement that decides nothing

Because declining a free measurement of one's own training corpus is a question at
the defense with no good answer. Taken with its scope pre-declared, it is simply the
record being complete.

## What would make this pre-declaration have failed

If the paragraph above needs amending once the number is known, that is a finding
about this file and gets recorded as one, not edited away.

---

# RESULT (appended 2026-08-17, after the run)

## Against the pre-declaration

**CE recall @ v0.5.15.1 = 2769/3626 = 76.4%** (evaluable rows), against the
manuscript's **73.4%** for the same corpus at v0.5.7. A **+3.0 point** catalog
delta with the corpus held fixed, which is exactly the comparison declared above
and its only purpose.

The four declared qualifications hold unchanged. It is a training-corpus figure and
therefore optimistic; the holdout's **75.9%** remains the number to cite for an
unbiased estimate; it uses evaluable rows (380 GEN-INVALID excluded on measured
conformance); and **P2-A remains open**. Nothing in this paragraph needed amending
once the number was known.

## An unanticipated second measurement, reported as a finding

The run also produced an M5 **negative-control** figure, which the pre-declaration
did not anticipate and therefore did not scope. It is reported here rather than
quietly dropped.

**NC clean rate on M5 at v0.5.15.1 = 8/176 = 4.5%**, against the headline
**97.1%** at the same catalog version.

The two figures use different NC corpora, and the corpora differ on precisely the
field the dominant rule reads:

| NC corpus | COU has envelope or constraint | COU has neither |
|---|---|---|
| M5 (2026-04-26) | 18 | **161** |
| v0.5.15.1 holdout (behind the 97.1%) | **176** | 0 |

W-ON-02 fires on **158 of 176** evaluable M5 NCs and is the single largest
contributor to the 4.5%.

This is the code-side mechanism recorded at INV-1 §3 row 8, now measured from the
corpus side. `adversarial/skeleton.py:70-95` inserts placeholder
`ApplicabilityConstraint` and `OperatingEnvelope` stubs into regenerated NC
packages, documented in the source as *"structurally well-formed, not substantively
meaningful"* and *"inserted to satisfy the noValue check on
uofa:hasApplicabilityConstraint in the W-ON-02 rule predicate."*

### Two readings, both defensible, not adjudicated here

**Corpus correction.** A genuinely clean package *should* bound its Context of Use.
An NC lacking an envelope is not clean — it carries a real defect that W-ON-02
correctly detects — so adding the field fixes the corpus rather than the rule. On
this reading the 97.1% is honest and the M5 figure measures a defective NC corpus.

**Rule suppression.** The inserted value is a placeholder the source itself calls
not substantively meaningful. On this reading the package is clean only in that the
rule can no longer see the absence, and part of the 0% → 97.1% trajectory is corpus
change rather than rule tightening.

The distinction matters because the 97.1% is a headline specificity claim and feeds
GATE-H3's FP clause. **Author call.** What can be said without ruling: the
trajectory should state which portion of the gain came from rule refinement and
which from NC regeneration, because both happened and the current framing attributes
all of it to the first.

### Measurement note

One package of 4,601 raised `decimal.InvalidOperation` during literal parsing and
was caught by the runner's handler, counting it GEN-INVALID. So 1 of the 380
GEN-INVALID rows is a reader exception rather than a generation failure. Immaterial
to the rates; recorded for accuracy.

---

# ADJUDICATION — 2026-08-17, author ruling

The two readings above were left open for the author. Ruled, and recorded here
rather than by editing the section that posed them, so the sequence stays legible:
the readings were framed before the ruling existed.

## The framing error was mine: these are not false positives

Ask what the rule is for. **W-ON-02 exists to flag a Context of Use with no stated
applicability bounds.** The M5 negative controls *genuinely lack* those bounds.
Nobody injected that absence — it is simply true of them.

So the rule firing on 158 of them is not a rule misfiring on clean packages. It is
the rule **correctly detecting a real, uninjected weakness** in packages that were
labelled "negative" only in the sense that no defect was *deliberately planted*.
Counting those firings as false positives assumes the label means "contains no
weakness," when what it means is "contains no weakness we put there."

**Independently supported by the week's own record:** the same rule fires on all
three published case-study encodings. Unbounded contexts of use are endemic in real
evidence. The rule keeps saying so, everywhere it looks, and it is right every time.

## Both figures are legitimate; they measure different things

**The 97.1% stands as the specificity figure, scoped.** It is measured on negative
controls *constructed to carry no catalog-detectable weakness*, bounded contexts of
use included. That construction is not cheating: **a true negative for a
presence-checking rule must actually have the thing present.** A control that omits
the field is not a clean package, it is a package with that defect. The scope rides
with the number **everywhere it appears, including GATE-H3's false-positive clause**.

**The M5 figure is a detection result, and gets reported as one.** On packages never
built to be complete, the dominant rule detects genuine incompleteness at scale —
158 of 176. It is a detection result wearing a specificity costume, and calling it
4.5% specificity mislabels it. Reported as detection, it **supports** the catalog
rather than indicting it.

Neither reading in the section above survives intact. "Corpus correction" is right
that the regenerated corpus is the valid specificity instrument, but wrong to treat
the M5 firings as measuring a defective corpus — they measure real absences. "Rule
suppression" is right that the trajectory conflates two causes, but wrong to imply
the rule was blinded — it was pointed at a corpus where the thing it checks for is
present.

## The trajectory gets decomposed

Session 1's proposal is adopted. The 0% → 97.1% story currently attributes
everything to rule refinement when part of it is corpus redefinition. **Both
components get stated.** The split is measurable from the committed corpora, and it
is the same argued-versus-measured discipline the whole phase ran on.

Measured at [INV-16](../../docs/investigations/INV-16-nc-trajectory-decomposition.md):
rule refinement accounts for **4.5 points** with the corpus held fixed; the
remainder travels with the corpus; **both were necessary and neither alone exceeds
4.5%**. Every rule the 2026-04 record labels a predicate fix went to zero; every
rule it labels corpus regen is unchanged to the decimal.

## The placeholder problem becomes a named limitation

This is the deeper finding, and it is kept as one rather than resolved away. The
regenerated controls satisfy the rule with stubs the source code itself calls **not
substantively meaningful**. A presence-checking rule cannot tell a real applicability
envelope from an empty one.

That is the [W-AR-05 case](../../docs/investigations/INV-15-m5-scale-and-phase3-gap-probes.md)
from the opposite direction: there, real evidence was invisible because it was not
structural; here, fake structure is visible and passes. **Structural capture is
necessary but not sufficient.** Substantive sufficiency checking is future work, and
the MECHANICAL/JUDGMENT partition already has the vocabulary for the distinction.

Two independent examples of one limitation, both from committed records, is a
limitations section that writes itself — and it strengthens the praxis by bounding
it precisely rather than leaving the boundary to be found by a reviewer.

## Status of the pre-declaration

**Unamended.** All four qualifications held once the number was known, which is a
pre-declaration working rather than a pre-declaration being lenient. The 76.4%
continuity figure lands as declared. **P2-A remains open** — this ruling adjudicates
the NC reading, not the re-baselining decision.

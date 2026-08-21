# Dispositions — ADJUDICATED by the author, 2026-08-21

**ADJUDICATED.** Every row below carries the author's verdict, ruled item by item in the
governed review session of 2026-08-21 and recorded in
`Johnson_Author_Verdict_Record.md`. That record is the authority; this file is its
application. The verdict vocabulary is Encoding Protocol v0.1 Part B —
**Confirmed / Overruled / Not Applicable** — which replaces the draft's
Accepted / Not Applicable wording. The change is vocabulary, not verdict: every row the
draft read Accepted the author ruled Confirmed, on the same rule as applied.

Governing protocol: `docs/Encoding_Protocol_v0_1.md` (v0.1, committed). The package was
signed by the author on 2026-08-21, re-imported the same day to correct its operator
attribution, and **re-signed**; `uofa check` returns C1 ✓ C2 ✓ C3 ✓. The verdicts below are
unaffected — the re-import changed five provenance and signature fields and no content, and
`uofa rules` reports the same eleven firings. `RUN_LOG.md` records all three acts.

Divergences between the verdict record and the artifacts are listed in
`APPLY_RECORD_ESCALATIONS.md` and were **not** silently reconciled here.

Refreshed against `johnson-pilot.jsonld` at `base_uri https://github.com/cloudronin/uofa`,
after the §3c additions. `uofa rules` reports **11 weakeners across 5 patterns** (10 High,
1 Medium); the previous pass reported 12. Full output in `rules-report.txt`.

Two changes from the pilot's table, both from the draft protocol rather than from me.

**§4a-0 rules that dispositions adjudicate against the package.** The pilot's three
JUDGMENT-CLASS rows were awaiting exactly that ruling and are now determinate. Where the
source holds evidence the package does not carry, the delta moves to the ambiguity log
instead of softening the verdict.

**§3c makes adding an evidence row a review act**, which closed A-24. One row was added and
one firing cleared.

## What the §3c additions actually did, measured

W-NASA-03 is gone. It required `uofa:hasEvidence` **on the factor**, not merely a
`ProcessAttestation` node existing, so clearing it took both the added row and a Linked
Evidence reference pointing at it.

The comparator repair worked and the count hid it. Repointing the output-comparison row's
Compares To at the dataset entity cleared its W-AR-05 firing, and the newly added
ProcessAttestation drew one in its place, so five became five. Confirmed by comparing the
affected-node lists rather than the totals.

Both repairs needed an **absolute** IRI. `comparedAgainst` and `hasEvidence` are
`@type: @id` terms in the v0.5 context, so a relative value is dropped at JSON-LD expansion
and the reference never reaches the graph, silently. The encoder therefore cannot author a
cross-reference without first fixing the minting namespace, and the namespace is an author
decision that is only frozen at signing. `review_pass.py` carries it as a single constant
for that reason. Recorded as ambiguity A-26.

## Dispositions against the eleven firings

Verdict and Class are the author's, from the verdict record's dispositions table. Node and
Rule as applied carry forward from the draft, which the author reviewed rather than
re-derived. Class is a property of the pattern under Part B and is not the encoder's to
reassign.

| # | Pattern | Node | Verdict | Class | Rule as applied | Author note |
|---|---|---|---|---|---|---|
| D-01 | W-AL-02 [Med] | the COU | **Confirmed** | mechanical | Confirmed because the package carries no `SensitivityAnalysis`, which is what the pattern tests. | The delta — source sensitivities at p.22 and a factor rated on them at p.25, against a package carrying neither — stays in the ambiguity log and does not soften the verdict. The missing-node route is schema-finding material; the on-ramp has no route to the node at all |
| D-02 | W-AR-05 | `independent-duplicate-regression-analysis` | **Confirmed** | mechanical | Confirmed because the package carries no `comparedAgainst` on this result. | Source names the comparator at p.18 — a competing software package, not an entity this package holds. Cited as the SF-2 instance |
| D-03 | W-AR-05 | `conceptual-validation-via-smeteam-review` | **Not Applicable** | scoping ruling | The pattern's precondition is not meaningful for this node class. A `ReviewActivity` has no comparator by definition. | SF-1. See the mis-scoping note below |
| D-04 | W-AR-05 | `independent-technical-review-of-model-and-analysis` | **Not Applicable** | scoping ruling | As D-03. | As D-03 |
| D-05 | W-AR-05 | `process-attestation-doe` | **Not Applicable** | scoping ruling | As D-03, for a `ProcessAttestation`. | The §3c-added row. The immediate firing on it is the SF-1 controlled experiment, and the experiment is now verdict-backed rather than session-asserted |
| D-06 | W-AR-05 | `waived-validation-against-real-world-system-data` | **Confirmed, with offsetRationale** | worked example | Confirmed because the source states at p.19 that no comparator data exists and the package correctly carries none. | **offsetRationale, anchored p.19:** no RWS data exists; test data served as the referent; the conservative tolerance bound and the PRA context bound the model's use. **Designated the v0.2 worked example.** **RULED on the E-3 escalation: disposition record only, no package node.** This adjudicated record is the governed artifact and the offsetRationale lives here. Minting a `hasOffsetRationale` node through a route the on-ramp does not have would be a hand-crafted graph edit of the class the fixtures finding warned about, and D-11's sibling rule — no per-package repair where the template lacks the route — applies squarely. The missing route is filed as a template finding |
| D-07 | W-CON-01 | `Numerical code verification` | **Confirmed** | JUDGMENT, author act | Confirmed because the package declares outcome Accepted while this factor is assessed and carries no level. | The package-level inconsistency is real. It is the price of decline-don't-invent, and the author's ruling is that the price is displayed rather than suppressed. Would not have fired on the raw extraction |
| D-08 | W-CON-01 | `Model form` | **Confirmed** | JUDGMENT, author act | As D-07. | As D-07 |
| D-09 | W-CON-01 | `Output comparison` | **Confirmed** | JUDGMENT, author act | As D-07. | As D-07 |
| D-10 | W-NASA-06 | `Results robustness` | **Confirmed** | mechanical | Confirmed because the factor is assessed with no linked `SensitivityAnalysis`. | Same missing-root as D-01, and not repairable through the on-ramp — unlike W-NASA-03, which the §3c row cleared |
| D-11 | W-ON-02 | the COU | **Confirmed** | mechanical | Confirmed because the COU carries neither an applicability constraint nor an operating envelope. | **RULED: no per-package repair.** The operating-envelope gap is a workbook/template finding, filed with SF-1/SF-2 for the schema increment. The source states the envelope at p.18, p.19 ×2, and p.23; the workbook holds none of them. Morrison COU1 fires it too |

### The mis-scoping finding, established by controlled experiment

D-03 through D-05 are Not Applicable rather than Confirmed because W-AR-05 tests every node
under `hasValidationResult`, and the mapper routes all five evidence types through that
predicate. A `ReviewActivity`, a `ProcessAttestation`, and a `DeploymentRecord` have no
comparator by nature, so the pattern reports an absence that could never be a presence.

Three of the five current firings are this. The experiment that established it: adding a
`ProcessAttestation` under §3c produced a W-AR-05 firing on it immediately, on a node whose
whole purpose is to attest a process rather than compare against a referent.

This also answers a worry the protocol draft raises about itself. Adjudicating against the
package looked as though it would make every mechanical firing Confirmed and drain the
verdict of information. It does not. Not Applicable does real work here, and the work it
does is to separate a pattern that is wrong about this node from a pattern that is right.

## Silence sweep, per §4e

**CONFIRMED by the author, 2026-08-21, as tabled.** The fifteen candidate dispositions
below stand as written: nine Declined-mapping, two Not Applicable (Discretization error;
Numerical solver error), one Source-absent level (Development technical review — the
content at p.10 and p.24 is not a level), five needing no disposition (the confirmed level
rows), and two ESCALATIONS acknowledged as the record with no disposition possible
(Model inputs and Input pedigree, A-07, the pack-has-no-home case, INV-20 channel).

The disposition pass covers every factor the pack expects, not every firing the engine
raised. Four factors drew a firing. **Fifteen drew nothing**, and they are where the
encoding's real gaps are.

| Factor | Levels | Status | Candidate disposition |
|---|---|---|---|
| Software quality assurance | none | not-assessed | **Declined mapping.** 7009A assesses no separate SQA factor; analysis-code verification was waived at p.6 |
| Numerical code verification | none | assessed | Evidence at p.18; level declined per the scale boundary. Drew D-07 |
| Discretization error | none | not-applicable | **Not Applicable.** A regression on test data has no discretization scheme |
| Numerical solver error | none | scoped-out | **Not Applicable.** Source answers solution verification "No. Not required" at p.18 |
| Use error | none | not-assessed | **Declined mapping.** Independent inspection is real evidence; 7009A rates no use-error factor |
| Model form | none | assessed | Evidence at p.17; level declined. Drew D-08 |
| Model inputs | none | not-assessed | **ESCALATION.** This is where 7009A's Input pedigree would go and it is a different question. A-07 |
| Test samples | none | not-assessed | **Declined mapping.** 18 planned and 15 completed is stated; no comparator-sample factor exists in 7009A |
| Test conditions | none | not-assessed | **Declined mapping.** |
| Equivalency of input parameters | none | not-assessed | **Declined mapping.** |
| Output comparison | none | assessed | Evidence at p.19; level declined. Drew D-09. Note 7009A rates Validation 1 where the extractor had put 4 |
| Relevance of the quantities of interest | none | not-assessed | **Declined mapping.** |
| Relevance of the validation activities to the COU | none | not-assessed | **Declined mapping.** The extractor put 1/1 here, the right story on the wrong factor |
| Development technical review | none | not-assessed | **Source-absent level.** Review content is abundant at p.10 and p.24; 7009A rates no such factor. Content is not a level |
| Data pedigree | 3 / 3 | assessed | **No disposition needed.** Both levels confirmed against Table 3 and p.25 |
| Development process and product management | 2 / 4 | assessed | **No disposition needed.** The two-level exceedance the extractor had erased |
| Results uncertainty | 4 / 4 | assessed | **No disposition needed.** |
| Results robustness | 4 / 4 | assessed | Levels confirmed. Drew D-10 |
| Use history | 3 / 3 | assessed | **No disposition needed.** |
| *Input pedigree* | — | — | **ESCALATION, no disposition possible.** Predeclared 3 and achieved 3 at p.25; the pack has no such factor. A-07, INV-20 |

## Summary

| Class | Firings | Factors |
|---|---|---|
| Confirmed | 8 | — |
| Not Applicable | 3 | 2 |
| Declined mapping | — | 9 |
| Source-absent level | — | 1 |
| No disposition needed | — | 5 |
| ESCALATION, none possible | — | 2 |

Of eleven firings, one (D-06) describes a limitation of the underlying assessment, three
(D-07 to D-09) exist because the encoding refused to invent levels, three (D-03 to D-05)
are a pattern mis-scoped for the node class, and four are things the workbook cannot carry.

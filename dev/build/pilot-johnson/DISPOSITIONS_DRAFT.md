# Candidate dispositions — DRAFT, refreshed under the protocol draft

**AWAITING-AUTHOR. Every row is DRAFT and nothing here is adjudicated.** The author's
verdicts are the governed act; this session prepares candidates.

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

| # | Pattern | Node | Verdict | Rule as applied | Note |
|---|---|---|---|---|---|
| D-01 | W-AL-02 [Med] | the COU | **Accepted** | Accepted because the package carries no `SensitivityAnalysis`, which is what the pattern tests. | The source documents sensitivities at p.22 and rates a factor on them at p.25. That delta is ambiguity-log material, not a softer verdict. The on-ramp has no route to the node at all |
| D-02 | W-AR-05 | `independent-duplicate-regression-analysis` | **Accepted** | Accepted because the package carries no `comparedAgainst` on this result. | Source names the comparator at p.18. It is a competing software package, not an entity this package holds |
| D-03 | W-AR-05 | `conceptual-validation-via-sme-team-review` | **Not Applicable** | The pattern's precondition is not meaningful for this node class. A `ReviewActivity` has no comparator by definition. | See the mis-scoping note below |
| D-04 | W-AR-05 | `independent-technical-review-of-model-and-analysis` | **Not Applicable** | As D-03. | |
| D-05 | W-AR-05 | `process-attestation-doe` | **Not Applicable** | As D-03, for a `ProcessAttestation`. | This node was added by this session under §3c, and drew the firing immediately |
| D-06 | W-AR-05 | `waived-validation-against-real-world-system-data` | **ACCEPTED** | Accepted because the source states at p.19 that no comparator data exists and the package correctly carries none. | The one firing that reads correctly whether adjudicated against source or package. The paper's own most conservative disclosure, restated by the engine |
| D-07 | W-CON-01 | `Numerical code verification` | **Accepted**, JUDGMENT class | Accepted because the package declares outcome Accepted while this factor is assessed and carries no level. | JUDGMENT per the A1 partition. Exists because the encoding refused to invent a level across the 0-4 to 1-5 boundary, not despite it. Would not have fired on the raw extraction |
| D-08 | W-CON-01 | `Model form` | **Accepted**, JUDGMENT class | As D-07. | |
| D-09 | W-CON-01 | `Output comparison` | **Accepted**, JUDGMENT class | As D-07. | |
| D-10 | W-NASA-06 | `Results robustness` | **Accepted** | Accepted because the factor is assessed with no linked `SensitivityAnalysis`. | Same root as D-01 and not repairable through the on-ramp, unlike W-NASA-03 which the §3c row cleared |
| D-11 | W-ON-02 | the COU | **Accepted** | Accepted because the COU carries neither an applicability constraint nor an operating envelope. | Source states the envelope four ways (p.18, p.19 twice, p.23) and the workbook holds none of them. Known observation across the queue; Morrison COU1 fires it too |

### The mis-scoping finding, established by controlled experiment

D-03 through D-05 are Not Applicable rather than Accepted because W-AR-05 tests every node
under `hasValidationResult`, and the mapper routes all five evidence types through that
predicate. A `ReviewActivity`, a `ProcessAttestation`, and a `DeploymentRecord` have no
comparator by nature, so the pattern reports an absence that could never be a presence.

Three of the five current firings are this. The experiment that established it: adding a
`ProcessAttestation` under §3c produced a W-AR-05 firing on it immediately, on a node whose
whole purpose is to attest a process rather than compare against a referent.

This also answers a worry the protocol draft raises about itself. Adjudicating against the
package looked as though it would make every mechanical firing Accepted and drain the
verdict of information. It does not. Not Applicable does real work here, and the work it
does is to separate a pattern that is wrong about this node from a pattern that is right.

## Silence sweep, per §4e

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
| Accepted | 8 | — |
| Not Applicable | 3 | 2 |
| Declined mapping | — | 9 |
| Source-absent level | — | 1 |
| No disposition needed | — | 5 |
| ESCALATION, none possible | — | 2 |

Of eleven firings, one (D-06) describes a limitation of the underlying assessment, three
(D-07 to D-09) exist because the encoding refused to invent levels, three (D-03 to D-05)
are a pattern mis-scoped for the node class, and four are things the workbook cannot carry.

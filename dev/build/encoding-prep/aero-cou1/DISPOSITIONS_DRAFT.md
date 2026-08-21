# Candidate dispositions — aero COU1

**ADJUDICATED by the author, 2026-08-21.** Every verdict below carries the author's ruling.
The drafting was mechanical under
`docs/Encoding_Protocol_v0_1.md` Part B plus the author's Johnson rulings, which transfer as
precedent. All five questions the draft raised were ruled by the author on 2026-08-21; no AUTHOR-RULE
rows remain. The rulings are recorded in `AUTHOR_SUMMARY_COU1.md` §4.

Package `aero-cou1.jsonld`, re-imported after the cell walk. `uofa rules` reports
**21 weakeners across 9 patterns** (8 Critical, 11 High, 2 Medium). The count rose from 20
because clearing the template placeholder from `Validation Results` C3 gave the MMS node a
well-formed identifier, so `W-AR-05` can now reach it; the fifth firing is a pre-existing
condition the placeholder had been hiding.

Verdict vocabulary is Part B's: **Confirmed / Overruled / Not Applicable**.

## Dispositions

| # | Pattern | Node | Verdict | Class | Rule as applied | Precedent |
|---|---|---|---|---|---|---|
| A1-01 | W-AR-05 [High] | `mms-code-verification-cht-coupling` | **Confirmed** | mechanical | Confirmed because the package carries no resolvable `comparedAgainst`. The source names the comparator — "Analytical manufactured solutions" — and `comparedAgainst` is `@type: @id`, so import drops it as a non-well-formed subject. | Johnson D-02; SF-5 |
| A1-02 | W-AR-05 [High] | `mid-span-grid-convergence-study` | **Confirmed** | mechanical | As A1-01. Comparator "GCI / Richardson-extrapolation across mesh levels" dropped at expansion. | Johnson D-02; SF-5 |
| A1-03 | W-AR-05 [High] | `cascade-rig-output-comparison` | **Confirmed** | mechanical | As A1-01. Comparator "Cascade rig 48-point thermocouple rake and thermal paint data" dropped at expansion. | Johnson D-02; SF-5 |
| A1-04 | W-AR-05 [High] | `sensitivityrobustness-study` | **Confirmed** | mechanical | As A1-01. Comparator "Baseline nominal Run #47 conditions" dropped at expansion. | Johnson D-02; SF-5 |
| A1-05 | W-AR-05 [High] | `monte-carlo-uq-on-cascade-comparison` | **Confirmed**, *stated-absence form* | mechanical | **Not an SF-5 instance.** `comparedAgainst` is `"N/A"`, which is the source asserting that no comparator exists rather than a real comparator lost at expansion. Narrative §5.4: UQ "was completed for the cascade comparison as part of validation analysis" but "the engine-COU probabilistic analysis has not been executed"; the workbook records Pass/Fail "Inconclusive". The run is uncertainty *propagation*, not a comparison against a referent, so the package correctly carries no comparator and the firing is true of it. | Johnson **D-06** (stated absence, carried), not D-02 |
| A1-06 | W-AL-02 [Medium] | the COU | **Confirmed** | mechanical | Confirmed because the package carries no `SensitivityAnalysis` node. The source has the work — `sensitivity_study_turbulence_intensity.csv`, 4 parameter classes — and the on-ramp has no route to the node. | Johnson D-01 |
| A1-07 | W-NASA-06 [High] | Results robustness | **Confirmed** | mechanical | Same missing root as A1-06: the factor is assessed with no linked `SensitivityAnalysis`. | Johnson D-10 |
| A1-08 | W-NASA-03 [High] | (factor, unnamed in report) | **Confirmed** | mechanical | Confirmed because the asserted factor carries no `uofa:hasEvidence` link. Johnson cleared its instance by adding a `ProcessAttestation` row under the fourth verb; here no source-supported row clears it, so the fourth verb does not apply. | Part B, pack-specific → consistency family |
| A1-09 | W-ON-02 [High] | the COU | **Confirmed** | mechanical | Confirmed because the COU carries neither an applicability constraint nor an operating envelope. **No per-package repair**; filed as the template finding. The source states the envelope repeatedly (`cou_definition.docx`; narrative §4.2 "NOT acceptable extrapolation for cruise, off-design, or tip-focused predictions"). | Johnson **D-11**; SF-6 |
| A1-10 | W-CON-04 [Medium] | the COU | **Confirmed** | mechanical | Confirmed because the package does not carry the referenced element. Same class as Morrison, which fires it hand-authored. | Part B, consistency structural |
| A1-11 | W-NASA-02 [High] | (unnamed) | **Confirmed** | mechanical | Confirmed on the pack-specific rule taking its core family's verdict rule; the named element is absent from the package. | Part B, pack-specific row |
| A1-12 | W-AR-02 [Critical] ×2 | (unnamed) | **Confirmed** | judgment, author act | **RULED 2026-08-21.** Confirmed on Part B's own W-AR-02 clause: *"an acceptance standing above a recorded shortfall."* The decision is Accepted while Discretization error (3/1) and Relevance of validation activities (3/2) carry achieved below required, so the firing stands on the package as it is. **The decision also stands** — see A1-16 | Part B, argumentation-reasoning |
| A1-16 | *(the decision itself)* | `Accepted (with conditions)` | **Stands as carried** | author ruling | **RULED 2026-08-21.** The source's own board accepted at MRL 3 for a concept-stage screening use, with the gaps named and conditions attached (probabilistic UQ, ground test before the next rung). The package carries those gaps loudly: the discretization shortfall, the film-cooling declination (G-06), and the un-executed engine-COU analysis. **An accepted decision *over* displayed weaknesses is what the framework is for.** The weakeners are Confirmed, the decision is the source's, and the two coexist on the record | author ruling; pairs with COU2 |
| A1-13 | W-EP-04 [High] | (unnamed) | **Confirmed** | judgment, author act | **RULED 2026-08-21**, under the shared W-EP-04 rule applied to both aero packages. Results uncertainty is `not-assessed` at MRL 3, and §5.4 states probabilistic UQ is required there — so as a package fact the unassessed factor at elevated risk does undermine the claim. **The disposition notes that the decision already prices it:** the conditions attached to the acceptance exist because of these gaps | Part B, epistemic risk-conditioned; pairs with COU2 A2-12 |
| A1-14 | COMPOUND-01 [Critical] ×6 | the COU | **Confirmed** (cascading) | excluded | Part B: compounds "are not dispositioned individually. They report coexistence of firings already dispositioned above." Bases A1-12 and A1-13 are now Confirmed, so the cascade resolves Confirmed. | Part B, compound row |
| A1-15 | COMPOUND-03 [High] ×1 | the COU | **Confirmed** (cascading) | excluded | As A1-14. | Part B, compound row |

**W-CON-01 does not fire on this package**, as the work order anticipated. These bundles were
authored against the pack, so no scale boundary exists and the Johnson D-07..09 precedent has
nothing to transfer to. That escalation path is retired rather than unused.

## Silence sweep, per §4e

Nineteen expected factors; **all nineteen are `assessed` except Results uncertainty**, so the
silence class that dominated Johnson barely arises here.

| Factor | Req / Ach | Status | Disposition |
|---|---|---|---|
| Software quality assurance | 2 / 2 | assessed | No disposition needed. Confirmed by pre-registration |
| Numerical code verification | 3 / 3 | assessed | No disposition needed |
| Discretization error | 3 / 1 | assessed | No disposition needed as a factor; the shortfall is the source's own disclosed gap (tip region), and it is a base of A1-12 |
| Numerical solver error | 1 / 1 | assessed | No disposition needed. **GT-DEFECT recorded**: the pre-registered expectation asserted required 2 against a source that states no required level. Workbook stands. See G-07 |
| Use error | 2 / 2 | assessed | No disposition needed |
| Model form | 3 / 3 | assessed | No disposition needed |
| Model inputs | 3 / 3 | assessed | No disposition needed |
| Test samples | 2 / 2 | assessed | No disposition needed |
| Test conditions | 3 / 3 | assessed | No disposition needed |
| Equivalency of input parameters | 2 / 2 | assessed | No disposition needed |
| Output comparison | 3 / 3 | assessed | No disposition needed |
| Relevance of the quantities of interest | 2 / 2 | assessed | No disposition needed |
| Relevance of the validation activities to the COU | 3 / **2** | assessed | **Corrected in the walk** from achieved 1. Shortfall is real and is a base of A1-12. The evicted film-cooling gap is G-06 |
| Data pedigree | 3 / 3 | assessed | No disposition needed |
| Development technical review | 3 / 3 | assessed | No disposition needed |
| Development process and product management | 2 / 2 | assessed | No disposition needed |
| Results uncertainty | 3 / — | **not-assessed** | **The one silence that matters.** Source §5.4 states engine-COU probabilistic UQ "has NOT been performed" and that it is required at MRL 3. Drives A1-13 |
| Results robustness | 2 / 2 | assessed | No disposition needed. Drew A1-07 |
| Use history | 2 / 2 | assessed | No disposition needed |
| *Film Cooling Validation* (narrative §4.3) | 3 / 1 | source-stated | **No pack factor exists.** Declination recorded on row 17's rationale and logged as G-06; filed as a schema finding. Johnson A-07 class |

## Summary

| Class | Firings |
|---|---|
| Confirmed, mechanical | 11 |
| Confirmed, judgment (author act) | 3 |
| Confirmed, cascading compounds | 7 |
| Not Applicable | 0 |
| **Total** | **21** |

**All 21 firings are Confirmed.** That is not the vocabulary draining of information — it is
Part B's intended result on an honest package, and the substantive content sits in the
ambiguity log and in the decision that stands beside them.

**No Not Applicable verdicts arise.** All five evidence nodes are `ValidationResult`, so SF-4's
node-class rule — which made three of Johnson's five `W-AR-05` firings Not Applicable — finds
nothing here to except.

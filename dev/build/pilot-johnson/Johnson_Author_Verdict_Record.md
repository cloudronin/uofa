# Johnson governed review — author verdict record

Date: 2026-08-21
Author: Vishnu Vettrivel
Governing protocol: docs/Encoding_Protocol_v0_1.md (committed)
Package: dev/build/pilot-johnson/johnson-pilot.jsonld, base_uri https://github.com/cloudronin/uofa
Session: conducted in conversation with author ruling each item; this record is the input for Claude Code to apply to the artifacts. Application is mechanical; any divergence between this record and an artifact's current state is an escalation, not a silent fix.

## Step 1 — Namespace

RULED: keep as minted, `https://github.com/cloudronin/uofa`. A-27 resolves as confirmed-by-author.

## Step 2 — Cell walk

1. Five level rows (18, 20, 21, 22, 23) CONFIRMED against Table 3 (p.7 shading) and p.25, including row 20's required 2 / achieved 4 exceedance.
2. Decision cell CONFIRMED: outcome Accepted anchored p.19; Decided By and Decision Date remain blank as faithful to source.
3. Assessment Summary CONFIRMED including the `NASA-STD-7009A` literal (dual standard declaration per protocol §8).
4. Row 8 Numerical solver error `scoped-out` CONFIRMED (waiver at p.6, p.18).
5. Row 7 Discretization error `not-applicable` CONFIRMED (regression model class, no discretization).
6. Added ProcessAttestation row (fourth verb, §3c) CONFIRMED as warranted, with one CORRECTION: its anchor becomes dual, `p.25 (assessment rationale) + p.24 (M&S 36 review summary incl. disclosed minor findings)`. Update the row's Source Anchor and the corresponding ledger entry.
7. Remaining no-level rows confirmed as a class per the declination pattern (spot-checks above representative).

## Dispositions — eleven firings (protocol vocabulary: Confirmed / Overruled / Not Applicable)

| # | Pattern | Verdict | Class | Notes to apply |
|---|---|---|---|---|
| D-01 | W-AL-02 | Confirmed | mechanical | delta (source sensitivities p.22/p.25 vs package) stays in log; missing node route is schema-finding material |
| D-02 | W-AR-05 | Confirmed | mechanical | non-URI comparator (competing software, p.18) cited as SF-2 instance |
| D-03 | W-AR-05 | Not Applicable | scoping ruling | ReviewActivity has no comparator by nature; SF-1 |
| D-04 | W-AR-05 | Not Applicable | scoping ruling | as D-03 |
| D-05 | W-AR-05 | Not Applicable | scoping ruling | the §3c-added ProcessAttestation; the immediate firing is the SF-1 controlled experiment, note verdict-backed |
| D-06 | W-AR-05 | **Confirmed with offsetRationale** | worked example | offsetRationale anchored p.19: no RWS data exists; test data served as referent; conservative tolerance bound and PRA context bound the model's use. Designated v0.2 worked example |
| D-07 | W-CON-01 | Confirmed | JUDGMENT, author act | package-level inconsistency real; price of decline-don't-invent, displayed not suppressed |
| D-08 | W-CON-01 | Confirmed | JUDGMENT, author act | as D-07 |
| D-09 | W-CON-01 | Confirmed | JUDGMENT, author act | as D-07 |
| D-10 | W-NASA-06 | Confirmed | mechanical | same missing SensitivityAnalysis root as D-01 |
| D-11 | W-ON-02 | Confirmed | mechanical | RULED: no per-package repair; the operating-envelope gap is a workbook/template finding filed with SF-1/SF-2 for the schema increment (source states envelope at p.18, p.19 ×2, p.23) |

## Silence sweep — fifteen factors, per §4e

CONFIRMED as tabled in DISPOSITIONS_DRAFT.md: nine Declined-mapping, two Not Applicable (Discretization error; Numerical solver error), one Source-absent level (Development technical review; content at p.10/p.24 is not a level), five no-disposition-needed (the confirmed level rows). Two ESCALATIONS acknowledged as the record, no disposition possible: Model inputs and Input pedigree (A-07, pack-has-no-home, INV-20 channel).

## Ambiguity log — 28 entries

Auto-resolved by tonight's rulings: 22 (the NA trio's entries, nine declined mappings, namespace A-27, scale-boundary declinations, dual-anchor correction, the 7009A literal, and kin — map each to its ruling above and mark re-adjudicated-by-author with this record's date).
Individually ruled:
- A-10 dual standard declaration: ACKNOWLEDGED, stands.
- A-13 waiver self-contradiction: CONFIRMED, answer-outranks-declination resolution, both anchors retained.
- A-17 negotiated predeclaration (Use history): CONFIRMED, value carried, provenance note stands.
- A-19 incomplete randomization: CONFIRMED, recorded as the source's SME judgment, not encoder endorsement.
- A-22 retained outlier: CONFIRMED, disclosure recorded without encoder ruling.
- A-26 relative-IRI silent drop: ACKNOWLEDGED as ESCALATION-class tooling finding.

## Findings filed or reinforced by this pass

1. SF-1 (evidence typing / W-AR-05 scope) now verdict-backed by D-03..05 including the controlled experiment.
2. SF-2 (non-URI comparators) reinforced by D-02 and D-06.
3. NEW template finding: the workbook carries no cell for a COU operating envelope / applicability constraint, while sources state it repeatedly (D-11 ruling). File beside SF-1/SF-2 for the schema increment; also the Morrison COU1 cross-reference.
4. A-26 tooling finding stands in the tooling channel.

## What remains for the author (not this session)

Apply-record session by Claude Code, then: author reviews the applied diffs, signs the package under the committed protocol, commits. Signing is the author's act alone. On sign-off, the Johnson worked-example citations for protocol v0.2 (D-06, and the NA-vs-Overruled case still awaiting aero COU2) become quotable.

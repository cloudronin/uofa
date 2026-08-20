# Review packet — Johnson (NTRS 20200002832)

**AWAITING-AUTHOR.** This is your evening. Everything below is prepared; nothing below is
decided. Walk it start to finish without needing a terminal.

Artifacts live in `dev/build/pilot-johnson/`. The package is unsigned and stays unsigned
until you sign it.

| | |
|---|---|
| Package | `johnson-pilot.jsonld`, profile Minimal, 19 factors, 6 evidence rows |
| Workbook | `johnson-extracted.xlsx`, 101 review decisions already taken |
| Weakeners | 11 across 5 patterns |
| Ambiguity entries to re-adjudicate | 28 |
| Governing draft | `docs/Encoding_Protocol_v0_1_DRAFT.md` |
| protocol-check | green on all eight checks |

**Time estimate: about three hours.** That is an assumption, not a measurement. The repo
records no adjudication pace, so it is built from 28 ambiguity entries plus 11 firings plus
20 factor rows at roughly three minutes each, with the four hard cases at ten. Correct it
after the first batch of ten and the rest of the estimate follows.

---

## Before you start: two things that are not decisions

Read these first. They change what the rest of the packet means.

**The package understates its source, on purpose.** All four derived credibility metrics
read 0.00. That is the declination rule working, not a defect. Johnson's levels are on a
nought-to-four scale and thirteen of the pack's nineteen factors are one-to-five, so no
level was carried across. If you want a package that does not read 0.00, that is a decision
to change the rule, not a correction to this encoding.

**The extractor's required-level column was synthesized on every factor.** It was not read
from the source and it is not in the workbook any more. Johnson's predeclared levels exist
only as green shading in Table 3 on page 7, recovered from page geometry, and they are
author-side values. If you doubt one, the recovery is reproducible from
`table3_recover.py` and corroborated in `TABLE3_RECOVERY.md`.

---

## Step 1. Confirm the namespace (5 minutes, do this first)

The package mints under `https://github.com/cloudronin/uofa`. `https://uofa.net` is refused
by the tool as reserved for published examples, so the repository namespace was used.

**The identifier is covered by the signature and cannot change after signing.** Confirm it
now or name the one you want. If you change it, `review_pass.py` carries it as a single
constant near the top; everything else follows from a re-run.

Recorded as ambiguity A-27.

## Step 2. The cell walk (about an hour)

`johnson-extracted.xlsx`, five sheets. Every populated row carries a Source Anchor naming
the page it came from, and `REVIEW_LEDGER.md` carries the per-cell record with the
extractor's original value beside the reviewed one.

Walk in this order.

**Credibility Factors, rows 5 to 23.** The heart of it. Only five rows carry levels, all in
the NASA block at the bottom. Check those five against Table 3 on page 7 and the achieved
assessment on page 25. The other fourteen carry status and rationale and no level; check
that you agree with the declination in each case rather than checking a number.

The one row to look at hardest is row 20, `Development process and product management`,
required 2 and achieved 4. The extractor said 4 and 4. This is the two-level exceedance the
paper exists to demonstrate and the encoding nearly lost.

**Assessment Summary, row 3.** Eight populated cells, four deliberately blank. The blanks
are Device Class, Model Risk Level, Assurance Level, and Assessment Date, all source-absent.
`Standards Reference` reads NASA-STD-7009A rather than 7009B; that is deliberate and A-10
explains why.

**Model & Data rows 3 to 5, Validation Results rows 3 to 8.** Row 8 of Validation Results
was added by this session under §3c of the draft protocol, the fourth review verb. It is a
ProcessAttestation drawn from page 25. Confirm the addition was warranted; the pilot
declined to make it and escalated instead, and the protocol draft is what permits it now.

**Decision, row 3.** Outcome reads Accepted, anchored to page 19. `Decided By` and
`Decision Date` are blank. The paper says acceptance requirements were met; it records no
decision act, no decider, and a `(Signed)` line with nothing after it. This is the one
summary-level cell where your judgment does real work.

## Step 3. The eleven dispositions (about 40 minutes)

`DISPOSITIONS_DRAFT.md`, table of eleven. Every row carries a candidate verdict, an anchor,
and the rule as applied.

Take them in three batches.

**Batch A, the six straightforward ones.** D-01, D-02, D-07, D-08, D-09, D-10. All Accepted
on the package basis. D-07 through D-09 are JUDGMENT class per the A1 partition, so your
verdict is the governed act rather than a confirmation.

**Batch B, the three Not Applicable ones.** D-03, D-04, D-05. These say W-AR-05 is
mis-scoped: it tests every node under `hasValidationResult`, and a ReviewActivity or a
ProcessAttestation has no comparator by nature. If you disagree, they become Accepted and
the finding goes away. If you agree, the finding is a rule scoping issue worth filing.

**Batch C, the two that matter most.** D-06 and D-11. D-06 is the Technical Authority waived
validation, the one firing that reads correctly whether adjudicated against source or
package, and the strongest worked-example candidate for §4d of the protocol. D-11 is
W-ON-02, which is a known observation across the queue rather than a property of this
encoding.

## Step 4. The silence sweep (about 30 minutes)

Same file, second table. Fifteen factors drew no firing at all, and that is where the real
gaps are. Nine are declined mappings, one is a source-absent level, five need nothing.

Two are escalations and are not yours to resolve here. `Input pedigree` is predeclared 3 and
achieved 3 in the paper and the pack has no such factor. `Model inputs` is where it would go
and asks a different question. Both route to the schema-findings channel.

## Step 5. The ambiguity log (about 45 minutes)

`AMBIGUITY_LOG.md`, 28 entries in four parts. Nineteen were raised before extraction ran.

Take them in batches of ten with a break between. The four that need real thought are
grouped in Part 3, where the source contradicts itself: A-17 on the waiver, A-18 on
verification, A-19 on the qualifications. Only A-19 has a defensible ordering rule.

Four entries are marked ESCALATION and are explicitly not resolutions. Confirm they should
stay open rather than trying to close them.

## Step 6. What you are not being asked to do

No signing. No ledger row changes. No marking any review complete on this session's behalf.
Those follow your verdicts, in your own commits.

---

## Open items this packet leaves you

1. **The namespace**, step 1. Blocks signing.
2. **Whether W-AR-05's scope is a rule bug**, batch B. Affects three verdicts and one
   possible rule change.
3. **The decision record**, step 2. Whether "acceptance requirements were met" supports an
   Accepted outcome with no decider named.
4. **Two escalations**, step 4. `Input pedigree` and Level 0, both INV-20 territory.

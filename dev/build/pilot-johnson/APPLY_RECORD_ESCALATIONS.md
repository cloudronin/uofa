# Apply-record escalations — Johnson governed review

Date: 2026-08-21
Input: `Johnson_Author_Verdict_Record.md`
Applied by: Claude Code, mechanically, in the apply-record session the verdict record calls for.

The verdict record sets the rule this file exists to obey:

> Application is mechanical; any divergence between this record and an artifact's current
> state is an escalation, not a silent fix.

Six divergences were found and none was reconciled by the session. **The author dispositioned all
six on 2026-08-21**, and this file now carries the round-trip: the divergence as found, the
ruling, and what was applied under it. Everything else in the record applied cleanly on the first
pass and is listed at the end.

| # | Divergence | Ruling | State |
|---|---|---|---|
| E-1 | four individually-ruled ambiguity entries name the wrong ID | re-issue the four by subject; three displaced entries come back for review | **applied; closed** |
| E-2 | two rulings have no log entry | create A-29 and A-30 | **applied** |
| E-3 | D-06's offsetRationale has no route into the package | disposition record only, no package node | **applied; package untouched** |
| E-4 | the ProcessAttestation anchor was already dual | restore all three anchors | **applied** |
| E-5 | the run log's review counts are stale | leave the prose, add a reconciliation line | **applied** |
| E-6 | SF-1/SF-2 mean two things in two places | order-of-filing wins; add a disambiguation note | **applied; closed** |

**All six are closed.** E-1's three displaced entries — A-13, A-19 and A-22 — were quoted back to
the author and confirmed as drafted on 2026-08-21. The ambiguity log's 30 entries are all
adjudicated, and nothing in this packet is waiting on the author except the two acts that were
always theirs alone: reviewing the diffs and signing.

---

## E-1 — four individually-ruled ambiguity entries name the wrong ID

**BLOCKING for those four rulings. Nothing was applied to A-13, A-17, A-19 or A-22.**

The record rules six ambiguity entries individually. Two match the committed log; four do not.

| Record says | Committed `AMBIGUITY_LOG.md` entry of that ID | Entry that actually carries the record's subject |
|---|---|---|
| A-10 dual standard declaration | A-10 = `Standards Reference`, 7009A vs 7009B | ✅ match, applied |
| A-26 relative-IRI silent drop | A-26 = relative IRIs dropped at expansion | ✅ match, applied |
| A-13 waiver self-contradiction | A-13 = `Assurance Level`, not stated | **A-17** (Waivers: p.8 describes a TA-approved waiver and denies one; p.23 answers "None") |
| A-17 negotiated predeclaration (Use history) | A-17 = Waivers | **A-02** is the Use history mapping; the negotiation is recorded in the row-23 note in `review_pass.py` ("Predeclaration was negotiated; see p.7-8"), not as a log entry |
| A-19 incomplete randomization | A-19 = [M&S 37] people qualifications, declined p.10 / answered p.24 | **none** — see E-2 |
| A-22 retained outlier | A-22 = factor status for evidence-without-level factors | **none** — see E-2 |

**The four mismatches are not random.** They are, in order, the four worked-example candidates
listed in `PROTOCOL_FINDINGS.md` F-4d: the TA-waived validation, the negotiated M&S History
predeclaration, the incomplete randomization judged inconsequential by SMEs, and the retained
outlier. The rulings read as rulings on that list, with ambiguity-log IDs attached to it.

**One ruling is internally mixed as well.** "A-13 waiver self-contradiction: CONFIRMED,
answer-outranks-declination resolution, both anchors retained" combines A-17's subject (the
waiver contradiction), A-19's rule (answer outranks declination — A-17's own rule is explicitly
*do not pick*), and A-17's disposition (both anchors retained). Applying it to either entry
would change what that entry decided.

### Ruling, 2026-08-21 — re-issue the four by subject

**Applied.**

- **The waivers self-contradiction (log A-17): CONFIRMED, with the rule corrected.** The entry's
  own resolution governs — *do not pick*. The record's summary had imported
  answer-outranks-declination, which is A-19's rule, and that import is **withdrawn as an error
  of the summary**. No harmonization; both anchors retained; the encoding carries the specific
  waiver record as data while the contradiction stays open in the log. This is consistent with the
  protocol's stated honest limit: A-9's ordering rule covers one of this source's three
  contradictions, and this is one of the other two.
- **The negotiated Use history predeclaration: CONFIRMED, and it is not a log entry.** It is
  F-4d's worked candidate. The confirmation lands in the disposition and finding record —
  `PROTOCOL_FINDINGS.md`, the F-4d ruling row — and not in the ambiguity log.
- **Incomplete randomization and the retained outlier:** E-2. Now A-29 and A-30.
- **A-10 and A-26 stand as applied.**

### The three displaced entries — quoted, returned, and ruled

The four mis-addressed rulings displaced three real entries that no pass had adjudicated. Each
was quoted back in one line and **confirmed as drafted on 2026-08-21**. A-19 was ruled first,
because it is where answer-outranks-declination properly lives; confirming it accounts for the
import withdrawn from A-17 and closes E-1.

| ID | The entry, in one line | Resolution, CONFIRMED as drafted 2026-08-21 |
|---|---|---|
| **A-13** | `Assurance Level` (Low / Medium / High) is not stated anywhere in the source. | Blank and listed, on the same rule as A-12: an assurance level is assigned by a decision process, and inferring one would be the encoder grading the model. |
| **A-19** | [M&S 37] people qualifications: p.10 says "(Will not be covered in this report.)" and p.24 answers it in full, with degrees and years of experience. | Use the p.24 content, anchored, and keep the p.10 declination in the same cell's anchor — *an answer outranks a declination; the declination is context*. **Ruled first.** The rule now lives on the entry it belongs to and nowhere else, which is what makes the A-17 withdrawal complete rather than merely stated. |
| **A-22** | Factor status for the V&V 40 factors carrying evidence but no level: `assessed` implies a level, `not-assessed` denies the evidence. | `assessed` for the four the LCW answers directly, `scoped-out` for Numerical solver error, `not-assessed` for the rest — what the Step 2 cell walk verified. D-07 to D-09 are Confirmed as the accepted *consequence* of this resolution and are not an adjudication of it; **this ruling is the adjudication**, and the distinction is kept verbatim in the log. |

---

## E-2 — two rulings have no ambiguity-log entry to attach to

**Nothing created.**

The record rules on *incomplete randomization* ("recorded as the source's SME judgment, not
encoder endorsement") and on a *retained outlier* ("disclosure recorded without encoder ruling").
Neither has an entry in `AMBIGUITY_LOG.md`. Both appear only in `PROTOCOL_FINDINGS.md` F-4d,
with anchors: randomization at p.8, p.15 and p.23; the outlier at p.21, "pulling it less than
0.003 cm in nonconservative direction".

These are not re-adjudications. They are new entries, and creating a log entry is authoring a
record of what the encoding decided — not something this session may do on the author's behalf.

### Ruling, 2026-08-21 — approved as proposed

**Applied.** Both disclosures are real source content, both were ruled on substance, and the log
is the right home. **A-29** *incomplete randomization* — recorded as the source's SME judgment,
not encoder endorsement. **A-30** *retained outlier* — disclosure recorded without an encoder
ruling. Both carry the rule that an assessment's disclosure of its own limitation is evidence
about the assessment, and that carrying it is not agreeing with it.

The log is now **30 entries**. The record's 28 was simply the pre-walk state.

**Anchors CONFIRMED 2026-08-21.** The dispositions gave p.24 for both; F-4d's committed anchors
are p.8, p.15 and p.23 for the randomization and p.21 for the outlier. **F-4d governs**, on the
same source-over-summary principle that decided E-1 and E-4: the anchored record outranks a
conversational note about it. The entries carry F-4d's anchors.

---

## E-3 — D-06's offsetRationale has no route into the package

**Applied to the disposition record. Not applied to the package.**

The record rules D-06 **Confirmed with offsetRationale**, anchored p.19. That verdict, its
rationale text and its designation as the v0.2 worked example are now in
`DISPOSITIONS_DRAFT.md`. The verdict itself is Confirmed, which is Part B vocabulary; the
offsetRationale is an addition alongside it rather than a fourth verdict.

What is escalated is whether the package should also carry it. The construct exists —
`uofa:OffsetRationale` and `hasOffsetRationale` are in the v0.5 context, and
`packs/vv40/examples/nagaraja/cou1` carries one on its decision record with `refersToFactor`
and `justification`. But:

1. **No on-ramp route.** `excel_mapper.py` has no offset handling and the `nasa-7009b` template
   has no column. Adding one to `johnson-pilot.jsonld` means hand-editing the package after
   import, which breaks the property that the package is reproducible from the workbook. This is
   the same class of gap as the `SensitivityAnalysis` node behind D-01 and D-10.
2. **The target is a validation result, not a factor.** Nagaraja's `refersToFactor` points at a
   credibility factor. D-06's firing is on `waived-validation-against-real-world-system-data`, a
   validation result. What the Johnson offsetRationale would refer to is a design question.
3. **D-11 rules the opposite way on a sibling case** — "no per-package repair" for the operating
   envelope, with the gap sent to the schema increment instead.

### Ruling, 2026-08-21 — disposition record only, no package node

**Applied. The package is untouched.** The adjudicated disposition record is the governed
artifact, and the verdict and its offsetRationale live there. Minting a package node through a
route the on-ramp does not have would be a hand-crafted graph edit of exactly the class the
fixtures finding warned about, and D-11's sibling rule — no per-package repair where the template
lacks the route — applies squarely.

The missing route is filed as a template finding beside the envelope gap: a row in
`PROTOCOL_FINDINGS.md`'s cross-cutting table, and a sibling-gap note under SF-6 in
`docs/SCHEMA_FINDINGS.md`, which flags that it can be promoted to SF-7 if the increment wants it
as its own entry.

---

## E-4 — the ProcessAttestation anchor was already dual, with a different partner

**Applied as ruled. Flagged because a value was displaced.**

The record's Step 2 item 6 reads "its anchor becomes dual", which describes a single anchor
gaining a second. The row's anchor was already dual:

- **before:** `p.25 M&S Process / Product Management rationale; p.12 4.1.3 a,b`
- **after (ruled):** `p.25 (assessment rationale) + p.24 (M&S 36 review summary incl. disclosed minor findings)`

So the ruling does not add p.24 to p.25 — it replaces **p.12 4.1.3 a,b** with p.24. The ruled
value is unambiguous, so it was applied to `review_pass.py`, and `johnson-extracted.xlsx` and
`REVIEW_LEDGER.md` were regenerated from it (the script is idempotent; the anchor is the only
diff). The package is untouched, because anchors do not reach the JSON-LD — `PROTOCOL_FINDINGS.md`
F-2b.

### Ruling, 2026-08-21 — restore all three anchors

**Applied.** The ruling was written as *add p.24*, not *displace p.12*; the displacement was an
artifact of the phrasing "p.25 + p.24". Final anchor, because all three genuinely carry the
attestation:

`p.25 (assessment rationale) + p.24 (M&S 36 review summary) + p.12 §4.1.3(a,b)`

Re-applied in `review_pass.py`; `johnson-extracted.xlsx` and `REVIEW_LEDGER.md` regenerated. The
package is unaffected — anchors do not reach the JSON-LD.

---

## E-5 — the run log's review counts are stale

**Flagged in place. The prose was not rewritten.**

`RUN_LOG.md`'s provenance self-audit reads "97 — 47 confirmed, 14 corrected, 36 blanked". The
generated ledger now reads **101 — 47 confirmed, 17 corrected, 36 blanked, 1 added**. The
difference is the §3c pass: one added row and three identifier corrections. The same 97/14 pair
also appears in `PROTOCOL_FINDINGS.md`, in finding 2 of the headline three and in F-7a.

This divergence predates the verdict record and was not created by it. The finding it supports —
that a hundred-odd review decisions still report `4 extracted` — is unaffected in substance and
gets stronger with the larger number.

### Ruling, 2026-08-21 — leave the prose, add a reconciliation line

**Applied.** The 97/14 pair is a historical statement about the pre-§3c pass and feeds Ch3 as
such; rewriting it would falsify the record. The run log's provenance table is restored to its
original wording, and a dated line sits under it: *post-§3c regeneration: 101 decisions, 17
corrected; the 97/14 figure describes the pre-addition pass.* `REVIEW_LEDGER.md` is the
authoritative count, and anything citing a decision total — Ch3's eventual sentence included —
cites the ledger.

---

## E-6 — SF-1 and SF-2 mean two different things in two places

**Filed under the channel's own numbering rule. Flagged for the author's call.**

The record's findings section refers to "SF-1 (evidence typing / W-AR-05 scope)" and "SF-2
(non-URI comparators)", following `docs/Ruling_WAR05_Schema_Findings.md`, which uses those labels.
In the committed channel, `docs/SCHEMA_FINDINGS.md`, **SF-1 is `Input pedigree`** and **SF-2 is
Level 0**, both filed earlier and both cited by the protocol.

Neither the ruling document's findings nor the record's third finding (the COU operating envelope)
had been filed in the channel at all. They are now, using the channel's stated rule — "entries are
numbered `SF-n` in the order they are filed":

- **SF-4** — non-comparison evidence has no predicate of its own *(the record's "SF-1")*
- **SF-5** — real comparators are not always URI-shaped *(the record's "SF-2")*
- **SF-6** — a context of use has no cell for its operating envelope *(the record's finding 3)*

Each carries a cross-reference note to the label it was given elsewhere, and the channel's header
records the collision.

### Ruling, 2026-08-21 — filed correctly; disambiguation note added. **CLOSED.**

**Applied.** The channel's order-of-filing rule wins and SF-4, SF-5 and SF-6 stand. The header of
`docs/SCHEMA_FINDINGS.md` now carries the line that kills the future confusion: where a
conversational or ruling document says "SF-1" or "SF-2" for the evidence-typing or
comparator-identity gap, it means SF-4 and SF-5 as filed, and SF-1 and SF-2 in the channel are
`Input pedigree` and Level 0, cited under those numbers from the protocol.

---

# What applied cleanly

Everything below matched the artifacts and is now in them.

**Step 1 — namespace.** `https://github.com/cloudronin/uofa` kept as minted. A-27 resolves
confirmed-by-author; the `[AUTHOR-CONFIRM]` gate on the `base_uri` row in `RUN_LOG.md` is
discharged.

**Step 2 — cell walk.** All seven items verified against the artifacts before anything was
written. The five level rows are 18, 20, 21, 22 and 23 as stated, with row 20 carrying required 2
/ achieved 4. The Decision cell carries outcome Accepted anchored p.19 with Decided By and
Decision Date blank. Assessment Summary carries the `NASA-STD-7009A` literal. Row 8 Numerical
solver error is `scoped-out`; row 7 Discretization error is `not-applicable`. The
`ProcessAttestation` row exists and its anchor is corrected — subject to E-4.

**Dispositions.** All eleven verdicts applied to `DISPOSITIONS_DRAFT.md` in Part B vocabulary:
eight Confirmed, three Not Applicable. The draft's Accepted/ACCEPTED wording is replaced
throughout, including in the two prose passages that used it as a verdict. Class and the author's
note are carried per row. The file's state changes from AWAITING-AUTHOR to ADJUDICATED. One
incidental correction: the draft's D-03 row spelled the node
`conceptual-validation-via-sme-team-review`; the package and the rules report both spell it
`conceptual-validation-via-smeteam-review`, and the table now uses the package's spelling.

**Silence sweep.** Confirmed as tabled, with the author's breakdown recorded above the table:
nine Declined-mapping, two Not Applicable, one Source-absent level, five needing no disposition,
two acknowledged escalations.

**Ambiguity log.** A re-adjudication section carries a verdict for all 28 entries, with the four
E-1 entries marked ESCALATED instead. A-07 and A-08 stand as acknowledged escalations. A-24 is
closed by the §3c ruling.

**Run log.** A governed-review-pass section records the reviewer by name, the date, the governing
protocol version and the form of the session — which is what protocol A-13 requires of the run
log. It now also records the signing, which happened on 2026-08-21 after these diffs were
reviewed.

**Findings.** SF-4, SF-5 and SF-6 filed, subject to E-6.

---

# Still outstanding for the author

E-1 through E-6 are dispositioned, applied and closed. All 30 ambiguity entries, all eleven
firings and all nineteen expected factors are adjudicated. The author reviewed the diffs and
**signed the package on 2026-08-21**.

**One item was raised after that signing**, and it is not part of this escalation set, because it
was not a divergence between the record and the artifacts: the signed package's `wasAttributedTo`
named `org/claude`, an incidental container identity picked up by the 2026-08-20 import rather
than a declaration anyone chose. **The author ruled to fix it.** The package was re-imported with
`UOFA_ASSESSOR` set explicitly, which corrected the attribution and discarded the signature.

Diffed field by field against the package it replaced: five fields differ — the attribution, the
import `sourceFile` and `timestamp`, `generatedAtTime`, and the signature and hash reverting to
placeholders — and no content. All 19 credibility factors, all 6 validation results and all
eleven firings are identical, so **every verdict in this packet stands unchanged**.

**The author re-signed the corrected package the same day**, and `uofa check` returns
C1 ✓ C2 ✓ C3 ✓ with the eleven firings matching the dispositioned set node for node.
`RUN_LOG.md` carries the full history: the superseded first signature, the correction, the
measured diff, and the signature in force.

**The packet is complete.**

On sign-off, the Johnson worked-example citations for protocol v0.2 become quotable: D-06, and
the Not-Applicable-versus-Overruled case still awaiting the aero COU2.

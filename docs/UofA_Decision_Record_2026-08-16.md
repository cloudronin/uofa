# UofA Author Decision Record 2026-08-16

Status: RULED
Owner: Vishnu Vettrivel
Consumers: Claude Code (Phase 2.5a and investigation follow-ups), A4 audit-trail appendix, parent spec UofA_Unified_Repair_Spec_v2_0.md.
All twelve decisions queued by the 2026-08-16 investigation SUMMARY are ruled below. Where a ruling changes parent-spec text, the delta is stated.

| # | Decision | Ruling | Effect |
|---|---|---|---|
| 1 | Mutator vs gate revision | Fund the deterministic mutator; GATE-H3 held as set (MECHANICAL ≥95%, JUDGMENT and overall ≥80%, FP <10%) | Phase 2.5a spec v1.0, handed off. Gate evaluated once against P25-A; misses reported, not patched |
| 2 | P25-A timing | Before any A2 manuscript text | Sequencing binding in Phase 2.5a spec §3 |
| 3 | Compounds in partition | EXCLUDED. Label classes and gates scope to the 21 base patterns; COMPOUND-01/03 reported separately as composition results | A1 partition table is 21 rows; B1 schema allows label_class=COMPOSITE or null for compounds; Ch3 partition text scoped accordingly |
| 4 | W-PROV-01 class | MECHANICAL. Criterion is the re-derivability test, not the measured score; isFoundationalEvidence is a structural declaration of the package as encoded | Stays under the ≥95% gate; its 0.672 is treated as generation artifact pending Arm M measurement |
| 5 | sh:in vocabularies | DEFERRED to v0.6, post-defense, as a disclosed catalog increment | No action now; freeze holds |
| 6 | A10 inclusion-rule N | N=3: admitted papers must carry prose evidence for ≥3 credibility factors | Rule is hereby committed BEFORE any admission; INV-13 screen results may now be applied same-day |
| 7 | Morrison/Nagaraja in H2 corpus | RECLASSIFY, not delete. Both become labeled development documents; headline real-corpus metrics report the held-out papers; with-development-documents figures shown as a sensitivity row | A9/A10 corpus text and per-document tables carry the two-tier structure; base held-out count is 4 pending A10 admissions |
| 8 | Bologna assignment | CONDITIONAL: screen Ahn & de Weck for the scorecard pool first. If it qualifies, Bologna goes to A3 (external negative). If not, Bologna still goes to A3; the scorecard pool takes the measured-scarcity disclosure instead | A3 is on the defense path (must-have 1 FP gate); scorecard pool is not |
| 9 | Ch4 H2 ordering claim | One recovery attempt on PR #62 pre-squash refs (refs/pull/62/head and reflog); if unrecoverable, reword the chapter claim to what the record proves | A4 presents each freeze at its actual evidentiary strength; Phase 3's provable ordering and H2's reworded claim sit in the same table |
| 10 | D6 contested numbers | MEASURE (~3h). Re-derive 384/427 from committed artifacts; verify the equality claim in both directions (every cleared result carries stated uncertainty AND every result with stated uncertainty is cleared) | D6 drafting blocked until the script and results are committed; invariance sentence stays on the Demonstrated rung |
| 11 | Phase 3 Stage 4 sitting | NOW, this week, author's own calendar, parallel to 2.5a | Closes Phase 3; 21-case queue adjudicated; Tier-1 gap-probe outcome reported; Ch4 §4.4.4 placeholder fills; any confirmed REAL-GAPs named as the v0.6 increment in future work |
| 12 | A8 washout clock | CONSERVATIVE: 2026-09-03 (last touch of any kind), applicable only if A8 is elected after ranks 1-7 | No current action |

## Immediate dispatch

To Claude Code (with Phase 2.5a already in hand): rulings 3 and 4 finalize the partition the operator registry reads (21 base patterns, W-PROV-01 MECHANICAL); ruling 6 unblocks INV-13 admissions; ruling 8's Ahn & de Weck screen and ruling 10's D6 measurement script are next in queue after 2.5a steps 0-2; ruling 9's recovery attempt can run in the same session as the A4 history work.

Author's own calendar: Stage 4 sitting this week (ruling 11).

## Audit-trail note (for A4)

Rulings 1, 3, 4, and 6 set or scope evaluation gates and selection rules. Each is recorded here with its date, before the measurements or admissions it governs: GATE-H3 held before P25-A runs; the 21-pattern scope and W-PROV-01 class fixed before Arm M is scored; N=3 committed before any paper is admitted. This ordering is the point of the record.

**A4 cites this file by its commit, not by its path.** The record sat untracked
until 2026-08-16; an untracked file carries a filesystem mtime, not a commit date,
and an mtime is not evidence of ordering. That is the same defect INV-6 §4 found in
the Ch4 H2 claim, where the thresholds could not be shown to precede their
measurement because both landed in one squashed commit. This record is therefore
committed **alone**, before Arm M is scored, so the ordering it asserts about itself
is provable from `git log` rather than asserted in prose.

---

# Addenda

Both addenda are dated 2026-08-16 and are committed in the same commit as the record
above, which precedes Phase 2.5a step 3 (Arm M).

## Addendum A — W-AR-03 class

**Ruling: MECHANICAL.**

Same criterion as ruling 4: class is decided by re-derivability of the label as the
rule exists at v0.5.15.1. W-AR-03's comparison
(`notEqual(requiredVerificationMethod, activityType)`) runs on declared package
fields, so a script re-derives it. The absence of the `sh:in` vocabulary makes the
rule **weaker, not human-dependent**; ruling 5 deferred the hardening, not the
classification.

**Effect.** The partition is **MECHANICAL 17, JUDGMENT 4**, over the 21 base
patterns (compounds excluded per ruling 3). **GATE-H3's MECHANICAL denominator is
17.** `docs/investigations/INV-1-findings.md` §3 is updated from its original 15/6
reading to the ruled partition; the two escalations it raised (W-AR-03 ambiguous;
COMPOUND-01 unclassifiable) are both now closed by ruling — the first by this
addendum, the second by ruling 3.

**Criterion, stated once for reuse in the A1 Ch3 text:** `isFoundationalEvidence` is
a *structural declaration* of the package as encoded; `factorStatus` and
`hasOffsetRationale` are *dispositional*. That is why W-PROV-01 and W-AR-03 are
MECHANICAL while W-EP-04, W-AR-01, W-AR-02 and W-CON-01 are not. The operator
registry carries this rationale as data so the asymmetry is auditable.

## Addendum B — GATE-H3 treatment of the enrichment split

**Ruling: GATE-H3's MECHANICAL ≥95% evaluates on the full battery.** The gate's
question is unit detection — does the rule fire when its precondition is present and
violated — which Class B (antecedent-instantiation) mutants test legitimately.

The as-encoded vs enrichment-required split is **reported alongside as the
ecological-validity result**: these rules are proven to work *and* proven unable to
fire on evidence produced by the project's own protocol. That second half is a
schema/protocol coverage finding feeding v0.6 — encodings should instantiate
`wasGeneratedBy` chains and inline their requirements — plus one honest sentence in
the A2 prose.

**Scope note.** The ruling was issued naming **three** such rules (W-EP-03, W-AR-04,
W-CON-03). Addendum A moved W-AR-03 to MECHANICAL, and the Phase 2.5a §0.1
precondition check then established that no substrate inlines `bindsRequirement` or
carries `activityType` — so W-AR-03 is Class B as well. **The enrichment-required set
is four, not three.** The ruling's reasoning is unchanged; only the count moved, and
it moved after the ruling rather than in response to a measurement.

## Why these are recorded before the measurement

Addendum B fixes how a result will be scored before the result exists, and addendum A
fixes the denominator it is scored against. Recording them afterwards would be the
retroactive thresholding that GATE-H2's own rationale condemns, and Phase 2.5a spec
§2.2 holds the gate to a single evaluation for the same reason.

# Ruling Implementation Plan 2026-08-16

> **Superseded, retained as record.** This is session 2's plan as approved on
> 2026-08-16, before execution. `UofA_Unified_Repair_Spec_v2_1.md` is the execution
> document; this file is kept because the rulings letter responds to it by name and
> because its §5 probe design and three-strength table are cited by the A4 material.
>
> **Three things in it were overtaken within the hour, and two of those were wrong
> when written:**
>
> 1. **Escalation 2 was incorrect.** It reported that the INV-8 addendum did not
>    exist. It does — session 1 wrote it, and it covers all five findings including
>    the stack order and the signing-policy block on MUT-INT-02. The error came from
>    a search that read the stale copy of the file. Escalation 4 is resolved by the
>    same artifact.
> 2. **Tasks 1 and 2 were already done by session 1.** The ruling record was
>    committed alone at `fad31cf5`, carrying both addenda, before the run it governs
>    — which is exactly what this plan's task 1 existed to produce.
> 3. **The 13/4 operator split in §1 is projected, not measured.** The step-1
>    precondition inventory (`fed5a37e`) measured **9/8**. See
>    `UofA_Phase2_5a_Spec_v1_1.md` §1.2.1.
>
> What survived execution: the §5 probe (run, negative), the three-strength
> evidentiary table, the v2.1 delta report, and the Phase 3 spec version finding.

Status: DRAFT for author approval
Owner: Vishnu Vettrivel
Inputs: `UofA_Decision_Record_2026-08-16.md` (12 rulings, RULED), the 2026-08-16
investigation SUMMARY (14 findings files), `UofA_Unified_Repair_Spec_v2_0.md` (parent, DRAFT).

This plan converts the twelve rulings into execution order. It does three things:
states the spec deltas the rulings force, sequences the work around the one
critical path, and names the four places where the rulings leave a residue that
still needs an author call.

---

## 0. What the review found

The rulings are internally consistent and mostly directly executable. Three
things are worth saying before the phase list:

1. **One critical path dominates.** Ruling 1 (fund the mutator, hold GATE-H3)
   and ruling 2 (P25-A before any A2 text) chain into a single sequence that
   blocks ranks 1 and 2 of the parent spec's own priority ordering. Everything
   else is parallel. If only one thing runs this week, it is this chain.

2. **The gate is held at a number the current data misses by 22 points.** That
   is a deliberate, disclosed bet: the misses are diagnosed as generation
   artifacts, and the mutator is the fix. The bet is sound but it is untested,
   and the test costs 15 minutes (Phase 1, step 1). Run the probe before
   spending 5-7h on the mutator.

3. **Ruling 9's recovery attempt has already been run — see §5.** The history is
   recoverable, but it does not prove what Ch4 claims. Details below; this
   changes the A4 drafting, not the plan's shape.

---

## 1. The partition after the rulings (A1's actual table)

Rulings 3 and 4 both move rows, and INV-1 moved eight rows against the parent
spec's provisional assignment. Composed, the A1 table is **21 base patterns**:

| Class | Count | Patterns |
|---|---|---|
| MECHANICAL | 16 | W-EP-01..03, W-AL-01..02, W-ON-01..02, W-AR-04..05, W-SI-01..02, W-CON-02..05, W-PROV-01 |
| JUDGMENT | 4 | W-EP-04, W-AR-01, W-AR-02, W-CON-01 |
| **Unresolved** | **1** | **W-AR-03 — see §6, residue 1** |
| Excluded (ruling 3) | 2 | COMPOUND-01, COMPOUND-03 → `label_class = COMPOSITE or null` |

Two consequences the parent spec does not yet carry:

- **The mutator's scope is 16-17 patterns, not 15.** Ruling 4 pulls W-PROV-01
  into MECHANICAL with its 0.672 explicitly deferred to Arm M, so it needs a
  mutation. The SUMMARY's 4-6h estimate was scoped to 15. Budget 5-7h (which is
  what ruling 1 funds).
- **The gate denominator is not yet fixed.** MECHANICAL at 16 vs 17 changes the
  ≥95% arithmetic. Resolve W-AR-03 before Arm M is scored, not after.

---

## 2. Phase 0 — Reconcile the parent spec with the rulings (2h, no dependencies)

v2.0 is still DRAFT and its text now contradicts the record in nine places.
Execution should read one document. Apply as one commit, before anything else:

| § | Current text | Delta | Ruling |
|---|---|---|---|
| A1.1 | "classify all 23 patterns"; provisional partition | 21 base patterns; the §1 table above; compounds `COMPOSITE`/null | 3, 4 |
| A1 done-gate | "23 patterns classified" | 21 classified; compounds reported separately | 3 |
| §0.1 GATE-H3 | "(the holdout supports it)" | Strike the parenthetical; replace with the measured 72.6% / 76.2% and the Arm M rationale | 1 |
| A3.2 | "one additional published, accepted submission... INV-5 confirm" | Bologna (Aldieri 2023) named as the external negative | 8 |
| A10 scorecard pool | "Bologna is the next bundle" | Bologna reassigned to A3; pool takes the measured-scarcity disclosure | 8 |
| A10.1 | "prose evidence for ≥N credibility factors" | **N=3**, committed 2026-08-16 before any admission | 6 |
| A10.1 exclusions | "Exclusions: Morrison, Nagaraja" | Reclassify as labeled development documents, not delete; two-tier reporting | 7 |
| A10.3 | "11-14 total (6 current + 5-8 admitted)" | Base held-out = **4**; 11-14 target restated against that base | 7 |
| A8 | "minimum 3-week washout (INV-3)" | Clock = **2026-09-03**, last touch of any kind | 12 |
| B2 | 2-3h | **5-7h**, deterministic mutator over 16-17 MECHANICAL patterns | 1 |
| C1 | 2-4h, contingent on INV-12 | **Shipped** at `535dfd52` (2026-08-13); replace with a 15-min deployment verification | INV-12 |
| A7 / INV-2 | "check whether protocol-check is cheap" | Build it with A7; clause 5 is a derived predicate, G3 eliminated; 3-5h total | INV-2 |
| INV register | all Open | INV-2/3/4/12 and INV-10-residual → CLOSED; rest → ruled | — |
| §5 A8 | "sh:in ... (~1h; free to decide now)" | **DEFERRED to v0.6**, disclosed catalog increment | 5 |

Effort roll-up after these deltas: **~48-68h** (v2.0's 44-61, plus B2 +3-4,
P25-A +3-5 and ~$50, D6 measurement +3, INV-10 residual +45m, less C1 -2 to -3.75).

---

## 3. Phase 1 — Cheap unblocks (~1h total, all parallel, no rulings pending)

Run these first. Two of them can change later decisions.

1. **The typing probe (15 min).** Open 2-3 failing `…w-ep-03…` generated
   packages, check the `dataVintage` literal datatype. This confirms or kills
   the typing hypothesis that the entire mutator bet rests on. INV-1 row 3
   flags exactly this: Jena `lessThan` needs comparably-typed literals, and a
   mistyped `xsd:string` date silently fails to fire. **If the hypothesis is
   wrong, the zeros are rule defects, not generation artifacts, and ruling 1's
   premise needs revisiting before 5-7h is spent.**
2. **The two-word fix (5 min).** `datasetcard_info.parquet` →
   `modelcard_info.parquet` in
   `docs/model-credibility-pack-addendum-v0_5-taxonomy-validation.md:32` and
   `studies/taxonomy-validation/frame.py:4`. Confirmed both still present; the
   third hit in `studies/taxonomy-validation/PREREGISTRATION.md:104` is the
   correction note itself and stays. One of the two is the script that computes
   the D6 frame, so this lands before D6 drafting.
3. **C1 deployment verification (15 min).** Confirm the deployed HF Space
   revision includes `535dfd52` and has `UOFA_DEMO_SIGNING_KEY` set. C1 is
   built; this is all that remains of a 2-4h line item.
4. **Ruling 9's recovery attempt — done, see §5.**

---

## 4. Phase 2 — The critical path: mutator → Arm M → P25-A

This is rulings 1 and 2 and it blocks A2, D7's Demonstrated rung, A1's Ch3
scoping and A2's null-control standard. Nothing in workstream D that reports a
number should be drafted until step 4 lands.

| Step | Work | Effort | Gate |
|---|---|---|---|
| 1 | **Specify Arm M before building it** — see §6, residue 2 | 30 min | Written, dated, committed before any scoring |
| 2 | `uofa inject --pattern <id> --package <clean-pack>` deterministic mutator over the 16-17 MECHANICAL patterns; one-line mutations per INV-11 §4b | 5-7h | Every MECHANICAL pattern has a mutation that provably fires |
| 3 | `uofa detect` + README walkthrough reproducing the letter's own description end to end | 1-2h | B2 done-gate; the live demo of must-have 1 |
| 4 | **P25-A: full-battery holdout at v0.5.15.1**, both arms | 3-5h + ~$50 | GATE-H3 evaluated **once**; misses reported, not patched (ruling 1) |

Three things this sequence fixes as a side effect, worth stating in A4:

- The version-mismatched pair the manuscript currently makes ("CE recall 73.4%
  at v0.5.7, NC clean 97.1% at v0.5.15.1") — one measurement at one version.
- W-PROV-01's 0.672, which ruling 4 explicitly parks pending Arm M.
- The v0.5.15.1 row of the recall table, currently "not measured" in all three columns.

**Discipline note.** Ruling 1 says the gate is evaluated once and misses are
reported, not patched. That is the whole value of the ruling and it only holds
if Arm M is specified before it is scored. Step 1 is not optional overhead.

---

## 5. Phase 3 — Ruling 9: recovery attempted, result below

Ruling 9 authorised one recovery attempt on PR #62 pre-squash refs. **Run.**

`refs/pull/62/head` survives on the remote at `ce46c17b`; the full 20-commit
pre-squash history fetched cleanly. So the premise that the history was lost to
the squash is wrong — it is recoverable and now fetched locally as
`refs/uofa/pr62`.

**But it does not prove the ordering claim.** Commit `1abbf8d6`
(2026-08-15 00:29:52 -0700) contains, in one commit:

- `docs/decisions/2026-08-14-h2-replacement-thresholds.md` (the declaration)
- `dev/tools/scripts/real_document_rescore.py` (the instrument)
- `studies/real-document-rescore/FINDINGS.md` (the result)

Declaration, script and result land together, so commit order separates nothing.
What the recovered history *does* carry is a contemporaneous written attestation
inside the declaration itself — "**Status: DECLARED, NOT YET MEASURED against
the real corpus**" and "The real-document re-score has not been run," with each
figure labelled synthetic or pre-existing.

That is real evidence, and it is weaker than Phase 3's. Phase 3's
`GATE7_DECISION.md` (2026-06-09 20:24) provably precedes every Stage 2 execution
artifact (2026-07-17 onward) by five weeks, in commit order, with no attestation
required. So A4's one table should show three evidentiary strengths, not two:

| Freeze | Evidence | Rung |
|---|---|---|
| Phase 3 gate | Commit order, 5-week separation | Provable |
| H2 replacement thresholds | Same-commit contemporaneous declaration, self-labelled unmeasured | Attested |
| — | — | — |

**Recommendation:** take ruling 9's second branch — reword the Ch4 H2 claim to
"declared before measurement and recorded as such" rather than "provable from
commit order," and cite `refs/pull/62/head` as the recovered record. One
remaining probe could still upgrade it: generated-at timestamps *inside*
`studies/real-document-rescore/` artifacts, if they postdate the declaration
file's own content. Worth 20 minutes before rewording, not more.

---

## 6. Phase 4 — Parallel workstreams (no dependency on Phase 2)

**Corpus and admissions (rulings 6, 7, 8).** N=3 is committed, so INV-13's
screen results can be applied same-day.
- Screen Ahn & de Weck first (1h) — ruling 8 makes this conditional-gating, and
  it can relieve the scorecard pool *and* count toward the annotation pool.
- Read the Bologna PDF for its decision record and required-vs-achieved levels (1h).
- Apply N=3 to the 7 screenable candidates; admit against the committed rule.
- Restructure A9/A10 corpus text two-tier (ruling 7): 4 held-out papers as the
  headline, Morrison/Nagaraja as labeled development documents in a sensitivity row.
- Note the arithmetic: base is 4, so reaching 11 requires **all 7** screenable
  candidates to qualify. If they do not, ruling 7's done-gate branch applies —
  disclose the measured ceiling with screen results.

**D6 measurement (ruling 10, ~3h).** Re-derive 384/427 from committed artifacts;
verify the equality claim in **both** directions. D6 drafting stays blocked until
the script and results are committed. The invariance sentence stays on the
Demonstrated rung either way.

**Stage 4 sitting (ruling 11, author's own calendar, this week).** 21-case queue
adjudicated; Tier-1 gap-probe outcome reported; Ch4 §4.4.4 placeholder fills; any
confirmed REAL-GAPs named as the v0.6 increment.

**A4 audit trail.** Now has four ordering entries to render at their actual
strengths: Phase 3 gate (provable), H2 thresholds (attested, §5), GATE-H3 and the
21-pattern scope and N=3 (all recorded 2026-08-16, before the measurements and
admissions they govern — which is the point of the decision record).

**INV-10 residual (90 min).** Label the 11 bucket-2 extraction citations
raw/adjudicated **and** synthetic/real, adding null columns where A5 requires.

---

## 7. Four residues the rulings leave

These are not blockers for Phase 1, but each needs a call before its consumer.

1. **W-AR-03 is unclassified, and rulings 3 and 5 interact to keep it that way.**
   INV-1 escalated it; committing `sh:in` vocabularies for `activityType` /
   `requiredVerificationMethod` would have resolved it to MECHANICAL "on
   evidence rather than argument" — but ruling 5 defers `sh:in` to v0.6. So the
   21-row table has one row resolvable only by author argument. Recall is 1.000
   either way so no metric moves, but **the gate denominator does** (16 vs 17
   MECHANICAL). *Needed before: Arm M scoring.*

2. **Arm M is not defined anywhere.** Ruling 1 evaluates GATE-H3 "once against
   P25-A"; ruling 4 defers W-PROV-01's score "pending Arm M measurement." But
   v2.0 has no Arm M. Which arm the gate is scored against (mutator-generated,
   LLM-generated, or pooled) is exactly the question that must not be settled
   after seeing the numbers. *Needed before: step 2 of Phase 2.* A2 §3's
   null-control standard also needs its Arm M null specified — for a
   deterministic mutator the natural null is a constant-fire checklist.

3. **The Phase 3 spec (v1.4/v1.6/v1.7) is not in the repo**, and A4 item 2 cites
   its gate values. `GATE7_DECISION.md` quotes the clause it amends, which is
   strong secondary evidence, but a reader cannot fetch the spec that set the
   gate. Either commit it or state the citation route in A4. No ruling covers
   this. *Needed before: A4 drafting.*

4. **`Encoding_Protocol_v0_1.md` does not exist yet.** Expected — INV-2 is its
   feasibility study, and INV-2 now says build it with A7 at 3-5h. But A9's
   disclosure text and D5's escort language both cite it, so it gates two
   manuscript items. *Needed before: D5, A9 text.*

---

## 8. Recommended order

| When | Work | Why |
|---|---|---|
| Today | Phase 1 (all four, ~1h) | Cheapest, and the typing probe can invalidate the mutator bet |
| Today | Phase 0 spec reconciliation (2h) | Execution should read one document |
| Today | Residues 1 and 2 (author call, ~30 min) | Both must precede Arm M scoring |
| This week | Phase 2 steps 1-4 | Critical path; blocks ranks 1-2 |
| This week, parallel | Stage 4 sitting (ruling 11) | Author's own calendar |
| This week, parallel | Ahn & de Weck screen, Bologna read, N=3 admissions | Reading-paced, no dependency |
| After Phase 2 step 4 | A2 manuscript text, D7 ladder, D2 final wording | Ruling 2 binding |
| After D6 measurement | D6 drafting | Ruling 10 binding |

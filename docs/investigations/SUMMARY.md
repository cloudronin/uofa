# Investigation summary — UofA Investigation Spec v1.0

Executed 2026-08-16 against `cloudronin/uofa`, branch
`cloudronin/uofa-investigation-spec-63614d` at `3a4b64c3`.

**Re-investigated the same day against `UofA_Unified_Repair_Spec_v2_0.md`.** Every
findings file now carries a v2.0 addendum ahead of its original text; the original
is retained below a divider so the delta is visible. Where v2.0 changed a verdict,
the addendum says so.

Statuses: OPEN / IN-PROGRESS / CLOSED / ESCALATED / PARTIAL.
An item with any live escalation is ESCALATED, not CLOSED, until the author rules.

| Item | Status | Finding after v2.0 | Live escalations |
|---|---|---|---|
| [INV-1](INV-1-findings.md) | **CLOSED by ruling** | Ruled partition is **17 MECHANICAL / 4 JUDGMENT over 21 base patterns**; GATE-H3's denominator is 17. The 13-of-23 correction to the provisional table stands as the evidence the ruling was taken against | none — W-PROV-01 → MECHANICAL (ruling 4), W-AR-03 → MECHANICAL (addendum A), compounds excluded (ruling 3) |
| [INV-2](INV-2-findings.md) | CLOSED | v2.0's A7 has a field structure, and three of five clauses are already checkable-first. **Clause 5's stopping rule is a derived predicate, not an attestation** — G3 eliminated. Residue 2.5h; total still 3-5h; build with A7 | none |
| [INV-3](INV-3-findings.md) | CLOSED | Last material touch 2026-08-06 → washout ends **2026-08-27** | none; v2.0's "last package touch" wording would give 2026-09-03 — one-line author call. A8 also depends on A7 (no ambiguity log exists yet) |
| [INV-4](INV-4-findings.md) | CLOSED | Extend `uofa diff`, 4-6h. v2.0's A8 states the requirement as *"per-weakener disposition agreement, per label class"* — **exactly the three gaps identified**. Thresholds now pre-committed | none |
| [INV-5](INV-5-findings.md) | ESCALATED | Bologna remains the only viable candidate. v2.0 §A10 assigns it to the **scorecard pool**, making the conflict three-way (A3 × scorecard pool × existing H2 corpus) | Which claim wins. **Relief route: screen Ahn & de Weck for the scorecard pool first** — v2.0 directs it, and success frees Bologna |
| [INV-6](INV-6-findings.md) | ESCALATED | **Catalog clean** (rule logic byte-identical to the freeze). **The (c) list is now empty** — see correction below | Ch4's "thresholds committed before measurement" is not provable from commit order (squashed PR #62), while Phase 3's equivalent claim *is*. A4 will sit both in one table |
| [INV-8](INV-8-findings.md) | ESCALATED | **Two corrections and a bigger finding.** Phase 3 completed (see below). v2.0 removes the judge leg from H3 by author decision. **GATE-H3 is not met: MECHANICAL 72.6% against a ≥95% gate; overall 76.2% against ≥80%** | The gate's own premise ("the holdout supports it") is contradicted by the committed data, and the MECHANICAL class is the *worse* performer. Decide the number **before** P25-A runs |
| [INV-11](INV-11-findings.md) | ESCALATED | Upgraded from "worth it" to **required**: five MECHANICAL patterns score 0.000 and two are unmeasurable, all as generation artifacts. GATE-H3's ≥95% is unreachable with the LLM generator, reachable by construction with the mutator | Fund B2 at 5-7h (not 2-3h), or revise GATE-H3 before measuring |
| [INV-12](INV-12-findings.md) | CLOSED | **C1 already shipped** (`535dfd52`, 2026-08-13). Shared path, emittability enforced by tests, 32 tests pass locally | none — strike C1's 2-4h estimate |
| [INV-13](INV-13-findings.md) | ESCALATED / PARTIAL | **Criterion escalation withdrawn** — v2.0's two-pool split re-qualifies the Frontiers papers, exactly as argued. New problem: **two of the six current documents (morrison, nagaraja) are the two the inclusion rule excludes by name** | The 11-14 target does not close under its own exclusions: base is 4, not 6; reaching 11 needs all 7 screenable candidates. **N in "≥N factors" is still unbound and decides everything** |
| [U-INV-1](U-INV-1-findings.md) | PARTIAL | Both citations verified bibliographically; full texts unreachable (5 routes failed). v2.0 fixes the escort sentence, narrowing what they must carry | Read after the INV-11 decision — if the mutator is not funded, the sentence changes |
| [U-INV-3](U-INV-3-findings.md) | ESCALATED | v2.0 §D6 promotes both contested elements to specified Ch4 text on the **Demonstrated** rung — which requires machine-re-derivability neither currently has | 384 is prose arithmetic; the equality claim's converse is unverified. Reword (0h) or measure (~3h). The invariance framing survives either way |
| [INV-10 residual](INV-10-residual-findings.md) | CLOSED | Re-run list empty. v2.0 confirms the scope verbatim. GATE-H2 adds a **second label** (synthetic/real) to the same pass; A5 adds null columns → 90 min, not 45 | none |

## Phase 2.5a §0.1 falsified this report's typing hypothesis

Recorded in full as [INV-8 addendum 2](INV-8-findings.md). The hypothesis that
W-EP-03 / W-CON-03 / W-AR-04 score 0.000 on mistyped literals is **wrong** — the
context declares all four date properties `xsd:dateTime`. The actual cause is that
the rule's antecedent never binds: 180/180 `w-ep-03` packages carry **zero**
ValidationResults with `wasGeneratedBy`, and 65 of them park datasets under terms
absent from the context, which expansion silently drops.

Worse and more useful: **no substrate can host these mutations either.** Four of the
seventeen MECHANICAL rules — W-EP-03, W-AR-04, W-CON-03, W-AR-03 — read structures no
encoding produced by the project's own protocol ever instantiates, across five packs
and seven example packages. That is a catalog-coverage finding that outranks the
recall number it was meant to unblock, and it feeds v0.6.

Two further Phase 2.5a escalations came from the same check: the assessment stack
runs **SHACL → integrity → derivation pre-pass → rules** (signature verification is
second, not last, and there is a fourth layer the spec does not mention), and
`sign_package`'s `assert_issuable` refuses synthetic documents, so a
re-sign-after-mutation operator **cannot be built** — a positive architectural claim
rather than a gap.

## Two corrections to what I reported earlier

Both stem from one wrong belief — that `dev/build/` was gitignored. It is not:
`.gitignore:41-43` force-tracks `dev/build/adversarial/` and `dev/build/phase2_5/`.
10,103 Phase 2 files, 113 Phase 2.5 files and 60 Phase 3 files are committed.

**1. Phase 3 did run, and the Tier-1 gate passed** (INV-8). Stage 2 completed
2026-07-19 (4,556/4,556 judged by all three); Stage 3 triage completed the same day
with a 21-case disagreement queue (0.5%, against a 9% pilot projection) and
**all 6 of 6 Tier-1 candidates supported**. Stage 4's worksheet is prepared;
the adjudication itself is the remaining step and is "a single sitting." I sourced
the original claim from `PHASE3_STATUS_REPORT.md`, whose own header warns it is a
point-in-time report last updated three days before the work finished.

**2. The Phase 3 gate artifacts are in the record** (INV-6). `GATE7_DECISION.md`
(2026-06-10) carries the amended clause, a drafted Ch3 disclosure paragraph and a
named residual risk; calibration v2-v5 are committed. My recommendation to relocate
them is withdrawn, and category (c) — undisclosed substantive post-freeze changes —
**is now empty across every freeze this audit could locate.**

The upside of the correction is real: the gate decision (2026-06-09 20:24) provably
precedes every Stage 2 execution artifact (2026-07-17 onward). That is exactly the
evidence A4 item 2 needs, and it is the form the H2 ordering claim lacks.

## The finding that reorders the work

Aggregating the committed per-pattern outcomes by INV-1's corrected partition:

| Catalog version | MECHANICAL recall | JUDGMENT recall | Overall |
|---|---|---|---|
| M5 baseline v0.5.7 | 0.5908 | 0.9368 | 0.7343 |
| holdout v0.5.13 | **0.7260** | **0.9160** | **0.7619** |
| holdout v0.5.15.1 (shipped) | **not measured** | **not measured** | **not measured** |

GATE-H3 requires MECHANICAL ≥95%, JUDGMENT and overall ≥80%. **The class the gate
treats as the safe one is the one that fails**, by 22 points, and the overall figure
misses by 4. The gate's justifying parenthetical — "(the holdout supports it)" —
is the premise the data contradicts.

The diagnosis is clean and fixable: every MECHANICAL zero is a *generation*
artifact, not a rule defect. Three value-comparison rules (W-EP-03, W-CON-03,
W-AR-04) need correctly-typed literal pairs the LLM does not reliably produce;
W-SI-02's flaw is SHACL-mandatory and gets validated away; W-ON-01 and W-SI-01 have
never produced a confirm-existing row at any version. **All of them are one-line
deterministic mutations.**

So three items converge on one sequence:

| Step | Work | Cost | Unblocks |
|---|---|---|---|
| 1 | `uofa inject` deterministic mutator over the 15 MECHANICAL patterns (INV-11 §4b) | 4-6h | B2, and the only route to a measurable ≥95% |
| 2 | `uofa detect` + README walkthrough | 1-2h | B2's done-gate |
| 3 | **P25-A: full-battery holdout at v0.5.15.1** (already scoped in `PHASE2_5_STATUS_REPORT.md:46-48`) | 3-5h + ~$50 | GATE-H3, A1's Ch3 scoping, A2's null-control standard, D7's Demonstrated rung |

Ranks 1 and 2 of v2.0's own priority ordering both sit on step 3. It should run
**before** A2's text is written, or the Ch3/Ch4 numbers get written twice.

## Cross-cutting notes

**A version-mismatched pair the manuscript currently makes.** "CE recall 73.4%,
NC clean 97.1%" pairs a v0.5.7 recall with a v0.5.15.1 specificity.
`PHASE2_5_STATUS_REPORT.md:34` says so directly. A2 §3's own new null-control
standard forbids it. One measurement at one version fixes it — the same P25-A.

**Two two-word fixes, before D6 drafting.** `datasetcard_info.parquet` →
`modelcard_info.parquet` in
`docs/model-credibility-pack-addendum-v0_5-taxonomy-validation.md:32` and
`studies/taxonomy-validation/frame.py:4`. The pre-registration explicitly corrected
this; ten other artifacts carry the corrected name; these two were missed, and one
is the script that computes the frame.

**Two spec artifacts still absent from the repo.** `Encoding_Protocol_v0_1.md`
(A7, expected — INV-2 is the feasibility study for it) and the **Phase 3 spec
v1.4/v1.6/v1.7**, whose gate values A4 item 2 will cite. `GATE7_DECISION.md` quotes
the clause it amends, which is strong secondary evidence, but the spec that set the
gate is not fetchable by a reader.

**What no finding changed.** No frozen artifact edited, no code modified, no
parent-spec decision acted on. Where a finding would change a decision, it stops and
reports.

## Author decisions — all twelve ruled

`docs/UofA_Decision_Record_2026-08-16.md`, committed alone at **`fad31cf5`** with two
dated addenda. A4 cites the commit, not the path — the record sat untracked until
then, and an untracked file carries an mtime, not a commit date, which is the same
defect INV-6 §4 found in the Ch4 H2 claim.

| # | Decision | Ruling |
|---|---|---|
| 1 | Mutator vs gate revision | **Fund the mutator**; GATE-H3 held as set. Phase 2.5a spec issued |
| 2 | P25-A timing | **Before any A2 manuscript text** |
| 3 | Compounds in partition | **Excluded**; classes and gates scope to the 21 base patterns |
| 4 | W-PROV-01 class | **MECHANICAL**; `isFoundationalEvidence` is a structural declaration |
| 5 | `sh:in` vocabularies | **Deferred to v0.6**, post-defense, as a disclosed increment |
| 6 | A10 inclusion-rule N | **N=3**, committed before any admission |
| 7 | Morrison/Nagaraja in H2 corpus | **Reclassify, not delete** — labelled development documents; headline metrics report the held-out papers |
| 8 | Bologna assignment | **Conditional** on the Ahn & de Weck scorecard screen; A3 gets Bologna either way |
| 9 | Ch4 H2 ordering claim | **One recovery attempt** on PR #62 pre-squash refs; if unrecoverable, reword to what the record proves |
| 10 | D6 contested numbers | **Measure** (~3h), both directions of the equality claim |
| 11 | Phase 3 Stage 4 sitting | **Now**, author's calendar, parallel to 2.5a |
| 12 | A8 washout clock | **Conservative: 2026-09-03** (last touch of any kind) |
| A | W-AR-03 class *(addendum)* | **MECHANICAL** — partition is 17/4, gate denominator 17 |
| B | GATE-H3 enrichment split *(addendum)* | Gate evaluates on the **full battery**; as-encoded vs enrichment-required reported alongside as the ecological-validity result |

## Open actions that need no decision

| Action | Effort | Item |
|---|---|---|
| Open 2-3 failing `…w-ep-03…` generated packages and check the `dataVintage` literal datatype — confirms or kills the typing hypothesis before the mutation table is written | 15 min | INV-8, INV-11 |
| Screen Ahn & de Weck first — it can relieve the scorecard pool *and* count toward the annotation pool | 1h | INV-5, INV-13 |
| Read the Bologna PDF for its decision record and required-vs-achieved levels | 1h | INV-5 §3 |
| Fix the two `datasetcard_info` references | 5 min | INV-6, U-INV-3 |
| Label the 11 bucket-2 extraction citations (raw/adjudicated **and** synthetic/real), adding null columns where A5 requires | 90 min | INV-10 residual |
| Confirm the deployed HF Space revision includes `535dfd52` and has `UOFA_DEMO_SIGNING_KEY` set | 15 min | INV-12 |
| Read Jia & Harman §1-2 and Hsueh et al. §1-2 behind the library proxy — after decision 1 | 20 min | U-INV-1 |
| Commit the Phase 3 spec, or state in A4 that its gate values are cited via `GATE7_DECISION.md` | — | INV-6 |
| Read `src/uofa_cli/eval_scoring.py` to harden the no-adjudication-stage conclusion | 20 min | INV-10 residual |

## Investigations opened after the spec

Not part of `UofA_Investigation_Spec_v1_0.md`; raised by Phase 2.5a and indexed here
so they are findable from one place.

| Item | Status | Finding |
|---|---|---|
| [INV-14](INV-14-analyze-pointer-fix.md) | **LANDED** (`548224d1`) | `analyze` produced zero rows on every committed corpus — stale `out_dir` pointers from two renames, 510/510 specs. Re-anchoring on `--in` fixes all three corpora and touches nothing frozen. Carries a self-correction: the "silent exit 0" I reported does not exist; `\| tail` was swallowing the status |
| [INV-15](INV-15-m5-scale-and-phase3-gap-probes.md) | CLOSED | The M5 scale gap is closed (66 specs, 330 packages, 0 skipped). Four rules fire on 329/329 gap probes, and Phase 3's 6-of-6 Tier-1 result survives it — the judge schema forced the confrontation, 0/288 empty. §4 carries the W-AR-05 case as chapter material |
| [INV-16](INV-16-nc-trajectory-decomposition.md) | CLOSED | The 0% → 97.1% NC trajectory decomposed over all four corpus×catalog cells: **rule refinement alone 4.5 points, regenerated corpus alone 0.0 points, 97.1% only where both are present** — each axis blocked by a rule the other fixes. Every rule the 2026-04 record labels a predicate fix went to zero; every rule it labels corpus regen is unchanged to the decimal. Both reproduction cells reproduced their committed figures exactly, and one sentence of the first version was falsified and is corrected in place |

| [INV-17](INV-17-prose-versus-property-count.md) | CLOSED | **The W-AR-05 case is not a single instance.** Across 14,659 judgments the prose-versus-property split recurs in **roughly 200 cases** (332 candidates, 60% hand-verified precision, 95% CI [141, 250]), in every absence-checking rule family measured; W-AR-05 is the most frequent at 104 cases. Two methodological traps recorded: six rules are *defined* as "X present but Y absent" so a presence match restates their precondition, and a first pass compiled its regex with `re.X`, silently killing every multi-word marker |
| [INV-18](INV-18-w-con-02-scope.md) | OPEN | **W-CON-02 reads one optional field and misses every load-bearing one.** The reference-resolution rule inspects only `uofa:referencesIdentifier`; `bindsRequirement`, `bindsModel`, `bindsDataset`, `wasDerivedFrom` and `wasAttributedTo` are outside its scope. In the adjudicated package 8 references dangle, the rule flagged 1, and that one resolves (HTTP 200) while the seven it ignored do not. Not a synthetic-data artifact: **every IRI reference in every canonical example dangles** (morrison-cou1 7/7, nagaraja-cou1 7/7) | open — applying the rule's own resolvable-or-hinted logic to all IRI-valued properties would fire on 100% of shipped packages, so the severity gradient is an author call, not a measurement |
| [INV-19](INV-19-requirement-layer-absent.md) | OPEN | **Requirement content has nowhere structured to live.** `uofa:Requirement` is a declared class with **zero declared properties**; `specification` — the field the whole corpus uses — is declared in neither the vocabulary nor the context, and expands into an undefined `uofa:` IRI via `@vocab`. Same for `acceptanceThreshold`, `comparisonValue`, `quantityOfInterest`; `OperatingEnvelope` and `ApplicabilityConstraint` are equally empty. Consequence: weakener analysis can check whether an assessment was adequately conducted, never whether the model meets its requirement | open — proposal at [UofA_Requirement_Layer_Spec_v0_1](../UofA_Requirement_Layer_Spec_v0_1.md); four questions unruled, quantity identity is the load-bearing one |
| [INV-20](INV-20-rq1-schema-adequacy.md) | OPEN | **The Stage 4 adjudication is answering RQ1, not the catalog-coverage question it was built for.** Bounded but negative: UofA captures the credibility *assessment* (factors, gradations, decisions, provenance, integrity — works across 4,556 packages) and **not the assurance case** (the requirement, its constraints, the argument connecting evidence to conclusion, the quantity identity linking them). INV-18 and INV-19 are the same gap at two depths, with a third beneath: no inference element, so `WeakenerAnnotation` — defined as *"a condition under which the stated evidence does not support the claim"* — has nothing to attach to | open — discovered not hypothesized, and it does not retire the ensemble readouts; those need the adjudication finished, and matter more under this finding |

## Method note

Every findings file ends with a coverage statement naming what was searched, with
which terms, and what was not. Search terms were derived from each claim's own
definition rather than from where the thing was last seen.

The re-investigation is itself the cautionary case. My original INV-8 and INV-6
findings rested on a committed status report rather than on the artifact tree,
because I had concluded the tree was gitignored without checking the ignore rules.
The report was accurate when written and stale by three days. **Reading
`.gitignore` — nine lines — would have prevented both errors**, and the corrected
findings are materially better news than the originals: Phase 3 completed with its
Tier-1 gate passed, and the undisclosed-change list is empty.

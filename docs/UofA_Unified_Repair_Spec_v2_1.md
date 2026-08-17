# UofA Unified Repair and Response Spec v2.1 (Consolidated, Queue-Organized)

Status: ACTIVE
Date: 2026-08-16
Owner: Vishnu Vettrivel
Supersedes: v2.0 and all earlier repair/update/prose-kit specs. Self-contained; no prior spec required to execute, though two child specs are referenced as the machines-queue work orders: UofA_Phase2_5a_Spec_v1_3.md and the session-2 brief (UofA_Decision_Record_2026-08-16.md + investigation SUMMARY.md).

v2.1 delta from v2.0: (1) reorganized from workstreams into the three execution queues (Machines / Calendar / Writing) so the spec answers "what runs next" directly; (2) all 2026-08-16 investigation findings folded in: C1 shipped, Phase 3 completed with Tier-1 gate passed, undisclosed-change list empty, GATE-H3 unmeasured at the shipped catalog and pending P25-A, partition corrected to 21 base patterns; (3) all twelve author decisions ruled and incorporated (see Decision Record); (4) Phase 2.5a (deterministic mutator + P25-A) added as the machines-queue centerpiece; (5) substrate ruling: mutation runs on every distinct encoded package (both Morrison COUs, both NASA HPT configurations, Nagaraja), with delta-from-baseline scoring for substrates whose unmutated baseline legitimately fires.

**Amended at commit time, 2026-08-16 (session 2).** Six corrections applied before this document was first put under version control, each traceable to an artifact that landed after v2.1 was drafted: (1) §0.1 GATE-H3 now carries the measured context it was held above, the ruled 17/4 partition table, and the pre-committed enrichment-split treatment; (2) the mutator scope is corrected from "21-pattern MECHANICAL set" to **17** — 21 is the base partition, and the error would have put the four JUDGMENT patterns into a manifest-scored mutation battery; (3) the step-0 typing check is marked RUN and FALSIFIED, since as written this document would have had session 1 re-run it; (4) the operator classes are restated as Class A / Class B (MUT-ANT), the MUT-TYP family deleted and MUT-INT-02 dropped as a finding; (5) the layer-attribution stack order is corrected to the verified four-layer order; (6) the A4 entry drops the "if the spec file is not committed" fallback, because the Phase 3 specs are now committed. Sources: `docs/UofA_Decision_Record_2026-08-16.md` addenda A and B (committed alone at `fad31cf5`), `docs/investigations/INV-8-findings.md` addendum 2, and the decision-9 recovery attempt.

Governing input: Fossaceca/Sarkani letter of 2026-08-11 ("solid and can move forward," five must-haves before defense). Program constraint: no contributors other than the author.

Execution: author + Claude Code sessions 1 and 2 + Mohammad (grammar-in-place only, after content stabilizes; re-synthesizing passes banned) + Turman (thesis and hypothesis wording review).

---

## 0. Must-have coverage map

| Must-have | Covered by | Status |
|---|---|---|
| 1. Replace LLM-as-judge with injected flaw testing | Phase 2.5a (mutator, P25-A), W1-A2 prose, W8 | Instrument being repaired; judges already demoted by decision; prose waits on P25-A report |
| 2. Tools that hide the complexity | Credibility Inspector (live, uofa.net/demo); pack download SHIPPED at 535dfd52 | **Deploy check CLOSED 2026-08-16** — see below. Remaining: W5 manuscript rendering only |
| 3. Simplify the hypotheses | W2, gates final (§0.1) | Unblocked, writing queue position 2 |
| 4. Preliminary framing, prototype language, open source | W3 | Unblocked, position 3 |
| 5. Human reviewer role and bias | W1-A7 protocol, W6 disclosure, Inspector confirm-step artifact | Protocol is writing-queue position 1 |

### 0.1 Gates (final, author-set, disclosed)

Recorded with rationale in the Decision Record (2026-08-16), dated before the measurements they govern; both entries reproduce in the A4 appendix.

**GATE-H3** (held, decision 1): MECHANICAL ≥95%, JUDGMENT ≥80%, overall ≥80% detection of injected flaws; FP <10% per class. Evaluated ONCE against P25-A at v0.5.15.1; misses reported with root cause, catalog not patched inside the phase (fix-and-remeasure is a disclosed v0.6 event).

*Measured context, disclosed because the gate is held above it.* The best committed measurement is the v0.5.13 holdout: **MECHANICAL 72.6%** against the ≥95% gate, **overall 76.2%** against ≥80% (JUDGMENT 91.6% clears). The shipped catalog **v0.5.15.1 is unmeasured** in all three columns. The gate is held rather than revised because every MECHANICAL zero is diagnosed as a generation artifact, not a rule defect (INV-8/INV-11); Phase 2.5a's deterministic mutation arm is what makes ≥95% reachable by construction. The gate's v2.0 justifying parenthetical — "(the holdout supports it)" — is withdrawn: the holdout does not support it, and saying so is the point of recording this here.

*Scope: the 21 base patterns* (compounds excluded, decision 3; reported separately as composition results). Partition per the corrected INV-1 table as ruled — W-PROV-01 MECHANICAL (decision 4) and W-AR-03 MECHANICAL (Decision Record addendum A); both on one criterion, re-derivability of the label as the rule exists at v0.5.15.1, not the measured score:

| Class | n | Patterns |
|---|---|---|
| MECHANICAL | **17** | W-EP-01..03, W-AL-01..02, W-ON-01..02, W-AR-03..05, W-SI-01..02, W-CON-02..05, W-PROV-01 |
| JUDGMENT | 4 | W-EP-04, W-AR-01, W-AR-02, W-CON-01 |
| Excluded | 2 | COMPOUND-01, COMPOUND-03 (`label_class = COMPOSITE`/null) |

**GATE-H3 is evaluated over 13** (Decision Record addendum F). The 17 is the *partition* size, which scopes the mutation battery and per-class coverage; it is not the gate denominator. Four exclusions, each named, mechanism'd and dated before scoring:

| Step | n | Excluded | Ground |
|---|---|---|---|
| MECHANICAL partition | **17** | — | Scopes the battery |
| less unfireable-as-shipped | 16 | W-EP-01 | Guard names `uofa:Claim`, a class the schema never declares. **Discovered catalog defect** |
| less architecturally unreachable | **13** | W-SI-01, W-ON-01, W-SI-02 | Deleted fields carry `sh:minCount`; the completeness profile intercepts before C3 runs. **Unreachable at the rule layer in a conformant pipeline** |

A defect the schema intercepts is not a rule-engine miss — it is the completeness layer working upstream. Scoring those three as zeros would make the gate measure the architecture's layering rather than the catalog's detection, and a gate that cannot mathematically pass regardless of rule quality is a foregone conclusion wearing one.

**Two conditions attached, so this is not gate-softening.** The three deletion mutants are still built and still reported, in a schema-caught table **beside** the rule-layer table, so total cross-layer detection is visible and nothing appears quietly dropped. And the A4 entry states the arithmetic plainly — denominator 13, **what the 16-version would have scored**, and why 13 is the honest framing.

The ≥95% itself is measured on **defect instances** per A5's effective-n rule; pattern count and instance count are both live and are not interchangeable.

*Enrichment-split treatment, pre-committed (Decision Record addendum B).* The full battery — Class A (edit a field the substrate already has) plus Class B (antecedent instantiation + violation) — evaluates GATE-H3, because the gate's question is unit detection: does the rule fire when its precondition is present and violated. The as-encoded vs enrichment-required split is **reported alongside as an ecological-validity finding, not folded into the gate arithmetic**.

**GATE-H2**: detection F1 ≥0.85 with required margin over the run's own null (a constant checklist reaches 0.95; passing on a measure the manuscript's own null disowns repeats the "proves nothing" pattern), plus attribution above the permutation null at a stated multiple. Raw AI performance only; adjudicated figures reported separately as ceiling. Reported per corpus: 50-bundle synthetic set and the real annotated corpus.

**H1** (unchanged): ≥90% completeness, ≥95% SHACL pass, 100% signatures valid.

### 0.2 Standing decisions incorporated (Decision Record 2026-08-16)

1 mutator funded, gate held; 2 P25-A before A2 prose; 3 compounds excluded; 4 W-PROV-01 MECHANICAL; 5 sh:in deferred to v0.6; 6 A10 inclusion N=3, committed before admissions; 7 Morrison/Nagaraja reclassified as development documents in the H2 corpus (headline = held-out papers, with-development sensitivity row); 8 Bologna conditional on the Ahn & de Weck scorecard screen, defaults to A3 external negative; 9 one PR #62 recovery attempt then reword; 10 D6 numbers measured (~3h script), both directions of the equality claim; 11 Stage 4 sitting this week; 12 A8 washout clock 2026-09-03 if elected.

### 0.3 Pre-meeting materials (send now)

1. Credibility Inspector link (uofa.net/demo): must-have 2, live today, pack download included.
2. ~~NAFEMS CLI reproduction page (uofa.net/demo/nafems)~~ **PULLED from the send list** until the correction pass lands — see §0.3a. Send two solid items rather than three with a known error.
3. One paragraph previewing the injected-flaw reframe: ground truth is the injection manifest; a deterministic mutation arm is being added that implements the prescribed test literally.

### 0.3a NAFEMS page correction pass (session 2, after the mutation report lands)

The page carries two independent defects, and it is the **single most reproducible artifact the committee has been pointed at** — which is exactly why it cannot go out as-is. Ruled: the link drops from the send list, and the fix becomes a queued task rather than an open flag.

| # | Defect | Fix |
|---|---|---|
| a | The HPT step (`nafems.mdx:138-142`) tells a reader to run `uofa rules` against two files holding only stored `WeakenerAnnotation` nodes and no `UnitOfAssurance`. The 17 and 20 it prints are **read-backs, not detections** — presented directly after a section where the same command genuinely detects. The source table (`:154`) calls them "HPT blade JSON-LD — Hand-authored"; the published site renders them as "The UofA package node …" | Correct the read-back: either drop the step or relabel it as displaying stored annotations, and fix the site's package-node rendering |
| b | The published "COU 1 = 11 weakeners across 5 patterns, COU 2 = 18 across 6" figures are committee-facing reproduction numbers, and **9 of COU 1's 11 are vacuous** — bare-IRI validation results make three `noValue` rules fire on every result (§A3) | **Restate from re-measured baselines.** Not fixable by relabelling: the count is correct and the command reproduces. Report the figure with its composition, or use a different figure |

**Sequenced after the mutation report** because (b)'s replacement numbers should come from the same re-measured baselines the report establishes, not from a second independent measurement that could disagree with it.

### 0.5 C1 deploy verification (closed 2026-08-16)

Must-have 2's pack download is verified **in production**, not merely shipped. Three independent checks, recorded because "the code is committed" and "a committee member gets a package" are different claims:

1. **Deployed code carries C1.** `space/pipeline.py` fetched from the running Space; `SIGNING_KEY_ENV`, `UOFA_DEMO_SIGNING_KEY` and `UOFA_DEMO_SIGNING_KEY_FILE` all present, and the signing-key handling is **byte-identical to local HEAD**.
2. **The control exists in the live UI.** The running Gradio config carries the `Download UofA package` component.
3. **The signing secret is set.** `UOFA_DEMO_SIGNING_KEY` confirmed in the Space's secrets, last updated 2026-08-13 — the same day as `535dfd52` (C1) and `09d19eeb` (research-key rotation), which is a consistent story rather than a coincidence.

**Why check 3 was not optional.** `pipeline.py:705` is explicit: *"A missing key is not an error: the Space degrades to the unsigned readout it has always shown."* With the secret unset the function returns `(payload, None)` and the download control simply does not appear — no error, no warning, nothing a visitor or the author would notice. So an unset secret is **invisible from outside**, while §0.3 sends the committee that link described as "pack download included." A silent-degradation path on a must-have deserves a positive check, not an inference from the deploy date.

### 0.4 Open asks

OPEN-2 (Turman): is a live demo (Inspector and/or inject-and-detect walkthrough) expected at the defense itself? Defense-prep calibration only; nothing builds on the answer.

---

## QUEUE 1: MACHINES (Claude Code; author reads escalations only)

### Session 1: Phase 2.5a (work order: UofA_Phase2_5a_Spec_v1_3.md)

Closes Phase 2.5's measurement debt: MECHANICAL-class recall was measured against a corrupt denominator (LLM generation failed to mechanically realize typed-literal and structural flaws; five patterns at 0.000 as generation artifacts, per INV-8/INV-11). Sequence, gates between steps per the child spec:

1. **Step 0, typing check — RUN 2026-08-16, diagnosis FALSIFIED.** Recorded in `docs/investigations/INV-8-findings.md` addendum 2. Typing is correct: the v0.5 context declares the date fields `xsd:dateTime`, so Jena's comparisons work. The real cause is that **the rules' antecedents never bind** — 180/180 committed `w-ep-03` packages carry zero ValidationResults with `wasGeneratedBy`, and 65/180 park datasets under terms absent from the context, which expansion silently drops. The escalation fired and is resolved by the redesigned operator classes below; **do not re-run this check**.
2. **Mutator (`uofa inject`):** deterministic mutations over the **17-pattern MECHANICAL set** (the 21-pattern figure is the *base* partition, not the MECHANICAL count — see §0.1). Two operator classes per the falsification, split as **measured** by the step-1 precondition inventory (`studies/phase2_5a/PRECONDITION-INVENTORY.md`, `fed5a37e`) rather than as projected: **Class A**, single edit to a field the substrate already has, **9 patterns**; **Class B (MUT-ANT-\*)**, antecedent instantiation plus violation, two edits carrying one fault, **8 patterns**, each mutant flagged `enrichment: true` so the rollup can be split. The enrichment family doubled against plan — a standing scope escalation the author resolves, not the implementation. Two rule findings ride on it: W-EP-01 cannot fire on schema-conformant evidence (its guard names a class the schema never defines), and W-ON-02 already fires on all three case studies, so its recall needs an enrich-to-clean operator. The MUT-TYP datatype family is **deleted** — it was built on the falsified theory. MUT-INT-02 is **dropped as a finding**, not worked around: the issuer path refuses to sign synthetic packages, which is the positive architectural claim that the production signing path cannot produce a fraudulent-but-valid package. Manifest derived from the canonical diff, never operator intent; liveness check excludes canonicalization-erased mutants from the denominator; mutants load through the production path (emittability rule).
3. **Substrates (ruled):** every distinct encoded package: Morrison COU1 and COU2, NASA HPT take-off and cruise, Nagaraja. Substrates with non-zero legitimate baselines (COU2, cruise) are scored on the DELTA from their baseline detection set, testing that the injected finding appears on top of existing findings without disturbing them.
4. **Layer attribution:** every mutant runs the full stack in production order, verified against `commands/check.py` as **C2 SHACL → C1 Integrity → C2.5 Derivation pre-pass → C3 Rules** — signature verification runs *before* the rule engine, and the derivation pre-pass is a fourth layer earlier drafts omitted. Detection recorded per layer (`shacl | integrity | derivations | rules | none`), with the report stating where the pre-pass was a no-op; recall scored at package-assessment level, reported per layer. SHACL-mandatory flaws (W-SI-02 class) additionally get the below-SHACL variant or the positive architectural finding ("cannot reach the rule layer in a conformant pipeline").
5. **CLI + walkthrough (B2):** `uofa inject / detect / inject-verify`, fresh-clone README walkthrough with the three letter-named demos (remove uncertainty, change version numbers, remove signatures).
6. **P25-A at v0.5.15.1, two arms:** Arm M (mutation battery, manifest ground truth, MECHANICAL primary) + Arm G (180-package holdout and Phase 2.5 battery rerun, JUDGMENT primary, NC clean rate re-measured, killing the manuscript's version-mismatched 73.4%/97.1% pair). Null controls on every headline number (fire-on-everything, fire-on-nothing, base-rate-matched random). Wilson CIs, per-pattern n in every row.
7. **REPORT (studies/phase2_5a/):** per-pattern table both arms, equivalent-mutant log, gate evaluation (once), generator-vs-mutator delta with interpretation column, version-consistent recall/NC pair. Writing-queue position 8 consumes this.

Budget 9-13h paired + ~$50. Scope cap and five escalation criteria per child spec; kill criterion: 21 patterns, single-fault, five substrates, no operator research, no catalog edits.

### Session 2: follow-up batch (brief: Decision Record + investigation SUMMARY)

| Item | Task | Feeds |
|---|---|---|
| A10 admissions | Apply committed rule (N=3, reader-pathology screen, Morrison/Nagaraja/NASA excluded as new admissions) to the screened candidates; produce the admission list | Writing-parked annotation |
| Ahn & de Weck read | Screen for scorecard pool (transcribable CAS table for SpaceNet?) and annotation pool | Decision 8 resolution; Bologna release |
| Bologna read | Decision record and required-vs-achieved levels; assign to A3 external negative per decision 8 | A3's external clean package |
| D6 measurement script (~3h) | Re-derive 384/427 from committed artifacts; verify the equality claim BOTH directions (every cleared result carries stated uncertainty AND converse) | Writing position 8 (D6 sections) |
| PR #62 recovery | One attempt (refs/pull/62/head, reflog); success or reword recommendation | Writing position 8 (A4 appendix) |
| Small fixes | ~~Two datasetcard_info → modelcard_info references~~ **DONE** (`ca24187f`); bucket-2 extraction citations labeled raw/adjudicated AND synthetic/real with null columns (90 min); ~~HF Space deploy check~~ **DONE** — see §0.5 | Hygiene; A9; C close-out |
| B4 register script | Banned-register (fail) + prose-tic (warn) sweep over exported manuscript text | Writing positions 9-10 |
| U-INV-1 reads | Jia & Harman §1-2, Hsueh et al. §1-2 via library proxy; extract the supporting sentences with page numbers | Writing position 7 (D4 escort citations) |

### Machines-queue status (from the 2026-08-16 investigation)

CLOSED and standing: C1 pack download shipped (535dfd52; shared path, emittability enforced by tests). Phase 3 completed: Stage 2 4,556/4,556 judged, Stage 3 triage done (21-case queue, 0.5% disagreement), all 6 Tier-1 gap-probe candidates supported; Stage 4 is the calendar-queue sitting. Undisclosed post-freeze change list EMPTY across every locatable freeze; catalog rule logic byte-identical to the freeze; Phase 3 gate decision (2026-06-09) provably precedes Stage 2 execution (2026-07-17+), which is exactly the evidence form the A4 appendix presents. Known evidentiary asymmetry for A4, **updated after the decision-9 recovery attempt ran**: PR #62's pre-squash history *is* recoverable (`refs/pull/62/head` at `ce46c17b`, fetched and pushed durable as `refs/uofa/pr62`), so the history is not lost — but it does not prove the ordering claim, because commit `1abbf8d6` contains the threshold declaration, the re-score script and the results together. A4 therefore presents **three** evidentiary strengths, not two: *provable* (Phase 3's gate decision precedes Stage 2 execution by five weeks in commit order; the 2026-08-16 ruling record committed alone at `fad31cf5` before the run it governs), *attested* (H2's thresholds, declared and self-labelled "NOT YET MEASURED" in the same commit as their measurement), and *recorded-before-the-governed-event*. Ch4's H2 sentence is reworded to "declared before measurement and recorded as such."

---

## QUEUE 2: CALENDAR (author, booked once)

**Stage 4 sitting, this week.** 21 disagreement cases, worksheet prepared, one sitting. Closes Phase 3 entirely; adjudicates whether Tier-1 gap-probe candidates confirm REAL-GAP; fills the Ch4 §4.4.4 placeholder; confirmed gaps are named as the v0.6 catalog increment in future work (patterns are NOT added now; v0.5.15.1 stays frozen through P25-A).

---

## QUEUE 3: WRITING (author + Mohammad + Turman; strictly one position at a time)

Rule: finish position n, take n+1. One branch only: if a machines output hasn't landed when position 8 opens, do position 9's preparable parts and return.

### Position 1: A7 Encoding Protocol (4h) — two items queue behind it

Encoding_Protocol_v0_1.md, published as praxis appendix and in the repo:
1. Source-evidence intake rules; citation anchoring (every encoded assertion cites page/section/table).
2. Ordered extraction passes: context of use, model description, V&V activities, results, applicability; per pass, entities instantiated and mandatory fields.
3. Disposition procedure: per weakener class, testable Accepted / Not Accepted / Not Applicable criteria referencing source text; untestable criteria mark the pattern JUDGMENT.
4. Mandatory ambiguity log (entry per underdetermined field: ambiguity, resolution, rule applied).
5. Stopping rule: complete when all mandatory fields populated or logged source-absent. Write clauses checkable-first: INV-2 found three of five clauses already mechanically checkable and the stopping rule expressible as a derived predicate; `uofa protocol-check` builds with this document (2.5h residue, machines queue after protocol lands).

**Done-gate:** published and tagged; citable from position 6.

### Position 2: D2 Hypotheses + A5 Metrics Specification (5-7h)

D2: the letter's three plain sentences adopted nearly verbatim as hypothesis statements, each with its §0.1 gate attached; technical operationalization (COV-HIT taxonomy, factor definitions) moves to methodology, referenced not inlined. RQ register fix: "standards-aligned (traceable to ASME V&V 40 and NASA-STD-7009B credibility factors) and machine-verifiable," never "regulatorily credible"; RQ2/RQ3 swept. Original and revised wording recorded side by side for the A4 appendix. Turman review.

A5: the single pre-results metrics table: detection rate per pattern per class on defect instances; Wilson 95% CIs where n<100; Cohen's κ per class, never pooled; the F1 definition as documented with nulls in ch4-h2-section; null controls on every headline metric (constant-checklist detection null, permutation attribution null, fire-on-nothing NC null); effective n = defect instances (H3) / factor-document pairs (H2); the three gates; no hypothesis tests unless pre-specified. Sweep existing text for conformance; recompute nonconforming metrics with A4 disclosure.

**Done-gate:** hypotheses are one plain sentence + gate each; table merged before any results section; Turman sign-off.

### Position 3: D1 Thesis + D3 Non-claims Box + D9 Ch5 (3.5h)

D1, §1.4 restructure: (a) UofA definition sentence; (b) weakener definition, Pollock lineage; (c) thesis sentence: "This praxis develops and evaluates a standards-mapped, machine-readable evidence package and rule catalog, with a documented coverage methodology validated against four published defeater taxonomies, that detects specified structural, provenance, and integrity defect classes in computational modeling and simulation evidence."; (d) C1/C2/C3 one paragraph each, the colon delivering them in order. Repair the garbles ("SHACL constraint shapes"; C2 sentence; CI/CD analogy rewritten or cut). Keep the SSP-LS humility passage. Closing sentence: "a prototype and proof of concept," their words.

D3, boxed and visually distinct at §1.7 end / §1.8 head: "This praxis makes no claim of regulatory acceptance, endorsement, or submission-readiness. The claim is narrower and structural: regulated domains require credibility arguments that are today prose-borne and manually audited; this work demonstrates a mechanism that renders such arguments machine-checkable, mapped to the published standards those domains already use (ASME V&V 40, NASA-STD-7009B, FDA 2023 CM&S guidance). Whether any regulator accepts machine-checkable evidence of this form is an empirical question for future work and is not asserted here." Adjacent: "The validation reported here is preliminary; real-world validation with human experts is essential future work." and "The system is released open source (github.com/cloudronin/uofa) to enable community validation." Abstract references the box.

D9: two-page Ch5 skeleton, DRAFT-marked: contributions on the claims ladder, limitations pointer, future work (multi-encoder replication, second-annotator agreement, regulatory acceptance, expert-panel validation, prose-path validation, v0.6 increment from Stage 4, domain packs). Placeholder title gone from every circulating copy immediately.

**Done-gate:** §1.4 parses on read-aloud; box renders distinctly; no placeholder Ch5 title anywhere.

### Position 4: E Tier A + Tier B Prose Repair (4-6h, author-only; claim repairs, not style)

Tier A, ten meaning inversions, each read aloud after patching: "excessively written"→"overwritten"; "workflow simulation"→"simulation workflow"; the VICTRE double negative→"provides no evidence package: no provenance graph, no SHACL-enforceable completeness check, no tamper detection"; "real-time"→"real-world" with the test stated; "SHACL obstacle constraints"→"SHACL constraint shapes"; the unparseable §1.2 sentence→"Publicly accessible instances of complete credibility assessments for FDA CM&S submissions are far fewer than the use cases that rely on them"; "experts eventually fixed via CI"→"software teams eventually solved with continuous integration"; "standards ensure robust models"→"standards define how that defensibility is established"; "lifetime cycle" sentence→"the field has not yet treated the resulting evidence as an engineering artifact with its own lifecycle"; the §1.8 run-on→"Results are specific to the encoded case studies. Tier coverage spans single-CoU and multi-CoU configurations; broader domain coverage is future work."

Tier B: drop-in rewrites of §1.1-§1.3 per the Prose Repair Kit text (background, problem-statement skeleton with CI analogy and three failure categories, §1.3 targeted repairs); diff after insertion for silently lost citations or claims. Process directive: condensation/paraphrase re-synthesis banned from all future passes; polish means grammar in place.

**Done-gate:** author read-aloud of Ch1 end to end, zero sentences requiring a second read.

### Position 5: C2 Inspector Manuscript Rendering (1-2h)

Ch3 subsection: the Inspector as the usability layer, in the letter's vocabulary (complexity hidden behind upload-and-confirm; semantic web invisible). Ch4: screenshots of the flow including pack download (shipped). One sentence connecting the confirm step to position 6's adjudication disclosure. Every UI claim matches the live demo at the pinned site commit; cold-start note in any committee-facing walkthrough.

### Position 6: A9 Human Adjudication Disclosure (2-3h; consumes position 1)

Ch3 subsection "Human Adjudication Role": all adjudication by the author; program constraint precludes independent reviewers; mitigations are the published protocol (position 1), the label-class partition confining author judgment to the JUDGMENT class, the Inspector confirm step as the visible artifact of where judgment enters, and A8 if elected. Every affected metric split raw vs adjudicated, plus the synthetic/real label (bucket-2 list from machines queue); never blended; GATE-H2 applies to raw only. Two reconciliations: the second-annotator relief sentence rewritten to program-constraint attribution with second-annotator agreement as protocol-enabled future work; the claim-density 0.000 finding (96 well-formed rationales, zero checkable quantities) promoted to Ch1 motivation, since prose-borne unverifiable evidence is the thesis demonstrated by the study's own extractor.

### Position 7: D4 Skim-Hardening (3h; escort citations from machines queue)

Two-arm validity figure in Ch1 (constructed ground truth via defect injection × published-case anchors × negative controls; caption: each arm covers the others' weakness; no arm depends on author opinion for ground truth; injected-flaw testing named as the constructed-ground-truth arm, now with the mutation arm making it literal). §1.2 corpus-absence sentence: "No adjudicated corpus of assurance defects in CM&S evidence packages exists. This absence is simultaneously the gap this praxis addresses and the reason its validation must construct its own ground truth: a first instrument cannot be calibrated against an instrument that does not exist." A10's measured-scarcity paragraph adjacent with its denominator. §3.1 Validity Strategy pointer to §3.10. Escort rule for "synthetic": first mentions become "constructed ground truth via defect injection into published-case substrate, following the fault-injection and mutation-testing tradition," citing Jia & Harman and Hsueh et al. per the verified extracts.

### Position 8: The Results Cluster (consumes machines outputs; 8-10h)

Opens when the P25-A report, D6 script results, and PR #62 outcome have landed. If one is missing, do position 9's preparable parts and return.

**A2 Injected-Flaw Validation prose:** judges demoted to realism screening everywhere (already ruled; INV-8's removal/relabel/prose-defect lists give the exact locations); ground truth stated as the injection manifest early and explicitly; the flaw-to-pattern mapping table (their named flaws → W-AL-01, W-CON version rules, W-PROV-01/signature → the operators that exercise them); detection numbers from P25-A only, per class, each beside its null; the generator-vs-mutator delta table with interpretation; Stage 5 gap-probe judge role clearly distinguished from ground truth (relabel, not removal).

**A3 Negative-controls reporting:** FP table per pattern per class from P25-A's zero-injection arm (clean substrates + Bologna external negative when encoded); falsification framing explicit; CI fixtures noted.

> **Binding precondition — settle before Bologna is encoded, because re-encoding is the expensive way to find this out.** W-AL-01, W-AR-05 and W-EP-02 all test `noValue(?result, <property>)` on a ValidationResult. Where a package references its results as **bare IRIs** rather than inline objects, the referenced node carries no properties, every `noValue` succeeds **vacuously**, and all three fire on every result. It is the same pathology W-EP-01's Phase 2.5 guard was added to cure; these three have no equivalent guard.
>
> Verified by construction: morrison/cou1 references its 3 results as bare IRI strings, cou2 inlines all 3 as full objects, nagaraja uses 6 bare IRIs. Inlining cou1's results — same IRIs, same count, only the three properties the rules read — takes W-AL-01/W-AR-05/W-EP-02 from **3/3/3 to 0/0/0**. Across the three substrates **27 of 48 baseline firings are vacuous**, and the split is exactly the inline/bare-IRI split.
>
> **Consequence for A3.** A genuinely defect-free package that happens to reference its results by IRI will fire all three patterns on every result. The clean case-study variants **and the Bologna external negative must inline their validation results**, or the FP arm measures encoding style rather than false positives. This is the one place where A3's "expect zero critical detections" can fail for a reason that has nothing to do with the evidence — so a nonzero FP result must be checked against serialization shape *before* it is root-caused as a rule defect.
>
> No catalog edit: v0.5.15.1 is frozen and this is a reported finding. A guard mirroring W-EP-01's is a clean **v0.6 candidate**, recorded here alongside the Stage 4 REAL-GAPs.

**A4 Audit-Trail appendix:** generated from the completed history audit: catalog freeze tags; Phase 2/2.5 closure; Phase 3 gate decision provably preceding execution (GATE7_DECISION.md, calibration v2-v5); A16 pre-registration with pinned commit 6bcc76fe6142 (pin-consistency verified); GATE-H2/GATE-H3 entries with the letter's dual figures and the author's resolution; D2 rewording entries side by side; the H2 ordering claim at its actual evidentiary strength, on the three-strength table (provable / attested / recorded-before-the-governed-event) rather than a two-way split; **the Phase 3 spec cited directly** — v1.4 and v1.6 are now committed to `docs/`, with `GATE7_DECISION.md` as the amendment record. Cite **v1.6 as governing** per `PHASE3_STATUS_REPORT.md` D1, and note that the Tier-1 gate is numbered **#13 in v1.4 and #14 in v1.6** with byte-identical text; "v1.7" is shorthand for v1.6-plus-the-GATE7-amendment and is **not a document**, so sweep any citation implying a v1.7 file exists. Disclosure section carries the H2 routing-defect correction and criterion replacement. Every results section cross-references it.

One entry belongs here that the audit did not have to find: the ruling record for the 2026-08-16 decisions was committed **alone**, at `fad31cf5`, before the measurements it governs — the practice whose absence is the H2 weakness, applied to the rulings themselves. Pair it with `67aefa42` (2026-08-15, *"declaration on disk before any arm runs"*): the correction became standing practice within the week, unprompted. That is a stronger sentence than any defense of the original weakness, and it is true.

**D6 External-arm sections:** §3.4 orthogonality paragraph with the division-of-labor sentence (this arm answers the external-data question, not the CM&S encoding question); §3.4.x corpus page (Liang 32,111 pinned, raidex pinned, what runs, what is excluded and why, re-derivation script); §4.x cohort table with the measured 384/427 and the two-directions-verified equality claim, framed as invariance (the same unmodified rule assesses blood-pump CFD and LLM benchmark evidence and discriminates), one sentence of finding; scope/limitations/abstract lines.

### Position 9: D7 Claims Ladder + D8 Subsection Fills (5-7h)

D7, "Scope of Claims," three rungs: Demonstrated (machine-re-derivable: MECHANICAL detection from Arm M, Liang deterministic arm with measured D6 numbers, negative-control FP results, coverage κ against published taxonomies, raw-AI extraction where gated and passed, claim-density finding); Feasibility (author-derived under published protocol: JUDGMENT dispositions, gold-set labels, adjudicated extraction, real-corpus attribution characterization, A8 if elected); Future work (named, protocol-enabled, not claimed: multi-encoder replication, second-annotator agreement, regulatory acceptance, expert-panel validation in their "essential future work" words, prose-path validation, v0.6 increment, domain packs). Every Ch4/Ch5 claim sentence tagged; single limitation-attribution sentence (program constraint; the protocol converts replication from aspiration to executable future work); §1.8 cross-references the ladder.

D8, subsections merged within 48h of their source artifacts: Encoding Protocol and Reproducibility; Label Classes and Evidence Types (21-pattern partition, re-derivability test, per-class scoping); Injected-Flaw Validation; Negative Controls; Human Adjudication Role; Metrics Specification; Real-Corpus Construction (N=3 rule, screen results, two-pool distinction, development-document reclassification); Audit Trail appendix; Usability Interface.

### Position 10: D5 Register Sweep + D10 Integration + Tier C (close-out)

D5: banned register (regulatory credibility / regulator-ready / regulatory-grade / acceptable-to-FDA / regulatory acceptance as claimed properties; literature-scope names exempt) replaced by standards-mapped / standards-aligned / traceable-to-factors / specified defect classes; "author-encoded" escorted by "encoded under the documented protocol (Appendix: Encoding_Protocol) from published regulatory cases"; verified by the B4 script, zero fail-level hits.

D10: script clean on full manuscript; read-aloud on §1.4, hypotheses, abstract; three-artifact reconstruction check (thesis → claims ladder → audit trail lets a committee member reconstruct what is claimed, on what evidence, fixed when; the walkthrough lets them reproduce the central detection result themselves); Mohammad full polish LAST, briefed on the parse gate and the re-synthesis ban; then Tier C tic sweep in his lane (the warn-pattern list: "has the potential of," "there is an absence of," "is yet to be," adverb-phrase padding, "validate regarding," sentence-initial Nevertheless ×4, comma-splice whereas ×7, stacked participles, empty intensifiers, empty topic sentences; Ch1/Ch3 primary, Ch2/Ch4 sampled ten paragraphs each).

**Done-gate:** all checks pass; version tagged; every spec item closed or explicitly deferred with reason.

### Parked (never blocks anything)

**A8 blind self re-encode (optional):** Morrison COU1 from the published paper only; washout clock 2026-09-03 (decision 12); blinding rules (no prior package/notes/log until committed and tagged); comparison via `uofa diff` extension (4-6h per INV-4: structural + per-weakener disposition agreement per label class); pre-committed threshold JUDGMENT raw agreement ≥0.85; MECHANICAL below ~1.0 is a protocol/tool finding. Elect only after positions 1-8. Note: A8 also depends on A7 (no ambiguity log exists yet).

**A10 annotation:** admitted papers (machines queue produces the list) annotated under the existing protocol at reading pace; per-document attribution and claim-density reporting so no single paper carries the result; target 11-14 total including the 4 held-out current documents, or the measured ceiling disclosed. More papers change the precision of the H2 characterization, not its verdict.

---

## Effort roll-up

| Queue | Hours |
|---|---|
| Machines session 1 (Phase 2.5a) | 9-13 + ~$50 |
| Machines session 2 (follow-ups) | 8-11 |
| Calendar (Stage 4 sitting) | one sitting |
| Writing positions 1-10 | 36-46 |
| Parked (if elected / reading pace) | A8: 6-8 + washout; A10: reading pace |

## Escalation protocol

Machines-queue escalations come to the author named and specific (each child spec lists its criteria); everything else proceeds. The author's standing question on any report: which queue, and did it hit an escalation. Writing queue has no escalations, only the position-8 branch.

## Consolidated done-gate

All queue items closed or explicitly deferred, plus the integration check: a committee member reading the plain-language hypotheses, then the claims ladder, then the audit-trail appendix, then running the inject-and-detect walkthrough, can independently verify what is claimed, on what evidence, fixed when, and can reproduce the central detection result themselves, with ground truth true by construction. Must-have 1's deepest ask is reproducibility without trusting anyone's judgment; the mutation arm delivers it literally.

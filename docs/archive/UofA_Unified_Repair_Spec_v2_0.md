# UofA Unified Repair and Response Spec v2.0 (Consolidated)

Status: DRAFT for author approval
Date: 2026-08-16
Owner: Vishnu Vettrivel
Supersedes: v1.2 and all earlier repair/update/prose-kit specs. This document is self-contained; no prior spec is required to execute it.

Governing input: Fossaceca/Sarkani letter of 2026-08-11 ("solid and can move forward," five must-haves required before defense). Where the earlier informal feedback conflicts with this letter, the letter governs. Program constraint in force throughout: no contributors other than the author.

Execution: author + Claude Code (paired throughput assumed in all estimates) + Mohammad (writing-quality lane only, grammar-in-place, after content stabilizes; re-synthesizing passes banned) + Turman (thesis statement and RQ/hypothesis wording review).

---

## 0. Must-have coverage map

| Must-have | Covered by | Current status |
|---|---|---|
| 1. Replace LLM-as-judge with injected flaw testing | A2, A1, A3, A5, B2 | Harness exists (Phase 2/2.5, 97.1% NC clean rate on 180-package holdout); framing and manuscript presentation are the gap |
| 2. Tools that hide the complexity | C1, C2 | Largely built: Credibility Inspector live at uofa.net/demo (upload, auto standard detection, plain-language Reviewer verdict, Author gap list, PDF export, no semantic-web exposure). Gap: signed pack download not surfaced |
| 3. Simplify the hypotheses | D2, A1, A5 | Rewrite, with author-set gates (GATE-H2, GATE-H3 below) |
| 4. Preliminary framing, prototype language, open source | D1, D3, D7 | Mostly existing; needs prominence and register repair |
| 5. Human reviewer role and bias | A9, A7, C-artifact | Disclosure gap; the encoding protocol and the Inspector's confirm step are the mitigation mechanisms |

### 0.1 Author-set gates (resolved, disclosed, not asked)

Threshold-setting is the author's responsibility; the committee letter is advisory input. Both resolutions and their rationales are disclosed in the A4 audit trail, including the letter's own dual figures.

**GATE-H3.** The letter contains both 95% (must-have 1 prose) and 80% (simplified H3 text). Resolution: gates scoped per label class (A1). MECHANICAL-class detection gated at ≥95% (the holdout supports it); JUDGMENT-class and overall gated at ≥80%. False positives <10%, per class, measured by A3.

**GATE-H2.** The letter's "F1 ≥0.85 on a test set of 50 documents" is met at 0.95 by the shipped detection measure, but that measure is non-discriminating: a constant checklist reaches the same score (see A5). Passing a hypothesis on a measure the manuscript's own null disowns repeats the exact "proves nothing" pattern the letter condemns for H3. Resolution: H2 gates on detection F1 ≥0.85 **with a required margin over the run's own null**, plus attribution above the run's permutation null at a stated multiple. Raw AI performance only; adjudicated figures are reported separately as the practical ceiling (A9). Reported per corpus: the 50-bundle synthetic set (30 dev + 20 held-out) and the real annotated corpus (A10).

### 0.2 Pre-meeting / next-contact materials (send now, no dependency)

1. Credibility Inspector link (uofa.net/demo) with one line: this is must-have 2, live today.
2. NAFEMS CLI reproduction page (uofa.net/demo/nafems) as the exact-numbers worked example, FDA-co-authored case.
3. One paragraph previewing the injected-flaw reframe (A2): ground truth was always the injection manifest; the manuscript will present it that way.

---

## 1. Priority ordering (by weight of committee concern)

| Rank | Work | Answers |
|---|---|---|
| 1 | A2 + B2 (judge demotion, injected-flaw reframe, one-command demo) | Must-have 1, their strongest language |
| 2 | D2 + A1 (plain hypotheses with author-set gates; label-class partition feeding them) | Must-have 3 and what "defensible" means |
| 3 | A9 (adjudication disclosure, raw/adjudicated split) | Must-have 5 |
| 4 | E Tier A + D1 + D5 (meaning inversions, thesis rewrite, register sweep) | Must-have 4 and the skim impression |
| 5 | A4 (audit trail, carrying gate disclosures) | Circularity / post hoc changes |
| 6 | A3 (negative controls, FP table for the <10% gate) | Must-have 1, second half |
| 7 | C1 + §0.2 send (pack download; Inspector link banked early) | Must-have 2 |
| 8 | A10 (real-corpus expansion) | Data adequacy; precision, nothing gates on it |

Ranks 1–3 are the defense-deciding tier.

## 1a. Dependency ordering (execution sequencing)

| Order | Items | Rationale |
|---|---|---|
| Now, parallel | A1, A3, A4, A5, A6, A7, A9, A10 rule+screen, B1–B4, C1 (after INV-12), C2, D1, D3, D4, D5, D6, D9, E Tier A, §0.2 send | No dependencies beyond INV-12 for C1 |
| After A1 | D7 claims ladder; D2 final wording | Partition feeds claim language |
| After A7 | D5 escort language; A9 manuscript text | Protocol must exist to be cited |
| After A-items land | D8 subsections filled | Each reports an artifact |
| Optional, post-washout | A8 blind self re-encode | Strengthening, not load-bearing |
| Last | D10 integration pass; E tic sweep | Full-document verification |

Effort roll-up:

| Workstream | Hours |
|---|---|
| A. Validation and study | 17–22 |
| B. Tooling | 6–9 |
| C. Web UI gap-close | 3–6 |
| D. Manuscript | 14–18 |
| E. Prose repair | 4–6 |
| Total | 44–61 |

A8 adds 6–8h if elected. A10 annotation runs at reading pace beyond its 1h setup and is excluded from the total.

---

## Workstream A: Validation and study

### A1. Label-class partition

**Question protected:** are ground-truth labels objective or author-dependent?

**Claim after change:** every detection result carries an evidence type. MECHANICAL patterns have machine-re-derivable labels requiring no human judgment; JUDGMENT patterns are explicitly scoped and laddered (D7).

Tool changes:
1. Add `label_class` metadata field (enum MECHANICAL / JUDGMENT) to the pattern catalog schema; classify all 23 patterns of v0.5.15.1. Provisional: MECHANICAL = W-PROV-01, W-SI-01..02, W-CON-01..05 (where the rule is field comparison), W-AR-01..05 (where the rule is structural presence/absence); JUDGMENT = W-EP-01..04, W-AL-01..02, W-ON-01..02, COMPOUND-01, COMPOUND-03. INV-1: confirm each assignment against actual rule logic; the test is "a script re-derives this label from the pinned evidence bundle with zero human input."
2. Emit `label_class` in weakener report output.
3. Add `uofa verify-labels`: re-derives all MECHANICAL labels from a pinned bundle, diffs against reported findings, exits nonzero on mismatch. Committee-facing reproducibility demonstration.

Praxis changes: new Ch3 subsection "Label Classes and Evidence Types" defining the classes and the re-derivability test; partition table; every κ/F1 statement in Ch3 and results re-scoped per class, never pooled across classes.

Study changes: case-study reports re-emitted with `label_class`; Phase 3 tables gain a class column; pooled metrics split per class.

The MECHANICAL class is precisely the territory where injected-flaw ground truth is 100% certain, which is the committee's own standard; lead with that alignment in D8.

**Done-gate:** 23 patterns classified and confirmed; verify-labels passes on all three case-study bundles; no unscoped metric statement in Ch3.
**Effort:** 3–4h.

### A2. Injected-flaw validation as the primary H3 evidence

**Question protected:** does the catalog detect real defects, proven without human or AI judgment?

The committee prescribed a script that starts with a perfect evidence package and systematically injects known flaws. Phase 2/2.5 is that script; the work is repositioning, not rebuilding.

1. **Demote the LLM judges.** In all manuscript text and results, judges appear only as realism screening of generated adversarial cases, never as ground truth. Ground truth is the injection manifest; say so explicitly and early. INV-8: audit current Ch3/Ch4 text and the Phase 3 spec for any place judge output is load-bearing for H3; remove those from the support chain (they may remain as clearly-labeled secondary characterization).
2. **Map their examples to the harness.** One Ch3 table: the letter's named flaw types (remove uncertainty, change version numbers, remove signatures) against the patterns that catch them (W-AL-01, W-CON version-pin rules, W-PROV-01 / signature integrity) and the Phase 2/2.5 injection classes that exercise them. Shows the prescribed test was designed in, not bolted on.
3. **Present the numbers against manifest ground truth:** per-pattern detection rate, per class per A1, FP rate from the zero-injection arm (A3), holdout clean rate (97.1% on 180 packages), Wilson CIs per A5. Apply the H2 null-control standard throughout: every headline metric reported beside a null that a non-reading system would achieve, so no H3 number repeats the detection-at-ceiling failure H2 caught in itself.
4. B2 exposes the harness as a one-command live demonstration.

**Done-gate:** manuscript H3 support chain contains no judge-derived ground truth; mapping table merged; detection metrics reported against manifests only, each beside its null.
**Effort:** 3–4h.

### A3. Negative controls and false-positive characterization

**Question protected:** does the engine fire only on real defects, or on clean evidence too?

Framed as the zero-injection arm of the A2 harness, so the falsification story is one apparatus.

Study changes:
1. Clean-case corpus: a defect-free package variant per case study (injected defects removed, known weakeners dispositioned per the published record). Expected: zero critical detections; root-cause any firing.
2. External negative: one additional published, accepted submission encoded straight from source, no injection. INV-5: confirm candidate availability by reading it before committing.
3. Report: FP rate table per pattern per label class across all clean runs; nonzero results disclosed with root cause and fix-or-disclose disposition.

Tool changes: clean-corpus fixtures merged into CI (B3) so FP regression is checked on every commit; any FP root-causing to a rule defect is fixed under a new patch version, logged in A4.

Praxis changes: Ch3 "Negative Controls" subsection with explicit falsification framing (the clean runs are attempts to make the engine fail).

**Done-gate:** three clean variants plus one external negative run; FP table generated; CI fixtures merged.
**Effort:** 5–6h.

### A4. Audit-trail appendix

**Question protected:** were the catalog and thresholds fixed before the results were seen?

Praxis changes: new appendix "Methodological Audit Trail," one dated table generated from audited git history (INV-6: audit history first; the appendix is generated from the record, not from memory; an omission discovered later costs more than any disclosed change):
1. Catalog version history through v0.5.15.1 with freeze dates and git tags.
2. Phase 2 / 2.5 closure dates; Phase 3 gates with dates set, shown to precede execution.
3. A16 pre-registration date and pinned Liang commit (6bcc76fe6142).
4. GATE-H2 and GATE-H3 entries: the letter's dual figures, the author's resolution, rationale.
5. Hypothesis rewording entries (D2): original and revised side by side, dated, rationale "plain-language operationalization following committee feedback; tests unchanged except as directed."
6. Disclosure section: every post-freeze change with rationale, including the H2 routing-defect correction and criterion replacement already documented in ch4-h2-section.

Every results section that depends on a freeze cross-references the appendix.

**Done-gate:** appendix drafted from audited history; zero undisclosed post-freeze changes.
**Effort:** 3h.

### A5. Metrics specification

**Question protected:** are reported numbers pre-specified and consistently defined?

One metrics-specification table in Ch3, placed before any results:

| Element | Specification |
|---|---|
| Detection rate | per pattern, per label class; numerator/denominator defined on defect instances |
| Confidence intervals | Wilson score, 95%, on all proportions with n < 100 |
| κ | Cohen's, per label class only, never pooled; thresholds named per use |
| F1 | the definition documented in ch4-h2-section, reported beside its null controls throughout |
| Null controls | every headline metric reported beside the score a non-reading system achieves (constant checklist for detection; permutation null for attribution) |
| Effective n | defect instances for H3, factor-document pairs for H2, not case-study or paper counts; per-class counts tabulated |
| Hypothesis gates | H1: ≥90% completeness, ≥95% SHACL pass, 100% signatures valid. H2: GATE-H2 (§0.1). H3: GATE-H3 (§0.1) |
| Multiple comparisons | none claimed; estimates with CIs, not hypothesis tests, unless pre-specified here |

Sweep Ch3 and all results sections for conformance; recompute any nonconforming metric and disclose the change in A4.

Status notes: the F1 definition question is closed (documented with nulls in ch4-h2-section). The 50-document question is closed for synthetic (30 dev + 20 held-out bundles exist) and converted for real documents into A10.

**Done-gate:** table merged before any results; sweep complete; recomputation diffs empty or disclosed; gate rationales in A4.
**Effort:** 3–4h.

### A6. Liang/modelbiome external at-scale arm (deterministic only)

**Question protected:** does the framework discriminate on evidence at scale that the author neither wrote nor selected?

Study changes: A16 reporting splits by label class per A1. Deterministic findings (completeness, provenance, pinning) reported as primary, re-derivation script published against the pinned commit. Author-labeled judgment findings on the 150-card gold set reported under feasibility framing, same disclosure language as CM&S judgment patterns; no second labeler (program constraint). DIV-07 zero-positive properties framed as prevalence findings with the bounded enrichment stratum.

Praxis changes: division-of-labor sentence in §3.4: this arm answers the external-data question and does not address the CM&S encoding question, which A7 addresses. Manuscript rendering per D6.

**Done-gate:** A16 results split by class; script published; framing sentence in Ch3.
**Effort:** 2h framing.

### A7. Encoding protocol (load-bearing for must-have 5)

**Question protected:** is the encoding reproducible from a written procedure, or does it live in the author's head?

Encoding_Protocol_v0_1.md, published as praxis appendix and in the repo:
1. Source-evidence intake rules; citation-anchoring (every encoded assertion cites page/section/table).
2. Ordered extraction passes: context of use, model description, V&V activities, results, applicability; per pass, which entities instantiate and which fields are mandatory.
3. Disposition procedure: per weakener class, testable Accepted / Not Accepted / Not Applicable criteria referencing source text. Where a criterion cannot be made testable, the pattern is JUDGMENT class (feeds INV-1).
4. Mandatory ambiguity log: entry per underdetermined field, recording ambiguity, resolution, rule applied.
5. Stopping rule: complete when all mandatory fields are populated or logged source-absent.

INV-2: check whether `uofa protocol-check` (mechanical conformance validation against the field list) is cheap; add if so, else future work.

**Done-gate:** protocol published and tagged; cited from A9's disclosure text.
**Effort:** 4h.

### A8. Blind self re-encode (optional strengthening)

Not load-bearing (the letter replaced the second-encoder demand with disclosure). Design on file, elected if calendar allows after ranks 1–7: Morrison COU1 re-encoded from the published paper only, minimum 3-week washout from last package touch (INV-3: set the clock from git history), no access to prior package/notes/ambiguity log until the re-encode is committed and tagged. Comparison run mechanically via `uofa diff-packages` (INV-4: extend existing diff tooling if present): structural agreement plus per-weakener disposition agreement, per label class. Pre-committed threshold: JUDGMENT disposition raw agreement ≥0.85 counts as consistent; below, report and root-cause via the ambiguity logs. MECHANICAL agreement below ~1.0 indicates a protocol or tool defect, itself reportable.

**Done-gate (if elected):** protocol followed blind; diff report generated; pre-committed thresholds honored.
**Effort if elected:** 6–8h plus washout.

### A9. Human adjudication disclosure

**Question protected:** can the reader tell whose judgment shaped the results and what the AI did unaided?

1. New Ch3 subsection "Human Adjudication Role." States plainly: all adjudication was performed by the author; the program's no-external-contributor constraint precludes independent reviewers; mitigations are the published protocol (A7), the label-class partition (A1) confining author judgment to the JUDGMENT class, and (if elected) A8. The Credibility Inspector's confirm step (user corrects factor statuses) is cited as the concrete artifact showing exactly where human judgment enters: bounded, visible in the UI, identical in the study workflow.
2. **Split every affected metric.** Wherever extraction results were touched by adjudication, raw AI performance and post-adjudication performance are separate, labeled numbers; never blended. INV-10 status: the shipped H2 section reports raw performance with nulls; audit remaining citations elsewhere in the manuscript and apply the split.
3. GATE-H2 applies to raw AI extraction; adjudicated figures are the practical ceiling, not the hypothesis result.

Two text reconciliations:
1. ch4-h2-section's limit-on-inference names a second annotator as one of two reliefs; the program constraint kills that relief. Rewrite to attribute the single-annotator design to the constraint; second-annotator agreement moves to protocol-enabled future work.
2. The claim-density 0.000 finding (96 well-formed rationales, zero checkable quantities) is promoted to Ch1: one sentence in the motivation, since prose-borne unverifiable evidence is the thesis, demonstrated by the study's own extractor. Tagged on the claims ladder (D7).

**Done-gate:** subsection merged; every extraction metric labeled raw or adjudicated; H2 chain uses raw only; both reconciliations landed.
**Effort:** 2–3h.

### A10. H2 real-corpus expansion via the annotation pool

**Question protected:** are real-document extraction claims a property of the corpus or of one lucky paper?

Consumes real-corpus-supply-survey.md. Two pools, two criteria; do not conflate:
- **Scorecard pool** (per-factor table transcribable): ~5 documents, near the published population; Bologna (Aldieri 2023) is the next bundle. No expansion expected. The measured scarcity becomes a §1.2 motivation paragraph with a denominator.
- **Annotation pool** (factor evidence present in prose, no scorecard required): the H2 reference corpus. The survey's scorecard rejects re-qualify here.

1. Commit the inclusion rule before admitting any paper: published paper or public report containing prose evidence for ≥N credibility factors of V&V 40 or NASA-STD-7009, readable by the pipeline reader. Exclusions: Morrison, Nagaraja, and NASA HPT sources (case-study contamination); any document failing the reader-pathology screen (TAVI I/II stay out unless the lost-spaces fix ships; never annotate what the extractor cannot ingest).
2. Screening candidates (INV-13: read each before admitting; both prior survey rejections were only visible on inspection): the Frontiers collection papers (coronary stent, flow-diverter, EVAR stent-graft, bioresorbable scaffold, cardiovascular-UQ), FDA nozzle validation (Hariharan 2017), spine PJF V&V 40 (2022), 3D-printed wrist-hand orthosis, Pathmanathan applicability analysis (2017), Ahn & de Weck SpaceNet Delphi CAS assessment (also screen for the scorecard pool: it carries a filled CAS of a named platform and sits outside NTRS), 2024 pharmaceutical-manufacturing 7009 paper.
3. Target: 11–14 total annotated documents (6 current + 5–8 admitted), annotated under the existing protocol. Report attribution and claim density per document so no single paper can silently carry the result.
4. Reporting effect: limit-on-inference rewritten from "too small to separate mechanism from noise" to measured precision; the synthetic/real router inversion (K6/K4) reported as a transfer finding at the larger n; the claim-density finding gains its denominator.

More papers change the precision of the H2 characterization, not its verdict; if the mechanism is weak, the larger corpus shows it more precisely, and that is the reportable result.

**Done-gate:** inclusion rule committed before any admission; ≥11 documents annotated, or the measured ceiling disclosed with screen results; per-document reporting in place.
**Effort:** ~1h rule + screening; annotation at reading pace; rank 8, parallel whenever reading time exists.

---

## Workstream B: Tooling

### B1. Catalog and CLI changes from A-items
`label_class` schema field and report emission; `uofa verify-labels` (A1); `uofa protocol-check` if INV-2 says cheap (A7); `uofa diff-packages` if A8 elected.
**Effort:** 3–4h.

### B2. One-command injection demonstration
Expose the Phase 2/2.5 harness as committee-runnable: `uofa inject --pattern <id> --package <clean-pack>` producing a corrupted package plus manifest, then `uofa detect` showing the catch. README walkthrough reproduces the letter's own description end to end: perfect package in, known flaw injected, flaw caught, manifest confirms. Cheapest high-credibility artifact in the response; must-have 1 becomes a live demo. INV-11: how much is CLI-exposed today vs internal scripts; wrap, don't rewrite.
**Effort:** 2–3h.

### B3. Clean-corpus CI fixtures
From A3; FP regression checked every commit.
**Effort:** 1h (inside A3's budget).

### B4. Register-check script
Scripted sweep over exported manuscript text: banned register (fail-level, per D5) plus prose-tic patterns (warn-level, per E). Script and output are A4-appendix material.
**Effort:** 1–2h.

---

## Workstream C: Web UI gap-close (must-have 2; Credibility Inspector exists)

**Existing artifact:** Credibility Inspector, live at uofa.net/demo, backed by HF Space cloudronin/uofa-demo (GPU, sleeps when idle). Flow: upload evidence or bundled sample → router auto-detects standard (V&V 40 / 7009B), user can override → user confirms/corrects the credibility-factor statuses the tool read → plain-language Reviewer verdict or Author gap list off the same analysis → Save as PDF. No RDF, SHACL, JSON-LD, or signature exposure anywhere. This satisfies the upload, background-generation, hidden-complexity, and adopt-without-knowing clauses of must-have 2.

### C1. Signed pack download (the literal gap)
The letter's "the system generates the UofA automatically in the background" implies the user gets the UofA, not only report views.
1. INV-12: confirm whether the Space's pipeline already constructs the signed pack internally (merely unsurfaced) or stops at analysis; wrap vs build follows.
2. Add "Download UofA package" emitting the signed pack (zip: JSON-LD graph, provenance, signature, report). The download path must be the production pack-build path, not a demo fork; if the demo path can produce a pack the CLI would reject, that is a defect.
3. Cold-start note (first load up to a minute) in any committee-facing walkthrough.

**Done-gate:** pack downloads from the demo; CLI `uofa verify` passes on a web-produced pack; walkthrough updated.
**Effort:** 2–4h (contingent on INV-12).

### C2. Manuscript rendering of the Inspector
Ch3 short subsection: the Inspector as the usability layer, stated in the letter's vocabulary (complexity hidden behind upload-and-confirm; semantic web invisible). Ch4: screenshots of the four-step flow, the Reviewer/Author toggle, and the pack-download step once C1 lands. One sentence connecting the confirm step to A9's adjudication disclosure.

**Done-gate:** subsection and screenshots merged; every UI claim matches the live demo at the pinned site commit.
**Effort:** 1–2h.

Standing note, once: the Space as a hosted demo with GPU cost and wake-time is fine. Anything adding uptime commitments, accounts, or support obligations is a separate post-defense decision.

---

## Workstream D: Manuscript

### D1. §1.4 thesis statement rewrite
Defect: the "three capabilities" colon never delivers; adjacent sentences are garbled editing artifacts.
1. Four fixed paragraphs: (a) UofA definition sentence (keep); (b) weakener definition, Pollock lineage intact; (c) the thesis sentence: "This praxis develops and evaluates a standards-mapped, machine-readable evidence package and rule catalog, with a documented coverage methodology validated against four published defeater taxonomies, that detects specified structural, provenance, and integrity defect classes in computational modeling and simulation evidence."; (d) C1/C2/C3 enumeration, one paragraph each, delivered in order.
2. Repair named garbles: "SHACL constraint shapes" (not "obstacle constraints"); the C2 sentence rewritten to parse; the CI/CD analogy sentence rewritten or cut.
3. Keep the C2/C3 humility passage (SSP-LS comparison); do not let condensation remove it.
4. Closing sentence names the contribution "a prototype and proof of concept" in those words (must-have 4).

**Done-gate:** every §1.4 sentence parses on read-aloud; the colon delivers C1/C2/C3; Turman sign-off on the thesis sentence.
**Effort:** 1h draft + review.

### D2. Hypotheses in plain language, author-set gates
1. Adopt the letter's three plain sentences nearly verbatim as hypothesis statements, each with its gate from A5's table (GATE-H2 and GATE-H3 applied). Technical operationalization (COV-HIT taxonomy, factor definitions) moves to methodology subsections, referenced not inlined.
2. RQ register fix: RQ1 "standards-aligned (traceable to ASME V&V 40 and NASA-STD-7009B credibility factors) and machine-verifiable," not "regulatorily credible"; H1 likewise; RQ2/RQ3 swept for the same register; empirical content unchanged.
3. Disclosure entries in A4: original and revised wording side by side, dated, with rationale.

**Done-gate:** each hypothesis is one plain sentence plus a measurable gate; no jargon in the statement; Turman review; disclosure entries drafted.
**Effort:** 2–3h.

### D3. Non-claims scope box plus prototype framing
Boxed, visually distinct paragraph at §1.7 end or §1.8 head:
> "This praxis makes no claim of regulatory acceptance, endorsement, or submission-readiness. The claim is narrower and structural: regulated domains require credibility arguments that are today prose-borne and manually audited; this work demonstrates a mechanism that renders such arguments machine-checkable, mapped to the published standards those domains already use (ASME V&V 40, NASA-STD-7009B, FDA 2023 CM&S guidance). Whether any regulator accepts machine-checkable evidence of this form is an empirical question for future work and is not asserted here."

Add adjacent: "The validation reported here is preliminary; real-world validation with human experts is essential future work." and "The system is released open source (github.com/cloudronin/uofa) to enable community validation." §1.8's "indirect manner via structured proxies" sentence moves adjacent. Abstract references the box.

**Done-gate:** box present, renders distinctly, referenced from abstract.
**Effort:** 30m.

### D4. Skim-hardening
1. New Ch1 figure: the two-arm validity diagram (constructed ground truth via defect injection into published-case substrate × published-case anchors × negative controls), caption naming injected-flaw testing as the constructed-ground-truth arm; one sentence: each arm covers the others' weakness; no arm depends on author opinion for its ground truth.
2. §1.2 gains the corpus-absence sentence as motivation: "No adjudicated corpus of assurance defects in CM&S evidence packages exists. This absence is simultaneously the gap this praxis addresses and the reason its validation must construct its own ground truth: a first instrument cannot be calibrated against an instrument that does not exist." (Promoted from §3.10.3, which keeps its copy.) A10's measured-scarcity paragraph lands adjacent with its denominator.
3. §3.1 Reading Guide gains a Validity Strategy paragraph pointing forward to §3.10 explicitly.
4. Escort rule for "synthetic": first mention in §1.6 and §3.7 becomes "constructed ground truth via defect injection into published-case substrate, following the fault-injection and mutation-testing tradition," with two citations. U-INV-1: select citations from sources actually read; do not cite from memory.

**Done-gate:** figure placed; insertions merged; a cold reader stopping at end of Ch1 can state the validity design.
**Effort:** 3h.

### D5. Terminology sweep
1. Banned as claimed properties of the UofA/tool: "regulatory credibility," "regulator-ready," "regulatory-grade," "acceptable to FDA," "regulatory acceptance" (except future-work and literature-review positions; "Audit and Regulatory Acceptance" as a Ch2 focus-area name is literature scope and stays).
2. Required register: "standards-mapped," "standards-aligned," "traceable to [named standard] factors," "specified defect classes."
3. "Author-encoded" always escorted: "encoded under the documented protocol (Appendix: Encoding_Protocol) from published regulatory cases" (depends on A7).
4. Verification scripted via B4; sweep done when the script reports zero violations on the full manuscript.

**Done-gate:** script clean.
**Effort:** 2h + script.

### D6. External at-scale arm rendered
Decision recorded: the AI/model-card work enters as an at-scale external validation arm, not a fourth case-study tier. Deterministic path only; prose path, judge labels, gold-set work stay post-defense.
1. §3.4 paragraph naming the arm as orthogonal to the tiers, with A6's division-of-labor sentence.
2. New §3.4.x (one page): corpus (Liang 32,111 cards, pinned commit 6bcc76fe6142; raidex models/results, pinned), what runs (completeness factors + core ValidationResult rules, all machine-re-derivable), what is excluded and why, re-derivation script published.
3. New §4.x (one to two pages): cohort table; W-AL-01 firing 384/427 and clearing exactly the results carrying real uncertainty, framed as the invariance demonstration (the same unmodified rule assesses blood-pump CFD and LLM benchmark evidence and discriminates). One sentence of finding, no field-reform rhetoric; Demonstrated rung (D7).
4. §1.7 scope sentence admitting the arm; §1.8 line that the judgment-layer extension is future work; abstract clause ("...demonstrated across three regulated CM&S case studies and an external corpus of 32,111 published AI model cards").
U-INV-3: every number traces to committed studies/ artifacts.

**Done-gate:** both sections drafted; numbers traced; register-check clean.
**Effort:** 3h.

### D7. Claims ladder
New "Scope of Claims" section (end of Ch1 or head of Ch5), three rungs:

| Rung | Definition | Contents |
|---|---|---|
| Demonstrated | machine-re-derivable evidence, external or published sources, reproducible by reader | MECHANICAL detection on published cases; injected-flaw detection against manifests; Liang deterministic arm; negative-control FP results; coverage methodology κ against published taxonomies; raw-AI extraction where gated and passed |
| Feasibility | author-derived evidence under published protocol | JUDGMENT-class dispositions; gold-set judgment labels; adjudicated extraction figures; attribution characterization on the real corpus; A8 self-consistency if elected |
| Future work | named, protocol-enabled, not claimed | multi-encoder replication; second-annotator agreement; regulatory acceptance; expert-panel validation ("essential future work," their words); prose-path validation; domain packs |

Every claim sentence in Ch4 results and Ch5 conclusions tagged to a rung (inline tag or claims-register appendix, one style applied uniformly). Limitation attribution stated once: single-encoder and single-annotator design reflects the program's no-external-contributor constraint; the published protocol converts replication from aspiration to executable future work. The claim-density 0.000 finding tagged Demonstrated. §1.8 cross-references the ladder instead of restating it.

**Done-gate:** claims register complete; no untagged claim above Feasibility.
**Effort:** 2–3h. (Depends on A1.)

### D8. Methodology subsections reporting artifacts

| Subsection | Reports | Depends on |
|---|---|---|
| §3.x Encoding Protocol and Reproducibility | A7 summary; A8 design if elected | A7 |
| §3.x Label Classes and Evidence Types | A1 partition, re-derivability test | A1 |
| §3.x Injected-Flaw Validation | A2 reframe, flaw-to-pattern mapping, harness description, B2 demo pointer | A2 |
| §3.x Negative Controls | A3 design, FP table pointer | A3 |
| §3.x Human Adjudication Role | A9 disclosure, metric split, Inspector confirm-step artifact | A9, A7 |
| §3.x Metrics Specification | A5 table including gates | A5 |
| §3.x Real-Corpus Construction | A10 inclusion rule, screen results, two-pool distinction | A10 |
| Appendix: Methodological Audit Trail | A4, including gate and rewording disclosures | A4 |
| §3.x / §4.x Usability Interface | C2 description, screenshots, pack-download step | C1, C2 |

**Done-gate:** each merged within 48h of its source item's gate.
**Effort:** 5h across items.

### D9. Chapter 5 disposition
The placeholder title ("Discussion, Conclusion, or Your Heading") is gone from every circulating copy this week. Recommended: two-page Ch5 skeleton, DRAFT-marked: contributions restated on the claims ladder, limitations pointer, future-work list (multi-encoder replication, regulatory acceptance, prose-path validation, domain packs).
**Effort:** 2h.

### D10. Final integration pass
1. B4 script clean on the full revised manuscript.
2. Read-aloud pass on §1.4, §1.6 (new hypothesis statements), abstract.
3. Three-artifact reconstruction check: thesis statement → claims ladder → audit trail, read in sequence, must let a committee member reconstruct what is claimed, on what evidence, fixed when; then the B2 demo lets them reproduce the central detection result themselves.
4. Mohammad full-manuscript polish last, briefed on the parse-on-read-aloud gate and the ban on re-synthesizing passes (condensation introduced the §1.4 artifacts).

**Done-gate:** all checks pass; version tagged; every spec item closed or explicitly deferred with reason.

---

## Workstream E: Prose repair

**Tier A, meaning inversions (author-only; these are claim repairs, not style).** Confirm intended meaning, patch in one pass, read each fix aloud:

| Loc | Currently says | Fix to |
|---|---|---|
| §1.2 | "mesh convergence studies might have been excessively written" | "...overwritten" (data loss, not verbosity) |
| §1.2 | "rooted in the workflow simulation" | "rooted in the simulation workflow" |
| §1.3 | "lacks a credible evidence package with no provenance graph..." | "provides no evidence package: no provenance graph, no SHACL-enforceable completeness check, no tamper detection" |
| §1.6 H3 | "validate regarding real-time practitioner packages" | "validate against real-world practitioner packages," with the test stated |
| §1.4 | "SHACL obstacle constraints" | "SHACL constraint shapes" |
| §1.2 | "becomes less than many utilized use cases" | "Publicly accessible instances of complete credibility assessments for FDA CM&S submissions are far fewer than the use cases that rely on them" |
| §1.2 | "issues experts eventually fixed via continuous integration" | "issues software teams eventually solved with continuous integration" |
| §1.1 | "standards ensure robust models to establish that defensibility" | "standards define how that defensibility is established" |
| §1.2 | "it is yet to treat... artifact having a lifetime cycle" | "the field has not yet treated the resulting evidence as an engineering artifact with its own lifecycle" |
| §1.8 | run-on tier-coverage sentence | "Results are specific to the encoded case studies. Tier coverage spans single-CoU and multi-CoU configurations; broader domain coverage is future work." |

**Tier B, drop-in rewrites of §1.1–§1.3** per the Prose Repair Kit's clean text (background/motivation, problem statement skeleton with the CI analogy and three failure categories, §1.3 targeted repairs). After insertion, diff against the original for silently lost citations or claims.

**Tier C, tic sweep (Mohammad's lane, after A and B land, driven by B4 warn patterns):** "has the potential of X-ing"→"can X"; "there is an absence of X"→"no X exists"; "is yet to be"→"has not been"; "in a quiet/indirect manner"→adverb; "validate regarding"→"validate against"; sentence-initial "Nevertheless" (4× in Ch1) varied; comma-splice "whereas" (7×) split; stacked participles→one finite verb per clause; "proper/robust/considerable" intensifiers deleted; empty topic sentences deleted. Ch1/Ch3 primary; Ch2/Ch4 sampled (10 paragraphs each) for the same fingerprint.

Process directive: the pass that produced the damage (condensation/paraphrase re-synthesis) is banned from all future editing; polish means grammar in place.

**Done-gate:** author read-aloud of Ch1 end to end, zero sentences requiring a second read.
**Effort:** 4–6h author + Mohammad lane.

---

## Investigation items register

| ID | Item | Blocks | Status |
|---|---|---|---|
| INV-1 | Confirm MECHANICAL/JUDGMENT assignment per pattern against rule logic | A1 | Open |
| INV-2 | Feasibility of `uofa protocol-check` | A7 (optional) | Open |
| INV-3 | Morrison COU1 last-touch date for washout clock | A8 if elected | Open |
| INV-4 | Existing package-diff tooling, extend vs build | A8 if elected | Open |
| INV-5 | External accepted-case source: read before asserting | A3 | Open |
| INV-6 | Git-history audit for post-freeze changes | A4 | Open |
| INV-8 | Where judge output is currently load-bearing for H3 | A2 | Open |
| INV-11 | Injection harness CLI exposure today; wrap vs rewrite | B2 | Open |
| INV-12 | Does the demo Space build the signed pack internally or stop at analysis? | C1 | Open |
| INV-13 | Read-before-admit screen of each A10 candidate against the committed rule | A10 | Open |
| U-INV-1 | Two fault-injection/mutation-testing citations, read before citing | D4 | Open |
| U-INV-3 | Every D6 number traces to committed studies/ artifacts | D6 | Open |
| INV-7 | F1 definition vs fixed definition | — | CLOSED: documented with nulls in ch4-h2-section |
| INV-9 | 50-document test set | — | CLOSED synthetic (30+20 bundles); converted to A10 for real |
| INV-10 | Raw vs adjudicated metric preservation | A9 sweep | CLOSED for H2 section; residual audit inside A9 |

## Open items

| ID | Question | Ask whom | Blocks |
|---|---|---|---|
| OPEN-2 | Is a live demo (Inspector and/or B2 inject-and-detect) expected at the defense itself? | Turman | Defense prep only; nothing builds on it |

## Consolidated done-gate

All workstream gates pass, plus the integration check: a committee member reading the plain-language hypotheses, then the claims ladder, then the audit-trail appendix, then running the B2 demo, can independently verify what is claimed, on what evidence, fixed when, and can reproduce the central detection result themselves. Must-have 1's deepest ask is reproducibility without trusting anyone's judgment, and B2 delivers it live.

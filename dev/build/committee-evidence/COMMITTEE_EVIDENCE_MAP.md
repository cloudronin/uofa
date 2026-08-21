# Committee-feedback evidence map — Aug 8 to Aug 21, 2026

Investigation output. Read-only against repo history; no code, no edits, no new work items.
Every claim below carries a commit, PR, or file ref. Every number carries the artifact that
re-derives it.

**Scope of the dig:** `git log --all --since=2026-08-08` (248 non-merge commits), merged PRs
**#74 through #100**, the decision records and addenda, `docs/SCHEMA_FINDINGS.md`, the encoding
protocol and its findings, `studies/` additions, and `studies/ch4_numbers/LEDGER.md`.
Base ref: `origin/main` at `28b036cf`.

**One caveat on the honest-labelling instruction.** MH-1 asks which parts predate the feedback
letter and which respond to it. **The letter is not in the repository and carries no date I can
cite**, so this report gives landing dates and lets the author draw the line. Where a document
states its own date, that date is used. Note that the bulk of the encoding-era commits carry
author date `2026-08-20` in a single cluster; **PR merge dates and in-document dated headers are
the more reliable timeline** and are what §3 uses.

---

# §2. The five must-haves

## MH-1 — Replace LLM-as-Judge with injected-flaw testing

**Slide claim:** *the committee asked for injected-flaw ground truth; that arm exists, ran, and
is the H3 evidence. The LLM ensemble is no longer a validator anywhere.*

### The mutation arm exists and ran

| Claim | Number | Artifact | Ref |
|---|---|---|---|
| Deterministic mutator | `uofa inject`, registered in the CLI | `src/uofa_cli/cli.py:68` (`inject` in the command import) | HEAD |
| Partition it scopes to | **21 base patterns**; compounds excluded | Decision 3, `docs/UofA_Decision_Record_2026-08-16.md:12` | `fad31cf5` |
| Arm M battery | **50 mutants, 17 operators, 3 substrates**, all live, all scored | `studies/phase2_5a/REPORT.md:273`; `run_arm_m.py:39` `SUBSTRATES`, pinned identically in `results.json` | `008626f2` |
| Which substrates | `morrison/cou1`, `morrison/cou2`, `nagaraja/cou1`. **No NASA file mutated** | `studies/ch4_numbers/LEDGER.md:153-163` | `008626f2` |
| MECHANICAL detection | **35/35 = 100.0%** over **13 patterns**, against a ≥95% bar. **Evaluated once** | `studies/phase2_5a/REPORT.md:113,129` | — |
| Overall detection | **287/378 = 75.9%** (Arm G, CE recall at v0.5.15.1) against ≥80% — **FAIL, reported as measured** | `REPORT.md:114`; `arm_g_results.json` | — |
| Negative-control clean rate | **97.1%** at v0.5.15.1 over **171 validated** packages | `REPORT.md:49,55` | — |
| False positives, per class | MECHANICAL 9 firings / JUDGMENT 1 over the 171-package holdout — **PASS** | `REPORT.md:115` | — |
| Aggregate Wilson over the gate | **35/35, [0.9011, 1.0000]** | `wilson_intervals.json` → `aggregate_over_gate` | — |
| Mutants that suppressed a baseline finding | **12 of 50, all twelve correct** | `REPORT.md:228` | — |

**The split verdict is the honest headline:** MECHANICAL passes, overall fails, and it is
reported as a split rather than resolved to one number (`REPORT.md:109-117`).

**Three disclosures that ride with it** and should be on the slide, because a committee will
find them otherwise:

- **Denominator 13, partition 17.** Four patterns are outside the gate: `W-EP-01` excluded as
  *unfireable*, and `W-ON-01`, `W-SI-01`, `W-SI-02` excluded for *no conformant mutant*
  (`wilson_intervals.json` `rows[].excluded_reason`).
- **Thin per-pattern n.** Five patterns rest on n=3 and two on n=1; every per-pattern Wilson
  floor sits below 0.5 (`gate_floor_below_half: true` on all in-gate rows). The **aggregate**
  is what carries weight, not the per-pattern figures (`REPORT.md:155-158`).
- **Three substrates, not five**, disclosed at the time and not retrofitted
  (`LEDGER.md:159-163`).

### The ensemble was demoted, and that is the framing sentence

Stage 4 repositioned the LLM judges from validators to **triage/screening**, with author
adjudication final.

| Claim | Number | Artifact |
|---|---|---|
| Cases the author adjudicated **blind** | **71** = 21 disagreement cases + a 50-case stratified spot-check | `studies/phase3_stage4/REPORT.md:23` |
| Weighted override rate | **0.2130** against target ≤0.10 — **FAIL as measured** | `stage4_readouts.json` `override.weighted_rate`; `REPORT.md:102` |
| EXISTING-RULE-MISBEHAVIOR | **7/12 = 0.583** overridden, weight 0.256 | `stage4_readouts.json` `override.per_stratum` |
| REAL-GAP | **12/12 = 1.000** overridden, **all twelve relocated to OUT-OF-SCOPE** | " ; `REPORT.md:109` |
| CORRECT-DETECTION + GENERATOR-ARTIFACT | **zero overrides across 23 cases** | `REPORT.md:35` |
| Verdicts across all 71 rows | CD 23 · OOS 21 · GA 19 · ERM 8. **No row ruled REAL-GAP or UNCERTAIN** | `REPORT.md:193-194` |
| Corpus-wide agreement | Fleiss κ **0.7685**; Cohen AB 0.6945 / AC 0.7595 / BC 0.8534; raw ≥2-of-3 **0.9954** over **4,556** cases | `stage4_readouts.json` `agreement` |
| Dedup sensitivity | override rate **0.2130 under both policies**; majorities changed **0** | `REPORT.md:158`; `dedup_sensitivity` |

**The decomposition is the point, and it is favourable without being spun.** The REAL-GAP
override is not judges hallucinating: a grounding check found the probe pointed at a Tier-1
candidate in 350 cases and at no candidate in 496, with a **0.0% override rate in both**
(`REPORT.md:132-133`), so the twelve relocations are a **schema-boundary** finding, not a judge
failure. ERM is an **ensemble-reliability** finding. **Neither is adverse to the catalog**
(`LEDGER.md:493-495`).

**Also state the small-denominator caveat:** REAL-GAP is 12 cases, OUT-OF-SCOPE is 3, and the
adjudication instructions call the latter *"indicative only"*. The report itself says 0.213
should read as *"roughly double the target"*, not to three decimal places (`REPORT.md:147-150`).

---

## MH-2 — Tools that hide the complexity

**Slide claim:** *the submit-button experience exists in demo form, and a full product design is
complete.* Public-side evidence only; see §5 for the private line.

| Capability | What it is | Ref |
|---|---|---|
| **Excel on-ramp, published** | `extract` → workbook → `import`, with no RDF exposure | `site/src/content/docs/start/from-excel.md`; siblings `install.md`, `first-uofa.md`, `index.md` |
| **`--protocol-check`** | The scriptable subset of the protocol on both `extract` and `import`, so no workbook reaches review still failing something a machine could catch. Checks: anchor column and per-row population, template placeholders in data rows, required-equals-achieved without waiver, ambiguity log, run-log lineage, minted namespace | `CHANGELOG.md` [0.12.0]; `fe62ce36`, `889d0a52` |
| **Deliberate asymmetry** | `extract` prints the table and leaves the exit code alone (a fresh workbook has no anchors — anchors are what review produces); `import` treats the same checks as gates | `CHANGELOG.md` [0.12.0] |
| **Evidence-where-it-lives ingest** | `uofa evidence inventory\|seal` reads native Ansys solver artifacts and Workbench project files **without the solver**, folds the seal into the package before signing, and redacts operator identity | PRs **#85**, **#90**; `dc60df76`, `d52df804`, `350ccee5`, `bbc5d958`, `a6bb0449`, `163151e4` |
| **Scale gate closed** | 405 MB gate — no archive holds solver results | `b59279fd` |
| **Prose-claim corroboration** | Evidence ingest corroborates prose claims against solver artifacts | `350ccee5` |
| **Space inspector** | Shows what the CLI read out of the solver artifacts | `00716a23`; `space/` |
| **Walkthrough** | Nagaraja evidence-folder demo written down | `5adcf8c6` |
| **Stranger-executable end to end** | Done-test: an LLM with only the protocol and the public CLI produced a package. **Run 2 PASSED all five pre-registered must-pass criteria** | `dev/build/encoding-prep/donetest/RESULTS.md:167-186` |

**The strongest MH-2 number is the done-test**, and it belongs on this slide as well as MH-5's:
a stranger session with no access to the pilot's artifacts produced a package that passes all
eight `--protocol-check` checks, unsigned, with **22 ambiguity entries, 6 marked ESCALATION**
(`RESULTS.md:176-186`).

---

## MH-3 — Simplify the hypotheses

**Slide claim:** *here are the committee's own simplified formulations with the measured values
dropped in — and here are the three places their proposed thresholds do not match the
measurement design.*

### The gate summary, as measured (this is the slide table)

Source: `studies/ch4_numbers/LEDGER.md:480-492` (E5, closed 2026-08-21).

| Hypothesis clause | Gate | Measured | Verdict |
|---|---|---|---|
| H2 detection F1, dev | ≥0.85 | **0.964** | pass |
| H2 detection F1, test | ≥0.80 | **0.954** | pass |
| H2 margin over the run's own null | "required margin" | **+0.004** | see below |
| H3 MECHANICAL | ≥95% | **100% over 13** | pass |
| H3 overall | ≥80% | **75.9%** | **FAIL** |
| H3 aggregate interval | — | 35/35, Wilson [0.9011, 1.0000] | — |
| Stage 4 spot-check override | ≤0.10 | **0.213** | **FAIL** |
| D6 equality, both directions | asserted | **HOLDS, 0 counterexamples** | pass |
| H1 per-substrate | — | **5 of 5 encoded**; 5/5 SHACL, integrity, rules; **3/5 complete** (2 blocked on SF-8) | pass |

Every row is on the **Demonstrated** rung. Both FAILs are reported as measured, per §0.1.

### H1 detail — five substrates

| Substrate | decision | MRL | complete | SHACL | integrity | rules |
|---|---|---|---|---|---|---|
| Morrison COU1 | Accepted | 2 | ✓ | pass | pass | pass |
| Morrison COU2 | Not accepted | 5 | ✓ | pass | pass | pass |
| Nagaraja COU1 | Accepted | 3 | ✓ | pass | pass | pass |
| NASA take-off | Accepted | 3 | **NO — SF-8** | pass | pass | pass |
| NASA cruise | Not accepted | 4 | **NO — SF-8** | pass | pass | pass |

Re-derive: `python studies/ch4_numbers/derive_h1_tier_table.py` → `h1_tier_table.json`
(`LEDGER.md:113-116`). The script **exits 1 if any substrate fails a check it should pass**.

### The three deltas the author should address, not paper over

**Delta 1 — H2's headline is +0.004 over its own null.** Mean overall F1 dev **0.964**
(`extract_eval_v1.md:58`, `a487d203`); the run's own null — the pack's fixed checklist, zero
parameters, **reads none of the input** — scores **F1 0.960** (`extract_eval_v1.md:24-26`). The
committee's proposed *"F1 ≥0.85 on 50 documents"* would be **passed by a constant checklist**.
The honest framing is that F1-on-synthetic-bundles is close to uninformative for this construct,
and the real-corpus number is the one that discriminates: **3/33 = 0.0909** held-out under
Decision 7's split (`LEDGER.md:244-262`; `studies/real-document-rescore/FINDINGS.md`).

**Delta 2 — H3's "<10% false positives" is not the shape the measurement takes.** The repo
measures a **negative-control clean rate of 97.1%** on a 171-package holdout *constructed to
carry no catalog-detectable weakness* (`REPORT.md:57`), and separately reports per-class firings
(MECHANICAL 9, JUDGMENT 1). The scope statement rides with the 97.1% wherever it appears.

**Delta 3 — the draft's own H1 threshold does not match the measured completeness.** The draft
states *"≥90% completeness"* (draft ¶439, see §4b). Measured completeness is **3 of 5 = 60%**,
blocked on SF-8. The ledger records H1 as **pass** on the strength of 5/5 SHACL, integrity and
rules with the completeness caveat *inside the rows*. **These two statements need reconciling
before Saturday** — this is the single largest internal inconsistency the dig surfaced.

---

## MH-4 — Preliminary-validation framing, prototype framing, open-source release

**Slide claim:** *the artifacts already practice the honest-limitations discipline; the
manuscript will state it.*

### Open-source state

| Claim | Evidence |
|---|---|
| Public repo, published site | `github.com/cloudronin/uofa`; `site/` deployed via `.github/workflows/deploy-site.yml` |
| Released wheel | **v0.12.0**, 2026-08-20 — the encoding protocol and the mechanical half of it as a gate | `CHANGELOG.md` [0.12.0]; `05186310`; PR **#92** |
| **Cross-version verify** | Both NASA substrates **imported and signed under `uofa-cli 0.11.0`, verify under the published `uofa 0.12.0` wheel**, in a clean venv, **with the packages copied outside the repository** so nothing resolves from the tree | `LEDGER.md:395-404`; `aero-cou2/RUN_LOG.md:92-96`; `AUTHOR_SUMMARY_COU2.md:122` |

**That last row is the strongest MH-4 sentence available:** *a package signed under one version
verifies under a later published tool, on a different machine, outside the repository.* The
ledger calls it the **exit-is-free claim with a measurement behind it** (`LEDGER.md:393-404`).

### The disclosure discipline is already practised, not promised

| Artifact | What it does |
|---|---|
| **SF-1 … SF-8** | Eight filed schema/tooling findings, numbered in filing order, including a ruled collision where a ruling document's "SF-1/SF-2" means the register's **SF-4/SF-5** | `docs/SCHEMA_FINDINGS.md:17-27` |
| **SF-8** | *No on-ramp package can bind the claim its evidence supports* — and **the definition of `complete` was explicitly NOT amended**, because that would tune the gate to the tooling: *"the retroactive-threshold move in a new costume"* | `SCHEMA_FINDINGS.md:262,296-300` |
| **Boundary finding, four routes** | Schema audit (empty `AssuranceClaim` interior), INV-21 (seven incompatible `bindsClaim` conventions), Stage 4 (all twelve REAL-GAP rows relocated), and the H1 derivation script measuring the same boundary from the tooling side. **"Four routes, four methods, one boundary."** | `SCHEMA_FINDINGS.md:285-292` |
| **Decline-don't-invent** | A-10 in the protocol; the source-absent and silence rulings | `docs/Encoding_Protocol_v0_1.md:163` (A-10) |
| **Confirm-only instrument family** | A named methods-lessons thread: *a test whose green means nothing* | `LEDGER.md:173-176`; `docs/UofA_Decision_Record_2026-08-19.md:229` |

### Future-work channel

Protocol v0.2 accumulation pile (`docs/protocol-v0_2-notes.md`, `9e8e0c94`, PR **#95**); the
schema increment (SF-4/5/6 filed for it); multi-encoder replication as named future work (draft
¶416); and the A3 bankings — **Maquer** as the post-defense clean external-negative upgrade and
**Kurtz** as a post-defense model-risk-arm candidate (`docs/UofA_Decision_Record_2026-08-16_Addenda.md`
§ R-A3-CLOSE).

---

## MH-5 — Human reviewer role, identity, and bias

**The strongest section.** Slide claim: *who reviewed is named, how is a committed protocol,
independence is a stated limitation with measured evidence of which direction the bias runs, and
raw-versus-corrected are never conflated.*

### The protocol is committed and executable by a stranger

| Claim | Evidence |
|---|---|
| **Encoding Protocol v0.1**, committed | Part A = 13 executable steps each ending in a check; Part B = disposition rules with a verdict rule per pattern family and an explicit mechanical-versus-judgment class; Part C = rationale cited to the Johnson pilot by finding number | `docs/Encoding_Protocol_v0_1.md`; `8928cbb8`; PR **#91** |
| Part B **calibrated against the 71** | Each rule's Calibration column says what it was derived from, **and which are not yet calibrated** | `CHANGELOG.md` [0.12.0]; `dbcb738e` |
| Named-reviewer requirement | *"the review in A-6 has not happened until a named person performs it"* | `Encoding_Protocol_v0_1.md:229` (A-13) |
| Judgment-rule definition | *"a rule whose verdict requires a human"* | `Encoding_Protocol_v0_1.md:251` |
| Version-stamped | An encoding records the protocol version that governed it, so a v0.1 package stays readable when v0.2 changes a rule | `CHANGELOG.md` [0.12.0] |

### The done-test — two isolated stranger sessions, pre-registered pass line

| Claim | Number | Ref |
|---|---|---|
| Pass line **pre-registered before run 1** | header committed before the run | `donetest/RESULTS.md:3,41` |
| Run 1 | Recovered **8 of 8** predeclared credibility levels correctly, **by a method it devised itself**, pilot answers physically absent. **Failed** must-pass #1 (protocol-check) — no package survived | `RESULTS.md:84-119` |
| Run 2 (`claude-opus-5`, 74 turns, 1759s) | **PASS on all five** must-pass criteria; all eight protocol checks green; unsigned; 8/8 levels exact with bounding boxes; **22 ambiguity entries, 6 ESCALATION** | `RESULTS.md:167-186` |
| The claim | **"Three sessions, three methods, one answer"** — levels 3, 3, 1, 3, 4, 4, 3, 2 | `RESULTS.md:188-193` |
| Divergence, reported | Run 2 declined three cross-standard **renames** the pilot judged near-mechanical, which **drops the two-level exceedance** that is the source's most interesting result. *"A-10 as written permits a conservative encoder to lose it."* | `RESULTS.md:212-217` |
| Residual defect, marked AUTHOR | The namespace check was weaker than the namespace rule; a reserved example domain cleared it. **Fixed** — the whole RFC 2606 / RFC 6761 family is now refused | `RESULTS.md:218-225`; `fe62ce36`; `CHANGELOG.md` [0.12.0] |

### Three governed review passes, all signed

| Pass | Volume | Ref |
|---|---|---|
| **Johnson** (NTRS 20200002832) | **28 ambiguity entries** and **eleven firings** adjudicated: 8 Confirmed (one with `offsetRationale`, designated the v0.2 worked example), 3 Not Applicable by scoping ruling, **none Overruled on merit**. Silence sweep over fifteen factors. Signed | `dev/build/pilot-johnson/Johnson_Author_Verdict_Record.md:23-46`; PR **#94**; `d633df0e` |
| **Aero COU1** | Ledger totals **18 confirmed · 29 corrected · 1 blanked · 48 decisions**; `Accepted (with conditions)` stands over displayed weaknesses | `aero-cou1/AUTHOR_SUMMARY_COU1.md:25,83-89`; PR **#97** |
| **Aero COU2** | The `Not accepted` arm; public-wheel round-trip **pass** | `aero-cou2/AUTHOR_SUMMARY_COU2.md:122`; PR **#97**; `76e6dae8` |

**Attribution, including the defect and its correction.** Operator identity resolves from
`UOFA_ASSESSOR`, then `git config user.name`, then `$USER`. The 2026-08-20 import **wrote the
wrong operator into the signature before anyone noticed**; corrected by re-importing with
`UOFA_ASSESSOR` set and re-signing (`docs/protocol-v0_2-notes.md:33-35`; `07484623` *"Johnson
pilot: correct the operator attribution and re-sign"*). **Put this on the slide.** A reviewer-
identity must-have answered with a story that includes catching and fixing an identity defect is
worth more than one answered with a clean assertion.

### The bias story inverts — this is the section's best card

The author adjudicated 71 cases **blind** and overrode **against his own instrument** at
**0.213**, failing the ≤0.10 gate. The overrides run **7/12 on ERM** and **12/12 on REAL-GAP**,
while CORRECT-DETECTION and GENERATOR-ARTIFACT took **zero overrides across 23 cases**
(`stage4_readouts.json`; `REPORT.md:35,87-102`). The author's review made the results
*worse*-looking, not better. **That is the direction an honest reviewer's bias runs**, and it is
measured rather than asserted.

### Raw versus corrected, never conflated

H2 measures the **raw extractor** against annotation-protocol references; the governed passes
measure the **corrected pipeline**. The separation is enforced at the protocol boundary:
*"Evaluation references for H2 are outside this protocol. They are built under the annotation
protocol and never regenerated through the extract path, because H2 measures agreement with a
corrected self and an extractor-derived reference would make the extractor a party to its own
evaluation"* (protocol §1, quoted at `dev/build/encoding-prep/BOLOGNA_STATUS.md:20-24`). That
rule is what disqualified Bologna from A3 (R-B, addenda).

### The limitation, already written down

*"The credibility corpus and corresponding weakener catalog were developed by a single author,
introducing encoder bias… Validation across multiple encoders therefore remains future work."*
— draft ¶416, §3.10.5. See §4b for the manuscript work this needs.

---

# §3. Timeline — the deck's spine

Dates from PR merges and in-document dated headers, which are more reliable than the compressed
author dates (see the caveat at the top).

| Date | Landing | Ref |
|---|---|---|
| **Aug 16** | Twelve author decisions ruled and put under version control | `docs/UofA_Decision_Record_2026-08-16.md`, `fad31cf5` |
| **Aug 17** | M5 re-baseline; P2-A close-out | PRs **#71**, **#72** |
| **Aug 18** | INV-18 → INV-20; argument-layer prototype; OOS backtracking fix; JSON Schema versioned | PRs **#74–#81** |
| **Aug 19** | INV-21, INV-22; **Ch4 numbers and repairs** — Stage 4 readouts, the R1a fix, the numbers ledger | PRs **#82–#84** |
| **Aug 20** | Ansys evidence ingest — seal and read solver artifacts without the solver | PR **#85** |
| **Aug 20** | Protocol outline v3 → draft → **done-test run 1** (recovery converged, 3 text defects) → fixes → **run 2 passes all five** | `d9b544b8`, `f76b982f`, `f3f64ae7`, `fe104b38` |
| **Aug 20** | **Encoding Protocol v0.1 finalized**; Part B derived from the Stage 4 adjudications | `dbcb738e`, `8928cbb8`; PR **#91** |
| **Aug 20** | **Release v0.12.0** — the protocol, and the mechanical half of it as a gate | `05186310`; PR **#92** |
| **Aug 21** | **Johnson signed** — first governed encoding, adjudicated; operator attribution corrected and re-signed | PR **#94**; `d633df0e`, `07484623` |
| **Aug 21** | **Aero COU1/COU2 signed**; public-wheel cross-version round-trip green | PR **#97**; `76e6dae8` |
| **Aug 21** | Protocol v0.2 accumulation pile opened | PR **#95** |
| **Aug 21** | **SF-8 filed; ledger closed at 98 entered / 0 pending / 0 escalation** | PR **#100**; `70657c8f`; `LEDGER.md:497-519` |
| **Aug 21** | Bologna disqualified from A3 (R-B); A3 search closed, Johnson takes the arm (R-A3-CLOSE) | PRs **#98**, **#99** |

---

# §4. Praxis-relevant work outside the five

**The numbers ledger as a discipline.** `studies/ch4_numbers/LEDGER.md` closed at **98 entered,
0 PENDING-ENCODING, 0 ESCALATION** (`LEDGER.md:497-519`). Every Ch4 figure carries an artifact
and a commit, and figures under `dev/build/adversarial/` are force-tracked so they re-derive
from a clean clone (`LEDGER.md:521+`). The chapter cannot cite a number that has no
re-derivation path. That is a methods contribution in its own right and it is worth a slide.

**The encoding protocol as a contribution.** Not merely a procedure but one **validated by
execution**: two isolated stranger sessions, a pre-registered pass line, and three independent
methods converging on the same eight levels (`donetest/RESULTS.md`). Most process contributions
in this literature are asserted; this one has a test.

**The boundary finding's fourth route.** The H1 derivation script — *"an instrument built for
something else entirely"* — measured the assurance-case boundary from the tooling side,
independently of the schema audit, INV-21, and Stage 4 (`SCHEMA_FINDINGS.md:285-292`). Four
methods, one boundary.

**The confirm-only instrument family, now a named thread.** *A test whose green means nothing.*
The tally was three as of Aug 19 (`docs/UofA_Decision_Record_2026-08-19.md:229`;
`studies/ch4_numbers/SESSION-REPORT-2026-08-19.md:80`) and grew through the encoding era — the
vacuous NASA annotation snapshots, whose `targetClass uofa:UnitOfAssurance` matched nothing, are
the sharpest instance (`LEDGER.md:131-137`). **The work item's "now 7" could not be confirmed
from a committed tally**; the register I found stops at three plus later un-numbered instances.
**See §5 — claim the pattern, not the count.**

**The worked-example pair.** Aero COU1 `Accepted (with conditions)` and COU2 `Not accepted`, on
the same source under the same protocol — opposite decisions, both governed, both signed
(`LEDGER.md` H1 table; `de04b7df` queues COU2 as the v0.2 Not-accepted worked example).

**The governed pipeline exposing what hand-authoring hid.** *"The two packages produced under
the governed pipeline are precisely the ones that expose the claim gap, because hand-authoring
had been silently supplying it"* (`LEDGER.md:145-150`). A finding that reflects well on the
process and is worth stating exactly that way.

**Writing-queue position.** With R5 discharged, SF-8 filed and the ledger closed, no
investigation blocks the manuscript. Position 1 is the encoding protocol's manuscript treatment,
now describing a five-package, four-times-triangulated reality.

---

# §4b. Manuscript inputs

**Where the draft lives.** The canonical draft is **outside the repository**, at
`~/Dropbox/Praxis/Writing/Drafts/UofA Praxis Draft 072726.docx` (2026-07-26, 544 paragraphs).
It **is** reachable, so the locations below are cited by **paragraph index and heading** from
that file rather than mapped against planning docs. **The author reconciles against Word himself
— paragraph indices are stable for this file only and will shift on the next edit.**

**Chapter 4 is a skeleton.** ¶425-476 are planning prose describing what each section will do,
not results text. That is good news: §4b's Ch4 fact sheet has no stale prose to displace, only
an outline to fill.

## Manuscript change inventory, per must-have

### MH-3 — every hypothesis statement and gate definition

| Location | Current text (abridged) | Replace with | Artifact |
|---|---|---|---|
| **¶103**, §1.6 | H1: *"≥90% completeness, ≥95% SHACL pass rate, 100% signature validation"* | 5/5 encoded; 5/5 SHACL, integrity, rules; **3/5 complete, 2 blocked on SF-8** | `LEDGER.md:118-124` |
| **¶105**, §1.6 | H2: *"mean F1 … exceeds the protocol threshold, per-factor F1 holds across the 19 … factors, results reproduce on the Morrison and aerospace regression cases, bundle-level crash rate is zero"* | 0.964 dev / 0.954 test, **and the null at 0.960, margin +0.004** | `extract_eval_v1.md:24-26,58`, `a487d203` |
| **¶107**, §1.6 | H3: *"≥80% of confirmed present specifications generates either COV-HIT or COV-HIT-PLUS, and at least one COV-MISS pattern … validates"* | MECHANICAL 100%/13 pass; overall 75.9% FAIL; NC clean 97.1% | `phase2_5a/REPORT.md:113-115` |
| **¶439**, §4.2 | *"≥90% completeness, ≥95% SHACL, 100% signature, sufficiency ≥4/5"* | **Reconcile with ¶103 and with the measured 3/5** — see MH-3 Delta 3 | `LEDGER.md:118` |
| **¶441**, §4.3 | *"manual versus AI-assisted … 50-bundle stratified synthetic corpus"* | add the null-control framing | `LEDGER.md:230-232` |
| **¶447**, §4.4 | Already carries an **H3 operationalization amendment**: *"the dependent-measure outcome classes are restated in the vocabulary the battery actually emits (COV-HIT-PLUS / COV-WRONG / COV-CLEAN-WRONG / GEN-INVALID; **no COV-HIT or COV-MISS rows occur**)"* | **This is the COV-HIT/COV-MISS fix, already drafted.** ¶107 is the location that still uses the dead vocabulary | ¶447 |
| **¶382**, §3.7 | Coverage analysis vocabulary | align with ¶447's amendment | ¶447 |

**The COV-HIT/COV-MISS finding, stated plainly:** the hypothesis in ¶107 is written in a
vocabulary **the battery never emits**. ¶447 already knows this and says so. **¶107 is the
statement that must change**, and ¶447 supplies its replacement text.

### MH-4 — claim-strength, open-source, Ch5

| Location | What it needs |
|---|---|
| **¶110-111**, §1.8 Research Limitations | Already hedged appropriately (*"indirect manner via structured proxies… does not rely on the results of practical FDA review"*). **Add the prototype/preliminary sentence here** — it is the natural home |
| **¶291-292**, §2.9 | Existing future-work statements (coverage bounded by published typologies; non-V&V 40 frameworks via pack architecture) — the **siblings** the committee's "real-world validation with human experts" item should land beside |
| **¶416**, §3.10.5 | *"Validation across multiple encoders therefore remains future work"* — **already written**. The new Ch5 item goes beside it, not duplicating it |
| **¶420**, §3.10.7 | *"The LLM-as-judge methodology remains the principal validity limitation"* — **needs revision under MH-1**: the ensemble is now triage, not a validator, so this caveat's scope narrows. See MH-1 below |
| **¶473-474**, §4.7 | The bridge to Ch5 — *"what the results mean, limitations, and future work"*. Currently one planning line |
| **§4.6 Execution Findings, ¶470-472** | Lists F1/F2, the masked-bug pair, the stale manifest count (**4,221 as-generated vs 4,605 analyzed**), and unrun secondary batteries. This is where the prototype framing has the most raw material already assembled |
| **Open-source statement** | **No location currently exists.** ¶86 discusses ENRICHMENT; ¶518 cites Pathmanathan's call for public examples. The release statement belongs in §1.7 Scope (¶108) or §4.7, and the strongest sentence is the **cross-version verify** (`LEDGER.md:395-404`) |

### MH-5 — reviewer role, identity, bias

| Location | Current | The artifact that now answers it |
|---|---|---|
| **¶388-389**, §3.9 | *"LLM-as-judge ensemble, with author adjudication on disagreement"* | Reposition: judges are **triage**; author adjudication is the validator. `phase3_stage4/REPORT.md` |
| **¶399-400**, §3.9.5 Author Adjudication | Describes escalation and the arbiter, but **does not name the adjudicator or state a protocol** | **Who:** the author, named, `UOFA_ASSESSOR` (`protocol-v0_2-notes.md:33-35`). **How:** `Encoding_Protocol_v0_1.md` Part A §§A-6, A-13. **Recorded:** the three verdict records and review ledgers |
| **¶415-416**, §3.10.5 | Encoder bias stated; mitigation asserted | Add the **measured direction**: author overrode his own instrument at 0.213, 12/12 on REAL-GAP, 0/23 on CD+GA |
| **¶419-420**, §3.10.7 | LLM-anchored caveat as *principal* limitation | Narrow it — the mutation arm is the H3 evidence and it is deterministic |
| **Raw vs corrected** | **No location states the separation** | Protocol §1's exclusion rule, quoted at `BOLOGNA_STATUS.md:20-24`, and R-B as the case where it was enforced against a convenient candidate |
| **Reviewer identity implied but unstated** | ¶311, ¶343, ¶385-386, ¶402 all say "expert adjudication" / "author adjudication" without naming or procedure | Each takes a pointer to the committed protocol |

### MH-1 — where H3's story is currently told via the ensemble

**Sections to re-center on the mutation arm (list, not a rewrite):** §3.9 (¶388-389), §3.9.1
Six-Verdict Classification (¶390-391), §3.9.2 Production Judge Ensemble (¶392-393), §3.9.3
Calibration (¶394-395), §3.9.4 Cross-Family Independence and the Circularity Defense (¶396-398),
§3.9.5 Author Adjudication (¶399-400), §3.9.6 Catalog Formalization (¶401-402), §3.9.7 Prior Art
(¶403-404), §3.10.7 (¶419-420), and §4.4 (¶446-447).

**The circularity defense at ¶396-398 is the highest-value single edit:** it currently defends
the ensemble's independence. Under MH-1 the defense is no longer needed in that form, because
**the H3 gate is measured by deterministic injection, not by judges**.

### MH-2 — toolchain-burden text

Where the draft describes the toolchain burden, the refs that let it claim a hidden-complexity
path exists in demo form: the on-ramp (`site/src/content/docs/start/from-excel.md`),
`--protocol-check` (`CHANGELOG.md` [0.12.0]), evidence ingest (PRs #85/#90), and the done-test
(`donetest/RESULTS.md:167-193`). **The specific burden paragraphs were not located** — §2.4-2.6
discuss tooling generally but no paragraph states the burden as such. **Flagged as a gap for the
author to point at.**

## Ch4 writing inputs, per section

Superseding stale figures in earlier planning docs. Version labels are mandatory.

**§4.1 / RQ1 — tier table.** Five substrates, table above. All five pass SHACL, integrity and
rules; three complete; two `NO — blocked on SF-8`. Re-derive: `derive_h1_tier_table.py` →
`h1_tier_table.json`. **The lead sentence turns on n, and n is now 5** (`LEDGER.md:150-152`).
The two NASA rows were **repointed on 2026-08-21** from the vacuous annotation snapshots to the
signed protocol encodings (`LEDGER.md:126-137`).

**The Morrison COU1 count trio — the stale-number warning.** Three values are in circulation and
**every sentence citing one carries its version label** (`LEDGER.md:71-88`):

| Value | Catalog / tag | Status |
|---|---|---|
| **14** | `v0.4.0-nafems` frozen demo tag | **Not superseded** — the frozen tag; `CONTRIBUTING.md` says do not change this commit |
| **11** across 5 patterns | v0.5.15.1 / tag `v0.7.1`, **9 of the 11 vacuous** | **Not wrong** — what v0.7.1 reproduces |
| **17** across 8 patterns | **current catalog, post-R1a** | **What HEAD reproduces — the current value** |

Unlabelled locations needing repair: `README.md:167`, `docs/design.md:9`. Correctly labelled:
`site/.../nafems-2026.md:21`. And a guard that does not guard:
`site/scripts/check-pages.mjs:90,118` asserts the **literal strings**, so it will keep passing
while the page drifts (`LEDGER.md:96-101`).

**§4.2 / H2.** Headline 0.964 dev, 0.954 test, null 0.960, margin +0.004
(`extract_eval_v1.md:24-26,58`, `a487d203`). Real corpus under Decision 7: **3/33 = 0.0909**
held-out; sensitivity all six **3/56 = 0.0536**; every hit from one paper (`ared`, the shortest
at 205 sentences); five of six score zero; Wilson [0.018, 0.146]; claim-density 0.000 before and
after, **split-invariant** (`LEDGER.md:244-262`).

**§4.3 / H3.** MECHANICAL 35/35 = 100% over 13; overall 287/378 = 75.9% FAIL; NC clean 97.1%;
Wilson aggregate [0.9011, 1.0000]; 50 mutants / 17 operators / 3 substrates.

**§4.3.6 — the generation arm, adjudicated.** `LEDGER.md:28-66`. Stage 4 figures as in MH-1.

**§4.4 / D6 — the external arm.** Validation results **427**; W-AL-01 fires **384**, clears
**43**; models **43**; **both directions HOLD, 0 counterexamples**. Re-derive with
`studies/d6-rederivation/rederive.py`, which **refuses to run against any revision other than
the pinned one** (`LEDGER.md:352-370`, `aa76cc6e`).

**§4.5 — gate summary.** The nine-row table in MH-3 above, entered as E5 and closed 2026-08-21.

**The boundary section.** Four routes, four methods, one boundary
(`SCHEMA_FINDINGS.md:285-292`), plus the un-amended `complete` definition as the recorded
refusal.

**The two cross-version-verify sentences.** Signed under `uofa-cli 0.11.0`, verified under the
published `uofa 0.12.0` wheel, clean venv, package outside the repository
(`LEDGER.md:395-404`; `aero-cou2/RUN_LOG.md:92-96`). They land in §4.1 (as a property of the
packages) and §4.7 or Ch5 (as the exit-is-free claim).

---

# §5. DO-NOT-CLAIM

| Item | Why | What may be said instead |
|---|---|---|
| **Credenza repo, build plan, product design detail** | Private | Exactly one abstract sentence: *"a productized review workspace is designed and in build."* **No repo pointers, no screenshots, no timeline** |
| **Anything from `uofa_labs`** | Out of scope for this repo's evidence | — |
| **Protocol v0.2 items** | **Queued, not done** — the accumulation pile is open (`docs/protocol-v0_2-notes.md`, PR #95) | *"v0.2 is accumulating against recorded findings"* |
| **"Confirm-only instrument family, now 7"** | **Could not be confirmed.** The committed tally reads **three** (`Decision_Record_2026-08-19.md:229`; `SESSION-REPORT-2026-08-19.md:80`), with later instances noted but not renumbered | Claim the **pattern** and the three-plus-instances, not a count of 7 |
| **H1 as "≥90% completeness met"** | Measured completeness is **3/5 = 60%**, blocked on SF-8 | *"5/5 on SHACL, integrity and rules; 3/5 complete, with the two gaps carrying a filed finding number"* |
| **H2's 0.964 without its null** | The constant checklist scores 0.960 | Always quote the pair, margin **+0.004** |
| **The 97.1% without its scope** | It is measured on a holdout **constructed to carry no catalog-detectable weakness** | The scope sentence rides with the number (`REPORT.md:57`) |
| **0.213 to three decimals** | REAL-GAP n=12, OUT-OF-SCOPE n=3; instructions call the latter *"indicative only"* | *"roughly double the target"* (`REPORT.md:147-150`) |
| **Per-pattern Arm M rates** | Five patterns at n=3, two at n=1; every in-gate Wilson floor is below 0.5 | Cite the **aggregate** 35/35 with its interval |
| **"Five substrates mutated"** | Arm M mutated **three**; NASA files were not mutated | *"three substrates, disclosed at the time"* |
| **A3 as an encoded external arm** | **No A3 encoding exists or is planned.** R-A3-CLOSE assigns the arm to the Johnson pass with the dual role disclosed | *"the external arm is the Johnson governed pass, dual role disclosed"* |
| **Unmerged work at report time** | — | Nothing is unmerged as of `28b036cf`; **this report's own branch is not merged** |
| **Any number without a re-derivation pointer** | Ledger discipline | If it is not in `LEDGER.md` with an artifact, it does not go on a slide |

---

## What this report is not

It does not rewrite any manuscript text, and it does not decide what Saturday's scope should be.
It maps evidence to must-haves and flags what should not be claimed. **Two items need an author
decision before the deck is built:** the H1 completeness reconciliation (MH-3 Delta 3) and
whether the "confirm-only, now 7" count exists in a source this dig did not reach.

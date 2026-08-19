# UofA Chapter 4 Numbers and Repairs Spec v1.0

Status: ACTIVE
Date: 2026-08-19
Owner: Vishnu Vettrivel
Relates to: UofA_Unified_Repair_Spec_v2_1 (writing position 8 preconditions), Stage 4 readout run of 2026-08-19, Decision Record 2026-08-16
Execution: Claude Code session; author reads escalations only
Purpose: produce every number, table, statistic, and committed artifact that writing position 8 (the results cluster) and the Chapter 4 draft will cite, so that when the author writes prose, every figure already has a committed artifact behind it at a stated version. This spec produces no manuscript prose. Writing-queue positions remain author-only.

## 0. Governing rulings (2026-08-19, author)

These three rulings were taken in conversation on 2026-08-19 and govern this spec. The author will commit a Decision Record addendum recording them; this spec may prepare the addendum text for author sign-off (item W11) but the author commits it.

**R1 — INV-21, three parts.**
- R1a: W-EP-01 drops its claim type guard. The line `(?claim rdf:type uofa:Claim)` is removed at all three rule sites. W-EP-01 fires on any `bindsClaim` target lacking derivation, restoring the behavior the 2026-04-26 corpus was recorded under. No typed-claim requirement is introduced.
- R1b: Stage 4 adjudicated against recorded generation-time `rules_fired`. The completed worksheet stands as ruled, including rows #3 and #65. The Stage 4 report carries one disclosure: 63 of 65 comparable packages have diverged from their recorded `rules_fired` under the current catalog, traced to the guard added in `205cc90e`.
- R1c: P25-A numbers stand as measured at v0.5.15.1. The R1a fix lands after, as a disclosed post-freeze correction. No re-run of P25-A. The chapter states catalog versions explicitly wherever a number is cited.

**R2 — Tier-1 restatement, Reading B.** The six Tier-1 candidates are restated as "6 of 6 confirmed as real weaknesses, located at the schema boundary rather than inside catalog scope." The finding relocates from RQ3 to RQ1. The author writes the reclassification paragraph (instrument built for one question, answered another, OUT-OF-SCOPE policy quoted); this spec digs its supporting numbers (W10).

**R3 — INV-22 out of scope.** The 16 OOS calibration packages are deferred post-defense. One line in Ch5 future work, authored later. No work item in this spec.

**Chapter placement (author choice, this session):** Stage 4 ensemble and adjudication numbers get a new subsection 4.3.6 ("the generation arm, adjudicated") in the Results Chapter structure; the REAL-GAP / OUT-OF-SCOPE mass is handed forward to §4.5 as the third side of the boundary. The Results Chapter Structure and Story Guide in the v2.1 doc otherwise holds.

## 1. Context: what is already done

- P25-A complete 2026-08-16: Arm M `008626f2`, Arm G `e40d7819`, report at `studies/phase2_5a/REPORT.md`, M5 rebaseline `98959943` (2026-08-17). GATE-H3 evaluated once, split verdict: MECHANICAL 100% over 13, overall 75.9% vs ≥80% FAIL, reported as measured.
- Stage 4 author adjudication complete: 71/71, clean verdict strings. Readouts run 2026-08-19: pairwise Cohen's κ 0.695 (A–B), 0.759 (A–C), 0.853 (B–C), Fleiss 0.768, raw 2-of-3 convergence 0.9954, all at n = 4,556 after last-wins dedup. Weighted spot-check override rate 0.213 vs ≤0.10 target, FAIL. Author-vs-judge over the 21-case queue: A 1/21, B 8/21, C 8/21. Grounding checker passes: 0.0% zero-echo across all categories, median 15–17 package-distinctive tokens echoed.
- `uofa inject` mutator exists, wired into the CLI, operators over all 21 base patterns.
- Known open defect: two dedup policies in the pipeline (`align_trios` last-wins vs grounding checker first-wins), 47 judge-case pairs where a retry changed the verdict.

## 2. Work items

Strict rule inherited from the repair spec: verify every load-bearing claim against the artifact tree before writing it into an output, or mark it INVESTIGATION and confirm before proceeding. Read `.gitignore` before concluding anything is untracked.

### W1 — Stage 4 report (1–2h)

Write `studies/phase3_stage4/REPORT.md` following the `studies/phase2_5a/REPORT.md` precedent (structure, tone, versioned-artifact citations).

Contents, all already computed on 2026-08-19; re-derive each from disk rather than transcribing from conversation:
1. Corpus-wide agreement: three pairwise κ, Fleiss κ, confusion matrices, with N stated per pair and the dedup policy named (last-wins via `align_trios`).
2. Retry characterization: per-judge extra-record counts (A 549, B and C to be re-derived), the 47 self-conflicting pairs, Judge A characterized separately (1/21 queue agreement, most retries, most self-conflicts).
3. Spot-check override table: per-stratum n, overridden, rate, weight, contribution; weighted total; gate verdict FAIL as measured. Include the decomposition: ERM 7/12 (4 → GENERATOR-ARTIFACT, 3 → CORRECT-DETECTION), REAL-GAP 12/12 → OUT-OF-SCOPE, zero overrides on CORRECT-DETECTION, GENERATOR-ARTIFACT, OUT-OF-SCOPE.
4. Author-vs-judge over the 21 disagreement cases, including the 4 cases where the author's verdict matched no judge.
5. Grounding readout with its scope sentence (token overlap measures package-reading, not verdict correctness).
6. Caveats: small denominators (12, 3); judges judged generation-time behavior (R1b disclosure with the 63/65 figure and `205cc90e`); rows #3 and #65 named; the dedup-policy split with W2's sensitivity result.
7. The R1b basis statement, verbatim from §0 above.

Done-gate: every number in the report re-derivable by a command or script named in the report; no number sourced from conversation memory.

### W2 — Dedup sensitivity (30 min; gates W1 item 3)

Recompute the 50 convergent-case ensemble majorities under first-wins dedup. Report whether any of the 50 majority verdicts changes, and whether the override count moves. If unchanged: one sentence in W1's caveats. If changed: report the override rate as a range across both policies, escalate before W1 finalizes, and identify which of the 47 pairs did it.

Also reconcile forward: recommend (do not implement) a single dedup policy for the pipeline, with the tradeoff stated, as an escalation note for the author.

### W3 — INV-21 fix (1h; after W1 and W2 land, per R1c ordering)

1. Remove `(?claim rdf:type uofa:Claim)` at the three sites in `packs/core/rules/uofa_weakener.rules` per R1a.
2. Run the full test suite; run the catalog against the six canonical examples and record the before/after `rules_fired` delta.
3. CHANGELOG entry as a disclosed post-freeze correction, dated, citing INV-21 and R1a, stating which measurements precede it (P25-A at v0.5.15.1, Stage 4 per R1b) and that neither is re-run.
4. Confirm compound-rule cascade behavior (COMPOUND-01/03) on the canonical examples matches expectation after the fix.

Escalate if: the fix changes any rule's behavior other than W-EP-01 and the two compounds, or any test fails for a reason other than the intended firing change.

### W4 — W-EP-01 contrast variant (20 min; pinned pre-fix)

Carry 1 from the repair spec, build-before-cite. The chapter sentence describes pre-fix behavior, so build and run at the pre-fix ref: check out the commit immediately preceding W3's fix, construct two mutants on one substrate (claim typed `uofa:Claim` vs typed `uofa:AssuranceClaim`), run the engine, record that the first fires W-EP-01 and the second does not. Commit the fixture and result under `studies/phase3_stage4/` with the ref pinned in the output. This is the machine verification for the "guard on an undeclared class" sentence.

### W5 — Wilson intervals (1h)

Carry 2. Script over the Arm M manifest and results: per-pattern Wilson 95% CI, added as a column to the per-pattern table, n per row stated (five patterns at n=3, two at n=1 expected; verify). Output alongside the Arm M table source so position 8 consumes one artifact. Flag any pattern whose interval floor sits below 0.5 at its measured n; those rows need the qualitative sentence the repair spec anticipated.

### W6 — The Chapter 4 numbers ledger (3–4h; consumes W1, W2, W5, W7)

The core item. Produce `studies/ch4_numbers/LEDGER.md`: one row per figure the Results Chapter Structure guide and §4.3.6 will cite. Columns: claim (one sentence), value, catalog/spec version it was measured at, artifact path, commit ref, re-derivation command. Sections mirror the chapter:

- 4.1 / H1: tier table values (Morrison COU1/COU2, Nagaraja, NASA take-off/cruise verdicts), completeness, SHACL pass, signature validity, the W-ON-02 observation (fires on 65/71 queue packages; verify against canonical encodings too).
- 4.2 / H2: headline vs null (0.964 vs 0.960 constant checklist), margin over null, attribution vs permutation null, real-corpus per-document figures, development-vs-held-out tier split per Decision 7, claim-density-zero count (96 rationales).
- 4.3 / H3: Arm M per-pattern table with W5 intervals; MECHANICAL 100% over 13 with the denominator-17 partition and four silent-null rules disclosed; split gate table (100 / 75.9 / FP clause); NC clean 97.1% at v0.5.15.1 with its scope sentence; version-continuity pair (75.9 beside 97.1, one version); generator-vs-mutator delta.
- 4.3.6: the W1 report's numbers, cited from W1.
- 4.4: external arm figures per W7.
- 4.5: W10's package.
- 4.6: the gate summary table rows (every hypothesis clause, gate, measured value, verdict, evidence rung).

Rule: any figure that cannot be re-derived from a committed artifact is not entered with a value; it is entered as ESCALATION with what was searched. Any figure that differs from what the Results guide or repair spec states is entered with both values and escalated.

Done-gate: every row has all six columns populated or is an explicit escalation; zero rows sourced from conversation or from status reports without artifact confirmation (the PHASE3_STATUS_REPORT lesson).

### W7 — D6 external arm, verify-or-execute (15 min to verify; ~3h if unrun)

INVESTIGATION first: Decision 10 ruled the 384/427 equality claim measured in both directions (~3h). Determine whether that measurement ran (search `studies/`, `dev/build/`, commit log since 2026-08-16). If run: enter its outputs in W6 and confirm both directions. If unrun: execute per Decision 10, both directions, results committed under `studies/`, then enter in W6. Also apply the two-word `datasetcard_info` → `modelcard_info` fixes at the two named sites if not already landed (`docs/model-credibility-pack-addendum-v0_5-taxonomy-validation.md:32`, `studies/taxonomy-validation/frame.py:4`); verify against the ten corrected artifacts before touching.

### W8 — Stale status tables (30 min)

Strike the P25-A row in `PHASE2_5_STATUS_REPORT.md` §4 with its completion date, matching the §1/§5 convention. Then sweep all status/report documents for remaining-work tables that predate 2026-08-16 closures (Phase 3 spec status, Stage 4 references, mutator status) and apply the same strikethrough-with-date convention. List every touched file in the session report.

### W9 — Version-label sweep (30 min)

Bare "v0.6" is ambiguous: core pack is at 0.6.0, the spec changelog line is past it, and the catalog is at v0.5.15.1. Sweep the Decision Record, both layer specs, the repair spec's descendants, CHANGELOG unreleased section, and any draft chapter text in the repo for bare "v0.6"/"v0.7" references. Disambiguate each to its intended line, preferring the phrase "the post-defense schema increment" in anything manuscript-bound and "catalog v0.6 (following v0.5.15.1)" where a version number is required. Do not renumber any existing released version. List every change for author review; anything inside a frozen or signed artifact is ESCALATION, not an edit.

### W10 — Tier-1 restatement support package (1h)

Digs, does not write, the support for R2's author paragraph:
1. The 12 REAL-GAP spot-check rows: case_id, target pattern, ensemble verdict, author verdict, one-line author rationale where the worksheet carries it.
2. The exact location and text of the author's OUT-OF-SCOPE policy statement ("real weakness but prose-level, not structural") in the adjudication instructions or worksheet notes, with path and ref.
3. Grounding figures scoped to the 496 REAL-GAP verdicts (zero-echo rate, median tokens).
4. The INV-20 triangulation references: schema audit figures (empty rooms, undeclared terms, 1-of-78 `requiredVerificationMethod`), row 16 identifiers, and the three-route convergence stated as pointers, not prose.
5. The original 6-of-6 claim's exact published wording and every location it appears (specs, status reports, draft text), so the restatement can be applied everywhere at once. Each location listed; no edits to frozen artifacts.

### W11 — Decision Record addendum text (30 min; author commits)

Draft the addendum recording R1a/R1b/R1c, R2, R3, and the 4.3.6 placement, in the existing addendum format with rationale one sentence each, dated 2026-08-19, explicitly noting R1b formalizes the basis the completed sitting already used and R1c precedes the W3 commit. Hand to author; do not commit.

## 3. Sequencing

```
W2 ──► W1 ──► W3 ──► (W4 runs at pre-fix ref; may run any time before W6 cites it)
W5 ──────────────┐
W7 ──────────────┼──► W6
W1 ──────────────┘
W8, W9, W10, W11: parallel-now, no dependencies
```

W3 lands after W1 so no report is written while the catalog changes underneath it. Everything else is parallel-now.

## 4. Effort roll-up

| Item | Hours |
|---|---|
| W1 Stage 4 report | 1–2 |
| W2 dedup sensitivity | 0.5 |
| W3 INV-21 fix | 1 |
| W4 contrast variant | 0.3 |
| W5 Wilson CIs | 1 |
| W6 numbers ledger | 3–4 |
| W7 D6 verify-or-execute | 0.25–3 |
| W8 stale tables | 0.5 |
| W9 version sweep | 0.5 |
| W10 Tier-1 support | 1 |
| W11 addendum text | 0.5 |
| **Total** | **10–14.5 solo; one paired weekend block at measured throughput** |

## 5. Escalation criteria (session-wide)

1. Any number that cannot be re-derived from a committed artifact.
2. Any figure that disagrees with the Results guide, the repair spec, or this spec's §1.
3. W2 sensitivity changes any majority verdict or the override count.
4. W3 changes behavior beyond W-EP-01 and the two compounds.
5. W7 finds the D6 measurement partially run or contradicting the 384/427 prose arithmetic.
6. Any edit that would touch a frozen, signed, or tagged artifact.
7. Anything requiring a decision this spec's §0 does not already cover.

Escalations come to the author named and specific; everything else proceeds.

## 6. Out of scope

Writing-queue positions 1–10 (author-only). The R2 reclassification paragraph and all manuscript prose. INV-22 (R3). The requirement and argument layers (post-defense schema increment). Re-running P25-A or any Stage 4 re-adjudication (R1b, R1c). The Nagaraja demo build (sequenced after this spec's outputs per the v2.1 doc).

## 7. Consolidated done-gate

All eleven items closed or escalated; the ledger's every row artifact-backed; the Stage 4 report committed; the fix landed with its disclosure; and the author can open writing position 8 with no number left to dig.

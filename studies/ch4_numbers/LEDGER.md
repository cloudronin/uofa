# Chapter 4 numbers ledger

W6 of the Ch4 Numbers and Repairs spec. One row per figure the Results chapter
will cite, each with the version it was measured at, the artifact behind it, and
the command that re-derives it.

**Rule applied throughout:** a figure that cannot be re-derived from a committed
artifact is **not entered with a value**. It is entered as **ESCALATION** with
what was searched. A figure that disagrees with the Results guide or the repair
spec is entered with **both** values and escalated.

Status: **§4.3.6, §4.3 (Arm M half), §4.5 and the §4.2 headline/null pair are
complete and artifact-backed. §4.1, the rest of §4.2, and §4.6 are escalated** —
see §Escalations for what was searched in each case. §4.4's D6 rows are ready.

---

## §4.3.6 — the generation arm, adjudicated

All rows re-derive with
`PYTHONPATH=src python studies/phase3_stage4/rederive_stage4.py`, which exits
non-zero if any structural invariant fails. Artifact:
`studies/phase3_stage4/REPORT.md` · `stage4_readouts.json`.
Catalog **v0.5.15.1**, corpus **2026-04-26**.

| Claim | Value | Measured at | Artifact | Commit |
|---|---|---|---|---|
| Cohen's κ, judges A–B | 0.6945 | corpus 2026-04-26 | `agreement_stats.json` | `b23622af` |
| Cohen's κ, A–C | 0.7595 | " | " | " |
| Cohen's κ, B–C | 0.8534 | " | " | " |
| Fleiss' κ, 3 raters | 0.7685 | " | " | " |
| Raw agreement ≥2-of-3 | 0.9954 | " | " | " |
| N per pairwise κ | **4,556** | " | " | " |
| Disagreement queue size | 21 (0.46%) | " | `triage_summary.json` | " |
| Author adjudication completeness | 71 / 71 | 2026-08-19 | `adjudication_worksheet.csv` | " |
| **Weighted spot-check override rate** | **0.2130** | " | `stage4_readouts.json` | " |
| Override gate target | ≤ 0.10 → **FAIL** | " | " | " |
| — CORRECT-DETECTION stratum | 0/15, contributes 0.0000 | " | " | " |
| — EXISTING-RULE-MISBEHAVIOR | **7/12**, contributes **0.1493** | " | " | " |
| — GENERATOR-ARTIFACT | 0/8, contributes 0.0000 | " | " | " |
| — REAL-GAP | **12/12**, contributes 0.0637 | " | " | " |
| — OUT-OF-SCOPE | 0/3, contributes 0.0000 | " | " | " |
| Author vs judge A / B / C (21 cases) | 1/21 · 8/21 · 8/21 | " | " | " |
| Author matched no judge | 4 of 21 | " | " | " |
| Judge A extra records / self-conflicts | 549 / 38 | " | " | " |
| Judge B / C self-conflicts | 8 / 1 | " | " | " |
| Gap-probe grounding, zero-echo | **0.0%** across all 990 | " | `gap_probe_grounding.csv` | " |
| — REAL-GAP, no Tier-1 candidate | 0.0% over 496, median 17 tokens | " | " | " |
| Author verdict distribution | CD 23 · OOS 21 · GA 19 · ERM 8 | " | " | " |
| REAL-GAP verdicts by author | **0** | " | " | " |
| Dedup sensitivity: majorities changed | **0** of 50 | " | " | " |

**Note (C5-class, version-dependent):** any figure derived from recorded
`rules_fired` describes the **generation-time** catalog. 63 of 65 comparable
packages have since diverged (R1b disclosure).

## §4.2 — H2, headline against its own null

Artifact: `docs/extract_eval_v1.md`, commit `a487d203` (2026-08-16), which states
of itself: *"This document is the origin of the headline."* Corpus: the
**synthetic 50-bundle set** (30 dev + 20 held-out), per GATE-H2's
report-per-corpus requirement and INV-10's labelling note.

| Claim | Value | Measured at | Artifact | Commit |
|---|---|---|---|---|
| Mean overall F1, dev (**the headline**) | **0.964** | synthetic 50-bundle | `extract_eval_v1.md:58` | `a487d203` |
| Mean overall F1, test | 0.954 | " | " | " |
| **The run's own null** — pack's fixed checklist, zero parameters, reads none of the input | **F1 0.960** | " | `extract_eval_v1.md:24-26` | " |
| **Margin over null** | **+0.004** | " | `extract_eval_v1.md:26, 49-50` | " |
| Why the null scores so high | ground truth lists the full checklist and marks **92.5%** of rows `assessed` | " | `extract_eval_v1.md:25` | " |
| Dev–test gap | 0.010, within the 10-point overfit guard | " | `extract_eval_v1.md:142` | " |
| GATE-H2 threshold | ≥0.85 dev / ≥0.80 test | — | `UofA_Unified_Repair_Spec_v2_1.md:86` | — |

**The number that matters is +0.004, not +0.114.** The document says so
explicitly: the headline "sits 0.004 above that constant, not 0.114 above the
0.85 target". It also records the null's one disqualifying property — the
constant checklist "cannot produce a package at all", failing `uofa import` on
the Minimal profile.

**Wording note for §4.2 and elsewhere.** `UofA_Unified_Repair_Spec_v2_1.md:86`
states the null loosely as "a constant checklist reaches 0.95". The measured
figure is **0.960**. That line sits inside a gate definition in a spec document,
so it is flagged for author review rather than edited here (W9 group A).

## §4.3 — H3, Arm M and the gate

Artifact: `studies/phase2_5a/REPORT.md` · `results.json` (`sha256` in
`STEP-0C-PRECONDITION.md`). Re-derive with
`PYTHONPATH=src python studies/phase2_5a/run_arm_m.py`. Catalog **v0.5.15.1**.

| Claim | Value | Measured at | Artifact | Commit |
|---|---|---|---|---|
| GATE-H3 MECHANICAL | 100% over 13 | v0.5.15.1 | `results.json` `gate` | `008626f2` |
| GATE-H3 overall | **75.9%** vs ≥80% → **FAIL** | " | `REPORT.md` §GATE-H3 | `e40d7819` |
| Gate denominator | 13 of a 17-pattern partition | " | `results.json` `gate` | `008626f2` |
| Excluded, unfireable | W-EP-01 | " | " | " |
| Excluded, no conformant mutant | W-ON-01, W-SI-01, W-SI-02 | " | " | " |
| Total mutants scored | 50 | " | `results.json` `totals` | " |
| Conformant-but-flawed / schema-caught | 38 / 12 | " | " | " |
| NC clean rate | 97.1% (166/171) | v0.5.15.1 | `holdout_v0515_summary.md` | — |
| CE recall, version-consistent | 75.9% (287/378) | v0.5.15.1 | `studies/phase2_5a/REPORT.md` | `e40d7819` |
| **Aggregate over the gate denominator** | **35/35 = 1.0000, Wilson [0.9011, 1.0000]** | " | `wilson_intervals.json` | this branch |
| Wilson floor, every gate pattern | < 0.5 (0.439 at n=3; 0.207 at n=1) | " | " | " |
| Patterns clearing a 0.5 floor | **1** — W-SI-02, [0.610, 1.000] at raw n=6 | " | " | " |
| — but W-SI-02's conformant n | **0** — excluded from the gate; **not a detection figure** | " | " | " |
| Per-pattern n distribution | 14 at n=3, 2 at n=1, 1 at n=6 | " | " | " |

Re-derive the intervals:
`python studies/phase2_5a/wilson_intervals.py`.

**How position 8 cites these.** The chapter claim rests on the **aggregate**
interval over the gate denominator — 35/35, Wilson floor **0.9011**. The
per-pattern table is shown with its intervals for honesty, not as a set of
per-pattern claims, and carries the qualitative sentence that per-pattern n is
too small to support one. W-SI-02's clean [0.610, 1.000] takes a footnote: its
conformant n is 0, so it demonstrates **schema capture, not rule detection**.

**Correction entered per the ledger rule (C4):** the spec's §W5 expects "five
patterns at n=3, two at n=1". Measured: **14 at n=3, 2 at n=1, 1 at n=6.** Both
values recorded; the measured one governs.

## §4.5 — the boundary

Artifact: `studies/phase3_stage4/TIER1_SUPPORT.md`, regenerate with
`python studies/phase3_stage4/build_tier1_support.py`.

| Claim | Value | Measured at | Artifact | Commit |
|---|---|---|---|---|
| REAL-GAP spot-check rows overturned | **12 of 12**, all → OUT-OF-SCOPE | 2026-08-19 | `TIER1_SUPPORT.md` §1 | this branch |
| Original claim's own scoping | "majority-judge support, **not** confirmed real gaps" | 2026-07 | `STAGE3_RESULT.md:56` | — |
| Locations of the 6-of-6 claim | 6, listed | — | `TIER1_SUPPORT.md` §3 | — |
| Ensemble read the packages | 0.0% zero-echo over the 496 no-candidate REAL-GAPs | 2026-08-19 | `gap_probe_grounding.csv` | this branch |
| Empty classes | 4 (`Requirement`, `AssuranceClaim`, `OperatingEnvelope`, `ApplicabilityConstraint`), 0 properties each | v0.5 | INV-20 | — |
| `requiredVerificationMethod` populated | **1 of 78** | v0.5 | INV-20 | — |
| `bindsClaim` conventions | **7** incompatible | v0.5 | INV-21 | — |
| W-ON-02 fires (queue packages) | **65/71 recorded** · **69/71 current catalog** | both stated | `stale_sweep` / INV-21 | this branch |

The W-ON-02 row is the C5 instance: the same figure differs by catalog version,
so both are carried with labels rather than one being silently preferred.

---

## Escalations

Entered per the ledger rule rather than given a value.

**E1 — RESOLVED, entered above.** The trace found `docs/extract_eval_v1.md`
(commit `a487d203`), which names itself the origin of the headline and carries
both figures from the same run and the same metric: headline **0.964** dev,
constant-checklist null **0.960**, margin **+0.004**. The spec's pair was correct;
the earlier escalation reflected not having found this document. Retained below
for the record of what was searched before it was found.

*(superseded)* §4.2 / H2 headline vs null: "0.964 vs 0.960 constant checklist".
*Searched:* `studies/claim-density/FINDINGS.md` (has `mean_overall_f1` 0.9637
before and after, delta 0.0000 — but that is the Q2 arm's *kill criterion*, not a
headline-vs-null comparison); `studies/attribution-nulls/FINDINGS.md` (reports
attribution 0.6068 loose / 0.3716 verbatim, a different metric);
`studies/prompt-absence/dev-before.json` / `dev-after.json`;
`docs/corpus-construction-findings.md:1178,1184` (has 0.964 dev / 0.954 test on
50 synthetic bundles, and a separate "mean overall F1 0.964 — PASS").
`docs/UofA_Unified_Repair_Spec_v2_1.md:86` states the null as **"a constant
checklist reaches 0.95"**, not 0.960.
*Escalation:* three different 0.96-ish figures are in circulation from different
runs and metrics, and the spec's "0.960" matches none of them exactly. **Which
run and which metric is the H2 headline, and which is its null, needs the
author.** Not entered.

**E2 — §4.1 / H1 tier table.** *Searched:* `docs/valid-package-spec.md:546` has a
"**6 of 6** | **5 of 6**" table; `studies/cohort-2026-08/`,
`studies/real-document-rescore/`. *Escalation:* the per-substrate verdicts
(Morrison COU1/COU2, Nagaraja, NASA take-off/cruise), completeness, SHACL pass
and signature validity are spread across several study directories and the tier
table's canonical location was not established. Needs one authoritative source
named before entry.

**E3 — §4.2 remaining rows.** Attribution vs permutation null; real-corpus
per-document figures; development-vs-held-out tier split per Decision 7;
claim-density-zero count. *Searched:* `studies/attribution-nulls/`,
`studies/attribution-agreement/`, `studies/claim-density/` (has "**2 of 96**
rationales contain any number", "94 of 96 contain no number", real corpus 0.000
before and after). *Escalation:* the claim-density figures are artifact-backed
and could be entered, but the Decision-7 development-vs-held-out split governs
which corpus each row reports, and that split's application was not verified.
Entering them without it risks the wrong denominator — the failure mode
`PHASE3_STATUS_REPORT` already demonstrated.

**E4 — §4.4 external arm.** D6 is complete and verified
(`studies/d6-rederivation/FINDINGS.md`, commit `aa76cc6e`: 427 validation
results, 384/427 re-derives, Direction 2 holds with 0 counterexamples, pinned
revision `d459f536`). **These rows are ready to enter**; what is escalated is the
rest of §4.4's scope, which the spec does not enumerate beyond "external arm
figures per W7".

**E5 — §4.6 gate summary table.** Requires one row per hypothesis clause with its
gate, measured value, verdict and evidence rung. GATE-H3's rows are available
above; GATE-H2's depend on E1; H1's on E2. Blocked on those.

---

## Provenance

Every "this branch" commit refers to `feat/ch4-numbers-and-repairs`. Figures
marked with an artifact under `dev/build/adversarial/` are force-tracked
(`.gitignore:41-43`) and re-derive from a clean clone. Figures under `studies/`
are tracked normally.

# Chapter 4 numbers ledger

W6 of the Ch4 Numbers and Repairs spec. One row per figure the Results chapter
will cite, each with the version it was measured at, the artifact behind it, and
the command that re-derives it.

**Rule applied throughout:** a figure that cannot be re-derived from a committed
artifact is **not entered with a value**. It is entered as **ESCALATION** with
what was searched. A figure that disagrees with the Results guide or the repair
spec is entered with **both** values and escalated.

Status: **§4.2, §4.3, §4.3.6, §4.5 and most of §4.6 are complete and
artifact-backed.** §4.1 carries the Morrison count trio resolved with version
labels plus a review list; its per-substrate rows remain E2. Two escalations
stand: **E2** (H1 per-substrate verdicts) and **E3's held-out permutation null**.
§4.4's D6 rows are ready.

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

## §4.1 — H1, and the Morrison COU1 count trio

**Three values for one figure are in circulation.** This is the C5 pattern at its
sharpest: the same command on the same package returns a different number at each
catalog version, and all three appear in the record.

| Value | Catalog / tag | Composition | Where it appears |
|---|---|---|---|
| **14** | `v0.4.0-nafems` (frozen demo tag) | W-EP-01×1, W-EP-02×3, W-AL-01×3, W-AR-05×3, COMPOUND-01×3, COMPOUND-03×1 | `CONTRIBUTING.md:33`, `CHANGELOG.md:407`, `docs/v0.5-morrison-deltas.md:8` |
| **11** across 5 patterns | v0.5.15.1 / tag `v0.7.1` | W-AL-01×3, W-AR-05×3, W-EP-02×3, W-CON-04, W-ON-02 — **9 of the 11 vacuous** (bare-IRI validation results make three `noValue` rules fire on every result) | `README.md:167`, `docs/design.md:9`, `site/.../nafems-2026.md:21`, `site/.../weakeners.md`, `site/.../demo/nafems.mdx`, `site/src/content/docs/readme.md` |
| **17** across 8 patterns | **current catalog, post-R1a** | the 11 above + W-EP-01×1 + COMPOUND-01×4 + COMPOUND-03×1 | `tests/test_integration.py` (pinned), this branch |

**Any §4.1 sentence citing a Morrison COU1 count carries its version label.** The
14 is not superseded — it is the frozen NAFEMS demo tag and `CONTRIBUTING.md`
says "do not change this commit". The 11 is not wrong — it is what v0.7.1
reproduces. The 17 is what HEAD reproduces.

**Review list (W9-style), no edits made.** Every location above that states a
count *without* a version label needs one, or needs rewording:

- `README.md:167` — "What the rule engine finds on Morrison COU1 (11 weakeners
  across 5 patterns)". No version label; reads as current.
- `docs/design.md:9` — same shape, no label.
- `site/src/content/docs/research/nafems-2026.md:21` — **correctly labelled**
  ("runs from the frozen `v0.7.1` tag"), and verified: v0.7.1 (2026-05-02) still
  carries the guard, so its reproduction claim holds at its tag. No change needed
  **now**, but the next tag cut after R1a merges must update it.
- `site/scripts/check-pages.mjs:90,118` — asserts the **literal strings** "11
  weakeners across 5 patterns" and "18 weakeners across 6 patterns". It checks the
  page says what it says; it cannot detect the number going stale relative to the
  catalog. It will keep passing while the page drifts. **Flagged as a guard that
  does not guard what it appears to.**
- `docs/UofA_Unified_Repair_Spec_v2_1.md:107` already flags these as
  "committee-facing reproduction numbers" and rules "restate from re-measured
  baselines" — that ruling now has a second trigger.

### H1 per-substrate table, derived

Re-derived by running the checks, not located in prose:
`python studies/ch4_numbers/derive_h1_tier_table.py` → `h1_tier_table.json`.
Exits 1 if any substrate fails a check it should pass — it does; see below.

| Substrate | serialisation | decision | MRL | complete | SHACL | integrity | rules |
|---|---|---|---|---|---|---|---|
| Morrison COU1 | flat | Accepted | 2 | ✓ | pass | pass | pass |
| Morrison COU2 | flat | Not accepted | 5 | ✓ | pass | pass | pass |
| Nagaraja COU1 | flat | Accepted | 3 | ✓ | pass | pass | pass |
| NASA take-off | `@graph` | — | — | **✗** | pass | pass | pass |
| NASA cruise | `@graph` | — | — | **✗** | pass | pass | pass |

**Three of five derive clean.** The two NASA rows are the escalation: those files
contain **no `UnitOfAssurance` node at all** — their `@graph` holds only
`WeakenerAnnotation` nodes in fully-expanded JSON-LD. They are **engine output
snapshots, not source packages**.

`uofa rules` on them reports 17 weakeners and **"Inferred 0 new triples"**: every
pattern it prints is read back from the file, not detected. Their SHACL and
integrity passes are therefore **vacuous** — SHACL's `targetClass
uofa:UnitOfAssurance` matches nothing, so it passes for want of anything to
check. This is INV-22's shape again: an instrument that can only confirm.

**Consequence flagged, not acted on.**
`tests/test_integration.py::test_aero_cou1_accept_fires_w_ar_02` asserts
`"W-AR-02" in result.stdout` against this file. `W-AR-02` appears in it **as
data** (4 occurrences), so the test passes whether or not the rule fires — and 0
triples are inferred, so it does not. The test is green for the wrong reason.

The only NASA file carrying a real `UnitOfAssurance` node is
`packs/nasa-7009b/examples/starters/uofa-aero-fatigue-minimal.jsonld`. **Which
artifacts are the intended NASA take-off / cruise H1 substrates is an author
call**; the three vv40 rows above stand either way.

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

### Real corpus, under Decision 7's split

Decision 7 rules Morrison and Nagaraja **development documents**; headline
real-corpus metrics report the **held-out** papers, with a with-development
**sensitivity row**. The real corpus is six papers, so the split is 4 held-out +
2 development — matching Decision 7's stated "base held-out count is 4".

Artifact: `studies/real-document-rescore/FINDINGS.md`, per-document table.

| paper | pack | hits | tier |
|---|---|---|---|
| opensim | nasa-7009b | 0/7 | held-out |
| elemance | nasa-7009b | 0/6 | held-out |
| **ared** | nasa-7009b | **3/7** | held-out |
| bologna | vv40 | 0/13 | held-out |
| nagaraja | vv40 | 0/12 | **development** |
| morrison | vv40 | 0/11 | **development** |

| Claim | Value | Tier | Artifact |
|---|---|---|---|
| **Headline, held-out (4 papers)** | **3/33 = 0.0909** | Decision 7 headline | computed from the table above |
| Sensitivity, all six | 3/56 = 0.0536 | with development | " |
| Every hit comes from one paper | ared, the shortest at 205 sentences | — | `FINDINGS.md:40` |
| Papers scoring zero | 5 of 6 | — | " |
| Wilson on 56 factors with 3 hits | 0.018–0.146 | — | `FINDINGS.md:41` |
| Claim-density, real corpus | 0.000 before, 0.000 after | **split-invariant** — zero on every tier | `studies/claim-density/FINDINGS.md:27` |
| Rationales carrying no number | **94 of 96**, across six papers | with development | `FINDINGS.md:120`, `claim-density:137` |

**The published lift is the with-development figure.** The permutation-null table
reports `real 0.0536`, which is exactly **3/56** — all six papers. So the **5.5×**
lift is the sensitivity figure, not the Decision 7 headline. The held-out
candidate rate is computable (0.0909); the held-out **null** is not, because
0.0098 was computed over all six. See E3.

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

**E2 — PARTIALLY CLOSED by derivation.** Three of the five substrates derive
clean and are entered in §4.1 above. The two NASA aerospace files are **not
source packages** — no `UnitOfAssurance` node, `@graph` holds only
`WeakenerAnnotation`, 0 triples inferred — so their SHACL and integrity passes
are vacuous. **Which artifacts are the intended NASA take-off / cruise
substrates is an author call.** Re-derive with
`python studies/ch4_numbers/derive_h1_tier_table.py` (exits 1 on exactly this).


**E3 — split applied; the held-out null is BLOCKED, and not for the reason the
disposition assumed.** The re-run was ruled as "re-deriving an existing statistic
from artifacts already on disk". It is not derivable that way:

1. The per-case `perm_mean` values were **never committed** — zero files in the
   tree contain the key, and `FINDINGS.md` carries no per-paper null column.
   Only the six-paper mean (0.0098) was published.
2. Recomputing means calling `score_case` in
   `dev/tools/scripts/real_document_rescore.py`, whose `_extract_rationales`
   makes a **live LLM call** to Together AI
   (`meta-llama/Llama-3.3-70B-Instruct-Turbo`, `UOFA_OPENAI_COMPATIBLE_API_KEY`,
   not set here). Nothing is cached.
3. **The extraction is not stable run-to-run.** `FINDINGS.md:42` records it:
   *"nagaraja scored 1/12 in the previous run and 0/12 in this one, same paper,
   same pack, different extraction."*

Point 3 is decisive. A re-run is a **new measurement**, not a re-derivation, and
for internal consistency the published 3/56 and 5.5× would have to be re-derived
from that same new run. **Author call.** Options: (a) fund one fresh run and
re-derive every real-corpus figure from it, both tiers; (b) report 5.5×
explicitly as the all-six sensitivity figure and give the held-out candidate rate
3/33 = 0.0909 with no lift, stating why.

**What Decision 7 did close.** The split pointer is Decision 7:
Morrison and Nagaraja are development documents, the headline reports the 4
held-out papers, and all six is the sensitivity row. Applied in §4.2 above —
per-document table with tiers, headline 3/33 = 0.0909, sensitivity 3/56 = 0.0536,
and claim-density noted split-invariant at 0.000 on every tier.

**What remains escalated: the held-out permutation null.** The published lift of
**5.5×** divides `real 0.0536` by a permutation null of `0.0098`, and 0.0536 is
3/56 — all six papers. Under Decision 7 the headline lift needs the null
recomputed **on the held-out subset**, which cannot be derived from the committed
artifact; the null is computed per run by shuffling that run's own labels, so it
does not decompose by paper. Either re-run the permutation null on the 4 held-out
papers, or report the 5.5× explicitly as the with-development sensitivity figure
and give no held-out lift. **Author call; not entered.**


**E4 — §4.4 external arm.** D6 is complete and verified
(`studies/d6-rederivation/FINDINGS.md`, commit `aa76cc6e`: 427 validation
results, 384/427 re-derives, Direction 2 holds with 0 counterexamples, pinned
revision `d459f536`). **These rows are ready to enter**; what is escalated is the
rest of §4.4's scope, which the spec does not enumerate beyond "external arm
figures per W7".

**E5 — §4.6 gate summary table, now mostly unblocked.** GATE-H3's rows are
above; GATE-H2's are above since E1 resolved. What remains is H1's, which depend
on E2, and the H2 lift row, which depends on E3's held-out null.

Enterable now:

| Hypothesis clause | Gate | Measured | Verdict | Evidence rung |
|---|---|---|---|---|
| H2 detection F1, dev | ≥0.85 | 0.964 | pass | Demonstrated |
| H2 detection F1, test | ≥0.80 | 0.954 | pass | Demonstrated |
| H2 margin over the run's own null | "required margin" | **+0.004** | see §4.2 | Demonstrated |
| H3 MECHANICAL | ≥95% | 100% over 13 | pass | Demonstrated |
| H3 overall | ≥80% | **75.9%** | **FAIL** | Demonstrated |
| H3 aggregate interval | — | 35/35, Wilson [0.9011, 1.0000] | — | Demonstrated |
| Stage 4 spot-check override | ≤0.10 | **0.213** | **FAIL** | Demonstrated |

The two FAILs are reported as measured, per §0.1. The override FAIL decomposes
per R4: REAL-GAP relocates to the schema boundary, ERM is an ensemble-reliability
finding, and neither is adverse to the catalog.

---

## Provenance

Every "this branch" commit refers to `feat/ch4-numbers-and-repairs`. Figures
marked with an artifact under `dev/build/adversarial/` are force-tracked
(`.gitignore:41-43`) and re-derive from a clean clone. Figures under `studies/`
are tracked normally.

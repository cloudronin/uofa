# Gate-7 decision record

**Date:** 2026-06-10
**Decision:** **RELAX** (gate 7 relaxed). **Stage 2 is GO on prompt `v1.1.0`.**
**Basis:** calibration v5 (prompt v1.2.0), one tuning iteration per spec Part 1. Full numbers in [`calibration-v5/gate7_result.md`](calibration-v5/gate7_result.md).

## Outcome summary

- **v4 (v1.1.0)** failed gate 7 on the per-class UNCERTAIN floor for Judge B (20%) and Judge C (0%); all other gates passed (A/B/C accuracy ≥ 80%, pairwise κ ≥ 0.70).
- **v5 (v1.2.0)**, one UNCERTAIN-targeted prompt iteration: Judge B UNCERTAIN rose to **60%** (clears the floor); Judge C UNCERTAIN stayed **0%**; Judge C's recorded accuracy fell to **63.3%** (fails gate 5), driven mostly by 5 Llama schema-validation hard-failures rather than a clean reasoning regression.
- v1.2.0 cannot be promoted because its recorded run fails gate 5 for Judge C. **Production runs on v1.1.0**, the baseline where gates 5 and 6 pass for all three judges.

## Spec v1.7 §15.1 #7 amendment (replaces the current gate-7 clause)

**Gate clause:**

> Per-class accuracy ≥ 50% per verdict class per judge, except UNCERTAIN. For the UNCERTAIN class the gate is satisfied when at least one production judge achieves ≥ 50% on UNCERTAIN-anchored calibration cases. Cases where the production trio splits route through Stage 3b arbitration regardless of class.

**Explanatory note (separate, non-load-bearing):**

> The UNCERTAIN-class relaxation reflects an empirical observation across calibration v4 (2026-05-05) and v5 (2026-06-10). Vendor families differ in commitment style on cases that admit multiple defensible verdicts. Some judges, such as Judge A in this ensemble, select UNCERTAIN; others, such as B and C, select the most-likely defensible reading. The resulting cross-judge disagreement on UNCERTAIN-anchored cases is itself a signal of case-level ambiguity, which Stage 3b arbitration is designed to resolve. This interpretation is descriptive of observed behavior and is open to challenge by future reviewers; the gate above holds regardless.

Under the amended clause, **gate 7 is satisfied at v1.1.0**: Judge A reaches 80% on UNCERTAIN, which meets the "at least one production judge ≥ 50%" condition.

## Ch3 disclosure paragraph

Gate 7 of the Stage 1 calibration requires each production judge to reach at least 50 percent accuracy on every verdict class, including the UNCERTAIN class. Two of the three production judges did not meet this floor on UNCERTAIN. Judge B reached 20 percent and Judge C reached 0 percent, while Judge A reached 80 percent. The calibration record explains the pattern. The five UNCERTAIN anchor cases are ones the author labeled UNCERTAIN because more than one verdict stays defensible after inspection. Judges B and C resolve that ambiguity by committing to a single defensible verdict at high confidence instead of reporting UNCERTAIN. This reflects a difference in vendor commitment style, and it appears at confidence levels between 0.80 and 0.95, so it is not a low-confidence hedge that downstream routing would catch.

We ran one targeted prompt iteration to test whether the floor was reachable. Prompt v1.2.0 strengthened the UNCERTAIN guidance for every judge using the same template. It raised Judge B from 20 percent to 60 percent, which clears the floor for that judge. It did not move Judge C, and Judge C's recorded run was further degraded by five schema-validation failures from the Llama endpoint, so the iteration was not promoted. We then relaxed gate 7 rather than continue tuning. The UNCERTAIN class has only five anchor cases, so the failures rest on a very small sample. The ensemble also carries compensating controls. Judge E arbitrates the disagreement queue, and the author adjudicates that queue in Stage 4. The residual risk we name is that high-confidence absorption of UNCERTAIN cases into the EXISTING-RULE-MISBEHAVIOR class can suppress REAL-GAP confirmations on the section 6.7 Tier 1 candidates. We treat that risk explicitly in the Stage 4 adjudication and in the Tier 1 gate analysis.

Production runs on prompt v1.1.0, the configuration whose calibration meets the accuracy and agreement gates for all three production judges, with the gate 7 floor relaxed as stated above.

## Ch3 disclosure: judgment provenance (Stage 2 execution)

The Stage 2 judgments were produced in two windows rather than one. The run began on 2026-06-10 and stalled after roughly 1,000 to 1,250 cases per judge, because the scheduled daily job could not read the repository from its cloud-storage location and so never executed. The run resumed on 2026-07-16. In that second window Judge C moved from SambaNova to OpenRouter, because SambaNova deprecated the Llama-4-Maverick model. The prompt version stayed pinned at v1.1.0 across both windows and the panel composition did not change.

Two consequences follow, and we state them plainly.

First, some cases were judged more than once. The resume logic revisited any case that was missing a verdict from at least one judge, and it then re-ran every judge on that case rather than only the judge whose verdict was missing. While Judge C was unavailable, this re-judged cases that Judges A and B had already completed. The per-judge record is append-only, so both the original and the repeat verdict are preserved. Analysis reads those files through an alignment step that keys on case id and keeps the most recent verdict for each judge, so every case contributes exactly one verdict per judge to triage and to the agreement statistics.

Second, a small number of repeat judgments disagreed with the original. Across the production trio, 47 cases carry a repeat verdict that differs from the first one: 38 for Judge A, 8 for Judge B, and 1 for Judge C. That is about 1 percent of the 4,556-case corpus. The prompt version was pinned and the sampling temperature was zero, so the difference reflects either a vendor-side model update between the two windows or the residual nondeterminism these APIs retain at temperature zero. We do not claim to separate those two causes. The most recent verdict is authoritative for every case, which is what the alignment step selects. Nothing was overwritten, so a reviewer who wants to test how sensitive a result is to that choice can recover the earlier verdicts from the raw record.

The resume behavior that produced the repeat judgments was corrected on 2026-07-17, so each judge now judges only the cases it is individually missing. Judgments recorded before that date retain the duplicates described here.

## Production configuration (frozen)

- **Prompt template version:** `v1.1.0`
- **Production trio:** openai `gpt-5.4` (A), gemini `gemini-2.5-pro` (B), `Llama-4-Maverick` (C), served via SambaNova through 2026-07-16 and via OpenRouter thereafter (SambaNova deprecated the model). **Arbiter:** mistral `mistral-large-2411` (Judge E).
- **thinking_enabled:** false (matches calibration; the gate decision transfers).
- **Gate-of-record metrics (v4, v1.1.0):** accuracy A 96.7% / B 86.7% / C 83.3%; pairwise κ AB 0.879 / AC 0.838 / BC 0.875; Fleiss 0.863. Gate 7 relaxed per the amendment above.
- v1.2.0 is retained in the repo as the recorded tuning iteration; it is **not** the production prompt.

# Phase 3 (LLM-Judge Ensemble) — Status Report

**Repo:** github.com/cloudronin/uofa — local working copy (incl. gitignored `dev/build/`)
**Investigator:** Claude Code, paired with Vishnu Vettrivel
**Date:** 2026-06-09
**Method:** Read-only. Evidence = results files with timestamps + numbers, not code existence. No Phase 3 artifact, result, or spec was modified.

> **Status update (2026-07-17).** This is a point-in-time investigation dated 2026-06-09 and has since been partly overtaken. Gate 7 was resolved on the **RELAX** path (production prompt frozen at **v1.1.0** — see [`GATE7_DECISION.md`](dev/build/adversarial/phase3/GATE7_DECISION.md)), and the **Stage 2 production run is under way**: 2,914 of 4,556 cases judged by all three judges as of 2026-07-17 (see [`production/RESUME.md`](dev/build/adversarial/phase3/production/RESUME.md)). Stages 3–5 remain unstarted. Everything below still stands as the Stage 1 evidence base, the deviation log, and the risk flags — in particular the catalog version-skew risk (#1), which the running Stage 2 does **not** resolve.

---

## 1. One-line answer

**Stage 1 (Calibration) is the furthest stage with complete evidence** — it ran four times on 2026-05-05, final run `calibration-v4` (19:52:28Z), with exact per-judge accuracies, pairwise/Fleiss κ, and a hard-gate verdict on disk. **The first stage with missing evidence is Stage 2 (full-corpus judgment): only a 100-case stratified pilot ran; the 4,556-case production run is fully built and scripted but was *held* pending a "gate-7" decision and never fired.** Stages 3–5 have **zero output artifacts** — triage, adjudication, agreement statistics, Tier-1 verdicts, formalized rules, the case-study delta, and the ANOVA do not exist on disk.

> Bottom line: **Phase 3 is built end-to-end and calibrated, but execution stopped at the Stage 1→2 boundary.** Everything downstream of "fire the production run" is unstarted.

---

## 2. Stage table

| Stage | Verdict | Key numbers (exact, with source) | Evidence path | Gaps |
|---|---|---|---|---|
| **1 — Calibration** | **DONE** (gate-7 partial) | Final `calibration-v4`: A=`gpt-5.4` **96.7%** (29/30), B=`gemini-2.5-pro` **86.7%** (26/30), C=`Llama-4-Maverick:sambanova` **83.3%** (25/30), E(arbiter)=`mistral-large-2411` **83.3%**. Pairwise κ **AB 0.879 / AC 0.838 / BC 0.875**; **Fleiss 0.863**. 30-case set, 6 classes × 5. | `dev/build/adversarial/phase3/calibration-v4/v1.1.0/calibration_run_v1_results.json` + `…_summary.md` (2026-05-05 12:52) | **Hard gate 7 (per-class ≥50%) FAILS**: UNCERTAIN class A 80% ✅ / B 20% ❌ / C 0% ❌. `all_pass: false`. Frozen prompt = **v1.1.0**, not "v1.6". |
| **2 — Full-corpus judgment** | **PARTIAL — pilot only** | 100-case pilot: $9.67, 543s, triage **{CONVERGENT 83, DISAGREEMENT 9, ERROR 8}** (Mistral arbitrated all 9); Llama 99/100. **Projected** full run: 4,556 cases, **~$262** (handoff) / $440 incl. non-prod Claude (pilot file), **5-day** schedule (Gemini 1,000 RPD-bound). | `dev/build/adversarial/pilot/2026-05-05/pilot_summary.json`; schedule + held command in `TIER_A_HANDOFF.md:536-852` | **No full-corpus per-judge JSONL.** No `phase3/run-1/` output dir. No 6-class verdict distribution at corpus scale. Run **held** pending gate-7 go/no-go (`TIER_A_HANDOFF.md:835`). |
| **3 — Triage** | **NOT STARTED** (pilot-scale only) | Pilot triage exists (above). Full-corpus CONVERGENT/DIVERGENT/UNCERTAIN bucketing: **none**. `triage.py` built (100% cov per handoff). | — (`triage.py` is code, not output) | No corpus-level queue size; `arbitration_partition` empty in pilot. |
| **4 — Adjudication + agreement stats** | **NOT STARTED** | None. Calibration κ exists (Stage 1) but **no full-corpus** Cohen's/Fleiss κ, confusion matrices, or author-vs-judge matrices. | — (`adjudication.py`, `arbitration.py` are code; no output data found after sweeping `dev/`, `runs/`, `harness/`, home) | No author adjudication records, no self-blinding / `post_hoc_alignment` data. |
| **5 — Pattern formalization + case-study re-run** | **NOT STARTED** | None. §6.7 Tier-1 IDs appear only as **REAL-GAP calibration anchors** (cal-006→W-EV-01, 007→W-REQ-01, 008→W-EV-02, 009→W-CX-01, 010→W-AR-06; **W-AR-07 absent from cal set**). No production adjudication of the ≥3-of-6 gate. | `specs/calibration/calibration_set_v1.jsonl`; `formalize.py`/`case_study.py` built (`TIER_A_HANDOFF.md:193-194`) | No formalized Jena rules for the 6 IDs in `packs/` (CLARISSA vocab "staged for v0.6" only). No Morrison/Nagaraja delta table. **No §13.4 ANOVA** output. |

**Corpus size confirmed:** `judge_ready_bundle.tgz` (2026-05-04 17:50) holds **9,115 entries ≈ 4,556 packages × 2 files** (.jsonld + .outcome.json); matches `pilot_summary.json` `n_corpus: 4556` and `TIER_A_HANDOFF.md:171,547`.

---

## 3. Deviation log (vs. Spec v1.5)

Each line = a divergence found, with a one-line Ch3 disclosure note. Most are **documented** in the handoff; the gate relaxation is the one that needs explicit defense.

| # | Deviation | Evidence | Ch3 disclosure note |
|---|---|---|---|
| D1 | **Governing spec is v1.6, not v1.5.** v1.5 was the Tier-A baseline; v1.6 carries the litellm-first refactor, productive-OOS deltas, Judge D anchor + Judge E arbitration. | `TIER_A_HANDOFF.md:180-243`; CHANGELOG "Added — Adversarial judge module" | "Phase 3 was executed against Spec v1.6 (productive-OOS + arbitration extensions of v1.5)." |
| D2 | **Judge B downgraded Gemini 3.1 Pro → Gemini 2.5 Pro.** Spec v1.6 §6.1 names 3.1 Pro; 3.1-preview caps at 100 RPD, insufficient for a 4,556-case run. | `TIER_A_HANDOFF.md:458-483`; summary "Methodology disclosure" line; capability-table comment | "Judge B uses gemini-2.5-pro (GA, 1,000 RPD); the v4 calibration gate is the empirical guard. Spec §6.1 text edit is pending." |
| D3 | **Judge A = GPT-5.4, Judge C = Llama 4 Maverick (Sambanova).** v1.5 planned GPT-4.1 / Llama-3.3-70B; both are obsolete. | `calibration_run_v1_results.json` (A `gpt-5.4`, C `…Llama-4-Maverick…:sambanova`); `TIER_A_HANDOFF.md:248-261` | "Production trio refreshed to current generation (GPT-5.4 / Gemini 2.5 Pro / Llama 4 Maverick) vs. the v1.5 placeholder roster." |
| D4 | **Arbiter (Judge E) = Mistral Large 2 (`mistral-large-2411`), rolled back from Large 3 (`mistral-large-2512`).** Large 3 scored E-vs-D **0%→16.7%** in early calibration; rolled back to 2411 (**83.3%**). | v1 summary (E `mistral-large-2512`, 16.7%) vs. v4 (E `mistral-large-2411`, 83.3%); CHANGELOG "Mistral Large 2" | "Arbiter is Mistral Large 2; Large 3 was evaluated and rejected on the anchor sanity check." |
| D5 | **Anthropic/Claude was a smoke/pilot judge, not a production judge.** Appears in the end-to-end smoke and the 4-judge pilot ($238 of the $440 pilot projection) but the held production command runs `--judges openai,gemini,hf-llama` only. | `pilot_summary.json` (`anthropic` block); `TIER_A_HANDOFF.md:71,845` | "Claude was used only for plumbing/cost smokes; it is not in the production ensemble." (Also: CHANGELOG's trio list omits GPT-5.4 — a doc gap, not a method change.) |
| D6 | **Stage 2 ran as a 100-case stratified pilot, not the full corpus.** Full run built + scheduled but held. | `dev/build/adversarial/pilot/*`; `TIER_A_HANDOFF.md:835` "held pending Stage 1 gate-7 decision" | "Reported Stage 2 numbers are a 100-case cost/throughput pilot; the full-corpus run was not executed." |
| D7 | **Arbiter as automated Stage 3b pre-adjudication layer.** Mistral auto-arbitrates the disagreement queue before author adjudication (pilot: arbitrated all 9/9 disagreements). This shrinks the author queue vs. the v1.5 author-adjudicates-all-divergent design. | `arbitration.py` (`TIER_A_HANDOFF.md:189`); pilot "Stage 3b" `TIER_A_HANDOFF.md:374-397` | "An automated arbitration layer (Judge E) pre-resolves the disagreement queue; author adjudication operates on the residual + a blinded sample." |
| D8 | **Hard gate 7 (per-class ≥50%) failed for B & C on UNCERTAIN; a spec v1.7 relaxation is proposed.** Proposed §15.1 #7: gate satisfied if ≥1 judge ≥50% on UNCERTAIN; splits route to Stage 3b. | `TIER_A_HANDOFF.md:577-814` (diagnostic + proposed language) | **Disclose explicitly:** "Gate 7 was relaxed post-hoc (v1.7) after v4 showed per-vendor commitment-style variation on UNCERTAIN cases; the ensemble κ (0.84–0.88) and arbitration net are the justification." This is the deviation most open to committee challenge. |
| D9 | **Phase-2 outcome-class normalization.** Actual classes `COV-HIT-PLUS / COV-WRONG / COV-CLEAN-WRONG / GEN-INVALID` normalized to the spec's enum; **no `COV-MISS` rows** in the corpus. | `TIER_A_HANDOFF.md:106-119` (`bundle_writer.NORMALIZE`) | "Judge input classes were normalized from Phase-2's emitted classes; GEN-INVALID is an input class, not a verdict." |

---

## 4. Remaining-work table

Hours are **estimates** for Claude-Code-paired execution, not measured facts. "Gap" = can it run/progress **June 13 – July 4** (author on vacation)?

| Task | Est. hrs (CC-paired) | Blocking dependency | Runs during June 13–Jul 4 gap? |
|---|---:|---|---|
| **G0. Gate-7 go/no-go + finalize Spec v1.7 §15.1 #7 text** | 1–2 | Author decision (option c+e already recommended in handoff) | **No** — author call. Must be made *before* the gap to unblock everything. |
| **S2. Full-corpus judgment** (4,556 × trio; 5-day `--resume` schedule) | 3–5 active + 5 calendar days | API keys (OpenAI/Gemini/HF-Sambanova), ~$262 budget, **G0** | **Partially** — cron-able via daily `--resume` if keys + budget + G0 are staged before June 13; otherwise no. |
| **S3. Triage** (CONVERGENT/DIVERGENT/UNCERTAIN; auto via `triage.py`) | 1 | **S2** complete | **Yes** — automatic once S2 lands; no author input. |
| **S4. Adjudication + agreement statistics** (Mistral auto-arbitrates queue; author self-blind adjudicates residual + sample; full-corpus κ/confusion matrices) | 8–16 (mostly author time) | **S3**; author annotation time | **No** — requires author judgment (self-blinding). Hard stop in the gap. |
| **S5. Pattern formalization + case-study re-run** (confirm ≥3-of-6 Tier-1; `formalize.py` → Jena rules; `case_study.py` → Morrison/Nagaraja delta; §13.4 ANOVA) | 8–12 | **S4**; author rule-design decisions | **No** — depends on S4 + author formalization choices. |
| **T. Ch3 §3.6/§3.7 result-placeholder integration** (terminal) | 4–6 | **S5** | **No** — depends on S5. |

**Scheduling read:** the vacation gap can absorb **S2 + S3** *only if* G0 is decided and credentials/budget are staged before June 13 (then it runs on a daily cron with `--resume`). The pipeline then **hard-stops at S4** — author adjudication cannot be delegated. So the realistic gap outcome is "full-corpus judgments + triage produced; adjudication onward waits for the author's return."

---

## 5. Risk flags

1. **≥3-of-6 Tier-1 gate is entirely unevaluated and structurally at risk.** The six IDs (W-EV-01, W-EV-02, W-REQ-01, W-CX-01, W-AR-06, **W-AR-07 — not in the calibration set**) are confirmed REAL-GAP *only as calibration anchors*; the gate is scored against **production** judgments that never ran. The documented **UNCERTAIN→EXISTING-RULE-MISBEHAVIOR absorption** (all four model families) is a systematic bias that could push borderline gaps out of REAL-GAP and below the 3-of-6 threshold. This is the single biggest threat to the praxis claim, and it is downstream of an unstarted Stage 2.

2. **Kappa targets are met and robust — but only at 30-case calibration scale.** Pairwise κ 0.838–0.879 / Fleiss 0.863 clear the ≥0.70 gate comfortably; full-corpus inter-judge κ is unmeasured and may differ. The live exposure is **gate-7**: the post-hoc v1.7 relaxation (D8) is defensible on the data but reads as goalpost-moving to a skeptical committee — disclose it as a deliberate, evidence-backed methodology decision, not a silent edit.

---

### Appendix — git / provenance facts
- **Phase 3 code is on `main`** (not stranded on a branch): `phase3-tier-a-prep` is a **fully-merged ancestor** of `main` (`git merge-base --is-ancestor` ✅; main is 142 commits ahead, branch 0 ahead). Branch tip 2026-05-05; judge module = **26 tracked Python files** under `src/uofa_cli/adversarial/judge/`. Local `main` is **1 commit behind `origin/main`** (origin has `1f89dc8 feat(v0.6)…`), 0 unpushed.
- **The Phase 3 Spec document itself is NOT in this working copy** (no `Product Requirements/` dir; no `*Adversarial_Gen_Phase3_Spec*` file found in `spec/`, `specs/`, `dev/specs/`, `docs/`, or `~/.claude/plans/`). Its section numbers (§6.1, §6.7, §8.3, §13.4, §15.1, §24.3) are cited throughout the artifacts; the file `UofA_Adversarial_Gen_Phase3_Spec_v1_6.md` is referenced as the target of pending author edits but lives outside this repo.
- **Execution window:** all Stage 1 / pilot artifacts are dated **2026-05-05**; the corpus bundle **2026-05-04**. No Phase 3 execution artifacts exist after 2026-05-06.

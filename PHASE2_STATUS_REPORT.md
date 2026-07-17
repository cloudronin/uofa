# Phase 2 (Adversarial Corpus Generation) — Status Report

**Repo:** github.com/cloudronin/uofa — local working copy (incl. gitignored `dev/build/`)
**Investigator:** Claude Code, paired with Vishnu Vettrivel
**Date:** 2026-06-09
**Method:** Read-only. Evidence = run artifacts with timestamps + numbers, not code existence. No artifact, result, or spec modified.
**Companion reports:** [PHASE2_5_STATUS_REPORT.md](PHASE2_5_STATUS_REPORT.md), [PHASE3_STATUS_REPORT.md](PHASE3_STATUS_REPORT.md).

---

## 1. One-line answer

**The Phase 2 primary full-battery (M5) is complete with full evidence** — it ran **2026-04-26**, produced a **4,605-row coverage corpus** (4,556 judge-ready packages), and the analysis (`outcomes/summary/matrix.csv` + `m5_findings.md`) is on disk with exact numbers. **The first missing stage is M6 (secondary batteries) — cross_pack, paraphrasing, and quality_benchmark never ran — and M7 (final exports + the `v0.5.5-phase2-complete` tag) is also unstarted.** The runbook scheduled M5–M7 for May 16–24; in fact only the April-26 primary battery exists, and there are **no May Phase 2 runs at all**.

> Bottom line: **Phase 2's core deliverable — the coverage corpus and its headline findings — exists and is solid. The secondary batteries, the exports, and the formal acceptance-gate closure do not.** And the corpus of record was generated against the *pre-refinement* catalog (see Risk flag #1).

---

## 2. Stage table

| Stage | Verdict | Key numbers (exact, with source) | Evidence path | Gaps |
|---|---|---|---|---|
| **M5 — Primary full-battery + analyze** | **DONE** | 4,605 outcome rows: **2,751 COV-HIT-PLUS / 1,294 COV-WRONG / 384 GEN-INVALID / 176 COV-CLEAN-WRONG**. Batteries: confirm_existing **4,005**, gap_probe **330**, negative_controls **180**, interaction **90**. Cost **$386.49**, model claude-sonnet-4-6, `halted:false`, strict-circularity. | `dev/build/adversarial/phase2/2026-04-26/` (`batch_manifest.json`, `coverage-seq/outcomes.csv`, `docs/m5_findings.md`) | Manifest `totalPackages:4221` is a stale as-generated count; analyzed corpus is 4,605 rows / 4,556 judge-ready (49 W-AR-05 legacy rows dropped). |
| **M5 results — coverage metrics** | **DONE** | Catalog **recall 73.4%** (CE, evaluable rows). Catalog **precision 0.0% / FPR 100%** (176/180 clean NCs fired ≥1 rule). **0 COV-HIT, 0 COV-MISS, 100% HIT-PLUS** (inter-rule correlation). GEN-INVALID **8.3%** overall (CE 9.5%). | `docs/m5_findings.md:151-193` | Precision=0% is a real, documented finding — it is the problem Phase 2.5 was created to fix. |
| **M6.1 — Cross-pack battery** | **NOT STARTED** | none | — (no `2026-05-18-crosspack/` dir) | Closes gate #17 (per runbook). |
| **M6.2 — Paraphrasing battery** | **NOT STARTED** | none | — (no `*paraphrasing*` dir) | Blocked by F2 (Anthropic safety-filter refusal on `p2` substitutions, `m5_findings.md:68-75`). Soft gate #29. |
| **M6.3 — Quality benchmark (multi-model)** | **NOT STARTED** | none | — (no `*quality*` dir) | 96-package, 3-model design. Closes gate #18; soft gates #30/#31. |
| **M7 — Exports + tag** | **NOT STARTED** | none | — (no `figure_3_x.pdf`, `view3_precision_recall.md`, `phase2_review_packet.md`; tag `v0.5.5-phase2-complete` absent) | `v0.5.5` plain tag exists; the `-phase2-complete` tag does not. Closes gates #20/#21. |
| **Acceptance gates #11–#21, #29–#31** | **NOT RECORDED** | no closure record | — | Phase 2 **Spec v1.8 is not in this repo**; gate definitions/closure are external. |

**Corpus confirmed:** `coverage-seq/outcomes.csv` = 4,605 rows; `judge_ready_bundle.tgz` (2026-05-04) = 9,115 entries ≈ **4,556 packages** — this is the exact corpus Phase 3 consumed.

---

## 3. Deviation log (vs. runbook / Phase 2 Spec v1.8)

| # | Deviation | Evidence | Ch3 disclosure note |
|---|---|---|---|
| D1 | **Scheduled May 16–24; actually ran April 26 (M5 only).** The runbook header and milestone dates (M5 May 16–17, M6 May 18–22, M7 May 23–24) do not match reality — `m5_findings.md` labels the **April 26** run "M5," and no May Phase 2 run exists. | `docs/phase2_runbook.md:1`; `docs/m5_findings.md:12`; `ls dev/build/adversarial/phase2/` | "The Phase 2 primary battery executed 2026-04-26; the runbook's May dates were not the execution window." |
| D2 | **Only the 4 primary batteries ran; the 3 secondary batteries did not.** Grand-total target ~4,656 (4,440 primary + 216 secondary); delivered = 4,605 primary-only rows. | runbook Appendix fan-out math; battery counts above | "Phase 2 coverage evidence covers the primary battery only; cross-pack, paraphrase-robustness, and multi-model quality batteries are not run." |
| D3 | **Manifest `model: null`.** Provenance of the generation model is by runbook convention (claude-sonnet-4-6), not recorded in the manifest. | `batch_manifest.json`; runbook §1 | "Generation model (sonnet-4-6) is documented in the runbook; the batch manifest does not stamp it." |
| D4 | **F1 design tension → "not_measurable" recall for W-ON-01 / W-SI-01.** These weakeners semantically require omitting SHACL-required fields (`hasContextOfUse`, `signature`), so no conformant package generates; reported as `not_measurable`, not 0%. Decision: Option A (accept + document). | `docs/m5_findings.md:14-58` | "Two weakener patterns are structurally untestable under current SHACL profiles; reported honestly as not-measurable." |
| D5 | **GEN-INVALID 8.3% overall exceeds the runbook's 5% triage threshold** — but the excess is concentrated on the F1 cells (CE 9.5%; residual well under 5%). | `docs/m5_findings.md:184-193` | "GEN-INVALID is above the 5% soft threshold, attributable to the documented F1 design tension, not generator quality." |
| D6 | **Phase 2 Spec v1.8 not in repo.** Like the Phase 3 spec, the governing Phase 2 spec (gate definitions §13.1) lives outside this working copy. | search of `spec/`,`specs/`,`dev/specs/`,`docs/` | "Acceptance-gate definitions are external; closure was not recorded in-repo." |

---

## 4. Remaining-work table

Hours are **estimates** for Claude-Code-paired execution. "Gap" = can it run/progress **June 13 – July 4** (author away)?

| Task | Est. hrs | Blocking dependency | Runs during June 13–Jul 4 gap? |
|---|---:|---|---|
| **P2-A. Decide whether to re-baseline Phase 2 on the v0.5.15.1 catalog** (see Risk #1) | 1–2 | Author decision | **No** — author call; must precede any re-run. |
| **P2-B. Re-run M5 primary battery on the refined catalog** (4,605 pkgs, ~$386, ~14h gen + ~5h analyze) | 4–6 active + ~1 day wall | API key + ~$386 budget + **P2-A** | **Partially** — `--resume`-able and largely unattended if budget/keys staged before June 13; otherwise no. |
| **P2-C. M6.1 cross-pack** (~$3) + **M6.3 quality** (~$12, 3 models) | 2–3 | API key + budget | **Partially** — automatable if staged. |
| **P2-D. M6.2 paraphrasing** (~$10) | 2–3 | **F2 fix** (soften/drop `p2` substitutions) | **No** — needs the F2 prompt fix first (author). |
| **P2-E. M7 exports** (Figure 3.x PDF, View 3 md, review packet) + tag | 2–4 | M5 (+ M6) final; `pip install -e '.[export]'` | **Partially** — scripted; runs once upstream lands. |
| **P2-F. F1 design-tension resolution** (W-ON-01/W-SI-01: accept / runner-bypass / SHACL loosen) | 3–6 | Author design decision | **No** — design judgment. |
| **P2-G. Acceptance-gate formalization vs. Spec v1.8** | 1–2 | External Spec v1.8 | **No** — needs the external spec + author. |

**Scheduling read:** the only gap-eligible work is unattended re-runs (P2-B/C) *if* budget + keys + the re-baseline decision are staged before June 13. Everything else (F1, F2, gate closure, the re-baseline decision itself) needs the author.

---

## 5. Risk flags

1. **Catalog version skew between the corpus of record and the refined catalog — the central cross-phase risk.** The 2026-04-26 corpus (consumed by Phase 3) was generated/analyzed against the **v0.5.0 / M5-baseline (v0.5.7)** catalog, whose **NC precision was 0% (FPR 100%)**. Phase 2.5 then refined the catalog to **v0.5.15.1 (97.1% NC clean)** — a substantial change to which rules fire. **No full-battery re-run on the refined catalog exists.** So Phase 3's §6.7 REAL-GAP adjudications, and any recall/precision figure quoted from M5, describe a catalog the project has since changed. Ch3 must either re-baseline Phase 2 on v0.5.15.1 and re-judge, or scope each claim to its catalog version explicitly.

2. **`precision = 0.0%` is the headline M5 number and reads catastrophically out of context.** It means every clean negative control fired ≥1 rule on the *pre-refinement* catalog. Stated alone it undercuts the catalog; stated with the Phase 2.5 trajectory (0% → 97.1% NC clean) it becomes the motivating problem the work solves. Never present the M5 precision without the Phase 2.5 fix in the same breath.

3. **No secondary-battery evidence.** Cross-pack generalization, paraphrase robustness (soft gate #29), and multi-model quality (gates #30/#31) have zero data. Any Ch3 claim depending on those gates is currently unsupported.

---

### Appendix — provenance facts
- **Run inventory** under `dev/build/adversarial/phase2/`: `2026-04-26` (canonical M5); `2026-04-28-v0510`, `-v0511`, `2026-04-29-v0512` (Phase 2.5 hybrid NC-regen variants); `2026-04-29-v0_phase2v2-test` (118-pkg NC smoke); `holdout-2026-04-29-v0513` (483 pkgs), `holdout-2026-04-29-v0515` (180 NCs). **No `2026-05-*` Phase 2 run.**
- **Tags present:** `v0.5.0-pre-phase2`, `v0.5.2`–`v0.5.7`, then the Phase 2.5 chain `v0.5.8-phase2.5-*` … `v0.5.15.1-phase2v3-…`. **`v0.5.5-phase2-complete` (runbook's M7 tag) does NOT exist.**
- **Known issues from `m5_findings.md`** already fixed (do not re-flag): F3 baseline-subtraction (`5698cc1`), F4 GEN-INVALID denominator (`9554b34`), F5 pyshacl stream-consume (`8aa63de`). Open: F1 (design), F2 (paraphrase safety-filter), F6 (resume cost double-count, cosmetic), F7 (analyze is sequential, ~5h wall).

# Phase 2.5 (Catalog Refinement Loop) — Status Report

**Repo:** github.com/cloudronin/uofa — local working copy (incl. gitignored `dev/build/`)
**Investigator:** Claude Code, paired with Vishnu Vettrivel
**Date:** 2026-06-09
**Method:** Read-only. Evidence = refinement-log records, milestone CSVs, and holdout summaries with numbers. No artifact, result, or spec modified.
**Companion reports:** [PHASE2_STATUS_REPORT.md](PHASE2_STATUS_REPORT.md), [PHASE3_STATUS_REPORT.md](PHASE3_STATUS_REPORT.md).

---

## 1. One-line answer

**Phase 2.5 is essentially COMPLETE and is the strongest-evidenced of the three phases.** A metric-gated, holdout-validated refinement loop drove the catalog's negative-control clean rate from **0% (M5 baseline) → 97.1% (v0.5.15.1 holdout, 166/171)** — **decomposed 2026-08-17 over all four corpus×catalog combinations: rule refinement alone is 4.5 points, the regenerated corpus alone is 0.0 points, and 97.1% appears only where both are present, because each axis is blocked by a rule the other one fixes ([INV-16](docs/investigations/INV-16-nc-trajectory-decomposition.md))** — with **7 target rules locked** (recall ≥0.90, nc_fpr ≤0.10) on seed-pinned train/dev/holdout splits, and a reproducible audit trail (`refinement_log.jsonl`, 15 iterations). ~~**The first gap is scope, not execution:** the validated endpoint is **NC-specificity only** — the v0.5.15.1 catalog was **never re-run as a full battery** to re-measure CE recall / gap-probe / interaction~~ — **CLOSED 2026-08-17 (`98959943`): the full battery is re-analyzed at v0.5.15.1**, all four intents, 4,601 packages, at zero LLM cost. **COMPOUND-01 remains unlocked** (corpus dependency on the W-EP-01 bug).

> Bottom line: **The specificity claim (97.1% NC clean) is rigorously earned and NAFEMS-ready.** What's missing is a full-battery holdout on the refined catalog and the closure of two known residuals — and the fact that downstream Phase 3 judged a corpus from *before* this refinement.

---

## 2. Stage table

| Stage | Verdict | Key numbers (exact, with source) | Evidence path | Gaps |
|---|---|---|---|---|
| **A — Per-rule refinement loop** (split→propose→measure→lock) | **DONE** | **15 iterations** logged. **7 rules LOCKED** at recall≥0.90/nc_fpr≤0.10: W-EP-01, W-AL-02, W-ON-02, W-AR-02, W-CON-01, W-CON-04 (all recall 1.000), W-AR-01 (0.936); + COMPOUND-03 lock-no-edit. **COMPOUND-01 NOT locked** (train recall 0.5714, "refinement-stuck"). | `dev/build/phase2_5/shared/refinement_log.jsonl`; `shared/milestones/after_*.csv`; `shared/holdout_used/*.lock` (7) | COMPOUND-01 stuck on a corpus-level dependency (54/126 targets relied on the W-EP-01 bug as input). |
| **B — Corpus regen + Phase 2 v2 prompt cleanup** (v0.5.10–v0.5.13) | **DONE** | NC clean on M5 corpus: **0% → 40.3% (v0.5.10) → 60.8% (v0.5.11) → 97.2% (v0.5.12)**. First **holdout 87.5%** (14/16, 483-pkg Phase C battery), which surfaced the W-CON-01 not-assessed gap (→ v0.5.14). | `v0.5.10-w-on-02/`, `v0.5.11-w-ar-02/`, `v0.5.12-w-con-fixes/`, `v0.5.13-prompt-cleanup/holdout_v0513_summary.md` | The 87.5% was "real-but-shaky" — masked by two latent bugs (see D2). |
| **C — Tool-use migration + SHACL/SA fix** (v0.5.15 / v0.5.15.1) | **DONE (NAFEMS-ready endpoint)** | **NC clean (validated) 166/171 = 97.1%**; strict 166/180 = 92.2%; gen success 179/180 = 99.4%; **GEN-INVALID 11.1% → 5.0%**; cost $34.48. All 7 Phase-2.5 rules **silent** on fresh holdout NCs. | `v0.5.15.1-shacl-and-sa-fix/holdout_v0515_summary.md` (2026-04-29) | Validated on **180 NCs only**. |
| **Validation scope** | **PARTIAL** | Validated on 3 corpora: M5 (4,605), Phase C holdout (483), v0.5.15.1 holdout (180 NC). | `holdout_v0515_summary.md:106-122,187-194` | **Explicitly does NOT test** CE recall, gap-probe MISS, or interaction on v0.5.15.1. Residual **5/171 NC firings (2.9%)** on non-target rules (W-ON-01, W-AL-01/W-AR-05/W-EP-02 cascade). |

---

## 3. Deviation / disclosure log

| # | Item to disclose | Evidence | Ch3 disclosure note |
|---|---|---|---|
| D1 | **"97.1%" is NC-specificity, not overall catalog quality.** It measures false-positive suppression on clean negative controls — not recall, not gap detection. | `holdout_v0515_summary.md:11-19,187-191` | "The headline 97.1% is the negative-control clean rate (specificity). CE recall (68.6% baseline) and gap-probe were validated separately/earlier and not re-measured at v0.5.15.1." |
| D2 | **The earlier 87.5% holdout was confounded by two masking bugs** — a pyshacl thread-safety race and a schema-mismatched `hasSensitivityAnalysis` (inline object vs. `xsd:boolean`). v0.5.15.1 fixed both; 97.1% is the reliable number. | `holdout_v0515_summary.md:31-65,126-139` | "Two latent bugs masked each other through v0.5.13; v0.5.15.1 corrects both, so the 97.1% is computed under correct SHACL behavior." |
| D3 | **COMPOUND-01 left unlocked** (train recall 0.5714, below the 0.80 floor) due to a corpus dependency on the (now-fixed) W-EP-01 bug. | `refinement_log.jsonl` ("rejected-baseline … COMPOUND-01 train recall=0.5714"); Phase 2.5 README | "COMPOUND-01 remains an open rule; its lock requires a corpus regen decoupling it from the W-EP-01 input." |
| D4 | **Catalog under test = v0.5.14 rules + v0.5.15.1 hooks.** The "version" is a rules+hooks pair, not a single artifact. | `holdout_v0515_summary.md:180-185` | "The terminal catalog is v0.5.14 rules with v0.5.15.1 post-LLM hooks (envelope, offset-rationale, boolean SA)." |
| D5 | **Placeholder SA / NC-patch content.** NC regens inject *placeholder* `hasSensitivityAnalysis: true` / envelope / offset-rationale values, not substantive content; substantive-content prompt engineering is deferred. | `dev/tools/phase2_5/README.md:37-39`; `holdout_v0515_summary.md:191` | "NC patches use schema-valid placeholders; substantive sensitivity-analysis content is future work." |

---

## 4. Remaining-work table

Hours are **estimates** for Claude-Code-paired execution. "Gap" = can it run/progress **June 13 – July 4**?

| Task | Est. hrs | Blocking dependency | Runs during June 13–Jul 4 gap? |
|---|---:|---|---|
| **P25-A. Full-battery holdout on v0.5.15.1** (the deferred 39-spec sample: CE recall + gap-probe + interaction, not just NC) — closes the validation-scope gap | 3–5 active + analyze | API key + ~$30–50 budget | **Partially** — automatable/unattended if staged before June 13. This is the highest-value remaining 2.5 item. |
| **P25-B. Lock COMPOUND-01** (corpus regen to decouple from W-EP-01 input, then re-run loop) | 4–8 | Author corpus-design decision | **No** — needs author judgment. |
| **P25-C. Investigate 5 residual NC firings** (W-ON-01 envelope-coverage gap; W-AL-01/W-AR-05/W-EP-02 validation-result cluster) — confirm legitimate vs. over-eager | 3–5 | P25-A sample (or M5) | **Partially** — analysis-only; can progress if data staged. |
| **P25-D. Substantive SA-content prompt engineering** (replace placeholder NC payloads) | 4–8 | Author prompt design | **No** — author. |
| **P25-E. Consolidate Phase 2.5 → Ch3 specificity narrative** (the 0%→97.1% trajectory + 3-corpus validation) | 3–5 | P25-A (ideally) | **No** — author writing. |

**Scheduling read:** Phase 2.5's substantive work is *done*; the gap-eligible item is the unattended full-battery v0.5.15.1 holdout (P25-A) if budget/keys are staged. The two open residuals (COMPOUND-01, substantive content) need the author.

---

## 5. Risk flags

1. **Downstream version skew (shared with Phase 2/3).** Phase 2.5's whole point was fixing the catalog's specificity (0%→97.1% NC clean), but **Phase 3 judged the pre-refinement 2026-04-26 corpus**. The refinement is validated; its *propagation* to the corpus the rest of the dissertation analyzes is not. ~~Without a full-battery re-run on v0.5.15.1 (P25-A) + a re-judge, the refined catalog and the judged corpus describe different rule behavior. This is the single most important coherence risk across all three phases.~~
   **RESOLVED 2026-08-17 by ruling, in two halves.** The full-battery re-analysis is **done** (`98959943`), so every figure is now quotable at one catalog version. **The re-judge is declined**, not deferred: the judge panel validated the adversarial corpus's *realism*, that corpus is frozen, and after this month's reframe the detection numbers no longer route through judges at all — so re-judging buys a cleaner footnote at real cost and touches nothing load-bearing. Disclosed in future work with the cost stated. **This is no longer the largest coherence risk**, because the risk was that figures and judgments described different catalogs; the figures have moved and the judgments are scoped to what they actually established.

2. ~~**The specificity gain may have cost recall, and that trade-off is under-measured.**~~ **CLOSED by P25-A Arm G, 2026-08-16 (`e40d7819`).** CE recall at v0.5.15.1 is **75.9%** (287/378 evaluable rows), beside a **97.1%** NC clean rate at the same version — the version-consistent pair that replaces M5's 73.4% @ v0.5.7 standing next to 97.1% @ v0.5.15.1.

   The trade-off turned out to be **one package**: W-CON-01 goes 20/20 → 19/20 between v0.5.13 and v0.5.15.1, and every other pattern's count is identical. The cause is the v0.5.14 guard `notEqual(?status,'not-assessed')`, which `rules:376-387` argued was recall-neutral. Measured, it costs one in twenty.

   **Denominator warning for anyone quoting these.** The **68.6%** above and the **76.2%** elsewhere in the record are the *same measurement* — 288/420 versus 288/378. The 42-package gap is the whole CE corpus for W-ON-01 and W-SI-01, `shaclFailed: 20` on both. The evaluable-rows convention is the one M5 used and the one followed here; a figure quoted without its denominator is ambiguous by 7.6 points.

3. **Generalization rests on small holdout samples for the specificity claim.** 97.1% is 166/171 validated NCs (180-package holdout); robust and seed-pinned, but the per-rule residuals (W-ON-01, W-AL-01 cluster) are single-digit counts. Honest as "no large-sample contradiction," not "proven at scale."

---

### Appendix — provenance facts
- **Cumulative NC-clean evidence chain** (`holdout_v0515_summary.md:106-116`): M5 v0.5.7 **0/176 = 0.0%** → v0.5.12 **175/180 = 97.2%** (M5 corpus) → v0.5.13 holdout **14/16 = 87.5%** → **v0.5.15.1 holdout 166/171 = 97.1%**.
  **Scope, added 2026-08-17 ([INV-16](docs/investigations/INV-16-nc-trajectory-decomposition.md)):** the chain's second row is labelled "M5 corpus" but was measured on a *hybrid* batch — M5 with placeholder stubs inserted by `dev/tools/phase2_5/corpus_regen/`. The unpatched M5 corpus at v0.5.15.1 scores **8/176 = 4.5%**, so the chain crosses a corpus boundary between rows 1 and 2 without marking it. All four corpus×catalog combinations are now measured: **rule refinement alone 4.5 points, regenerated corpus alone 0.0 points, both together 97.1%** — the gain is interactive, not a sum. W-EP-01 fires on 171/171 of the regenerated holdout at v0.5.7 (no regen tool targeted it), and W-ON-02 fires on 158/176 of M5 at v0.5.15.1 (it was never rule-fixed), so each axis is blocked by a rule the other one fixes. Both reproduction cells reproduced their committed figures exactly.
- **Holdout discipline:** 7 `shared/holdout_used/<rule>.lock` files (one per locked rule, dated 2026-04-27/28), 9 seed-pinned (`seed=20260427`) `shared/splits/*_split.json` — holdout spent at most once per rule.
- **Tags:** `v0.5.8-phase2.5-*` (w-ep-01, w-con-01, w-con-04, compound-03), `v0.5.9-phase2.5-w-al-02`, `v0.5.10`/`.11`/`.12`/`.12.1`/`.14` phase2.5, `v0.5.13-phase2v2-prompt-cleanup`, `v0.5.15-phase2v3-tool-use`, `v0.5.15.1-phase2v3-shacl-threadsafe-and-sa-boolean`, plus `holdout-v0513-validation` / `holdout-v0515-validation`. The Phase 2.5 chain is **fully merged into main** (the v0.5.x → v0.10.0 tag line is on the mainline).
- **Tooling tests exist** (`dev/tools/phase2_5/tests/`: `test_log.py`, `test_metrics.py`, `test_refine_loop.py`, `test_split.py`); not run in this read-only pass.
